# src/routers/session.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from src.database.connection import db
from src.middleware.auth import get_current_user, require_instructor
from src.services.zoom_service import create_zoom_meeting, ZoomServiceError

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


class SessionCreate(BaseModel):
    title: str
    course: str
    courseCode: str
    date: str          # "2025-11-25"
    time: str          # "10:00 AM - 11:00 AM" or "10:00"
    durationMinutes: int
    timezone: str = "Asia/Colombo"


class SessionOut(BaseModel):
    id: str
    title: str
    course: str
    courseCode: str
    instructor: str
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


def _session_doc_to_out(doc) -> SessionOut:
    return SessionOut(
        id=str(doc["_id"]),
        title=doc["title"],
        course=doc["course"],
        courseCode=doc["courseCode"],
        instructor=doc["instructor"],
        date=doc["date"],
        time=doc["time"],
        duration=doc["duration"],
        status=doc.get("status", "upcoming"),
        participants=doc.get("participants", 0),
        expectedParticipants=doc.get("expectedParticipants", 0),
        engagement=doc.get("engagement", 0),
        recordingAvailable=doc.get("recordingAvailable", False),
        zoomMeetingId=str(doc.get("zoomMeetingId")) if doc.get("zoomMeetingId") else None,
        join_url=doc.get("join_url"),
        start_url=doc.get("start_url"),
    )


@router.post("", response_model=SessionOut)
async def create_session(
    payload: SessionCreate,
    user: dict = Depends(require_instructor),
):
    """
    Create session + Zoom meeting.
    """
    try:
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
            "instructor": f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
                          or user.get("email", "Unknown Instructor"),
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
    except Exception as e:
        print("Error creating session:", e)
        raise HTTPException(status_code=500, detail="Failed to create session")


@router.get("", response_model=List[SessionOut])
async def list_sessions(user: dict = Depends(get_current_user)):
    cursor = db.database.sessions.find().sort("date", -1)
    sessions = await cursor.to_list(length=None)
    return [_session_doc_to_out(doc) for doc in sessions]


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(session_id: str, user: dict = Depends(get_current_user)):
    try:
        doc = await db.database.sessions.find_one({"_id": ObjectId(session_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Session not found")
        return _session_doc_to_out(doc)
    except Exception:
        raise HTTPException(status_code=404, detail="Session not found")
