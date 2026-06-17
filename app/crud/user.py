from sqlalchemy.orm import Session

from app.auth import get_password_hash, get_user_by_email, get_user_by_username
from app.models import User
from app.schemas import UserCreate


def get_registration_error(db: Session, user_in: UserCreate) -> str | None:
    if get_user_by_username(db, user_in.username):
        return "Username already registered"
    if get_user_by_email(db, user_in.email):
        return "Email already registered"
    return None


def create_user(db: Session, user_in: UserCreate) -> User:
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
