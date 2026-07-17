import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from src.api.errors import register_error_handlers
from src.api.routers import auth, course_space, courses, health, knowledge


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SESSION_SECRET = "learning-os-local-development-secret"


def create_app(session_secret=None):
    load_dotenv(BASE_DIR / ".env", override=False)
    selected_session_secret = session_secret or os.getenv(
        "API_SESSION_SECRET",
        DEFAULT_SESSION_SECRET,
    )
    _validate_production_session_secret(selected_session_secret)

    app = FastAPI(
        title="Learning OS API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_get_allowed_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=selected_session_secret,
        session_cookie="learning_os_session",
        max_age=60 * 60 * 24 * 7,
        same_site="lax",
        https_only=_get_boolean_setting("API_COOKIE_SECURE", False),
    )

    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(courses.router)
    app.include_router(course_space.router)
    app.include_router(knowledge.router)
    return app


def _get_allowed_origins():
    configured = os.getenv("API_ALLOWED_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173")
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


def _get_boolean_setting(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _validate_production_session_secret(session_secret):
    if os.getenv("APP_ENV", "").strip().lower() != "production":
        return
    insecure_values = {"", "secret", DEFAULT_SESSION_SECRET}
    if session_secret.strip() in insecure_values or len(session_secret.strip()) < 32:
        raise RuntimeError(
            "API_SESSION_SECRET must contain at least 32 non-default characters in production."
        )
