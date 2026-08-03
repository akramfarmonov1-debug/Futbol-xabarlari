"""Ishonchli manbalardan futbol yangiliklarini yig'ish va dublikatlarni filtrlash.

RSS 2.0 va Atom formatlarini stdlib (xml.etree) bilan o'qiydi —
tashqi parser kutubxonalariga bog'liq emas.
"""

import os
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qs, urlparse
from xml.etree import ElementTree

import httpx
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from ..models import Article, ArticleSource
from ..utils import title_hash
from .content_quality import is_football_content
from .ingestion_log import record_ingestion_decision

# "keywords" — ixtiyoriy regex: faqat mos kelgan yozuvlar olinadi
# (aralash sport manbalaridan faqat futbolni ajratish uchun).
FUTBOL_KEYWORDS = (
    r"футбол|futbol|суперлига|superliga|\bпфл\b|\bpfl\b"
    r"|чемпионлар лигаси|chempionlar ligasi|мундиал|mundial|жч-?\d|jch-?\d"
    r"|уефа|uefa|фифа|fifa|трансфер|transfer"
    # mashhur klublar (o'zbek matbuotida tez-tez uchraydigan yozilishlar)
    r"|пахтакор|paxtakor|бунёдкор|bunyodkor|насаф|nasaf|навбаҳор|navbahor"
    r"|барселона|barselona|реал мадрид|real madrid|манчестер|manchester"
    r"|ливерпул|liverpul|арсенал|arsenal|челси|chelsi|ювентус|yuventus"
    r"|[«\"“„]милан|[«\"“„]milan|байерн|bayern|псж|psj"
)

FEEDS = [
    {"name": "BBC Sport Football", "url": "https://feeds.bbci.co.uk/sport/football/rss.xml"},
    {"name": "The Guardian Football", "url": "https://www.theguardian.com/football/rss"},
    {"name": "Sky Sports Football", "url": "https://www.skysports.com/rss/12040"},
    {"name": "ESPN Soccer", "url": "https://www.espn.com/espn/rss/soccer/news"},
    # O'zbek manbalari — aralash sport, futbol filtri bilan
    {"name": "Sports.uz", "url": "https://sports.uz/rss", "keywords": FUTBOL_KEYWORDS},
]

ATOM = "{http://www.w3.org/2005/Atom}"
MEDIA = "{http://search.yahoo.com/mrss/}"
CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}"
DC = "{http://purl.org/dc/elements/1.1/}"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; FutbolXabar/1.0; +https://futbolxabar.uz)"}
MAX_NEWS_AGE_DAYS = max(1, int(os.getenv("MAX_NEWS_AGE_DAYS", "3")))


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text or "").strip()


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
    except Exception:
        pass
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
    except Exception:
        return None


def _first_image(item: ElementTree.Element, html_text: str) -> str | None:
    for tag in (f"{MEDIA}content", f"{MEDIA}thumbnail"):
        el = item.find(tag)
        if el is not None and el.get("url"):
            return el.get("url")
    enclosure = item.find("enclosure")
    if enclosure is not None and str(enclosure.get("type", "")).startswith("image"):
        return enclosure.get("url")
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html_text or "")
    return match.group(1) if match else None


def _parse_feed(xml_text: str) -> list[dict]:
    """RSS 2.0 yoki Atom hujjatidan yozuvlar ro'yxatini qaytaradi."""
    root = ElementTree.fromstring(xml_text)
    entries = []

    # RSS 2.0
    for item in root.iter("item"):
        raw_html = (
            (item.findtext(f"{CONTENT_NS}encoded") or item.findtext("description") or "")
        )
        entries.append({
            "title": (item.findtext("title") or "").strip(),
            "url": (item.findtext("link") or "").strip(),
            "summary": _strip_html(raw_html),
            "published": _parse_date(
                item.findtext("pubDate")
                or item.findtext(f"{DC}date")
                or item.findtext("date")
            ),
            "image": _first_image(item, raw_html),
        })

    # Atom
    for entry in root.iter(f"{ATOM}entry"):
        link = ""
        for l in entry.findall(f"{ATOM}link"):
            if l.get("rel") in (None, "alternate"):
                link = l.get("href", "")
                break
        raw_html = entry.findtext(f"{ATOM}content") or entry.findtext(f"{ATOM}summary") or ""
        entries.append({
            "title": (entry.findtext(f"{ATOM}title") or "").strip(),
            "url": link.strip(),
            "summary": _strip_html(raw_html),
            "published": _parse_date(
                entry.findtext(f"{ATOM}published") or entry.findtext(f"{ATOM}updated")
            ),
            "image": _first_image(entry, raw_html),
        })

    return entries


