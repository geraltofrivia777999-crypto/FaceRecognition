from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app import schemas
from backend.app.config import get_settings
from backend.app.deps import get_db
from backend.app.security import create_access_token
from backend.app.services.user_service import authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials")
    settings = get_settings()
    access_token = create_access_token(user.identifier, settings.jwt_exp_minutes)
    refresh_token = create_access_token(user.identifier, settings.refresh_exp_minutes)
    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_exp_minutes * 60,
        refresh_expires_in=settings.refresh_exp_minutes * 60,
    )
