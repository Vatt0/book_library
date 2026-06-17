from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)


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


class GoogleBookResult(BaseModel):
    google_books_id: str
    title: str
    author: str | None = None
    isbn: str | None = None
    description: str | None = None
    published_date: str | None = None
    cover_url: str | None = None
