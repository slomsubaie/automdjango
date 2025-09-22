#!/bin/sh
set -e

# default values (can come from .env)
DB_HOST=${POSTGRES_HOST:-db}
DB_PORT=${POSTGRES_PORT:-5432}
DB_NAME=${POSTGRES_DB:-postgres}
DB_USER=${POSTGRES_USER:-postgres}
DB_PASS=${POSTGRES_PASSWORD:-postgres}

echo "Waiting for Postgres at $DB_HOST:$DB_PORT..."

# small python loop to wait for postgres to accept connections
python - <<'PY'
import os, sys, time
import psycopg2

host = os.environ.get("POSTGRES_HOST", "db")
port = int(os.environ.get("POSTGRES_PORT", 5432))
user = os.environ.get("POSTGRES_USER", "postgres")
password = os.environ.get("POSTGRES_PASSWORD", "postgres")
dbname = os.environ.get("POSTGRES_DB", "postgres")

for i in range(60):
    try:
        conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname=dbname)
        conn.close()
        print("Postgres is up")
        sys.exit(0)
    except Exception:
        time.sleep(1)
print("Timed out waiting for Postgres", file=sys.stderr)
sys.exit(1)
PY

# run migrations and collectstatic
echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# finally exec the CMD from Dockerfile or compose override
exec "$@"
