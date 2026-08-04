import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Article
from app.services.content_quality import (
    analysis_is_auto_publishable,
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
        # "Liverpoool" kodlash xatosi tuzatiladi, "Wrexham" esa yagona
        # o'zbekcha shakl (Vrekshem) ga keltiriladi.
        self.assertEqual(
            normalize_text("Wrexham Liverpooolga qarshi"),
            "Vrekshem Liverpulga qarshi",
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

    def test_structured_quality_gate_requires_supported_facts(self):
        source = (
            "Chelsea signed Valentin Barco from Strasbourg on a seven-year contract."
        )
        valid = {
            "sarlavha": "Chelsi Valentin Barkoni Strasburgdan sotib oldi",
            "xulosa": "Chelsi Valentin Barkoni Strasburgdan sotib oldi. Klub futbolchi "
            "bilan yetti yillik shartnoma imzolaganini rasman ma'lum qildi.",
            "maqola": "Chelsi Valentin Barkoni Strasburgdan sotib olganini e'lon qildi. "
            "Futbolchi klub bilan yetti yillik shartnoma imzoladi. Ushbu kelishuv "
            "London klubining uzoq muddatli rejasiga mos keladi.\n\nBarko yangi jamoasi "
            "mashg'ulotlariga qo'shiladi. Murabbiylar shtabi uning imkoniyatlarini "
            "mavsumoldi tayyorgarlikda baholaydi. Futbolchi asosiy tarkib uchun kurashadi.",
            "entities": ["Chelsea", "Valentin Barco", "Strasbourg"],
            "facts": [
                {
                    "subject": "Valentin Barco",
                    "predicate": "transferred from",
                    "value": "Strasbourg to Chelsea",
                    "evidence": "Chelsea signed Valentin Barco from Strasbourg",
                }
            ],
            "event_key": "transfer:valentin-barco:chelsea",
            "football_confidence": 98,
            "category_confidence": 95,
            "fact_confidence": 94,
        }
        self.assertTrue(
            analysis_is_publishable(
                valid,
                source_text=source,
                require_structured=True,
            )[0]
        )

        unsupported = dict(valid)
        unsupported["facts"] = [
            dict(valid["facts"][0], evidence="Barco is 19 years old")
        ]
        publishable, reasons = analysis_is_publishable(
            unsupported,
            source_text=source,
            require_structured=True,
        )
        self.assertFalse(publishable)
        self.assertTrue(any("dalili" in reason for reason in reasons))

    def test_structured_quality_gate_rejects_low_confidence(self):
        analysis = {
            "sarlavha": "Chelsi yangi transfer bo'yicha muzokara boshladi",
            "xulosa": "Chelsi yangi transfer bo'yicha muzokara boshladi. Hozircha "
            "kelishuv tafsilotlari va futbolchining qarori rasman ma'lum qilinmagan.",
            "maqola": "Chelsi yangi futbolchi bo'yicha muzokara boshladi. Manba "
            "kelishuv hali yakunlanmaganini qayd etdi. Shu sabab xabar hozircha "
            "mish-mish darajasida qolmoqda.\n\nKlub va futbolchi vakillari muzokarani "
            "davom ettirishi mumkin. Rasmiy bayonot berilmaguncha transfer amalga "
            "oshgan deb bo'lmaydi. Qo'shimcha tafsilotlar keyinroq kutilmoqda.",
            "entities": ["Chelsea"],
            "facts": [{
                "subject": "Chelsea",
                "predicate": "is linked with",
                "value": "a player",
                "evidence": "Chelsea is linked with a player",
            }],
            "event_key": "rumour:chelsea:unknown-player",
            "football_confidence": 95,
            "category_confidence": 70,
            "fact_confidence": 60,
        }
        publishable, reasons = analysis_is_publishable(
            analysis,
            source_text="Chelsea is linked with a player",
            require_structured=True,
        )
        self.assertFalse(publishable)
        self.assertIn("fakt confidence past", reasons)

    def test_auto_publish_gate_requires_90_confidence_and_trusted_source(self):
        analysis = {
            "football_confidence": 95,
            "category_confidence": 92,
            "fact_confidence": 94,
            "ahamiyati": 3,
        }
        self.assertTrue(
            analysis_is_auto_publishable(
                analysis,
                source_name="BBC Sport Football",
                source_url="https://www.bbc.com/sport/football/articles/example",
            )[0]
        )

        low_fact = dict(analysis, fact_confidence=89)
        publishable, reasons = analysis_is_auto_publishable(
            low_fact,
            source_name="BBC Sport Football",
            source_url="https://www.bbc.com/sport/football/articles/example",
        )
        self.assertFalse(publishable)
        self.assertTrue(any("fakt confidence" in reason for reason in reasons))

    def test_auto_publish_gate_rejects_missing_or_untrusted_source(self):
        analysis = {
            "football_confidence": 95,
            "category_confidence": 95,
            "fact_confidence": 95,
            "ahamiyati": 3,
        }
        publishable, reasons = analysis_is_auto_publishable(
            analysis,
            source_name="Unknown Blog",
            source_url="http://example.com/story",
        )
        self.assertFalse(publishable)
        self.assertTrue(any("HTTPS" in reason for reason in reasons))
        self.assertTrue(any("ishonchli ro'yxatda" in reason for reason in reasons))

    def test_category_override(self):
        self.assertEqual(
            infer_category(
                "Arsenal Premyer-ligada yangi mavsumga tayyorlanmoqda",
                "jahon-futboli",
            ),
            "premyer-liga",
        )

    def test_wsl_is_not_uzbekistan_football(self):
        self.assertEqual(
            infer_category(
                "Ayollar Superligasi yakshanba oqshom o'yinlarini qaytaradi",
                "uzbekiston-futboli",
            ),
            "jahon-futboli",
        )

    def test_uzbekistan_super_league_keeps_local_category(self):
        self.assertEqual(
            infer_category(
                "O'zbekiston Superligasida Nasaf va Paxtakor uchrashadi",
                "jahon-futboli",
            ),
            "uzbekiston-futboli",
        )

    def test_transfer_denial_is_not_a_transfer(self):
        self.assertEqual(
            infer_category(
                "Bu viktorina bo'lib, transferlar haqida ma'lumot bermaydi. "
                "Angliya Premyer-ligasi futbolchisini toping.",
                "transferlar",
            ),
            "premyer-liga",
        )

    def test_positive_transfer_action_wins(self):
        self.assertEqual(
            infer_category(
                "Chelsi Valentin Barconi Strasburgdan sotib oldi va uzoq "
                "muddatli shartnoma imzoladi.",
                "premyer-liga",
            ),
            "transferlar",
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

    def test_glossary_unifies_team_and_word_spellings(self):
        self.assertEqual(
            normalize_text("Chelsea va Rangers o'yini bo'yicha muxokama"),
            "Chelsi va Reynjers o'yini bo'yicha muhokama",
        )
        self.assertEqual(
            normalize_text("Wrexham Liverpulga qarshi"),
            "Vrekshem Liverpulga qarshi",
        )
        self.assertEqual(
            normalize_text("Barcelona Atletico Madridga qarshi"),
            "Barselona Atletiko Madridga qarshi",
        )

    def test_overlong_title_rejected(self):
        analysis = {
            "sarlavha": "A" * 111,
            "xulosa": "Qisqa xulosa emas, yetarlicha uzun matn." * 3,
            "maqola": "To'liq maqola matni. " * 30,
        }
        publishable, reasons = analysis_is_publishable(analysis)
        self.assertFalse(publishable)
        self.assertTrue(any("sarlavha uzunligi" in reason for reason in reasons))

    def test_excessive_repetition_rejected(self):
        repeated = "anomaliya " * 10
        content = (
            "Mavsum davomida " + repeated
            + "qayd etildi, bu holat kuzatuvchilarni xavotirga soldi. " * 6
        )
        analysis = {
            "sarlavha": "Barselona mavsum oldidan tarkibini yangiladi",
            "xulosa": "Barselona mavsumoldi tayyorgarlikni boshladi. Klub bir necha "
            "o'zgarish kiritdi va muxlislar natijani kutmoqda.",
            "maqola": content,
        }
        publishable, reasons = analysis_is_publishable(analysis)
        self.assertFalse(publishable)
        self.assertTrue(any("takrorlangan" in reason for reason in reasons))


if __name__ == "__main__":
    unittest.main()
