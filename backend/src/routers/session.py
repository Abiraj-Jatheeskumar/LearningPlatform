# src/routers/live.py
from typing import List, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId

from src.database.connection import db
from src.middleware.auth import get_current_user, require_instructor
from src.services.zoom_service import create_zoom_meeting

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


class SessionCreateRequest(BaseModel):
    title: str
    courseName: str
    courseCode: str
    description: str | None = None
    date: str          # "2025-11-30"
    startTime: str     # "10:00"
    endTime: str       # "11:30"
    durationMinutes: int


def session_to_dict(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc["_id"]),
        "title": doc["title"],
        "courseName": doc["courseName"],
        "courseCode": doc["courseCode"],
        "description": doc.get("description"),
        "date": doc["date"],
        "startTime": doc["startTime"],
        "endTime": doc["endTime"],
        "durationMinutes": doc["durationMinutes"],
        "status": doc.get("status", "upcoming"),
        "instructorId": doc["instructorId"],
        "instructorName": doc.get("instructorName"),
        "zoom": {
            "meetingId": doc["zoom"]["meetingId"],
            "joinUrl": doc["zoom"]["joinUrl"],
            "startUrl": doc["zoom"]["startUrl"],
            "password": doc["zoom"].get("password"),
        },
    }


@router.post("", status_code=201)
async def create_session(
    payload: SessionCreateRequest,
    user: dict = Depends(require_instructor),
):
    """
    Instructor creates a session + Zoom meeting.
    """
    try:
        # combine date + time to ISO string (Zoom needs this)
        start_dt_str = f"{payload.date}T{payload.startTime}:00"
        # simple: assume local timezone; Zoom timezone handled in service

        zoom_meeting = await create_zoom_meeting(
            topic=payload.title,
            start_time=start_dt_str,
            duration_minutes=payload.durationMinutes,
        )

        doc = {
            "title": payload.title,
            "courseName": payload.courseName,
            "courseCode": payload.courseCode,
            "description": payload.description,
            "date": payload.date,
            "startTime": payload.startTime,
            "endTime": payload.endTime,
            "durationMinutes": payload.durationMinutes,
            "status": "upcoming",
            "instructorId": user["id"],
            "instructorName": f"{user.get('firstName', '')} {user.get('lastName', '')}".strip(),
            "createdAt": datetime.utcnow(),
            "zoom": {
                "meetingId": zoom_meeting["id"],
                "joinUrl": zoom_meeting["join_url"],
                "startUrl": zoom_meeting["start_url"],
                "password": zoom_meeting.get("password"),
            },
        }

        result = await db.database.sessions.insert_one(doc)
        doc["_id"] = result.inserted_id

        return {"success": True, "session": session_to_dict(doc)}

    except Exception as e:
        print("Create session error:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session",
        )


@router.get("")
async def list_sessions(user: dict = Depends(get_current_user)):
    """
    List all sessions (simple version).
    Later you can filter by instructorId / enrolled courses.
    """
    cursor = db.database.sessions.find({}).sort("date", 1)
    items = [session_to_dict(doc) async for doc in cursor]
    return {"success": True, "sessions": items}
