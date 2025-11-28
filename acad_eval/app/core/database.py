"""
Database Module - MongoDB operations for the Academic Evaluation System
"""

import pymongo
from pymongo import MongoClient
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import bcrypt

from app.core.config import MONGO_URI, DATABASE_NAME, SUBMISSIONS_COLLECTION, RUBRIC_SETS_COLLECTION


class MongoDBClient:
    """Manages connection and operations for MongoDB."""
    
    def __init__(self):
        """Initialize MongoDB client and collections"""
        try:
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            self.db = self.client[DATABASE_NAME]
            self.submissions_col = self.db[SUBMISSIONS_COLLECTION]
            self.rubric_sets_col = self.db[RUBRIC_SETS_COLLECTION]
            
            # User collections for registration/login
            self.students_col = self.db["students"]
            self.teachers_col = self.db["teachers"]
            
            self._ensure_indexes()
            print("✅ MongoDB client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize MongoDB: {e}")
            raise
    
    def _ensure_indexes(self):
        """Ensures unique indexes are set on the collections."""
        try:
            # Submission indexes
            self.submissions_col.create_index(
                [("student_id", pymongo.ASCENDING), ("rubric_set_id", pymongo.ASCENDING)], 
                unique=True
            )
            
            # Rubric set indexes
            self.rubric_sets_col.create_index(
                [("rubric_set_id", pymongo.ASCENDING)], 
                unique=True
            )
            
            # User indexes
            self.students_col.create_index([("student_id", pymongo.ASCENDING)], unique=True)
            self.teachers_col.create_index([("teacher_id", pymongo.ASCENDING)], unique=True)
            
            print("✅ MongoDB indexes ensured.")
        except Exception as e:
            # Index creation may fail if fields don't exist yet; ignore gracefully
            print(f"Warning: Index creation: {e}")
    
    # ============================================
    # RUBRIC SET OPERATIONS
    # ============================================
    
    def get_rubric_meta(self, rubric_set_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves authoritative rubric metadata (deadline, attempts)."""
        try:
            return self.rubric_sets_col.find_one(
                {"rubric_set_id": rubric_set_id},
                {"_id": 0}
            )
        except Exception as e:
            print(f"Error getting rubric meta: {e}")
            return None
    
    def upsert_rubric_set(self, rubric_set_id: str, parsed_rubrics: List[Dict[str, Any]], 
                         deadline: Optional[datetime], max_attempts: Optional[int]):
        """Persists rubric, deadline, and max_attempts metadata."""
        try:
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
            print(f"✅ Rubric set {rubric_set_id[:16]}... saved successfully")
        except Exception as e:
            print(f"Error upserting rubric set: {e}")
            raise
    
    # ============================================
    # SUBMISSION OPERATIONS
    # ============================================
    
    def get_submission_record(self, student_id: str, rubric_set_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the last submission record for a student."""
        try:
            return self.submissions_col.find_one(
                {"student_id": student_id, "rubric_set_id": rubric_set_id},
                {"_id": 0}
            )
        except Exception as e:
            print(f"Error getting submission record: {e}")
            return None
    
    def upsert_submission(self, student_id: str, rubric_set_id: str, filename: str, 
                         parsed_rubrics: List[Dict[str, Any]], parsed_result: Dict[str, Any], 
                         new_attempt_number: int) -> str:
        """Upserts the grading result and updates attempt number."""
        try:
            update_doc = {
                "$set": {
                    "filename": filename,
                    "rubric_set_id": rubric_set_id,
                    "rubrics": parsed_rubrics,
                    "result": parsed_result,
                    "timestamp": parsed_result.get("_timestamp", datetime.now(timezone.utc).isoformat()),
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
            
            operation = "updated" if res.modified_count else "inserted"
            print(f"✅ Submission {operation} for student {student_id}")
            return operation
            
        except Exception as e:
            print(f"Error upserting submission: {e}")
            raise
    
    # ============================================
    # STUDENT MANAGEMENT
    # ============================================
    
    def create_student(self, student_id: str, name: Optional[str], password_plain: str) -> bool:
        """Create a student user with hashed password. Returns True on success, False if exists."""
        if not student_id or not password_plain:
            return False
        
        try:
            # Check if student already exists
            existing = self.students_col.find_one({"student_id": student_id})
            if existing:
                print(f"❌ Student {student_id} already exists")
                return False
            
            # Hash password
            pw_hash = bcrypt.hashpw(password_plain.encode(), bcrypt.gensalt()).decode()
            
            # Create student document
            doc = {
                "student_id": student_id,
                "name": name,
                "password_hash": pw_hash,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            self.students_col.insert_one(doc)
            print(f"✅ Student {student_id} created successfully")
            return True
            
        except Exception as e:
            print(f"Error creating student: {e}")
            return False
    
    def get_student(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Get student information by ID"""
        try:
            return self.students_col.find_one(
                {"student_id": student_id},
                {"_id": 0, "password_hash": 0}  # Don't return password hash
            )
        except Exception as e:
            print(f"Error getting student: {e}")
            return None
    
    def verify_student_password(self, student_id: str, password_plain: str) -> bool:
        """Verify student login credentials"""
        try:
            user = self.students_col.find_one({"student_id": student_id})
            
            if not user or not user.get("password_hash"):
                return False
            
            # Verify password
            return bcrypt.checkpw(
                password_plain.encode(), 
                user.get("password_hash").encode()
            )
            
        except Exception as e:
            print(f"Error verifying student password: {e}")
            return False
    
    # ============================================
    # TEACHER MANAGEMENT
    # ============================================
    
    def create_teacher(self, teacher_id: str, name: Optional[str], password_plain: str) -> bool:
        """Create a teacher user with hashed password. Returns True on success, False if exists."""
        if not teacher_id or not password_plain:
            return False
        
        try:
            # Check if teacher already exists
            existing = self.teachers_col.find_one({"teacher_id": teacher_id})
            if existing:
                print(f"❌ Teacher {teacher_id} already exists")
                return False
            
            # Hash password
            pw_hash = bcrypt.hashpw(password_plain.encode(), bcrypt.gensalt()).decode()
            
            # Create teacher document
            doc = {
                "teacher_id": teacher_id,
                "name": name,
                "password_hash": pw_hash,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            self.teachers_col.insert_one(doc)
            print(f"✅ Teacher {teacher_id} created successfully")
            return True
            
        except Exception as e:
            print(f"Error creating teacher: {e}")
            return False
    
    def get_teacher(self, teacher_id: str) -> Optional[Dict[str, Any]]:
        """Get teacher information by ID"""
        try:
            return self.teachers_col.find_one(
                {"teacher_id": teacher_id},
                {"_id": 0, "password_hash": 0}  # Don't return password hash
            )
        except Exception as e:
            print(f"Error getting teacher: {e}")
            return None
    
    def verify_teacher_password(self, teacher_id: str, password_plain: str) -> bool:
        """Verify teacher login credentials"""
        try:
            user = self.teachers_col.find_one({"teacher_id": teacher_id})
            
            if not user or not user.get("password_hash"):
                return False
            
            # Verify password
            return bcrypt.checkpw(
                password_plain.encode(), 
                user.get("password_hash").encode()
            )
            
        except Exception as e:
            print(f"Error verifying teacher password: {e}")
            return False


# ============================================
# INITIALIZE DATABASE CLIENT
# ============================================

try:
    db_client = MongoDBClient()
except Exception as e:
    print(f"❌ Critical: Failed to initialize MongoDB client: {e}")
    db_client = None
