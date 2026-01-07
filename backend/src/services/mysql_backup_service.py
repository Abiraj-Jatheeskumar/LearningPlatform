"""
MySQL Backup Service
=====================
HYBRID ARCHITECTURE: MongoDB (Primary) + MySQL (Backup)

This service handles the asynchronous backup of reports from MongoDB to MySQL.
It is designed to be NON-BLOCKING and FAILURE-TOLERANT.

KEY DESIGN PRINCIPLES:
1. MongoDB is the SOURCE OF TRUTH - always written to first
2. MySQL backup is triggered ASYNCHRONOUSLY after MongoDB success
3. MySQL failures are LOGGED but NEVER crash or block the API
4. All MySQL data is READ-ONLY after insertion (no updates/deletes)
5. Duplicate prevention using MongoDB _id as unique constraint

VIVA EXPLANATION:
-----------------
Q: Why use both MongoDB and MySQL?
A: MongoDB provides flexible document storage ideal for nested session data,
   while MySQL provides structured SQL access for reporting and auditing.

Q: Which database is authoritative?
A: MongoDB is always the source of truth. MySQL is a read-only backup.

Q: What happens if MySQL is down?
A: The API continues normally. Backup failures are logged but don't affect users.

Q: How do you prevent duplicate backups?
A: The MongoDB _id is stored as a unique constraint in MySQL.

Author: Learning Platform Team
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Optional, Any
from ..database.mysql_connection import mysql_backup


class MySQLBackupService:
    """
    Service for backing up MongoDB reports to MySQL.
    
    This service provides safe, async methods to copy report data
    from MongoDB to MySQL for backup and SQL-based querying.
    
    All methods are designed to:
    - Never raise exceptions that could crash the caller
    - Never block the main request/response flow
    - Log all operations for auditing
    """
    
    @staticmethod
    def _serialize_for_json(obj: Any) -> Any:
        """
        Recursively convert MongoDB objects to JSON-serializable format.
        Handles ObjectId, datetime, and other non-serializable types.
        """
        if obj is None:
            return None
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: MySQLBackupService._serialize_for_json(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [MySQLBackupService._serialize_for_json(item) for item in obj]
        if hasattr(obj, '__str__') and not isinstance(obj, (str, int, float, bool)):
            return str(obj)
        return obj
    
    @staticmethod
    async def backup_session_report(report_data: Dict) -> bool:
        """
        Backup a session report to MySQL.
        
        This method should be called AFTER the report is successfully saved to MongoDB.
        It extracts key fields for SQL queries and stores the full document as JSON.
        
        Args:
            report_data: The complete report document from MongoDB
            
        Returns:
            True if backup succeeded, False otherwise (never raises)
        """
        if not mysql_backup.is_connected:
            print("⚠️ MySQL backup skipped: not connected")
            return False
        
        try:
            mongo_id = report_data.get("id") or str(report_data.get("_id", ""))
            if not mongo_id:
                print("⚠️ MySQL backup skipped: no MongoDB ID")
                return False
            
            # Extract flattened fields for SQL queries
            session_date = report_data.get("sessionDate", "")
            try:
                # Parse date string to date object
                if session_date:
                    parsed_date = datetime.strptime(session_date, "%Y-%m-%d").date()
                else:
                    parsed_date = None
            except:
                parsed_date = None
            
            # Parse generated_at timestamp
            generated_at = report_data.get("generatedAt")
            if isinstance(generated_at, str):
                try:
                    generated_at = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
                except:
                    generated_at = datetime.utcnow()
            elif not isinstance(generated_at, datetime):
                generated_at = datetime.utcnow()
            
            # Extract engagement summary
            engagement = report_data.get("engagementSummary", {})
            
            # Serialize full document to JSON
            serialized_doc = MySQLBackupService._serialize_for_json(report_data)
            full_json = json.dumps(serialized_doc, ensure_ascii=False)
            
            async with mysql_backup.get_connection() as conn:
                if conn is None:
                    return False
                
                async with conn.cursor() as cursor:
                    # Insert with duplicate handling (IGNORE duplicates)
                    await cursor.execute("""
                        INSERT IGNORE INTO session_reports_backup (
                            mongo_id,
                            session_id,
                            session_title,
                            course_name,
                            course_code,
                            instructor_id,
                            instructor_name,
                            session_date,
                            session_status,
                            total_participants,
                            total_questions_asked,
                            average_quiz_score,
                            highly_engaged_count,
                            moderately_engaged_count,
                            at_risk_count,
                            full_document,
                            report_type,
                            generated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        mongo_id,
                        report_data.get("sessionId", ""),
                        report_data.get("sessionTitle", "")[:255] if report_data.get("sessionTitle") else None,
                        report_data.get("courseName", "")[:255] if report_data.get("courseName") else None,
                        report_data.get("courseCode", "")[:50] if report_data.get("courseCode") else None,
                        report_data.get("instructorId", ""),
                        report_data.get("instructorName", "")[:255] if report_data.get("instructorName") else None,
                        parsed_date,
                        report_data.get("sessionStatus", "completed"),
                        report_data.get("totalParticipants", 0),
                        report_data.get("totalQuestionsAsked", 0),
                        report_data.get("averageQuizScore"),
                        engagement.get("highly_engaged", 0),
                        engagement.get("moderately_engaged", 0),
                        engagement.get("at_risk", 0),
                        full_json,
                        report_data.get("reportType", "master"),
                        generated_at
                    ))
                    
                    # Check if row was inserted (not a duplicate)
                    if cursor.rowcount > 0:
                        print(f"✅ MySQL backup: session report {mongo_id} saved")
                        
                        # Also backup individual student participation
                        await MySQLBackupService._backup_student_participation(
                            cursor,
                            mongo_id,
                            report_data.get("sessionId", ""),
                            report_data.get("students", [])
                        )
                        return True
                    else:
                        print(f"ℹ️ MySQL backup: session report {mongo_id} already exists (skipped)")
                        return True
            
        except Exception as e:
            # Log error but NEVER raise - this is a backup, not critical path
            print(f"⚠️ MySQL backup failed (non-fatal): {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    async def _backup_student_participation(
        cursor,
        report_mongo_id: str,
        session_id: str,
        students: list
    ):
        """
        Backup individual student participation records.
        Called as part of the session report backup.
        """
        if not students:
            return
        
        try:
            for student in students:
                # Parse timestamps
                joined_at = student.get("joinedAt")
                left_at = student.get("leftAt")
                
                if isinstance(joined_at, str):
                    try:
                        joined_at = datetime.fromisoformat(joined_at.replace('Z', '+00:00'))
                    except:
                        joined_at = None
                elif not isinstance(joined_at, datetime):
                    joined_at = None
                
                if isinstance(left_at, str):
                    try:
                        left_at = datetime.fromisoformat(left_at.replace('Z', '+00:00'))
                    except:
                        left_at = None
                elif not isinstance(left_at, datetime):
                    left_at = None
                
                await cursor.execute("""
                    INSERT IGNORE INTO student_participation_backup (
                        report_mongo_id,
                        session_id,
                        student_id,
                        student_name,
                        student_email,
                        joined_at,
                        left_at,
                        attendance_duration_minutes,
                        total_questions,
                        correct_answers,
                        incorrect_answers,
                        quiz_score,
                        average_response_time,
                        connection_quality
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    report_mongo_id,
                    session_id,
                    student.get("studentId", ""),
                    student.get("studentName", "")[:255] if student.get("studentName") else None,
                    student.get("studentEmail", "")[:255] if student.get("studentEmail") else None,
                    joined_at,
                    left_at,
                    student.get("attendanceDuration"),
                    student.get("totalQuestions", 0),
                    student.get("correctAnswers", 0),
                    student.get("incorrectAnswers", 0),
                    student.get("quizScore"),
                    student.get("averageResponseTime"),
                    student.get("averageConnectionQuality")
                ))
            
            print(f"✅ MySQL backup: {len(students)} student participation records saved")
            
        except Exception as e:
            print(f"⚠️ MySQL student backup failed (non-fatal): {e}")
    
    @staticmethod
    async def backup_report_async(report_data: Dict):
        """
        Trigger backup in the background without blocking.
        
        This method creates a background task for the backup,
        ensuring the API response is not delayed by MySQL operations.
        
        Usage:
            # After saving to MongoDB:
            asyncio.create_task(mysql_backup_service.backup_report_async(report_data))
        """
        try:
            await MySQLBackupService.backup_session_report(report_data)
        except Exception as e:
            # Catch-all to ensure task doesn't crash
            print(f"⚠️ Background MySQL backup failed: {e}")


# Global singleton instance
mysql_backup_service = MySQLBackupService()

