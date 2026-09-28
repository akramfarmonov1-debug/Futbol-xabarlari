import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, defer, joinedload, load_only, with_expression

from .. import cache
from ..database import get_db
from ..models import Article, Category
from ..schemas import ArticleCardOut, ArticleOut, SitemapArticleOut
from ..tags import canonical_tag, tag_key

router = APIRouter(prefix="/api/news", tags=["news"])

# Baza Neon'da, bepul tarif oyiga 5 GB trafik beradi — u ro'yxatlar uchun
# to'liq maqola matnini qayta-qayta o'qishga ketgan. Ro'yxatlar matnsiz
# (kartochka) olinadi, o'qish vaqti esa SQL'da hisoblanadi: so'zlar ≈
# bo'shliqlar + 1 (length/replace SQLite va PostgreSQL'da bir xil).
_CONTENT_WORDS = (
    func.length(Article.content)
    - func.length(func.replace(Article.content, " ", ""))
    + 1
)
READING_MINUTES = (_CONTENT_WORDS + 199) // 200

# Kesh muddatlari, soniya: yangi yoki tahrirlangan maqola ro'yxatlarda
# ko'pi bilan shuncha kechikib ko'rinadi.
LIST_TTL = 60
SLOW_TTL = 300
SITEMAP_TTL = 600


def published(db: Session):
    return db.query(Article).filter(Article.status == "published")


def published_cards(db: Session):
    return published(db).options(
        defer(Article.content),
        joinedload(Article.category),
        with_expression(Article.reading_minutes, READING_MINUTES),
    )


def _cards(query) -> list[ArticleCardOut]:
    return [ArticleCardOut.model_validate(article) for article in query.all()]


@router.get("", response_model=list[ArticleCardOut])
def latest_news(
    db: Session = Depends(get_db),
    kategoriya: str | None = None,
    limit: int = Query(default=20, le=1000),
    offset: int = 0,
):
    """Eng so'nggi yangiliklar (ixtiyoriy kategoriya filtri bilan)."""

    def load():
        query = published_cards(db)
        if kategoriya:
            query = query.join(Category).filter(Category.slug == kategoriya)
        return _cards(
            query.order_by(Article.published_at.desc())
            .offset(offset)
            .limit(limit)
        )

    return cache.cached(("latest", kategoriya, limit, offset), LIST_TTL, load)


@router.get("/top", response_model=list[ArticleCardOut])
def top_news(db: Session = Depends(get_db), kunlar: int = 7, limit: int = Query(default=5, le=50)):
    """Top yangiliklar — o'qilishlar soni va muhimlik bahosi bo'yicha."""

    def load():
        since = datetime.utcnow() - timedelta(days=kunlar)
        articles = _cards(
            published_cards(db)
            .filter(Article.published_at >= since)
            .order_by(Article.views_count.desc(), Article.importance.desc(), Article.published_at.desc())
            .limit(limit)
        )
        if not articles:
            articles = _cards(
                published_cards(db)
                .order_by(Article.views_count.desc(), Article.importance.desc(), Article.published_at.desc())
                .limit(limit)
            )
        return articles

    return cache.cached(("top", kunlar, limit), LIST_TTL, load)


@router.get("/digest", response_model=list[ArticleCardOut])
def daily_digest(db: Session = Depends(get_db)):
    """Bugungi futbol dayjesti — bugun chop etilgan barcha yangiliklar."""

    def load():
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return _cards(
            published_cards(db)
            .filter(Article.published_at >= today)
            .order_by(Article.importance.desc())
        )

    return cache.cached(("digest",), LIST_TTL, load)


@router.get("/trends")
def trend_topics(db: Session = Depends(get_db), kunlar: int = 7, limit: int = 15):
    """Trend mavzular — so'nggi kunlardagi eng ko'p uchragan teglar.

    Teglar kanonik yozuvi bo'yicha guruhlanadi, shuning uchun eski
    xabarlardagi "Barsa" yozuvi "Barcelona" bilan bitta mavzu bo'lib sanaladi.
    """

    def load():
        since = datetime.utcnow() - timedelta(days=kunlar)
        # Faqat teglar ustuni: ilgari 7 kunlik barcha maqolalar to'liq o'qilardi.
        rows = (
            published(db)
            .filter(Article.published_at >= since)
            .with_entities(Article.tags)
            .all()
        )

        totals: Counter = Counter()
        spellings: dict[str, Counter] = defaultdict(Counter)
        for (tags,) in rows:
            for tag in tags or []:
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

    return cache.cached(("trends", kunlar, limit), SLOW_TTL, load)