_OG_PATTERNS = [
    r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)(?::src)?["\'][^>]*content=["\']([^"\']+)["\']',
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\'](?:og:image|twitter:image)(?::src)?["\']',
]


def fetch_og_image(url: str, client: httpx.Client | None = None) -> str | None:
    """Maqola sahifasidan og:image / twitter:image meta tegini oladi
    (RSS'da rasm bo'lmaganda zaxira usul)."""
    owned_client = None
    try:
        if client is None:
            owned_client = httpx.Client(
                timeout=15,
                follow_redirects=True,
                headers=HEADERS,
            )
            client = owned_client

        # Ayrim yangilik sahifalari bir necha megabayt HTML qaytaradi. Meta
        # teglar boshida bo'lgani uchun faqat dastlabki 200 KB oqimda o'qiladi.
        body = bytearray()
        with client.stream("GET", url) as response:
            response.raise_for_status()
            for chunk in response.iter_bytes():
                remaining = 200_000 - len(body)
                if remaining <= 0:
                    break
                body.extend(chunk[:remaining])
                if len(body) >= 200_000:
                    break
            html = body.decode(response.encoding or "utf-8", errors="ignore")
    except Exception:
        return None
    finally:
        if owned_client is not None:
            owned_client.close()

    for pattern in _OG_PATTERNS:
        match = re.search(pattern, html, re.IGNORECASE)
        if match and match.group(1).startswith("http"):
            return match.group(1)
    return None


def _query_width(url: str) -> int | None:
    try:
        raw_width = parse_qs(urlparse(url).query).get("width", [None])[0]
        return int(raw_width) if raw_width else None
    except (TypeError, ValueError):
        return None


def improve_image_url(
    image_url: str | None,
    article_url: str = "",
    source: str = "",
    client: httpx.Client | None = None,
) -> str | None:
    """RSS thumbnailini mavjud bo'lsa katta, maqola darajasidagi rasmga almashtiradi."""
    if not image_url:
        return fetch_og_image(article_url, client) if article_url else None

    host = urlparse(image_url).hostname or ""

    # BBC RSS odatda 240px thumbnail beradi; shu assetning 1200px varianti mavjud.
    if host == "ichef.bbci.co.uk":
        upgraded = re.sub(
            r"/ace/(?:standard|branded_sport)/\d+/",
            "/ace/branded_sport/1200/",
            image_url,
        )
        if upgraded != image_url:
            return upgraded

    # Guardian URL imzosi o'lchamga bog'liq. Parametrni qo'lda o'zgartirish
    # 401 beradi, shuning uchun maqola sahifasidagi imzolangan og:image olinadi.
    is_small_guardian = (
        host == "i.guim.co.uk"
        and (_query_width(image_url) or 0) < 1000
    )
    is_sports_thumbnail = (
        host == "media.sports.uz" and "/thumbnails/" in image_url
    )
    if (is_small_guardian or is_sports_thumbnail) and article_url:
        return fetch_og_image(article_url, client) or image_url

    return image_url


