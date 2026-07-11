import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.core.security import create_access_token, validate_amrita_email
from app.core.config import get_settings

settings = get_settings()

GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"


async def verify_google_token(token: str) -> dict:
    """Verify Google OAuth token and return user info."""
    async with httpx.AsyncClient() as client:
        # Try as access token first
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 200:
            return response.json()

        # Try as ID token
        response = await client.get(
            GOOGLE_TOKEN_INFO_URL,
            params={"id_token": token},
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "sub": data.get("sub"),
                "email": data.get("email"),
                "name": data.get("name"),
                "picture": data.get("picture"),
                "email_verified": data.get("email_verified") == "true",
            }

    return None


async def authenticate_with_google(
    token: str,
    db: AsyncSession,
) -> tuple[User, bool]:
    """
    Authenticate user via Google OAuth.
    Returns (user, is_new_user) tuple.
    """
    google_user = await verify_google_token(token)
    if not google_user:
        raise ValueError("Invalid Google token")

    email = google_user.get("email", "").lower()
    if not email:
        raise ValueError("No email in Google profile")

    if not validate_amrita_email(email):
        raise ValueError(
            "Only Amrita university email addresses are allowed. "
            f"Please sign in with your @amrita.edu email."
        )

    # Check if user exists
    result = await db.execute(
        select(User).where(
            (User.google_id == google_user.get("sub")) | (User.email == email)
        )
    )
    user = result.scalar_one_or_none()

    if user:
        # Update Google info if needed
        if not user.google_id:
            user.google_id = google_user.get("sub")
        if google_user.get("picture") and not user.avatar_url:
            user.avatar_url = google_user["picture"]
        user.is_verified = True
        await db.flush()
        return user, False

    # Create new user
    user = User(
        email=email,
        full_name=google_user.get("name", email.split("@")[0]),
        google_id=google_user.get("sub"),
        avatar_url=google_user.get("picture"),
        department="",
        year=1,
        campus=settings.default_campus,
        is_verified=True,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user, True


def create_user_token(user: User) -> str:
    return create_access_token(data={"sub": str(user.id), "email": user.email})
