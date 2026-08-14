"""Legionerlar API — O'zbekistonlik xorijdagi futbolchilar ma'lumotlari."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import legionnaires

router = APIRouter(prefix="/api/legionnaires", tags=["legionnaires"])


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
