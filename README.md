# Clinical Case Scoring Platform

A demonstration platform for working with clinical cases. It turns raw clinical text into a
structured, scored case, stores it in PostgreSQL, serves it over a typed HTTP API, renders a
web UI to take the case, and measures the quality of the LLM extraction with an offline
harness.

> This is a demo/educational project. Authentication, roles, multi-tenancy, and medical
> certification are out of scope.

## What it does

- **Extraction pipeline** — raw clinical text → structured case (title, questions, answer
  options with weights) using a provider-agnostic LLM client, with schema validation and a
  repair attempt.
- **REST API** — create/read a case, submit answers, and get a deterministic score.
- **Web UI** — a case list and a run-through flow rendered with Next.js Server Components,
  with client-side answer submission.
- **Accuracy harness** — per-field precision/recall/F1 over a golden set.

## Architecture

Three independent services in one monorepo:

```
pipeline (LLM + harness) ──POST /cases──▶ backend (FastAPI) ──▶ PostgreSQL
                                              ▲
                          browser ──▶ frontend (Next.js, RSC)
```

| Component | Stack | Responsibility |
|---|---|---|
| `backend/` | Python 3.14 · FastAPI · SQLAlchemy 2.0 async · Alembic · Pydantic v2 | API, schema, migrations, scoring |
| `frontend/` | Node 24 · Next.js (App Router) · React 19 · TypeScript | Case list and run-through |
| `pipeline/` | Python 3.14 · google-genai · httpx | LLM extraction + offline harness |
| `infra/` | Docker · Docker Compose · GCP Cloud Run | Images, local stacks, deploy scripts |

The backend follows **ports & adapters**: `api → domain → data`, with framework-free domain
logic and SQLAlchemy confined to the data layer. The frontend follows **FSD + Clean layers**
(`modules/{common,case}/{data,domain,ui}`). See [Architecture](docs/en/architecture.md).

## Quick start

Prerequisites: Docker Desktop, Git Bash (Windows). For native runs: Python 3.14 and Node 24.

```bash
# Full dev stack with hot reload (postgres + backend + frontend)
POSTGRES_PASSWORD=clinical docker compose -f infra/docker-compose.dev.yml up --build

# backend  http://localhost:8000/health
# frontend http://localhost:3000
```

Other modes (native run, prod-like stack) and environment variables are covered in
[Getting started](docs/en/getting-started.md).

## Development

```bash
pip install -e "backend[dev]"      # backend toolchain
pip install -e "pipeline[dev]"     # pipeline toolchain
cd frontend && npm ci              # frontend toolchain
```

Tests are hermetic — no database or Docker required. Lint/type/test/build commands per
service and the CI matrix are documented in [Development](docs/en/development.md).

## Deployment

Images are built from `infra/Dockerfile.*`; `infra/docker-compose.prod.yml` runs a local
prod-like stack; `infra/cloudrun/*.sh` build, push, and deploy to GCP Cloud Run with secrets
from Secret Manager. See [Deployment](docs/en/deployment.md).

## Documentation

- English: [`docs/en/`](docs/en/index.md)
- Русский: [`docs/ru/`](docs/ru/index.md)
- HTTP API: [`docs/en/api.md`](docs/en/api.md)

## Repository layout

```
backend/    FastAPI service (app/{api,domain,data}, tests/, alembic/)
frontend/   Next.js app (src/{app,modules,lib,components})
pipeline/   LLM extraction + harness (app/{client,harness,input,sink,schema})
infra/      Dockerfiles, compose stacks, Cloud Run scripts
docs/       Developer documentation (en + ru)
```
