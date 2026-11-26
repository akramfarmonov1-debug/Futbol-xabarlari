import unittest

from sqlalchemy.engine import make_url

from app.config import GEMINI_FALLBACK_MODELS, _normalize_gemini_model, pin_postgres_driver


class DatabaseUrlTests(unittest.TestCase):
    """SQLAlchemy 2.1 "postgresql://" uchun psycopg (v3) ni tanlaydi — o'rnatilgani psycopg2."""

    def test_render_style_urls_get_the_installed_driver(self):
        for url in ("postgresql://u:p@dpg-x/db", "postgres://u:p@dpg-x/db"):
            self.assertEqual(pin_postgres_driver(url), "postgresql+psycopg2://u:p@dpg-x/db")

    def test_sqlalchemy_picks_psycopg2(self):
        url = make_url(pin_postgres_driver("postgresql://u:p@localhost/db"))

        self.assertEqual(url.get_dialect().driver, "psycopg2")

    def test_other_urls_are_left_alone(self):
        for url in ("sqlite:///./x.db", "sqlite://", "postgresql+psycopg2://u:p@h/db"):
            self.assertEqual(pin_postgres_driver(url), url)

    def test_normalize_gemini_model_upgrades_deprecated_models(self):
        for deprecated in ("", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3.7-flash"):
            self.assertEqual(_normalize_gemini_model(deprecated), "gemini-3.8-flash")
        for supported in ("gemini-3.8-flash", "gemini-4-hydrogen", "gemini-3.5-flash-lite"):
            self.assertEqual(_normalize_gemini_model(supported), supported)

    def test_gemini_fallback_models_default(self):
        self.assertIsInstance(GEMINI_FALLBACK_MODELS, tuple)
        self.assertIn("gemini-4-hydrogen", GEMINI_FALLBACK_MODELS)
        self.assertIn("gemini-3.5-flash-lite", GEMINI_FALLBACK_MODELS)


if __name__ == "__main__":
    unittest.main()
