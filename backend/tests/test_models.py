import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.database import tables_without_row_level_security
from app.models import EMBEDDING_DIMENSIONS, Chunk, Conversation, Document, Message, User


def make_user(db, email="reader@example.com"):
    user = User(email=email, password_hash="not-a-real-hash")
    db.add(user)
    db.commit()
    return user


def make_document(db, user, content_hash="a" * 64, status="ready"):
    document = Document(
        user_id=user.id,
        filename="notes.md",
        file_type="md",
        content_hash=content_hash,
        status=status,
    )
    db.add(document)
    db.commit()
    return document


def count(db, model):
    return db.scalar(select(func.count()).select_from(model))


def test_same_user_cannot_upload_the_same_file_twice(db):
    user = make_user(db)
    make_document(db, user)

    with pytest.raises(IntegrityError):
        make_document(db, user)


def test_different_users_can_upload_the_same_file(db):
    make_document(db, make_user(db, "one@example.com"))
    make_document(db, make_user(db, "two@example.com"))

    assert count(db, Document) == 2


def test_document_status_must_be_a_known_value(db):
    with pytest.raises(IntegrityError):
        make_document(db, make_user(db), status="almost-done")


def test_deleting_a_document_deletes_its_chunks(db):
    user = make_user(db)
    document = make_document(db, user)
    db.add(
        Chunk(
            user_id=user.id,
            document_id=document.id,
            text="Owls can rotate their heads 270 degrees.",
            position=0,
            embedding=[0.1] * EMBEDDING_DIMENSIONS,
            embedding_model="test-model",
        )
    )
    db.commit()

    db.delete(document)
    db.commit()

    assert count(db, Chunk) == 0


def test_deleting_a_conversation_deletes_its_messages(db):
    user = make_user(db)
    conversation = Conversation(user_id=user.id)
    db.add(conversation)
    db.commit()
    db.add(Message(conversation_id=conversation.id, user_id=user.id, role="user", content="Hi"))
    db.commit()

    db.delete(conversation)
    db.commit()

    assert count(db, Message) == 0


def test_deleting_a_user_deletes_everything_they_own(db):
    user = make_user(db)
    make_document(db, user)
    db.add(Conversation(user_id=user.id))
    db.commit()

    db.delete(user)
    db.commit()

    assert count(db, Document) == 0
    assert count(db, Conversation) == 0


def test_new_conversation_has_a_default_title(db):
    conversation = Conversation(user_id=make_user(db).id)
    db.add(conversation)
    db.commit()

    assert conversation.title == "New conversation"


def test_every_table_has_row_level_security(db):
    assert tables_without_row_level_security(db) == []