def upgrade_existing_images(db: Session) -> int:
    """Bazadagi eski past aniqlikdagi rasmlarni kam xotira bilan yangilaydi."""
    changed = 0
    guardian_small_widths = or_(
        Article.image_url.contains("width=140"),
        Article.image_url.contains("width=240"),
        Article.image_url.contains("width=300"),
        Article.image_url.contains("width=500"),
        Article.image_url.contains("width=620"),
    )

    with httpx.Client(timeout=15, follow_redirects=True, headers=HEADERS) as client:
        # Eng yangi maqolalar avval yangilanadi. Har ishga tushishda qat'iy
        # limit Render free instansiyasida xotira va vaqt sarfini boshqaradi.
        candidates = (
            db.query(
                Article.id,
                Article.image_url,
                Article.original_url,
                Article.source_name,
            )
            .filter(
                Article.image_url.isnot(None),
                or_(
                    and_(
                        Article.image_url.contains("i.guim.co.uk"),
                        guardian_small_widths,
                    ),
                    and_(
                        Article.image_url.contains("ichef.bbci.co.uk"),
                        or_(
                            Article.image_url.contains("/ace/standard/"),
                            Article.image_url.contains("/240/"),
                        ),
                    ),
                    Article.image_url.contains("media.sports.uz/thumbnails/"),
                ),
            )
            .order_by(Article.id.desc())
            .limit(20)
            .all()
        )

        for article_id, image_url, original_url, source_name in candidates:
            improved = improve_image_url(
                image_url,
                original_url,
                source_name,
                client,
            )
            if improved and improved != image_url:
                (
                    db.query(Article)
                    .filter(Article.id == article_id)
                    .update(
                        {Article.image_url: improved},
                        synchronize_session=False,
                    )
                )
                changed += 1
        db.commit()

    return changed


def collect_news(db: Session, per_feed: int = 5) -> list[dict]:
    """RSS/Atom manbalardan yangi (bazada yo'q) yangiliklarni qaytaradi."""
    existing_urls = {u for (u,) in db.query(Article.original_url).all()}
    existing_urls.update(u for (u,) in db.query(ArticleSource.original_url).all())
    existing_hashes = {title_hash(t) for (t,) in db.query(Article.original_title).all()}
    cutoff = datetime.utcnow() - timedelta(days=MAX_NEWS_AGE_DAYS)

    fresh: list[dict] = []
    with httpx.Client(timeout=20, follow_redirects=True, headers=HEADERS) as client:
        for feed in FEEDS:
            try:
                response = client.get(feed["url"])
                response.raise_for_status()
                entries = _parse_feed(response.text)
            except Exception as error:
                print(f"  ✗ Manba o'qilmadi ({feed['name']}): {error}")
                continue

            # Manba filtri va umumiy sifat darvozasi: faqat futbol.
            keywords = feed.get("keywords")
            football_entries = []
            for entry in entries:
                keyword_match = not keywords or re.search(
                    keywords,
                    f"{entry['title']} {entry['summary']}",
                    re.IGNORECASE,
                )
                football_match = keyword_match and is_football_content(
                    entry["title"],
                    entry["summary"],
                    entry["url"],
                    feed["name"],
                )
                if football_match:
                    football_entries.append(entry)
                elif entry["url"]:
                    record_ingestion_decision(
                        db,
                        original_url=entry["url"],
                        original_title=entry["title"],
                        source_name=feed["name"],
                        decision="non_football",
                        reasons=["RSS sport/kontekst filtri futbolga aloqador deb topmadi"],
                        commit=False,
                    )
            entries = football_entries

            entries.sort(
                key=lambda entry: entry["published"] or datetime.min,
                reverse=True,
            )
            for entry in entries[:per_feed]:
                url, title = entry["url"], entry["title"]
                if not url or not title:
                    continue
                if entry["published"] and entry["published"] < cutoff:
                    continue
                # Dublikat: URL yoki normallashtirilgan sarlavha bo'yicha
                if url in existing_urls or title_hash(title) in existing_hashes:
                    record_ingestion_decision(
                        db,
                        original_url=url,
                        original_title=title,
                        source_name=feed["name"],
                        decision="duplicate_url_or_title",
                        reasons=["URL yoki normallashtirilgan sarlavha avval qayd etilgan"],
                        commit=False,
                    )
                    continue

                fresh.append({
                    "title": title,
                    "content": entry["summary"][:6000],
                    "url": url,
                    "source": feed["name"],
                    "image_url": entry["image"],
                    "published_at": entry["published"],
                })
                existing_urls.add(url)
                existing_hashes.add(title_hash(title))

    db.commit()
    return sorted(
        fresh,
        key=lambda entry: entry["published_at"] or datetime.min,
        reverse=True,
    )
