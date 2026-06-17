from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers import pages

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Book Library", version="1.0.0")

app.include_router(pages.router)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")
