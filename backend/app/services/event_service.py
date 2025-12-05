from sqlalchemy.orm import Session

from backend.app import models
from backend.app.schemas import EventCreate


def log_event(db: Session, payload: EventCreate, user: models.User | None) -> models.EventLog:
    event = models.EventLog(
        user_id=user.id if user else None,
        status=payload.status,
        message=payload.message,
        device_id=payload.device_id,
        confidence=payload.confidence,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_events(db: Session, limit: int = 100) -> list[models.EventLog]:
    return db.query(models.EventLog).order_by(models.EventLog.created_at.desc()).limit(limit).all()
