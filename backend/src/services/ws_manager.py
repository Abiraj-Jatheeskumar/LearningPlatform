"""
WebSocket Connection Manager Service
Manages real-time WebSocket connections with SESSION-BASED ROOMS
Only students who join a session will receive quiz questions for that session
"""
from fastapi import WebSocket
from typing import Dict, Set, Optional, List
from datetime import datetime


class WebSocketManager:
    """
    Centralized WebSocket connection manager with SESSION ROOMS
    Supports:
      ✅ Session-based rooms (only joined students receive quizzes)
      ✅ Global WebSocket (all students - for announcements)
      ✅ Meeting-based connections (Zoom session)
    """

    def __init__(self):
        # Store meeting-based connections {meetingId: {studentId: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        self.connection_times: Dict[str, Dict[str, datetime]] = {}

        # ⭐ GLOBAL CONNECTIONS — all students
        self.global_connections: Set[WebSocket] = set()

        # 🎯 SESSION ROOMS - Only joined students receive quizzes
        # Structure: {sessionId: {studentId: {"websocket": ws, "status": "joined", "name": str, "email": str}}}
        self.session_rooms: Dict[str, Dict[str, dict]] = {}

    # =========================================================
    # 🎯 SESSION ROOM HANDLERS (NEW - For Quiz Delivery)
    # =========================================================

    async def join_session_room(
        self, 
        websocket: WebSocket, 
        session_id: str, 
        student_id: str,
        student_name: str = None,
        student_email: str = None
    ) -> dict:
        """
        Student joins a session room - REQUIRED to receive quiz questions
        Returns participant info
        """
        if session_id not in self.session_rooms:
            self.session_rooms[session_id] = {}

        participant = {
            "websocket": websocket,
            "studentId": student_id,
            "studentName": student_name or f"Student {student_id[:8]}",
            "studentEmail": student_email,
            "status": "joined",
            "joinedAt": datetime.now().isoformat()
        }

        self.session_rooms[session_id][student_id] = participant

        print(f"✅ Student joined session room: session={session_id}, student={student_id}")
        print(f"   Session room now has {len(self.session_rooms[session_id])} participants")

        return {
            "sessionId": session_id,
            "studentId": student_id,
            "studentName": participant["studentName"],
            "status": "joined",
            "participantCount": len(self.session_rooms[session_id])
        }

    def leave_session_room(self, session_id: str, student_id: str) -> bool:
        """Student leaves session room - will no longer receive quizzes"""
        if session_id in self.session_rooms and student_id in self.session_rooms[session_id]:
            # Mark as left instead of removing (for tracking)
            self.session_rooms[session_id][student_id]["status"] = "left"
            self.session_rooms[session_id][student_id]["leftAt"] = datetime.now().isoformat()
            
            print(f"👋 Student left session room: session={session_id}, student={student_id}")
            return True
        return False

    def remove_from_session_room(self, session_id: str, student_id: str) -> bool:
        """Completely remove student from session room"""
        if session_id in self.session_rooms and student_id in self.session_rooms[session_id]:
            del self.session_rooms[session_id][student_id]
            
            # Clean up empty rooms
            if len(self.session_rooms[session_id]) == 0:
                del self.session_rooms[session_id]
                print(f"🧹 Cleaned empty session room: {session_id}")
            
            return True
        return False

    def is_in_session_room(self, session_id: str, student_id: str) -> bool:
        """Check if student is an active participant in session room"""
        if session_id not in self.session_rooms:
            return False
        if student_id not in self.session_rooms[session_id]:
            return False
        return self.session_rooms[session_id][student_id].get("status") == "joined"

    def get_session_participants(self, session_id: str) -> List[dict]:
        """Get all ACTIVE participants in a session room"""
        if session_id not in self.session_rooms:
            return []
        
        participants = []
        for student_id, data in self.session_rooms[session_id].items():
            if data.get("status") == "joined":
                participants.append({
                    "studentId": student_id,
                    "studentName": data.get("studentName"),
                    "studentEmail": data.get("studentEmail"),
                    "joinedAt": data.get("joinedAt"),
                    "status": data.get("status")
                })
        return participants

    def get_session_participant_count(self, session_id: str) -> int:
        """Get count of active participants in session"""
        return len(self.get_session_participants(session_id))

    async def broadcast_to_session(self, session_id: str, message: dict) -> int:
        """
        🎯 BROADCAST QUIZ TO SESSION ROOM ONLY
        Only students who have joined this session will receive the message
        """
        if session_id not in self.session_rooms:
            print(f"⚠️ No participants in session {session_id}")
            return 0

        sent = 0
        dead_connections = []

        for student_id, data in self.session_rooms[session_id].items():
            # Only send to JOINED students (not "left")
            if data.get("status") != "joined":
                continue

            websocket = data.get("websocket")
            if not websocket:
                continue

            try:
                await websocket.send_json(message)
                sent += 1
                print(f"   ✅ Sent to {data.get('studentName', student_id)}")
            except Exception as e:
                print(f"   ❌ Failed to send to {student_id}: {e}")
                dead_connections.append(student_id)

        # Clean up dead connections
        for student_id in dead_connections:
            self.leave_session_room(session_id, student_id)

        print(f"📢 SESSION BROADCAST [{session_id}] → Sent to {sent} students")
        return sent

    # =========================================================
    # ⭐ GLOBAL CONNECTION HANDLERS
    # =========================================================

    async def connect_global(self, websocket: WebSocket):
        """Accept and store a global WebSocket connection"""
        await websocket.accept()
        self.global_connections.add(websocket)
        print(f"🌍 Global WS Connected (total={len(self.global_connections)})")

    def disconnect_global(self, websocket: WebSocket):
        """Remove global WebSocket connection"""
        if websocket in self.global_connections:
            self.global_connections.remove(websocket)
            print(f"❌ Global WS Disconnected (remaining={len(self.global_connections)})")

    async def broadcast_global(self, message: dict) -> int:
        """Broadcast message to ALL connected students globally"""
        dead = []
        sent = 0

        for ws in list(self.global_connections):
            try:
                await ws.send_json(message)
                sent += 1
            except:
                dead.append(ws)

        # Remove dead sockets
        for ws in dead:
            self.global_connections.remove(ws)

        print(f"📢 GLOBAL BROADCAST → Sent to {sent} students")
        return sent

    # =========================================================
    # 🎯 MEETING BASED HANDLERS (kept for compatibility)
    # =========================================================

    async def connect(self, websocket: WebSocket, meeting_id: str, student_id: str):
        """Accept meeting-based WebSocket connection"""
        await websocket.accept()

        if meeting_id not in self.active_connections:
            self.active_connections[meeting_id] = {}
            self.connection_times[meeting_id] = {}

        self.active_connections[meeting_id][student_id] = websocket
        self.connection_times[meeting_id][student_id] = datetime.now()

        print(f"✅ WS Connected: Meeting={meeting_id}, Student={student_id}")

        # Auto-send welcome message
        await websocket.send_json({
            "type": "connected",
            "meeting_id": meeting_id,
            "student_id": student_id,
            "timestamp": datetime.now().isoformat()
        })

    def disconnect(self, meeting_id: str, student_id: str):
        """Disconnect meeting-based WebSocket connection"""
        if meeting_id in self.active_connections and student_id in self.active_connections[meeting_id]:
            del self.active_connections[meeting_id][student_id]

            if student_id in self.connection_times.get(meeting_id, {}):
                del self.connection_times[meeting_id][student_id]

            print(f"❌ WS Disconnected: Meeting={meeting_id}, Student={student_id}")

            # Remove empty meeting room
            if len(self.active_connections[meeting_id]) == 0:
                del self.active_connections[meeting_id]
                if meeting_id in self.connection_times:
                    del self.connection_times[meeting_id]
                print(f"🧹 Cleaned empty meeting {meeting_id}")

    async def broadcast_to_meeting(self, meeting_id: str, message: dict) -> int:
        """Send message to all students in ONE meeting"""
        if meeting_id not in self.active_connections:
            return 0

        sent = 0
        dead = []

        for student_id, ws in self.active_connections[meeting_id].items():
            try:
                await ws.send_json(message)
                sent += 1
            except:
                dead.append(student_id)

        for sid in dead:
            self.disconnect(meeting_id, sid)

        return sent

    async def broadcast_to_all_meetings(self, message: dict) -> int:
        """Send to all students across all meetings"""
        total = 0
        for m in list(self.active_connections.keys()):
            total += await self.broadcast_to_meeting(m, message)
        return total

    # =========================================================
    # 🔍 STATS
    # =========================================================

    def get_all_stats(self):
        session_stats = {}
        for session_id in self.session_rooms:
            session_stats[session_id] = self.get_session_participant_count(session_id)

        return {
            "global_connections": len(self.global_connections),
            "meeting_rooms": list(self.active_connections.keys()),
            "session_rooms": session_stats,
            "total_session_participants": sum(session_stats.values()),
            "timestamp": datetime.now().isoformat()
        }


# Export instance
ws_manager = WebSocketManager()
__all__ = ["ws_manager", "WebSocketManager"]
