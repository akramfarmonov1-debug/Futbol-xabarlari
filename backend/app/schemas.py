from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


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
    published_at: datetime | None
    created_at: datetime


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
    kategoriyalar_boyicha: dict
