import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import IngestionDecision
from app.services.ingestion_log import record_ingestion_decision


class IngestionLogTests(unittest.TestCase):
    def test_same_url_updates_last_decision(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine)()
        common = {
            "original_url": "https://example.com/story",
            "original_title": "Example story",
            "source_name": "Example",
        }
        record_ingestion_decision(
            session,
            **common,
            decision="ai_error",
            reasons=["temporary"],
        )
        record_ingestion_decision(
            session,
            **common,
            decision="ready",
            reasons=[],
        )
        rows = session.query(IngestionDecision).all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].decision, "ready")
        self.assertEqual(rows[0].reasons, [])
        session.close()


if __name__ == "__main__":
    unittest.main()
