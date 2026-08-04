"""Ommaviy news marshrutlarini end-to-end tekshiradi (TestClient + in-memory DB).

TestClient so'rovlarni alohida ishchi thread'da bajaradi, shuning uchun
``sqlite:///:memory:`` o'rniga StaticPool ishlatiladi — barcha thread'lar
bitta ulanishni ko'radi.
"""

import unittest
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Article, Category


def _session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


class NewsRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = _session()
        cls.client = TestClient(app)
        app.dependency_overrides[get_db] = lambda: cls.db

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        app.dependency_overrides.pop(get_db, None)

    def test_latest_detail_and_related(self):
        cat = Category(name="Premyer-liga", slug="premyer-liga")
        self.db.add(cat)
        self.db.flush()
        articles = []
        for i in range(4):
            articles.append(
                Article(
                    title=f"Maqola {i}",
                    slug=f"maqola-{i}",
                    summary="Qisqa xulosa matni yetarlicha uzun bo'lishi kerak. " * 2,
                    content="Matn tarkibi bir nechta jumladan iborat. " * 20,
                    original_url=f"https://example.com/{i}",
                    source_name="Test",
                    status="published",
                    category_id=cat.id,
                    tags=["transfer", "futbol"],
                    importance=4,
                    published_at=datetime(2026, 8, 4, 9, 0),
                    created_at=datetime(2026, 8, 4, 9, 0),
                )
            )
        self.db.add_all(articles)
        self.db.commit()

        latest = self.client.get("/api/news?limit=10")
        self.assertEqual(latest.status_code, 200)
        self.assertEqual(len(latest.json()), 4)

        detail = self.client.get("/api/news/maqola-0")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["slug"], "maqola-0")
        # "Oxirgi yangilangan" maydoni mavjud.
        self.assertIn("updated_at", detail.json())

        related = self.client.get("/api/news/maqola-0/related?limit=3")
        self.assertEqual(related.status_code, 200)
        related_data = related.json()
        self.assertEqual(len(related_data), 3)
        self.assertTrue(all(item["slug"] != "maqola-0" for item in related_data))

    def test_missing_article_returns_404(self):
        response = self.client.get("/api/news/yoq-mavjud-emas")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
