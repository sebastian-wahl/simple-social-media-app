# Use a slim Python image
FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Working directory inside the container
WORKDIR /app

# Install system-level dependencies (if you ever need psycopg etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the actual backend source code
COPY backend/src ./src

# Make sure Python can find social_media_app
ENV PYTHONPATH=/app/src

# Expose FastAPI port
EXPOSE 8000

# Default command: run the API with Uvicorn
CMD ["sh", "-c", "uvicorn social_media_app.app:app --host ${APP_HOST:-0.0.0.0} --port ${APP_PORT:-8000}"]

