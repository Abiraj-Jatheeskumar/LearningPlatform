from typing import Dict, Optional, Any, List
from bson import ObjectId
import asyncio
from ..database.connection import get_database


class Question:
    @staticmethod
    async def find_by_id(id: str) -> Optional[Dict[str, Any]]:
        """Find question by ID"""
        database = get_database()
        if database is None:
            return None
        try:
            question = await database.questions.find_one({"_id": ObjectId(id)})
            if question:
                question["id"] = str(question["_id"])
                del question["_id"]
            return question
        except:
            # Try finding by string id if ObjectId fails
            question = await database.questions.find_one({"id": id})
            if question and "_id" in question:
                question["id"] = str(question["_id"])
                del question["_id"]
            return question

    @staticmethod
    async def create(data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new question"""
        database = get_database()
        if database is None:
            raise Exception("Database not connected")
        
        # If id is provided as string, use it; otherwise generate ObjectId
        if "id" in data:
            question_data = {**data}
            if "_id" not in question_data:
                try:
                    question_data["_id"] = ObjectId(data["id"])
                except:
                    pass
        else:
            question_data = {**data}
        
        result = await database.questions.insert_one(question_data)
        question_data["id"] = str(result.inserted_id)
        if "_id" in question_data:
            question_data["_id"] = result.inserted_id
        
        # ============================================================
        # MYSQL BACKUP: Auto-backup new question (non-blocking)
        # ============================================================
        try:
            from ..services.mysql_backup_service import mysql_backup_service
            asyncio.create_task(mysql_backup_service.backup_question(question_data))
            print(f"📦 MySQL backup triggered for question: {question_data['id']}")
        except Exception as e:
            print(f"⚠️ MySQL question backup failed (non-fatal): {e}")
        
        return question_data

    @staticmethod
    async def find_all() -> List[Dict[str, Any]]:
        """Find all questions"""
        database = get_database()
        if database is None:
            return []
        
        questions = []
        async for question in database.questions.find():
            question["id"] = str(question["_id"])
            del question["_id"]
            questions.append(question)
        return questions

    @staticmethod
    async def update(question_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update question"""
        database = get_database()
        if database is None:
            return None
        
        try:
            result = await database.questions.update_one(
                {"_id": ObjectId(question_id)},
                {"$set": update_data}
            )
            if result.modified_count:
                return await Question.find_by_id(question_id)
        except:
            pass
        return None

    @staticmethod
    async def delete(question_id: str) -> bool:
        """Delete question"""
        database = get_database()
        if database is None:
            return False
        
        try:
            result = await database.questions.delete_one({"_id": ObjectId(question_id)})
            return result.deleted_count > 0
        except:
            return False

