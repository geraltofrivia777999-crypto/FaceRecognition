import hashlib
from datetime import datetime
from pathlib import Path
from typing import Tuple

from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.config import get_settings


def build_sync_payload(db: Session) -> tuple[schemas.SyncPayload, str]:
    settings = get_settings()
    users = [schemas.UserOut.model_validate(user) for user in db.query(models.User).all()]
    windows = [schemas.AccessWindowOut.model_validate(w) for w in db.query(models.AccessWindow).all()]
    photos: list[schemas.PhotoMeta] = []
    photos_root = Path("data/photos")
    for user in users:
        user_dir = photos_root / f"user_{user.id}"
        if not user_dir.exists():
            continue
        for file_path in user_dir.iterdir():
            if not file_path.is_file():
                continue
            stat = file_path.stat()
            photos.append(
                schemas.PhotoMeta(
                    user_id=user.id,
                    filename=file_path.name,
                    url=f"/uploads/user_{user.id}/{file_path.name}",
                    captured_at=datetime.fromtimestamp(stat.st_mtime),
                )
            )
    config = {
        "threshold": settings.threshold,
        "gpio_pin": settings.gpio_pin,
        "gpio_pulse_ms": settings.gpio_pulse_ms,
        "sync_interval_sec": settings.sync_interval_sec,
    }
    payload = schemas.SyncPayload(
        photos=photos,
        users=users,
        access_windows=windows,
        config=config,
    )
    payload_hash = hashlib.sha256(payload.model_dump_json().encode()).hexdigest()
    return payload, payload_hash
