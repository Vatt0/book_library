from fastapi import Request
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.auth import get_user_by_username
from app.config import settings
from app.models import User


def get_user_from_token(db: Session, token: str | None) -> User | None:
    if not token:
        return None
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        username: str | None = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    return get_user_by_username(db, username)


def get_user_from_request(request: Request, db: Session) -> User | None:
    token = request.cookies.get("access_token")
    return get_user_from_token(db, token)


def require_user(request: Request, db: Session) -> User | RedirectResponse:
    user = get_user_from_request(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return user


def page_context(request: Request, user: User | None = None, **kwargs) -> dict:
    return {
        "request": request,
        "user": user,
        "success": request.query_params.get("success"),
        "error": request.query_params.get("error"),
        **kwargs,
    }
