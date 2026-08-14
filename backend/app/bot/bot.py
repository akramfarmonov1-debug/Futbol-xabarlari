"""Futbol Xabar — Telegram bot (aiogram 3).

Interaktiv buyruqlar:
  /start — Botni ishga tushirish va asosiy menyu
  /bugun — Bugungi jonli o'yinlar va hisoblar
  /jadval — Turnir jadvallari (APL, La Liga, Seriya A, Bundesliga, Superliga)
  /legionerlar — O'zbekistonlik legionerlar (Husanov, Fayzullayev, Shomurodov)
  /top — Bugungi eng ko'p o'qilgan xabarlar
  /yangiliklar — Eng so'nggi xabarlar
  /kategoriyalar — Mavzular bo'yicha saralash
  /qidiruv — Yangiliklar bo'yicha qidiruv
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
from ..services.runtime_lock import (
    BOT_LOCK_ID,
    release_runtime_lock,
    try_runtime_lock,
)

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
API_URL = os.getenv("API_URL", "http://localhost:8000")
SITE_URL = os.getenv("SITE_URL", "http://localhost:3000")

dp = Dispatcher()

MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚽ Bugungi o'yinlar"), KeyboardButton(text="🏆 Turnir jadvallari")],
        [KeyboardButton(text="🇺🇿 Legionerlarimiz"), KeyboardButton(text="🔥 Top 5 Yangiliklar")],
        [KeyboardButton(text="📰 So'nggi xabarlar"), KeyboardButton(text="📂 Kategoriyalar")],
        [KeyboardButton(text="🔍 Qidiruv"), KeyboardButton(text="⭐ Saqlanganlar"), KeyboardButton(text="🔔 Xabarnomalar")],
    ],
    resize_keyboard=True,
)

awaiting_search: set[int] = set()


async def api_get(path: str, params: dict | None = None):
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            response = await client.get(f"{API_URL}{path}", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API so'rov xatosi ({path}): {e}")
            return None


def article_text(article: dict) -> str:
    stars = "⭐" * max(1, min(5, article.get("importance", 3)))
    category = (article.get("category") or {}).get("name", "Jahon futboli")
    views = article.get("views_count") or 1
    return (
        f"⚽️ <b>{html.escape(article['title'])}</b>\n\n"
        f"{html.escape(article['summary'])}\n\n"
        f"💡 <b>Nega muhim?</b>\n"
        f"<i>{html.escape(article.get('practical_note', ''))}</i>\n\n"
        f"📂 {html.escape(category)}  •  👁 {views}  •  {stars}"
    )


def article_buttons(article: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📖 Saytda to‘liq o‘qish",
                    url=f"{SITE_URL}/maqola/{article['slug']}",
                ),
                InlineKeyboardButton(
                    text="🔗 Asl manba",
                    url=article.get("original_url", SITE_URL),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⭐ Saqlash",
                    callback_data=f"save:{article['slug']}",
                )
            ],
        ]
    )


async def send_articles(message: Message, articles: list[dict] | None, empty_text: str, limit: int = 5):
    if not articles:
        await message.answer(empty_text)
        return
    for article in articles[:limit]:
        await message.answer(
            article_text(article),
            parse_mode="HTML",
            reply_markup=article_buttons(article),
            disable_web_page_preview=True,
        )


# ===================== COMMAND HANDLERS =====================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    storage.ensure_user(message.chat.id)
    await message.answer(
        "👋 <b>Futbol Xabar</b> rasmiy botiga xush kelibsiz!\n\n"
        "⚡️ Jahon futboli va O‘zbekiston legionerlarining eng so‘nggi, tahliliy yangiliklari, "
        "jonli natijalar va turnir jadvallari — toza o‘zbek tilida!\n\n"
        "Quyidagi menyudan kerakli bo‘limni tanlang 👇",
        parse_mode="HTML",
        reply_markup=MENU,
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📌 <b>Mavjud buyruqlar ro‘yxati:</b>\n\n"
        "⚽ /bugun — Bugungi jonli natijalar va o‘yinlar\n"
        "🏆 /jadval — Yevropa va O‘zbekiston ligalari jadvallari\n"
        "🇺🇿 /legionerlar — O‘zbekistonlik legionerlar holati\n"
        "🔥 /top — Eng ko‘p o‘qilgan va muhim xabarlar\n"
        "📰 /yangiliklar — So‘nggi yangiliklar\n"
        "📂 /kategoriyalar — Mavzular ro‘yxati\n"
        "🔍 /qidiruv — Yangiliklar ichidan qidirish\n"
        "🌐 /sayt — Veb-saytga to‘g‘ridan-to‘g‘ri o‘tish",
        parse_mode="HTML",
        reply_markup=MENU,
    )


@dp.message(Command("sayt"))
async def cmd_sayt(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🌐 futbolxabar.uz saytiga o‘tish", url=SITE_URL)]]
    )
    await message.answer("Rasmiy veb-saytimizga tashrif buyuring:", reply_markup=keyboard)


# ===================== ⚽ BUGUN / SCORES =====================

@dp.message(Command("bugun"))
@dp.message(F.text == "⚽ Bugungi o'yinlar")
async def cmd_scores(message: Message):
    data = await api_get("/api/scores")
    if not data or not data.get("matches"):
        await message.answer("⚽ Bugunga belgilangan asosiy o‘yinlar topilmadi.")
        return

    matches = data.get("matches", [])
    lines = ["⚽ <b>Bugungi futbol o‘yinlari va hisoblar:</b>\n"]
    
    for m in matches[:15]:
        home = m.get("home_team", "")
        away = m.get("away_team", "")
        home_score = m.get("home_score")
        away_score = m.get("away_score")
        status = m.get("status", "")
        league = m.get("league", "")

        score_str = f"{home_score} : {away_score}" if home_score is not None and away_score is not None else "vs"
        status_icon = "🔴 LIVE" if status == "IN_PLAY" else "🏁 FT" if status == "FINISHED" else "⏰"

        lines.append(f"• <b>{home}</b> {score_str} <b>{away}</b> ({status_icon})")
        if league:
            lines.append(f"  <i>🏆 {league}</i>")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="📊 Saytda barcha hisoblar", url=f"{SITE_URL}/jadval")]]
    )
    await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=keyboard)


# ===================== 🏆 JADVAL / STANDINGS =====================

LEAGUE_BUTTONS = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premyer-liga (APL)", callback_data="table:PL"),
            InlineKeyboardButton(text="🇪🇸 La Liga", callback_data="table:PD"),
        ],
        [
            InlineKeyboardButton(text="🇮🇹 Seriya A", callback_data="table:SA"),
            InlineKeyboardButton(text="🇩🇪 Bundesliga", callback_data="table:BL1"),
        ],
        [
            InlineKeyboardButton(text="🏆 Chempionlar ligasi", callback_data="table:CL"),
            InlineKeyboardButton(text="🇺🇿 O'zbekiston Superligasi", callback_data="table:UZ"),
        ],
    ]
)

@dp.message(Command("jadval"))
@dp.message(F.text == "🏆 Turnir jadvallari")
async def cmd_standings(message: Message):
    await message.answer("🏆 Qaysi liganing turnir jadvalini ko‘rmoqchisiz?", reply_markup=LEAGUE_BUTTONS)


@dp.callback_query(F.data.startswith("table:"))
async def handle_table_callback(callback: CallbackQuery):
    league_code = callback.data.split(":", 1)[1]
    data = await api_get(f"/api/scores/standings?league={league_code}")
    await callback.answer()

    if not data or not data.get("table"):
        await callback.message.answer("Ushbu liga bo‘yicha jadval ma'lumotlari hozircha yangilanmoqda.")
        return

    league_name = data.get("league", "Turnir jadvali")
    table = data.get("table", [])
    
    lines = [f"🏆 <b>{league_name} — Turnir jadvali (Top-8):</b>\n"]
    for row in table[:8]:
        pos = row.get("position", "")
        name = row.get("team_name", "")
        pts = row.get("points", "")
        played = row.get("played", "")
        lines.append(f"<b>{pos}. {name}</b> — <b>{pts}</b> ochko ({played} o‘yin)")

    link_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Saytda to‘liq jadvalni ko‘rish", url=f"{SITE_URL}/jadval")],
            [InlineKeyboardButton(text="🔙 Boshqa ligalar", callback_data="back_leagues")],
        ]
    )
    await callback.message.answer("\n".join(lines), parse_mode="HTML", reply_markup=link_markup)


@dp.callback_query(F.data == "back_leagues")
async def handle_back_leagues(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("🏆 Turnir jadvalini tanlang:", reply_markup=LEAGUE_BUTTONS)


# ===================== 🇺🇿 LEGIONERLAR =====================

@dp.message(Command("legionerlar"))
@dp.message(F.text == "🇺🇿 Legionerlarimiz")
async def cmd_legionnaires(message: Message):
    data = await api_get("/api/legionnaires")
    if not data or not data.get("legionnaires"):
        await message.answer("🇺🇿 Legionerlarimiz haqidagi ma'lumotlar yangilanmoqda.")
        return

    players = data.get("legionnaires", [])
    lines = ["🇺🇿 <b>O‘zbekistonlik legionerlar joriy holati:</b>\n"]

    for p in players:
        name = p.get("name", "")
        club = p.get("club", "")
        league = p.get("league", "")
        status = p.get("status", "")
        next_match = p.get("next_match")

        lines.append(f"⭐️ <b>{name}</b> ({club} / {league})")
        lines.append(f"   ℹ️ <i>{status}</i>")
        if next_match:
            lines.append(f"   📅 Keyingi o‘yin: <b>{next_match.get('opponent')}</b> ({next_match.get('date')})")
        lines.append("")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🇺🇿 Saytda legionerlar sahifasi", url=f"{SITE_URL}/legionerlar")]]
    )
    await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=keyboard)


# ===================== 🔥 TOP / NEWS =====================

@dp.message(Command("top"))
@dp.message(F.text == "🔥 Top 5 Yangiliklar")
async def cmd_top_news(message: Message):
    articles = await api_get("/api/news/top", {"kunlar": 7, "limit": 5})
    await send_articles(message, articles, "Eng so‘nggi top yangiliklar topilmadi.")


@dp.message(Command("yangiliklar"))
@dp.message(F.text == "📰 So'nggi xabarlar")
async def cmd_latest_news(message: Message):
    articles = await api_get("/api/news", {"limit": 5})
    await send_articles(message, articles, "Hozircha yangiliklar yo‘q.")


@dp.message(Command("kategoriyalar"))
@dp.message(F.text == "📂 Kategoriyalar")
async def cmd_categories(message: Message):
    cats = await api_get("/api/categories")
    if not cats:
        await message.answer("Kategoriyalar yuklanmadi.")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=c["name"], callback_data=f"cat:{c['slug']}")]
        for c in cats
    ])
    await message.answer("📂 Kategoriyani tanlang:", reply_markup=keyboard)


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


@dp.message(Command("saqlanganlar"))
@dp.message(F.text == "⭐ Saqlanganlar")
async def saved_articles(message: Message):
    saved = storage.get_saved(message.chat.id)
    if not saved:
        await message.answer("Saqlangan maqolalar yo'q. Yangilik ostidagi ⭐ Saqlash tugmasini bosing.")
        return
    lines = [
        f"• <a href=\"{SITE_URL}/maqola/{slug}\">{html.escape(title)}</a>"
        for slug, title in saved[-15:]
    ]
    await message.answer(
        "<b>⭐ Saqlangan maqolalaringiz:</b>\n\n" + "\n".join(lines),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


@dp.message(F.text == "🔔 Xabarnomalar")
async def toggle_notifications(message: Message):
    enabled = storage.toggle_notifications(message.chat.id)
    if enabled:
        await message.answer("🔔 Bildirishnomalar yoqildi — eng muhim yangiliklar chiqqanda xabar beramiz.")
    else:
        await message.answer("🔕 Bildirishnomalar o'chirildi.")


@dp.message(Command("qidiruv"))
@dp.message(F.text == "🔍 Qidiruv")
async def ask_search(message: Message):
    awaiting_search.add(message.chat.id)
    await message.answer("🔍 Qidiruv so'zini yozing (masalan: <i>Husanov</i> yoki <i>Real Madrid</i>):", parse_mode="HTML")


@dp.message(F.text)
async def handle_text(message: Message):
    if message.chat.id in awaiting_search:
        awaiting_search.discard(message.chat.id)
        articles = await api_get("/api/news/search", {"q": message.text})
        await send_articles(message, articles, f"«{message.text}» bo'yicha yangilik topilmadi.")
    else:
        await message.answer("Menyudan birini tanlang 👇", reply_markup=MENU)


# ===================== RUNNER =====================

async def main():
    if not BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN is empty. Skipping Telegram Bot startup.")
        return

    runtime_lock = try_runtime_lock(BOT_LOCK_ID)
    while not runtime_lock.acquired:
        print("🤖 Bot boshqa instance'da ishlayapti; navbat kutilmoqda...")
        await asyncio.sleep(15)
        runtime_lock = try_runtime_lock(BOT_LOCK_ID)

    bot = Bot(token=BOT_TOKEN)
    try:
        print("🤖 Bot ishga tushdi (yagona faol instance).")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        release_runtime_lock(runtime_lock)


if __name__ == "__main__":
    asyncio.run(main())
