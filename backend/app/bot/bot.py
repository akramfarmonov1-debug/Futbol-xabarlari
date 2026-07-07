"""Futbol Xabar — Telegram bot (aiogram 3).

Funksiyalar: bugungi yangiliklar, haftalik dayjest, kategoriya tanlash,
qidiruv, saqlangan maqolalar, bildirishnomalarni yoqish/o'chirish.

Ishga tushirish:  python bot.py
"""

import asyncio
import html
import os

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from dotenv import load_dotenv

from . import storage

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
API_URL = os.getenv("API_URL", "http://localhost:8000")
SITE_URL = os.getenv("SITE_URL", "http://localhost:3000")

dp = Dispatcher()

MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📰 Bugungi yangiliklar"), KeyboardButton(text="🗓 Haftalik dayjest")],
        [KeyboardButton(text="📂 Kategoriyalar"), KeyboardButton(text="🔍 Qidiruv")],
        [KeyboardButton(text="⭐ Saqlanganlar"), KeyboardButton(text="🔔 Bildirishnomalar")],
    ],
    resize_keyboard=True,
)

# Qidiruv rejimini kutayotgan foydalanuvchilar
awaiting_search: set[int] = set()


async def api_get(path: str, params: dict | None = None):
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(f"{API_URL}{path}", params=params)
        response.raise_for_status()
        return response.json()


def article_text(article: dict) -> str:
    stars = "⭐" * max(1, min(5, article.get("importance", 3)))
    category = (article.get("category") or {}).get("name", "AI")
    return (
        f"<b>{html.escape(article['title'])}</b>\n\n"
        f"{html.escape(article['summary'])}\n\n"
        f"💡 <i>{html.escape(article.get('practical_note', ''))}</i>\n\n"
        f"📂 {html.escape(category)} | {stars}\n"
        f"🔗 <a href=\"{article['original_url']}\">Asl manba</a> | "
        f"<a href=\"{SITE_URL}/maqola/{article['slug']}\">Saytda o'qish</a>"
    )


def save_button(article: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⭐ Saqlash", callback_data=f"save:{article['slug']}")
    ]])


async def send_articles(message: Message, articles: list[dict], empty_text: str, limit: int = 5):
    if not articles:
        await message.answer(empty_text)
        return
    for article in articles[:limit]:
        await message.answer(
            article_text(article),
            parse_mode="HTML",
            reply_markup=save_button(article),
            disable_web_page_preview=False,
        )


@dp.message(Command("start"))
async def cmd_start(message: Message):
    storage.ensure_user(message.chat.id)
    await message.answer(
        "🤖 <b>Futbol Xabar</b> botiga xush kelibsiz!\n\n"
        "Bu bot dunyodagi eng muhim jahon futboli yangiliklarini "
        "o'zbek tilida yetkazib beradi.\n\n"
        "Quyidagi menyudan foydalaning 👇",
        parse_mode="HTML",
        reply_markup=MENU,
    )


@dp.message(F.text == "📰 Bugungi yangiliklar")
async def today_news(message: Message):
    articles = await api_get("/api/news/digest")
    await send_articles(message, articles, "Bugun hali yangiliklar chop etilmadi.")


@dp.message(F.text == "🗓 Haftalik dayjest")
async def weekly_digest(message: Message):
    articles = await api_get("/api/news/top", {"kunlar": 7, "limit": 10})
    await send_articles(message, articles, "So'nggi haftada yangiliklar topilmadi.", limit=10)


@dp.message(F.text == "📂 Kategoriyalar")
async def categories(message: Message):
    cats = await api_get("/api/categories")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=c["name"], callback_data=f"cat:{c['slug']}")]
        for c in cats
    ])
    await message.answer("Kategoriyani tanlang:", reply_markup=keyboard)


@dp.callback_query(F.data.startswith("cat:"))
async def category_news(callback: CallbackQuery):
    slug = callback.data.split(":", 1)[1]
    articles = await api_get("/api/news", {"kategoriya": slug, "limit": 5})
    await callback.answer()
    await send_articles(callback.message, articles, "Bu kategoriyada hali yangiliklar yo'q.")


@dp.callback_query(F.data.startswith("save:"))
async def save_article(callback: CallbackQuery):
    slug = callback.data.split(":", 1)[1]
    try:
        article = await api_get(f"/api/news/{slug}")
        storage.save_article(callback.message.chat.id, slug, article["title"])
        await callback.answer("⭐ Saqlandi!")
    except Exception:
        await callback.answer("Xatolik yuz berdi", show_alert=True)


@dp.message(F.text == "⭐ Saqlanganlar")
async def saved_articles(message: Message):
    saved = storage.get_saved(message.chat.id)
    if not saved:
        await message.answer("Saqlangan maqolalar yo'q. Yangilik ostidagi ⭐ tugmasini bosing.")
        return
    lines = [
        f"• <a href=\"{SITE_URL}/maqola/{slug}\">{html.escape(title)}</a>"
        for slug, title in saved[-20:]
    ]
    await message.answer(
        "<b>⭐ Saqlangan maqolalaringiz:</b>\n\n" + "\n".join(lines),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


@dp.message(F.text == "🔔 Bildirishnomalar")
async def toggle_notifications(message: Message):
    enabled = storage.toggle_notifications(message.chat.id)
    if enabled:
        await message.answer("🔔 Bildirishnomalar yoqildi — muhim yangiliklar chiqqanda xabar beramiz.")
    else:
        await message.answer("🔕 Bildirishnomalar o'chirildi.")


@dp.message(F.text == "🔍 Qidiruv")
async def ask_search(message: Message):
    awaiting_search.add(message.chat.id)
    await message.answer("Qidiruv so'zini yozing (masalan: <i>Gemini</i>):", parse_mode="HTML")


@dp.message(F.text)
async def handle_text(message: Message):
    if message.chat.id in awaiting_search:
        awaiting_search.discard(message.chat.id)
        articles = await api_get("/api/news/search", {"q": message.text})
        await send_articles(message, articles, f"«{message.text}» bo'yicha hech narsa topilmadi.")
    else:
        await message.answer("Menyudan birini tanlang 👇", reply_markup=MENU)


async def main():
    if not BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN is empty. Skipping Telegram Bot startup.")
        return
    bot = Bot(token=BOT_TOKEN)
    print("🤖 Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
