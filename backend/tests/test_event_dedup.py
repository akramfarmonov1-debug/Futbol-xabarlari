import unittest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Article, ArticleSource
from app.services.event_dedup import (
    attach_article_source,
    compare_events,
    find_duplicate_article,
)


class EventDedupTests(unittest.TestCase):
    def assertDuplicate(self, first_title, first_content, second_title, second_content):
        match = compare_events(first_title, first_content, second_title, second_content)
        self.assertTrue(match.is_duplicate, match)

    def assertDifferent(self, first_title, first_content, second_title, second_content):
        match = compare_events(first_title, first_content, second_title, second_content)
        self.assertFalse(match.is_duplicate, match)

    def test_barco_transfer_variants_are_one_event(self):
        self.assertDuplicate(
            "Chelsi Valetin Barkoni Shtutgartdan sotib oldi",
            "Chelsi himoyachi Valentin Barco bilan yetti yillik shartnoma imzoladi.",
            "Valentin Barco Angliya Premer-ligasida",
            "Chelsea Valentin Barconi Strasbourgdan o'z safiga qo'shib oldi.",
        )

    def test_liverpool_leeds_match_variants_are_one_event(self):
        self.assertDuplicate(
            "Liverpulga qarshi ajoyib qaytish: Lids g'alaba qozondi",
            "Lids Liverpoolni 4:2 hisobida mag'lub etdi.",
            "Liverpulning AQShdagi safariga yomon yakun: Lids ustun keldi",
            "Leeds ikkinchi bo'limda qaytish qilib 4:2 hisobida g'alaba qozondi.",
        )

    def test_salah_rumour_variants_are_one_event(self):
        self.assertDuplicate(
            "Mohamed Solahning Trabzonsporga o'tishi haqidagi mish-mishlar",
            "Salah Trabzonspor bilan transfer muzokarasida ekani aytilmoqda.",
            "Shok yangilik: Salah Trabzonsporda?",
            "Muhammad Saloh Turkiyaning Trabzonspor klubiga o'tishi mumkin.",
        )

    def test_two_different_chelsea_transfers_stay_separate(self):
        self.assertDifferent(
            "Chelsi Valentin Barconi sotib oldi",
            "Chelsea Barco bilan shartnoma imzoladi.",
            "Chelsi yangi darvozabon bilan shartnoma imzoladi",
            "Chelsea Mayk Menyanni Milandan sotib oldi.",
        )

    def test_related_infantino_stories_stay_separate(self):
        self.assertDifferent(
            "Infantino lavozimidan ketishi mumkinmi?",
            "FIFA prezidenti faoliyati tanqid qilindi.",
            "Uels Infantino nomzodligini qo'llab-quvvatlashdan voz kechdi",
            "Uels futbol assotsiatsiyasi FIFA saylovi bo'yicha qarorini o'zgartirdi.",
        )

    def test_database_match_attaches_source_once(self):
        engine = create_engine("sqlite:///:memory:")
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

        duplicate, match = find_duplicate_article(
            session,
            "Chelsi Valetin Barkoni sotib oldi",
            "Chelsea Barco bilan yetti yillik shartnoma imzoladi.",
            datetime.utcnow(),
        )
        self.assertEqual(duplicate.id, article.id)
        self.assertTrue(match.is_duplicate)

        source_args = {
            "original_url": "https://source-two.example/barco",
            "original_title": "Chelsea complete Barco deal",
            "source_name": "Source Two",
            "source_published_at": datetime.utcnow(),
        }
        attach_article_source(session, article, **source_args)
        attach_article_source(session, article, **source_args)
        self.assertEqual(session.query(ArticleSource).count(), 1)
        session.close()


if __name__ == "__main__":
    unittest.main()
