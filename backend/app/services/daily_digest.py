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


def _digest_articles(
    db: Session,
    day: date,
    limit: int = DAILY_DIGEST_LIMIT,
    min_importance: int = DAILY_DIGEST_MIN_IMPORTANCE,
) -> list[Article]:
    """Kun davomida chop etilgan, muhimligi yetarli maqolalarni tanlaydi."""
    start = datetime.combine(day, time.min)
    end = start + timedelta(days=1)
    return (
        db.query(Article)
        .filter(
            Article.status == "published",
            Article.published_at >= start,
            Article.published_at < end,
            Article.importance >= min_importance,
        )
        .order_by(Article.importance.desc(), Article.published_at.desc())
        .limit(limit)
        .all()
    )


def _truncate(text: str, limit: int) -> str:
    clean = re.sub(r"\s+", " ", text or "").strip()
    if len(clean) <= limit:
        return clean
    return clean[: max(1, limit - 1)].rsplit(" ", 1)[0].rstrip(".,;:") + "…"


def build_digest_message(articles: list[Article], day: date) -> str:
    """Maqolalar ro'yxatidan HTML formatdagi dayjest xabari tayyorlaydi."""
    if not articles:
        return ""
    lines = [
        "📋 <b>Futbol Xabar — kunning dayjesti</b>",
        "",
        f"🗓 {day.strftime('%d %B %Y')} uchun eng muhim yangiliklar:",
        "",
    ]
    for index, article in enumerate(articles, 1):
        category = article.category.name if article.category else "Futbol"
        title = html.escape(_truncate(article.title, 160))
        url = f"{FRONTEND_ORIGIN}/maqola/{article.slug}"
        stars = "⭐" * max(1, min(5, article.importance))
        lines.append(
            f"<b>{index}. {title}</b>\n"
            f"    {stars} • 📂 {html.escape(category)}\n"
            f"    <a href=\"{url}\">Saytda o'qish</a>"
        )
    return "\n".join(lines)


def _send_digest(message: str) -> None:
    api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
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
