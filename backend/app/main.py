from fastapi import FastAPI, Response, status

from app.database import database_is_reachable

app = FastAPI(title="Owl API")


@app.get("/api/health")
def health(response: Response) -> dict[str, str]:
    if database_is_reachable():
        return {"status": "ok"}
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "not ok"}
