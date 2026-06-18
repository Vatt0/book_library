from typing import Literal
import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, ValidationError, field_validator

LibraryVisibility = Literal["private", "public"]

PASSWORD_SPECIAL_RE = re.compile(r"[!@#$%^&*(),.?\":{}|<>\[\]\\/_+=\-~`]")


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must include at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must include at least one lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must include at least one number")
        if not PASSWORD_SPECIAL_RE.search(value):
            raise ValueError("Password must include at least one special character")
        return value


def format_validation_error(exc: ValidationError) -> str:
    errors = exc.errors()
    for field in ("password", "email", "username"):
        for err in errors:
            if err.get("loc") and err["loc"][-1] == field:
                msg = err.get("msg", "Invalid input")
                if msg.startswith("Value error, "):
                    msg = msg.removeprefix("Value error, ")
                return msg
    msg = errors[0].get("msg", "Invalid input")
    if msg.startswith("Value error, "):
        msg = msg.removeprefix("Value error, ")
    return msg


class PublicLibrarySummary(BaseModel):
    username: str
    book_count: int


class BookBase(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    author: str | None = Field(default=None, max_length=500)
    isbn: str | None = Field(default=None, max_length=20)
    description: str | None = None
    published_date: str | None = Field(default=None, max_length=20)
    cover_url: str | None = Field(default=None, max_length=1000)


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    author: str | None = Field(default=None, max_length=500)
    isbn: str | None = Field(default=None, max_length=20)
    description: str | None = None
    published_date: str | None = Field(default=None, max_length=20)
    cover_url: str | None = Field(default=None, max_length=1000)


class PublicBookResponse(BookBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class GoogleBookResult(BaseModel):
    google_books_id: str
    title: str
    author: str | None = None
    isbn: str | None = None
    description: str | None = None
    published_date: str | None = None
    cover_url: str | None = None
