import hashlib
import json
from abc import ABC, abstractmethod
from typing import Dict, Optional


class BaseEmbedder(ABC):
    name: str = "base"

    @abstractmethod
    def generate_embedding(self, image_bytes: bytes) -> list[float]:
        raise NotImplementedError


class HashedEmbedder(BaseEmbedder):
    """
    Lightweight deterministic embedder. Useful for testing and keeps the interface
    compatible with a real FaceNet implementation that can replace this class later.
    """

    name = "hashed"

    def generate_embedding(self, image_bytes: bytes) -> list[float]:
        digest = hashlib.sha256(image_bytes).digest()
        # Expand digest to a pseudo-vector in [0,1].
        floats = [b / 255 for b in digest]
        # Pad or trim to 128 dims for compatibility with FaceNet-style vectors.
        repeated = (floats * ((128 // len(floats)) + 1))[:128]
        return repeated


class FaceEmbedderRegistry:
    def __init__(self):
        self._registry: Dict[str, BaseEmbedder] = {}
        self._default: Optional[str] = None

    def register(self, name: str, embedder: BaseEmbedder) -> None:
        self._registry[name] = embedder
        if not self._default:
            self._default = name

    def get(self, name: str) -> BaseEmbedder:
        if name not in self._registry:
            raise KeyError(f"Embedder {name} is not registered")
        return self._registry[name]

    def get_default(self) -> BaseEmbedder:
        if not self._default:
            raise KeyError("No embedder registered")
        return self._registry[self._default]
