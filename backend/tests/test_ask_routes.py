import json

from sqlalchemy import select

from app.chat.answering import REFUSED, TROUBLE
from app.chat.claude import AnswerEnd
from app.config import get_settings
from app.models import Usage
from tests.helpers import sign_up, upload

NOTES = b"# Refunds\nWithin 30 days."


def ready_user_with_conversation(client):
    sign_up(client)
    upload(client, "notes.md", NOTES)  # the fake embedder makes it Ready at once
    return client.post("/api/conversations").json()["id"]


def ask(client, conversation_id, content="How long do refunds take?"):
    return client.post(f"/api/conversations/{conversation_id}/messages", json={"content": content})


def events(response):
    return [json.loads(line) for line in response.text.splitlines() if line]


def saved_messages(client, conversation_id):
    return client.get(f"/api/conversations/{conversation_id}").json()["messages"]


def test_answer_streams_with_citations_and_is_saved(client, fake_embedder, fake_chat):
    conversation_id = ready_user_with_conversation(client)

    response = ask(client, conversation_id)

    assert response.headers["content-type"].startswith("application/x-ndjson")
    streamed = events(response)
    assert [event["type"] for event in streamed] == ["text", "text", "citation", "done"]
    assert streamed[2]["citation"] == {
        "filename": "notes.md",
        "location": "Refunds",
        "quote": "Within 30 days.",
        "deleted": False,
    }
    assert streamed[3]["message"]["content"] == "Refunds take 30 days."
    assert streamed[3]["title"] == "Refund policy"
    conversation = client.get(f"/api/conversations/{conversation_id}").json()
    assert conversation["title"] == "Refund policy"
    assert [message["role"] for message in conversation["messages"]] == ["user", "assistant"]


def test_no_ready_documents_means_no_model_call_and_no_count(client, fake_embedder, fake_chat, db):
    sign_up(client)
    conversation_id = client.post("/api/conversations").json()["id"]

    response = ask(client, conversation_id)

    assert response.status_code == 409
    assert response.json() == {"detail": "Upload a document and wait until it's Ready, then ask your question."}
    assert fake_chat.answer_calls == []
    assert db.scalar(select(Usage)) is None


def test_daily_limit(client, fake_embedder, fake_chat, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_questions_per_day", 1)
    conversation_id = ready_user_with_conversation(client)
    ask(client, conversation_id)

    response = ask(client, conversation_id, "Another one?")

    assert response.status_code == 429
    assert response.json() == {"detail": "You've asked 1 questions today. The limit resets at midnight UTC."}


def test_follow_ups_are_rewritten_for_search_and_keep_the_title(client, fake_embedder, fake_chat):
    conversation_id = ready_user_with_conversation(client)
    ask(client, conversation_id, "Refund policy?")
    assert fake_chat.rewrites == []
    fake_chat.title = "Something else"

    ask(client, conversation_id, "And annual plans?")

    assert fake_chat.rewrites == ["And annual plans?"]
    assert fake_embedder.calls[-1] == (["standalone: And annual plans?"], "query")
    history, _, question = fake_chat.answer_calls[-1]
    assert history == [
        {"role": "user", "content": "Refund policy?"},
        {"role": "assistant", "content": "Refunds take 30 days."},
    ]
    assert question == "And annual plans?"
    assert client.get(f"/api/conversations/{conversation_id}").json()["title"] == "Refund policy"


def test_refused_answer_is_not_saved(client, fake_embedder, fake_chat):
    conversation_id = ready_user_with_conversation(client)
    fake_chat.answer_events = fake_chat.answer_events[:2] + [AnswerEnd(refused=True)]

    streamed = events(ask(client, conversation_id))

    assert streamed[-1] == {"type": "error", "message": REFUSED}
    assert [message["role"] for message in saved_messages(client, conversation_id)] == ["user"]


def test_failure_midway_saves_nothing_for_the_answer(client, fake_embedder, fake_chat):
    conversation_id = ready_user_with_conversation(client)
    fake_chat.fail_midway = True

    streamed = events(ask(client, conversation_id))

    assert [event["type"] for event in streamed] == ["text", "text", "citation", "error"]
    assert streamed[-1]["message"] == TROUBLE
    assert [message["role"] for message in saved_messages(client, conversation_id)] == ["user"]


def test_retry_reuses_the_unanswered_question(client, fake_embedder, fake_chat):
    conversation_id = ready_user_with_conversation(client)
    fake_chat.fail_midway = True
    ask(client, conversation_id)
    fake_chat.fail_midway = False

    ask(client, conversation_id)

    assert [message["role"] for message in saved_messages(client, conversation_id)] == ["user", "assistant"]


def test_voyage_trouble_before_answering(client, fake_embedder, fake_chat):
    conversation_id = ready_user_with_conversation(client)
    fake_embedder.fail = True

    response = ask(client, conversation_id)

    assert response.status_code == 503
    assert response.json() == {"detail": TROUBLE}


def test_cannot_ask_in_someone_elses_conversation(client, fake_embedder, fake_chat):
    conversation_id = ready_user_with_conversation(client)
    client.cookies.clear()
    sign_up(client, "b@example.com")
    upload(client, "notes.md", NOTES)

    assert ask(client, conversation_id).status_code == 404
