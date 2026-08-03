import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
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


if __name__ == "__main__":
    unittest.main()
