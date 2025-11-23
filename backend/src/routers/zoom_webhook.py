from fastapi import APIRouter, Request, Header, HTTPException
import hmac, hashlib, base64, os, json
from datetime import datetime
from src.database.connection import get_database

router = APIRouter(prefix="/api/zoom", tags=["Zoom Webhook"])


# -------------------------------------------------------------
# Compute Zoom signature (Zoom V0 signing method)
# -------------------------------------------------------------
def compute_signature(secret: str, timestamp: str, body: bytes):
    message = f"v0:{timestamp}:{body.decode()}"
    hash_ = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return f"v0={hash_}"


# -------------------------------------------------------------
# MAIN ZOOM WEBHOOK ENDPOINT
# -------------------------------------------------------------
@router.post("/events")
async def zoom_events(
    request: Request,
    zoom_signature: str = Header(None, alias="x-zoom-signature"),
    zoom_timestamp: str = Header(None, alias="x-zoom-request-timestamp")
):

    raw = await request.body()

    # Parse incoming JSON
    try:
        data = json.loads(raw.decode())
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON received")

    event = data.get("event")
    print("\n==============================")
    print("ZOOM WEBHOOK RECEIVED:", event)
    print("==============================")
    print(raw.decode(), "\n")

    # ---------------------------------------------------------
    # 1. URL VALIDATION EVENT
    # ---------------------------------------------------------
    if event == "endpoint.url_validation":
        print("Handling Zoom URL validation...")

        plain = data["payload"]["plainToken"]
        secret = os.getenv("ZOOM_WEBHOOK_SECRET", "")

        if not secret:
            raise HTTPException(status_code=500, detail="ZOOM_WEBHOOK_SECRET missing")

        hashed = hmac.new(secret.encode(), plain.encode(), hashlib.sha256).digest()
        encrypted = base64.b64encode(hashed).decode()

        return {
            "plainToken": plain,
            "encryptedToken": encrypted
        }

    # ---------------------------------------------------------
    # 2. SIGNATURE VALIDATION (Required for real events)
    # ---------------------------------------------------------
    if zoom_signature and zoom_timestamp:
        secret = os.getenv("ZOOM_WEBHOOK_SECRET", "")
        expected = compute_signature(secret, zoom_timestamp, raw)

        if not hmac.compare_digest(expected, zoom_signature):
            print("❌ INVALID SIGNATURE!")
            raise HTTPException(status_code=401, detail="Invalid signature")

        print("✅ Signature verified")
    else:
        print("⚠️ No signature (this is normal during URL validation)")

    # ---------------------------------------------------------
    # 3. FETCH DATABASE + OBJECT DATA
    # ---------------------------------------------------------
    db = get_database()
    print("👉 USING DATABASE:", db.name)

    obj = data.get("payload", {}).get("object", {})
    participant = obj.get("participant", {})


    # =========================================================
    # PARTICIPANT JOINED
    # =========================================================
    if event == "meeting.participant_joined":
        doc = {
            "event": "joined",
            "meeting_id": obj.get("id"),
            "meeting_uuid": obj.get("uuid"),
            "topic": obj.get("topic"),

            "user_id": participant.get("user_id") or participant.get("id"),
            "name": participant.get("user_name") or participant.get("name"),
            "email": participant.get("email"),
            "join_time": participant.get("join_time"),

            "timestamp": datetime.utcnow()
        }

        await db.zoom_participants.insert_one(doc)
        print("✔ JOIN STORED:", doc)

        return {"status": "ok", "event": "participant_joined"}


    # =========================================================
    # PARTICIPANT LEFT
    # =========================================================
    if event == "meeting.participant_left":
        doc = {
            "event": "left",
            "meeting_id": obj.get("id"),
            "meeting_uuid": obj.get("uuid"),
            "topic": obj.get("topic"),

            "user_id": participant.get("user_id") or participant.get("id"),
            "name": participant.get("user_name") or participant.get("name"),
            "email": participant.get("email"),
            "leave_time": participant.get("leave_time"),

            "timestamp": datetime.utcnow()
        }

        await db.zoom_participants.insert_one(doc)
        print("✔ LEAVE STORED:", doc)

        return {"status": "ok", "event": "participant_left"}


    # =========================================================
    # MEETING ENDED
    # =========================================================
    if event == "meeting.ended":
        doc = {
            "event": "meeting_ended",
            "meeting_id": obj.get("id"),
            "meeting_uuid": obj.get("uuid"),
            "topic": obj.get("topic"),
            "duration": obj.get("duration"),
            "timezone": obj.get("timezone"),
            "timestamp": datetime.utcnow()
        }

        await db.zoom_meetings.insert_one(doc)
        print("✔ MEETING ENDED STORED:", doc)

        return {"status": "ok", "event": "meeting_ended"}


    # Unknown events — ignore
    return {"status": "ignored", "event": event}



# -------------------------------------------------------------
# TEST ENDPOINT (OPTIONAL)
# -------------------------------------------------------------
@router.get("/events/test")
async def webhook_test():
    return {"status": "ok", "message": "zoom webhook active"}
