from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "StudyMatch"
    app_version: str = "1.0.0"
    debug: bool = True

    # Database (SQLite for local dev, switch to PostgreSQL for production)
    database_url: str = "sqlite+aiosqlite:///./studymatch.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str = "your-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440  # 24 hours

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

    # Allowed email domains
    allowed_email_domains: list[str] = [
        "am.students.amrita.edu",
        "am.amrita.edu",
        "amrita.edu",
    ]

    # Campuses
    campuses: list[str] = [
        "Bengaluru",
        "Coimbatore",
        "Amritapuri",
        "Chennai",
        "Kochi",
    ]
    default_campus: str = "Bengaluru"

    # Departments
    departments: list[str] = [
        "CSE",
        "ECE",
        "EEE",
        "ME",
        "CE",
        "CHE",
        "AE",
        "CSE-AI",
        "CSE-CYS",
        "AI&DS",
        "IT",
        "BioTech",
        "Physics",
        "Chemistry",
        "Mathematics",
        "English",
        "MBA",
        "MCA",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
