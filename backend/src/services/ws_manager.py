"""
WebSocket Connection Manager Service
Manages real-time WebSocket connections for students in Zoom meetings
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set, Optional
from datetime import datetime
import json


class WebSocketManager:
    """
    Centralized WebSocket connection manager
    Handles student connections per Zoom meeting
    """
    
    def __init__(self):
        # Store connections: {meeting_id: {student_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # Track connection timestamps
        self.connection_times: Dict[str, Dict[str, datetime]] = {}
    
    async def connect(self, websocket: WebSocket, meeting_id: str, student_id: str):
        """
        Accept and store a new WebSocket connection
        
        Args:
            websocket: The WebSocket connection
            meeting_id: Zoom meeting ID
            student_id: Unique student identifier
        """
        await websocket.accept()
        
        # Initialize meeting room if not exists
        if meeting_id not in self.active_connections:
            self.active_connections[meeting_id] = {}
            self.connection_times[meeting_id] = {}
        
        # Store connection
        self.active_connections[meeting_id][student_id] = websocket
        self.connection_times[meeting_id][student_id] = datetime.now()
        
        print(f"✅ WebSocket Connected: Meeting={meeting_id}, Student={student_id}")
        print(f"📊 Total connections in meeting {meeting_id}: {len(self.active_connections[meeting_id])}")
        
        # Send welcome message
        await self.send_personal_message(
            websocket,
            {
                "type": "connected",
                "message": "Successfully connected to notification system",
                "meeting_id": meeting_id,
                "student_id": student_id,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def disconnect(self, meeting_id: str, student_id: str):
        """
        Remove a WebSocket connection
        
        Args:
            meeting_id: Zoom meeting ID
            student_id: Unique student identifier
        """
        if meeting_id in self.active_connections:
            if student_id in self.active_connections[meeting_id]:
                del self.active_connections[meeting_id][student_id]
                
                # Clean up connection time
                if meeting_id in self.connection_times and student_id in self.connection_times[meeting_id]:
                    del self.connection_times[meeting_id][student_id]
                
                print(f"❌ WebSocket Disconnected: Meeting={meeting_id}, Student={student_id}")
                print(f"📊 Remaining connections in meeting {meeting_id}: {len(self.active_connections[meeting_id])}")
            
            # Clean up empty meeting rooms
            if len(self.active_connections[meeting_id]) == 0:
                del self.active_connections[meeting_id]
                if meeting_id in self.connection_times:
                    del self.connection_times[meeting_id]
                print(f"🧹 Meeting room {meeting_id} cleaned up (no active connections)")
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """
        Send a message to a specific WebSocket connection
        
        Args:
            websocket: The WebSocket connection
            message: Message dictionary to send
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"❌ Error sending personal message: {e}")
    
    async def broadcast_to_meeting(self, meeting_id: str, message: dict) -> int:
        """
        Broadcast a message to all students in a specific meeting
        
        Args:
            meeting_id: Zoom meeting ID
            message: Message dictionary to broadcast
            
        Returns:
            int: Number of students who received the message
        """
        if meeting_id not in self.active_connections:
            print(f"⚠️  No active connections for meeting {meeting_id}")
            return 0
        
        # Get all connections for this meeting
        connections = list(self.active_connections[meeting_id].items())
        sent_count = 0
        failed_students = []
        
        # Broadcast to all connected students
        for student_id, websocket in connections:
            try:
                await websocket.send_json(message)
                sent_count += 1
                print(f"📤 Sent to {student_id} in meeting {meeting_id}")
            except Exception as e:
                print(f"❌ Failed to send to {student_id}: {e}")
                failed_students.append(student_id)
        
        # Clean up failed connections
        for student_id in failed_students:
            self.disconnect(meeting_id, student_id)
        
        print(f"✅ Broadcast complete: {sent_count} students reached in meeting {meeting_id}")
        return sent_count
    
    async def broadcast_to_all(self, message: dict) -> int:
        """
        Broadcast a message to all connected students in all meetings
        
        Args:
            message: Message dictionary to broadcast
            
        Returns:
            int: Total number of students who received the message
        """
        total_sent = 0
        
        for meeting_id in list(self.active_connections.keys()):
            sent = await self.broadcast_to_meeting(meeting_id, message)
            total_sent += sent
        
        return total_sent
    
    def get_connected_students(self, meeting_id: str) -> list:
        """
        Get list of connected student IDs for a meeting
        
        Args:
            meeting_id: Zoom meeting ID
            
        Returns:
            list: List of student IDs
        """
        if meeting_id not in self.active_connections:
            return []
        
        return list(self.active_connections[meeting_id].keys())
    
    def get_connection_count(self, meeting_id: Optional[str] = None) -> int:
        """
        Get the number of active connections
        
        Args:
            meeting_id: Optional meeting ID to filter by
            
        Returns:
            int: Number of active connections
        """
        if meeting_id:
            return len(self.active_connections.get(meeting_id, {}))
        
        # Total across all meetings
        return sum(len(students) for students in self.active_connections.values())
    
    def get_all_meetings(self) -> list:
        """
        Get list of all meetings with active connections
        
        Returns:
            list: List of meeting IDs
        """
        return list(self.active_connections.keys())
    
    def get_meeting_stats(self, meeting_id: str) -> dict:
        """
        Get statistics for a specific meeting
        
        Args:
            meeting_id: Zoom meeting ID
            
        Returns:
            dict: Meeting statistics
        """
        if meeting_id not in self.active_connections:
            return {
                "meeting_id": meeting_id,
                "connected_students": 0,
                "student_ids": [],
                "connection_times": {}
            }
        
        connection_times = {}
        if meeting_id in self.connection_times:
            connection_times = {
                student_id: timestamp.isoformat()
                for student_id, timestamp in self.connection_times[meeting_id].items()
            }
        
        return {
            "meeting_id": meeting_id,
            "connected_students": len(self.active_connections[meeting_id]),
            "student_ids": list(self.active_connections[meeting_id].keys()),
            "connection_times": connection_times
        }
    
    def get_all_stats(self) -> dict:
        """
        Get statistics for all meetings
        
        Returns:
            dict: Overall statistics
        """
        meetings = []
        total_connections = 0
        
        for meeting_id in self.active_connections.keys():
            stats = self.get_meeting_stats(meeting_id)
            meetings.append(stats)
            total_connections += stats["connected_students"]
        
        return {
            "total_meetings": len(meetings),
            "total_connections": total_connections,
            "meetings": meetings,
            "timestamp": datetime.now().isoformat()
        }


# Global WebSocket manager instance
ws_manager = WebSocketManager()


# Export for use in routers
__all__ = ['WebSocketManager', 'ws_manager']

