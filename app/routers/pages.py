from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.auth import authenticate_user, create_access_token
from app.config import settings
from app.crud import book as book_crud
from app.crud import user as user_crud
from app.database import get_db
from app.dependencies import get_user_from_request, page_context, require_user
from app.schemas import BookCreate, BookUpdate, UserCreate
from app.services.google_books import add_google_book_to_library, search_google_books

router = APIRouter(tags=["pages"])

templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


def _set_auth_cookie(response: RedirectResponse, token: str) -> RedirectResponse:
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=settings.access_token_expire_minutes * 60,
        samesite="lax",
    )
    return response


def _empty_to_none(value: str | None) -> str | None:
    if value is None or value.strip() == "":
        return None
    return value.strip()


def _login_required(request: Request, db: Session):
    user = require_user(request, db)
    if isinstance(user, RedirectResponse):
        return None, user
    return user, None


def _book_or_redirect(db: Session, book_id: int, user_id: int):
    book = book_crud.get_book(db, book_id, user_id)
    if not book:
        return None, RedirectResponse(url="/library?error=Book not found", status_code=303)
    return book, None


def _book_form_data(
    title: str,
    author: str,
    isbn: str,
    description: str,
    published_date: str,
    cover_url: str,
) -> dict:
    return {
        "title": title,
        "author": _empty_to_none(author),
        "isbn": _empty_to_none(isbn),
        "description": _empty_to_none(description),
        "published_date": _empty_to_none(published_date),
        "cover_url": _empty_to_none(cover_url),
    }


@router.get("/")
def landing_page(request: Request, db: Session = Depends(get_db)):
    user = get_user_from_request(request, db)
    if user:
        return RedirectResponse(url="/library", status_code=303)
    return templates.TemplateResponse(
        request, "landing.html", page_context(request)
    )


@router.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    if get_user_from_request(request, db):
        return RedirectResponse(url="/library", status_code=303)
    return templates.TemplateResponse(
        request, "login.html", page_context(request)
    )


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse(
            request,
            "login.html",
            page_context(request, error="Invalid username or password"),
        )
    token = create_access_token(data={"sub": user.username})
    response = RedirectResponse(url="/library", status_code=303)
    return _set_auth_cookie(response, token)


@router.get("/register")
def register_page(request: Request, db: Session = Depends(get_db)):
    if get_user_from_request(request, db):
        return RedirectResponse(url="/library", status_code=303)
    return templates.TemplateResponse(
        request, "register.html", page_context(request)
    )


@router.post("/register")
def register_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        user_data = UserCreate(username=username, email=email, password=password)
    except ValidationError as exc:
        message = exc.errors()[0]["msg"]
        return templates.TemplateResponse(
            request,
            "register.html",
            page_context(
                request,
                error=message,
                form={"username": username, "email": email},
            ),
        )

    error = user_crud.get_registration_error(db, user_data)
    if error:
        return templates.TemplateResponse(
            request,
            "register.html",
            page_context(
                request,
                error=error,
                form={"username": username, "email": email},
            ),
        )

    user = user_crud.create_user(db, user_data)
    token = create_access_token(data={"sub": user.username})
    response = RedirectResponse(url="/library", status_code=303)
    return _set_auth_cookie(response, token)


