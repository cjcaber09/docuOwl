"""Turns text into embeddings (lists of 1,024 numbers) with Voyage AI. Similar meaning, similar numbers."""

import time
from collections.abc import Callable
from functools import lru_cache
from typing import Literal, Protocol

import httpx

from app.config import get_settings
from app.models import EMBEDDING_DIMENSIONS

VOYAGE_URL = "https://api.voyageai.com/v1/embeddings"
# 128 chunks of ~500 words is roughly 90K tokens, well under Voyage's 320K-token limit per request.
BATCH_SIZE = 128
RETRY_STATUSES = {429, 500, 502, 503, 504}
RETRY_WAITS = (1, 4, 10)  # seconds to wait before the 2nd, 3rd and 4th try

InputType = Literal["document", "query"]


class EmbeddingError(Exception):
    """Voyage couldn't embed the text, even after retrying. Details are for the server log only."""


class Embedder(Protocol):
    """Anything with a model name and an embed method. Voyage in the app, a fake in tests."""

    model: str

    def embed(self, texts: list[str], input_type: InputType) -> list[list[float]]: ...


class VoyageEmbedder:
    def __init__(
        self,
        api_key: str,
        model: str,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.model = model
        self._client = httpx.Client(headers={"Authorization": f"Bearer {api_key}"}, timeout=60, transport=transport)
        self._sleep = sleep

    def embed(self, texts: list[str], input_type: InputType) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), BATCH_SIZE):
            embeddings.extend(self._embed_batch(texts[start : start + BATCH_SIZE], input_type))
        return embeddings

    def _embed_batch(self, texts: list[str], input_type: InputType) -> list[list[float]]:
        body = {"input": texts, "model": self.model, "input_type": input_type, "output_dimension": EMBEDDING_DIMENSIONS}
        problem = ""
        for wait in (*RETRY_WAITS, None):
            try:
                response = self._client.post(VOYAGE_URL, json=body)
            except httpx.TransportError as error:
                problem = f"network error: {error}"
            else:
                if response.status_code == 200:
                    items = sorted(response.json()["data"], key=lambda item: item["index"])
                    return [item["embedding"] for item in items]
                problem = f"HTTP {response.status_code}"
                if response.status_code not in RETRY_STATUSES:
                    break
            if wait is not None:
                self._sleep(wait)
        raise EmbeddingError(f"Voyage embedding failed: {problem}")


@lru_cache
def get_embedder() -> Embedder:
    """One shared embedder (and connection pool) for the whole app. Tests replace it with a fake."""
    settings = get_settings()
    return VoyageEmbedder(settings.voyage_api_key, settings.embedding_model)
