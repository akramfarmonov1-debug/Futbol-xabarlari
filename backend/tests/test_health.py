import unittest

from app.pipeline import LAST_RUN, format_error, redact_secrets


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


if __name__ == "__main__":
    unittest.main()
