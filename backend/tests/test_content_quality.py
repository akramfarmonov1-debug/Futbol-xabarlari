import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Article
from app.services.content_quality import (
    analysis_is_publishable,
    cleanup_existing_articles,
    infer_category,
    is_football_content,
    normalize_text,
)


class ContentQualityTests(unittest.TestCase):
    def test_sky_accepts_only_football_path(self):
        self.assertTrue(
            is_football_content(
                "Transfer Centre",
                "",
                "https://www.skysports.com/football/news/12040/example",
                "Sky Sports Football",
            )
        )
        self.assertFalse(
            is_football_content(
                "F1 driver ratings",
                "",
                "https://www.skysports.com/f1/news/12040/example",
                "Sky Sports Football",
            )
        )
        self.assertFalse(
            is_football_content(
                "AIG Women's Open",
                "",
                "https://www.skysports.com/golf/news/12040/example",
                "Sky Sports Football",
            )
        )

    def test_known_football_sources(self):
        self.assertTrue(
            is_football_content(
                "Wrexham face Liverpool",
                "",
                "https://www.theguardian.com/football/2026/jul/28/example",
                "The Guardian Football",
            )
        )
        self.assertTrue(
            is_football_content(
                "USMNT coach update",
                "",
                "https://www.espn.com/soccer/story/_/id/1/example",
                "ESPN Soccer",
            )
        )

    def test_text_cleanup(self):
        self.assertEqual(
            normalize_text("Wrexham Liverpooolga qarshi"),
            "Wrexham Liverpulga qarshi",
        )
        self.assertEqual(normalize_text("ZinÃ©din Â«RealÂ»"), "Zinédin «Real»")

    def test_quality_gate(self):
        valid = {
            "sarlavha": "Liverpul yangi mavsum oldidan tarkibini kuchaytirdi",
            "xulosa": "Liverpul yangi mavsum oldidan muhim transferni yakunladi. "
            "Klub futbolchi bilan uzoq muddatli shartnoma imzoladi.",
            "maqola": "Liverpul yangi mavsumga tayyorgarlik doirasida tarkibini "
            "kuchaytirdi. Klub yangi futbolchi bilan shartnoma imzolaganini e'lon "
            "qildi. Ushbu kelishuv murabbiyga yangi taktik imkoniyatlar beradi.\n\n"
            "Futbolchi jamoaning mashg'ulotlariga tez orada qo'shiladi. U yangi "
            "mavsumda asosiy tarkib uchun kurashadi va muxlislar undan yuqori "
            "natija kutmoqda.",
        }
        self.assertTrue(analysis_is_publishable(valid)[0])

        invalid = dict(valid, maqola="Juda qisqa.")
        self.assertFalse(analysis_is_publishable(invalid)[0])

        unnatural = dict(valid, maqola=valid["maqola"] + " Bu juda katta HYPE.")
        self.assertFalse(analysis_is_publishable(unnatural)[0])

    def test_category_override(self):
        self.assertEqual(
            infer_category(
                "Arsenal Premyer-ligada yangi mavsumga tayyorlanmoqda",
                "jahon-futboli",
            ),
            "premyer-liga",
        )

    def test_existing_cleanup_rejects_other_sports_and_fixes_title(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine)()
        session.add_all(
            [
                Article(
                    title="F1 haydovchilari reytingi",
                    slug="f1",
                    original_url="https://www.skysports.com/f1/news/1",
                    source_name="Sky Sports Football",
                    status="published",
                ),
                Article(
                    title="Goodwood kubogi",
                    slug="racing",
                    original_url="https://www.skysports.com/racing/news/2",
                    source_name="Sky Sports Football",
                    status="published",
                ),
                Article(
                    title="Wrexham Liverpooolga qarshi",
                    slug="wrexham",
                    original_url="https://www.theguardian.com/football/example",
                    source_name="The Guardian Football",
                    status="published",
                ),
            ]
        )
        session.commit()

        rejected, corrected = cleanup_existing_articles(session)
        self.assertEqual(rejected, 2)
        self.assertGreaterEqual(corrected, 1)
        self.assertEqual(session.query(Article).filter_by(slug="f1").one().status, "rejected")
        self.assertEqual(
            session.query(Article).filter_by(slug="racing").one().status,
            "rejected",
        )
        self.assertEqual(
            session.query(Article).filter_by(slug="wrexham").one().title,
            "Wrexham Liverpulga qarshi",
        )
        session.close()


if __name__ == "__main__":
    unittest.main()
