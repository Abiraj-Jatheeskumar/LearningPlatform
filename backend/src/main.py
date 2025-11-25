from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from contextlib import asynccontextmanager

from src.middleware.auth import AuthMiddleware
from src.database.connection import connect_to_mongo, close_mongo_connection

# ✅ Only the correct WebSocket manager
from src.services.ws_manager import ws_manager


# --------------------------------------------------------
# LIFESPAN (DB connect/disconnect)
# --------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(lifespan=lifespan)


# --------------------------------------------------------
# CORS (Open for Zoom + Vercel Frontend)
# --------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------
# AUTH MIDDLEWARE (Skip Zoom webhook path)
# --------------------------------------------------------
auth_middleware = AuthMiddleware()

@app.middleware("http")
async def auth_middleware_wrapper(request: Request, call_next):
    if request.url.path.startswith("/api/zoom/events"):
        return await call_next(request)
    return await auth_middleware(request, call_next)


# --------------------------------------------------------
# SECURITY HEADERS (Disable for Zoom webhook)
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

    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self' https:; frame-ancestors 'self' https://*.zoom.us;"
    )

    return response


# --------------------------------------------------------
# IMPORT ROUTERS (NO websocket_notifications!)
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
# TEST GLOBAL BROADCAST (Use for debugging)
# --------------------------------------------------------
@app.get("/test-ws")
async def test_ws():
    message = {
        "type": "test_message",
        "title": "Hello from Backend 👋",
        "body": "If you see this in browser, WebSocket works!",
        "timestamp": datetime.now().isoformat()
    }
    sent = await ws_manager.broadcast_global(message)
    return {"success": True, "sent": sent}


# --------------------------------------------------------
# GLOBAL STUDENT WEBSOCKET ENDPOINT
# --------------------------------------------------------
@app.websocket("/ws/global/{student_id}")
async def websocket_global(websocket: WebSocket, student_id: str):
    """
    Every student connects here.
    Instructor sends broadcast (global).
    """
    try:
        await ws_manager.connect_global(websocket)

        # keep websocket alive
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        ws_manager.disconnect_global(websocket)
