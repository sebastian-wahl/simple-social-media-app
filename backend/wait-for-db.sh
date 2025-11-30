#!/bin/sh
set -e

echo "Waiting for Postgres to be ready..."

# Keep trying until pg_isready reports success
until pg_isready -h db -p 5432 -U "$POSTGRES_USER" > /dev/null 2>&1; do
  echo "Postgres is unavailable - sleeping"
  sleep 2
done

echo "Postgres is ready!"

# Execute the command we pass to the script
exec "$@"
