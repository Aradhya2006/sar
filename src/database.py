"""
database.py
-----------
Handles all MongoDB operations for the SAR Automator.
Stores raw inputs, masked text, AI narratives, risk scores, and audit metadata.
"""

import pymongo
from datetime import datetime
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError


class SARDatabase:
    def __init__(self, uri: str = "mongodb://localhost:27017/", timeout_ms: int = 3000):
        """
        Connects to MongoDB with a configurable timeout so the app does not
        hang if the database is unavailable.

        Args:
            uri:        MongoDB connection URI.
            timeout_ms: How long (ms) to wait for a connection before raising.
        """
        self.connected = False
        try:
            self.client = pymongo.MongoClient(
                uri,
                serverSelectionTimeoutMS=timeout_ms,
            )
            # Force an actual connection attempt now (not lazy)
            self.client.admin.command("ping")
            self.db = self.client["Barclays_Hackathon"]
            self.collection = self.db["Reports"]
            self.connected = True
            print("[Database] Connected to MongoDB successfully.")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(
                f"[Database] WARNING: Could not connect to MongoDB at {uri}.\n"
                f"  Reports will not be persisted this session.\n"
                f"  Error: {e}"
            )
            self.client = None
            self.db = None
            self.collection = None

    def save_report(
        self,
        raw_data: str,
        masked_text: str,
        ai_narrative: str,
        risk_level: str = "Unknown",
        risk_score: int = 0,
        risk_flags: list[str] | None = None,
    ) -> str:
        """
        Saves a complete SAR case to MongoDB.

        Args:
            raw_data:      The original unmasked transaction text.
            masked_text:   The PII-anonymised version.
            ai_narrative:  The LLM-generated SAR narrative.
            risk_level:    'Low', 'Medium', or 'High'.
            risk_score:    Numeric risk score 0–100.
            risk_flags:    List of triggered rule descriptions.

        Returns:
            A string representation of the MongoDB ObjectId,
            or a fallback stub ID if the database is unavailable.
        """
        if not self.connected or self.collection is None:
            stub_id = f"LOCAL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            print(f"[Database] DB offline — report not persisted (stub ID: {stub_id})")
            return stub_id

        report_data = {
            "timestamp": datetime.now(),
            "raw_input": raw_data,
            "anonymized_text": masked_text,
            "final_narrative": ai_narrative,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_flags": risk_flags or [],
            "status": "Flagged for Review",
        }

        try:
            result = self.collection.insert_one(report_data)
            inserted_id = str(result.inserted_id)
            print(f"[Database] Report saved with ID: {inserted_id}")
            return inserted_id
        except Exception as e:
            print(f"[Database] Failed to save report: {e}")
            return f"ERROR-{datetime.now().strftime('%H%M%S')}"

    def get_all_reports(self, limit: int = 50) -> list[dict]:
        """
        Retrieves recent reports from the database, newest first.

        Args:
            limit: Maximum number of reports to return.

        Returns:
            List of report dicts (MongoDB _id cast to string).
        """
        if not self.connected or self.collection is None:
            return []

        try:
            cursor = self.collection.find().sort("timestamp", -1).limit(limit)
            reports = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                reports.append(doc)
            return reports
        except Exception as e:
            print(f"[Database] Failed to fetch reports: {e}")
            return []

    def update_status(self, report_id: str, new_status: str) -> bool:
        """
        Updates the investigation status of an existing report.

        Args:
            report_id:  The string representation of the MongoDB ObjectId.
            new_status: New status label (e.g. 'Filed to FinCEN').

        Returns:
            True if the update succeeded, False otherwise.
        """
        if not self.connected or self.collection is None:
            return False

        try:
            from bson import ObjectId
            result = self.collection.update_one(
                {"_id": ObjectId(report_id)},
                {"$set": {"status": new_status, "updated_at": datetime.now()}},
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"[Database] Failed to update status: {e}")
            return False

    def get_stats(self) -> dict:
        """
        Returns aggregate counts useful for the dashboard.

        Returns:
            Dict with keys: total, high_risk, medium_risk, low_risk, pending.
        """
        if not self.connected or self.collection is None:
            return {"total": 0, "high_risk": 0, "medium_risk": 0, "low_risk": 0, "pending": 0}

        try:
            total = self.collection.count_documents({})
            high = self.collection.count_documents({"risk_level": "High"})
            medium = self.collection.count_documents({"risk_level": "Medium"})
            low = self.collection.count_documents({"risk_level": "Low"})
            pending = self.collection.count_documents({"status": "Flagged for Review"})
            return {
                "total": total,
                "high_risk": high,
                "medium_risk": medium,
                "low_risk": low,
                "pending": pending,
            }
        except Exception as e:
            print(f"[Database] Failed to fetch stats: {e}")
            return {"total": 0, "high_risk": 0, "medium_risk": 0, "low_risk": 0, "pending": 0}


# ── Self-test ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    db = SARDatabase()
    if db.connected:
        test_id = db.save_report(
            raw_data="John Doe sent $10k",
            masked_text="<n> sent $10k",
            ai_narrative="Sample narrative.",
            risk_level="High",
            risk_score=75,
            risk_flags=["Amount >= $10,000", "International transfer"],
        )
        print(f"Saved report ID: {test_id}")
        stats = db.get_stats()
        print(f"DB stats: {stats}")
    else:
        print("MongoDB not available — skipping insert test.")
