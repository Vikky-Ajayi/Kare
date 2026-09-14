#!/bin/sh
# Railway's custom startCommand isn't reliably run through a shell, so
# ${VAR:-default} expansion silently fails there (confirmed from deploy logs:
# gunicorn received the literal string "${WEB_CONCURRENCY:-2}"). Wrapping in
# `sh -c '...'` inside railway.json's startCommand did not fix it either —
# something (possibly a dashboard-level Custom Start Command override) is
# still bypassing shell interpretation. A real script file sidesteps the
# whole question: Railway just has to execute one file, and *that* always
# runs under a shell.
set -e
alembic upgrade head
exec gunicorn app.main:app -k uvicorn.workers.UvicornWorker \
  -w "${WEB_CONCURRENCY:-2}" -b "0.0.0.0:${PORT:-8000}" --timeout 120
