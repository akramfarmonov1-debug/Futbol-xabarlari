import asyncio
import os
import traceback
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from .config import (
    AUTO_PUBLISH,
    AUTO_PUBLISH_MIN_IMPORTANCE,
    AUTO_TELEGRAM,
    AUTO_TELEGRAM_MIN_IMPORTANCE,
    DAILY_DIGEST,
    FRONTEND_ORIGIN,
    MEDIA_DIR,
)
from .database import Base, SessionLocal, engine, ensure_schema
from .models import Article
from .routers import admin, categories, legionnaires, news, push, scores
from .backfill import backfill_tags
from .seed import seed_categories
from .pipeline import LAST_RUN, format_error, run_pipeline
from .bot.bot import main as run_bot
from .services.daily_digest import run_digest_loop

PIPELINE_STATE = {
    "status": "not_started",
    "last_started_at": None,
    "last_completed_at": None,
    "last_error_at": None,
    "last_error": None,
    "last_saved": None,
}

# Baza start paytida yiqilgan bo'lsa ham ilova ko'tariladi — nima bo'lgani
# shu yerda turadi va /health orqali ko'rinadi.
DATABASE_STATE = {
    "status": "not_started",
    "ready_at": None,
    "last_error_at": None,
    "last_error": None,
}
DB_RETRY_INTERVAL = 60  # soniya


async def pipeline_loop_task():
    # Wait for the server to spin up fully
    await asyncio.sleep(15)
    while True:
        PIPELINE_STATE["status"] = "running"
        PIPELINE_STATE["last_started_at"] = datetime.now(timezone.utc).isoformat()
        try:
            print("⏳ Running background news pipeline...")
            loop = asyncio.get_running_loop()
            saved = await loop.run_in_executor(None, run_pipeline, 5)
            PIPELINE_STATE["status"] = "ok"
            PIPELINE_STATE["last_completed_at"] = datetime.now(timezone.utc).isoformat()
            PIPELINE_STATE["last_saved"] = saved
            print(f"✅ Pipeline done. Saved {saved} articles.")
        except Exception as e:
            PIPELINE_STATE["status"] = "error"
            PIPELINE_STATE["last_error_at"] = datetime.now(timezone.utc).isoformat()
            PIPELINE_STATE["last_error"] = format_error(e)
            traceback.print_exc()
            print(f"❌ Pipeline loop error: {e}")

        interval = int(os.getenv("PIPELINE_INTERVAL", "3600"))
        await asyncio.sleep(interval)


async def bot_task():
    await asyncio.sleep(5)
    try:
        print("🤖 Starting background Telegram Bot...")
        await run_bot()
    except Exception as e:
        print(f"❌ Telegram Bot error: {e}")


async def digest_task():
    await asyncio.sleep(20)
    try:
        print("📋 Starting background Daily Digest loop...")
        await run_digest_loop()
    except Exception as e:
        print(f"❌ Daily Digest loop error: {e}")


def init_database() -> None:
    Base.metadata.create_all(engine)
    ensure_schema()
    db = SessionLocal()
    try:
        seed_categories(db)
        renamed = backfill_tags(db)
        if renamed:
            print(f"Teglar kanonik ko'rinishga keltirildi: {renamed} ta xabar.")
    finally:
        db.close()


def try_init_database() -> bool:
    try:
        init_database()
    except SQLAlchemyError as e:
        DATABASE_STATE["status"] = "error"
        DATABASE_STATE["last_error_at"] = datetime.now(timezone.utc).isoformat()
        DATABASE_STATE["last_error"] = format_error(e)
        print(f"❌ Bazaga ulanib bo'lmadi: {DATABASE_STATE['last_error']}")
        return False
    DATABASE_STATE["status"] = "ok"
    DATABASE_STATE["ready_at"] = datetime.now(timezone.utc).isoformat()
    return True


