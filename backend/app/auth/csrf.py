from fastapi import Request
from fastapi.responses import JSONResponse

from app.config import get_settings

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


async def require_same_origin(request: Request, call_next):
    """Block changes (POST, DELETE, ...) unless the browser says the request came from Owl's own page.

    Browsers add the Origin header themselves and pages can't fake it, so another website
    can't make a logged-in user's browser upload, delete or chat on their behalf.
    """
    if request.method not in SAFE_METHODS and request.headers.get("origin") != get_settings().frontend_url:
        return JSONResponse({"detail": "Request blocked: it didn't come from Owl."}, status_code=403)
    return await call_next(request)
