import uuid

from app.chat.retrieval import find_passages, has_ready_documents, location_label
from app.models import EMBEDDING_DIMENSIONS, Chunk, Document
from tests.helpers import make_user


def unit(index: int) -> list[float]:
    """A vector pointing in one direction only, so distances in the tests are easy to predict."""
    vector = [0.0] * EMBEDDING_DIMENSIONS
    vector[index] = 1.0
    return vector


def add_document(db, user, status="ready", filename="notes.md"):
    document = Document(
        user_id=user.id, filename=filename, file_type="md", content_hash=uuid.uuid4().hex * 2, status=status
    )
    db.add(document)
    db.commit()
    return document


def add_chunk(db, document, text, direction, position=0, page_number=None, heading=None):
    db.add(
        Chunk(
            user_id=document.user_id,
            document_id=document.id,
            text=text,
            page_number=page_number,
            heading=heading,
            position=position,
            embedding=unit(direction),
            embedding_model="test",
        )
    )
    db.commit()


def test_closest_chunks_come_first(db):
    user = make_user(db)
    document = add_document(db, user)
    for position, text in enumerate(["zero", "one", "two"]):
        add_chunk(db, document, text, direction=position, position=position)

    passages = find_passages(db, user.id, unit(1), limit=2)

    assert len(passages) == 2
    assert passages[0].text == "one"
    assert passages[0].filename == "notes.md"
    assert passages[0].location == "part 2 of 3"


def test_only_the_users_own_ready_documents_are_searched(db):
    user = make_user(db)
    stranger = make_user(db, "stranger@example.com")
    add_chunk(db, add_document(db, stranger), "theirs", direction=1)
    add_chunk(db, add_document(db, user, status="processing"), "unfinished", direction=1)
    add_chunk(db, add_document(db, user), "mine", direction=5)

    passages = find_passages(db, user.id, unit(1))

    assert [passage.text for passage in passages] == ["mine"]


def test_location_labels():
    assert location_label(page_number=4, heading=None, position=0, chunk_count=1) == "p. 4"
    assert location_label(page_number=None, heading="Refunds", position=0, chunk_count=1) == "Refunds"
    assert location_label(page_number=None, heading=None, position=2, chunk_count=12) == "part 3 of 12"


def test_has_ready_documents(db):
    user = make_user(db)
    add_document(db, user, status="processing")

    assert has_ready_documents(db, user.id) is False

    add_document(db, user, status="ready")

    assert has_ready_documents(db, user.id) is True
