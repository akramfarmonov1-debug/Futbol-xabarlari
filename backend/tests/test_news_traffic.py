"""Neon trafigi: ro'yxatlar maqolalarning to'liq matnini bazadan o'qimasin.

Baza Neon'da va bepul tarif oyiga 5 GB trafik beradi; u to'liq matnlarni
qayta-qayta o'qishga ketib, sayt 12-sentabrda to'xtagan. Testlar SQL
darajasida tekshiradi: so'rovlarning SELECT qismida ``articles.content``
bo'lmasligi kerak (``length(...)`` ichida bo'lishi mumkin — o'qish vaqti uchun).
"""

import unittest
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import cache
from app.database import Base, get_db
from app.main import app
from app.models import Article, Category
from app.services import event_dedup


def _reads_article_body(statement: str) -> bool:
    columns = statement.split("FROM", 1)[0]
    for wrapped in ("length(articles.content)", "replace(articles.content"):
        columns = columns.replace(wrapped, "")
    return "articles.content" in columns


class ListTrafficTests(unittest.TestCase):
    def setUp(self):
        cache.clear()
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app)

        category = Category(name="Transferlar", slug="transferlar")
        self.db.add(category)
        self.db.flush()
        now = datetime.utcnow()
        for i in range(3):
            self.db.add(
                Article(
                    title=f"Transfer yangiligi {i}",
                    slug=f"transfer-{i}",
                    summary="Qisqa xulosa.",
                    content="so'z " * 450,  # 450 so'z → 3 daqiqa
                    practical_note="Nega muhim.",
                    original_url=f"https://example.com/{i}",
                    source_name="Test",
                    status="published",
                    category_id=category.id,
                    tags=["Transfer", "Chelsea"],
                    published_at=now - timedelta(minutes=10 - i),
                )
            )
        self.db.commit()

        self.statements = []
        event.listen(self.engine, "before_cursor_execute", self._record)

    def tearDown(self):
        event.remove(self.engine, "before_cursor_execute", self._record)
        app.dependency_overrides.pop(get_db, None)
        self.db.close()
        cache.clear()

    def _record(self, conn, cursor, statement, parameters, context, executemany):
        self.statements.append(statement)

    def test_lists_do_not_read_article_bodies(self):
        for path in (
            "/api/news",
            "/api/news?kategoriya=transferlar",
            "/api/news/top",
            "/api/news/digest",
            "/api/news/trends",
            "/api/news/sitemap",
            "/api/news/rss",
            "/api/news/search?q=Transfer",
            "/api/news/transfer-0/related",
            "/api/legionnaires",
        ):
            self.statements.clear()
            response = self.client.get(path)

            self.assertEqual(response.status_code, 200, path)
            self.assertTrue(self.statements, path)
            self.assertEqual([s for s in self.statements if _reads_article_body(s)], [], path)

    def test_card_carries_reading_time_not_the_body(self):
        cards = self.client.get("/api/news").json()

        self.assertEqual(len(cards), 3)
        for card in cards:
            self.assertNotIn("content", card)
            self.assertEqual(card["reading_minutes"], 3)
            # Bot ro'yxatlarda "Nega muhim?" bo'limini shu maydondan ko'rsatadi.
            self.assertEqual(card["practical_note"], "Nega muhim.")

    def test_detail_keeps_the_body_and_views_leave_updated_at_alone(self):
        first = self.client.get("/api/news/transfer-0").json()
        second = self.client.get("/api/news/transfer-0").json()

        self.assertIn("so'z", first["content"])
        self.assertEqual(second["views_count"], first["views_count"] + 1)
        # "Oxirgi yangilangan" ko'rishlar bilan emas, tahrir bilan o'zgaradi.
        self.assertEqual(second["updated_at"], first["updated_at"])

    def test_related_and_trends_keep_their_results(self):
        related = self.client.get("/api/news/transfer-0/related?limit=5").json()
        trends = self.client.get("/api/news/trends").json()

        # Teng ball — yangirog'i birinchi, o'zi ro'yxatda yo'q.
        self.assertEqual([item["slug"] for item in related], ["transfer-2", "transfer-1"])
        self.assertEqual(sorted(trend["soni"] for trend in trends), [3, 3])

    def test_repeated_list_requests_are_served_from_the_cache(self):
        self.client.get("/api/news")
        self.statements.clear()

        self.client.get("/api/news")

        self.assertEqual(self.statements, [])


class DedupTrafficTests(unittest.TestCase):
    def test_candidate_texts_are_read_from_the_database_once(self):
        """Pipeline har bir yangi xabar uchun ikki marta solishtiradi —
        nomzodlar matni har safar bazadan qayta o'qilmasin, natija esa o'zgarmasin."""
        event_dedup._candidate_texts.clear()
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine)()
        article = Article(
            title="Valentin Barco Angliya Premer-ligasida",
            slug="barco-chelsea",
            summary="Chelsea Valentin Barconi Strasbourgdan o'z safiga qo'shib oldi.",
            content="Chelsea futbolchi bilan yetti yillik shartnoma imzoladi.",
            original_title="Chelsea sign Valentin Barco from Strasbourg",
            original_url="https://source-one.example/barco",
            source_name="Source One",
            source_published_at=datetime.utcnow(),
            status="pending",
        )
        session.add(article)
        session.commit()
        statements = []

        def record(conn, cursor, statement, parameters, context, executemany):
            statements.append(statement)

        event.listen(engine, "before_cursor_execute", record)

        unrelated, _ = event_dedup.find_duplicate_article(
            session, "Real Madrid yangi murabbiy tayinladi", "Klub rasmiy bayonot berdi.", datetime.utcnow()
        )
        read_first = any(_reads_article_body(s) for s in statements)
        statements.clear()
        duplicate, match = event_dedup.find_duplicate_article(
            session,
            "Chelsi Valetin Barkoni sotib oldi",
            "Chelsea Barco bilan yetti yillik shartnoma imzoladi.",
            datetime.utcnow(),
        )

        self.assertIsNone(unrelated)
        self.assertTrue(read_first)
        self.assertFalse(any(_reads_article_body(s) for s in statements))
        self.assertEqual(duplicate.id, article.id)
        self.assertTrue(match.is_duplicate)
        event.remove(engine, "before_cursor_execute", record)
        session.close()


if __name__ == "__main__":
    unittest.main()
