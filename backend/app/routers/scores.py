from fastapi import APIRouter, HTTPException

from ..services import scores

router = APIRouter(prefix="/api/scores", tags=["scores"])


@router.get("/today")
def today_matches():
    """Bugungi va ertangi o'yinlar (turnirlar bo'yicha guruhlangan)."""
    return scores.get_today_matches()


@router.get("/competitions")
def competitions():
    """Jadval mavjud turnirlar ro'yxati."""
    return scores.list_competitions()


@router.get("/standings/{code}")
def standings(code: str):
    """Bitta turnirning joriy jadvali."""
    result = scores.get_standings(code.upper())
    if result is None:
        raise HTTPException(status_code=404, detail="Jadval topilmadi yoki API kaliti sozlanmagan")
    return result
