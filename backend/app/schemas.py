from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class ArticleSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_url: str
    original_title: str
    source_name: str
    source_published_at: datetime | None


class ArticleQualityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    football_confidence: int
    category_confidence: int
    fact_confidence: int
    event_key: str
    entities: list
    facts: list
    decision: str
    reasons: list


class IngestionDecisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_url: str
    original_title: str
    source_name: str
    decision: str
    reasons: list
    matched_article_id: int | None
    updated_at: datetime


class ArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    seo_title: str
    slug: str
    summary: str
    content: str
    practical_note: str
    tags: list
    importance: int
    original_url: str
    source_name: str
    image_url: str | None
    category: CategoryOut | None
    status: str
    sent_to_telegram: bool
    source_published_at: datetime | None
    published_at: datetime | None
    views_count: int = 0
    created_at: datetime
    updated_at: datetime | None = None


class SitemapArticleOut(BaseModel):
    slug: str
    title: str
    published_at: datetime | None
    category_slug: str | None


class AdminArticleOut(ArticleOut):
    sources: list[ArticleSourceOut] = Field(default_factory=list)
    quality: ArticleQualityOut | None = None


class ArticleUpdate(BaseModel):
    title: str | None = None
    seo_title: str | None = None
    summary: str | None = None
    content: str | None = None
    practical_note: str | None = None
    tags: list | None = None
    importance: int | None = None
    category_id: int | None = None
    image_url: str | None = None


class StatsOut(BaseModel):
    jami: int
    kutilmoqda: int
    chop_etilgan: int
    rad_etilgan: int
    telegramga_yuborilgan: int
    tekshiruv_talab: int
    kategoriyalar_boyicha: dict
