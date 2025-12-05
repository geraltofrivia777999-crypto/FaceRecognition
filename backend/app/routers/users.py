import json
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.deps import get_current_user, get_db, get_embedder
from backend.app.services import embedding_service, user_service
from backend.app.services.model_registry import BaseEmbedder

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/create", response_model=schemas.UserOut)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    existing = user_service.get_user_by_identifier(db, payload.identifier)
    if existing:
        raise HTTPException(status_code=400, detail="User identifier already exists")
    return user_service.create_user(db, payload)


@router.get("/", response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    return user_service.list_users(db)


@router.put("/update/{user_id}", response_model=schemas.UserOut)
def update_user(
    user_id: int,
    payload: schemas.UserUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_service.update_user(db, user, payload)


@router.delete("/delete/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_service.delete_user(db, user)
    return {"status": "deleted"}


@router.post("/upload-photo", response_model=list[schemas.EmbeddingOut])
async def upload_photo(
    user_id: int = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    embedder: BaseEmbedder = Depends(get_embedder),
    _: models.User = Depends(get_current_user),
):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    stored: list[schemas.EmbeddingOut] = []
    photo_dir = Path("data/photos") / f"user_{user_id}"
    photo_dir.mkdir(parents=True, exist_ok=True)
    for file in files:
        content = await file.read()
        vector = embedder.generate_embedding(content)
        emb = embedding_service.add_embedding(db, user.id, vector, embedder.name)
        # Save photo for preview
        ext = Path(file.filename or "").suffix or ".jpg"
        out_path = photo_dir / f"{emb.id}{ext}"
        out_path.write_bytes(content)
        stored.append(
            schemas.EmbeddingOut(
                id=emb.id,
                model_name=emb.model_name,
                created_at=emb.created_at,
                vector=vector,
            )
        )
    return stored


@router.get("/get-embeddings/{user_id}", response_model=list[schemas.EmbeddingOut])
def get_embeddings(user_id: int, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    embeddings = embedding_service.get_embeddings_for_user(db, user.id)
    return [
        schemas.EmbeddingOut(
            id=emb.id,
            model_name=emb.model_name,
            created_at=emb.created_at,
            vector=json.loads(emb.vector),
        )
        for emb in embeddings
    ]


@router.get("/photos/{user_id}", response_model=list[str])
def list_photos(user_id: int, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    photo_dir = Path("data/photos") / f"user_{user_id}"
    if not photo_dir.exists():
        return []
    base_url = "/uploads"
    files = []
    for path in photo_dir.iterdir():
        if path.is_file():
            files.append(f"{base_url}/user_{user_id}/{path.name}")
    return files
