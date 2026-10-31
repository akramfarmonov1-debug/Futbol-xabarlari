import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import cache
from app.database import Base, get_db
from app.main import app
from app.models import Article, ArticleQuality, ArticleSource
from app.schemas import AdminArticleOut


class AdminQualityContractTests(unittest.TestCase):
    def test_admin_article_exposes_quality_and_sources(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine)()
        article = Article(
            title="Sinov maqola",
            slug="sinov-maqola",
            original_url="https://example.com/primary",
            source_name="Primary",
            status="pending",
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        session.add_all(
            [
                ArticleSource(
                    article_id=article.id,
                    original_url="https://example.com/primary",
                    original_title="Test article",
                    source_name="Primary",
                ),
                ArticleQuality(
                    article_id=article.id,
                    football_confidence=96,
                    category_confidence=91,
                    fact_confidence=89,
                    event_key="transfer:test-player:test-club",
                    entities=["Test Player", "Test Club"],
                    facts=[],
                    decision="ready",
                    reasons=[],
                ),
            ]
        )
        session.commit()
        session.refresh(article)

        payload = AdminArticleOut.model_validate(article)
        self.assertEqual(payload.quality.fact_confidence, 89)
        self.assertEqual(payload.quality.decision, "ready")
        self.assertEqual(len(payload.sources), 1)
        session.close()

    @patch("app.deps.ADMIN_TOKEN", "test-admin-secret")
    def test_admin_approve_and_reject_clear_news_cache(self):
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine)()

        article = Article(
            title="Pending maqola",
            slug="pending-maqola",
            summary="Xulosa",
            content="Matn",
            original_url="https://example.com/pending",
            source_name="BBC Sport Football",
            status="pending",
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        app.dependency_overrides[get_db] = lambda: session
        cache.clear()
        try:
            client = TestClient(app)
            headers = {"X-Admin-Token": "test-admin-secret"}

            # 1. Warm the /api/news cache while article is pending
            initial = client.get("/api/news").json()
            self.assertEqual(initial, [])

            # 2. Approve article -> cache should be cleared and /api/news returns it immediately
            resp = client.post(f"/api/admin/articles/{article.id}/approve", headers=headers)
            self.assertEqual(resp.status_code, 200)
            after_approve = client.get("/api/news").json()
            self.assertEqual(len(after_approve), 1)
            self.assertEqual(after_approve[0]["slug"], "pending-maqola")

            # 3. Reject article -> cache cleared and /api/news is empty immediately
            resp_reject = client.post(f"/api/admin/articles/{article.id}/reject", headers=headers)
            self.assertEqual(resp_reject.status_code, 200)
            after_reject = client.get("/api/news").json()
            self.assertEqual(after_reject, [])
        finally:
            cache.clear()
            app.dependency_overrides.clear()
            session.close()


if __name__ == "__main__":
    unittest.main()
