"""Answering one question: saving it, the conversation history, and the streamed answer."""

import json
import logging
import uuid
from collections.abc import Iterator

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.chat.claude import AnswerEnd, ChatModel, CitedPassage, TextChunk
from app.chat.retrieval import Passage
from app.chat.schemas import CitationOut, message_out
from app.database import SessionLocal
from app.models import Conversation, Message

logger = logging.getLogger("owl.chat")

HISTORY_LIMIT = 10
TROUBLE = "Owl is having trouble right now, please try again."
REFUSED = "Owl couldn't answer that one, try rephrasing."


def save_question(db: Session, conversation: Conversation, content: str) -> Message:
    """Saves the question. A Retry of a question that never got an answer reuses it instead."""
    last = db.scalar(
        select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at.desc()).limit(1)
    )
    if last is not None and last.role == "user" and last.content == content:
        return last
    question = Message(conversation_id=conversation.id, user_id=conversation.user_id, role="user", content=content)
    db.add(question)
    conversation.updated_at = func.now()
    db.commit()
    return question


def recent_history(db: Session, conversation_id: uuid.UUID, question: Message) -> list[dict[str, str]]:
    """The last 10 messages before the question, oldest first, starting with a user message."""
    earlier = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id, Message.created_at < question.created_at)
        .order_by(Message.created_at.desc())
        .limit(HISTORY_LIMIT)
    ).all()
    history = [{"role": message.role, "content": message.content} for message in reversed(earlier)]
    while history and history[0]["role"] == "assistant":
        history.pop(0)
    return history


def event_line(event: dict) -> str:
    return json.dumps(event) + "\n"


def stream_answer(
    chat: ChatModel,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    history: list[dict[str, str]],
    passages: list[Passage],
    question: str,
    first_answer: bool,
) -> Iterator[str]:
    """Yields one JSON line per event. The answer is saved only once it is complete."""
    parts: list[str] = []
    citations: list[dict[str, str]] = []
    refused = False
    try:
        for event in chat.stream_answer(history, passages, question):
            if isinstance(event, TextChunk):
                parts.append(event.text)
                yield event_line({"type": "text", "text": event.text})
            elif isinstance(event, CitedPassage) and 0 <= event.passage_index < len(passages):
                passage = passages[event.passage_index]
                snapshot = {
                    "documentId": str(passage.document_id),
                    "filename": passage.filename,
                    "location": passage.location,
                    "quote": event.quote,
                }
                if snapshot not in citations:
                    citations.append(snapshot)
                    public = CitationOut(filename=passage.filename, location=passage.location, quote=event.quote)
                    yield event_line({"type": "citation", "citation": public.model_dump()})
            elif isinstance(event, AnswerEnd):
                refused = event.refused
    except Exception:
        logger.exception("Answer failed for conversation %s", conversation_id)
        yield event_line({"type": "error", "message": TROUBLE})
        return

    if refused:
        yield event_line({"type": "error", "message": REFUSED})
        return

    answer = "".join(parts)
    title = chat.make_title(question, answer) if first_answer else None
    saved = save_answer(conversation_id, user_id, answer, citations, title)
    yield event_line({"type": "done", "message": saved, "title": title})


def save_answer(
    conversation_id: uuid.UUID, user_id: uuid.UUID, content: str, citations: list[dict[str, str]], title: str | None
) -> dict | None:
    # Its own session: the request's session is already closed while the response streams.
    with SessionLocal() as session:
        conversation = session.get(Conversation, conversation_id)
        if conversation is None:
            return None  # deleted while the answer was streaming
        message = Message(
            conversation_id=conversation_id, user_id=user_id, role="assistant", content=content, citations=citations
        )
        session.add(message)
        conversation.updated_at = func.now()
        if title:
            conversation.title = title[:200]
        session.commit()
        cited = {snapshot["documentId"] for snapshot in citations}
        return message_out(message, cited).model_dump(mode="json")
