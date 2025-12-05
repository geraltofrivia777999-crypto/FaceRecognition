from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app import schemas
from backend.app.deps import get_current_user, get_db
from backend.app.services import event_service

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=list[schemas.EventOut])
def list_events(db: Session = Depends(get_db), _: str = Depends(get_current_user)):
    events = event_service.list_events(db)
    return [schemas.EventOut.model_validate(ev) for ev in events]
