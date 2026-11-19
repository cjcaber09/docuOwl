import uuid

from sqlalchemy import delete, select

from app.database import SessionLocal
from app.documents.processing import EMBEDDING_FAILED, process_document
from app.models import Chunk, Document, User
from tests.fakes import FakeEmbedder
from tests.sample_files import make_pdf


def make_document(db, tmp_path, file_type: str, content: bytes):
    user = User(email="reader@example.com", password_hash="not-a-real-hash")
    db.add(user)
    db.commit()
    document = Document(
        user_id=user.id, filename=f"file.{file_type}", file_type=file_type, content_hash="a" * 64, status="processing"
    )
    db.add(document)
    db.commit()
    path = tmp_path / "upload"
    path.write_bytes(content)
    return document, path


def chunks_of(db, document_id):
    return db.scalars(select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.position)).all()


def test_pdf_becomes_ready_with_one_chunk_per_page(db, tmp_path):
    document, path = make_document(db, tmp_path, "pdf", make_pdf(["Refunds take 30 days.", "Annual plans are pro rata."]))
    embedder = FakeEmbedder()

    process_document(document.id, path, embedder)

    db.refresh(document)
    chunks = chunks_of(db, document.id)
    assert document.status == "ready"
    assert document.page_count == 2
    assert [(chunk.position, chunk.page_number) for chunk in chunks] == [(0, 1), (1, 2)]
    assert all(chunk.user_id == document.user_id for chunk in chunks)
    assert all(chunk.embedding_model == "fake-embedder" for chunk in chunks)
    assert embedder.calls[0][1] == "document"
    assert not path.exists()


def test_markdown_chunks_keep_their_headings(db, tmp_path):
    document, path = make_document(db, tmp_path, "md", b"# Refunds\nWithin 30 days.\n# Annual\nPro rata.")

    process_document(document.id, path, FakeEmbedder())

    assert [chunk.heading for chunk in chunks_of(db, document.id)] == ["Refunds", "Annual"]


def test_scanned_pdf_fails_with_a_reason(db, tmp_path):
    document, path = make_document(db, tmp_path, "pdf", make_pdf([""]))

    process_document(document.id, path, FakeEmbedder())

    db.refresh(document)
    assert document.status == "failed"
    assert document.failure_reason == "No text found, scanned PDFs aren't supported yet."
    assert chunks_of(db, document.id) == []
    assert not path.exists()


def test_voyage_trouble_fails_with_a_friendly_reason(db, tmp_path):
    document, path = make_document(db, tmp_path, "txt", b"Some notes.")
    embedder = FakeEmbedder()
    embedder.fail = True

    process_document(document.id, path, embedder)

    db.refresh(document)
    assert document.status == "failed"
    assert document.failure_reason == EMBEDDING_FAILED
    assert chunks_of(db, document.id) == []


def test_document_deleted_during_processing_is_left_alone(db, tmp_path):
    document, path = make_document(db, tmp_path, "txt", b"Some notes.")

    class DeleteWhileEmbedding(FakeEmbedder):
        def embed(self, texts, input_type):
            with SessionLocal() as session:
                session.execute(delete(Document).where(Document.id == document.id))
                session.commit()
            return super().embed(texts, input_type)

    process_document(document.id, path, DeleteWhileEmbedding())  # no error

    # A fresh query, not db.get: db.get would return the copy this session already holds in memory.
    assert db.scalar(select(Document).where(Document.id == document.id)) is None
    assert chunks_of(db, document.id) == []
    assert not path.exists()


def test_document_deleted_before_processing_skips_all_work(tmp_path):
    path = tmp_path / "upload"
    path.write_bytes(b"Some notes.")
    embedder = FakeEmbedder()

    process_document(uuid.uuid4(), path, embedder)

    assert embedder.calls == []
    assert not path.exists()
