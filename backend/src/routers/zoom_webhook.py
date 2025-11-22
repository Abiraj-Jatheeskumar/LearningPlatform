from fastapi import APIRouter, Request, Header, HTTPException
from fastapi.responses import JSONResponse
import hmac, hashlib, base64, os, json
from datetime import datetime
from src.database.connection import get_database

router = APIRouter(prefix="/api/zoom", tags=["Zoom Webhook"])

# -------------------------------------------------------------
# Compute Zoom signature
# -------------------------------------------------------------
def compute_signature(secret: str, timestamp: str, body: bytes):
    message = f"v0:{timestamp}:{body.decode()}"
    hash_ = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return f"v0={hash_}"

# -------------------------------------------------------------
# MAIN WEBHOOK ENDPOINT
# -------------------------------------------------------------
@router.post("/webhook")
async def zoom_webhook(
    request: Request,
    zoom_signature: str = Header(None, alias="x-zoom-signature"),
    zoom_timestamp: str = Header(None, alias="x-zoom-request-timestamp")
):

    raw = await request.body()

    # Parse JSON
    try:
        data = json.loads(raw.decode())
    except:
        raise HTTPException(status_code=400, detail="Bad JSON")

    event = data.get("event")
    print("\n==============================")
    print("ZOOM WEBHOOK RECEIVED:", event)
    print("==============================")
    print(raw.decode())

    # =====================================================
    # 1) URL VALIDATION
    # =====================================================
    if event == "endpoint.url_validation":
        print("Processing Zoom URL validation...")
        plain = data["payload"]["plainToken"]
        secret = os.getenv("ZOOM_WEBHOOK_SECRET", "")

        if secret == "":
            raise HTTPException(status_code=500, detail="Secret missing")

        hashed = hmac.new(secret.encode(), plain.encode(), hashlib.sha256).digest()
        encrypted = base64.b64encode(hashed).decode()

        return {
            "plainToken": plain,
            "encryptedToken": encrypted
        }

    # =====================================================
    # 2) VALIDATE SIGNATURE (mandatory for real events)
    # =====================================================
    if zoom_signature and zoom_timestamp:
        secret = os.getenv("ZOOM_WEBHOOK_SECRET", "")
        expected = compute_signature(secret, zoom_timestamp, raw)

        if not hmac.compare_digest(expected, zoom_signature):
            print("❌ INVALID SIGNATURE!")
            raise HTTPException(status_code=401, detail="Invalid signature")
        print("✅ Signature verified successfully")
    else:
        print("⚠️ No signature provided (Zoom URL validation?)")

    # =====================================================
    # 3) MEETING PARTICIPANT JOIN / LEAVE
    # =====================================================
    obj = data.get("payload", {}).get("object", {})
    participant = obj.get("participant", {})
    db = get_database()

    # JOIN
    if event in ["meeting.participant_joined", "participant.joined"]:
        await db.participants.insert_one({
            "meeting_id": obj.get("id"),
            "user_id": participant.get("user_id") or participant.get("id"),
            "name": participant.get("user_name") or participant.get("name"),
            "email": participant.get("email"),
            "status": "joined",
            "timestamp": datetime.utcnow()
        })
        print("✔ JOIN STORED")
        return {"status": "ok", "event": "participant_joined"}

    # LEAVE
    if event in ["meeting.participant_left", "participant.left"]:
        await db.participants.update_one(
            {
                "meeting_id": obj.get("id"),
                "user_id": participant.get("user_id") or participant.get("id")
            },
            {"$set": {"status": "left", "timestamp": datetime.utcnow()}}
        )
        print("✔ LEAVE UPDATED")
        return {"status": "ok", "event": "participant_left"}

    # OTHER EVENTS
    return {"status": "ignored", "event": event}


@router.get("/webhook/test")
async def webhook_test():
    return {"status": "ok", "message": "webhook active"}
