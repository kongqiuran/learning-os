import os
import time
from uuid import uuid4
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from src.api.errors import register_error_handlers
from src.api.routers import account, admin_billing, auth, billing, chapters, course_space, courses, health, knowledge, privacy, visual_assets
from src.logging_config import configure_logging, get_logger


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SESSION_SECRET = "learning-os-local-development-secret"
logger = get_logger("learning_os.api")


def create_app(session_secret=None):
    configure_logging()
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

    @app.middleware("http")
    async def request_log_middleware(request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid4().hex
        started = time.monotonic()
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.exception(
                "Unhandled API request failure.",
                extra={
                    "event": "api.request.failed",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "user_id": getattr(request.state, "user_id", None),
                    "task_id": None,
                    "document_id": None,
                    "exception": exc,
                },
            )
            raise
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "API request completed.",
            extra={
                "event": "api.request.completed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "user_id": getattr(request.state, "user_id", None),
                "status": response.status_code,
                "duration_ms": int((time.monotonic() - started) * 1000),
            },
        )
        return response
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
    app.include_router(account.router)
    app.include_router(privacy.router)
    app.include_router(billing.router)
    app.include_router(admin_billing.router)
    app.include_router(courses.router)
    app.include_router(chapters.router)
    app.include_router(course_space.router)
    app.include_router(knowledge.router)
    app.include_router(visual_assets.router)
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
