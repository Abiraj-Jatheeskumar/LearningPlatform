from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import os
from contextlib import asynccontextmanager

from src.middleware.auth import AuthMiddleware
from src.database.connection import connect_to_mongo, close_mongo_connection

# ✅ Use ONLY this manager — the correct one
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

    # Allow Zoom webhooks without authentication
    if request.url.path.startswith("/api/zoom/events"):
        return await call_next(request)

    return await auth_middleware(request, call_next)


# --------------------------------------------------------
# SECURITY HEADERS (DISABLE FOR /api/zoom/events)
# --------------------------------------------------------
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):

    response = await call_next(request)

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
            response.headers.pop(h, None)
        return response

    # Default security headers
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
# ROUTERS  (NO websocket_notifications ANYWHERE!!)
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
app.include_router(live.router)


# --------------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "ok", "time": datetime.now().isoformat()}


# --------------------------------------------------------
# TEST – BROADCAST TO ALL STUDENTS
# --------------------------------------------------------
@app.get("/test-ws")
async def test_ws():
    message = {
        "type": "test_message",
        "title": "Hello from Backend 👋",
        "body": "If you see this message in the browser, WebSocket works!",
        "timestamp": datetime.now().isoformat()
    }
    sent = await ws_manager.broadcast_to_all(message)
    return {"success": True, "sent": sent}


# --------------------------------------------------------
# WEBSOCKET ENDPOINT (ONLY ONE CORRECT ENDPOINT)
# --------------------------------------------------------
@app.websocket("/ws/{meeting_id}/{student_id}")
async def websocket_endpoint(websocket: WebSocket, meeting_id: str, student_id: str):
    """
    Real-time WebSocket notifications for students
    """
    try:
        await ws_manager.connect(websocket, meeting_id, student_id)

        # Keep alive forever
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        ws_manager.disconnect(meeting_id, student_id)
