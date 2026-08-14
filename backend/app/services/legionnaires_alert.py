import html
import os
from datetime import datetime
import httpx
from sqlalchemy.orm import Session

from ..config import FRONTEND_ORIGIN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
from ..models import LegionnaireAlertLog
from .push_service import send_web_push


def format_legionnaire_post(
    player_name: str,
    club: str,
    event_type: str,
    headline: str,
    detail: str,
    match_opponent: str = "",
    score: str = "",
    minute: str = "",
) -> str:
    """Telegram uchun emojilar bilan boyitilgan tezkor legioner xabari."""
    event_icons = {
        "goal": "⚽️🔥 <b>GOOOOL!</b>",
        "assist": "🎯⚡️ <b>GOLGA HAMMUALLIF!</b>",
        "lineup": "📋📌 <b>ASOSIY TARKIBDA!</b>",
        "result": "🏁 <b>O‘YIN YAKUNLANDI!</b>",
    }
    header = event_icons.get(event_type, "⚡️ <b>TEZKOR XABAR!</b>")

    lines = [
        f"{header} <b>{html.escape(player_name.upper())}!</b> 🇺🇿",
        "",
        f"🏆 <b>{html.escape(club)}</b>" + (f" vs <b>{html.escape(match_opponent)}</b>" if match_opponent else ""),
    ]
    if score:
        lines.append(f"📊 <b>Hisob:</b> {score}")
    if minute:
        lines.append(f"⏱ <b>Daqiqa:</b> {minute}")

    lines.append("")
    lines.append(f"<b>{html.escape(headline)}</b>")
    if detail:
        lines.append(html.escape(detail))

    tag = "#" + "".join(player_name.split())
    club_tag = "#" + "".join(club.split())
    lines.append(f"\n{tag}  {club_tag}  #Legionerlarimiz  #Uzbekistan")

    return "\n".join(lines)


def broadcast_legionnaire_alert(
    db: Session,
    event_key: str,
    player_name: str,
    player_slug: str,
    club: str,
    event_type: str,
    headline: str,
    detail: str,
    match_opponent: str = "",
    score: str = "",
    minute: str = "",
    image_url: str | None = None,
) -> dict:
    """Legionerning goli/tarkibi haqida Telegram va Web Push orqali bir lahzada ogohlantirish."""
    # 1. Dublikat tekshiruvi
    existing = db.query(LegionnaireAlertLog).filter(LegionnaireAlertLog.event_key == event_key).first()
    if existing:
        return {"status": "already_sent", "event_key": event_key}

    # 2. Telegram matni va tugmalari
    post_text = format_legionnaire_post(
        player_name=player_name,
        club=club,
        event_type=event_type,
        headline=headline,
        detail=detail,
        match_opponent=match_opponent,
        score=score,
        minute=minute,
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {
                    "text": "🇺🇿 Legionerlar sahifasi",
                    "url": f"{FRONTEND_ORIGIN}/legionerlar",
                },
                {
                    "text": "📊 Jonli hisoblar",
                    "url": f"{FRONTEND_ORIGIN}/jadval",
                },
            ],
            [
                {
                    "text": "🤖 Futbol Xabar Boti",
                    "url": "https://t.me/Futbolxabari_bot",
                }
            ],
        ]
    }

    tg_success = False
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID:
        channel_id = TELEGRAM_CHANNEL_ID.strip()
        if not channel_id.startswith("@") and not channel_id.startswith("-"):
            channel_id = f"@{channel_id}"

        api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
        try:
            if image_url and image_url.startswith("http"):
                payload = {
                    "chat_id": channel_id,
                    "photo": image_url,
                    "caption": post_text[:1024],
                    "parse_mode": "HTML",
                    "reply_markup": reply_markup,
                }
                resp = httpx.post(f"{api}/sendPhoto", json=payload, timeout=20)
                if resp.status_code == 200 and resp.json().get("ok"):
                    tg_success = True
            
            if not tg_success:
                payload = {
                    "chat_id": channel_id,
                    "text": post_text[:4096],
                    "parse_mode": "HTML",
                    "reply_markup": reply_markup,
                }
                resp = httpx.post(f"{api}/sendMessage", json=payload, timeout=20)
                if resp.status_code == 200 and resp.json().get("ok"):
                    tg_success = True
        except Exception as tg_err:
            print(f"  ⚠ Legioner xabarini Telegramga yuborishda xatolik: {tg_err}")

    # 3. Web Push yuborish
    push_title = f"⚽️ {player_name}: {headline[:40]}" if event_type == "goal" else f"⚡️ {player_name} ({club})"
    push_result = send_web_push(
        db,
        title=push_title,
        body=detail[:150] if detail else headline[:150],
        url=f"/legionerlar",
        icon="/icon-192",
    )

    # 4. Logga qayd qilish
    log_entry = LegionnaireAlertLog(
        event_key=event_key,
        player_slug=player_slug,
        event_type=event_type,
        message=headline[:1000],
        created_at=datetime.utcnow(),
    )
    db.add(log_entry)
    db.commit()

    return {
        "status": "sent",
        "event_key": event_key,
        "telegram_sent": tg_success,
        "push_result": push_result,
    }
