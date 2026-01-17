import asyncio
from src.database.connection import get_database

async def check_users():
    db = await get_database()
    count = await db['users'].count_documents({})
    print(f"Total users in database: {count}")
    
    if count > 0:
        users = await db['users'].find({}, {"email": 1, "name": 1, "role": 1}).to_list(length=10)
        print("\nUsers found:")
        for user in users:
            print(f"  - {user['name']} ({user['email']}) - Role: {user['role']}")
    else:
        print("No users found! Run: python src/database/seed.py")

if __name__ == "__main__":
    asyncio.run(check_users())
