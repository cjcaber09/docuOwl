import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, DbSession
from app.chat.answering import TROUBLE, recent_history, save_question, stream_answer
from app.chat.claude import ChatModel, get_chat_model
from app.chat.retrieval import find_passages, has_ready_documents
from app.chat.schemas import ConversationOut, ConversationSummary, QuestionIn, message_out
from app.chat.usage import use_one_question
from app.config import get_settings
from app.documents.embeddings import Embedder, EmbeddingError, get_embedder
from app.models import Conversation, Document, Message

logger = logging.getLogger("owl.chat")

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

NOT_FOUND = "Conversation not found."
NO_DOCUMENTS = "Upload a document and wait until it's Ready, then ask your question."

ChatModelDep = Annotated[ChatModel, Depends(get_chat_model)]
EmbedderDep = Annotated[Embedder, Depends(get_embedder)]


def own_conversation(db: Session, user_id: uuid.UUID, conversation_id: uuid.UUID) -> Conversation:
    """The user's conversation, or 404. Someone else's looks exactly like a missing one."""
    conversation = db.scalar(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id)
    )
    if conversation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)
    return conversation


@router.get("")
def list_conversations(user: CurrentUser, db: DbSession) -> list[ConversationSummary]:
    conversations = db.scalars(
        select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.updated_at.desc())
    )
    return [ConversationSummary.model_validate(conversation) for conversation in conversations]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_conversation(user: CurrentUser, db: DbSession) -> ConversationSummary:
    conversation = Conversation(user_id=user.id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return ConversationSummary.model_validate(conversation)


@router.get("/{conversation_id}")
def get_conversation(conversation_id: uuid.UUID, user: CurrentUser, db: DbSession) -> ConversationOut:
    conversation = own_conversation(db, user.id, conversation_id)
    messages = db.scalars(
        select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at)
    ).all()
    # One query to learn which cited files still exist; the rest show as "(deleted)".
    cited = {uuid.UUID(snapshot["documentId"]) for message in messages for snapshot in message.citations}
    existing: set[str] = set()
    if cited:
        existing = {
            str(document_id)
            for document_id in db.scalars(
                select(Document.id).where(Document.user_id == user.id, Document.id.in_(cited))
            )
        }
    return ConversationOut(
        id=conversation.id,
        title=conversation.title,
        messages=[message_out(message, existing) for message in messages],
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: uuid.UUID, user: CurrentUser, db: DbSession) -> None:
    result = db.execute(
        delete(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)


@router.post("/{conversation_id}/messages")
def ask_question(
    conversation_id: uuid.UUID,
    body: QuestionIn,
    user: CurrentUser,
    db: DbSession,
    chat: ChatModelDep,
    embedder: EmbedderDep,
) -> StreamingResponse:
    # Everything that can fail with a plain HTTP error happens before the stream starts.
    conversation = own_conversation(db, user.id, conversation_id)
    if not has_ready_documents(db, user.id):
        raise HTTPException(status.HTTP_409_CONFLICT, NO_DOCUMENTS)
    limit = get_settings().max_questions_per_day
    if not use_one_question(db, user.id, limit):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"You've asked {limit} questions today. The limit resets at midnight UTC.",
        )

    question = save_question(db, conversation, body.content)
    history = recent_history(db, conversation.id, question)
    search_text = chat.rewrite_question(history, body.content) if history else body.content
    try:
        [query_embedding] = embedder.embed([search_text], input_type="query")
    except EmbeddingError:
        logger.exception("Embedding the question failed")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, TROUBLE)
    passages = find_passages(db, user.id, query_embedding)
    first_answer = all(message["role"] != "assistant" for message in history)

    return StreamingResponse(
        stream_answer(chat, conversation.id, user.id, history, passages, body.content, first_answer),
        media_type="application/x-ndjson",
    )
