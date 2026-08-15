import unittest

from app.services.ai_agent import ANALYSIS_SCHEMA, SYSTEM_PROMPT, _google_schema
from app.services.content_quality import normalize_analysis
from app.tags import canonical_tag, normalize_tags, tag_key


class TagKeyTests(unittest.TestCase):
    def test_case_and_apostrophes_are_ignored(self):
        self.assertEqual(tag_key("O'zbekiston Terma Jamoasi"), tag_key("ozbekiston terma jamoasi"))

    def test_punctuation_is_ignored(self):
        self.assertEqual(tag_key("#Barcelona!"), tag_key("barcelona"))


class CanonicalTagTests(unittest.TestCase):
    def test_club_spellings_collapse_to_one(self):
        for variant in ("barca", "Barsa", "BARSELONA", "FC Barcelona"):
            self.assertEqual(canonical_tag(variant), "Barcelona")

    def test_cyrillic_club_names_map_to_latin(self):
        self.assertEqual(canonical_tag("Реал"), "Real Madrid")
        self.assertEqual(canonical_tag("Манчестер Юнайтед"), "Manchester United")

    def test_competition_aliases(self):
        self.assertEqual(canonical_tag("Champions League"), "Chempionlar ligasi")
        self.assertEqual(canonical_tag("UCL"), "Chempionlar ligasi")
        self.assertEqual(canonical_tag("APL"), "Premyer-liga")

    def test_player_names_keep_their_spelling(self):
        self.assertEqual(canonical_tag("Abduqodir Husanov"), "Abduqodir Husanov")
        self.assertEqual(canonical_tag("PSG"), "PSG")

    def test_lowercase_tag_gets_a_capital(self):
        self.assertEqual(canonical_tag("yosh futbolchilar"), "Yosh futbolchilar")

    def test_variant_spellings_still_group_together(self):
        """Yozuvi saqlansa ham, kalit bo'yicha bitta mavzu bo'lib qoladi."""
        self.assertEqual(
            tag_key(canonical_tag("Yosh Futbolchilar")),
            tag_key(canonical_tag("yosh futbolchilar")),
        )

    def test_empty_tag_is_dropped(self):
        self.assertEqual(canonical_tag("  "), "")
        self.assertEqual(canonical_tag("#"), "")


class NormalizeTagsTests(unittest.TestCase):
    def test_duplicates_within_one_article_are_removed(self):
        self.assertEqual(
            normalize_tags(["Barsa", "barcelona", "Real", "REAL MADRID"]),
            ["Barcelona", "Real Madrid"],
        )

    def test_limit_applies_after_deduplication(self):
        tags = ["Barsa", "Barcelona", "a", "b", "c", "d", "e", "f"]
        self.assertEqual(len(normalize_tags(tags, limit=6)), 6)

    def test_empty_input_is_safe(self):
        self.assertEqual(normalize_tags(None), [])
        self.assertEqual(normalize_tags(["", " ", "#"]), [])

    def test_result_is_idempotent(self):
        once = normalize_tags(["barca", "UCL", "yosh futbolchilar"])
        self.assertEqual(normalize_tags(once), once)


class AnalysisIntegrationTests(unittest.TestCase):
    def test_normalize_analysis_canonicalises_tags(self):
        analysis = normalize_analysis({
            "sarlavha": "Sinov",
            "seo_sarlavha": "Sinov",
            "xulosa": "Sinov xulosasi",
            "maqola": "Sinov matni",
            "amaliy_ahamiyat": "Sinov",
            "teglar": ["barca", "Barsa", "champions league"],
            "entities": [],
            "facts": [],
            "event_key": "sinov",
        })

        self.assertEqual(analysis["teglar"], ["Barcelona", "Chempionlar ligasi"])


class SchemaOrderTests(unittest.TestCase):
    """Maydonlar tartibi kalibrlashning bir qismi."""

    def test_score_is_generated_last(self):
        order = _google_schema()["propertyOrdering"]

        self.assertEqual(order[-1], "ahamiyati")
        self.assertEqual(order[-2], "baho_sababi")

    def test_facts_are_extracted_before_the_article_is_written(self):
        order = _google_schema()["propertyOrdering"]

        self.assertLess(order.index("facts"), order.index("maqola"))
        self.assertLess(order.index("maqola"), order.index("ahamiyati"))

    def test_ordering_covers_every_field(self):
        self.assertEqual(
            sorted(_google_schema()["propertyOrdering"]),
            sorted(ANALYSIS_SCHEMA["properties"]),
        )

    def test_google_schema_drops_unsupported_keyword(self):
        self.assertNotIn("additionalProperties", _google_schema())

    def test_prompt_states_the_whole_scale(self):
        for level in ("1 —", "2 —", "3 —", "4 —", "5 —"):
            self.assertIn(level, SYSTEM_PROMPT)

    def test_prompt_lifts_uzbek_relevant_news(self):
        self.assertIn("legioner", SYSTEM_PROMPT.lower())


if __name__ == "__main__":
    unittest.main()
