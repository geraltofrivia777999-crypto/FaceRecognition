import json
from typing import Iterable, List

from sqlalchemy.orm import Session

from backend.app import models


def add_embedding(db: Session, user_id: int, vector: list[float], model_name: str) -> models.Embedding:
    serialized = json.dumps(vector)
    embedding = models.Embedding(user_id=user_id, vector=serialized, model_name=model_name)
    db.add(embedding)
    db.commit()
    db.refresh(embedding)
    return embedding


def get_embeddings_for_user(db: Session, user_id: int) -> list[models.Embedding]:
    return db.query(models.Embedding).filter(models.Embedding.user_id == user_id).all()


def get_all_embeddings(db: Session) -> list[models.Embedding]:
    return db.query(models.Embedding).all()


def remove_embeddings(db: Session, embedding_ids: Iterable[int]) -> None:
    db.query(models.Embedding).filter(models.Embedding.id.in_(embedding_ids)).delete(synchronize_session=False)
    db.commit()
