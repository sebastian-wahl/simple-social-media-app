# Social Media App (Backend + Frontend)

This repository contains the initial backend setup for a social media–style application.  
The backend is written in **Python** using **SQLModel** (built on top of SQLAlchemy) and currently uses an **in-memory SQLite** database for testing.  
The frontend (React or Angular) will be added later.

---

## Project Structure
```
your-repo/
├─ .venv/ Python virtual environment
├─ backend/
│ ├─ src/
│ │ └─ social_media_app/
│ │  ├─ init.py
│ │  ├─ models.py # SQLModel Post model
│ │  └─ db.py # DB engine + CRUD helper functions
│ ├─ tests/
│ │ └─ test_db.py # Unit tests for Post + DB helper logic
│ ├─ requirements.txt # Dependencies for backend
│ ├─ pyproject.toml # pytest configuration (adds src/ to PYTHONPATH)
| └─ ruff.toml # ruff configuration file
├─ frontend/ # (to be implemented later)
└─ .github/workflows/ # (CI configuration will go here)
```


---

## Backend Setup
1) **Create a virtual environment (recommended)**
```
python -m venv .venv
```
2) **Activate the environment**
- macOS / Linux
```
source .venv/bin/activate
```

- Windows (PowerShell)
```
.\.venv\Scripts\Activate
```

You should see a (.venv) prefix in your terminal prompt.

3) **Install dependencies**
```
pip install -r backend/requirements.txt
```

---
## Running Tests (pytest)
Run all backend tests:
```
# from repo root
pytest -q backend
# or from backend/
pytest -q
```

Run a single test file:
```
pytest -q backend/tests/test_db.py
```

Run a single test function:
```
pytest -q backend/tests/test_db.py::test_add_and_get_latest
```

**Useful flags:**
- -q — quiet output (short)
- -v — verbose (shows each test name)
- -k < expr > — run tests matching an expression
```
pytest -k latest -v backend
```
- -x — stop after first failure
- -s — don’t capture stdout (see print output)

Pytest is configured via `backend/pyproject.toml`.

---

## Linting & Formatting (Ruff)

Ruff handles linting, import sorting, and formatting.

### Core commands

**Lint only (no changes):**
```
ruff check backend
```

**Lint and auto-fix (where safe):**
```
ruff check backend --fix
```

**Format code (like Black):**
```
ruff format backend
```

**Verify formatting (CI-friendly, no changes):**
```
ruff format --check backend
```

**Typical local workflow**
```
# Auto-fix lint issues
ruff check backend --fix
# Format code
ruff format backend
# Run tests
pytest -q backend
```

Ruff is configured in `backend/ruff.toml`.