"""Legionerlar API — O'zbekistonlik xorijdagi futbolchilar ma'lumotlari."""

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import legionnaires
from ..services.legionnaires_alert import broadcast_legionnaire_alert

router = APIRouter(prefix="/api/legionnaires", tags=["legionnaires"])


class LegionnaireAlertRequest(BaseModel):
    event_key: str
    player_name: str
    player_slug: str
    club: str
    event_type: str  # goal, assist, lineup, result
    headline: str
    detail: str = ""
    match_opponent: str = ""
    score: str = ""
    minute: str = ""
    image_url: str | None = None


@router.get("")
def list_legionnaires(db: Session = Depends(get_db)):
    """O'zbekistonlik legionerlar va ularga oid yangiliklar xulosasi."""
    return legionnaires.get_legionnaires_summary(db)


@router.get("/{slug}")
def legionnaire_detail(slug: str, db: Session = Depends(get_db)):
    """Bitta legionerning to'liq profili va barcha xabarlari."""
    result = legionnaires.get_legionnaire_detail(db, slug)
    if result is None:
        raise HTTPException(status_code=404, detail="Legioner topilmadi")
    return result


@router.post("/alert")
def send_legionnaire_alert(
    payload: LegionnaireAlertRequest,
    db: Session = Depends(get_db),
):
    """Tezkor legioner voqeasi haqida Telegram va Web Push bildirishnomasi yuborish."""
    return broadcast_legionnaire_alert(
        db=db,
        event_key=payload.event_key,
        player_name=payload.player_name,
        player_slug=payload.player_slug,
        club=payload.club,
        event_type=payload.event_type,
        headline=payload.headline,
        detail=payload.detail,
        match_opponent=payload.match_opponent,
        score=payload.score,
        minute=payload.minute,
        image_url=payload.image_url,
    )
