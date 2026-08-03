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

    def test_same_url_is_upserted_before_batch_commit(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine, autoflush=False)()
        common = {
            "original_url": "https://example.com/batch-story",
            "original_title": "Batch story",
            "source_name": "Example",
            "commit": False,
        }
        record_ingestion_decision(
            session,
            **common,
            decision="non_football",
            reasons=["first"],
        )
        record_ingestion_decision(
            session,
            **common,
            decision="duplicate_url_or_title",
            reasons=["second"],
        )
        session.commit()

        rows = session.query(IngestionDecision).all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].decision, "duplicate_url_or_title")
        self.assertEqual(rows[0].reasons, ["second"])
        session.close()


if __name__ == "__main__":
    unittest.main()
