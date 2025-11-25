# src/services/zoom_service.py
import os
import base64
from typing import Dict, Any
import httpx

ZOOM_ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")
ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")


async def get_zoom_access_token() -> str:
    if not (ZOOM_ACCOUNT_ID and ZOOM_CLIENT_ID and ZOOM_CLIENT_SECRET):
        raise RuntimeError("Missing Zoom S2S env vars")

    auth_str = f"{ZOOM_CLIENT_ID}:{ZOOM_CLIENT_SECRET}"
    basic_token = base64.b64encode(auth_str.encode()).decode()

    url = "https://zoom.us/oauth/token"

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            params={
                "grant_type": "account_credentials",
                "account_id": ZOOM_ACCOUNT_ID,
            },
            headers={
                "Authorization": f"Basic {basic_token}",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["access_token"]


async def create_zoom_meeting(
    topic: str,
    start_time: str,
    duration_minutes: int,
    timezone: str = "Asia/Colombo",
) -> Dict[str, Any]:
    """
    Returns dict with: id, join_url, start_url, password, start_time, duration
    """
    access_token = await get_zoom_access_token()

    url = "https://api.zoom.us/v2/users/me/meetings"

    payload = {
        "topic": topic,
        "type": 2,  # scheduled meeting
        "start_time": start_time,  # ISO 8601 string
        "duration": duration_minutes,
        "timezone": timezone,
        "settings": {
            "join_before_host": False,
            "waiting_room": True,
            "approval_type": 2,
        },
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        data = resp.json()

    return {
        "id": str(data["id"]),
        "join_url": data["join_url"],
        "start_url": data["start_url"],
        "password": data.get("password"),
        "start_time": data.get("start_time"),
        "duration": data.get("duration"),
    }
