"""Bir futbol voqeasini turli manba va sarlavhalarda aniqlash."""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..models import Article, ArticleQuality, ArticleSource


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
    # Ayni voqeaning davomiy yangilanishi (yangi hisob/natija) — takror emas.
    is_followup: bool = False


def _event_key_parts(event_key: str) -> tuple[str, set[str]]:
    """AI event_key'ini (tur, entitylar) shaklida ajratadi.

    Misol: ``transfer:valentin-barco:chelsea`` -> ("transfer", {"valentin-barco", "chelsea"})
    """
    if not event_key:
        return "", set()
    parts = [p.strip().casefold() for p in str(event_key).split(":") if p.strip()]
    if not parts:
        return "", set()
    return parts[0], set(parts[1:])


def _normalized_entities(entities: list | None) -> set[str]:
    """AI tomonidan kanoniklashtirilgan entitylar ro'yxatini token set'iga aylantiradi."""
    result = set()
    for entity in entities or []:
        normalized = _normalized_token(str(entity).strip())
        if normalized and normalized not in STOPWORDS and len(normalized) >= 3:
            result.add(normalized)
    return result


def compare_events(
    first_title: str,
    first_content: str,
    second_title: str,
    second_content: str,
    *,
    first_event_key: str = "",
    second_event_key: str = "",
    first_entities: list | None = None,
    second_entities: list | None = None,
) -> EventMatch:
    """Ikki xabar ayni voqeani yoritishini konservativ baholaydi.

    ``first_*`` — yangi (kiruvchi) xabar, ``second_*`` — mavjud canonical maqola.
    AI'ning event_key va entities'lari qo'shimcha kuchli signal sifatida
    ishlatiladi. Bir xil voqeada butunlay yangi aniq raqam (masalan, yangi hisob)
    paydo bo'lsa, bu takror emas, davomiy yangilanish (is_followup) hisoblanadi.
    """
    first_title_tokens = _tokens(first_title)
    second_title_tokens = _tokens(second_title)
    first_all = _tokens(f"{first_title} {first_content}")
    second_all = _tokens(f"{second_title} {second_content}")
    first_entities_title = _title_entities(first_title)
    second_entities_title = _title_entities(second_title)

    title_overlap = _jaccard(first_title_tokens, second_title_tokens)
    content_overlap = _jaccard(first_all, second_all)
    shared_entities = first_entities_title & second_entities_title
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

    # AI event_key mosligi — eng kuchli signal.
    first_key_type, first_key_entities = _event_key_parts(first_event_key)
    second_key_type, second_key_entities = _event_key_parts(second_event_key)
    event_key_match = bool(
        first_key_type
        and first_key_type == second_key_type
        and bool(first_key_entities & second_key_entities)
    )

    # AI entities ro'yxati mosligi (kanonik yozuv, transkripsiya farqlarini
    # TOKEN_ALIASES hal qiladi).
    first_ai_entities = _normalized_entities(first_entities)
    second_ai_entities = _normalized_entities(second_entities)
    ai_shared = first_ai_entities & second_ai_entities
    ai_entity_match = len(ai_shared) >= 2

    reasons = []
    if shared_entities:
        reasons.append("entities:" + ",".join(sorted(shared_entities)))
    if shared_numbers:
        reasons.append("numbers:" + ",".join(sorted(shared_numbers)))
    if same_type:
        reasons.append(f"event_type:{first_type}")
    if event_key_match:
        reasons.append("event_key_match:" + ",".join(sorted(ai_shared or first_key_entities & second_key_entities)))
    if ai_entity_match:
        reasons.append("ai_entities:" + ",".join(sorted(ai_shared)))

    duplicate = False
    if event_key_match:
        duplicate = True
    elif title_overlap >= 0.55 or fuzzy_title >= 0.78:
        duplicate = True
        reasons.append("title_similarity")
    elif ai_entity_match and same_type:
        if first_type in {"transfer", "match"}:
            duplicate = True
        elif content_overlap >= 0.25:
            duplicate = True
    elif same_type and len(shared_entities) >= 2:
        if first_type in {"transfer", "match"}:
            duplicate = True
        elif content_overlap >= 0.28:
            duplicate = True
    elif same_type and len(shared_entities) >= 1 and shared_numbers and content_overlap >= 0.2:
        duplicate = True

    # Davomiy yangilanish: ayni voqeada butunlay yangi aniq raqam (yangi hisob,
    # transfer narxi) paydo bo'lgan bo'lsa — bu takror emas.
    # Diqqat: first_* — yangi (kiruvchi) xabar, second_* — mavjud maqola.
    is_followup = False
    if duplicate:
        existing_numbers = {token for token in second_all if token.isdigit()}
        incoming_numbers = {token for token in first_all if token.isdigit()}
        genuinely_new = incoming_numbers - existing_numbers
        if genuinely_new and len(incoming_numbers) <= 3 and len(existing_numbers) <= 1:
            is_followup = True
            duplicate = False
            reasons.append("new_fact_number:" + ",".join(sorted(genuinely_new)))

    score = round(
        min(
            1.0,
            title_overlap * 0.4
            + content_overlap * 0.2
            + min(len(shared_entities), 3) * 0.08
            + (0.12 if event_key_match else 0.0)
            + (0.08 if ai_entity_match else 0.0)
            + (0.08 if shared_numbers else 0.0),
        ),
        3,
    )
    return EventMatch(duplicate, score, tuple(reasons), is_followup=is_followup)


def find_duplicate_article(
    db: Session,
    title: str,
    content: str,
    published_at: datetime | None = None,
    lookback_days: int = 7,
    event_key: str = "",
    entities: list | None = None,
) -> tuple[Article | None, EventMatch | None]:
    """Yaqindagi canonical maqolalar ichidan ayni voqeani topadi.

    ``event_key`` va ``entities`` AI tahlilidan kelgan bo'lsa, ular mavjud
    maqolalarning ArticleQuality qiymatlari bilan solishtiriladi.
    """
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
    # ArticleQuality joylanmagan eski maqolalar ham bo'lishi mumkin.
    quality_by_id: dict[int, "ArticleQuality"] = {}
    if event_key or entities:
        quality_rows = (
            db.query(ArticleQuality)
            .filter(
                ArticleQuality.article_id.in_([a.id for a in candidates]),
                or_(
                    ArticleQuality.event_key != "",
                    ArticleQuality.entities != [],
                ),
            )
            .all()
        )
        quality_by_id = {q.article_id: q for q in quality_rows}

    for article in candidates:
        quality = quality_by_id.get(article.id)
        match = compare_events(
            title,
            content,
            article.original_title or article.title,
            f"{article.title} {article.summary} {article.content}",
            first_event_key=event_key,
            second_event_key=(quality.event_key if quality else ""),
            first_entities=entities,
            second_entities=(quality.entities if quality else None),
        )
        if match.is_duplicate or match.is_followup:
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
