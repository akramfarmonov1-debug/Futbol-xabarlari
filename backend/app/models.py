from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    articles: Mapped[list["Article"]] = relationship(back_populates="category")


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)

    # O'zbekcha kontent (AI agent tayyorlaydi)
    title: Mapped[str] = mapped_column(String(300))
    seo_title: Mapped[str] = mapped_column(String(300), default="")
    slug: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    summary: Mapped[str] = mapped_column(Text, default="")           # qisqa xulosa
    content: Mapped[str] = mapped_column(Text, default="")           # to'liq maqola
    practical_note: Mapped[str] = mapped_column(Text, default="")    # "Bu nima degani?"
    tags: Mapped[list] = mapped_column(JSON, default=list)
    importance: Mapped[int] = mapped_column(Integer, default=3)      # 1-5

    # Asl manba
    original_title: Mapped[str] = mapped_column(String(500), default="")
    original_url: Mapped[str] = mapped_column(String(1000), unique=True, index=True)
    source_name: Mapped[str] = mapped_column(String(200), default="")
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    category: Mapped[Category | None] = relationship(back_populates="articles")
    sources: Mapped[list["ArticleSource"]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
    )
    quality: Mapped["ArticleQuality | None"] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
        uselist=False,
    )

    # Holat oqimi: pending -> published (admin tasdiqlagach) yoki rejected
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    sent_to_telegram: Mapped[bool] = mapped_column(Boolean, default=False)

    source_published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # "Oxirgi yangilangan" — admin tahriri/tasdiqlashda avtomatik yangilanadi.
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=True,
    )


class ArticleSource(Base):
    """Bitta canonical maqolani tasdiqlovchi asl manbalar."""

    __tablename__ = "article_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"),
        index=True,
    )
    original_url: Mapped[str] = mapped_column(String(1000), unique=True, index=True)
    original_title: Mapped[str] = mapped_column(String(500), default="")
    source_name: Mapped[str] = mapped_column(String(200), default="")
    source_published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    article: Mapped[Article] = relationship(back_populates="sources")


class ArticleQuality(Base):
    """AI tahlili va publish gate qarorining audit izi."""

    __tablename__ = "article_quality"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    football_confidence: Mapped[int] = mapped_column(Integer, default=0)
    category_confidence: Mapped[int] = mapped_column(Integer, default=0)
    fact_confidence: Mapped[int] = mapped_column(Integer, default=0)
    event_key: Mapped[str] = mapped_column(String(300), default="", index=True)
    entities: Mapped[list] = mapped_column(JSON, default=list)
    facts: Mapped[list] = mapped_column(JSON, default=list)
    decision: Mapped[str] = mapped_column(String(30), default="needs_review", index=True)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    article: Mapped[Article] = relationship(back_populates="quality")


class IngestionDecision(Base):
    """Har bir RSS elementiga berilgan oxirgi pipeline qarori."""

    __tablename__ = "ingestion_decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    original_url: Mapped[str] = mapped_column(String(1000), unique=True, index=True)
    original_title: Mapped[str] = mapped_column(String(500), default="")
    source_name: Mapped[str] = mapped_column(String(200), default="")
    decision: Mapped[str] = mapped_column(String(40), index=True)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    matched_article_id: Mapped[int | None] = mapped_column(
        ForeignKey("articles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class DailyDigestLog(Base):
    """Kunlik dayjest kanalga qachon yuborilgani — bir kunda bir marta."""

    __tablename__ = "daily_digest_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    digest_date: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    articles_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
