"""Bir futbol voqeasini turli manba va sarlavhalarda aniqlash."""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..models import Article, ArticleSource


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "for", "from", "has",
    "in", "is", "of", "on", "the", "to", "with", "after", "before",
    "haqida", "uchun", "bilan", "yangi", "yana", "endi", "sari", "qarshi",
    "qanday", "qildi", "bo'ldi", "bo‘ladi", "mumkin", "klubi", "jamoasi",
    "angliya", "premyer", "premer", "ligasi", "futbol", "xabar",
}

TOKEN_ALIASES = {
    "chelsi": "chelsea",
    "liverpul": "liverpool",
    "liverpulga": "liverpool",
    "liverpulning": "liverpool",
    "lids": "leeds",
    "barko": "barco",
    "barkoni": "barco",
    "barconi": "barco",
    "valetin": "valentin",
    "solah": "salah",
    "saloh": "salah",
    "solahning": "salah",
    "salohning": "salah",
    "trabzonsporga": "trabzonspor",
    "trabzonsporda": "trabzonspor",
    "muhammad": "mohamed",
    "shtutgart": "stuttgart",
    "shtutgartdan": "stuttgart",
    "strasburg": "strasbourg",
    "strasburgdan": "strasbourg",
    "myu": "manchester-united",
    "yunayted": "united",
}

TRANSFER_TERMS = {
    "transfer", "transfers", "sign", "signs", "signed", "signing", "deal",
    "imzoladi", "imzolash", "shartnoma", "sotib", "o'tdi", "o‘tdi",
    "o'tishi", "o‘tishi", "qo'shib", "qo‘shib", "ijara", "taklif",
}
MATCH_TERMS = {
    "match", "game", "win", "wins", "won", "beat", "defeat", "result",
    "uchrashuv", "o'yin", "o‘yin", "g'alaba", "g‘alaba", "mag'lub",
    "hisob", "gol", "dubl", "qaytish",
}


def _raw_tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-zÀ-žʻʼ’'-]+|\d+", str(text or ""))


def _normalized_token(token: str) -> str:
    value = token.lower().replace("’", "'").replace("ʻ", "'").strip("'-")
    return TOKEN_ALIASES.get(value, value)


def _tokens(text: str) -> set[str]:
    return {
        normalized
        for token in _raw_tokens(text)
        if (normalized := _normalized_token(token))
        and normalized not in STOPWORDS
        and (len(normalized) >= 3 or normalized.isdigit())
    }


def _title_entities(title: str) -> set[str]:
    entities = set()
    for token in _raw_tokens(title):
        normalized = _normalized_token(token)
        is_named = token[:1].isupper() or token.lower() in TOKEN_ALIASES
        if is_named and normalized not in STOPWORDS and len(normalized) >= 3:
            entities.add(normalized)
    return entities


def _event_type(tokens: set[str]) -> str:
    if tokens & TRANSFER_TERMS:
        return "transfer"
    if tokens & MATCH_TERMS or any(token.isdigit() for token in tokens):
        return "match"
    return "general"


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0


@dataclass(frozen=True)
class EventMatch:
    is_duplicate: bool
    score: float
    reasons: tuple[str, ...]


def compare_events(
    first_title: str,
    first_content: str,
    second_title: str,
    second_content: str,
) -> EventMatch:
    """Ikki xabar ayni voqeani yoritishini konservativ baholaydi."""
    first_title_tokens = _tokens(first_title)
    second_title_tokens = _tokens(second_title)
    first_all = _tokens(f"{first_title} {first_content}")
    second_all = _tokens(f"{second_title} {second_content}")
    first_entities = _title_entities(first_title)
    second_entities = _title_entities(second_title)

    title_overlap = _jaccard(first_title_tokens, second_title_tokens)
    content_overlap = _jaccard(first_all, second_all)
    shared_entities = first_entities & second_entities
    shared_numbers = {
        token for token in first_all & second_all if token.isdigit()
    }
    first_type = _event_type(first_all)
    second_type = _event_type(second_all)
    same_type = first_type == second_type
    fuzzy_title = SequenceMatcher(
        None,
        " ".join(sorted(first_title_tokens)),
        " ".join(sorted(second_title_tokens)),
    ).ratio()

    reasons = []
    if shared_entities:
        reasons.append("entities:" + ",".join(sorted(shared_entities)))
    if shared_numbers:
        reasons.append("numbers:" + ",".join(sorted(shared_numbers)))
    if same_type:
        reasons.append(f"event_type:{first_type}")

    duplicate = False
    if title_overlap >= 0.55 or fuzzy_title >= 0.78:
        duplicate = True
        reasons.append("title_similarity")
    elif same_type and len(shared_entities) >= 2:
        if first_type in {"transfer", "match"}:
            duplicate = True
        elif content_overlap >= 0.28:
            duplicate = True
    elif same_type and len(shared_entities) >= 1 and shared_numbers and content_overlap >= 0.2:
        duplicate = True

    score = round(
        min(
            1.0,
            title_overlap * 0.45
            + content_overlap * 0.25
            + min(len(shared_entities), 3) * 0.1
            + (0.1 if shared_numbers else 0.0),
        ),
        3,
    )
    return EventMatch(duplicate, score, tuple(reasons))


def find_duplicate_article(
    db: Session,
    title: str,
    content: str,
    published_at: datetime | None = None,
    lookback_days: int = 7,
) -> tuple[Article | None, EventMatch | None]:
    """Yaqindagi canonical maqolalar ichidan ayni voqeani topadi."""
    reference_time = published_at or datetime.utcnow()
    cutoff = reference_time - timedelta(days=lookback_days)
    candidates = (
        db.query(Article)
        .filter(
            Article.status.in_(("pending", "published")),
            or_(
                Article.source_published_at >= cutoff,
                Article.created_at >= cutoff,
            ),
        )
        .order_by(Article.created_at.desc())
        .limit(250)
        .all()
    )
    for article in candidates:
        match = compare_events(
            title,
            content,
            article.original_title or article.title,
            f"{article.title} {article.summary} {article.content}",
        )
        if match.is_duplicate:
            return article, match
    return None, None


def attach_article_source(
    db: Session,
    article: Article,
    *,
    original_url: str,
    original_title: str,
    source_name: str,
    source_published_at: datetime | None,
) -> ArticleSource:
    """Manbani canonical maqolaga idempotent tarzda bog'laydi."""
    existing = (
        db.query(ArticleSource)
        .filter(ArticleSource.original_url == original_url)
        .first()
    )
    if existing:
        return existing
    source = ArticleSource(
        article_id=article.id,
        original_url=original_url,
        original_title=original_title,
        source_name=source_name,
        source_published_at=source_published_at,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source
