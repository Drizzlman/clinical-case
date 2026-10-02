# Deployment

## Docker images

Three images are built from the repository root (build context = the root, see
`.dockerignore`). All are multi-stage, run as a non-privileged user, and listen on port
**8080**.

| Image | Dockerfile | Role |
|---|---|---|
| `clinical-backend` | `infra/Dockerfile.backend` | FastAPI + uvicorn |
| `clinical-frontend` | `infra/Dockerfile.frontend` | Next.js standalone server |
| `clinical-pipeline` | `infra/Dockerfile.pipeline` | Cloud Run Job: extraction/harness CLI |

Building by hand:

```bash
docker build -f infra/Dockerfile.backend  -t clinical-backend  .
docker build -f infra/Dockerfile.frontend --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 -t clinical-frontend .
docker build -f infra/Dockerfile.pipeline -t clinical-pipeline .
```

`NEXT_PUBLIC_API_URL` is inlined into the client bundle **at build time**; `BACKEND_URL` is
read by server components **at runtime**. This matters for the deploy order (see below).

## Local prod-like stack

Builds backend and frontend from the Dockerfiles, brings up PostgreSQL, applies migrations,
seeds demo data, and runs both services:

```bash
POSTGRES_PASSWORD=clinical docker compose -f infra/docker-compose.prod.yml up --build
```

Verify:

```bash
curl -s http://localhost:8000/health        # {"status":"ok"}
curl -s http://localhost:8000/ready         # {"status":"ready"}
curl -s http://localhost:8000/cases         # 2 cases after seeding
open http://localhost:3000                  # Windows: start http://localhost:3000
```

Stop:

```bash
docker compose -f infra/docker-compose.prod.yml down        # keep data
docker compose -f infra/docker-compose.prod.yml down -v     # + remove the PostgreSQL volume
```

## Secrets

Secrets (the database connection string, provider credentials) are supplied **only** through
the environment or Secret Manager and never end up in the image. Verify:

```bash
docker run --rm clinical-backend sh -c 'env | grep -iE "password|secret|database_url" || echo "no secrets in env"'
docker image history clinical-backend      # no lines with secrets
```

Locally/in compose the database connection is set as separate parts (`POSTGRES_USER`,
`POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`); in production it is a
single `DATABASE_URL` (Secret Manager). Both are supported, with `DATABASE_URL` taking
precedence. If required configuration is missing, the service fails at startup (fail-fast)
rather than coming up with a default `localhost`.

## Deploying to GCP Cloud Run

### 0. Prepare the project

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
export GCP_PROJECT=YOUR_PROJECT_ID

gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com aiplatform.googleapis.com --project "$GCP_PROJECT"
```

### 1. Database URL secret (Secret Manager)

`DATABASE_URL` points at an external managed PostgreSQL (Cloud SQL/Neon, etc.) — it is not
part of the images.

```bash
printf '%s' 'postgresql+asyncpg://USER:PASSWORD@HOST:5432/clinical' | \
  gcloud secrets create clinical-database-url \
    --project "$GCP_PROJECT" --replication-policy automatic --data-file=-
```

Grant the Cloud Run service account access to the secret:

```bash
gcloud secrets add-iam-policy-binding clinical-database-url \
  --project "$GCP_PROJECT" \
  --member "serviceAccount:YOUR_COMPUTE_SA@$GCP_PROJECT.iam.gserviceaccount.com" \
  --role roles/secretmanager.secretAccessor
```

> The default compute service account has access by default; a separate IAM binding is needed
> only if you specify a custom `--service-account`.

### 2. Build and push images

```bash
GCP_PROJECT=YOUR_PROJECT_ID GCP_REGION=europe-west1 TAG=v1 \
  bash infra/cloudrun/build-and-push.sh
```

The script creates the Artifact Registry repository `clinical-case` (if absent), builds and
pushes `backend`, `frontend`, and `pipeline` with tag `TAG`. For the frontend,
`NEXT_PUBLIC_API_URL` is inlined into the image (defaults to `http://localhost:8000` — set it
explicitly for production).

