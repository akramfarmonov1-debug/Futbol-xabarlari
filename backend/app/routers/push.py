from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import ADMIN_TOKEN
from ..database import get_db
from ..services.push_service import (
    get_subscribers_count,
    remove_subscription,
    save_subscription,
    send_web_push,
)

router = APIRouter(prefix="/api/push", tags=["push"])


class SubscribeRequest(BaseModel):
    endpoint: str
    p256dh: str | None = ""
    auth: str | None = ""


class SendPushRequest(BaseModel):
    title: str
    body: str
    url: str | None = "/"
    icon: str | None = "/icon-192"


@router.post("/subscribe")
def subscribe_push(
    data: SubscribeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Brauzerdan kelgan push obunasini saqlash."""
    if not data.endpoint:
        raise HTTPException(status_code=400, detail="Endpoint bo'sh bo'lishi mumkin emas")

    user_agent = request.headers.get("user-agent", "")
    sub = save_subscription(
        db,
        endpoint=data.endpoint,
        p256dh=data.p256dh or "",
        auth=data.auth or "",
        user_agent=user_agent,
    )
    return {
        "status": "ok",
        "id": sub.id,
        "message": "Obuna muvaffaqiyatli saqlandi",
    }


@router.post("/unsubscribe")
def unsubscribe_push(
    data: SubscribeRequest,
    db: Session = Depends(get_db),
):
    """Push obunasini o'chirish."""
    success = remove_subscription(db, endpoint=data.endpoint)
    return {"status": "ok", "deleted": success}


@router.get("/status")
def push_status(db: Session = Depends(get_db)):
    """Obunachilar soni."""
    count = get_subscribers_count(db)
    return {"status": "ok", "subscribers_count": count}


@router.post("/broadcast")
def admin_broadcast_push(
    payload: SendPushRequest,
    db: Session = Depends(get_db),
    x_admin_token: str | None = Header(default=None),
):
    """Admin uchun: barcha obunachilarga bildirishnoma yuborish."""
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Noto'g'ri admin tokeni")

    res = send_web_push(
        db,
        title=payload.title,
        body=payload.body,
        url=payload.url or "/",
        icon=payload.icon or "/icon-192",
    )
    return {"status": "ok", "result": res}