def start_background_tasks(bg_tasks: list) -> None:
    bg_tasks.append(asyncio.create_task(pipeline_loop_task()))

    if os.getenv("TELEGRAM_BOT_TOKEN"):
        bg_tasks.append(asyncio.create_task(bot_task()))
    else:
        print("[INFO] TELEGRAM_BOT_TOKEN is not set. Bot background task will not start.")

    if DAILY_DIGEST:
        bg_tasks.append(asyncio.create_task(digest_task()))
    else:
        print("[INFO] DAILY_DIGEST is not enabled. Daily digest task will not start.")


async def database_retry_task(bg_tasks: list) -> None:
    loop = asyncio.get_running_loop()
    while True:
        await asyncio.sleep(DB_RETRY_INTERVAL)
        if await loop.run_in_executor(None, try_init_database):
            print("✅ Baza qayta ulandi; fon vazifalari ishga tushirilmoqda.")
            start_background_tasks(bg_tasks)
            return


@asynccontextmanager
async def lifespan(app: FastAPI):
    bg_tasks = []
    if try_init_database():
        start_background_tasks(bg_tasks)
    else:
        # Ilova baribir ko'tarilsin: aks holda Render'da servis butunlay
        # g'oyib bo'ladi (so'rovlar osilib qoladi) va /health sababini ayta
        # olmaydi. Pipeline, bot va digest bazasiz ishlamaydi — baza qaytgach
        # o'zi ishga tushadi.
        bg_tasks.append(asyncio.create_task(database_retry_task(bg_tasks)))

    yield
    
    for task in bg_tasks:
        task.cancel()
    if bg_tasks:
        await asyncio.gather(*bg_tasks, return_exceptions=True)


app = FastAPI(
    title="Futbol Xabar API",
    description="Jahon futboli yangiliklari — o'zbek tilida",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_ORIGIN,
        "http://localhost:3000",
        "https://futbolxabar.uz",
        "https://www.futbolxabar.uz",
        "https://futbol-xabarlari.vercel.app",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(news.router)
app.include_router(categories.router)
app.include_router(admin.router)
app.include_router(scores.router)
app.include_router(legionnaires.router)
app.include_router(push.router)

# Generatsiya qilingan rasmlar (IMAGE_GENERATION=true rejimi uchun)
Path(MEDIA_DIR).mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")


@app.get("/")
def root():
    return {"loyiha": "Futbol Xabar", "hujjatlar": "/docs"}


@app.get("/health")
def health():
    """Diagnostika: baza tirikmi, oxirgi sikl nima qildi va nima yiqildi.

    Bu ochiq endpoint — xato matnlari `format_error` orqali tozalab
    beriladi, aks holda service-account kaliti tashqariga chiqib ketishi
    mumkin.
    """
    body = {
        "status": "ok",
        "database": "ok",
        "latest_article_at": None,
        # Amaldagi chegaralar ham shu yerda: server environment koddagi
        # standartni bekor qilsa, buni taxmin qilib emas, ko'rib bilamiz.
        "publish": {
            "auto_publish": AUTO_PUBLISH,
            "auto_publish_min_importance": AUTO_PUBLISH_MIN_IMPORTANCE,
            "auto_telegram": AUTO_TELEGRAM,
            "auto_telegram_min_importance": AUTO_TELEGRAM_MIN_IMPORTANCE,
        },
        "pipeline": {**PIPELINE_STATE, "last_run": LAST_RUN},
        "database_init": dict(DATABASE_STATE),
    }
    db = SessionLocal()
    try:
        latest = db.query(func.max(Article.created_at)).scalar()
    except SQLAlchemyError as e:
        # 503 — monitoring nosozlikni sezadi; sababi esa javobning o'zida,
        # Render log'ini ochmasdan ham nima yiqilgani ko'rinadi.
        body.update(status="error", database="error", database_error=format_error(e))
        return JSONResponse(status_code=503, content=jsonable_encoder(body))
    finally:
        db.close()
    body["latest_article_at"] = latest
    return body
