"""
WebSocket Connection Manager Service
Manages real-time WebSocket connections for ALL students + meeting-based groups
"""
from fastapi import WebSocket
from typing import Dict, Set, Optional
from datetime import datetime


class WebSocketManager:
    """
    Centralized WebSocket connection manager
    Supports:
      ✅ Global WebSocket (all students)
      ✅ Meeting-based connections (Zoom session)
    """

    def __init__(self):
        # Store meeting-based connections {meetingId: {studentId: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        self.connection_times: Dict[str, Dict[str, datetime]] = {}

        # ⭐ GLOBAL CONNECTIONS — all students
        self.global_connections: Set[WebSocket] = set()

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
    # 🎯 MEETING BASED HANDLERS (kept for future use)
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
        return {
            "global_connections": len(self.global_connections),
            "meeting_rooms": list(self.active_connections.keys()),
            "timestamp": datetime.now().isoformat()
        }


# Export instance
ws_manager = WebSocketManager()
__all__ = ["ws_manager", "WebSocketManager"]
