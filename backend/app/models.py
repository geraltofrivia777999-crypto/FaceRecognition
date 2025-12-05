from datetime import datetime, time
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    identifier = Column(String(64), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    embeddings = relationship("Embedding", back_populates="user", cascade="all, delete-orphan")
    access_windows = relationship("AccessWindow", back_populates="user", cascade="all, delete-orphan")
    events = relationship("EventLog", back_populates="user")


class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    vector = Column(Text, nullable=False)
    model_name = Column(String(64), default="facenet")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="embeddings")


class AccessWindow(Base):
    __tablename__ = "access_windows"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0-6
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    user = relationship("User", back_populates="access_windows")


class EventLog(Base):
    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    status = Column(String(32), nullable=False)
    message = Column(Text, nullable=True)
    device_id = Column(String(64), nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="events")


class DeviceSync(Base):
    __tablename__ = "device_sync"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(64), unique=True, nullable=False)
    last_sync_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_payload_hash = Column(String(128), nullable=True)
