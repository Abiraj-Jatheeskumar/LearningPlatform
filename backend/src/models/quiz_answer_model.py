from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import asyncio
from ..database.connection import get_database
from .quiz_answer import QuizAnswer


class QuizAnswerModel:
    @staticmethod
    async def create(answer: QuizAnswer) -> dict:
        """Store a quiz answer"""
        database = get_database()
        if database is None:
            raise Exception("Database not connected")
        
        answer_data = answer.model_dump()
        answer_data["timestamp"] = datetime.now()
        
        result = await database.quiz_answers.insert_one(answer_data)
        answer_data["id"] = str(result.inserted_id)
        
        # ============================================================
        # MYSQL BACKUP: Auto-backup new quiz answer (non-blocking)
        # ============================================================
        try:
            from ..services.mysql_backup_service import mysql_backup_service
            asyncio.create_task(mysql_backup_service.backup_quiz_answer(answer_data))
            print(f"📦 MySQL backup triggered for quiz_answer: {answer_data['id']}")
        except Exception as e:
            print(f"⚠️ MySQL quiz_answer backup failed (non-fatal): {e}")
        
        return answer_data

    @staticmethod
    async def find_by_question(question_id: str) -> List[dict]:
        """Find all answers for a question"""
        database = get_database()
        if database is None:
            return []
        
        answers = []
        async for answer in database.quiz_answers.find({"questionId": question_id}):
            answer["id"] = str(answer["_id"])
            del answer["_id"]
            answers.append(answer)
        return answers

    @staticmethod
    async def find_by_question_and_session(question_id: str, session_id: str) -> List[dict]:
        """Find answers for a question in a specific session"""
        database = get_database()
        if database is None:
            return []
        
        answers = []
        async for answer in database.quiz_answers.find({
            "questionId": question_id,
            "sessionId": session_id
        }):
            answer["id"] = str(answer["_id"])
            del answer["_id"]
            answers.append(answer)
        return answers

    @staticmethod
    async def delete_by_question_and_session(question_id: str, session_id: str) -> int:
        """Delete answers for a question in a session"""
        database = get_database()
        if database is None:
            return 0
        
        result = await database.quiz_answers.delete_many({
            "questionId": question_id,
            "sessionId": session_id
        })
        return result.deleted_count

    @staticmethod
    async def delete_by_session(session_id: str) -> int:
        """Delete all answers for a specific session"""
        database = get_database()
        if database is None:
            return 0

        result = await database.quiz_answers.delete_many({
            "sessionId": session_id
        })
        return result.deleted_count

