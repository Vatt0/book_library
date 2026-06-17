from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Book
from app.schemas import BookCreate, BookUpdate, GoogleBookResult


def create_book(
    db: Session,
    *,
    user_id: int,
    book_in: BookCreate,
    google_books_id: str | None = None,
) -> Book:
    book = Book(
        user_id=user_id,
        google_books_id=google_books_id,
        **book_in.model_dump(),
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def create_book_from_google(
    db: Session, *, user_id: int, google_book: GoogleBookResult
) -> Book:
    book_in = BookCreate(
        title=google_book.title,
        author=google_book.author,
        isbn=google_book.isbn,
        description=google_book.description,
        published_date=google_book.published_date,
        cover_url=google_book.cover_url,
    )
    return create_book(
        db,
        user_id=user_id,
        book_in=book_in,
        google_books_id=google_book.google_books_id,
    )


def get_book(db: Session, book_id: int, user_id: int) -> Book | None:
    return (
        db.query(Book)
        .filter(Book.id == book_id, Book.user_id == user_id)
        .first()
    )


def get_books(db: Session, user_id: int, *, query: str = "") -> list[Book]:
    q = db.query(Book).filter(Book.user_id == user_id)

    if query.strip():
        term = f"%{query.strip()}%"
        q = q.filter(
            or_(
                Book.title.ilike(term),
                Book.author.ilike(term),
                Book.isbn.ilike(term),
                Book.description.ilike(term),
            )
        )

    return q.order_by(Book.updated_at.desc()).all()


def get_book_by_google_id(
    db: Session, user_id: int, google_books_id: str
) -> Book | None:
    return (
        db.query(Book)
        .filter(Book.user_id == user_id, Book.google_books_id == google_books_id)
        .first()
    )


def update_book(db: Session, *, book: Book, book_in: BookUpdate) -> Book:
    update_data = book_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(book, field, value)
    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, *, book: Book) -> None:
    db.delete(book)
    db.commit()
