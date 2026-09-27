import asyncio
import json
import os
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite://")

from app.pipeline import LAST_RUN, format_error, redact_secrets  # noqa: E402


class SecretRedactionTests(unittest.TestCase):
    """/health ochiq endpoint — xato matni kalit olib chiqib ketmasin."""

    def test_private_key_is_removed(self):
        message = 'File { "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvAIBAD" }'

        text = format_error(RuntimeError(message))

        self.assertNotIn("MIIEvAIBAD", text)
        self.assertNotIn("BEGIN PRIVATE KEY", text)
        self.assertIn("maxfiy", text)

    def test_api_keys_are_masked(self):
        for secret in ("AIzaSyC1234567890abcdef", "sk-ant-api03-abcdef123456"):
            self.assertNotIn(secret, redact_secrets(f"xato: {secret} yaroqsiz"))

    def test_telegram_token_is_masked(self):
        token = "1234567890:AAHfakeTokenValueThatIsLongEnough123"

        self.assertNotIn(token, redact_secrets(f"Unauthorized for {token}"))

    def test_error_is_a_single_short_line(self):
        text = format_error(RuntimeError("birinchi qator\nikkinchi qator   uchinchi"))

        self.assertNotIn("\n", text)
        self.assertLessEqual(len(text), 300)

    def test_long_error_is_truncated(self):
        self.assertLessEqual(len(format_error(RuntimeError("x" * 5000))), 300)

    def test_ordinary_message_survives(self):
        self.assertIn("Vertex AI xatosi 401", format_error(RuntimeError("Vertex AI xatosi 401")))

    def test_database_url_credentials_are_masked(self):
        """Baza xatosi endi /health da chiqadi — ulanish URL'idagi parol bilan emas."""
        text = redact_secrets("xato: postgresql://futbol:S3cr3tPass@dpg-x.render.com/db")

        self.assertNotIn("S3cr3tPass", text)
        self.assertIn("dpg-x.render.com", text)


class LastRunShapeTests(unittest.TestCase):
    def test_health_reports_the_model_in_use(self):
        """Render environment kod standartini bekor qilsa, shundan ko'rinadi."""
        self.assertIn("provider", LAST_RUN)
        self.assertTrue(LAST_RUN["model"])

    def test_counters_are_present(self):
        for key in (
            "collected", "saved", "non_football", "duplicates",
            "ai_errors", "needs_review", "telegram_sent", "skipped_locked",
        ):
            self.assertIn(key, LAST_RUN)


class HealthResponseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import database

        cls.previous_bind = database.SessionLocal.kw.get("bind")
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        database.Base.metadata.create_all(cls.engine)
        database.SessionLocal.configure(bind=cls.engine)
        cls.database = database

    @classmethod
    def tearDownClass(cls):
        cls.database.SessionLocal.configure(bind=cls.previous_bind)

    def test_health_reports_the_effective_thresholds(self):
        """Render environment kod standartini bekor qilsa, shu yerda ko'rinadi."""
        from app.main import health

        body = health()

        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["database"], "ok")
        for key in (
            "auto_publish", "auto_publish_min_importance",
            "auto_telegram", "auto_telegram_min_importance",
        ):
            self.assertIn(key, body["publish"])

    def test_health_carries_the_pipeline_state(self):
        from app.main import health

        pipeline = health()["pipeline"]

        self.assertIn("status", pipeline)
        self.assertIn("model", pipeline["last_run"])


class HealthWithoutDatabaseTests(unittest.TestCase):
    """Baza yiqilganda /health sababsiz 500 emas, sababi bilan 503 qaytarsin."""

    @classmethod
    def setUpClass(cls):
        from app import database

        cls.previous_bind = database.SessionLocal.kw.get("bind")
        # Jadvalsiz baza: so'rov SQLAlchemyError bilan yiqiladi — Postgres
        # o'chirilgan yoki hali tayyor bo'lmagandagidek.
        database.SessionLocal.configure(
            bind=create_engine("sqlite://", poolclass=StaticPool)
        )
        cls.database = database

    @classmethod
    def tearDownClass(cls):
        cls.database.SessionLocal.configure(bind=cls.previous_bind)

    def test_health_answers_503_with_the_reason(self):
        from app.main import health

        response = health()

        self.assertEqual(response.status_code, 503)
        body = json.loads(response.body)
        self.assertEqual(body["status"], "error")
        self.assertEqual(body["database"], "error")
        self.assertIn("articles", body["database_error"])
        self.assertIn("status", body["database_init"])


class StartupWithoutDatabaseTests(unittest.IsolatedAsyncioTestCase):
    """Baza yo'qligi ilovani yiqitmasin; baza qaytgach fon vazifalari boshlansin."""

    async def test_app_starts_without_database_and_recovers(self):
        from app import main

        self.addCleanup(main.DATABASE_STATE.update, dict(main.DATABASE_STATE))
        attempts = []
        started = []

        def init_database():
            attempts.append(True)
            if len(attempts) == 1:
                raise OperationalError("SELECT 1", {}, Exception("connection refused"))

        with (
            patch.object(main, "init_database", init_database),
            patch.object(main, "start_background_tasks", lambda tasks: started.append(True)),
            patch.object(main, "DB_RETRY_INTERVAL", 0),
        ):
            async with main.lifespan(main.app):
                self.assertEqual(main.DATABASE_STATE["status"], "error")
                self.assertIn("connection refused", main.DATABASE_STATE["last_error"])
                self.assertEqual(started, [])

                for _ in range(100):
                    if started:
                        break
                    await asyncio.sleep(0.01)

                self.assertEqual(started, [True])
                self.assertEqual(main.DATABASE_STATE["status"], "ok")


if __name__ == "__main__":
    unittest.main()
