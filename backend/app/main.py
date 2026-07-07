import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import FRONTEND_ORIGIN, MEDIA_DIR
from .database import Base, SessionLocal, engine
from .routers import admin, categories, news
from .seed import seed_categories
from .pipeline import run_pipeline
from .bot.bot import main as run_bot


async def pipeline_loop_task():
    # Wait for the server to spin up fully
    await asyncio.sleep(15)
    while True:
        try:
            print("⏳ Running background news pipeline...")
            loop = asyncio.get_running_loop()
            saved = await loop.run_in_executor(None, run_pipeline, 5)
            print(f"✅ Pipeline done. Saved {saved} articles.")
        except Exception as e:
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        seed_categories(db)
    finally:
        db.close()
    
    bg_tasks = []
    
    # Start pipeline
    bg_tasks.append(asyncio.create_task(pipeline_loop_task()))
    
    # Start bot if token exists
    if os.getenv("TELEGRAM_BOT_TOKEN"):
        bg_tasks.append(asyncio.create_task(bot_task()))
    else:
        print("⚠️ TELEGRAM_BOT_TOKEN is not set. Bot background task will not start.")
        
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
    allow_origins=[FRONTEND_ORIGIN, "http://localhost:3000", "https://yangi18.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(news.router)
app.include_router(categories.router)
app.include_router(admin.router)

# Generatsiya qilingan rasmlar (IMAGE_GENERATION=true rejimi uchun)
Path(MEDIA_DIR).mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")


@app.get("/")
def root():
    return {"loyiha": "Futbol Xabar", "hujjatlar": "/docs"}
