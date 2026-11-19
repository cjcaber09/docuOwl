import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, DbSession
from app.config import get_settings
from app.documents.embeddings import Embedder, get_embedder
from app.documents.processing import process_document
from app.documents.schemas import DocumentOut
from app.documents.validation import (
    UploadRejected,
    check_contents,
    clean_filename,
    file_type_from_name,
    save_upload,
    too_large_message,
)
from app.models import Document

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Room for the form's own bytes around the file (boundaries, field names).
MULTIPART_OVERHEAD_BYTES = 64 * 1024


async def reject_oversized_uploads(request: Request, call_next):
    """Refuses a huge upload from its declared size, before FastAPI copies it to disk."""
    if request.method == "POST" and request.url.path == "/api/documents":
        max_mb = get_settings().max_upload_mb
        declared = request.headers.get("content-length", "")
        if declared.isdigit() and int(declared) > max_mb * 1024 * 1024 + MULTIPART_OVERHEAD_BYTES:
            return JSONResponse({"detail": too_large_message(max_mb)}, status_code=status.HTTP_413_CONTENT_TOO_LARGE)
    return await call_next(request)


@router.get("")
def list_documents(user: CurrentUser, db: DbSession) -> list[DocumentOut]:
    documents = db.scalars(
        select(Document).where(Document.user_id == user.id).order_by(Document.created_at.desc())
    )
    return [DocumentOut.model_validate(document) for document in documents]


@router.post("", status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile,
    user: CurrentUser,
    db: DbSession,
    background: BackgroundTasks,
    embedder: Annotated[Embedder, Depends(get_embedder)],
) -> DocumentOut:
    settings = get_settings()
    filename = clean_filename(file.filename)
    try:
        file_type = file_type_from_name(filename)
        saved = save_upload(file.file, settings.max_upload_mb)
    except UploadRejected as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error))

    try:
        check_contents(saved.path, file_type)
        document = create_document_row(
            db, user.id, filename, file_type, saved.content_hash, settings.max_documents_per_user
        )
    except UploadRejected as error:
        saved.path.unlink(missing_ok=True)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error))
    except Exception:
        saved.path.unlink(missing_ok=True)
        raise

    # Runs after the response is sent; the browser polls the list to see it finish.
    background.add_task(process_document, document.id, saved.path, embedder)
    return DocumentOut.model_validate(document)


def create_document_row(
    db: Session, user_id: uuid.UUID, filename: str, file_type: str, content_hash: str, max_documents: int
) -> Document:
    """Applies the duplicate and limit rules, then saves the new row, all in one transaction."""
    existing = db.scalar(select(Document).where(Document.user_id == user_id, Document.content_hash == content_hash))
    if existing is not None:
        if existing.status == "ready":
            raise HTTPException(status.HTTP_409_CONFLICT, f"You already uploaded this file as '{existing.filename}'.")
        if existing.status == "processing":
            raise HTTPException(status.HTTP_409_CONFLICT, "This file is still being processed.")
        db.delete(existing)  # a failed copy is replaced by the new upload
        db.flush()  # send the DELETE now, before the INSERT below needs the same hash

    count = db.scalar(select(func.count()).select_from(Document).where(Document.user_id == user_id))
    if count >= max_documents:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"You've reached the limit of {max_documents} documents. Delete one to upload more.",
        )

    document = Document(
        user_id=user_id, filename=filename, file_type=file_type, content_hash=content_hash, status="processing"
    )
    db.add(document)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()  # the same file arrived twice at the same moment
        raise HTTPException(status.HTTP_409_CONFLICT, "This file is still being processed.")
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: uuid.UUID, user: CurrentUser, db: DbSession) -> None:
    # Filtering by user_id too means another user's document looks exactly like a missing one.
    result = db.execute(delete(Document).where(Document.id == document_id, Document.user_id == user.id))
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found.")
