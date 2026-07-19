import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select, text

from src.api.schemas import HealthResponse
from src.config import DATA_DIR, UPLOAD_DIR
from src.database.connection import engine
from src.database import get_db_session
from src.models import Task


router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="ok", service="learning-os-api")


@router.get("/health/live")
def liveness():
    return {"status": "ok", "service": "learning-os-api"}


@router.get("/health/ready")
def readiness():
    checks = {}
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "failed"
    checks["uploads"] = "ok" if UPLOAD_DIR.exists() and os.access(UPLOAD_DIR, os.W_OK) else "failed"
    heartbeat = Path(DATA_DIR) / "database" / "worker-heartbeat"
    age = datetime.now(timezone.utc).timestamp() - heartbeat.stat().st_mtime if heartbeat.exists() else None
    checks["worker"] = "ok" if age is not None and age <= 90 else "failed"
    free = shutil.disk_usage(DATA_DIR).free
    checks["disk"] = "ok" if free >= 1024 * 1024 * 1024 else "low"
    if "failed" in checks.values() or "low" in checks.values():
        raise HTTPException(503, detail={"code": "service_not_ready", "checks": checks})
    return {"status": "ready", "checks": checks}


@router.get("/health/metrics")
def task_metrics():
    with get_db_session() as session:
        rows = session.execute(select(Task.status, func.count(Task.id)).group_by(Task.status)).all()
    return {"generation_tasks": {status: count for status, count in rows}}
