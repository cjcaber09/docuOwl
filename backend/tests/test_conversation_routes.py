import uuid

from sqlalchemy import select

from app.models import Conversation, Document, Message, User
from tests.helpers import sign_up


def create_conversation(client):
    return client.post("/api/conversations").json()


def test_new_conversation_is_listed(client):
    sign_up(client)

    created = client.post("/api/conversations")

    assert created.status_code == 201
    assert set(created.json()) == {"id", "title", "updatedAt"}
    assert created.json()["title"] == "New conversation"
    assert client.get("/api/conversations").json() == [created.json()]


def test_new_conversation_has_no_messages(client):
    sign_up(client)
    conversation = create_conversation(client)

    response = client.get(f"/api/conversations/{conversation['id']}")

    assert response.json() == {"id": conversation["id"], "title": "New conversation", "messages": []}


def test_citations_of_deleted_files_are_marked(client, db):
    sign_up(client)
    conversation = create_conversation(client)
    user = db.scalar(select(User))
    kept = Document(user_id=user.id, filename="terms.pdf", file_type="pdf", content_hash="a" * 64, status="ready")
    db.add(kept)
    db.commit()
    conversation_id = uuid.UUID(conversation["id"])
    db.add(Message(conversation_id=conversation_id, user_id=user.id, role="user", content="Refunds?"))
    db.commit()
    db.add(
        Message(
            conversation_id=conversation_id,
            user_id=user.id,
            role="assistant",
            content="30 days.",
            citations=[
                {"documentId": str(kept.id), "filename": "terms.pdf", "location": "p. 4", "quote": "30 days"},
                {"documentId": str(uuid.uuid4()), "filename": "old.docx", "location": "Refunds", "quote": "pro rata"},
            ],
        )
    )
    db.commit()

    messages = client.get(f"/api/conversations/{conversation['id']}").json()["messages"]

    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert set(messages[1]) == {"id", "role", "content", "citations", "createdAt"}
    assert messages[1]["citations"] == [
        {"filename": "terms.pdf", "location": "p. 4", "quote": "30 days", "deleted": False},
        {"filename": "old.docx", "location": "Refunds", "quote": "pro rata", "deleted": True},
    ]


def test_conversations_are_listed_newest_first(client):
    sign_up(client)
    first = create_conversation(client)
    second = create_conversation(client)

    listed = client.get("/api/conversations").json()

    assert [conversation["id"] for conversation in listed] == [second["id"], first["id"]]


def test_users_never_see_or_delete_each_others_conversations(client, db):
    sign_up(client, "a@example.com")
    conversation = create_conversation(client)
    client.cookies.clear()
    sign_up(client, "b@example.com")

    assert client.get("/api/conversations").json() == []
    assert client.get(f"/api/conversations/{conversation['id']}").status_code == 404
    assert client.delete(f"/api/conversations/{conversation['id']}").status_code == 404
    assert db.get(Conversation, uuid.UUID(conversation["id"])) is not None


def test_delete_removes_the_conversation_and_its_messages(client, db):
    sign_up(client)
    conversation = create_conversation(client)
    user = db.scalar(select(User))
    db.add(Message(conversation_id=uuid.UUID(conversation["id"]), user_id=user.id, role="user", content="Hi"))
    db.commit()

    assert client.delete(f"/api/conversations/{conversation['id']}").status_code == 204

    assert client.get("/api/conversations").json() == []
    assert db.scalar(select(Message)) is None