### 3. Deploy the services and the job

```bash
GCP_PROJECT=YOUR_PROJECT_ID GCP_REGION=europe-west1 TAG=v1 \
  DATABASE_URL='postgresql+asyncpg://...' \
  bash infra/cloudrun/deploy.sh
```

The script:

1. creates the secret (if absent) from `DATABASE_URL`;
2. deploys the backend (`--allow-unauthenticated`, `--set-secrets DATABASE_URL=...:latest`);
3. prints the backend URL;
4. deploys the frontend with `BACKEND_URL=<backend-url>`;
5. deploys the Cloud Run **Job** `clinical-pipeline` with env `GCP_PROJECT`, `GCP_LOCATION`,
   `LLM_MODEL`, `LLM_CLIENT=vertex`, `BACKEND_URL`.

### Two-pass frontend build

Because `NEXT_PUBLIC_API_URL` is inlined at build time and the backend URL is unknown up
front:

```bash
# 1. read the backend URL (after the backend is deployed)
BACKEND_URL=$(gcloud run services describe clinical-backend --region europe-west1 \
  --format 'value(status.url)')

# 2. rebuild/push the frontend with that URL and deploy it
GCP_PROJECT=YOUR_PROJECT_ID NEXT_PUBLIC_API_URL="$BACKEND_URL" TAG=v1 \
  bash infra/cloudrun/build-and-push.sh
GCP_PROJECT=YOUR_PROJECT_ID TAG=v1 bash infra/cloudrun/deploy.sh
```

### 4. Verify the deployment

```bash
curl -fsS "$(gcloud run services describe clinical-backend --region europe-west1 --format 'value(status.url)')/health"

gcloud run jobs execute clinical-pipeline --region europe-west1 --wait
gcloud run jobs executions list --job clinical-pipeline --region europe-west1
```

Expected: `/health` → `200 {"status":"ok"}`; the job exits with code 0 and prints the harness
table to the logs (`gcloud run jobs executions logs <execution>`).

## Acceptance checklist

- [ ] linters/types/tests/build are green (see [Development](development.md) and CI)
- [ ] backend: `GET /health` → 200, `GET /ready` → 200 with a live DB
- [ ] `POST /cases` → `GET /cases/{id}` → `POST /cases/{id}/submissions` returns a score
- [ ] frontend: case list → run-through → result, responsive without horizontal scroll
- [ ] `python -m app.harness.runner` prints per-field P/R/F1 (on mock = `1.000`)
- [ ] locally `POSTGRES_PASSWORD=clinical docker compose -f infra/docker-compose.prod.yml up --build` brings up the stack
- [ ] images contain no secrets; `/health` responds on Cloud Run
- [ ] `gcloud run jobs execute clinical-pipeline` completes successfully

## Troubleshooting

- **`/ready` → 503** — PostgreSQL is unreachable or `DATABASE_URL`/`POSTGRES_*` is wrong.
  Check `docker compose ps` and the connection string.
- **Frontend empty or 500 on RSC** — `BACKEND_URL` is not set (on Cloud Run it is the
  frontend service env; locally it defaults to `http://localhost:8000`).
- **Client requests from the frontend go to the wrong place** — `NEXT_PUBLIC_API_URL` is
  inlined at build time; rebuild the frontend (see Two-pass).
- **`DATABASE_URL must be provided` at startup** — this is fail-fast: set the secret and
  `--set-secrets`; the service intentionally does not start with a default localhost.
- **`docker build` fails on `COPY .../public`** — the repository has `frontend/public/`
  (with `.gitkeep`); do not remove it.
- **Windows: `bash` launches WSL** — use the full path to Git Bash
  (`...\Git\bin\bash.exe`) rather than `bash script.sh`.
- **Compose: `POSTGRES_PASSWORD must be set`** — provide `POSTGRES_PASSWORD` (in the
  environment or the root `.env`); it has no default.
