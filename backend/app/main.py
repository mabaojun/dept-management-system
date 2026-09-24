import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.api import analysis, auth, config_api, dashboard, reports, tasks, users, worklogs
from app.core.config import get_settings
from app.db.base import Base, SessionLocal, engine
from app.db.seed import seed_admin
from app.models import (  # noqa: F401 确保模型注册
    PerformanceReview,
    PeriodReport,
    Task,
    TaskChangeLog,
    User,
    WorkLog,
)
from app.services.scheduler import scheduler_loop

logging.basicConfig(level=logging.INFO)

# 轻量迁移：旧库缺列时补充（SQLite/PostgreSQL 通用写法）
_MIGRATIONS: dict[str, str] = {
    "tasks.archived": "ALTER TABLE tasks ADD COLUMN archived BOOLEAN NOT NULL DEFAULT FALSE",
    "tasks.progress": "ALTER TABLE tasks ADD COLUMN progress TEXT NOT NULL DEFAULT ''",
}


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    for table, ddl in _MIGRATIONS.items():
        table_name, column = table.split(".")
        if table_name in inspector.get_table_names():
            columns = {c["name"] for c in inspector.get_columns(table_name)}
            if column not in columns:
                with engine.begin() as conn:
                    conn.execute(text(ddl))
    with SessionLocal() as db:
        seed_admin(db)
    scheduler = asyncio.create_task(scheduler_loop())
    yield
    scheduler.cancel()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for r in (auth, users, tasks, worklogs, analysis, dashboard, reports, config_api):
        app.include_router(r.router, prefix="/api")
    return app


app = create_app()


@app.get("/api/health")
def health():
    return {"status": "ok"}
