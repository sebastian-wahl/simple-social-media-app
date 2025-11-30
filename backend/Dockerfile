# Use a slim Python image
FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Working directory inside the container
WORKDIR /app

# Install system-level dependencies (psycopg needs build tools, wait script needs pg_isready from postgresql-client)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker caching)
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/src ./src

# Copy wait script and make executable
COPY backend/wait-for-db.sh /wait-for-db.sh
RUN chmod +x /wait-for-db.sh

# Make sure Python can find social_media_app
ENV PYTHONPATH=/app/src

# Expose FastAPI port
EXPOSE 8000

# Default command: run wait script then uvicorn
CMD ["/wait-for-db.sh", "uvicorn", "social_media_app.app:app", "--host", "0.0.0.0", "--port", "8000"]
