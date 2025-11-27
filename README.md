# Social Media App — Backend & Frontend

This repository hosts the backend for a social-media–style application built using:

- **FastAPI** (API layer)
- **SQLModel** (SQLAlchemy ORM)
- **SQLite** for development / **PostgreSQL** in production
- **MinIO** for image storage (S3 compatible)

A frontend (React or Angular) will be implemented later.

---

# Project Structure

```
your-repo/
├─ .venv/                       # Python virtual env (local only)
├─ .env.template                # Template for environment variables
├─ .env                         # for the environment variables
├─ backend/
│  ├─ src/
│  │  └─ social_media_app/
│  │     ├─ __init__.py
│  │     ├─ app.py              # FastAPI application
│  │     ├─ config.py           # Environment + configuration loading
│  │     ├─ main.py             # Uvicorn startup wrapper (python -m)
│  │     ├─ models.py           # SQLModel models
│  │     ├─ dtos.py             # DTOs for request/response + mapping helpers
│  │     ├─ db.py               # Database access layer (CRUD + filters)
│  │     └─ minio_db.py         # MinIO storage helper functions
│  │
│  ├─ tests/
│  │  ├─ __init__.py
│  │  ├─ test_api.py            # API-level tests
│  │  ├─ test_db.py             # DB + CRUD tests
│  │  └─ test_minio_db.py       # MinIO helper tests
│  │
│  ├─ requirements.txt          # Backend dependencies
│  ├─ pyproject.toml            # pytest configuration (adds src to PYTHONPATH)
│  └─ ruff.toml                 # Linting + formatting configuration
│
├─ frontend/                
│   ├─ node_modules             # modules created from node.js
│   ├─ pic                      # Logo
│   ├─ public                   # vite.svg
│   ├─ src/                 
│   │  ├─ api/
│   │  │  ├─ client.ts          # client env
│   │  │  ├─ dto.ts             # DTOs for Pages / Comments / Posts
│   │  │  ├─ posts.ts           # functions for posting / listing Posts / Comments etc.
│   │  │  └─ tags.ts            # list tags
│   │  ├─ assets/
│   │  │  └─ react.svg          # react pic
│   │  ├─ components/
│   │  │  ├─ CommentForm.tsx    # Form for the Comments
│   │  │  ├─ CommentList.tsx    # Lists all the comments
│   │  │  ├─ PostCard.tsx       # Card for the posts
│   │  │  ├─ RatingStars.tsx    # Card for the Rating Stars feature
│   │  │  └─ TagFilter.tsx      # Function for the Filter
│   │  ├─ pages/
│   │  │  ├─ CreatePostPage.tsx # Creates the Post Page Page
│   │  │  ├─ FeedPage.tsx       # Creates the Page for the Feeds 
│   │  │  └─ PostDetailPage.tsx # Creates Page for the Post Details
│   │  ├─ style
│   │  │  └─ index.css          # Cosmetics
│   │  ├─ App.css               # Cosmetics App
│   │  ├─ App.tsx               # Main App.tsx
│   │  ├─ index.css             # Main Cosmetics Page
│   │  └─ main.tsx              # Main Page
│   ├─ .env.development         # env data
│   ├─ eslint.config.js         # config
│   ├─ index.html               # main index
│   ├─ package-lock.json        # versions
│   ├─ package.json             # package informations
│   ├─ postcss.config.cjs       # modules tailwindcss prefixer
│   ├─ tailwind.config.cjs      # tailwind config
│   ├─ tsconfig.app.json        # config json
│   └─ vite.config.ts           # vite config
│
└─ .github/workflows/           # GitHub Actions (CI)
```

---

# Environment Configuration

The backend uses environment variables to configure:

- SQLite / PostgreSQL database
- MinIO storage
- FastAPI runtime settings

A template exists at:

```
backend/.env.template
```

## Setup:

1) **Copy the template**
```
cp backend/.env.template backend/.env
```

2) **Customize values** (SQLite is default):

Example for local dev:
```
DATABASE_URL=sqlite:///social-media-app.db
MINIO_ENABLED=false
```

Example when running MinIO & Postgres via Docker:
```
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/appdb
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=post-images
MINIO_ENABLED=true
```

## How env files are loaded

The file `config.py` uses `python-dotenv` to load `.env` automatically:

```python
from dotenv import load_dotenv
load_dotenv()
```

Meaning:  
Just create a `.env` file — no manual exporting needed.

---

# Backend Setup

1) **Create a virtual environment**
```
python -m venv .venv
```

2) **Activate it**

macOS / Linux:
```
source .venv/bin/activate
```

Windows (PowerShell):
```
.\.venv\Scripts\Activate
```

3) **Install dependencies**
```
pip install -r backend/requirements.txt
```

---

# Running the API

### Option A — Using Uvicorn directly:
```
uvicorn social_media_app.app:app --reload
```

### Option B — Using the provided `main.py`:
```
python -m social_media_app.main
```

This loads env settings such as:
- host
- port
- environment
- reload mode

---

# Testing (pytest)

Run all backend tests:

```
pytest -q backend
```

or:
```
pytest -q
```

Run a specific file:

```
pytest backend/tests/test_db.py -q
```

Run a single test function:

```
pytest backend/tests/test_db.py::test_add_and_get_latest
```

Useful flags:

- `-q` quiet output
- `-v` verbose
- `-k <expr>` filter by test name
- `-s` show print output
- `-x` stop after first failure

Pytest configuration lives in `backend/pyproject.toml`.

---

# Linting & Formatting (Ruff)

Ruff performs linting, import-sorting, and formatting.

### Lint only:
```
ruff check backend
```

### Lint + auto-fix:
```
ruff check backend --fix
```

### Format:
```
ruff format backend
```

### Format check (CI-safe):
```
ruff format --check backend
```

Typical workflow:

```
ruff check backend --fix
ruff format backend
pytest -q backend
```

Configured via `backend/ruff.toml`.

---

# MinIO Image Storage

- `/uploads/images` handles file uploads.
- Backend stores images in MinIO (or uses dummy mode if MINIO_ENABLED=false).
- `/posts` uses the `image_path` returned from upload.

---

# Notes for development

- Always run `ruff check` + `ruff format` before committing.
- `.env` should **NEVER** be committed — only `.env.template`.
- Use `MINIO_ENABLED=false` during early development.

---

# Frontend (placeholder)

The frontend folder exists for future React / Angular implementation.
