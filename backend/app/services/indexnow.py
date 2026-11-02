"""IndexNow protokoli — yangi maqola chop etilishi bilan qidiruv tizimlariga
(Yandex, Bing, Seznam, Naver) URL ro'yxatini darhol yuboradi.
"""

import os
from urllib.parse import urlparse

import httpx

from ..config import FRONTEND_ORIGIN
from ..tags import tag_slug

INDEXNOW_KEY = os.getenv("INDEXNOW_KEY", "futbolxabar8f6cda2ee1dde7db").strip()
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"


def build_article_index_urls(article, base_url: str | None = None) -> list[str]:
    """Maqola chop etilganda indekslanishi kerak bo'lgan barcha URL'lar."""
    site = (base_url or FRONTEND_ORIGIN or "").rstrip("/")
    if not site or not getattr(article, "slug", None):
        return []

    urls = [
        f"{site}/maqola/{article.slug}",
        f"{site}/",
        f"{site}/sitemap.xml",
        f"{site}/news-sitemap.xml",
    ]
    category = getattr(article, "category", None)
    if category and getattr(category, "slug", None):
        urls.append(f"{site}/kategoriya/{category.slug}")

    for raw_tag in (getattr(article, "tags", None) or [])[:4]:
        slug = tag_slug(raw_tag)
        if slug:
            urls.append(f"{site}/mavzu/{slug}")

    # Tartibni saqlagan holda dublikatlarni olib tashlash
    return list(dict.fromkeys(urls))


def notify_indexnow_article(article) -> bool:
    """Maqola URL'larini IndexNow API'ga xavfsiz yuboradi (xato bo'lsa oqimni to'xtatmaydi)."""
    site = (FRONTEND_ORIGIN or "").rstrip("/")
    if not site or not INDEXNOW_KEY:
        return False

    parsed = urlparse(site)
    host = (parsed.hostname or "").lower()
    force_enabled = os.getenv("INDEXNOW_ENABLED", "").strip().lower() in ("1", "true", "yes", "ha")
    if not force_enabled and (
        not host or host in {"localhost", "127.0.0.1", "0.0.0.0"} or not site.startswith("https://")
    ):
        return False

    url_list = build_article_index_urls(article, base_url=site)
    if not url_list:
        return False

    payload = {
        "host": host,
        "key": INDEXNOW_KEY,
        "keyLocation": f"{site}/{INDEXNOW_KEY}.txt",
        "urlList": url_list,
    }
    try:
        resp = httpx.post(INDEXNOW_ENDPOINT, json=payload, timeout=5.0)
        return resp.status_code in (200, 202)
    except Exception:
        return False
