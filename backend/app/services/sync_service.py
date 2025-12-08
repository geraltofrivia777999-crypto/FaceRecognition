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
    user_lookup = {user.id: user for user in users}
    if photos_root.exists():
        for user_dir in photos_root.iterdir():
            if not user_dir.is_dir():
                continue
            name = user_dir.name
            if not name.startswith("user_"):
                continue
            try:
                uid = int(name.split("_", 1)[1])
            except Exception:
                continue
            for file_path in user_dir.iterdir():
                if not file_path.is_file():
                    continue
                if file_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                    continue
                stat = file_path.stat()
                user_obj = user_lookup.get(uid)
                photos.append(
                    schemas.PhotoMeta(
                        user_id=uid if user_obj else None,
                        person_name=user_obj.full_name if user_obj else None,
                        filename=file_path.name,
                        url=f"/uploads/user_{uid}/{file_path.name}",
                        captured_at=datetime.fromtimestamp(stat.st_mtime),
                    )
                )
    captures_root = Path("data/captures")
    if captures_root.exists():
        for device_dir in captures_root.iterdir():
            if not device_dir.is_dir():
                continue
            for file_path in device_dir.iterdir():
                if not file_path.is_file():
                    continue
                if file_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                    continue
                meta_path = file_path.with_suffix(file_path.suffix + ".json")
                person_name = None
                captured_at = None
                try:
                    if meta_path.exists():
                        import json

                        meta = json.loads(meta_path.read_text())
                        person_name = meta.get("person_name")
                        captured_at_raw = meta.get("captured_at")
                        if captured_at_raw:
                            captured_at = datetime.fromisoformat(str(captured_at_raw))
                except Exception:
                    pass
                photos.append(
                    schemas.PhotoMeta(
                        user_id=None,
                        person_name=person_name,
                        filename=file_path.name,
                        url=f"/captures/{device_dir.name}/{file_path.name}",
                        captured_at=captured_at,
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
