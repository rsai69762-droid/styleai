#!/bin/bash
set -e
 
echo "Waiting for database to be ready..."
while ! pg_isready -h postgres -U stylai; do
  echo "Database is unavailable - sleeping"
  sleep 1
done
 
echo "Database is ready!"
 
echo "Running database migrations..."
alembic upgrade head
 
echo "Starting FastAPI application..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
 