import asyncio

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Book
from app.schemas import GoogleBookResult


def _extract_isbn(industry_identifiers: list[dict] | None) -> str | None:
    if not industry_identifiers:
        return None
    for identifier in industry_identifiers:
        if identifier.get("type") in ("ISBN_13", "ISBN_10"):
            return identifier.get("identifier")
    return None


def _parse_volume(volume: dict) -> GoogleBookResult | None:
    volume_id = volume.get("id")
    info = volume.get("volumeInfo", {})
    title = info.get("title")
    if not volume_id or not title:
        return None

    authors = info.get("authors") or []
    image_links = info.get("imageLinks") or {}

    return GoogleBookResult(
        google_books_id=volume_id,
        title=title,
        author=", ".join(authors) if authors else None,
        isbn=_extract_isbn(info.get("industryIdentifiers")),
        description=info.get("description"),
        published_date=info.get("publishedDate"),
        cover_url=image_links.get("thumbnail") or image_links.get("smallThumbnail"),
    )


def _api_params(**extra: str | int) -> dict[str, str | int]:
    params: dict[str, str | int] = dict(extra)
    if settings.google_books_api_key:
        params["key"] = settings.google_books_api_key
    return params


def _rate_limit_message() -> str:
    if settings.google_books_api_key:
        return (
            "Google Books rate limit reached. Wait a minute and try again, "
            "or check that your API key is valid in Google Cloud Console."
        )
    return (
        "Google Books rate limit reached. Add GOOGLE_BOOKS_API_KEY to your .env file "
        "(get a free key from Google Cloud Console → Books API), then restart the server."
    )


async def _get_with_retry(
    client: httpx.AsyncClient, url: str, params: dict[str, str | int]
) -> httpx.Response:
    last_exc: httpx.HTTPStatusError | None = None
    for attempt in range(2):
        response = await client.get(url, params=params)
        if response.status_code != 429:
            return response
        last_exc = httpx.HTTPStatusError(
            "429 Too Many Requests", request=response.request, response=response
        )
        if attempt == 0:
            await asyncio.sleep(1.5)
    assert last_exc is not None
    raise last_exc


async def search_google_books(query: str, max_results: int = 20) -> list[GoogleBookResult]:
    params = _api_params(q=query, maxResults=max_results)
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await _get_with_retry(
                client, settings.google_books_api_url, params
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=_rate_limit_message(),
            ) from exc
        if exc.response.status_code in (400, 403):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Google Books API rejected the request. Check your API key in .env.",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch results from Google Books",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to connect to Google Books API",
        ) from exc

    results: list[GoogleBookResult] = []
    for item in data.get("items", []):
        parsed = _parse_volume(item)
        if parsed:
            results.append(parsed)
    return results


async def add_google_book_to_library(
    db: Session, *, user_id: int, google_books_id: str
) -> Book:
    from app.crud import book as book_crud

    existing = book_crud.get_book_by_google_id(db, user_id, google_books_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This book is already in your library",
        )

    google_book = await get_google_book_by_id(google_books_id)
    if not google_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found on Google Books",
        )

    return book_crud.create_book_from_google(
        db, user_id=user_id, google_book=google_book
    )


async def get_google_book_by_id(google_books_id: str) -> GoogleBookResult | None:
    url = f"{settings.google_books_api_url}/{google_books_id}"
    params = _api_params()
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await _get_with_retry(client, url, params)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return _parse_volume(response.json())
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=_rate_limit_message(),
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch book from Google Books",
        ) from exc
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch book from Google Books",
        )
