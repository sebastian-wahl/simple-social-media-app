#!/bin/sh
set -e

echo "Waiting for Postgres..."

until pg_isready -h db -p 5432 -U "$POSTGRES_USER" > /dev/null 2>&1; do
    echo "Postgres is unavailable - sleeping"
    sleep 2
done

echo "Postgres is ready!"


echo "Waiting for MinIO..."

# Check the /ready endpoint
until curl -sf http://minio:9000/minio/health/ready > /dev/null 2>&1; do
    echo "MinIO is unavailable - sleeping"
    sleep 2
done

echo "MinIO is ready!"


echo "Starting application..."
exec "$@"
