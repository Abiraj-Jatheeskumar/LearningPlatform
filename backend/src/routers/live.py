"""
Live Learning Router
Trigger questions → Sent to ALL students via GLOBAL WebSocket + Push Notifications
"""
from fastapi import APIRouter
from bson import ObjectId
from src.services.ws_manager import ws_manager
from src.services.push_service import push_service
from src.database.connection import db
import random
from datetime import datetime

router = APIRouter(prefix="/api/live", tags=["Live Learning"])


# ================================================================
# ⭐ TRIGGER QUESTION (Instructor clicks → ALL students get quiz)
# ================================================================
@router.post("/trigger/{meeting_id}")
async def trigger_question(meeting_id: str):
    """
    Instructor triggers a question.
    A random question is selected from MongoDB and sent to ALL students.
    """

    try:
        # 1) Fetch all questions from MongoDB
        questions = await db.database.questions.find({}).to_list(length=None)

        if not questions:
            return {"success": False, "message": "No questions found in DB"}

        # 2) Pick one question randomly
        q = random.choice(questions)

        # 3) Prepare WebSocket broadcast message
        message = {
            "type": "quiz",
            "questionId": str(q["_id"]),
            "question": q["question"],
            "options": q["options"],
            "timeLimit": q.get("timeLimit", 30),
            "difficulty": q.get("difficulty", "medium"),
            "category": q.get("category", "General"),
            "sessionId": meeting_id,
            "timestamp": datetime.now().isoformat()
        }

        # 4) Send to ALL connected students (GLOBAL WS)
        ws_sent_count = await ws_manager.broadcast_global(message)

        print(f"✅ Question broadcast via WebSocket to {ws_sent_count} students")

        # 5) Send Web Push Notifications to all subscribed students
        push_sent_count = await push_service.send_quiz_notification(message)
        
        print(f"✅ Push notifications sent to {push_sent_count} students")

        return {
            "success": True,
            "websocketSent": ws_sent_count,
            "pushSent": push_sent_count,
            "totalReached": ws_sent_count + push_sent_count,
            "sentQuestion": message
        }

    except Exception as e:
        print(f"❌ Error triggering question: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


# ================================================================
# ⭐ MEETING STATS (Optional – still works)
# ================================================================
@router.get("/stats/{meeting_id}")
async def get_meeting_stats(meeting_id: str):
    stats = ws_manager.get_meeting_stats(meeting_id)
    return {"success": True, "stats": stats}


# ================================================================
# ⭐ GLOBAL STATS (Optional)
# ================================================================
@router.get("/stats")
async def get_all_stats():
    stats = ws_manager.get_all_stats()
    return {"success": True, "stats": stats}
