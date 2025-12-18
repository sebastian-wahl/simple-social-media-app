FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy worker requirements (from repo root context)
COPY backend/src/worker/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker source
COPY backend/src/worker/resize_worker.py .

CMD ["python", "resize_worker.py"]