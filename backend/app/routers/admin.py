"""Admin API — tasdiqlash, tahrirlash, o'chirish, Telegramga yuborish, statistika.
Barcha so'rovlar X-Admin-Token sarlavhasini talab qiladi."""

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import Article, Category
from ..schemas import ArticleOut, ArticleUpdate, StatsOut
from ..services.telegram import send_to_channel

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def get_article(db: Session, article_id: int) -> Article:
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Maqola topilmadi")
    return article


@router.get("/articles", response_model=list[ArticleOut])
def list_articles(db: Session = Depends(get_db), status: str | None = None, limit: int = 50, offset: int = 0):
    query = db.query(Article)
    if status:
        query = query.filter(Article.status == status)
    return query.order_by(Article.created_at.desc()).offset(offset).limit(limit).all()


@router.put("/articles/{article_id}", response_model=ArticleOut)
def update_article(article_id: int, data: ArticleUpdate, db: Session = Depends(get_db)):
    article = get_article(db, article_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(article, field, value)
    db.commit()
    db.refresh(article)
    return article


@router.post("/articles/{article_id}/approve", response_model=ArticleOut)
def approve_article(article_id: int, db: Session = Depends(get_db)):
    """Maqolani tasdiqlash — saytga chiqariladi."""
    article = get_article(db, article_id)
    article.status = "published"
    article.published_at = datetime.utcnow()
    db.commit()
    db.refresh(article)
    return article


@router.post("/articles/{article_id}/reject", response_model=ArticleOut)
def reject_article(article_id: int, db: Session = Depends(get_db)):
    article = get_article(db, article_id)
    article.status = "rejected"
    db.commit()
    db.refresh(article)
    return article


@router.post("/articles/{article_id}/telegram")
def send_article_to_telegram(article_id: int, background: BackgroundTasks, db: Session = Depends(get_db)):
    """Maqolani Telegram kanaliga yuborish."""
    article = get_article(db, article_id)
    try:
        send_to_channel(article)
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error))
    article.sent_to_telegram = True
    db.commit()
    return {"ok": True, "xabar": "Telegram kanaliga yuborildi"}


@router.delete("/articles/{article_id}")
def delete_article(article_id: int, db: Session = Depends(get_db)):
    article = get_article(db, article_id)
    db.delete(article)
    db.commit()
    return {"ok": True}


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)):
    by_category = {}
    for category in db.query(Category).all():
        count = db.query(Article).filter(
            Article.category_id == category.id, Article.status == "published"
        ).count()
        if count:
            by_category[category.name] = count

    return StatsOut(
        jami=db.query(Article).count(),
        kutilmoqda=db.query(Article).filter(Article.status == "pending").count(),
        chop_etilgan=db.query(Article).filter(Article.status == "published").count(),
        rad_etilgan=db.query(Article).filter(Article.status == "rejected").count(),
        telegramga_yuborilgan=db.query(Article).filter(Article.sent_to_telegram.is_(True)).count(),
        kategoriyalar_boyicha=by_category,
    )
