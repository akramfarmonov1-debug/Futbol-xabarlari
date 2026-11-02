import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import PushSubscription


def _session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


class TestPushRoutes(unittest.TestCase):
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

    def test_subscribe_and_status(self):
        # 1. Subscribe
        resp = self.client.post(
            "/api/push/subscribe",
            json={
                "endpoint": "https://fcm.googleapis.com/fcm/send/test_token_123",
                "p256dh": "key_p256dh",
                "auth": "key_auth",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")

        # 2. Check status count
        status_resp = self.client.get("/api/push/status")
        self.assertEqual(status_resp.status_code, 200)
        self.assertEqual(status_resp.json()["subscribers_count"], 1)

        # 3. Unsubscribe
        unsub_resp = self.client.post(
            "/api/push/unsubscribe",
            json={"endpoint": "https://fcm.googleapis.com/fcm/send/test_token_123"},
        )
        self.assertEqual(unsub_resp.status_code, 200)
        self.assertTrue(unsub_resp.json()["deleted"])

        # 4. Status is 0
        status_resp2 = self.client.get("/api/push/status")
        self.assertEqual(status_resp2.json()["subscribers_count"], 0)

    def test_subscribe_rejects_ssrf_or_non_https_endpoints(self):
        for unsafe_url in [
            "http://fcm.googleapis.com/fcm/send/token",
            "https://localhost:8000/api/admin",
            "https://127.0.0.1/internal",
            "https://169.254.169.254/latest/meta-data/",
        ]:
            resp = self.client.post(
                "/api/push/subscribe",
                json={"endpoint": unsafe_url},
            )
            self.assertEqual(resp.status_code, 400, msg=f"Should reject {unsafe_url}")

    def test_vapid_public_key_endpoint(self):
        resp = self.client.get("/api/push/vapid-public-key")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("public_key", resp.json())


if __name__ == "__main__":
    unittest.main()
