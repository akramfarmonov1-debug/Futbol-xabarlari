"""Kunlik dayjest — har kuni DAILY_DIGEST_TIME (Toshkent vaqti) da Telegram
kanaliga bugungi muhim yangiliklarni bitta xulosa posti sifatida yuboradi.

Bir kunda faqat bir marta yuboriladi (``daily_digest_log`` jadvali orqali
nazorat qilinadi) va PostgreSQL advisory lock ko'p instance'da takror
yuborilishni oldini oladi. Lokal SQLite muhitida lock no-op hisoblanadi.
"""

import asyncio
import html
import re
from datetime import date, datetime, time, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from ..config import (
    DAILY_DIGEST,
    DAILY_DIGEST_INTERVAL,
    DAILY_DIGEST_LIMIT,
    DAILY_DIGEST_MIN_IMPORTANCE,
    DAILY_DIGEST_TIME,
    DAILY_DIGEST_WINDOW_MINUTES,
    FRONTEND_ORIGIN,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHANNEL_ID,
)
from ..database import SessionLocal
from ..models import Article, DailyDigestLog
from ..utils import safe_print
from .runtime_lock import DIGEST_LOCK_ID, release_runtime_lock, try_runtime_lock

# Toshkent vaqti = UTC+5
TASHKENT_TZ = timezone(timedelta(hours=5))


def now_tashkent() -> datetime:
    """Joriy vaqtni Toshkent vaqti bo'yicha (timezone-siz, naiv) qaytaradi."""
    return datetime.now(TASHKENT_TZ).replace(tzinfo=None)


def _parse_time(value: str) -> time:
    try:
        hour, minute = value.strip().split(":")
        return time(int(hour), int(minute))
    except (ValueError, AttributeError):
        return time(9, 0)


def is_digest_time(
    moment: datetime | None = None,
    target: str | None = None,
    window_minutes: int | None = None,
) -> bool:
    """Joriy vaqt maqsadli dayjest vaqti atrofidagi oynada ekanini tekshiradi.

    Misol: target="09:00", window=30 -> 09:00..09:30 oralig'i True.
    """
    moment = moment or now_tashkent()
    target_time = _parse_time(target or DAILY_DIGEST_TIME)
    window = timedelta(
        minutes=(
            window_minutes
            if window_minutes is not None
            else DAILY_DIGEST_WINDOW_MINUTES
        )
    )
    start = datetime.combine(moment.date(), target_time)
    return start <= moment <= start + window


MONTH_NAMES_UZ = {
    1: "yanvar", 2: "fevral", 3: "mart", 4: "aprel", 5: "may", 6: "iyun",
    7: "iyul", 8: "avgust", 9: "sentyabr", 10: "oktyabr", 11: "noyabr", 12: "dekabr",
}
NUM_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


def _digest_articles(
    db: Session,
    day: date,
    limit: int = DAILY_DIGEST_LIMIT,
    min_importance: int = DAILY_DIGEST_MIN_IMPORTANCE,
) -> list[Article]:
    """Oxirgi 24 soat ichida chop etilgan, eng muhim maqolalarni tanlaydi."""
    start = datetime.combine(day - timedelta(days=1), time(6, 0))
    end = datetime.combine(day, time(23, 59, 59))
    articles = (
        db.query(Article)
        .filter(
            Article.status == "published",
            Article.published_at >= start,
            Article.published_at <= end,
            Article.importance >= min_importance,
        )
        .order_by(Article.importance.desc(), Article.published_at.desc())
        .limit(limit)
        .all()
    )
    if not articles:
        articles = (
            db.query(Article)
            .filter(
                Article.status == "published",
                Article.published_at >= start,
                Article.published_at <= end,
            )
            .order_by(Article.importance.desc(), Article.published_at.desc())
            .limit(limit)
            .all()
        )
    return articles


def _truncate(text: str, limit: int) -> str:
    clean = re.sub(r"\s+", " ", text or "").strip()
    if len(clean) <= limit:
        return clean
    return clean[: max(1, limit - 1)].rsplit(" ", 1)[0].rstrip(".,;:") + "…"


