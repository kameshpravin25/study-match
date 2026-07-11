from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.database import create_tables
from app.api.v1.auth import router as auth_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.requests import router as requests_router
from app.api.v1.profiles import router as profiles_router
from app.api.v1.admin import router as admin_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (for SQLite dev)
    await create_tables()
    yield

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Study matching platform for Amrita students",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# CORS — allow Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(requests_router, prefix="/api/v1")
app.include_router(profiles_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")


# Admin dashboard page
@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    html_path = Path(__file__).parent / "static" / "admin.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
