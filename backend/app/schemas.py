from datetime import datetime, time
from typing import List, Optional

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int


class TokenPayload(BaseModel):
    sub: str
    exp: int


class AccessWindowBase(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time


class AccessWindowCreate(AccessWindowBase):
    pass


class AccessWindowOut(AccessWindowBase):
    id: int

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    full_name: str
    identifier: str
    is_active: bool = True
    expires_at: datetime | None = None


class UserCreate(UserBase):
    password: str
    access_windows: list[AccessWindowCreate] | None = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    access_windows: list[AccessWindowCreate] | None = None


class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmbeddingOut(BaseModel):
    id: int
    model_name: str
    created_at: datetime
    vector: list[float]

    class Config:
        from_attributes = True
        protected_namespaces = ()


class EventCreate(BaseModel):
    user_identifier: Optional[str] = None
    status: str
    message: Optional[str] = None
    device_id: Optional[str] = None
    confidence: Optional[float] = None


class EventOut(BaseModel):
    id: int
    user_id: Optional[int]
    status: str
    message: Optional[str]
    device_id: Optional[str]
    confidence: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class SyncPayload(BaseModel):
    photos: list["PhotoMeta"]
    users: list[UserOut]
    access_windows: list[AccessWindowOut]
    config: dict


class CaptureUploadResponse(BaseModel):
    device_id: str | None
    person_name: str
    captured_at: datetime
    filename: str
    url: str
    size_bytes: int


class PhotoMeta(BaseModel):
    user_id: int | None = None
    person_name: str | None = None
    filename: str
    url: str
    captured_at: datetime | None = None


SyncPayload.model_rebuild()
