import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status

from app.auth.csrf import require_same_origin
from app.auth.routes import router as auth_router
from app.chat.routes import router as chat_router
from app.database import SessionLocal, database_is_reachable
from app.documents.routes import reject_oversized_uploads
from app.documents.routes import router as documents_router
from app.startup import check_database, clear_upload_folder, mark_interrupted_documents

logger = logging.getLogger("owl")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts. An error here stops the server with a clear message.
    with SessionLocal() as session:
        check_database(session)
        interrupted = mark_interrupted_documents(session)
    if interrupted:
        logger.warning("Marked %d interrupted document(s) as failed.", interrupted)
    clear_upload_folder()
    yield


app = FastAPI(title="Owl API", lifespan=lifespan)
app.middleware("http")(reject_oversized_uploads)
app.middleware("http")(require_same_origin)  # added last, so it runs first
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(chat_router)


@app.get("/api/health")
def health(response: Response) -> dict[str, str]:
    if database_is_reachable():
        return {"status": "ok"}
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "not ok"}


@app.get("/api/config")
def public_config() -> dict[str, bool]:
    """Which optional features are on, so the frontend can hide Download and Forgot password.

    Both are off until build step 8 adds the storage bucket and email settings.
    """
    return {"storageEnabled": False, "emailEnabled": False}
