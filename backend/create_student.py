"""Quick script to create a test student account"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.database.connection import connect_to_mongo, close_mongo_connection, get_database
import hashlib

async def create_student():
    await connect_to_mongo()
    db = get_database()
    
    if db is None:
        print("❌ Failed to connect to database")
        return
    
    # Check if student already exists
    existing = await db['users'].find_one({"email": "student@example.com"})
    if existing:
        print("✅ Student already exists: student@example.com")
        return
    
    # Create student
    user = {
        'firstName': 'Test',
        'lastName': 'Student',
        'email': 'student@example.com',
        'password': hashlib.sha256('password123'.encode()).hexdigest(),
        'role': 'student',
        'status': 1
    }
    
    result = await db['users'].insert_one(user)
    print(f"✅ Created student account:")
    print(f"   Email: student@example.com")
    print(f"   Password: password123")
    print(f"   ID: {result.inserted_id}")
    
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(create_student())
