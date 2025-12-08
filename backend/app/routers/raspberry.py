import re
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.deps import get_db
from backend.app.services import event_service
from backend.app.services.sync_service import build_sync_payload

router = APIRouter(prefix="/raspberry", tags=["raspberry"])
CAPTURES_DIR = Path("data") / "captures"
_SAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


@router.get("/sync", response_model=schemas.SyncPayload)
def sync(device_id: str | None = Header(default=None, alias="X-Device-Id"), db: Session = Depends(get_db)):
    payload, payload_hash = build_sync_payload(db)
    if device_id:
        existing = db.query(models.DeviceSync).filter(models.DeviceSync.device_id == device_id).first()
        if existing:
            existing.last_payload_hash = payload_hash
            db.add(existing)
        else:
            db.add(models.DeviceSync(device_id=device_id, last_payload_hash=payload_hash))
        db.commit()
    response = payload
    return response


@router.post("/events/log", response_model=schemas.EventOut)
def log_event(
    payload: schemas.EventCreate,
    db: Session = Depends(get_db),
):
    user = None
    if payload.user_identifier:
        user = db.query(models.User).filter(models.User.identifier == payload.user_identifier).first()
    event = event_service.log_event(db, payload, user)
    return schemas.EventOut.model_validate(event)


def _sanitize(value: str, fallback: str) -> str:
    cleaned = _SAFE_CHARS.sub("_", value.strip())
    return cleaned or fallback


@router.post("/upload-capture", response_model=schemas.CaptureUploadResponse)
async def upload_capture(
    person_name: str = Form(...),
    image: UploadFile = File(...),
    captured_at: datetime | None = Form(None),
    device_id: str | None = Header(default=None, alias="X-Device-Id"),
):
    """
    Accept a raw photo + metadata from Raspberry Pi without creating embeddings on the server.
    The image is stored on disk along with the provided person name and capture time.
    """
    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
    device_slug = _sanitize(device_id or "unknown_device", "unknown_device")
    person_slug = _sanitize(person_name or "unknown", "unknown")
    device_dir = CAPTURES_DIR / device_slug
    device_dir.mkdir(parents=True, exist_ok=True)

    try:
        content = await image.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read uploaded image: {exc}") from exc
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")

    ts = captured_at or datetime.utcnow()
    ext = Path(image.filename or "").suffix or ".jpg"
    filename = f"{ts.strftime('%Y%m%dT%H%M%S')}_{person_slug}{ext}"
    out_path = device_dir / filename
    try:
        out_path.write_bytes(content)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to store image: {exc}") from exc

    rel_url = f"/captures/{device_slug}/{filename}"
    return schemas.CaptureUploadResponse(
        device_id=device_id,
        person_name=person_name,
        captured_at=ts,
        filename=filename,
        url=rel_url,
        size_bytes=len(content),
    )
