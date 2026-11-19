from contextlib import asynccontextmanager
import logging
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import get_db, get_db_mode, init_db
from app.routers import (
    auth,
    schedules,
    settings as settings_router,
    users,
)
from app.seed import seed_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nurseshift")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.auto_seed:
        seed_database(force=False)
    yield


app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="API pro plánování a optimalizaci 12h směn zdravotních sester",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(settings_router.router)
app.include_router(schedules.router)


@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    db = get_db()
    users_count = sum(1 for _ in db.collection("users").stream())
    settings_doc = db.collection("settings").document("department_config").get()
    return {
        "status": "ok",
        "service": settings.project_name,
        "version": settings.version,
        "db_mode": get_db_mode(),
        "users_count": users_count,
        "department_configured": settings_doc.exists,
    }


@app.post("/api/seed")
def trigger_seed(force: bool = True) -> Dict[str, Any]:
    result = seed_database(force=force)
    return {
        "status": "ok",
        "db_mode": get_db_mode(),
        **result,
    }