@router.post("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response


@router.get("/library")
def library_page(
    request: Request,
    q: str = Query(default=""),
    db: Session = Depends(get_db),
):
    user, redirect = _login_required(request, db)
    if redirect:
        return redirect

    search_query = q.strip()
    books = book_crud.get_books(db, user.id, query=search_query)
    return templates.TemplateResponse(
        request,
        "library.html",
        page_context(
            request,
            user=user,
            books=books,
            active_tab="library",
            query=search_query,
        ),
    )


@router.get("/library/search")
async def library_search_page(
    request: Request,
    q: str = "",
    db: Session = Depends(get_db),
):
    user, redirect = _login_required(request, db)
    if redirect:
        return redirect

    results = []
    search_error = None
    if q.strip():
        try:
            results = await search_google_books(q.strip())
        except HTTPException as exc:
            search_error = exc.detail

    return templates.TemplateResponse(
        request,
        "search.html",
        page_context(
            request,
            user=user,
            query=q,
            results=results,
            active_tab="search",
            error=search_error,
        ),
    )


@router.post("/library/google/add")
async def add_google_book(
    request: Request,
    google_books_id: str = Form(...),
    db: Session = Depends(get_db),
):
    user, redirect = _login_required(request, db)
    if redirect:
        return redirect

    try:
        await add_google_book_to_library(
            db, user_id=user.id, google_books_id=google_books_id
        )
    except HTTPException as exc:
        return RedirectResponse(
            url=f"/library/search?error={quote(str(exc.detail))}",
            status_code=303,
        )

    return RedirectResponse(
        url="/library?success=Book added from Google Books", status_code=303
    )


@router.get("/library/add")
def add_book_page(request: Request, db: Session = Depends(get_db)):
    user, redirect = _login_required(request, db)
    if redirect:
        return redirect

    return templates.TemplateResponse(
        request,
        "book_form.html",
        page_context(request, user=user, book=None, form_action="/library/add"),
    )


@router.post("/library/add")
def add_book_submit(
    request: Request,
    title: str = Form(...),
    author: str = Form(""),
    isbn: str = Form(""),
    description: str = Form(""),
    published_date: str = Form(""),
    cover_url: str = Form(""),
    db: Session = Depends(get_db),
):
    user, redirect = _login_required(request, db)
    if redirect:
        return redirect

    form_data = _book_form_data(
        title, author, isbn, description, published_date, cover_url
    )

    try:
        book_in = BookCreate(**form_data)
    except ValidationError as exc:
        return templates.TemplateResponse(
            request,
            "book_form.html",
            page_context(
                request,
                user=user,
                book=None,
                form_action="/library/add",
                error=exc.errors()[0]["msg"],
                form=form_data,
            ),
        )

    book_crud.create_book(db, user_id=user.id, book_in=book_in)
    return RedirectResponse(url="/library?success=Book added", status_code=303)


@router.get("/library/{book_id}")
def book_detail_page(
    request: Request, book_id: int, db: Session = Depends(get_db)
):
    user, redirect = _login_required(request, db)
    if redirect:
        return redirect

    book, redirect = _book_or_redirect(db, book_id, user.id)
    if redirect:
        return redirect

    return templates.TemplateResponse(
        request,
        "book_detail.html",
        page_context(request, user=user, book=book, active_tab="library"),
    )


@router.get("/library/{book_id}/edit")
def edit_book_page(
    request: Request, book_id: int, db: Session = Depends(get_db)
):
    user, redirect = _login_required(request, db)
    if redirect:
        return redirect

    book, redirect = _book_or_redirect(db, book_id, user.id)
    if redirect:
        return redirect

    return templates.TemplateResponse(
        request,
        "book_form.html",
        page_context(
            request,
            user=user,
            book=book,
            form_action=f"/library/{book_id}/edit",
        ),
    )


@router.post("/library/{book_id}/edit")
def edit_book_submit(
    request: Request,
    book_id: int,
    title: str = Form(...),
    author: str = Form(""),
    isbn: str = Form(""),
    description: str = Form(""),
    published_date: str = Form(""),
    cover_url: str = Form(""),
    db: Session = Depends(get_db),
):
    user, redirect = _login_required(request, db)
    if redirect:
        return redirect

    book, redirect = _book_or_redirect(db, book_id, user.id)
    if redirect:
        return redirect

    form_data = _book_form_data(
        title, author, isbn, description, published_date, cover_url
    )

    try:
        book_in = BookUpdate(**form_data)
    except ValidationError as exc:
        return templates.TemplateResponse(
            request,
            "book_form.html",
            page_context(
                request,
                user=user,
                book=book,
                form_action=f"/library/{book_id}/edit",
                error=exc.errors()[0]["msg"],
                form=form_data,
            ),
        )

    book_crud.update_book(db, book=book, book_in=book_in)
    return RedirectResponse(url="/library?success=Book updated", status_code=303)


@router.get("/library/{book_id}/delete")
def delete_book_page(
    request: Request, book_id: int, db: Session = Depends(get_db)
):
    user, redirect = _login_required(request, db)
    if redirect:
        return redirect

    book, redirect = _book_or_redirect(db, book_id, user.id)
    if redirect:
        return redirect

    return templates.TemplateResponse(
        request,
        "delete_confirm.html",
        page_context(request, user=user, book=book),
    )


@router.post("/library/{book_id}/delete")
def delete_book_submit(
    request: Request, book_id: int, db: Session = Depends(get_db)
):
    user, redirect = _login_required(request, db)
    if redirect:
        return redirect

    book, redirect = _book_or_redirect(db, book_id, user.id)
    if redirect:
        return redirect

    book_crud.delete_book(db, book=book)
    return RedirectResponse(url="/library?success=Book deleted", status_code=303)
