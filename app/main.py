from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine, run_migrations
from app.routers import libraries, pages

Base.metadata.create_all(bind=engine)
run_migrations()

app = FastAPI(title="Book Library", version="1.0.0")

app.include_router(pages.router)
app.include_router(libraries.router, prefix="/api")

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")
