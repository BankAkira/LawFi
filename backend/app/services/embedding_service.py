from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel

from app.config import settings


class EmbeddingService:
    """Generate text embeddings using Google Vertex AI."""

    def __init__(self):
        aiplatform.init(
            project=settings.gcp_project_id,
            location=settings.gcp_location,
        )
        self.model = TextEmbeddingModel.from_pretrained(settings.embedding_model)

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        embeddings = self.model.get_embeddings([text])
        return embeddings[0].values

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts (max 250 per call)."""
        all_embeddings = []
        batch_size = 250
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = self.model.get_embeddings(batch)
            all_embeddings.extend([e.values for e in embeddings])
        return all_embeddings
