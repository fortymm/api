#!/usr/bin/env sh
set -eu

echo "Running alembic upgrade head..."
alembic upgrade head

exec "$@"
