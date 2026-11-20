"""Stand-ins for paid services, so tests need no network and cost nothing."""

import anthropic

from app.chat.claude import AnswerEnd, CitedPassage, TextChunk
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


class FakeChatModel:
    """Stands in for Claude: a scripted answer that cites passage 0, and recorded calls."""

    def __init__(self) -> None:
        self.answer_events = [
            TextChunk("Refunds take "),
            TextChunk("30 days."),
            CitedPassage(0, "Within 30 days."),
            AnswerEnd(refused=False),
        ]
        self.fail_midway = False
        self.title = "Refund policy"
        self.rewrites: list[str] = []
        self.answer_calls: list[tuple[list[dict[str, str]], list, str]] = []

    def stream_answer(self, history, passages, question):
        self.answer_calls.append((history, passages, question))
        for event in self.answer_events:
            if self.fail_midway and isinstance(event, AnswerEnd):
                raise anthropic.APIConnectionError(request=None)
            yield event

    def rewrite_question(self, history, question):
        self.rewrites.append(question)
        return f"standalone: {question}"

    def make_title(self, question, answer):
        return self.title
