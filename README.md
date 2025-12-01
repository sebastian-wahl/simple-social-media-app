# Social Media App — Backend & Frontend

A simple social-media–style application built with:

- **FastAPI** (API)
- **SQLModel** / SQLAlchemy ORM
- **PostgreSQL** (via Docker) or SQLite (local dev)
- **MinIO** (S3-compatible object storage)
- React/Vite Frontend

This repository contains both backend and frontend code, plus a Docker-based local development stack.

## Project Structure

```
project-root/
├─ .env                     # All environment variables live here
├─ .env.template            # Example configuration
├─ docker-compose.yml       # Local stack (API + Postgres + MinIO)

├─ backend/
│  ├─ Dockerfile
│  ├─ requirements.txt
│  ├─ wait-for-services.sh
│  └─ src/
│     └─ social_media_app/
│         ├─ app.py
│         ├─ config.py
│         ├─ db.py
│         ├─ dtos.py
│         ├─ main.py
│         ├─ minio_db.py
│         └─ models.py

├─ db/
│  ├─ init.sql
│  ├─ postgres-data/
│  └─ minio-data/

├─ frontend/
│  ├─ public/
│  ├─ src/
│  ├─ package.json
│  └─ vite.config.ts
```

## Environment Configuration

Your full environment lives in one root-level `.env` file:

```
project-root/.env
```

Create it:

```bash
cp .env.template .env
```
---

## Docker Compose (Local Development Stack)

The `docker-compose.yml` spins up:

- **PostgreSQL**
- **MinIO**
- **Backend API (FastAPI)**

Run all services:

```bash
docker compose up --build
```

### ⚠️ Note for Development

When using the API through Docker:

- **Every backend code change requires rebuilding the image**,  
  because the Dockerfile copies source code into the container image.

So for active development, prefer running FastAPI directly:

```bash
uvicorn social_media_app.app:app --reload
```

And reserve Docker Compose for:

- full-stack testing,
- integration tests,
- CI,
- running Postgres + MinIO,
- demonstrating the packaged application.

---

## Backend Development

Create venv:

```bash
python -m venv .venv
source .venv/bin/activate  # PowerShell: .\.venv\Scripts\Activate
pip install -r backend/requirements.txt
```

Run API:

```bash
uvicorn social_media_app.app:app --reload
```

---

## API Docker Image

The backend image is built using:

```
backend/Dockerfile
```

Build manually:

```bash
docker build -t social-media-backend -f backend/Dockerfile .
```

Run manually:

```bash
docker run -p 8000:8000 --env-file .env social-media-backend
```

---

## Database Initialization (PostgreSQL)

The initialization script is located at:

```
db/init.sql
```

This script:

- Drops all tables (development mode)
- Recreates schema from SQLModel definitions
- Inserts optional test data (commented out)

It runs **only the first time a fresh database volume is created**.

Reset database:

```bash
docker compose down -v
docker compose up --build
```

---

## MinIO

MinIO is used to store uploaded images.
- `/uploads/images` handles file uploads.
- Backend stores images in MinIO (or uses dummy mode if MINIO_ENABLED=false).
- `/posts` uses the `image_path` returned from upload.

Health endpoint:

```
http://localhost:9002
```

API endpoint:

```
http://localhost:9000
```

Credentials come from `.env`.

---

## Frontend

The frontend folder is unchanged from the original structure and includes a full Vite + React setup.

Run development frontend:

```bash
cd frontend
npm install
npm run dev
```

---

## Testing

Run tests:

```bash
pytest -q
```

---

## Linting (Ruff)

```
ruff check backend --fix
ruff format backend
```

---

## Notes

- `.env` should never be committed.
- The Docker stack is ideal for full integration testing or demo deployments.
- For rapid backend development, use Uvicorn directly with reload mode.
