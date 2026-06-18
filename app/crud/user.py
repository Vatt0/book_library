from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_password_hash, get_user_by_email, get_user_by_username
from app.models import Book, User
from app.schemas import LibraryVisibility, UserCreate


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


def update_library_visibility(
    db: Session, *, user: User, visibility: LibraryVisibility
) -> User:
    user.library_visibility = visibility
    db.commit()
    db.refresh(user)
    return user


def get_public_libraries(db: Session) -> list[dict]:
    rows = (
        db.query(
            User.username,
            func.count(Book.id).label("book_count"),
        )
        .outerjoin(Book, Book.user_id == User.id)
        .filter(User.library_visibility == "public")
        .group_by(User.id)
        .order_by(User.username.asc())
        .all()
    )
    return [{"username": row.username, "book_count": row.book_count} for row in rows]


def get_public_user_by_username(db: Session, username: str) -> User | None:
    return (
        db.query(User)
        .filter(User.username == username, User.library_visibility == "public")
        .first()
    )
