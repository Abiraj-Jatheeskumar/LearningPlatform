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
                            report_type,
                            generated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s
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
    
    # ============================================================
    # BACKUP USER
    # ============================================================
    @staticmethod
    async def backup_user(user_data: Dict) -> bool:
        """
        Backup a user document to MySQL.
        Called after user is saved to MongoDB.
        """
        if not mysql_backup.is_connected:
            return False
        
        try:
            mongo_id = str(user_data.get("_id", user_data.get("id", "")))
            if not mongo_id:
                return False
            
            # Parse timestamps
            created_at = user_data.get("createdAt") or user_data.get("created_at")
            last_login = user_data.get("lastLogin") or user_data.get("last_login")
            
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    created_at = None
            
            if isinstance(last_login, str):
                try:
                    last_login = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                except:
                    last_login = None
            
            async with mysql_backup.get_connection() as conn:
                if conn is None:
                    return False
                
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        INSERT IGNORE INTO users_backup (
                            mongo_id, email, first_name, last_name, role,
                            created_at, last_login, is_active
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        mongo_id,
                        user_data.get("email", "")[:255],
                        user_data.get("firstName", user_data.get("first_name", ""))[:100] if user_data.get("firstName") or user_data.get("first_name") else None,
                        user_data.get("lastName", user_data.get("last_name", ""))[:100] if user_data.get("lastName") or user_data.get("last_name") else None,
                        user_data.get("role", "student"),
                        created_at,
                        last_login,
                        user_data.get("isActive", True)
                    ))
                    
                    if cursor.rowcount > 0:
                        print(f"✅ MySQL backup: user {mongo_id} saved")
                    return True
                    
        except Exception as e:
            print(f"⚠️ MySQL user backup failed (non-fatal): {e}")
            return False
    
    # ============================================================
    # BACKUP QUIZ ANSWER
    # ============================================================
    @staticmethod
    async def backup_quiz_answer(answer_data: Dict) -> bool:
        """
        Backup a quiz answer to MySQL.
        Called after quiz answer is saved to MongoDB.
        """
        if not mysql_backup.is_connected:
            return False
        
        try:
            mongo_id = str(answer_data.get("_id", answer_data.get("id", "")))
            if not mongo_id:
                return False
            
            # Parse timestamp
            answered_at = answer_data.get("timestamp") or answer_data.get("answeredAt")
            if isinstance(answered_at, str):
                try:
                    answered_at = datetime.fromisoformat(answered_at.replace('Z', '+00:00'))
                except:
                    answered_at = None
            elif not isinstance(answered_at, datetime):
                answered_at = datetime.utcnow()
            
            # Get network quality
            network = answer_data.get("networkStrength", {})
            network_quality = network.get("quality") if isinstance(network, dict) else None
            
            async with mysql_backup.get_connection() as conn:
                if conn is None:
                    return False
                
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        INSERT IGNORE INTO quiz_answers_backup (
                            mongo_id, session_id, student_id, question_id,
                            answer_index, is_correct, time_taken, network_quality,
                            answered_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        mongo_id,
                        answer_data.get("sessionId", ""),
                        answer_data.get("studentId", ""),
                        answer_data.get("questionId", ""),
                        answer_data.get("answerIndex"),
                        answer_data.get("isCorrect"),
                        answer_data.get("timeTaken"),
                        network_quality,
                        answered_at
                    ))
                    
                    if cursor.rowcount > 0:
                        print(f"✅ MySQL backup: quiz_answer {mongo_id} saved")
                    return True
                    
        except Exception as e:
            print(f"⚠️ MySQL quiz_answer backup failed (non-fatal): {e}")
            return False
    
    # ============================================================
    # BACKUP QUESTION
    # ============================================================
    @staticmethod
    async def backup_question(question_data: Dict) -> bool:
        """
        Backup a question to MySQL.
        Called after question is saved to MongoDB.
        """
        if not mysql_backup.is_connected:
            return False
        
        try:
            mongo_id = str(question_data.get("_id", question_data.get("id", "")))
            if not mongo_id:
                return False
            
            # Parse timestamp
            created_at = question_data.get("createdAt") or question_data.get("created_at")
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    created_at = None
            
            # Serialize options and tags
            options = question_data.get("options", [])
            tags = question_data.get("tags", [])
            options_json = json.dumps(options, ensure_ascii=False) if options else None
            tags_json = json.dumps(tags, ensure_ascii=False) if tags else None
            
            async with mysql_backup.get_connection() as conn:
                if conn is None:
                    return False
                
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        INSERT IGNORE INTO questions_backup (
                            mongo_id, question_text, question_type, difficulty,
                            course_id, created_by, correct_answer, options, tags,
                            created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        mongo_id,
                        question_data.get("question", question_data.get("text", ""))[:65535] if question_data.get("question") or question_data.get("text") else None,
                        question_data.get("type", question_data.get("questionType", "multiple_choice")),
                        question_data.get("difficulty", "medium"),
                        question_data.get("courseId", question_data.get("course_id", "")),
                        question_data.get("createdBy", question_data.get("created_by", "")),
                        question_data.get("correctAnswer", question_data.get("correct_answer")),
                        options_json,
                        tags_json,
                        created_at
                    ))
                    
                    if cursor.rowcount > 0:
                        print(f"✅ MySQL backup: question {mongo_id} saved")
                    return True
                    
        except Exception as e:
            print(f"⚠️ MySQL question backup failed (non-fatal): {e}")
            return False
    
    # ============================================================
    # BACKUP COURSE
    # ============================================================
    @staticmethod
    async def backup_course(course_data: Dict) -> bool:
        """
        Backup a course to MySQL.
        Called after course is saved to MongoDB.
        """
        if not mysql_backup.is_connected:
            return False
        
        try:
            mongo_id = str(course_data.get("_id", course_data.get("id", "")))
            if not mongo_id:
                return False
            
            # Parse timestamp
            created_at = course_data.get("createdAt") or course_data.get("created_at")
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    created_at = None
            elif not isinstance(created_at, datetime):
                created_at = None
            
            async with mysql_backup.get_connection() as conn:
                if conn is None:
                    return False
                
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        INSERT IGNORE INTO courses_backup (
                            mongo_id, course_code, course_name, description,
                            instructor_id, instructor_name, semester, year,
                            credits, status, enrolled_count, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        mongo_id,
                        course_data.get("code", course_data.get("courseCode", ""))[:50] if course_data.get("code") or course_data.get("courseCode") else None,
                        course_data.get("name", course_data.get("courseName", ""))[:255] if course_data.get("name") or course_data.get("courseName") else None,
                        course_data.get("description", "")[:65535] if course_data.get("description") else None,
                        course_data.get("instructorId", course_data.get("instructor_id", "")),
                        course_data.get("instructorName", course_data.get("instructor", "")),
                        course_data.get("semester", ""),
                        course_data.get("year"),
                        course_data.get("credits"),
                        course_data.get("status", "active"),
                        len(course_data.get("enrolledStudents", [])) if course_data.get("enrolledStudents") else 0,
                        created_at
                    ))
                    
                    if cursor.rowcount > 0:
                        print(f"✅ MySQL backup: course {mongo_id} saved")
                    return True
                    
        except Exception as e:
            print(f"⚠️ MySQL course backup failed (non-fatal): {e}")
            return False


# Global singleton instance
mysql_backup_service = MySQLBackupService()

