#!/usr/bin/env bash
# Activates the Python virtual environment and exports PostgreSQL connection variables
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/venv/bin/activate"
export PATH="$HERE/venv/bin:$PATH"

export POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
export POSTGRES_USER="${POSTGRES_USER:-raw_user}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-raw_password}"
export POSTGRES_DB="${POSTGRES_DB:-raw_db}"
export DW_POSTGRES_DB="${DW_POSTGRES_DB:-analytics_db}"

export PGHOST="$POSTGRES_HOST"
export PGPORT="$POSTGRES_PORT"
export PGUSER="$POSTGRES_USER"
export PGPASSWORD="$POSTGRES_PASSWORD"
export PGDATABASE="$DW_POSTGRES_DB"
