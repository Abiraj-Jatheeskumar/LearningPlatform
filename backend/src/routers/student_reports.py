# src/routers/student_reports.py
"""
Student Reports API
===================
Endpoints for students to view their personal reports.
Students can ONLY see their own data - never other students' data.

USES STORED REPORTS FROM MongoDB when available.
Students only see their own personal data from the stored reports.

Includes:
- Attendance Report (sessions attended, join/leave times, duration)
- Quiz Report (quizzes attempted, scores, correct/incorrect)
- Session History (all sessions joined)
- Stored Session Reports (from MongoDB after session ends)
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from src.database.connection import db
from src.middleware.auth import get_current_user
from src.models.session_report_model import SessionReportModel

router = APIRouter(prefix="/api/student/reports", tags=["Student Reports"])


def require_student(user: dict = Depends(get_current_user)):
    """Middleware to ensure user is a student"""
    if user.get("role") not in ["student"]:
        raise HTTPException(status_code=403, detail="Only students can access this endpoint")
    return user


# ============================================================
# 1. ATTENDANCE REPORT - Student's own attendance
# ============================================================
@router.get("/attendance")
async def get_my_attendance_report(user: dict = Depends(require_student)):
    """
    Get student's attendance report across all sessions.
    Shows: Sessions attended, join time, leave time, duration.
    Student can ONLY see their own attendance data.
    """
    try:
        student_id = user.get("id")
        
        # Get all sessions this student participated in
        attendance_records = []
        async for participant in db.database.session_participants.find({"studentId": student_id}):
            session_id = participant.get("sessionId")
            
            # Get session details
            try:
                session = await db.database.sessions.find_one({"_id": ObjectId(session_id)})
            except:
                session = None
            
            if not session:
                continue
            
            joined_at = participant.get("joinedAt")
            left_at = participant.get("leftAt")
            
            # Calculate duration
            duration_minutes = None
            if joined_at and left_at:
                duration_minutes = int((left_at - joined_at).total_seconds() / 60)
            elif joined_at:
                duration_minutes = int((datetime.utcnow() - joined_at).total_seconds() / 60)
            
            attendance_records.append({
                "sessionId": session_id,
                "sessionName": session.get("title", "Unknown Session"),
                "courseName": session.get("course", ""),
                "courseCode": session.get("courseCode", ""),
                "instructorName": session.get("instructor", ""),
                "sessionDate": session.get("date", ""),
                "sessionTime": session.get("time", ""),
                "sessionStatus": session.get("status", ""),
                "joinTime": joined_at.isoformat() if joined_at else None,
                "leaveTime": left_at.isoformat() if left_at else None,
                "durationMinutes": duration_minutes,
                "attendanceStatus": participant.get("status", "unknown")
            })
        
        # Sort by date (most recent first)
        attendance_records.sort(key=lambda x: x["sessionDate"] or "", reverse=True)
        
        # Calculate summary stats
        total_sessions = len(attendance_records)
        total_duration = sum(r["durationMinutes"] or 0 for r in attendance_records)
        
        return {
            "success": True,
            "studentId": student_id,
            "studentName": f"{user.get('firstName', '')} {user.get('lastName', '')}".strip(),
            "summary": {
                "totalSessionsAttended": total_sessions,
                "totalMinutesAttended": total_duration,
                "averageDurationPerSession": round(total_duration / total_sessions, 1) if total_sessions > 0 else 0
            },
            "attendance": attendance_records
        }
        
    except Exception as e:
        print(f"Error fetching student attendance: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch attendance report")


# ============================================================
# 2. QUIZ REPORT - Student's own quiz performance
# ============================================================
@router.get("/quiz")
async def get_my_quiz_report(user: dict = Depends(require_student)):
    """
    Get student's quiz performance across all sessions.
    Shows: Quizzes attempted, correct/incorrect answers, scores.
    Student can ONLY see their own quiz data.
    """
    try:
        student_id = user.get("id")
        
        # Get all quiz assignments for this student
        quiz_by_session = {}
        
        async for assignment in db.database.question_assignments.find({"studentId": student_id}):
            session_id = assignment.get("sessionId")
            
            if session_id not in quiz_by_session:
                # Get session info
                try:
                    session = await db.database.sessions.find_one({"_id": ObjectId(session_id)})
                except:
                    session = None
                
                quiz_by_session[session_id] = {
                    "sessionId": session_id,
                    "sessionName": session.get("title", "Unknown") if session else "Unknown",
                    "courseName": session.get("course", "") if session else "",
                    "sessionDate": session.get("date", "") if session else "",
                    "totalQuestions": 0,
                    "correctAnswers": 0,
                    "incorrectAnswers": 0,
                    "unanswered": 0,
                    "totalResponseTime": 0,
                    "answeredCount": 0,
                    "questions": []
                }
            
            quiz_by_session[session_id]["totalQuestions"] += 1
            
            # Get question details
            question_id = assignment.get("questionId")
            question_text = "Unknown Question"
            try:
                question = await db.database.questions.find_one({"_id": ObjectId(question_id)})
                if question:
                    question_text = question.get("question", "Unknown Question")
            except:
                pass
            
            question_detail = {
                "questionId": question_id,
                "question": question_text,
                "yourAnswer": assignment.get("answerIndex"),
                "isCorrect": assignment.get("isCorrect"),
                "timeTaken": assignment.get("timeTaken"),
                "answeredAt": assignment.get("answeredAt").isoformat() if assignment.get("answeredAt") else None
            }
            
            quiz_by_session[session_id]["questions"].append(question_detail)
            
            if assignment.get("answerIndex") is not None:
                if assignment.get("isCorrect"):
                    quiz_by_session[session_id]["correctAnswers"] += 1
                else:
                    quiz_by_session[session_id]["incorrectAnswers"] += 1
                
                if assignment.get("timeTaken"):
                    quiz_by_session[session_id]["totalResponseTime"] += assignment.get("timeTaken")
                    quiz_by_session[session_id]["answeredCount"] += 1
            else:
                quiz_by_session[session_id]["unanswered"] += 1
        
        # Calculate scores for each session
        session_quizzes = []
        for session_id, data in quiz_by_session.items():
            total = data["totalQuestions"]
            correct = data["correctAnswers"]
            score = (correct / total * 100) if total > 0 else 0
            avg_time = (data["totalResponseTime"] / data["answeredCount"]) if data["answeredCount"] > 0 else None
            
            session_quizzes.append({
                "sessionId": data["sessionId"],
                "sessionName": data["sessionName"],
                "courseName": data["courseName"],
                "sessionDate": data["sessionDate"],
                "totalQuestions": total,
                "correctAnswers": correct,
                "incorrectAnswers": data["incorrectAnswers"],
                "unanswered": data["unanswered"],
                "score": round(score, 1),
                "averageResponseTime": round(avg_time, 2) if avg_time else None,
                "questionDetails": data["questions"]
            })
        
        # Sort by date (most recent first)
        session_quizzes.sort(key=lambda x: x["sessionDate"] or "", reverse=True)
        
        # Calculate overall stats
        total_questions = sum(q["totalQuestions"] for q in session_quizzes)
        total_correct = sum(q["correctAnswers"] for q in session_quizzes)
        overall_score = (total_correct / total_questions * 100) if total_questions > 0 else 0
        
        return {
            "success": True,
            "studentId": student_id,
            "studentName": f"{user.get('firstName', '')} {user.get('lastName', '')}".strip(),
            "overallStats": {
                "totalSessionsWithQuiz": len(session_quizzes),
                "totalQuestionsAttempted": total_questions,
                "totalCorrectAnswers": total_correct,
                "overallScore": round(overall_score, 1)
            },
            "sessionQuizzes": session_quizzes
        }
        
    except Exception as e:
        print(f"Error fetching student quiz report: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch quiz report")


# ============================================================
# 3. SESSION HISTORY - All sessions student joined
# ============================================================
@router.get("/session-history")
async def get_my_session_history(user: dict = Depends(require_student)):
    """
    Get student's session history.
    Shows: All sessions joined, quiz participation status.
    Student can ONLY see their own session history.
    """
    try:
        student_id = user.get("id")
        
        # Get all sessions this student participated in
        session_history = []
        async for participant in db.database.session_participants.find({"studentId": student_id}):
            session_id = participant.get("sessionId")
            
            # Get session details
            try:
                session = await db.database.sessions.find_one({"_id": ObjectId(session_id)})
            except:
                session = None
            
            if not session:
                continue
            
            # Check quiz participation
            quiz_count = await db.database.question_assignments.count_documents({
                "sessionId": session_id,
                "studentId": student_id
            })
            
            quiz_answered = await db.database.question_assignments.count_documents({
                "sessionId": session_id,
                "studentId": student_id,
                "answerIndex": {"$ne": None}
            })
            
            quiz_correct = await db.database.question_assignments.count_documents({
                "sessionId": session_id,
                "studentId": student_id,
                "isCorrect": True
            })
            
            joined_at = participant.get("joinedAt")
            left_at = participant.get("leftAt")
            duration = None
            if joined_at and left_at:
                duration = int((left_at - joined_at).total_seconds() / 60)
            
            session_history.append({
                "sessionId": session_id,
                "sessionName": session.get("title", "Unknown"),
                "courseName": session.get("course", ""),
                "courseCode": session.get("courseCode", ""),
                "instructorName": session.get("instructor", ""),
                "sessionDate": session.get("date", ""),
                "sessionTime": session.get("time", ""),
                "sessionStatus": session.get("status", ""),
                "joinedAt": joined_at.isoformat() if joined_at else None,
                "leftAt": left_at.isoformat() if left_at else None,
                "durationMinutes": duration,
                "quizParticipation": {
                    "totalQuestions": quiz_count,
                    "questionsAnswered": quiz_answered,
                    "correctAnswers": quiz_correct,
                    "score": round((quiz_correct / quiz_count * 100), 1) if quiz_count > 0 else None
                }
            })
        
        # Sort by date (most recent first)
        session_history.sort(key=lambda x: x["sessionDate"] or "", reverse=True)
        
        return {
            "success": True,
            "studentId": student_id,
            "studentName": f"{user.get('firstName', '')} {user.get('lastName', '')}".strip(),
            "totalSessions": len(session_history),
            "sessionHistory": session_history
        }
        
    except Exception as e:
        print(f"Error fetching session history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch session history")


# ============================================================
# 4. STUDENT DASHBOARD STATS
# ============================================================
@router.get("/dashboard-stats")
async def get_my_dashboard_stats(user: dict = Depends(require_student)):
    """
    Get summary statistics for student dashboard.
    Student can ONLY see their own stats.
    """
    try:
        student_id = user.get("id")
        
        # Count sessions attended
        sessions_attended = await db.database.session_participants.count_documents({
            "studentId": student_id
        })
        
        # Get quiz stats
        total_questions = await db.database.question_assignments.count_documents({
            "studentId": student_id
        })
        
        correct_answers = await db.database.question_assignments.count_documents({
            "studentId": student_id,
            "isCorrect": True
        })
        
        # Calculate overall score
        overall_score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        # Calculate total attendance time
        total_minutes = 0
        async for p in db.database.session_participants.find({"studentId": student_id}):
            if p.get("joinedAt") and p.get("leftAt"):
                duration = int((p["leftAt"] - p["joinedAt"]).total_seconds() / 60)
                total_minutes += duration
        
        # Get enrolled courses count
        enrolled_courses = await db.database.course_enrollments.count_documents({
            "studentId": student_id
        })
        
        return {
            "success": True,
            "studentId": student_id,
            "studentName": f"{user.get('firstName', '')} {user.get('lastName', '')}".strip(),
            "stats": {
                "sessionsAttended": sessions_attended,
                "totalQuizQuestions": total_questions,
                "correctAnswers": correct_answers,
                "overallQuizScore": round(overall_score, 1),
                "totalAttendanceMinutes": total_minutes,
                "enrolledCourses": enrolled_courses
            }
        }
        
    except Exception as e:
        print(f"Error fetching student stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard stats")


# ============================================================
# 5. GET STORED REPORT FOR A SESSION (Student's own data only)
# ============================================================
@router.get("/sessions/{session_id}/stored-report")
async def get_my_stored_session_report(
    session_id: str,
    user: dict = Depends(require_student)
):
    """
    Get the STORED report from MongoDB for a session.
    Student can ONLY see their own personal data from the report.
    """
    try:
        student_id = user.get("id")
        
        # Verify student participated in this session
        participant = await db.database.session_participants.find_one({
            "sessionId": session_id,
            "studentId": student_id
        })
        
        if not participant:
            raise HTTPException(status_code=403, detail="You did not participate in this session")
        
        # Get session info
        try:
            session = await db.database.sessions.find_one({"_id": ObjectId(session_id)})
        except:
            session = None
        
        # Get stored report from MongoDB
        stored_report = await SessionReportModel.get_stored_master_report(session_id)
        
        if not stored_report:
            return {
                "success": False,
                "stored": False,
                "message": "No stored report found. Report is available after the session ends.",
                "sessionStatus": session.get("status", "unknown") if session else "unknown",
                "sessionId": session_id,
                "report": None
            }
        
        # Filter to only include THIS student's data
        student_data = None
        for s in stored_report.get("students", []):
            if s.get("studentId") == student_id:
                student_data = s
                break
        
        # Create personalized report for student
        personal_report = {
            "sessionId": stored_report.get("sessionId"),
            "sessionTitle": stored_report.get("sessionTitle"),
            "courseName": stored_report.get("courseName"),
            "courseCode": stored_report.get("courseCode"),
            "instructorName": stored_report.get("instructorName"),
            "sessionDate": stored_report.get("sessionDate"),
            "sessionTime": stored_report.get("sessionTime"),
            "sessionDuration": stored_report.get("sessionDuration"),
            "generatedAt": stored_report.get("generatedAt"),
            # Personal data only
            "myData": student_data
        }
        
        return {
            "success": True,
            "stored": True,
            "message": "Your personal report retrieved from MongoDB",
            "sessionId": session_id,
            "sessionStatus": session.get("status", "completed") if session else "completed",
            "report": personal_report
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching student stored report: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stored report")


# ============================================================
# 6. GET ALL MY STORED REPORTS
# ============================================================
@router.get("/stored-reports")
async def get_all_my_stored_reports(user: dict = Depends(require_student)):
    """
    Get all stored reports from MongoDB where the student participated.
    Only shows student's own data from each report.
    """
    try:
        student_id = user.get("id")
        
        # Get all reports where this student participated
        reports = []
        async for report in db.database.session_reports.find({
            "students.studentId": student_id,
            "reportType": "master"
        }).sort("generatedAt", -1):
            
            # Find this student's data in the report
            student_data = None
            for s in report.get("students", []):
                if s.get("studentId") == student_id:
                    student_data = s
                    break
            
            if student_data:
                reports.append({
                    "reportId": str(report["_id"]),
                    "sessionId": report.get("sessionId"),
                    "sessionTitle": report.get("sessionTitle"),
                    "courseName": report.get("courseName"),
                    "sessionDate": report.get("sessionDate"),
                    "generatedAt": report.get("generatedAt"),
                    # My personal summary
                    "myTotalQuestions": student_data.get("totalQuestions", 0),
                    "myCorrectAnswers": student_data.get("correctAnswers", 0),
                    "myScore": student_data.get("quizScore"),
                    "myAttendanceDuration": student_data.get("attendanceDuration")
                })
        
        return {
            "success": True,
            "totalReports": len(reports),
            "reports": reports
        }
        
    except Exception as e:
        print(f"Error fetching student stored reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stored reports")

