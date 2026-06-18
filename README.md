# Book Library

A personal book library web app built with FastAPI. Create an account, manage your books, search Google Books to add titles, and optionally make your library public for others to browse.

## Features

- **User accounts** — register, login, secure password rules, JWT cookie auth
- **Book management** — add, edit, view, and delete books in your library
- **Google Books search** — find and import book metadata (title, author, ISBN, cover, etc.)
- **Private or public libraries** — keep your collection private or share it publicly
- **Browse public libraries** — explore other users' public collections in the web UI
- **REST API** — read-only access to public libraries (no login required)

## Tech stack

- Python, FastAPI, SQLAlchemy, SQLite
- Jinja2 templates, vanilla CSS/JS
- bcrypt + JWT for authentication
- Google Books API (optional API key)

## Requirements

- Python 3.11+ (3.10+ should work)
- pip

## Setup

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd book_library
   ```

2. **Create a virtual environment and install dependencies**

   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

   On macOS/Linux:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   Copy `.env.example` to `.env` and set a strong `SECRET_KEY`:

   ```powershell
   copy .env.example .env
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

   Paste the generated value into `.env` as `SECRET_KEY=...`.

    Variable  Required  Description 
   
    `SECRET_KEY`  Yes  Signs login tokens (min 32 chars, random) 
    `DATABASE_URL`  No  Defaults to `sqlite:///./book_library.db` 
    `ACCESS_TOKEN_EXPIRE_MINUTES`  No  Login session length (default: 1440) 
    `GOOGLE_BOOKS_API_KEY`  No  Google Books API key (recommended for search) 

   Do not commit `.env` to version control.

## Run

```powershell
.\venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

Interactive API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Public API

Read-only endpoints for public libraries (no authentication):

 Method  Endpoint  Description 

 `GET`  `/api/libraries/public`  List users with public libraries 
 `GET`  `/api/libraries/{username}/books?q=`  Books from a public library |

Example:

```bash
curl http://127.0.0.1:8000/api/libraries/public
curl http://127.0.0.1:8000/api/libraries/demo/books?q=harry
```

Private libraries return `404`. All book management is done through the web UI.

See [API_DOCUMENTATION.txt](API_DOCUMENTATION.txt) for full route details.

## Project structure

```
app/
  main.py              # App entry point
  config.py            # Settings from .env
  auth.py              # Password hashing and JWT
  models.py            # User and Book models
  schemas.py           # Validation
  routers/
    pages.py           # Web UI routes
    libraries.py       # Public library REST API
  crud/                # Database operations
  services/            # Google Books integration
  templates/           # HTML templates
  static/              # CSS, JS, images
```

## Notes

- Rotating `SECRET_KEY` logs out all existing sessions.
- The SQLite database file (`book_library.db`) is created automatically on first run.
- Set library visibility under **Settings** after logging in.
