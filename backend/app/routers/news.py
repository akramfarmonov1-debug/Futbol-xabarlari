import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Article, Category
from ..schemas import ArticleOut, SitemapArticleOut
from ..tags import canonical_tag, tag_key

router = APIRouter(prefix="/api/news", tags=["news"])


def published(db: Session):
    return db.query(Article).filter(Article.status == "published")


@router.get("", response_model=list[ArticleOut])
def latest_news(
    db: Session = Depends(get_db),
    kategoriya: str | None = None,
    limit: int = Query(default=20, le=1000),
    offset: int = 0,
):
    """Eng so'nggi yangiliklar (ixtiyoriy kategoriya filtri bilan)."""
    query = published(db)
    if kategoriya:
        query = query.join(Category).filter(Category.slug == kategoriya)
    return (
        query.order_by(Article.published_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/top", response_model=list[ArticleOut])
def top_news(db: Session = Depends(get_db), kunlar: int = 7, limit: int = Query(default=5, le=50)):
    """Top yangiliklar — o'qilishlar soni va muhimlik bahosi bo'yicha."""
    since = datetime.utcnow() - timedelta(days=kunlar)
    articles = (
        published(db)
        .filter(Article.published_at >= since)
        .order_by(Article.views_count.desc(), Article.importance.desc(), Article.published_at.desc())
        .limit(limit)
        .all()
    )
    if not articles:
        articles = (
            published(db)
            .order_by(Article.views_count.desc(), Article.importance.desc(), Article.published_at.desc())
            .limit(limit)
            .all()
        )
    return articles


@router.get("/digest", response_model=list[ArticleOut])
def daily_digest(db: Session = Depends(get_db)):
    """Bugungi futbol dayjesti — bugun chop etilgan barcha yangiliklar."""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        published(db)
        .filter(Article.published_at >= today)
        .order_by(Article.importance.desc())
        .all()
    )


@router.get("/trends")
def trend_topics(db: Session = Depends(get_db), kunlar: int = 7, limit: int = 15):
    """Trend mavzular — so'nggi kunlardagi eng ko'p uchragan teglar.

    Teglar kanonik yozuvi bo'yicha guruhlanadi, shuning uchun eski
    xabarlardagi "Barsa" yozuvi "Barcelona" bilan bitta mavzu bo'lib sanaladi.
    """
    since = datetime.utcnow() - timedelta(days=kunlar)
    articles = published(db).filter(Article.published_at >= since).all()

    totals: Counter = Counter()
    spellings: dict[str, Counter] = defaultdict(Counter)
    for article in articles:
        for tag in article.tags or []:
            canonical = canonical_tag(tag)
            if not canonical:
                continue
            key = tag_key(canonical)
            totals[key] += 1
            spellings[key][canonical] += 1

    return [
        {"teg": spellings[key].most_common(1)[0][0], "soni": count}
        for key, count in totals.most_common(limit)
    ]


@router.get("/sitemap", response_model=list[SitemapArticleOut])
def sitemap_articles(
    db: Session = Depends(get_db),
    hours: int | None = Query(default=None, ge=1, le=168),
):
    """Sitemaplar uchun matnsiz, yengil maqola ro'yxati."""
    query = published(db).options(joinedload(Article.category))
    if hours is not None:
        query = query.filter(
            Article.published_at
            >= datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
        )

    articles = query.order_by(Article.published_at.desc()).all()
    return [
        SitemapArticleOut(
            slug=article.slug,
            title=article.title,
            published_at=article.published_at,
            category_slug=article.category.slug if article.category else None,
        )
        for article in articles
    ]


@router.get("/search", response_model=list[ArticleOut])
def search_news(q: str, db: Session = Depends(get_db), limit: int = Query(default=20, le=100)):
    """Sarlavha, xulosa va matn bo'yicha kengaytirilgan qidiruv."""
    raw_query = q.strip()
    if not raw_query:
        return []

    # Har xil tutuq belgilari va shakllar
    normalized = raw_query.replace("ʻ", "'").replace("’", "'").replace("`", "'")
    patterns = {f"%{raw_query}%", f"%{normalized}%"}
    patterns.add(f"%{normalized.replace('\'', 'ʻ')}%")
    patterns.add(f"%{normalized.replace('\'', '’')}%")

    filters = []
    for pat in patterns:
        filters.extend([
            Article.title.ilike(pat),
            Article.summary.ilike(pat),
            Article.content.ilike(pat),
        ])

    # Ko'p so'zli so'rov bo'lsa, har bir asosiy so'z bo'yicha ham qidirish
    words = [w for w in re.findall(r"[A-Za-zÀ-žʻʼ’'-]+|\d+", raw_query) if len(w) >= 3]
    for word in words[:4]:
        w_norm = word.replace("ʻ", "'").replace("’", "'")
        filters.extend([
            Article.title.ilike(f"%{word}%"),
            Article.title.ilike(f"%{w_norm}%"),
            Article.summary.ilike(f"%{word}%"),
        ])

    return (
        published(db)
        .filter(or_(*filters))
        .order_by(Article.published_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/rss")
def get_rss_feed(db: Session = Depends(get_db)):
    """Google News va boshqa agregatorlar uchun RSS feed."""
    import html
    from fastapi import Response
    from ..config import FRONTEND_ORIGIN

    articles = (
        published(db)
        .order_by(Article.published_at.desc())
        .limit(50)
        .all()
    )
    
    rss_items = []
    for article in articles:
        pub_date = article.published_at.strftime("%a, %d %b %Y %H:%M:%S GMT") if article.published_at else ""
        link = f"{FRONTEND_ORIGIN}/maqola/{article.slug}"
        rss_items.append(
            f"<item>\n"
            f"  <title>{html.escape(article.title)}</title>\n"
            f"  <link>{link}</link>\n"
            f"  <guid isPermaLink=\"true\">{link}</guid>\n"
            f"  <description>{html.escape(article.summary)}</description>\n"
            f"  <pubDate>{pub_date}</pubDate>\n"
            f"</item>"
        )
    
    rss_items_str = "\n".join(rss_items)
    rss_xml = (
        f"<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n"
        f"<rss version=\"2.0\" xmlns:atom=\"http://www.w3.org/2005/Atom\">\n"
        f"<channel>\n"
        f"  <title>Futbol Xabar — Jahon futboli yangiliklari o'zbek tilida</title>\n"
        f"  <link>{FRONTEND_ORIGIN}</link>\n"
        f"  <description>Dunyodagi eng so'nggi jahon futboli yangiliklari va tahlillari o'zbek tilida.</description>\n"
        f"  <language>uz</language>\n"
        f"  {rss_items_str}\n"
        f"</channel>\n"
        f"</rss>"
    )
    return Response(content=rss_xml, media_type="application/xml")


@router.get("/{slug}/related", response_model=list[ArticleOut])
def related_news(
    slug: str,
    db: Session = Depends(get_db),
    limit: int = Query(default=4, le=10),
):
    """O'xshash xabarlar — bir kategoriya yoki umumiy teglar bo'yicha."""
    article = published(db).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(status_code=404, detail="Maqola topilmadi")

    tags = set(article.tags or [])
    category_id = article.category_id

    candidates = (
        published(db)
        .filter(Article.id != article.id)
        .order_by(Article.published_at.desc())
        .limit(150)
        .all()
    )

    def _score(candidate: Article) -> int:
        score = 0
        if category_id and candidate.category_id == category_id:
            score += 2
        score += len(tags & set(candidate.tags or [])) * 3
        return score

    scored = [(candidate, _score(candidate)) for candidate in candidates]
    scored.sort(
        key=lambda pair: (pair[1], pair[0].published_at or datetime.min),
        reverse=True,
    )
    return [candidate for candidate, score in scored if score > 0][:limit]


@router.get("/{slug}", response_model=ArticleOut)
def article_detail(slug: str, db: Session = Depends(get_db)):
    article = published(db).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(status_code=404, detail="Maqola topilmadi")
    article.views_count = (article.views_count or 0) + 1
    db.commit()
    db.refresh(article)
    return article

