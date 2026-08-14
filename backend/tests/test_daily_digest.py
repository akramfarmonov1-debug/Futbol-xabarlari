import html
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Article, DailyDigestLog
from app.services import daily_digest


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _article(title="Liverpul yangi transferni e'lon qildi", importance=4, published=None):
    return Article(
        title=title,
        slug=title.lower().replace(" ", "-")[:50],
        summary="Qisqa xulosa matni yetarlicha uzun bo'lishi kerak.",
        content="Maqola matni bir nechta jumladan iborat. " * 10,
        original_url=f"https://example.com/{title[:10]}",
        source_name="Test Source",
        status="published",
        importance=importance,
        published_at=published or datetime(2026, 8, 4, 8, 0),
        created_at=datetime(2026, 8, 4, 8, 0),
    )


class DigestTimeTests(unittest.TestCase):
    def test_within_window_is_true(self):
        moment = datetime(2026, 8, 4, 9, 15)
        self.assertTrue(daily_digest.is_digest_time(moment, "09:00", 30))

    def test_exactly_at_target_is_true(self):
        self.assertTrue(daily_digest.is_digest_time(datetime(2026, 8, 4, 9, 0), "09:00", 30))

    def test_after_window_is_false(self):
        self.assertFalse(daily_digest.is_digest_time(datetime(2026, 8, 4, 9, 31), "09:00", 30))

    def test_before_target_is_false(self):
        self.assertFalse(daily_digest.is_digest_time(datetime(2026, 8, 4, 8, 59), "09:00", 30))

    def test_invalid_target_falls_back_to_nine(self):
        self.assertTrue(daily_digest.is_digest_time(datetime(2026, 8, 4, 9, 5), "not-a-time", 30))


class DigestMessageTests(unittest.TestCase):
    def test_message_contains_articles(self):
        article = _article()
        message = daily_digest.build_digest_message([article], date(2026, 8, 4))
        self.assertIn("KUNNING ENG MUHIM FUTBOL XABARLARI", message)
        # HTML-escape qilingan xabar asl matnni o'z ichiga oladi.
        self.assertIn(
            "Liverpul yangi transferni e'lon qildi",
            html.unescape(message),
        )
        self.assertIn("Batafsil o'qish", message)
        self.assertIn(article.slug, message)

    def test_empty_message(self):
        self.assertEqual(daily_digest.build_digest_message([], date(2026, 8, 4)), "")


class DigestSelectionTests(unittest.TestCase):
    def test_selects_published_important_same_day(self):
        db = _session()
        day = date(2026, 8, 4)
        db.add_all(
            [
                _article(title="Muhim xabar", importance=5, published=datetime(2026, 8, 4, 9, 0)),
                _article(title="O'rtacha xabar", importance=2, published=datetime(2026, 8, 4, 9, 5)),
                _article(title="Eski xabar", importance=5, published=datetime(2026, 8, 1, 9, 0)),
            ]
        )
        db.commit()
        result = daily_digest._digest_articles(db, day, limit=5, min_importance=3)
        self.assertEqual([a.title for a in result], ["Muhim xabar"])
        db.close()


class SendDigestTests(unittest.TestCase):
    @patch.object(daily_digest, "DAILY_DIGEST", True)
    @patch.object(daily_digest, "TELEGRAM_BOT_TOKEN", "token")
    @patch.object(daily_digest, "TELEGRAM_CHANNEL_ID", "@kanal")
    @patch.object(daily_digest, "_send_digest")
    def test_sends_once_per_day(self, mock_send):
        db = _session()
        db.add(_article(importance=4))
        db.commit()

        moment = datetime(2026, 8, 4, 9, 5)
        sent = daily_digest.send_daily_digest(db, moment=moment)
        self.assertTrue(sent)
        self.assertEqual(mock_send.call_count, 1)
        self.assertEqual(db.query(DailyDigestLog).count(), 1)

        # Xuddi shu kunda qayta urinish — yuborilmaydi.
        again = daily_digest.send_daily_digest(db, moment=moment)
        self.assertFalse(again)
        self.assertEqual(mock_send.call_count, 1)
        db.close()

    @patch.object(daily_digest, "DAILY_DIGEST", True)
    @patch.object(daily_digest, "TELEGRAM_BOT_TOKEN", "token")
    @patch.object(daily_digest, "TELEGRAM_CHANNEL_ID", "@kanal")
    @patch.object(daily_digest, "_send_digest")
    def test_outside_window_does_not_send(self, mock_send):
        db = _session()
        db.add(_article(importance=4))
        db.commit()
        sent = daily_digest.send_daily_digest(db, moment=datetime(2026, 8, 4, 12, 0))
        self.assertFalse(sent)
        mock_send.assert_not_called()
        db.close()

    @patch.object(daily_digest, "DAILY_DIGEST", False)
    @patch.object(daily_digest, "_send_digest")
    def test_disabled_feature_does_not_send(self, mock_send):
        db = _session()
        db.add(_article(importance=4))
        db.commit()
        sent = daily_digest.send_daily_digest(db, moment=datetime(2026, 8, 4, 9, 5))
        self.assertFalse(sent)
        mock_send.assert_not_called()
        db.close()


if __name__ == "__main__":
    unittest.main()
