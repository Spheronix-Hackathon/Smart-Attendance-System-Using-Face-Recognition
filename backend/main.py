from __future__ import annotations

import os
from pathlib import Path

import asyncio
from contextlib import asynccontextmanager, suppress
from datetime import timedelta

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.config import settings
from app.database.mongo import ensure_indexes, get_database
from app.realtime import ws_manager
from app.routes.admin import router as admin_router
from app.routes.attendance import router as attendance_router
from app.routes.auth import router as auth_router
from app.routes.teacher import router as teacher_router
from app.routes.student import router as student_router
from app.services.attendance_service import send_absent_notifications
from app.services.face_service import get_face_recognition_status
from app.utils.time import now_ist
from app.utils.time import iso_ist


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

# ── Startup validation ────────────────────────────────────────────────────────
_INSECURE_KEYS = {"change-me-in-production", "change-this-secret", "", "your-secret-key"}
if settings.secret_key in _INSECURE_KEYS:
    import sys
    print(
        "[STARTUP ERROR] SECRET_KEY is not set or is using an insecure default value. "
        "Set a strong SECRET_KEY environment variable before starting the server.",
        file=sys.stderr,
    )
    sys.exit(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_indexes()
    app.state.absent_notices_task = asyncio.create_task(_absent_notices_worker())
    try:
        yield
    finally:
        task = getattr(app.state, "absent_notices_task", None)
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


app = FastAPI(title="Smart Attendance System Using Face Recognition API", lifespan=lifespan)
app.state.ws_manager = ws_manager
app.state.absent_notices_task = None

# ── CORS ──────────────────────────────────────────────────────────────────────
# On Render the app is same-origin (FastAPI serves both API + static frontend),
# so allow_credentials + wildcard is not needed. We still expose a
# ALLOWED_ORIGINS env var for explicit cross-origin setups (e.g. a separate
# React frontend on a different domain).
_allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "")
_allowed_origins: list[str] = (
    [o.strip() for o in _allowed_origins_raw.split(",") if o.strip()]
    if _allowed_origins_raw.strip()
    else ["*"]
)
_use_credentials = "*" not in _allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=_use_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    icon_file = FRONTEND_DIR / "favicon.svg"
    if icon_file.exists():
        return FileResponse(icon_file, media_type="image/svg+xml")
    return Response(status_code=204)


async def _absent_notices_worker() -> None:
    while True:
        try:
            if not settings.absent_notifications_enabled:
                await asyncio.sleep(60)
                continue

            current = now_ist()
            cutoff_passed = (current.hour, current.minute) >= (settings.absent_notice_hour, settings.absent_notice_minute)
            if cutoff_passed:
                db = await get_database()
                departments = await db.users.distinct("department", {"role": "student", "department": {"$ne": None}})
                for department in departments:
                    result = await send_absent_notifications(db, department)
                    if result.get("status") == "failed":
                        print(f"[ABSENT:FAILED] {department} | {result.get('message')}")
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(60)


@app.get("/")
async def root():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return RedirectResponse(url="/static/index.html")
    return {"message": "Smart Attendance System Using Face Recognition API is operational."}


@app.get("/health")
async def health():
    face_status = get_face_recognition_status()
    return {
        "status": "ok",
        "time": iso_ist(),
        "face_recognition_available": face_status["available"],
        "face_recognition_error": face_status["error"],
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


app.include_router(auth_router)
app.include_router(attendance_router)
app.include_router(teacher_router)
app.include_router(student_router)
app.include_router(admin_router)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

