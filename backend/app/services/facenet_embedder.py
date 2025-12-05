import io
import logging
from typing import Optional

import torch
from facenet_pytorch import InceptionResnetV1, fixed_image_standardization
from PIL import Image
from torchvision import transforms

from backend.app.services.model_registry import BaseEmbedder

logger = logging.getLogger(__name__)


class FaceNetEmbedder(BaseEmbedder):
    """
    Face embedding generator based on facenet-pytorch (InceptionResnetV1).
    Returns 512-dim vectors compatible with FaceNet pipelines.
    """

    name = "facenet"

    def __init__(self, device: Optional[str] = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = (
            InceptionResnetV1(pretrained="vggface2")
            .eval()
            .to(self.device)
        )
        self.transform = transforms.Compose(
            [
                transforms.Resize((160, 160)),
                transforms.ToTensor(),
                fixed_image_standardization,
            ]
        )
        logger.info("FaceNetEmbedder initialized on device=%s", self.device)

    def _preprocess(self, image_bytes: bytes) -> torch.Tensor:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = self.transform(img).unsqueeze(0).to(self.device)
        return tensor

    def generate_embedding(self, image_bytes: bytes) -> list[float]:
        with torch.inference_mode():
            tensor = self._preprocess(image_bytes)
            embedding = self.model(tensor)
        return embedding.squeeze(0).cpu().tolist()
