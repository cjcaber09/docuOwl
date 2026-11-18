from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.auth.dependencies import SESSION_COOKIE, CurrentUser, DbSession
from app.auth.passwords import DUMMY_HASH, hash_password, verify_password
from app.auth.rate_limit import login_by_email, login_by_ip, signup_by_ip
from app.auth.schemas import LoginRequest, SignupRequest, UserOut
from app.auth.tokens import SESSION_LIFETIME, create_session_token
from app.config import get_settings
from app.models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def too_many_attempts() -> HTTPException:
    return HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many attempts. Please wait a few minutes and try again.")


def set_session_cookie(response: Response, user: User) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        create_session_token(user.id, user.token_version),
        max_age=int(SESSION_LIFETIME.total_seconds()),
        httponly=True,
        secure=get_settings().cookie_secure,
        samesite="lax",
        path="/",
    )


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest, request: Request, response: Response, db: DbSession) -> UserOut:
    if not signup_by_ip.allow(client_ip(request)):
        raise too_many_attempts()
    user = User(email=body.email, password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")
    set_session_cookie(response, user)
    return UserOut.model_validate(user)


@router.post("/login")
def login(body: LoginRequest, request: Request, response: Response, db: DbSession) -> UserOut:
    if not (login_by_ip.allow(client_ip(request)) and login_by_email.allow(body.email)):
        raise too_many_attempts()
    user = db.scalar(select(User).where(User.email == body.email))
    # Always check a hash, even for unknown emails, so both cases take the same time.
    password_ok = verify_password(body.password, user.password_hash if user else DUMMY_HASH)
    if user is None or not password_ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong email or password.")
    set_session_cookie(response, user)
    return UserOut.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    response.delete_cookie(
        SESSION_COOKIE, path="/", httponly=True, secure=get_settings().cookie_secure, samesite="lax"
    )


@router.get("/me")
def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
