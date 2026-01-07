"""
MySQL Sync Router
==================
Endpoints to sync existing MongoDB data to MySQL backup.

This is a ONE-WAY sync: MongoDB → MySQL
MySQL is READ-ONLY backup, MongoDB remains the source of truth.

VIVA EXPLANATION:
-----------------
Q: What does this endpoint do?
A: It reads all session reports from MongoDB and copies them to MySQL for backup.

Q: Why is this needed?
A: For reports that existed before MySQL backup was added, this syncs them.

Q: Is this automatic?
A: No, this is manual sync. New reports are auto-backed up when created.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
from datetime import datetime
from ..middleware.auth import require_instructor
from ..database.connection import get_database
from ..database.mysql_connection import mysql_backup
from ..services.mysql_backup_service import mysql_backup_service

router = APIRouter(prefix="/api/admin/mysql-sync", tags=["MySQL Sync"])


@router.post("/sync-all-reports")
async def sync_all_reports_to_mysql(user: dict = Depends(require_instructor)):
    """
    Sync ALL existing session reports from MongoDB to MySQL.
    """
    if not mysql_backup.is_connected:
        raise HTTPException(status_code=503, detail="MySQL backup is not connected")
    
    database = get_database()
    if database is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    
    results = {"total": 0, "synced": 0, "skipped": 0, "failed": 0}
    
    try:
        cursor = database.session_reports.find({"reportType": "master"})
        reports = await cursor.to_list(length=None)
        results["total"] = len(reports)
        
        for report in reports:
            try:
                report["id"] = str(report["_id"])
                success = await mysql_backup_service.backup_session_report(report)
                if success:
                    results["synced"] += 1
                else:
                    results["skipped"] += 1
            except Exception as e:
                results["failed"] += 1
        
        return {"success": True, "collection": "session_reports", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-users")
async def sync_users_to_mysql(user: dict = Depends(require_instructor)):
    """
    Sync ALL users from MongoDB to MySQL.
    """
    if not mysql_backup.is_connected:
        raise HTTPException(status_code=503, detail="MySQL backup is not connected")
    
    database = get_database()
    if database is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    
    results = {"total": 0, "synced": 0, "skipped": 0, "failed": 0}
    
    try:
        cursor = database.users.find({})
        users = await cursor.to_list(length=None)
        results["total"] = len(users)
        
        print(f"👥 Found {len(users)} users in MongoDB to sync")
        
        for u in users:
            try:
                u["id"] = str(u["_id"])
                success = await mysql_backup_service.backup_user(u)
                if success:
                    results["synced"] += 1
                else:
                    results["skipped"] += 1
            except Exception as e:
                results["failed"] += 1
        
        print(f"✅ Users sync complete: {results['synced']} synced")
        return {"success": True, "collection": "users", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-quiz-answers")
async def sync_quiz_answers_to_mysql(user: dict = Depends(require_instructor)):
    """
    Sync ALL quiz answers from MongoDB to MySQL.
    """
    if not mysql_backup.is_connected:
        raise HTTPException(status_code=503, detail="MySQL backup is not connected")
    
    database = get_database()
    if database is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    
    results = {"total": 0, "synced": 0, "skipped": 0, "failed": 0}
    
    try:
        cursor = database.quiz_answers.find({})
        answers = await cursor.to_list(length=None)
        results["total"] = len(answers)
        
        print(f"📝 Found {len(answers)} quiz answers in MongoDB to sync")
        
        for answer in answers:
            try:
                answer["id"] = str(answer["_id"])
                success = await mysql_backup_service.backup_quiz_answer(answer)
                if success:
                    results["synced"] += 1
                else:
                    results["skipped"] += 1
            except Exception as e:
                results["failed"] += 1
        
        print(f"✅ Quiz answers sync complete: {results['synced']} synced")
        return {"success": True, "collection": "quiz_answers", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-questions")
async def sync_questions_to_mysql(user: dict = Depends(require_instructor)):
    """
    Sync ALL questions from MongoDB to MySQL.
    """
    if not mysql_backup.is_connected:
        raise HTTPException(status_code=503, detail="MySQL backup is not connected")
    
    database = get_database()
    if database is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    
    results = {"total": 0, "synced": 0, "skipped": 0, "failed": 0}
    
    try:
        cursor = database.questions.find({})
        questions = await cursor.to_list(length=None)
        results["total"] = len(questions)
        
        print(f"❓ Found {len(questions)} questions in MongoDB to sync")
        
        for q in questions:
            try:
                q["id"] = str(q["_id"])
                success = await mysql_backup_service.backup_question(q)
                if success:
                    results["synced"] += 1
                else:
                    results["skipped"] += 1
            except Exception as e:
                results["failed"] += 1
        
        print(f"✅ Questions sync complete: {results['synced']} synced")
        return {"success": True, "collection": "questions", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-courses")
async def sync_courses_to_mysql(user: dict = Depends(require_instructor)):
    """
    Sync all courses from MongoDB to MySQL backup table.
    This endpoint handles EXISTING data migration.
    """
    if not mysql_backup.is_connected:
        raise HTTPException(status_code=503, detail="MySQL backup is not connected")
    
    database = get_database()
    if database is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    
    results = {"total": 0, "synced": 0, "skipped": 0, "failed": 0}
    
    try:
        cursor = database.courses.find({})
        courses = await cursor.to_list(length=None)
        results["total"] = len(courses)
        
        print(f"📚 Found {len(courses)} courses in MongoDB to sync")
        
        for c in courses:
            try:
                c["id"] = str(c["_id"])
                success = await mysql_backup_service.backup_course(c)
                if success:
                    results["synced"] += 1
                else:
                    results["skipped"] += 1
            except Exception as e:
                results["failed"] += 1
        
        print(f"✅ Courses sync complete: {results['synced']} synced")
        return {"success": True, "collection": "courses", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-all")
async def sync_all_collections_to_mysql(user: dict = Depends(require_instructor)):
    """
    Sync ALL collections from MongoDB to MySQL:
    - users
    - courses
    - questions
    - quiz_answers
    - session_reports
    """
    if not mysql_backup.is_connected:
        raise HTTPException(status_code=503, detail="MySQL backup is not connected")
    
    database = get_database()
    if database is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    
    all_results = {}
    
    # Sync Users
    try:
        users = await database.users.find({}).to_list(length=None)
        synced = 0
        for u in users:
            u["id"] = str(u["_id"])
            if await mysql_backup_service.backup_user(u):
                synced += 1
        all_results["users"] = {"total": len(users), "synced": synced}
    except Exception as e:
        all_results["users"] = {"error": str(e)}
    
    # Sync Courses
    try:
        courses = await database.courses.find({}).to_list(length=None)
        synced = 0
        for c in courses:
            c["id"] = str(c["_id"])
            if await mysql_backup_service.backup_course(c):
                synced += 1
        all_results["courses"] = {"total": len(courses), "synced": synced}
    except Exception as e:
        all_results["courses"] = {"error": str(e)}
    
    # Sync Questions
    try:
        questions = await database.questions.find({}).to_list(length=None)
        synced = 0
        for q in questions:
            q["id"] = str(q["_id"])
            if await mysql_backup_service.backup_question(q):
                synced += 1
        all_results["questions"] = {"total": len(questions), "synced": synced}
    except Exception as e:
        all_results["questions"] = {"error": str(e)}
    
    # Sync Quiz Answers
    try:
        answers = await database.quiz_answers.find({}).to_list(length=None)
        synced = 0
        for a in answers:
            a["id"] = str(a["_id"])
            if await mysql_backup_service.backup_quiz_answer(a):
                synced += 1
        all_results["quiz_answers"] = {"total": len(answers), "synced": synced}
    except Exception as e:
        all_results["quiz_answers"] = {"error": str(e)}
    
    # Sync Session Reports
    try:
        reports = await database.session_reports.find({"reportType": "master"}).to_list(length=None)
        synced = 0
        for r in reports:
            r["id"] = str(r["_id"])
            if await mysql_backup_service.backup_session_report(r):
                synced += 1
        all_results["session_reports"] = {"total": len(reports), "synced": synced}
    except Exception as e:
        all_results["session_reports"] = {"error": str(e)}
    
    return {
        "success": True,
        "message": "All collections synced from MongoDB to MySQL",
        "results": all_results
    }


@router.get("/status")
async def get_sync_status(user: dict = Depends(require_instructor)):
    """
    Get sync status - compare counts between MongoDB and MySQL.
    """
    database = get_database()
    if database is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    
    # Count in MongoDB
    mongo_count = await database.session_reports.count_documents({"reportType": "master"})
    
    # Count in MySQL
    mysql_count = 0
    mysql_connected = mysql_backup.is_connected
    
    if mysql_connected:
        try:
            async with mysql_backup.get_connection() as conn:
                if conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute("SELECT COUNT(*) FROM session_reports_backup")
                        result = await cursor.fetchone()
                        mysql_count = result[0] if result else 0
        except Exception as e:
            print(f"Error counting MySQL records: {e}")
    
    return {
        "mongodb": {
            "connected": True,
            "report_count": mongo_count
        },
        "mysql": {
            "connected": mysql_connected,
            "report_count": mysql_count
        },
        "sync_status": "in_sync" if mongo_count == mysql_count else "needs_sync",
        "missing_in_mysql": mongo_count - mysql_count
    }


@router.get("/mysql-data")
async def get_mysql_data(user: dict = Depends(require_instructor)):
    """
    View data stored in MySQL backup tables.
    Shows flattened data (not the full JSON document).
    """
    if not mysql_backup.is_connected:
        raise HTTPException(status_code=503, detail="MySQL not connected")
    
    try:
        async with mysql_backup.get_connection() as conn:
            if not conn:
                raise HTTPException(status_code=503, detail="Failed to get MySQL connection")
            
            async with conn.cursor() as cursor:
                # Get session reports
                await cursor.execute("""
                    SELECT 
                        id, mongo_id, session_id, session_title, course_name,
                        instructor_name, session_date, total_participants,
                        total_questions_asked, average_quiz_score, backed_up_at
                    FROM session_reports_backup
                    ORDER BY backed_up_at DESC
                    LIMIT 50
                """)
                
                columns = [
                    "id", "mongo_id", "session_id", "session_title", "course_name",
                    "instructor_name", "session_date", "total_participants",
                    "total_questions_asked", "average_quiz_score", "backed_up_at"
                ]
                
                reports = []
                rows = await cursor.fetchall()
                for row in rows:
                    report = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        # Convert datetime to string
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        report[col] = value
                    reports.append(report)
                
                # Get student participation count
                await cursor.execute("SELECT COUNT(*) FROM student_participation_backup")
                student_count = (await cursor.fetchone())[0]
                
                return {
                    "success": True,
                    "session_reports": {
                        "count": len(reports),
                        "data": reports
                    },
                    "student_participation": {
                        "total_records": student_count
                    }
                }
                
    except Exception as e:
        print(f"Error fetching MySQL data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch MySQL data: {str(e)}")


@router.delete("/clear-mysql")
async def clear_mysql_backup(user: dict = Depends(require_instructor)):
    """
    Clear all data from MySQL backup tables.
    WARNING: This deletes all MySQL backup data. MongoDB data is NOT affected.
    """
    if not mysql_backup.is_connected:
        raise HTTPException(status_code=503, detail="MySQL not connected")
    
    try:
        async with mysql_backup.get_connection() as conn:
            if not conn:
                raise HTTPException(status_code=503, detail="Failed to get MySQL connection")
            
            async with conn.cursor() as cursor:
                # Delete student participation first (foreign key dependency)
                await cursor.execute("DELETE FROM student_participation_backup")
                students_deleted = cursor.rowcount
                
                # Delete session reports
                await cursor.execute("DELETE FROM session_reports_backup")
                reports_deleted = cursor.rowcount
                
                return {
                    "success": True,
                    "message": "MySQL backup data cleared",
                    "deleted": {
                        "session_reports": reports_deleted,
                        "student_participation": students_deleted
                    },
                    "note": "MongoDB data was NOT affected"
                }
                
    except Exception as e:
        print(f"Error clearing MySQL data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear MySQL data: {str(e)}")

