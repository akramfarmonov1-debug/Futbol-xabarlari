"""Telegram kanaliga post yuborish (Bot API orqali)."""

import html
import re

import httpx

from ..config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, FRONTEND_ORIGIN
from ..models import Article


def _truncate(text: str, limit: int) -> str:
    clean = re.sub(r"\s+", " ", text or "").strip()
    if len(clean) <= limit:
        return clean
    shortened = clean[: max(1, limit - 1)].rsplit(" ", 1)[0].rstrip(".,;:")
    return f"{shortened}…"


def _hashtag(value: str) -> str:
    """Erkin AI tegini Telegram uchun o'qilishi oson CamelCase hashtag qiladi."""
    value = re.sub(r"^#+", "", str(value or "").strip())
    words = re.findall(r"[^\W_]+", value.replace("’", "").replace("'", ""), re.UNICODE)
    if not words:
        return ""
    tag = "".join(word[:1].upper() + word[1:].lower() for word in words)
    return f"#{tag[:45]}"


def _post_tags(article: Article) -> str:
    category = article.category.name if article.category else "Jahon futboli"
    values = [category, *(article.tags or [])]
    tags = []
    seen = set()
    for value in values:
        tag = _hashtag(value)
        key = tag.casefold()
        if tag and key not in seen:
            tags.append(tag)
            seen.add(key)
        if len(tags) == 3:
            break
    return "  ".join(tags)


def _importance_label(importance: int) -> str:
    if importance >= 5:
        return "🔥 <b>ASOSIY XABAR</b>"
    if importance >= 4:
        return "⚡️ <b>MUHIM XABAR</b>"
    return "⚽️ <b>FUTBOL XABARI</b>"


def _build_post(article: Article, summary: str, practical_note: str) -> str:
    category = article.category.name if article.category else "Jahon futboli"
    source = article.source_name or "Ochiq manba"
    blocks = [
        _importance_label(article.importance),
        f"<b>{html.escape(_truncate(article.title, 220))}</b>",
        html.escape(summary),
    ]
    if practical_note:
        blocks.append(
            "💡 <b>Nega muhim?</b>\n"
            f"<i>{html.escape(practical_note)}</i>"
        )
    blocks.extend(
        [
            f"🗞 {html.escape(source)}  •  📂 {html.escape(category)}",
            _post_tags(article),
        ]
    )
    return "\n\n".join(block for block in blocks if block)


def format_post(article: Article, max_caption_len: int = 1024) -> str:
    summary_limit = 480 if max_caption_len <= 1024 else 1200
    note_limit = 220 if max_caption_len <= 1024 else 500
    summary = _truncate(article.summary, summary_limit)
    practical_note = _truncate(article.practical_note or "", note_limit)
    post = _build_post(article, summary, practical_note)

    # Telegram limitni HTML teglar va entity'lar yechilgandan keyin hisoblaydi.
    def visible_length(value: str) -> int:
        return len(html.unescape(re.sub(r"<[^>]+>", "", value)))

    overflow = visible_length(post) - max_caption_len
    if overflow > 0:
        summary = _truncate(summary, max(120, len(summary) - overflow - 20))
        post = _build_post(article, summary, practical_note)
    overflow = visible_length(post) - max_caption_len
    if overflow > 0 and practical_note:
        practical_note = _truncate(
            practical_note,
            max(80, len(practical_note) - overflow - 20),
        )
        post = _build_post(article, summary, practical_note)
    return post


def article_buttons(article: Article) -> dict:
    return {
        "inline_keyboard": [
            [
                {
                    "text": "📖 Saytda o'qish",
                    "url": f"{FRONTEND_ORIGIN}/maqola/{article.slug}",
                },
                {"text": "🔗 Asl manba", "url": article.original_url},
            ]
        ]
    }


def send_to_channel(article: Article) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        raise RuntimeError("TELEGRAM_BOT_TOKEN yoki TELEGRAM_CHANNEL_ID sozlanmagan")

    channel_id = TELEGRAM_CHANNEL_ID.strip()
    if not channel_id.startswith("@") and not channel_id.startswith("-"):
        channel_id = f"@{channel_id}"

    api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

    sent = False
    # Agar maqolada rasm bo'lsa, avval rasm bilan yuborishga urinamiz
    if article.image_url and article.image_url.startswith("http"):
        try:
            text = format_post(article, max_caption_len=1024)
            payload = {
                "chat_id": channel_id,
                "photo": article.image_url,
                "caption": text,
                "parse_mode": "HTML",
                "reply_markup": article_buttons(article),
            }
            response = httpx.post(f"{api}/sendPhoto", json=payload, timeout=25)
            data = response.json()
            if data.get("ok"):
                sent = True
            else:
                print(
                    f"  ⚠ Telegram sendPhoto rad etildi ({data.get('description')}), "
                    f"matn ko'rinishida yuborilmoqda..."
                )
        except Exception as photo_err:
            print(f"  ⚠ Telegram photo so'rovida xatolik: {photo_err}")

    # Agar rasm bo'lmasa yoki rasm yuborishda xatolik bo'lsa, to'liq matn bilan yuboramiz
    if not sent:
        text = format_post(article, max_caption_len=4096)
        payload = {
            "chat_id": channel_id,
            "text": text,
            "parse_mode": "HTML",
            "link_preview_options": {"is_disabled": True},
            "reply_markup": article_buttons(article),
        }
        response = httpx.post(f"{api}/sendMessage", json=payload, timeout=25)
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram API xatosi: {data.get('description')}")
