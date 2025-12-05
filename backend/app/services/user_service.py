from sqlalchemy.orm import Session

from backend.app import models
from backend.app.schemas import UserCreate, UserUpdate
from backend.app.security import get_password_hash, verify_password


def get_user_by_identifier(db: Session, identifier: str) -> models.User | None:
    return db.query(models.User).filter(models.User.identifier == identifier).first()


def create_user(db: Session, payload: UserCreate) -> models.User:
    hashed = get_password_hash(payload.password)
    user = models.User(
        full_name=payload.full_name,
        identifier=payload.identifier,
        password_hash=hashed,
        is_active=payload.is_active,
        expires_at=payload.expires_at,
    )
    db.add(user)
    db.flush()

    if payload.access_windows:
        for window in payload.access_windows:
            db.add(
                models.AccessWindow(
                    user_id=user.id,
                    day_of_week=window.day_of_week,
                    start_time=window.start_time,
                    end_time=window.end_time,
                )
            )
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: models.User, payload: UserUpdate) -> models.User:
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.password:
        user.password_hash = get_password_hash(payload.password)
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.expires_at is not None:
        user.expires_at = payload.expires_at
    db.add(user)
    if payload.access_windows is not None:
        db.query(models.AccessWindow).filter(models.AccessWindow.user_id == user.id).delete()
        for window in payload.access_windows:
            db.add(
                models.AccessWindow(
                    user_id=user.id,
                    day_of_week=window.day_of_week,
                    start_time=window.start_time,
                    end_time=window.end_time,
                )
            )
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: models.User) -> None:
    db.delete(user)
    db.commit()


def list_users(db: Session) -> list[models.User]:
    return db.query(models.User).order_by(models.User.created_at.desc()).all()


def authenticate_user(db: Session, identifier: str, password: str) -> models.User | None:
    user = get_user_by_identifier(db, identifier)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def ensure_default_admin(db: Session, identifier: str, password: str) -> None:
    if get_user_by_identifier(db, identifier):
        return
    safe_password = password.encode("utf-8")[:64].decode("utf-8", errors="ignore") or "admin"
    try:
        pwd_hash = get_password_hash(safe_password)
    except Exception:
        pwd_hash = get_password_hash("admin")
    admin = models.User(
        full_name="Administrator",
        identifier=identifier,
        password_hash=pwd_hash,
        is_active=True,
    )
    db.add(admin)
    db.commit()
