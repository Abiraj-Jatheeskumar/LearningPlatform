from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from ..database.connection import get_database


class SessionParticipantModel:
    """Track students who have joined a session - only these students will receive quiz questions"""

    @staticmethod
    async def join_session(session_id: str, student_id: str, student_name: str = None, student_email: str = None) -> Optional[dict]:
        """Record a student joining the session"""
        database = get_database()
        if database is None:
            raise Exception("Database not connected")

        participant = {
            "sessionId": session_id,
            "studentId": student_id,
            "studentName": student_name,
            "studentEmail": student_email,
            "joinedAt": datetime.utcnow(),
            "status": "active",
            "leftAt": None
        }

        result = await database.session_participants.update_one(
            {"sessionId": session_id, "studentId": student_id},
            {"$set": participant},
            upsert=True
        )

        if result.upserted_id:
            participant["id"] = str(result.upserted_id)
        else:
            existing = await database.session_participants.find_one(
                {"sessionId": session_id, "studentId": student_id}
            )
            if existing:
                participant["id"] = str(existing["_id"])

        return participant

    @staticmethod
    async def leave_session(session_id: str, student_id: str) -> bool:
        """Record a student leaving the session"""
        database = get_database()
        if database is None:
            return False

        result = await database.session_participants.update_one(
            {"sessionId": session_id, "studentId": student_id},
            {"$set": {"status": "left", "leftAt": datetime.utcnow()}}
        )
        return result.modified_count > 0

    @staticmethod
    async def is_participant(session_id: str, student_id: str) -> bool:
        """Check if a student is an active participant in the session"""
        database = get_database()
        if database is None:
            return False

        participant = await database.session_participants.find_one({
            "sessionId": session_id,
            "studentId": student_id,
            "status": "active"
        })
        return participant is not None

    @staticmethod
    async def get_active_participants(session_id: str) -> List[dict]:
        """Get all active participants in a session"""
        database = get_database()
        if database is None:
            return []

        participants = []
        async for participant in database.session_participants.find({
            "sessionId": session_id,
            "status": "active"
        }):
            participant["id"] = str(participant["_id"])
            del participant["_id"]
            participants.append(participant)
        return participants

    @staticmethod
    async def get_participant_count(session_id: str) -> int:
        """Get count of active participants"""
        database = get_database()
        if database is None:
            return 0

        count = await database.session_participants.count_documents({
            "sessionId": session_id,
            "status": "active"
        })
        return count

    @staticmethod
    async def get_participant_ids(session_id: str) -> List[str]:
        """Get list of active participant student IDs"""
        database = get_database()
        if database is None:
            return []

        participant_ids = []
        async for participant in database.session_participants.find(
            {"sessionId": session_id, "status": "active"},
            {"studentId": 1}
        ):
            participant_ids.append(participant["studentId"])
        return participant_ids

    @staticmethod
    async def reset_session(session_id: str) -> int:
        """Remove all participants from a session"""
        database = get_database()
        if database is None:
            return 0

        result = await database.session_participants.delete_many({
            "sessionId": session_id
        })
        return result.deleted_count

