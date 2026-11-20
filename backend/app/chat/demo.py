"""Demo mode: free answers that quote the best-matching passage instead of asking Claude."""

from collections.abc import Iterator

from app.chat.claude import DEFAULT_TITLE, NOT_FOUND_REPLY, AnswerEnd, AnswerEvent, CitedPassage, TextChunk
from app.chat.retrieval import Passage

TITLE_WORDS = 6


class DemoChatModel:
    """Fits the same ChatModel interface as Claude, so the rest of Owl can't tell the difference."""

    def stream_answer(
        self, history: list[dict[str, str]], passages: list[Passage], question: str
    ) -> Iterator[AnswerEvent]:
        if not passages:
            yield TextChunk(NOT_FOUND_REPLY)
        else:
            best = passages[0]  # passages arrive closest first
            words = f'From {best.filename} ({best.location}):\n"{best.text}"'.split(" ")
            # Word by word, so the page streams just as it does with Claude.
            for index, word in enumerate(words):
                yield TextChunk(word if index == len(words) - 1 else word + " ")
            yield CitedPassage(0, best.text)
        yield AnswerEnd(refused=False)

    def rewrite_question(self, history: list[dict[str, str]], question: str) -> str:
        return question  # no model to rewrite with: search uses the words as typed

    def make_title(self, question: str, answer: str) -> str:
        words = question.split()
        title = " ".join(words[:TITLE_WORDS]) + ("…" if len(words) > TITLE_WORDS else "")
        return title or DEFAULT_TITLE
