"""Telegram kanaliga post yuborish (Bot API orqali)."""

import html

import httpx

from ..config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, FRONTEND_ORIGIN
from ..models import Article


def format_post(article: Article, max_caption_len: int = None) -> str:
    stars = "⭐" * max(1, min(5, article.importance))
    tags = " ".join(f"#{t.replace(' ', '_')}" for t in (article.tags or [])[:5])
    category = article.category.name if article.category else "AI"
    
    title = article.title
    summary = article.summary
    practical_note = article.practical_note or ""

    # Caption cheklovini hisobga olish (HTML teglar buzilmasligi uchun)
    if max_caption_len:
        # Havolalar, teglar va formatlar uchun taxminan 450 belgi zaxira qilamiz
        reserved_len = 450
        available_len = max_caption_len - reserved_len - len(title) - len(practical_note) - len(category)
        if available_len < 100:
            available_len = 100
        if len(summary) > available_len:
            summary = summary[:available_len - 3] + "..."

    return (
        f"<b>{html.escape(title)}</b>\n\n"
        f"{html.escape(summary)}\n\n"
        f"💡 <i>{html.escape(practical_note)}</i>\n\n"
        f"📂 {html.escape(category)} | Ahamiyati: {stars}\n"
        f"🔗 <a href=\"{article.original_url}\">Asl manba</a> | "
        f"<a href=\"{FRONTEND_ORIGIN}/maqola/{article.slug}\">Batafsil o'qish</a>\n"
        f"{tags}"
    )


def send_to_channel(article: Article) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        raise RuntimeError("TELEGRAM_BOT_TOKEN yoki TELEGRAM_CHANNEL_ID sozlanmagan")

    api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

    if article.image_url:
        text = format_post(article, max_caption_len=1024)
        payload = {
            "chat_id": TELEGRAM_CHANNEL_ID,
            "photo": article.image_url,
            "caption": text,
            "parse_mode": "HTML",
        }
        response = httpx.post(f"{api}/sendPhoto", json=payload, timeout=30)
    else:
        text = format_post(article, max_caption_len=4096)
        payload = {
            "chat_id": TELEGRAM_CHANNEL_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
        response = httpx.post(f"{api}/sendMessage", json=payload, timeout=30)

    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram xatosi: {data.get('description')}")
