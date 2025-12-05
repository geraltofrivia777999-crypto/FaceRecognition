from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.config import get_settings
from backend.app.db import SessionLocal, init_db
from backend.app.routers import auth, events, raspberry, users
from backend.app.services.user_service import ensure_default_admin

settings = get_settings()

# Ensure required directories exist before mounting static files
DATA_DIR = Path("data")
PHOTOS_DIR = DATA_DIR / "photos"
EMBED_DIR = Path(settings.embeddings_dir)
DATA_DIR.mkdir(exist_ok=True)
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
EMBED_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Path("data").mkdir(exist_ok=True)
    Path(settings.embeddings_dir).mkdir(parents=True, exist_ok=True)
    Path("data/photos").mkdir(parents=True, exist_ok=True)
    init_db()
    db = SessionLocal()
    try:
        ensure_default_admin(db, settings.default_admin_identifier, settings.default_admin_password)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(raspberry.router)
app.include_router(events.router)

frontend_path = Path(__file__).resolve().parents[2] / "frontend"
if frontend_path.exists():
    app.mount("/ui", StaticFiles(directory=frontend_path, html=True), name="ui")
app.mount("/uploads", StaticFiles(directory=PHOTOS_DIR, check_dir=False), name="uploads")


def get_app() -> FastAPI:
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
