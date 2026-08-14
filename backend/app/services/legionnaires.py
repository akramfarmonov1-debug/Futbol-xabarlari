"""O'zbekistonlik legioner futbolchilar haqida ma'lumotlar va yangiliklar agregatori."""

from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..models import Article

LEGIONNAIRES = [
    {
        "id": "khusanov",
        "slug": "abduqodir-husanov",
        "name": "Abduqodir Husanov",
        "club": "Lans (RC Lens)",
        "league": "Ligue 1 (Fransiya)",
        "country": "Fransiya",
        "country_flag": "🇫🇷",
        "position": "Markaziy himoyachi",
        "number": 25,
        "birth_date": "2004-02-29",
        "market_value": "€12.0M",
        "search_keywords": ["husanov", "khusanov", "abduqodir husanov", "lans", "lens"],
    },
    {
        "id": "fayzullaev",
        "slug": "abbosbek-fayzullayev",
        "name": "Abbosbek Fayzullayev",
        "club": "SSKA Moskva",
        "league": "RPL (Rossiya)",
        "country": "Rossiya",
        "country_flag": "🇷🇺",
        "position": "Hujumkor yarim himoyachi",
        "number": 11,
        "birth_date": "2003-10-03",
        "market_value": "€6.0M",
        "search_keywords": ["fayzullaev", "fayzullayev", "abbosbek fayzullaev", "sska", "cska"],
    },
    {
        "id": "shomurodov",
        "slug": "eldor-shomurodov",
        "name": "Eldor Shomurodov",
        "club": "AS Roma",
        "league": "Serie A (Italiya)",
        "country": "Italiya",
        "country_flag": "🇮🇹",
        "position": "Markaziy hujumchi",
        "number": 14,
        "birth_date": "1995-06-29",
        "market_value": "€4.0M",
        "search_keywords": ["shomurodov", "eldor shomurodov", "roma", "kalyari"],
    },
    {
        "id": "urunov",
        "slug": "oston-orunov",
        "name": "Oston O'runov",
        "club": "Persepolis",
        "league": "Pro League (Eron)",
        "country": "Eron",
        "country_flag": "🇮🇷",
        "position": "Vinger / Yarim himoyachi",
        "number": 70,
        "birth_date": "2000-12-19",
        "market_value": "€2.5M",
        "search_keywords": ["orunov", "urunov", "o'runov", "o‘runov", "persepolis"],
    },
    {
        "id": "masharipov",
        "slug": "jaloliddin-masharipov",
        "name": "Jaloliddin Masharipov",
        "club": "Esteghlal",
        "league": "Pro League (Eron)",
        "country": "Eron",
        "country_flag": "🇮🇷",
        "position": "Hujumchi / Vinger",
        "number": 77,
        "birth_date": "1993-09-01",
        "market_value": "€1.2M",
        "search_keywords": ["masharipov", "jaloliddin masharipov", "esteghlal"],
    },
    {
        "id": "aliqulov",
        "slug": "husniddin-aliqulov",
        "name": "Husniddin Aliqulov",
        "club": "Rizespor",
        "league": "Super Lig (Turkiya)",
        "country": "Turkiya",
        "country_flag": "🇹🇷",
        "position": "Himoyachi",
        "number": 4,
        "birth_date": "1999-04-04",
        "market_value": "€1.5M",
        "search_keywords": ["aliqulov", "husniddin aliqulov", "rizespor"],
    },
]


def get_legionnaires_summary(db: Session) -> list[dict]:
    """Barcha legionerlar ro'yxati va ularga oid so'nggi xabarlar bilan."""
    result = []
    for p in LEGIONNAIRES:
        filters = []
        for kw in p["search_keywords"]:
            filters.append(Article.title.ilike(f"%{kw}%"))
            filters.append(Article.summary.ilike(f"%{kw}%"))

        articles = (
            db.query(Article)
            .filter(Article.status == "published")
            .filter(or_(*filters))
            .order_by(Article.published_at.desc())
            .limit(3)
            .all()
        )

        result.append({
            **p,
            "articles_count": len(articles),
            "recent_articles": [
                {
                    "id": a.id,
                    "title": a.title,
                    "slug": a.slug,
                    "published_at": a.published_at,
                    "image_url": a.image_url,
                }
                for a in articles
            ],
        })
    return result


def get_legionnaire_detail(db: Session, slug: str) -> dict | None:
    """Bitta legionerning to'liq profili va barcha yangiliklari."""
    player = next((p for p in LEGIONNAIRES if p["slug"] == slug or p["id"] == slug), None)
    if not player:
        return None

    filters = []
    for kw in player["search_keywords"]:
        filters.append(Article.title.ilike(f"%{kw}%"))
        filters.append(Article.summary.ilike(f"%{kw}%"))

    articles = (
        db.query(Article)
        .filter(Article.status == "published")
        .filter(or_(*filters))
        .order_by(Article.published_at.desc())
        .limit(20)
        .all()
    )

    return {
        **player,
        "articles": [
            {
                "id": a.id,
                "title": a.title,
                "slug": a.slug,
                "summary": a.summary,
                "published_at": a.published_at,
                "image_url": a.image_url,
                "importance": a.importance,
            }
            for a in articles
        ],
    }
