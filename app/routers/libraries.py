from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.crud import book as book_crud
from app.crud import user as user_crud
from app.database import get_db
from app.schemas import PublicBookResponse, PublicLibrarySummary

router = APIRouter(prefix="/libraries", tags=["libraries"])


@router.get("/public", response_model=list[PublicLibrarySummary])
def list_public_libraries(db: Session = Depends(get_db)):
    return user_crud.get_public_libraries(db)


@router.get("/{username}/books", response_model=list[PublicBookResponse])
def read_public_library_books(
    username: str,
    q: str = Query(default=""),
    db: Session = Depends(get_db),
):
    owner = user_crud.get_public_user_by_username(db, username)
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Public library not found",
        )
    return book_crud.get_books(db, owner.id, query=q)
