import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Article, Category
from app.routers.news import sitemap_articles


class SitemapContractTests(unittest.TestCase):
    def test_sitemap_is_lightweight_and_only_contains_published_articles(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine)()
        category = Category(name="Transferlar", slug="transferlar")
        session.add(category)
        session.flush()
        session.add_all(
            [
                Article(
                    title="Chop etilgan xabar",
                    slug="chop-etilgan-xabar",
                    original_url="https://example.com/published",
                    category_id=category.id,
                    status="published",
                    published_at=datetime.now() - timedelta(hours=2),
                ),
                Article(
                    title="Kutilayotgan xabar",
                    slug="kutilayotgan-xabar",
                    original_url="https://example.com/pending",
                    category_id=category.id,
                    status="pending",
                ),
            ]
        )
        session.commit()

        payload = sitemap_articles(db=session, hours=48)

        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0].slug, "chop-etilgan-xabar")
        self.assertEqual(payload[0].category_slug, "transferlar")
        self.assertFalse(hasattr(payload[0], "content"))
        session.close()


if __name__ == "__main__":
    unittest.main()
