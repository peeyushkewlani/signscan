"""FastAPI application — SignScan traffic sign recognition with auth."""

from __future__ import annotations

import shutil
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Header, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ai_pipeline import CLASS_NAMES, SignDetector
from auth import GOOGLE_CLIENT_ID, change_password, get_user_from_token, google_login, login_user, logout_user, register_user

BASE_DIR   = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = BASE_DIR / "uploads"

ALLOWED_CONTENT_TYPES = {
    "application/octet-stream", "image/bmp", "image/jpeg",
    "image/png", "image/tiff", "image/webp", "image/x-portable-pixmap",
}
ALLOWED_EXTENSIONS = {".bmp", ".jpeg", ".jpg", ".png", ".ppm", ".tif", ".tiff", ".webp"}


# ── Lifespan ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    app.state.detector = None
    try:
        app.state.detector = SignDetector()
        print("[INFO] Detection pipeline is ready.")
    except Exception as exc:
        print(f"[ERROR] Failed to load detection pipeline: {exc}")
    yield


# ── App ───────────────────────────────────────────────────────────────────
app = FastAPI(
    title="SignScan — Traffic Sign Recognition",
    description="AI-powered traffic sign detection and OCR.",
    version="2.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Helpers ───────────────────────────────────────────────────────────────
def get_detector(request: Request) -> SignDetector:
    detector = getattr(request.app.state, "detector", None)
    if detector is None:
        raise HTTPException(503, "The AI pipeline is not available. Check the server logs.")
    return detector


def validate_upload(file: UploadFile) -> str:
    if not file.filename:
        raise HTTPException(400, "Please choose an image file.")
    extension    = Path(file.filename).suffix.lower()
    content_type = (file.content_type or "").lower()
    if extension not in ALLOWED_EXTENSIONS and content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(400, "Unsupported file type. Please upload a JPG, PNG, BMP, TIFF, WebP, or PPM image.")
    return extension or ".jpg"


# ── Pages ─────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def serve_frontend() -> HTMLResponse:
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>Frontend not found</h1>", status_code=404)
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


# ── Auth endpoints ────────────────────────────────────────────────────────
class AuthBody(BaseModel):
    username: str
    password: str


class GoogleBody(BaseModel):
    credential: str  # Google ID token (JWT)


@app.post("/api/auth/register")
async def api_register(body: AuthBody) -> JSONResponse:
    result = register_user(body.username, body.password)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return JSONResponse({"message": "Account created! Please log in."})


@app.post("/api/auth/login")
async def api_login(body: AuthBody) -> JSONResponse:
    result = login_user(body.username, body.password)
    if "error" in result:
        raise HTTPException(401, result["error"])
    return JSONResponse(result)


@app.post("/api/auth/google")
async def api_google_auth(body: GoogleBody) -> JSONResponse:
    """Verify a Google ID token and create a session."""
    result = google_login(body.credential)
    if "error" in result:
        raise HTTPException(401, result["error"])
    return JSONResponse(result)


@app.post("/api/auth/logout")
async def api_logout(authorization: str = Header(default="")) -> JSONResponse:
    logout_user(authorization)
    return JSONResponse({"message": "Logged out successfully."})





@app.get("/api/auth/me")
async def api_me(authorization: str = Header(default="")) -> JSONResponse:
    user = get_user_from_token(authorization)
    if not user:
        raise HTTPException(401, "Not authenticated.")
    return JSONResponse({"username": user})


# ── Health ────────────────────────────────────────────────────────────────
# ── Config (public) ──────────────────────────────────────────────────────
@app.get("/api/config")
async def api_config() -> JSONResponse:
    """Expose non-secret config to the frontend."""
    return JSONResponse({"google_client_id": GOOGLE_CLIENT_ID})


@app.get("/api/health")
async def health_check(request: Request) -> JSONResponse:
    detector = getattr(request.app.state, "detector", None)
    if detector is None:
        return JSONResponse(status_code=503, content={
            "status": "degraded", "model_loaded": False,
            "ocr": {"enabled": False, "message": "Model failed to load."}, "version": "2.0.0",
        })
    return JSONResponse(content={
        "status": "healthy", "model_loaded": True,
        "ocr": {"enabled": detector.ocr_available, "message": detector.ocr_message},
        "model": {"path": detector.model_path.name, "class_count": len(detector.class_names)},
        "version": "2.0.0",
    })


# ── Analyze ───────────────────────────────────────────────────────────────
@app.post("/api/analyze")
async def analyze_image(
    request: Request,
    file: UploadFile = File(...),
    confidence: float = Query(default=0.25, ge=0.05, le=0.95),
    authorization: str = Header(default=""),
) -> JSONResponse:
    """Analyze an uploaded image. Requires a valid auth token."""
    if not get_user_from_token(authorization):
        raise HTTPException(401, "Please log in to use this feature.")

    detector      = get_detector(request)
    file_extension = validate_upload(file)
    temp_path     = UPLOAD_DIR / f"{uuid.uuid4()}{file_extension}"

    try:
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        result = detector.analyze(temp_path, confidence_threshold=confidence)
        result["filename"] = file.filename
        return JSONResponse(content=result)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, f"Analysis failed: {exc}") from exc
    finally:
        if temp_path.exists():
            temp_path.unlink()


@app.get("/api/classes")
async def get_classes(request: Request) -> JSONResponse:
    detector = getattr(request.app.state, "detector", None)
    classes  = detector.class_names if detector else CLASS_NAMES
    return JSONResponse({"classes": classes, "total": len(classes)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
