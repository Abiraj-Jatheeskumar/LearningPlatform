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
    
    Process:
    1. Read all reports from MongoDB session_reports collection
    2. Transform each document to MySQL table format
    3. Insert into MySQL (skip duplicates)
    
    This is idempotent - running multiple times won't create duplicates.
    """
    if not mysql_backup.is_connected:
        raise HTTPException(
            status_code=503, 
            detail="MySQL backup is not connected. Please configure MySQL first."
        )
    
    database = get_database()
    if not database:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    
    results = {
        "total_in_mongodb": 0,
        "synced_to_mysql": 0,
        "already_exists": 0,
        "failed": 0,
        "errors": []
    }
    
    try:
        # Step 1: Read ALL reports from MongoDB
        cursor = database.session_reports.find({"reportType": "master"})
        reports = await cursor.to_list(length=None)
        results["total_in_mongodb"] = len(reports)
        
        print(f"📊 Found {len(reports)} reports in MongoDB to sync")
        
        # Step 2 & 3: Transform and Insert each report
        for report in reports:
            try:
                # Convert ObjectId to string
                report["id"] = str(report["_id"])
                
                # Call backup service (handles transformation internally)
                success = await mysql_backup_service.backup_session_report(report)
                
                if success:
                    results["synced_to_mysql"] += 1
                else:
                    results["already_exists"] += 1
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Report {report.get('_id')}: {str(e)}")
                print(f"❌ Failed to sync report: {e}")
        
        print(f"✅ Sync complete: {results['synced_to_mysql']} synced, {results['already_exists']} already existed")
        
        return {
            "success": True,
            "message": "MongoDB → MySQL sync completed",
            "results": results
        }
        
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/status")
async def get_sync_status(user: dict = Depends(require_instructor)):
    """
    Get sync status - compare counts between MongoDB and MySQL.
    """
    database = get_database()
    if not database:
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

