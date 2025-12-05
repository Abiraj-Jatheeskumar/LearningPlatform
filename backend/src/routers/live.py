"""
Live Learning Router
Trigger questions → Sent ONLY to students who JOINED the session via WebSocket
🎯 Session-based delivery: Only students connected to /ws/session/<meetingId>/<studentId> receive quizzes
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
# 🎯 TRIGGER QUESTION (Only students who JOINED session receive quiz)
# ================================================================
@router.post("/trigger/{meeting_id}")
async def trigger_question(meeting_id: str):
    """
    Instructor triggers a question.
    A random question is selected from MongoDB and sent ONLY to students
    who have joined this specific session via WebSocket.
    
    🎯 Students must be connected to /ws/session/<meeting_id>/<student_id>
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

        # Debug: Show session room stats before sending
        all_stats = ws_manager.get_all_stats()
        print(f"📊 WebSocket Stats BEFORE broadcast:")
        print(f"   Session rooms: {all_stats.get('session_rooms', {})}")
        print(f"   Target session: {meeting_id}")
        
        # 🎯 4) Send ONLY to students in this session room (not global broadcast!)
        # Only students who clicked "Join" and connected to /ws/session/<meetingId>/<studentId> will receive
        ws_sent_count = await ws_manager.broadcast_to_session(meeting_id, message)
        
        # Get participant list for response
        participants = ws_manager.get_session_participants(meeting_id)

        print(f"✅ Question sent to SESSION {meeting_id}: {ws_sent_count} students")
        print(f"   Participants: {[p.get('studentId', 'unknown') for p in participants]}")
        print(f"   Message sent: {message}")

        # 5) Optionally send Web Push Notifications to subscribed students in this session
        # (For now, push is still global - can be made session-specific later)
        push_sent_count = 0
        try:
            push_sent_count = await push_service.send_quiz_notification(message)
            print(f"✅ Push notifications sent to {push_sent_count} students")
        except Exception as push_error:
            print(f"⚠️ Push notification error (non-fatal): {push_error}")

        return {
            "success": True,
            "sessionId": meeting_id,
            "websocketSent": ws_sent_count,
            "pushSent": push_sent_count,
            "totalReached": ws_sent_count + push_sent_count,
            "participants": participants,
            "sentQuestion": message,
            "message": f"Quiz sent to {ws_sent_count} students in session {meeting_id}"
        }

    except Exception as e:
        print(f"❌ Error triggering question: {e}")
        import traceback
        traceback.print_exc()
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
