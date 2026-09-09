# Deploying Kare

Two hosts: **Railway** (FastAPI + Postgres) and **Vercel** (the React PWA).
~15 minutes end to end. Nothing here needs a credit card beyond Railway's ~$5/mo
hobby plan.

---

## 1 · Railway — backend + database

### 1a. Create the project + database
1. [railway.com](https://railway.com) → **New Project** → **Deploy PostgreSQL**.
2. Open the Postgres service → **Variables** → note two values:
   - `DATABASE_URL` — internal (`postgres.railway.internal`), used by the app
   - `DATABASE_PUBLIC_URL` — proxy (`*.proxy.rlwy.net`), used for local dev + psql

### 1b. Add the web service
1. In the project → **New** → **GitHub Repo** → pick this repo.
2. Settings → **Region**: `europe-west4` (Amsterdam — lowest latency to Nigeria
   of Railway's regions).
3. Build & deploy come from [`railway.json`](railway.json): Docker build, then
   `alembic upgrade head && gunicorn …` on every deploy. Health check: `/health`.
4. **Variables** (Raw editor — paste, then fill in):
   ```
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   SECRET_KEY=            # python -c "import secrets; print(secrets.token_hex(32))"
   DEBUG=False
   GROQ_API_KEY=
   SAHARA_API_KEY=
   VAPID_PUBLIC_KEY=
   VAPID_PRIVATE_KEY=
   VAPID_SUBJECT=mailto:you@example.com
   PUBLIC_APP_URL=https://<your-vercel-domain>
   ALLOWED_ORIGINS_STR=https://<your-vercel-domain>
   WEB_CONCURRENCY=1
   INPROCESS_SCHEDULER=True
   INPROCESS_SCHEDULER_MINUTES=15
   ```
   - `INPROCESS_SCHEDULER=True` runs the proactive-follow-up tick inside the web
     process (APScheduler, `max_instances=1`). With `WEB_CONCURRENCY=1` that is
     exactly one ticker — simplest reliable setup for the demo. For scale, set
     both to their defaults and add the separate cron service below.
   - Generate the VAPID pair once. Easiest: open
     `https://web-push-codelab.glitch.me` and copy the "Public Key" /
     "Private Key" (both are base64url strings, exactly what Kare wants). Or
     with the `py-vapid` CLI: `vapid --gen && vapid --applicationServerKey`.
     The frontend reads the public key from `GET /notifications/vapid-key` at
     runtime, so it only needs to be set here.
5. Deploy. When it's green, hit `https://<web>.up.railway.app/health` → `{"status":"healthy","database":"ok"}`.

### 1c. Seed the demo data (once)
From your machine, pointed at the **public** URL:
```bash
export DATABASE_URL='postgresql://…@…proxy.rlwy.net:PORT/railway'
make migrate      # no-op if the deploy already ran it
make seed         # 4 demo patients, password: demo-kare-2026
```

### 1d. (optional, for scale) separate follow-up cron
Instead of `INPROCESS_SCHEDULER`, add a second service from the same repo:
- **Settings → Start Command:** `python -m app.worker.followup_tick`
- **Settings → Cron Schedule:** `*/15 * * * *`
- Same `DATABASE_URL`, `GROQ_API_KEY`, `VAPID_*`, `PUBLIC_APP_URL` variables.
- It processes the due queue once and exits; Railway re-runs it on schedule.
- Then set `INPROCESS_SCHEDULER=False` on the web service.

---

## 2 · Vercel — frontend

1. [vercel.com](https://vercel.com) → **Add New → Project** → import this repo.
2. **Root Directory:** `frontend_kare`
3. Framework preset: **Vite**. Build: `npm run build`, output: `dist`.
4. **Environment Variable** (just one — the frontend fetches the VAPID public
   key from the API at runtime):
   ```
   VITE_API_BASE_URL=https://<your-web-service>.up.railway.app/api/v1
   ```
5. Deploy. Then go back to Railway and set `PUBLIC_APP_URL` +
   `ALLOWED_ORIGINS_STR` to the real Vercel URL, and redeploy the web service.

---

## 3 · Smoke test the live stack

```
1. open the Vercel URL → register → you land in the dashboard
2. Voice Doctor → accept the consent gate → type "I have a headache and I'm on amlodipine"
   → reply comes back, "Checked drug interactions" chip appears
3. Settings → enable proactive check-ins → allow the browser prompt
4. end the consultation → in Railway shell (or locally against the public DB):
     python -m app.worker.followup_tick
   → a push notification arrives → tapping it reopens the same conversation
5. /health is green; /docs renders
```

---

## Local dev

```bash
make install                       # uv venv (py3.12) + deps
cp .env.example .env                # DATABASE_URL = the public proxy URL; fill keys
make migrate
make seed
make run                            # :8000  ·  /docs

cd frontend_kare && npm install && npm run dev   # :3000
```

Set `INPROCESS_SCHEDULER=True` in `.env` to exercise the follow-up tick locally,
or run `python -m app.worker.followup_tick` by hand.

## Notes

- **Migrations** run automatically on every Railway deploy (`railway.json`
  start command). The chain is 4 migrations; `alembic upgrade head` from an
  empty database creates all 14 tables.
- **CORS** is header-based (`allow_credentials=False`); `ALLOWED_ORIGINS_STR`
  must list the exact Vercel origin(s), comma-separated, no trailing slash.
- **The app refuses to boot** on a broken production config (`SECRET_KEY` too
  short, `DATABASE_URL` still SQLite, missing `GROQ_API_KEY` / `SAHARA_API_KEY`)
  — check the deploy logs if it crash-loops.
- **tzdata** is a dependency because slim containers ship no OS timezone DB and
  the quiet-hours logic needs `zoneinfo`.
