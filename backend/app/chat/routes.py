import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, DbSession
from app.chat.schemas import ConversationOut, ConversationSummary, message_out
from app.models import Conversation, Document, Message

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

NOT_FOUND = "Conversation not found."


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
