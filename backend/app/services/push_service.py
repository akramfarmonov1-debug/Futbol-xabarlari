import ipaddress
import json
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import httpx
from sqlalchemy.orm import Session

from ..config import VAPID_CLAIMS_SUB, VAPID_PRIVATE_KEY
from ..models import PushSubscription

try:
    from pywebpush import WebPushException, webpush
except ImportError:  # pragma: no cover
    WebPushException = Exception
    webpush = None


def is_deliverable_push_url(endpoint: str) -> bool:
    """Faqat xavfsiz tashqi HTTPS Web Push URL manzillariga tarmoq so'rovi yuborishga ruxsat beradi (SSRF himoyasi)."""
    if not endpoint or not endpoint.startswith("https://"):
        return False
    try:
        parsed = urlparse(endpoint)
    except Exception:
        return False
    host = (parsed.hostname or "").strip().lower()
    if not host or host in {"localhost", "0.0.0.0"} or host.endswith((".local", ".internal")):
        return False
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    except ValueError:
        # Domen nomi bo'lsa kamida bitta nuqta bo'lishi kerak
        if "." not in host:
            return False
    return True


def is_valid_subscription_endpoint(endpoint: str) -> bool:
    """Obuna endpointi haqiqiy HTTPS Web Push URL yoki brauzer fallback identifikatori ekanini tekshiradi."""
    if not endpoint:
        return False
    if endpoint.startswith("browser_"):
        return len(endpoint) <= 120
    return is_deliverable_push_url(endpoint)


def save_subscription(
    db: Session,
    endpoint: str,
    p256dh: str = "",
    auth: str = "",
    user_agent: str = "",
) -> PushSubscription:
    """Yangi obunani saqlaydi yoki mavjudini yangilaydi."""
    sub = db.query(PushSubscription).filter(PushSubscription.endpoint == endpoint).first()
    if not sub:
        sub = PushSubscription(
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            user_agent=user_agent[:500] if user_agent else "",
            created_at=datetime.utcnow(),
        )
        db.add(sub)
    else:
        sub.p256dh = p256dh
        sub.auth = auth
        if user_agent:
            sub.user_agent = user_agent[:500]
    db.commit()
    db.refresh(sub)
    return sub


def remove_subscription(db: Session, endpoint: str) -> bool:
    """Obunani o'chiradi."""
    sub = db.query(PushSubscription).filter(PushSubscription.endpoint == endpoint).first()
    if sub:
        db.delete(sub)
        db.commit()
        return True
    return False


def get_subscribers_count(db: Session) -> int:
    return db.query(PushSubscription).count()


def send_web_push(
    db: Session,
    title: str,
    body: str,
    url: str = "/",
    icon: str = "/icon-192",
) -> dict:
    """Barcha faol brauzer obunachilariga Web Push yuboradi."""
    subscriptions = db.query(PushSubscription).all()
    if not subscriptions:
        return {"total": 0, "success": 0, "failed": 0}

    payload = json.dumps({
        "title": title,
        "body": body,
        "url": url,
        "icon": icon,
    })

    success_count = 0
    failed_count = 0
    to_delete = []

    with httpx.Client(timeout=10) as client:
        for sub in subscriptions:
            if not is_deliverable_push_url(sub.endpoint):
                failed_count += 1
                continue
            try:
                if webpush is not None and VAPID_PRIVATE_KEY and sub.p256dh and sub.auth:
                    try:
                        webpush(
                            subscription_info={
                                "endpoint": sub.endpoint,
                                "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                            },
                            data=payload,
                            vapid_private_key=VAPID_PRIVATE_KEY,
                            vapid_claims={"sub": VAPID_CLAIMS_SUB},
                            ttl=86400,
                        )
                        success_count += 1
                    except WebPushException as exc:
                        status_code = getattr(getattr(exc, "response", None), "status_code", None)
                        if status_code in (404, 410):
                            to_delete.append(sub.id)
                        failed_count += 1
                    continue

                # VAPID sozlanmagan muhitlar uchun fallback HTTP POST
                resp = client.post(
                    sub.endpoint,
                    content=payload.encode("utf-8"),
                    headers={"Content-Type": "application/json", "TTL": "86400"},
                )
                if resp.status_code in (200, 201, 202):
                    success_count += 1
                elif resp.status_code in (404, 410):
                    # Obuna eskirgan yoki foydalanuvchi ruxsatni bekor qilgan
                    to_delete.append(sub.id)
                    failed_count += 1
                else:
                    failed_count += 1
            except Exception:
                failed_count += 1

    if to_delete:
        db.query(PushSubscription).filter(PushSubscription.id.in_(to_delete)).delete(synchronize_session=False)
        db.commit()

    return {
        "total": len(subscriptions),
        "success": success_count,
        "failed": failed_count,
    }
