# Deploying Kare

## Railway (backend + database + follow-up cron)

One Railway project, three services, all from this repo.

### 1. Postgres
Provision PostgreSQL. Note the private `DATABASE_URL` (`postgres.railway.internal`)
and the public `DATABASE_PUBLIC_URL` (for local dev + migrations).

### 2. `web` service
- Source: this repo. Build: Dockerfile (picked up from `railway.json`).
- Region: **europe-west4** (closest to Nigeria).
- Variables:
  ```
  DATABASE_URL=${{Postgres.DATABASE_URL}}
  SECRET_KEY=<32+ byte hex>
  DEBUG=False
  GROQ_API_KEY=...
  SAHARA_API_KEY=...
  VAPID_PUBLIC_KEY=...
  VAPID_PRIVATE_KEY=...
  VAPID_SUBJECT=mailto:you@example.com
  PUBLIC_APP_URL=https://<your-vercel-domain>
  ALLOWED_ORIGINS_STR=https://<your-vercel-domain>
  ```
- `railway.json` runs `alembic upgrade head` before gunicorn on every deploy.

### 3. `followups` service (cron)
- Same repo. Build: Dockerfile.
- **Settings → Cron Schedule:** `*/15 * * * *`
- **Settings → Start Command:** `python -m app.worker.followup_tick`
- Same `DATABASE_URL`, `GROQ_API_KEY`, `VAPID_*`, `PUBLIC_APP_URL` variables.
- It runs one pass over the due follow-up queue and exits; Railway restarts it on schedule.

## Vercel (frontend)

- Root: `frontend_kare/`
- Build: `npm run build`, output `dist/`
- Env: `VITE_API_BASE_URL=https://<your-web-service>.up.railway.app/api/v1`

## Local dev

```bash
make install           # uv venv on 3.12 + deps
cp .env.example .env    # fill in DATABASE_URL (public proxy), keys
make migrate
make seed               # 4 demo patients
make run                # :8000
```

Set `INPROCESS_SCHEDULER=True` in `.env` to run the follow-up tick inside the
dev server instead of a separate cron.
