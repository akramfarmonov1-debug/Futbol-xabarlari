import json
from datetime import datetime
from typing import Optional
import httpx
from sqlalchemy.orm import Session

from ..models import PushSubscription


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
            try:
                # Oddiy push endpointga xabar yuborish
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
