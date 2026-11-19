"""Stand-ins for paid services, so tests need no network and cost nothing."""

from app.documents.embeddings import EmbeddingError
from app.models import EMBEDDING_DIMENSIONS


class FakeEmbedder:
    model = "fake-embedder"

    def __init__(self) -> None:
        self.calls: list[tuple[list[str], str]] = []
        self.fail = False

    def embed(self, texts: list[str], input_type: str) -> list[list[float]]:
        self.calls.append((list(texts), input_type))
        if self.fail:
            raise EmbeddingError("Voyage embedding failed: HTTP 503")
        return [[0.0] * (EMBEDDING_DIMENSIONS - 1) + [1.0] for _ in texts]
