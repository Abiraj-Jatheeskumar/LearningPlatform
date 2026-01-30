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

        # 2) Get all participants in this session
        # Students might be connected using either zoomMeetingId or MongoDB sessionId
        # ALWAYS check both IDs to find all connected students
        
        # First, try to find the session document to get both IDs
        session_doc = None
        session_ids_to_check = [meeting_id]  # Start with the provided meeting_id
        effective_meeting_id = meeting_id
        
        try:
            # Try to find the session document to get both IDs
            # Try as integer first (Zoom IDs are usually integers)
            if meeting_id.isdigit():
                try:
                    session_doc = await db.database.sessions.find_one({"zoomMeetingId": int(meeting_id)})
                except:
                    pass
            
            # Try as string
            if not session_doc:
                session_doc = await db.database.sessions.find_one({"zoomMeetingId": meeting_id})
            
            # Try as MongoDB ObjectId
            if not session_doc:
                try:
                    if len(meeting_id) == 24:
                        session_doc = await db.database.sessions.find_one({"_id": ObjectId(meeting_id)})
                except:
                    pass
            
            # If we found the session document, get both IDs
            if session_doc:
                zoom_id = str(session_doc.get("zoomMeetingId", "")) if session_doc.get("zoomMeetingId") else None
                mongo_id = str(session_doc["_id"])
                
                # Add both IDs to check list (avoid duplicates)
                if zoom_id and zoom_id not in session_ids_to_check:
                    session_ids_to_check.append(zoom_id)
                if mongo_id and mongo_id not in session_ids_to_check:
                    session_ids_to_check.append(mongo_id)
                
                print(f"📍 Found session document: title='{session_doc.get('title', 'N/A')}'")
                print(f"   zoomMeetingId: {zoom_id}")
                print(f"   mongoSessionId: {mongo_id}")
                print(f"   Checking session IDs: {session_ids_to_check}")
        except Exception as lookup_error:
            print(f"⚠️ Error looking up session: {lookup_error}")
            import traceback
            traceback.print_exc()
        
        # Now check participants using ALL possible session IDs
        # This ensures we find students regardless of which ID they used to join
        participants = ws_manager.get_session_participants_by_multiple_ids(session_ids_to_check)
        
        if participants:
            # Use the session ID that has the most participants
            participant_counts = {}
            for p in participants:
                sid = p.get("sessionId", meeting_id)
                participant_counts[sid] = participant_counts.get(sid, 0) + 1
            
            if participant_counts:
                effective_meeting_id = max(participant_counts.items(), key=lambda x: x[1])[0]
                print(f"📍 Found {len(participants)} participants across multiple session IDs")
                print(f"   Using session ID: {effective_meeting_id} (has {participant_counts[effective_meeting_id]} participants)")
        else:
            print(f"⚠️ No participants found in any session room: {session_ids_to_check}")
            # Show all active session rooms for debugging
            all_stats = ws_manager.get_all_stats()
            all_rooms = list(all_stats.get('session_rooms', {}).keys())
            print(f"   All active session rooms: {all_rooms}")
        
        if not participants:
            return {"success": False, "message": "No students connected to this session. Make sure students have joined the meeting from the dashboard."}
        
        # Update meeting_id to the effective one for sending messages
        meeting_id = effective_meeting_id

        # Debug: Show session room stats before sending
        all_stats = ws_manager.get_all_stats()
        all_rooms = list(all_stats.get('session_rooms', {}).keys())
        print(f"\n{'='*60}")
        print(f"📊 QUIZ TRIGGER DEBUG INFO")
        print(f"{'='*60}")
        print(f"   Request meeting_id: {meeting_id}")
        print(f"   Effective meeting_id: {effective_meeting_id}")
        print(f"   Session IDs checked: {session_ids_to_check}")
        print(f"   All active session rooms: {all_rooms}")
        print(f"   Target session room: {meeting_id}")
        print(f"   Participants found: {len(participants)}")
        if participants:
            print(f"   Participant details:")
            for p in participants:
                print(f"      - {p.get('studentName', 'Unknown')} (ID: {p.get('studentId', 'N/A')}, Session: {p.get('sessionId', meeting_id)})")
        else:
            print(f"   ⚠️ No participants found!")
            print(f"   💡 Students must connect via WebSocket: /ws/session/<sessionId>/<studentId>")
        print(f"{'='*60}\n")
        
        # 3) Send DIFFERENT random question to EACH student
        # Filter out instructor connections - instructors have studentId starting with "instructor_" or have role="instructor"
        student_participants = []
        print(f"\n🔍 Filtering participants to find students:")
        for p in participants:
            student_id = p.get("studentId", "")
            student_name = p.get("studentName", "Unknown")
            print(f"   Checking: ID={student_id}, Name={student_name}")
            
            # Skip instructor connections (instructors connect with IDs like "instructor_xxx")
            if student_id.startswith("instructor_"):
                print(f"   ⏭️ Skipping instructor (starts with 'instructor_'): {student_id}")
                continue
            
            # Add student to list
            print(f"   ✅ Adding student: {student_name} ({student_id})")
            student_participants.append(p)
        
        print(f"\n📊 Filter results: {len(participants)} total → {len(student_participants)} students")
        
        if not student_participants:
            # Provide more helpful error message
            if participants:
                instructor_count = len(participants) - len(student_participants)
                return {
                    "success": False, 
                    "message": f"No students found in session (only {instructor_count} instructor(s) connected). Students must click 'Join' button on the session to receive quiz questions."
                }
            else:
                return {
                    "success": False, 
                    "message": f"No participants found in session. Students must click 'Join' button on the session before you trigger questions. Session IDs checked: {session_ids_to_check}"
                }
        
        ws_sent_count = 0
        sent_questions = []
        
        # Send individual random question to each student
        # Use the session_id that each student is actually connected with (from participant data)
        for participant in student_participants:
            student_id = participant.get("studentId")
            # Get the session_id this student is connected with (could be zoomMeetingId or MongoDB sessionId)
            student_session_id = participant.get("sessionId", meeting_id)
            
            # Pick a random question for this student
            q = random.choice(questions)
            
            # Prepare individual message for this student
            message = {
                "type": "quiz",
                "questionId": str(q["_id"]),
                "question": q["question"],
                "options": q["options"],
                "timeLimit": q.get("timeLimit", 30),
                "difficulty": q.get("difficulty", "medium"),
                "category": q.get("category", "General"),
                "sessionId": student_session_id,
                "studentId": student_id,  # Include student ID so they know it's for them
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to this student using their actual session_id
            sent = await ws_manager.send_to_student_in_session(student_session_id, student_id, message)
            
            # If failed, try with the effective meeting_id as fallback
            if not sent and student_session_id != meeting_id:
                sent = await ws_manager.send_to_student_in_session(meeting_id, student_id, message)
                if sent:
                    print(f"   ✅ Sent using fallback session_id: {meeting_id}")
            if sent:
                ws_sent_count += 1
                sent_questions.append({
                    "studentId": student_id,
                    "studentName": participant.get("studentName"),
                    "questionId": str(q["_id"]),
                    "question": q["question"]
                })
                print(f"   ✅ Sent question to {participant.get('studentName', student_id)}: {q['question'][:50]}...")

        print(f"✅ Questions sent to SESSION {meeting_id}: {ws_sent_count} students (each got a different random question)")
        print(f"   Participants: {[p.get('studentName', p.get('studentId', 'unknown')) for p in student_participants]}")

        # 🔄 STORE QUIZ IN SESSION for polling fallback
        # Store the first question as current_quiz (or pick one representative question)
        if sent_questions and session_doc:
            try:
                # Pick the first question sent (they're all random anyway)
                first_question = sent_questions[0]
                quiz_data = {
                    "questionId": first_question["questionId"],
                    "question": first_question["question"],
                    "options": questions[0]["options"],  # Get full options from original question
                    "timeLimit": questions[0].get("timeLimit", 30),
                    "difficulty": questions[0].get("difficulty", "medium"),
                    "category": questions[0].get("category", "General"),
                    "triggeredAt": datetime.now().isoformat(),
                    "type": "quiz"
                }
                
                # Update session document with current quiz
                await db.database.sessions.update_one(
                    {"_id": session_doc["_id"]},
                    {"$set": {"current_quiz": quiz_data}}
                )
                print(f"📝 Stored quiz in session document for polling fallback")
            except Exception as store_error:
                print(f"⚠️ Failed to store quiz for polling: {store_error}")

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
            "participants": student_participants,
            "sentQuestions": sent_questions,  # List of questions sent to each student
            "message": f"Quiz sent to {ws_sent_count} students in session {meeting_id} (each received a different random question)"
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
# 🔍 DIAGNOSTIC ENDPOINT - Check Session Connections
# ================================================================
@router.get("/debug/session/{session_id}")
async def debug_session_connections(session_id: str):
    """
    Diagnostic endpoint to check what students are connected to a session.
    Useful for debugging quiz trigger issues.
    """
    all_stats = ws_manager.get_all_stats()
    participants = ws_manager.get_session_participants(session_id)
    
    # Try to find session in database
    session_doc = None
    try:
        if session_id.isdigit():
            session_doc = await db.database.sessions.find_one({"zoomMeetingId": int(session_id)})
        if not session_doc:
            session_doc = await db.database.sessions.find_one({"zoomMeetingId": session_id})
        if not session_doc and len(session_id) == 24:
            session_doc = await db.database.sessions.find_one({"_id": ObjectId(session_id)})
    except:
        pass
    
    return {
        "success": True,
        "debug_info": {
            "requested_session_id": session_id,
            "session_exists_in_db": session_doc is not None,
            "session_title": session_doc.get("title") if session_doc else None,
            "zoom_meeting_id": session_doc.get("zoomMeetingId") if session_doc else None,
            "mongo_session_id": str(session_doc["_id"]) if session_doc else None,
            "all_active_session_rooms": list(all_stats.get("session_rooms", {}).keys()),
            "participants_in_this_session": len(participants),
            "participant_details": [
                {
                    "studentId": p.get("studentId"),
                    "studentName": p.get("studentName"),
                    "joinedAt": p.get("joinedAt"),
                    "status": p.get("status")
                }
                for p in participants
            ],
            "total_websocket_connections": all_stats.get("total_session_participants", 0),
            "help": "If participants_in_this_session is 0, students need to click 'Join Now' in the web browser"
        }
    }


# ================================================================
# ⭐ GLOBAL STATS (Optional)
# ================================================================
@router.get("/stats")
async def get_all_stats():
    stats = ws_manager.get_all_stats()
    return {"success": True, "stats": stats}


# ================================================================
# 🔄 POLLING ENDPOINT - Students check for new quizzes
# Backup delivery method when WebSocket registration fails
# ================================================================
@router.get("/poll-quiz/{session_id}")
async def poll_quiz(session_id: str, studentId: str):
    """
    Students poll this endpoint every 5 seconds to check for new quizzes.
    Returns the latest triggered quiz if one exists for this session.
    This is a BACKUP to WebSocket delivery - more reliable on poor networks.
    """
    try:
        # Check if there's a pending quiz for this session
        # We'll store triggered quizzes in a simple in-memory cache
        # (In production, you'd use Redis with TTL)
        
        # Get the latest triggered quiz from the session document
        session_doc = None
        try:
            if session_id.isdigit():
                session_doc = await db.database.sessions.find_one({"zoomMeetingId": int(session_id)})
            if not session_doc:
                session_doc = await db.database.sessions.find_one({"zoomMeetingId": session_id})
            if not session_doc and len(session_id) == 24:
                session_doc = await db.database.sessions.find_one({"_id": ObjectId(session_id)})
        except:
            pass
        
        if not session_doc:
            return {"hasNewQuiz": False, "message": "Session not found"}
        
        # Check if there's a current_quiz in the session (we'll add this field when triggering)
        current_quiz = session_doc.get("current_quiz")
        if not current_quiz:
            return {"hasNewQuiz": False}
        
        # Check if student has already answered this quiz
        quiz_id = current_quiz.get("questionId")
        already_answered = await db.database.quiz_responses.find_one({
            "studentId": studentId,
            "questionId": quiz_id,
            "sessionId": str(session_doc["_id"])
        })
        
        if already_answered:
            return {"hasNewQuiz": False, "message": "Already answered"}
        
        # Return the quiz
        return {
            "hasNewQuiz": True,
            "quiz": current_quiz
        }
        
    except Exception as e:
        print(f"❌ Polling error: {e}")
        return {"hasNewQuiz": False, "error": str(e)}
