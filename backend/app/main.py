import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status

from app.database import SessionLocal, database_is_reachable
from app.startup import check_database, mark_interrupted_documents

logger = logging.getLogger("owl")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts. An error here stops the server with a clear message.
    with SessionLocal() as session:
        check_database(session)
        interrupted = mark_interrupted_documents(session)
    if interrupted:
        logger.warning("Marked %d interrupted document(s) as failed.", interrupted)
    yield


app = FastAPI(title="Owl API", lifespan=lifespan)


@app.get("/api/health")
def health(response: Response) -> dict[str, str]:
    if database_is_reachable():
        return {"status": "ok"}
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "not ok"}
