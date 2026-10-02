# Getting started

## Prerequisites

- **Docker Desktop** (engine running) — `docker version`, `docker compose version`.
- **Python 3.14** (for native runs and tests) — `python --version`.
- **Node 24 + npm** — `node --version`.
- **Git Bash** on Windows — run all `.sh` scripts from it, not from PowerShell or WSL.
- _(optional, for deployment and the real LLM)_ **Google Cloud SDK** — `gcloud --version`.

## Environment variables

Nothing is hardcoded: each service reads its own variables through `pydantic-settings`. A
missing required variable makes the service fail at startup (fail-fast) instead of coming up
with a wrong configuration.

### Backend (`backend/.env`)

```bash
cp backend/.env.example backend/.env
```

| Variable | Purpose |
|---|---|
| `ENVIRONMENT` | environment (`development` / `production` / `test`) |
| `CORS_ORIGINS` | JSON array of allowed origins, e.g. `["http://localhost:3000"]` |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_HOST` / `POSTGRES_PORT` / `POSTGRES_DB` | individual connection parts (local/compose) |
| `DATABASE_URL` | single `postgresql+asyncpg://...` string; takes precedence over `POSTGRES_*` (production/Secret Manager) |

Either `DATABASE_URL` or **all** `POSTGRES_*` must be set.

### Pipeline (`pipeline/.env`)

```bash
cp pipeline/.env.example pipeline/.env
```

| Variable | Purpose |
|---|---|
| `GCP_PROJECT`, `GCP_LOCATION`, `LLM_MODEL` | LLM provider settings |
| `LLM_CLIENT` | `mock` (offline fixtures) or `vertex` (real Gemini) |
| `BACKEND_URL` | backend base URL for pushing a case (`--post`) |
| `GEMINI_API_KEY` | optional: Developer API key for local work without ADC |

### Frontend

| Variable | Purpose |
|---|---|
| `BACKEND_URL` | backend URL for **server-side** requests (RSC); in Docker — `http://backend:8080` |
| `NEXT_PUBLIC_API_URL` | backend URL for **browser** requests; in the browser — `http://localhost:8000` |
| `MIN_PAGE_LOAD_MS` | optional: minimum page-load duration (default `2000`) |

### Root `.env` (for Docker Compose)

Compose interpolates variables from the root `.env`. The key variable is
**`POSTGRES_PASSWORD`**: it is required and has no default (a weak password is never
silently substituted). Example for local development:

```bash
POSTGRES_USER=clinical
POSTGRES_PASSWORD=clinical
POSTGRES_DB=clinical
```

Never commit real `.env` files — they are in `.gitignore`.

## Mode 1 — full dev stack in Docker (recommended)

One command brings up PostgreSQL + backend (`uvicorn --reload`) + frontend (`next dev`).
Sources are bind-mounted into the containers, so edits reload without a rebuild.

```bash
POSTGRES_PASSWORD=clinical docker compose -f infra/docker-compose.dev.yml up --build
```

Verify:

```bash
curl -s http://localhost:8000/health        # {"status":"ok"}
curl -s http://localhost:8000/ready         # {"status":"ready"} (DB reachable)
curl -s http://localhost:8000/cases         # 2 demo cases (seeded on backend start)
open http://localhost:3000                  # Windows: start http://localhost:3000
```

Stop:

```bash
docker compose -f infra/docker-compose.dev.yml down        # keep data
docker compose -f infra/docker-compose.dev.yml down -v     # + remove the DB volume
```

Overridable ports: `POSTGRES_PORT` (5432), `BACKEND_PORT` (8000), `FRONTEND_PORT` (3000).
Inside Docker the frontend reaches the backend at `http://backend:8080`.

Database only (with backend/frontend running natively — see Mode 2):

```bash
POSTGRES_PASSWORD=clinical docker compose -f infra/docker-compose.dev.yml up -d postgres
```

## Mode 2 — native run (fast IDE cycle)

The app runs on the host; only PostgreSQL runs in Docker.

```bash
# 1. Database
POSTGRES_PASSWORD=clinical docker compose -f infra/docker-compose.dev.yml up -d postgres

# 2. Backend
cd backend
python -m venv .venv                                   # if .venv does not exist yet
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m alembic upgrade head       # database schema
.venv/Scripts/python.exe -m app.seed                   # 2 demo cases (idempotent)
.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000

# 3. Frontend (in a separate terminal)
cd frontend
npm install
npm run dev                                            # http://localhost:3000
```

On Linux/macOS the interpreter is `.venv/bin/python` instead of `.venv/Scripts/python.exe`.

## Mode 3 — prod-like stack (real images)

Builds backend and frontend from the Dockerfiles, applies migrations, seeds demo data, and
runs the services — as close to production as it gets locally.

```bash
POSTGRES_PASSWORD=clinical docker compose -f infra/docker-compose.prod.yml up --build
```

Details, the "no secrets in the image" check, the acceptance checklist, and troubleshooting
are in [Deployment](deployment.md).

## Manual E2E scenario

1. Open `http://localhost:3000` — the list of demo cases should appear.
2. Open a case → answer the questions → **Submit**.
3. Expected: the page switches to review mode, shows the known score, and highlights correct
   / incorrect options.
4. Check a narrow viewport (DevTools → mobile): no horizontal scroll.

## Next steps

- How the system works — [Architecture](architecture.md).
- How to run tests and linters — [Development](development.md).
- Deploying to GCP — [Deployment](deployment.md).