def build_digest_message(articles: list[Article], day: date) -> str:
    """Maqolalar ro'yxatidan HTML formatdagi jozibador dayjest xabari tayyorlaydi."""
    if not articles:
        return ""
    month_str = MONTH_NAMES_UZ.get(day.month, "")
    date_str = f"{day.day}-{month_str.capitalize()}, {day.year}"
    lines = [
        "🌅 <b>KUNNING ENG MUHIM FUTBOL XABARLARI</b>",
        f"🗓 <i>{date_str}</i>",
        "━━━━━━━━━━━━━━━━━━",
        "",
    ]
    for index, article in enumerate(articles):
        num_icon = NUM_EMOJIS[index] if index < len(NUM_EMOJIS) else f"<b>{index+1}.</b>"
        category = article.category.name if article.category else "Futbol"
        title = html.escape(_truncate(article.title, 160))
        url = f"{FRONTEND_ORIGIN}/maqola/{article.slug}"
        stars = "⭐" * max(1, min(5, article.importance))
        lines.append(
            f"{num_icon} <b>{title}</b>\n"
            f"   {stars} • 📂 {html.escape(category)}\n"
            f"   👉 <a href=\"{url}\">Batafsil o'qish</a>\n"
        )
    lines.extend([
        "━━━━━━━━━━━━━━━━━━",
        f"🌐 <b>Barcha yangiliklar:</b> <a href=\"{FRONTEND_ORIGIN}\">futbolxabar.uz</a>",
        "#Dayjest #FutbolXabar",
    ])
    return "\n".join(lines)


def _send_digest(message: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        raise RuntimeError("TELEGRAM_BOT_TOKEN yoki TELEGRAM_CHANNEL_ID sozlanmagan")
    channel_id = TELEGRAM_CHANNEL_ID.strip()
    if not channel_id.startswith("@") and not channel_id.startswith("-"):
        channel_id = f"@{channel_id}"
    api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    payload = {
        "chat_id": channel_id,
        "text": message,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
    }
    response = httpx.post(f"{api}/sendMessage", json=payload, timeout=30)
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram xatosi: {data.get('description')}")


def send_daily_digest(db: Session, moment: datetime | None = None) -> bool:
    """Shartlar bajarilsa kanalga kunlik dayjest yuboradi.

    Qaytish qiymati: yuborildi (True) yoki o'tkazib yuborildi (False).
    """
    moment = moment or now_tashkent()
    if not DAILY_DIGEST or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        return False
    if not is_digest_time(moment):
        return False

    lock = try_runtime_lock(DIGEST_LOCK_ID)
    if not lock.acquired:
        safe_print("⏭ Dayjest boshqa instance'da ishlayapti; o'tkazib yuborildi.")
        return False
    try:
        day = moment.date()
        already_sent = (
            db.query(DailyDigestLog)
            .filter(DailyDigestLog.digest_date == day.isoformat())
            .first()
        )
        if already_sent:
            return False

        articles = _digest_articles(db, day)
        if not articles:
            # Bugun hali muhim yangilik yo'q — keyingi tekshiruvlarda qayta uriniladi.
            safe_print("📋 Dayjest: bugungi muhim yangiliklar topilmadi.")
            return False

        message = build_digest_message(articles, day)
        _send_digest(message)
        db.add(
            DailyDigestLog(
                digest_date=day.isoformat(),
                articles_count=len(articles),
            )
        )
        db.commit()
        safe_print(f"📋 Kunlik dayjest yuborildi ({len(articles)} ta yangilik).")
        return True
    finally:
        release_runtime_lock(lock)


async def run_digest_loop() -> None:
    """Fon vazifasi: har DAILY_DIGEST_INTERVAL soniyada dayjestni tekshiradi."""
    while True:
        try:
            db = SessionLocal()
            try:
                send_daily_digest(db)
            finally:
                db.close()
        except Exception as error:
            safe_print(f"❌ Kunlik dayjest xatosi: {error}")
        await asyncio.sleep(DAILY_DIGEST_INTERVAL)
