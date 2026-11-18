from app.models import Document, User
from app.startup import INTERRUPTED_REASON, check_database, mark_interrupted_documents


def test_check_database_passes_on_a_migrated_database(db):
    check_database(db)  # raises StartupCheckError if something is wrong


def test_processing_documents_are_marked_failed_at_startup(db):
    user = User(email="reader@example.com", password_hash="not-a-real-hash")
    db.add(user)
    db.commit()
    stuck = Document(user_id=user.id, filename="a.pdf", file_type="pdf", content_hash="a" * 64, status="processing")
    finished = Document(user_id=user.id, filename="b.pdf", file_type="pdf", content_hash="b" * 64, status="ready")
    db.add_all([stuck, finished])
    db.commit()

    marked = mark_interrupted_documents(db)

    db.refresh(stuck)
    db.refresh(finished)
    assert marked == 1
    assert stuck.status == "failed"
    assert stuck.failure_reason == INTERRUPTED_REASON
    assert finished.status == "ready"
    assert finished.failure_reason is None
