from pydantic import field_validator
from pydantic_settings import BaseSettings

WEAK_SECRET_KEYS = frozenset(
    {
        "change-this-secret-key-in-production",
        "change-this-to-a-long-random-string",
        "replace-with-output-from-command-above",
        "secret",
        "your-secret-key",
        "dev",
        "test",
    }
)


SECRET_KEY_GENERATE_CMD = 'python -c "import secrets; print(secrets.token_urlsafe(48))"'


class Settings(BaseSettings):
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    database_url: str = "sqlite:///./book_library.db"
    google_books_api_url: str = "https://www.googleapis.com/books/v1/volumes"
    google_books_api_key: str | None = None

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        key = value.strip()
        if len(key) < 32:
            raise ValueError(
                f"SECRET_KEY must be at least 32 characters. "
                f"Generate one with: {SECRET_KEY_GENERATE_CMD}"
            )
        if key.lower() in WEAK_SECRET_KEYS:
            raise ValueError(
                f"SECRET_KEY is a known weak placeholder. "
                f"Generate a random key with: {SECRET_KEY_GENERATE_CMD}"
            )
        return key

    @field_validator("google_books_api_key", mode="before")
    @classmethod
    def empty_api_key_to_none(cls, value: str | None) -> str | None:
        if value is None or str(value).strip() == "":
            return None
        return str(value).strip()

    class Config:
        env_file = ".env"


settings = Settings()
