import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import func, select, text

from app.api import admin, auth, chat, container_admin, containers, system
from app.config import get_settings
from app.db import SessionLocal, engine
from app.models import User
from app.redis_client import get_redis
from app.security import hash_password
from app.services import ingestion
from app.services.container import get_embedder, get_vectorstore

settings = get_settings()
logging.basicConfig(level=settings.log_level.upper(), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("app")


async def seed_admin() -> None:
    if not (settings.admin_email and settings.admin_password):
        return
    email = settings.admin_email.strip().lower()
    async with SessionLocal() as session:
        exists = (await session.execute(select(User).where(func.lower(User.email) == email))).scalar_one_or_none()
        if exists:
            return
        session.add(User(email=email, name=settings.admin_name, password_hash=hash_password(settings.admin_password), role="admin"))
        await session.commit()
        log.info("Seeded admin user %s", email)


async def background_index() -> None:
    for attempt in range(1, 6):  # Qdrant / model download may still be warming up
        try:
            report = await ingestion.sync_directory()
            log.info("Startup indexing: %d indexed, %d unchanged, %d removed, %d errors",
                     len(report.indexed), report.skipped, len(report.removed), len(report.errors))
            return
        except Exception as exc:  # noqa: BLE001
            log.warning("Startup indexing attempt %d failed: %s", attempt, exc)
            await asyncio.sleep(10 * attempt)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await seed_admin()
    get_embedder().warmup()  # start loading/downloading the embedding model right away
    task = asyncio.create_task(background_index()) if settings.auto_index_on_start else None
    yield
    if task:
        task.cancel()
    await engine.dispose()


app = FastAPI(title="DevOps AI Assistant", version="1.0.0", lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json")
app.include_router(auth.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(system.router, prefix="/api")
app.include_router(containers.router, prefix="/api")
app.include_router(container_admin.router, prefix="/api")


@app.get("/api/health")
async def health() -> dict[str, object]:
    checks: dict[str, bool] = {}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("select 1"))
        checks["postgres"] = True
    except Exception:  # noqa: BLE001
        checks["postgres"] = False
    try:
        checks["redis"] = bool(await get_redis().ping())
    except Exception:  # noqa: BLE001
        checks["redis"] = False
    checks["qdrant"] = await get_vectorstore().health()
    return {"ok": all(checks.values()), **checks}
