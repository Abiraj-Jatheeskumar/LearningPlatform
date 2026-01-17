import os
import httpx
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ZOOM_ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")
ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")

print("=== Zoom Credentials Check ===")
print(f"Account ID: {ZOOM_ACCOUNT_ID}")
print(f"Client ID: {ZOOM_CLIENT_ID}")
print(f"Client Secret: {ZOOM_CLIENT_SECRET[:10]}..." if ZOOM_CLIENT_SECRET else "None")
print()

async def test_zoom_token():
    print("Testing Zoom OAuth token request...")
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://zoom.us/oauth/token",
            params={
                "grant_type": "account_credentials",
                "account_id": ZOOM_ACCOUNT_ID,
            },
            auth=(ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET),
        )
        
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text}")
        
        if resp.status_code == 200:
            print("\n✅ SUCCESS! Token obtained successfully.")
        else:
            print("\n❌ FAILED! Check credentials or Zoom app configuration.")
            print("\nPossible issues:")
            print("1. Verify Zoom app type is 'Server-to-Server OAuth'")
            print("2. Check if credentials are copied correctly")
            print("3. Ensure app is activated in Zoom Marketplace")

if __name__ == "__main__":
    asyncio.run(test_zoom_token())
