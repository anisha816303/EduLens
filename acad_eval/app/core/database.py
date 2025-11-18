import pymongo
from pymongo import MongoClient
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.core.config import MONGO_URI, DATABASE_NAME, SUBMISSIONS_COLLECTION, RUBRIC_SETS_COLLECTION

class MongoDBClient:
    """Manages connection and operations for MongoDB."""
    def __init__(self):
        self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        self.db = self.client[DATABASE_NAME]
        self.submissions_col = self.db[SUBMISSIONS_COLLECTION]
        self.rubric_sets_col = self.db[RUBRIC_SETS_COLLECTION]
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Ensures unique indexes are set on the collections."""
        self.submissions_col.create_index(
            [("student_id", pymongo.ASCENDING), ("rubric_set_id", pymongo.ASCENDING)], unique=True
        )
        self.rubric_sets_col.create_index(
            [("rubric_set_id", pymongo.ASCENDING)], unique=True
        )
        print("✅ MongoDB indexes ensured.")

    def get_rubric_meta(self, rubric_set_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves authoritative rubric metadata (deadline, attempts)."""
        return self.rubric_sets_col.find_one({"rubric_set_id": rubric_set_id})

    def get_submission_record(self, student_id: str, rubric_set_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the last submission record for a student."""
        return self.submissions_col.find_one({"student_id": student_id, "rubric_set_id": rubric_set_id})

    def upsert_rubric_set(self, rubric_set_id: str, parsed_rubrics: List[Dict[str, Any]], deadline: Optional[datetime], max_attempts: Optional[int]):
        """Persists rubric, deadline, and max_attempts metadata."""
        deadline_iso = deadline.isoformat() if deadline else None
        max_attempts_val = max_attempts if max_attempts is not None else None

        self.rubric_sets_col.update_one(
            {"rubric_set_id": rubric_set_id},
            {
                "$setOnInsert": {
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "parsed_rubrics": parsed_rubrics
                },
                "$set": {
                    "deadline": deadline_iso,
                    "max_attempts": max_attempts_val
                }
            },
            upsert=True
        )

    def upsert_submission(self, student_id: str, rubric_set_id: str, filename: str, parsed_rubrics: List[Dict[str, Any]], parsed_result: Dict[str, Any], new_attempt_number: int) -> str:
        """Upserts the grading result and updates attempt number."""
        update_doc = {
            "$set": {
                "filename": filename,
                "rubric_set_id": rubric_set_id,
                "rubrics": parsed_rubrics,
                "result": parsed_result,
                "timestamp": parsed_result["_timestamp"],
                "attempt_number": new_attempt_number
            },
            "$setOnInsert": {
                "student_id": student_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        }

        res = self.submissions_col.update_one(
            {"student_id": student_id, "rubric_set_id": rubric_set_id},
            update_doc,
            upsert=True
        )
        return "updated" if res.modified_count else "inserted"

# Initialize client outside the class for easy import in other modules
try:
    db_client = MongoDBClient()
    print("✅ Successfully initialized MongoDB client.")
except Exception as e:
    print(f"❌ Failed to initialize MongoDB: {e}")
    db_client = None