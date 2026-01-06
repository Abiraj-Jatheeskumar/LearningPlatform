# src/routers/instructor_reports.py
"""
Instructor Reports API
======================
Endpoints for instructors to view reports for their sessions.
Includes: Session Summary, Quiz Performance, Engagement Activity reports.

Access Control:
- Only instructors can access these endpoints
- Instructors can only view reports for sessions they created
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from src.database.connection import db
from src.middleware.auth import get_current_user, require_instructor

router = APIRouter(prefix="/api/instructor/reports", tags=["Instructor Reports"])


# ============================================================
# 1. SESSION SUMMARY REPORT
# ============================================================
@router.get("/sessions")
async def get_session_summary_report(user: dict = Depends(require_instructor)):
    """
    Get summary of all sessions created by the instructor.
    Returns: List of sessions with participant counts and status.
    """
    try:
        instructor_id = user.get("id")
        
        # Get all sessions by this instructor
        sessions = []
        async for session in db.database.sessions.find({"instructorId": instructor_id}).sort("date", -1):
            session_id = str(session["_id"])
            
            # Count participants for this session
            participant_count = await db.database.session_participants.count_documents({
                "sessionId": session_id
            })
            
            sessions.append({
                "sessionId": session_id,
                "sessionName": session.get("title", "Untitled Session"),
                "courseName": session.get("course", ""),
                "courseCode": session.get("courseCode", ""),
                "date": session.get("date", ""),
                "time": session.get("time", ""),
                "duration": session.get("duration", ""),
                "status": session.get("status", "upcoming"),
                "totalStudentsJoined": participant_count,
                "zoomMeetingId": str(session.get("zoomMeetingId")) if session.get("zoomMeetingId") else None,
                "actualStartTime": session.get("actualStartTime"),
                "actualEndTime": session.get("actualEndTime")
            })
        
        return {
            "success": True,
            "totalSessions": len(sessions),
            "sessions": sessions
        }
        
    except Exception as e:
        print(f"Error fetching session summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch session summary")


@router.get("/sessions/{session_id}/attendance")
async def get_session_attendance_report(
    session_id: str,
    user: dict = Depends(require_instructor)
):
    """
    Get detailed attendance report for a specific session.
    Shows: Each student's join time, leave time, and total duration.
    """
    try:
        instructor_id = user.get("id")
        
        # Verify session belongs to instructor
        session = await db.database.sessions.find_one({"_id": ObjectId(session_id)})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.get("instructorId") != instructor_id:
            raise HTTPException(status_code=403, detail="You can only view reports for your own sessions")
        
        # Get all participants with their attendance data
        attendance_data = []
        async for participant in db.database.session_participants.find({"sessionId": session_id}):
            joined_at = participant.get("joinedAt")
            left_at = participant.get("leftAt")
            
            # Calculate duration in minutes
            duration_minutes = None
            if joined_at and left_at:
                duration_minutes = int((left_at - joined_at).total_seconds() / 60)
            elif joined_at:
                # Still in session or didn't leave properly
                duration_minutes = int((datetime.utcnow() - joined_at).total_seconds() / 60)
            
            attendance_data.append({
                "studentId": participant.get("studentId"),
                "studentName": participant.get("studentName", "Unknown Student"),
                "studentEmail": participant.get("studentEmail", ""),
                "joinTime": joined_at.isoformat() if joined_at else None,
                "leaveTime": left_at.isoformat() if left_at else None,
                "durationMinutes": duration_minutes,
                "status": participant.get("status", "unknown")
            })
        
        # Sort by join time
        attendance_data.sort(key=lambda x: x["joinTime"] or "", reverse=True)
        
        return {
            "success": True,
            "sessionId": session_id,
            "sessionName": session.get("title", ""),
            "sessionDate": session.get("date", ""),
            "totalStudents": len(attendance_data),
            "attendance": attendance_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching attendance report: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch attendance report")


# ============================================================
# 2. QUIZ PERFORMANCE REPORT
# ============================================================
@router.get("/sessions/{session_id}/quiz-performance")
async def get_quiz_performance_report(
    session_id: str,
    user: dict = Depends(require_instructor)
):
    """
    Get quiz performance report for a specific session.
    Shows: Each student's quiz scores, correct/incorrect answers.
    """
    try:
        instructor_id = user.get("id")
        
        # Verify session belongs to instructor
        session = await db.database.sessions.find_one({"_id": ObjectId(session_id)})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.get("instructorId") != instructor_id:
            raise HTTPException(status_code=403, detail="You can only view reports for your own sessions")
        
        # Get question assignments for this session
        assignments = []
        async for assignment in db.database.question_assignments.find({"sessionId": session_id}):
            assignments.append(assignment)
        
        # Get quiz answers for this session
        quiz_answers = []
        async for answer in db.database.quiz_answers.find({"sessionId": session_id}):
            quiz_answers.append(answer)
        
        # Get participants for this session
        participants = {}
        async for p in db.database.session_participants.find({"sessionId": session_id}):
            participants[p.get("studentId")] = {
                "studentName": p.get("studentName", "Unknown"),
                "studentEmail": p.get("studentEmail", "")
            }
        
        # Aggregate performance by student
        student_performance = {}
        
        for assignment in assignments:
            student_id = assignment.get("studentId")
            if student_id not in student_performance:
                student_info = participants.get(student_id, {})
                student_performance[student_id] = {
                    "studentId": student_id,
                    "studentName": student_info.get("studentName", "Unknown"),
                    "studentEmail": student_info.get("studentEmail", ""),
                    "totalQuestions": 0,
                    "correctAnswers": 0,
                    "incorrectAnswers": 0,
                    "unanswered": 0,
                    "totalResponseTime": 0,
                    "answeredCount": 0
                }
            
            student_performance[student_id]["totalQuestions"] += 1
            
            if assignment.get("answerIndex") is not None:
                if assignment.get("isCorrect"):
                    student_performance[student_id]["correctAnswers"] += 1
                else:
                    student_performance[student_id]["incorrectAnswers"] += 1
                
                if assignment.get("timeTaken"):
                    student_performance[student_id]["totalResponseTime"] += assignment.get("timeTaken")
                    student_performance[student_id]["answeredCount"] += 1
            else:
                student_performance[student_id]["unanswered"] += 1
        
        # Calculate scores and averages
        performance_list = []
        for student_id, perf in student_performance.items():
            total = perf["totalQuestions"]
            correct = perf["correctAnswers"]
            score = (correct / total * 100) if total > 0 else 0
            avg_time = (perf["totalResponseTime"] / perf["answeredCount"]) if perf["answeredCount"] > 0 else None
            
            performance_list.append({
                "studentId": student_id,
                "studentName": perf["studentName"],
                "studentEmail": perf["studentEmail"],
                "totalQuestions": total,
                "correctAnswers": correct,
                "incorrectAnswers": perf["incorrectAnswers"],
                "unanswered": perf["unanswered"],
                "score": round(score, 1),
                "averageResponseTime": round(avg_time, 2) if avg_time else None
            })
        
        # Sort by score descending
        performance_list.sort(key=lambda x: x["score"], reverse=True)
        
        # Calculate class averages
        total_students = len(performance_list)
        avg_score = sum(p["score"] for p in performance_list) / total_students if total_students > 0 else 0
        
        return {
            "success": True,
            "sessionId": session_id,
            "sessionName": session.get("title", ""),
            "totalQuestions": len(set(a.get("questionId") for a in assignments)),
            "totalParticipants": total_students,
            "classAverageScore": round(avg_score, 1),
            "studentPerformance": performance_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching quiz performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch quiz performance report")


# ============================================================
# 3. ENGAGEMENT ACTIVITY REPORT
# ============================================================
@router.get("/sessions/{session_id}/engagement")
async def get_engagement_report(
    session_id: str,
    user: dict = Depends(require_instructor)
):
    """
    Get engagement activity report for a specific session.
    Shows: Number of interactions per student, participation metrics.
    """
    try:
        instructor_id = user.get("id")
        
        # Verify session belongs to instructor
        session = await db.database.sessions.find_one({"_id": ObjectId(session_id)})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.get("instructorId") != instructor_id:
            raise HTTPException(status_code=403, detail="You can only view reports for your own sessions")
        
        # Get participants
        participants = {}
        async for p in db.database.session_participants.find({"sessionId": session_id}):
            student_id = p.get("studentId")
            participants[student_id] = {
                "studentId": student_id,
                "studentName": p.get("studentName", "Unknown"),
                "studentEmail": p.get("studentEmail", ""),
                "joinedAt": p.get("joinedAt"),
                "leftAt": p.get("leftAt")
            }
        
        # Count quiz interactions per student
        quiz_interactions = {}
        async for answer in db.database.quiz_answers.find({"sessionId": session_id}):
            student_id = answer.get("studentId")
            if student_id not in quiz_interactions:
                quiz_interactions[student_id] = 0
            quiz_interactions[student_id] += 1
        
        # Count question assignments answered
        assignments_answered = {}
        async for assignment in db.database.question_assignments.find({
            "sessionId": session_id,
            "answerIndex": {"$ne": None}
        }):
            student_id = assignment.get("studentId")
            if student_id not in assignments_answered:
                assignments_answered[student_id] = 0
            assignments_answered[student_id] += 1
        
        # Get latency/connection data
        connection_data = {}
        async for metric in db.database.latency_metrics.find({"session_id": session_id}):
            student_id = metric.get("student_id")
            connection_data[student_id] = metric.get("overall_quality", "unknown")
        
        # Build engagement report
        engagement_list = []
        for student_id, info in participants.items():
            quiz_count = quiz_interactions.get(student_id, 0)
            answered_count = assignments_answered.get(student_id, 0)
            connection = connection_data.get(student_id, "unknown")
            
            # Calculate attendance duration
            duration_minutes = None
            if info.get("joinedAt") and info.get("leftAt"):
                duration_minutes = int((info["leftAt"] - info["joinedAt"]).total_seconds() / 60)
            
            # Determine engagement level based on quiz participation
            if answered_count >= 3:
                engagement_level = "High"
            elif answered_count >= 1:
                engagement_level = "Medium"
            else:
                engagement_level = "Low"
            
            engagement_list.append({
                "studentId": student_id,
                "studentName": info["studentName"],
                "studentEmail": info["studentEmail"],
                "quizInteractions": quiz_count,
                "questionsAnswered": answered_count,
                "attendanceDuration": duration_minutes,
                "connectionQuality": connection,
                "engagementLevel": engagement_level
            })
        
        # Sort by engagement (questions answered)
        engagement_list.sort(key=lambda x: x["questionsAnswered"], reverse=True)
        
        # Calculate summary stats
        total_students = len(engagement_list)
        high_engagement = sum(1 for e in engagement_list if e["engagementLevel"] == "High")
        medium_engagement = sum(1 for e in engagement_list if e["engagementLevel"] == "Medium")
        low_engagement = sum(1 for e in engagement_list if e["engagementLevel"] == "Low")
        
        return {
            "success": True,
            "sessionId": session_id,
            "sessionName": session.get("title", ""),
            "totalParticipants": total_students,
            "engagementSummary": {
                "highEngagement": high_engagement,
                "mediumEngagement": medium_engagement,
                "lowEngagement": low_engagement
            },
            "studentEngagement": engagement_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching engagement report: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch engagement report")


# ============================================================
# 4. OVERALL INSTRUCTOR DASHBOARD STATS
# ============================================================
@router.get("/dashboard-stats")
async def get_instructor_dashboard_stats(user: dict = Depends(require_instructor)):
    """
    Get overall statistics for instructor dashboard.
    """
    try:
        instructor_id = user.get("id")
        
        # Count sessions
        total_sessions = await db.database.sessions.count_documents({"instructorId": instructor_id})
        completed_sessions = await db.database.sessions.count_documents({
            "instructorId": instructor_id,
            "status": "completed"
        })
        live_sessions = await db.database.sessions.count_documents({
            "instructorId": instructor_id,
            "status": "live"
        })
        
        # Get session IDs for this instructor
        session_ids = []
        async for session in db.database.sessions.find({"instructorId": instructor_id}, {"_id": 1}):
            session_ids.append(str(session["_id"]))
        
        # Count total participants across all sessions
        total_participants = await db.database.session_participants.count_documents({
            "sessionId": {"$in": session_ids}
        })
        
        # Count total quiz questions asked
        total_questions = await db.database.question_assignments.count_documents({
            "sessionId": {"$in": session_ids}
        })
        
        # Calculate average quiz score
        pipeline = [
            {"$match": {"sessionId": {"$in": session_ids}}},
            {"$group": {
                "_id": None,
                "total": {"$sum": 1},
                "correct": {"$sum": {"$cond": ["$isCorrect", 1, 0]}}
            }}
        ]
        
        result = await db.database.question_assignments.aggregate(pipeline).to_list(length=1)
        avg_score = 0
        if result and result[0]["total"] > 0:
            avg_score = round((result[0]["correct"] / result[0]["total"]) * 100, 1)
        
        return {
            "success": True,
            "stats": {
                "totalSessions": total_sessions,
                "completedSessions": completed_sessions,
                "liveSessions": live_sessions,
                "upcomingSessions": total_sessions - completed_sessions - live_sessions,
                "totalParticipants": total_participants,
                "totalQuestionsAsked": total_questions,
                "averageQuizScore": avg_score
            }
        }
        
    except Exception as e:
        print(f"Error fetching dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard stats")

