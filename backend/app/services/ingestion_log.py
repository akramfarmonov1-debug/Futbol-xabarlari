"""Pipeline qarorlarini takrorlanmaydigan audit jurnaliga yozish."""

from datetime import datetime

from sqlalchemy.orm import Session

from ..models import IngestionDecision


def record_ingestion_decision(
    db: Session,
    *,
    original_url: str,
    original_title: str,
    source_name: str,
    decision: str,
    reasons: list[str] | None = None,
    matched_article_id: int | None = None,
    commit: bool = True,
) -> IngestionDecision:
    """Bir URL uchun oxirgi qarorni insert yoki update qiladi."""
    # SessionLocal autoflush=False ishlatadi. Shu batch ichida hali flush
    # qilinmagan bir xil URL query'da ko'rinmaydi, shuning uchun avval
    # session pending obyektlarini tekshiramiz.
    entry = next(
        (
            pending
            for pending in db.new
            if isinstance(pending, IngestionDecision)
            and pending.original_url == original_url
        ),
        None,
    )
    if entry is None:
        entry = (
            db.query(IngestionDecision)
            .filter(IngestionDecision.original_url == original_url)
            .first()
        )
    if entry is None:
        entry = IngestionDecision(original_url=original_url)
        db.add(entry)
    entry.original_title = original_title
    entry.source_name = source_name
    entry.decision = decision
    entry.reasons = reasons or []
    entry.matched_article_id = matched_article_id
    entry.updated_at = datetime.utcnow()
    if commit:
        db.commit()
        db.refresh(entry)
    return entry