@router.get("/sitemap", response_model=list[SitemapArticleOut])
def sitemap_articles(
    db: Session = Depends(get_db),
    hours: int | None = Query(default=None, ge=1, le=168),
):
    """Sitemaplar uchun matnsiz, yengil maqola ro'yxati."""

    def load():
        # Faqat to'rtta ustun: ilgari har bir sitemap so'rovi barcha
        # maqolalarni to'liq matni bilan o'qirdi.
        query = (
            published(db)
            .outerjoin(Category, Article.category_id == Category.id)
            .with_entities(Article.slug, Article.title, Article.published_at, Category.slug)
        )
        if hours is not None:
            query = query.filter(
                Article.published_at
                >= datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
            )

        return [
            SitemapArticleOut(
                slug=slug,
                title=title,
                published_at=published_at,
                category_slug=category_slug,
            )
            for slug, title, published_at, category_slug in query.order_by(
                Article.published_at.desc()
            ).all()
        ]

    return cache.cached(("sitemap", hours), SITEMAP_TTL, load)


@router.get("/search", response_model=list[ArticleCardOut])
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

    return _cards(
        published_cards(db)
        .filter(or_(*filters))
        .order_by(Article.published_at.desc())
        .limit(limit)
    )


@router.get("/rss")
def get_rss_feed(db: Session = Depends(get_db)):
    """Google News va boshqa agregatorlar uchun RSS feed."""
    from fastapi import Response

    xml = cache.cached(("rss",), SLOW_TTL, lambda: _rss_xml(db))
    return Response(content=xml, media_type="application/xml")


def _rss_xml(db: Session) -> str:
    import html
    from ..config import FRONTEND_ORIGIN

    articles = (
        published(db)
        .options(load_only(Article.title, Article.slug, Article.summary, Article.published_at))
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
    return rss_xml


@router.get("/{slug}/related", response_model=list[ArticleCardOut])
def related_news(
    slug: str,
    db: Session = Depends(get_db),
    limit: int = Query(default=4, le=10),
):
    """O'xshash xabarlar — bir kategoriya yoki umumiy teglar bo'yicha."""

    def load():
        article = (
            published(db)
            .options(load_only(Article.id, Article.category_id, Article.tags))
            .filter(Article.slug == slug)
            .first()
        )
        if not article:
            raise HTTPException(status_code=404, detail="Maqola topilmadi")

        tags = set(article.tags or [])
        category_id = article.category_id

        # Baholash uchun to'rtta ustun yetadi: ilgari har bir maqola sahifasi
        # 150 ta maqolani to'liq matni bilan o'qirdi.
        candidates = (
            published(db)
            .filter(Article.id != article.id)
            .with_entities(Article.id, Article.category_id, Article.tags, Article.published_at)
            .order_by(Article.published_at.desc())
            .limit(150)
            .all()
        )

        def _score(candidate) -> int:
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
        ids = [candidate.id for candidate, score in scored if score > 0][:limit]
        if not ids:
            return []
        cards = {
            card.id: card
            for card in _cards(published_cards(db).filter(Article.id.in_(ids)))
        }
        return [cards[article_id] for article_id in ids if article_id in cards]

    return cache.cached(("related", slug, limit), SLOW_TTL, load)


@router.get("/{slug}", response_model=ArticleOut)
def article_detail(slug: str, db: Session = Depends(get_db)):
    article = (
        published(db)
        .options(joinedload(Article.category))
        .filter(Article.slug == slug)
        .first()
    )
    if not article:
        raise HTTPException(status_code=404, detail="Maqola topilmadi")
    return article


@router.post("/{slug}/view", status_code=204)
def count_view(slug: str, db: Session = Depends(get_db)):
    """Bitta ko'rishni sanaydi — brauzer maqolani ochganda yuboradi.

    Sayt sahifalari keshlanadi (ISR): maqola daqiqada ko'pi bilan bir marta
    yasaladi, shuning uchun ko'rishni GET /{slug} ichida sanash tashriflarni
    emas, sahifa yangilanishlarini sanardi. Qator o'qilmaydi (faqat UPDATE),
    updated_at ("Oxirgi yangilangan") esa ko'rishlar bilan o'zgarmaydi.
    """
    counted = (
        published(db)
        .filter(Article.slug == slug)
        .update(
            {
                Article.views_count: Article.views_count + 1,
                Article.updated_at: Article.updated_at,
            },
            synchronize_session=False,
        )
    )
    if not counted:
        raise HTTPException(status_code=404, detail="Maqola topilmadi")
    db.commit()
    return Response(status_code=204)

