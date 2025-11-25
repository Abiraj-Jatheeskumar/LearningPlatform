"""
Live Learning Router
Simplified trigger for sending questions to students via WebSocket
"""
from fastapi import APIRouter
from bson import ObjectId
from src.services.ws_manager import ws_manager
from src.database.connection import db  # IMPORTANT: You must import your DB instance
import random
from datetime import datetime

router = APIRouter(prefix="/api/live", tags=["Live Learning"])


@router.post("/trigger/{meeting_id}")
async def trigger_question(meeting_id: str):
    """
    Trigger a random question to all students in a meeting
    
    Args:
        meeting_id: Zoom meeting ID
        
    Returns:
        Success status, number of students notified, and question details
    """
    try:
        # Fetch all questions from DB
        questions = await db.database.questions.find({}).to_list(length=None)
        
        if not questions:
            return {"success": False, "message": "No questions found in DB"}
        
        # Randomly select 1 question
        q = random.choice(questions)
        
        # Prepare message for students
        message = {
            "type": "quiz",
            "questionId": str(q["_id"]),
            "question": q["question"],
            "options": q["options"],
            "timeLimit": q.get("timeLimit", 30),
            "difficulty": q.get("difficulty", "medium"),
            "category": q.get("category", "General"),
            "timestamp": datetime.now().isoformat()
        }
        
        # Broadcast to all connected students in meeting
        #sent_count = await ws_manager.broadcast_to_meeting(meeting_id, message)
        sent_count = await ws_manager.broadcast_global(message)

        
        print(f"✅ Triggered question to {sent_count} students in meeting {meeting_id}")
        
        return {
            "success": True,
            "sent": sent_count,
            "sentQuestion": message
        }
    
    except Exception as e:
        print(f"❌ Error triggering question: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


@router.get("/stats/{meeting_id}")
async def get_meeting_stats(meeting_id: str):
    """
    Get WebSocket connection statistics for a meeting
    
    Args:
        meeting_id: Zoom meeting ID
        
    Returns:
        Connection statistics
    """
    stats = ws_manager.get_meeting_stats(meeting_id)
    return {
        "success": True,
        "stats": stats
    }


@router.get("/stats")
async def get_all_stats():
    """
    Get WebSocket connection statistics for all meetings
    
    Returns:
        Overall connection statistics
    """
    stats = ws_manager.get_all_stats()
    return {
        "success": True,
        "stats": stats
    }

