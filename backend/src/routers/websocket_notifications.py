"""
WebSocket Notifications Router
Real-time notifications for students when instructors trigger questions
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
from datetime import datetime

router = APIRouter()

# Store active connections: {meeting_id: {websocket1, websocket2, ...}}
active_connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Manages WebSocket connections for real-time notifications"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, meeting_id: str, student_id: str):
        """Connect a student to a meeting's notification channel"""
        await websocket.accept()
        
        if meeting_id not in self.active_connections:
            self.active_connections[meeting_id] = set()
        
        self.active_connections[meeting_id].add(websocket)
        print(f"✅ Student {student_id} connected to meeting {meeting_id}")
        print(f"📊 Total connections for meeting {meeting_id}: {len(self.active_connections[meeting_id])}")
    
    def disconnect(self, websocket: WebSocket, meeting_id: str, student_id: str):
        """Disconnect a student from a meeting's notification channel"""
        if meeting_id in self.active_connections:
            self.active_connections[meeting_id].discard(websocket)
            
            # Clean up empty meeting rooms
            if len(self.active_connections[meeting_id]) == 0:
                del self.active_connections[meeting_id]
            
            print(f"❌ Student {student_id} disconnected from meeting {meeting_id}")
    
    async def broadcast_to_meeting(self, meeting_id: str, message: dict):
        """Broadcast a notification to all students in a meeting"""
        if meeting_id not in self.active_connections:
            print(f"⚠️  No active connections for meeting {meeting_id}")
            return 0
        
        connections = list(self.active_connections[meeting_id])  # Copy to avoid modification during iteration
        sent_count = 0
        
        for connection in connections:
            try:
                await connection.send_json(message)
                sent_count += 1
            except Exception as e:
                print(f"❌ Error sending to connection: {e}")
                # Remove dead connection
                self.active_connections[meeting_id].discard(connection)
        
        print(f"📤 Broadcast to {sent_count} students in meeting {meeting_id}")
        return sent_count


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/notifications/{meeting_id}/{student_id}")
async def websocket_endpoint(websocket: WebSocket, meeting_id: str, student_id: str):
    """
    WebSocket endpoint for student notifications
    Students connect to this to receive real-time question notifications
    """
    await manager.connect(websocket, meeting_id, student_id)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to notification system",
            "meeting_id": meeting_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive and listen for messages
        while True:
            # Receive any messages from client (heartbeat, etc.)
            data = await websocket.receive_text()
            
            # Handle heartbeat
            if data == "ping":
                await websocket.send_text("pong")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, meeting_id, student_id)
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket, meeting_id, student_id)


async def notify_question_triggered(
    meeting_id: str,
    question_data: dict,
    session_token: str,
    question_url: str,
    instructor_name: str,
    time_limit: int
):
    """
    Send notification to all students in a meeting when a question is triggered
    This function is called from the trigger_question endpoint
    """
    notification = {
        "type": "question_triggered",
        "data": {
            "sessionToken": session_token,
            "question": question_data.get("question"),
            "options": question_data.get("options"),
            "timeLimit": time_limit,
            "questionUrl": question_url,
            "instructorName": instructor_name,
            "triggeredAt": datetime.now().isoformat()
        },
        "timestamp": datetime.now().isoformat()
    }
    
    sent_count = await manager.broadcast_to_meeting(meeting_id, notification)
    return sent_count


# Export for use in other routers
__all__ = ['router', 'notify_question_triggered', 'manager']

