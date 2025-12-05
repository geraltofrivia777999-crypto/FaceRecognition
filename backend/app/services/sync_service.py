import hashlib
import json
from typing import Tuple

from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.config import get_settings


def build_sync_payload(db: Session) -> tuple[schemas.SyncPayload, str]:
    settings = get_settings()
    embeddings_out: list[schemas.EmbeddingOut] = []
    for emb in db.query(models.Embedding).all():
        vector = json.loads(emb.vector)
        embeddings_out.append(
            schemas.EmbeddingOut(
                id=emb.id,
                model_name=emb.model_name,
                created_at=emb.created_at,
                vector=vector,
            )
        )

    users = [schemas.UserOut.model_validate(user) for user in db.query(models.User).all()]
    windows = [schemas.AccessWindowOut.model_validate(w) for w in db.query(models.AccessWindow).all()]
    config = {
        "threshold": settings.threshold,
        "gpio_pin": settings.gpio_pin,
        "gpio_pulse_ms": settings.gpio_pulse_ms,
        "sync_interval_sec": settings.sync_interval_sec,
    }
    payload = schemas.SyncPayload(
        embeddings=embeddings_out,
        users=users,
        access_windows=windows,
        config=config,
    )
    payload_hash = hashlib.sha256(payload.model_dump_json().encode()).hexdigest()
    return payload, payload_hash
