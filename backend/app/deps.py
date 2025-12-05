import logging
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import models
from .config import get_settings
from .db import SessionLocal
from .security import decode_token
from .services.model_registry import FaceEmbedderRegistry, HashedEmbedder

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
logger = logging.getLogger(__name__)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    payload = decode_token(token)
    identifier: str | None = payload.get("sub")  # type: ignore
    if not identifier:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = db.query(models.User).filter(models.User.identifier == identifier).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@lru_cache()
def get_embedder():
    # Registry allows swapping FaceNet to another model later.
    registry = FaceEmbedderRegistry()
    settings = get_settings()

    try:
        from .services.facenet_embedder import FaceNetEmbedder

        registry.register("facenet", FaceNetEmbedder())
    except Exception as exc:
        logger.warning("FaceNet not available, falling back to hashed embedder: %s", exc)

    registry.register("hashed", HashedEmbedder())

    try:
        return registry.get(settings.embedder_name)
    except Exception:
        logger.warning("Embedder %s not found, using default", settings.embedder_name)
        return registry.get_default()
