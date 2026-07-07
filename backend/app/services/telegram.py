"""Telegram kanaliga post yuborish (Bot API orqali)."""

import html

import httpx

from ..config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, FRONTEND_ORIGIN
from ..models import Article


def format_post(article: Article) -> str:
    stars = "⭐" * max(1, min(5, article.importance))
    tags = " ".join(f"#{t.replace(' ', '_')}" for t in (article.tags or [])[:5])
    category = article.category.name if article.category else "AI"
    return (
        f"<b>{html.escape(article.title)}</b>\n\n"
        f"{html.escape(article.summary)}\n\n"
        f"💡 <i>{html.escape(article.practical_note)}</i>\n\n"
        f"📂 {html.escape(category)} | Ahamiyati: {stars}\n"
        f"🔗 <a href=\"{article.original_url}\">Asl manba</a> | "
        f"<a href=\"{FRONTEND_ORIGIN}/maqola/{article.slug}\">Batafsil o'qish</a>\n"
        f"{tags}"
    )



def send_to_channel(article: Article) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        raise RuntimeError("TELEGRAM_BOT_TOKEN yoki TELEGRAM_CHANNEL_ID sozlanmagan")

    api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    text = format_post(article)

    if article.image_url:
        payload = {
            "chat_id": TELEGRAM_CHANNEL_ID,
            "photo": article.image_url,
            "caption": text[:1024],
            "parse_mode": "HTML",
        }
        response = httpx.post(f"{api}/sendPhoto", json=payload, timeout=30)
    else:
        payload = {
            "chat_id": TELEGRAM_CHANNEL_ID,
            "text": text[:4096],
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
        response = httpx.post(f"{api}/sendMessage", json=payload, timeout=30)

    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram xatosi: {data.get('description')}")
