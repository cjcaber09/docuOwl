import hashlib
import uuid

from sqlalchemy import func, select

from app.config import get_settings
from app.models import Chunk, Document, User
from tests.sample_files import make_pdf

NOTES = b"# Refunds\nWithin 30 days."


def sign_up(client, email="reader@example.com"):
    client.post("/api/auth/signup", json={"email": email, "password": "correct horse battery"})


def upload(client, filename, content):
    return client.post("/api/documents", files={"file": (filename, content)})


def test_upload_is_processed_and_listed(client, fake_embedder):
    sign_up(client)

    response = upload(client, "notes.md", NOTES)

    assert response.status_code == 201
    assert response.json()["status"] == "processing"
    listed = client.get("/api/documents").json()
    assert set(listed[0]) == {"id", "filename", "fileType", "status", "failureReason", "pageCount", "createdAt"}
    assert listed[0]["filename"] == "notes.md"
    assert listed[0]["fileType"] == "md"
    assert listed[0]["status"] == "ready"
    assert listed[0]["failureReason"] is None


def test_pdf_upload_records_its_page_count(client, fake_embedder):
    sign_up(client)

    upload(client, "report.pdf", make_pdf(["Page one.", "Page two."]))

    assert client.get("/api/documents").json()[0]["pageCount"] == 2


def test_upload_needs_a_login(client, fake_embedder):
    assert upload(client, "notes.md", NOTES).status_code == 401


def test_unsupported_type_is_rejected(client, fake_embedder):
    sign_up(client)

    response = upload(client, "setup.exe", b"MZ program")

    assert response.status_code == 400
    assert response.json() == {"detail": "Owl accepts PDF, DOCX, TXT and MD files."}


def test_fake_pdf_is_rejected_and_not_listed(client, fake_embedder):
    sign_up(client)

    response = upload(client, "report.pdf", b"not really a pdf")

    assert response.json() == {"detail": "This file isn't a valid PDF."}
    assert client.get("/api/documents").json() == []


def test_file_over_the_size_limit_is_rejected(client, fake_embedder, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_upload_mb", 1)
    sign_up(client)

    response = upload(client, "big.txt", b"x" * (1024 * 1024 + 1))

    assert response.status_code == 400
    assert response.json() == {"detail": "Files can be at most 1 MB."}


def test_huge_upload_is_stopped_before_it_is_read(client, fake_embedder, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_upload_mb", 1)
    sign_up(client)

    response = upload(client, "huge.txt", b"x" * (2 * 1024 * 1024))

    assert response.status_code == 413
    assert response.json() == {"detail": "Files can be at most 1 MB."}


def test_same_file_twice_is_refused(client, fake_embedder):
    sign_up(client)
    upload(client, "notes.md", NOTES)

    response = upload(client, "copy-of-notes.md", NOTES)

    assert response.status_code == 409
    assert response.json() == {"detail": "You already uploaded this file as 'notes.md'."}


def test_same_file_while_still_processing_is_refused(client, fake_embedder, db):
    sign_up(client)
    user = db.scalar(select(User))
    db.add(
        Document(
            user_id=user.id,
            filename="notes.md",
            file_type="md",
            content_hash=hashlib.sha256(NOTES).hexdigest(),
            status="processing",
        )
    )
    db.commit()

    response = upload(client, "notes.md", NOTES)

    assert response.status_code == 409
    assert response.json() == {"detail": "This file is still being processed."}


def test_failed_copy_is_replaced_by_a_new_upload(client, fake_embedder):
    sign_up(client)
    fake_embedder.fail = True
    upload(client, "notes.md", NOTES)
    assert client.get("/api/documents").json()[0]["status"] == "failed"
    fake_embedder.fail = False

    response = upload(client, "notes.md", NOTES)

    assert response.status_code == 201
    assert [document["status"] for document in client.get("/api/documents").json()] == ["ready"]


def test_document_limit_per_user(client, fake_embedder, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_documents_per_user", 2)
    sign_up(client)
    upload(client, "a.md", b"first")
    upload(client, "b.md", b"second")

    response = upload(client, "c.md", b"third")

    assert response.status_code == 409
    assert response.json() == {"detail": "You've reached the limit of 2 documents. Delete one to upload more."}


def test_users_never_see_or_delete_each_others_documents(client, fake_embedder, db):
    sign_up(client, "a@example.com")
    document_id = upload(client, "a.md", NOTES).json()["id"]
    client.cookies.clear()
    sign_up(client, "b@example.com")

    assert client.get("/api/documents").json() == []
    assert client.delete(f"/api/documents/{document_id}").status_code == 404
    assert db.get(Document, uuid.UUID(document_id)) is not None


def test_two_users_may_upload_the_same_file(client, fake_embedder):
    sign_up(client, "a@example.com")
    upload(client, "notes.md", NOTES)
    client.cookies.clear()
    sign_up(client, "b@example.com")

    assert upload(client, "notes.md", NOTES).status_code == 201


def test_delete_removes_the_document_and_its_chunks(client, fake_embedder, db):
    sign_up(client)
    document_id = upload(client, "notes.md", NOTES).json()["id"]
    assert db.scalar(select(func.count()).select_from(Chunk)) > 0

    assert client.delete(f"/api/documents/{document_id}").status_code == 204

    assert client.get("/api/documents").json() == []
    assert db.scalar(select(func.count()).select_from(Chunk)) == 0
