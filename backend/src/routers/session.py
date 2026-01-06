# src/routers/session.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from src.database.connection import db
from src.middleware.auth import get_current_user, require_instructor
from src.services.zoom_service import create_zoom_meeting, ZoomServiceError
from src.models.course import CourseModel
from src.models.session_report_model import SessionReportModel
from src.services.email_service import email_service

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


class SessionCreate(BaseModel):
    title: str
    course: str  # Course name for display
    courseCode: str
    courseId: Optional[str] = None  # Link to Course document for access control
    date: str          # "2025-11-25"
    time: str          # "10:00 AM - 11:00 AM" or "10:00"
    durationMinutes: int
    timezone: str = "Asia/Colombo"


class SessionOut(BaseModel):
    id: str
    title: str
    course: str
    courseCode: str
    courseId: Optional[str] = None  # Link to Course document
    instructor: str
    instructorId: Optional[str] = None  # Link to instructor user
    date: str
    time: str
    duration: str
    status: str
    participants: Optional[int] = 0
    expectedParticipants: Optional[int] = 0
    engagement: Optional[int] = 0
    recordingAvailable: Optional[bool] = False
    zoomMeetingId: Optional[str] = None
    join_url: Optional[str] = None
    start_url: Optional[str] = None


def _session_doc_to_out(doc, include_urls: bool = True) -> SessionOut:
    return SessionOut(
        id=str(doc["_id"]),
        title=doc["title"],
        course=doc["course"],
        courseCode=doc["courseCode"],
        courseId=doc.get("courseId"),
        instructor=doc["instructor"],
        instructorId=doc.get("instructorId"),
        date=doc["date"],
        time=doc["time"],
        duration=doc["duration"],
        status=doc.get("status", "upcoming"),
        participants=doc.get("participants", 0),
        expectedParticipants=doc.get("expectedParticipants", 0),
        engagement=doc.get("engagement", 0),
        recordingAvailable=doc.get("recordingAvailable", False),
        zoomMeetingId=str(doc.get("zoomMeetingId")) if doc.get("zoomMeetingId") else None,
        join_url=doc.get("join_url") if include_urls else None,
        start_url=doc.get("start_url") if include_urls else None,
    )


@router.post("", response_model=SessionOut)
async def create_session(
    payload: SessionCreate,
    user: dict = Depends(require_instructor),
):
    """
    Create session + Zoom meeting.
    Sessions are linked to courses. Only enrolled students can see the join URL.
    """
    try:
        # Verify course belongs to this instructor if courseId is provided
        if payload.courseId:
            course = await CourseModel.find_by_id(payload.courseId)
            if not course:
                raise HTTPException(status_code=404, detail="Course not found")
            if course["instructorId"] != user["id"]:
                raise HTTPException(status_code=403, detail="You can only create sessions for your own courses")

        # 1) parse date+time into ISO for Zoom
        # simple version: just use today's date/time string if parsing fails
        try:
            # Expect "HH:MM" 24h time
            dt = datetime.fromisoformat(f"{payload.date}T{payload.time}")
        except Exception:
            # fallback = now + 10 minutes
            dt = datetime.utcnow()

        zoom_time_iso = dt.isoformat(timespec="seconds")

        zoom = await create_zoom_meeting(
            topic=payload.title,
            start_time_iso=zoom_time_iso,
            duration_minutes=payload.durationMinutes,
            timezone=payload.timezone,
        )

        doc = {
            "title": payload.title,
            "course": payload.course,
            "courseCode": payload.courseCode,
            "courseId": payload.courseId,  # Link to Course for access control
            "instructor": f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
                          or user.get("email", "Unknown Instructor"),
            "instructorId": user["id"],  # Link to instructor user
            "date": payload.date,
            "time": payload.time,
            "duration": f"{payload.durationMinutes} minutes",
            "status": "upcoming",
            "participants": 0,
            "expectedParticipants": 0,
            "engagement": 0,
            "recordingAvailable": False,
            "zoomMeetingId": str(zoom["meeting_id"]),
            "join_url": zoom["join_url"],
            "start_url": zoom["start_url"],
            "createdAt": datetime.utcnow(),
        }

        result = await db.database.sessions.insert_one(doc)
        saved = await db.database.sessions.find_one({"_id": result.inserted_id})
        return _session_doc_to_out(saved)

    except ZoomServiceError as ze:
        raise HTTPException(status_code=400, detail=str(ze))
    except HTTPException:
        raise
    except Exception as e:
        print("Error creating session:", e)
        raise HTTPException(status_code=500, detail="Failed to create session")


@router.get("", response_model=List[SessionOut])
async def list_sessions(user: dict = Depends(get_current_user)):
    """
    List sessions based on user role:
    - Instructors: See only their own sessions (with full URLs)
    - Students: See only sessions from courses they're enrolled in (with join URLs)
    - Admin: See all sessions
    """
    user_role = user.get("role", "student")
    user_id = user.get("id")
    
    if user_role == "admin":
        # Admins see all sessions
        cursor = db.database.sessions.find().sort("date", -1)
        sessions = await cursor.to_list(length=None)
        return [_session_doc_to_out(doc) for doc in sessions]
    
    elif user_role == "instructor":
        # Instructors see only their own sessions
        cursor = db.database.sessions.find({"instructorId": user_id}).sort("date", -1)
        sessions = await cursor.to_list(length=None)
        return [_session_doc_to_out(doc) for doc in sessions]
    
    else:
        # Students see only sessions from courses they're enrolled in
        enrolled_courses = await CourseModel.find_enrolled_courses(user_id)
        enrolled_course_ids = [c["id"] for c in enrolled_courses]
        
        if not enrolled_course_ids:
            return []  # No enrolled courses = no sessions
        
        cursor = db.database.sessions.find({
            "courseId": {"$in": enrolled_course_ids}
        }).sort("date", -1)
        sessions = await cursor.to_list(length=None)
        
        # Include join URLs for enrolled students
        return [_session_doc_to_out(doc, include_urls=True) for doc in sessions]


