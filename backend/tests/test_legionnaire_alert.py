import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import LegionnaireAlertLog


def _session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


class TestLegionnaireAlert(unittest.TestCase):
    def setUp(self):
        self.db = _session()

        def override_get_db():
            try:
                yield self.db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        self.db.close()
        app.dependency_overrides.clear()

    def test_send_and_dedup_alert(self):
        payload = {
            "event_key": "goal:husanov:lens-psg:42",
            "player_name": "Abduqodir Husanov",
            "player_slug": "abduqodir-husanov",
            "club": "RC Lens",
            "event_type": "goal",
            "headline": "Husanov burchak to'pidan so'ng hisobni ochdi!",
            "detail": "O'zbekistonlik markaziy himoyachi 42-daqiqada gol urdi.",
            "match_opponent": "PSG",
            "score": "1:0",
            "minute": "42'",
        }

        # 1. First alert -> sent
        resp = self.client.post("/api/legionnaires/alert", json=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "sent")

        # 2. Duplicate alert with same event_key -> already_sent
        resp2 = self.client.post("/api/legionnaires/alert", json=payload)
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json()["status"], "already_sent")


if __name__ == "__main__":
    unittest.main()
