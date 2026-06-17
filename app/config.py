from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    secret_key: str = "change-this-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    database_url: str = "sqlite:///./book_library.db"
    google_books_api_url: str = "https://www.googleapis.com/books/v1/volumes"
    google_books_api_key: str | None = None

    @field_validator("google_books_api_key", mode="before")
    @classmethod
    def empty_api_key_to_none(cls, value: str | None) -> str | None:
        if value is None or str(value).strip() == "":
            return None
        return str(value).strip()

    class Config:
        env_file = ".env"


settings = Settings()