@router.get("/instructor/my-sessions", response_model=List[SessionOut])
async def get_my_sessions(user: dict = Depends(require_instructor)):
    """Get all sessions created by the current instructor"""
    cursor = db.database.sessions.find({"instructorId": user["id"]}).sort("date", -1)
    sessions = await cursor.to_list(length=None)
    return [_session_doc_to_out(doc) for doc in sessions]


@router.get("/course/{course_id}", response_model=List[SessionOut])
async def get_sessions_by_course(course_id: str, user: dict = Depends(get_current_user)):
    """Get all sessions for a specific course"""
    user_role = user.get("role", "student")
    user_id = user.get("id")
    
    # Check if user has access to this course
    if user_role == "student":
        is_enrolled = await CourseModel.is_student_enrolled(course_id, user_id)
        if not is_enrolled:
            raise HTTPException(status_code=403, detail="You are not enrolled in this course")
    elif user_role == "instructor":
        course = await CourseModel.find_by_id(course_id)
        if course and course["instructorId"] != user_id:
            raise HTTPException(status_code=403, detail="You can only view sessions for your own courses")
    
    cursor = db.database.sessions.find({"courseId": course_id}).sort("date", -1)
    sessions = await cursor.to_list(length=None)
    return [_session_doc_to_out(doc) for doc in sessions]


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(session_id: str, user: dict = Depends(get_current_user)):
    """Get a specific session - access controlled based on enrollment"""
    try:
        doc = await db.database.sessions.find_one({"_id": ObjectId(session_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Session not found")
        
        user_role = user.get("role", "student")
        user_id = user.get("id")
        
        # Access control
        if user_role == "instructor":
            if doc.get("instructorId") != user_id:
                raise HTTPException(status_code=403, detail="You can only view your own sessions")
        elif user_role == "student":
            course_id = doc.get("courseId")
            if course_id:
                is_enrolled = await CourseModel.is_student_enrolled(course_id, user_id)
                if not is_enrolled:
                    raise HTTPException(status_code=403, detail="You are not enrolled in this course")
        
        return _session_doc_to_out(doc)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/{session_id}/end")
async def end_session(
    session_id: str,
    user: dict = Depends(require_instructor)
):
    """
    End a session and automatically generate report.
    - Marks session as 'completed'
    - Generates full report with all participant data
    - Saves report to MongoDB
    - Optionally sends email notifications to participants
    """
    try:
        # Verify session exists and belongs to this instructor
        session = await db.database.sessions.find_one({"_id": ObjectId(session_id)})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.get("instructorId") != user["id"]:
            raise HTTPException(status_code=403, detail="You can only end your own sessions")
        
        if session.get("status") == "completed":
            raise HTTPException(status_code=400, detail="Session is already completed")
        
        # Update session status to completed
        await db.database.sessions.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "status": "completed",
                    "endedAt": datetime.utcnow(),
                    "endedBy": user["id"]
                }
            }
        )
        
        # Get participant count
        participant_count = await db.database.session_participants.count_documents({
            "sessionId": session_id
        })
        
        # Update participant count in session
        await db.database.sessions.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {"participants": participant_count}}
        )
        
        # Generate and save MASTER report with ALL data to MongoDB
        # This stores complete session data separately in session_reports collection
        report = await SessionReportModel.generate_master_report(
            session_id=session_id,
            instructor_id=user["id"]
        )
        
        # Send email notifications to all participants
        emails_sent = 0
        participants = []
        async for p in db.database.session_participants.find({"sessionId": session_id}):
            participants.append(p)
            if p.get("studentEmail"):
                try:
                    success = email_service.send_session_report_email(
                        to_email=p.get("studentEmail"),
                        student_name=p.get("studentName", "Student"),
                        session_title=session.get("title", "Session"),
                        course_name=session.get("course", "Course"),
                        session_id=session_id,
                        is_instructor=False
                    )
                    if success:
                        emails_sent += 1
                except Exception as e:
                    print(f"Failed to send email to {p.get('studentEmail')}: {e}")
        
        # Send email to instructor
        instructor_email = user.get("email")
        if instructor_email:
            try:
                email_service.send_session_report_email(
                    to_email=instructor_email,
                    student_name=f"{user.get('firstName', '')} {user.get('lastName', '')}".strip(),
                    session_title=session.get("title", "Session"),
                    course_name=session.get("course", "Course"),
                    session_id=session_id,
                    is_instructor=True
                )
                emails_sent += 1
            except Exception as e:
                print(f"Failed to send email to instructor: {e}")
        
        return {
            "success": True,
            "message": "Session ended successfully",
            "sessionId": session_id,
            "status": "completed",
            "participantCount": participant_count,
            "reportGenerated": report is not None,
            "reportId": report.get("id") if report else None,
            "emailsSent": emails_sent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error ending session: {e}")
        raise HTTPException(status_code=500, detail="Failed to end session")


@router.post("/{session_id}/start")
async def start_session(
    session_id: str,
    user: dict = Depends(require_instructor)
):
    """Start a session (mark as live)"""
    try:
        session = await db.database.sessions.find_one({"_id": ObjectId(session_id)})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.get("instructorId") != user["id"]:
            raise HTTPException(status_code=403, detail="You can only start your own sessions")
        
        await db.database.sessions.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "status": "live",
                    "startedAt": datetime.utcnow()
                }
            }
        )
        
        return {"success": True, "message": "Session started", "status": "live"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error starting session: {e}")
        raise HTTPException(status_code=500, detail="Failed to start session")
