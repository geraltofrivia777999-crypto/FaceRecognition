from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.config import get_settings
from backend.app.deps import get_current_user, get_db
from backend.app.services import event_service
from backend.app.services.sync_service import build_sync_payload

router = APIRouter(prefix="/raspberry", tags=["raspberry"])


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
