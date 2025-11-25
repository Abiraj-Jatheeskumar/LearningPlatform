from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import os
from contextlib import asynccontextmanager

from src.middleware.auth import AuthMiddleware
from src.database.connection import connect_to_mongo, close_mongo_connection
from src.services.ws_manager import ws_manager


# --------------------------------------------------------
# LIFESPAN
# --------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(lifespan=lifespan)


# --------------------------------------------------------
# CORS (open for Zoom + Frontend)
# --------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------
# AUTH MIDDLEWARE (ALLOW /api/zoom/events)
# --------------------------------------------------------
auth_middleware = AuthMiddleware()

@app.middleware("http")
async def auth_middleware_wrapper(request: Request, call_next):

    # Allow Zoom webhooks
    if request.url.path.startswith("/api/zoom/events"):
        return await call_next(request)

    return await auth_middleware(request, call_next)


# --------------------------------------------------------
# SECURITY HEADERS (DISABLE FOR /api/zoom/events)
# --------------------------------------------------------
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):

    response = await call_next(request)

    # Disable security headers for Zoom webhook
    if request.url.path.startswith("/api/zoom/events"):
        remove_headers = [
            "Strict-Transport-Security",
            "X-Content-Type-Options",
            "Referrer-Policy",
            "X-Frame-Options",
            "Permissions-Policy",
            "Content-Security-Policy"
        ]
        for h in remove_headers:
            if h in response.headers:
                del response.headers[h]
        return response

    # Security headers for everything else
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self' https:; "
        "frame-ancestors 'self' https://*.zoom.us;"
    )

    return response


# --------------------------------------------------------
# ROUTERS
# --------------------------------------------------------
from src.routers import (
    auth,
    quiz,
    clustering,
    question,
    zoom_webhook,
    zoom_chatbot,
    course,
    live_question,
    websocket_notifications,
    live,
)

app.include_router(auth.router)
app.include_router(quiz.router)
app.include_router(clustering.router)
app.include_router(question.router)
app.include_router(zoom_webhook.router)
app.include_router(zoom_chatbot.router)
app.include_router(course.router)
app.include_router(live_question.router)
app.include_router(websocket_notifications.router)
app.include_router(live.router)


# --------------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "ok", "time": datetime.now().isoformat()}

# --------------------------------------------------------
# TEST – BROADCAST TO ALL WEBSOCKET CLIENTS
# --------------------------------------------------------
@app.get("/test-ws")
async def test_ws():
    message = {
        "type": "test_message",
        "title": "Hello from Backend 👋",
        "body": "If you see this in browser console, WebSocket broadcast works.",
        "timestamp": datetime.now().isoformat()
    }

    sent = await ws_manager.broadcast_to_all(message)
    return {"success": True, "sent": sent}



# --------------------------------------------------------
# WEBSOCKET ENDPOINT
# --------------------------------------------------------
@app.websocket("/ws/{meeting_id}/{student_id}")
async def websocket_endpoint(websocket: WebSocket, meeting_id: str, student_id: str):
    """
    WebSocket endpoint for real-time student notifications
    Students connect here to receive question triggers and updates
    """
    try:
        await ws_manager.connect(websocket, meeting_id, student_id)
        while True:
            # Keep connection alive, receive heartbeat or other messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(meeting_id, student_id)
