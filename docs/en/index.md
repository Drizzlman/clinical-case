# Clinical Case Scoring Platform

Developer and maintainer documentation. It describes what this system is, how it is
built, how to run it locally, how it works internally, how it is tested, and how it is
deployed.

## What it is

A service for working with clinical cases. It:

1. **extracts** a structured case (title, questions, answer options with weights) from raw
   clinical text using an LLM;
2. **stores** the case in a normalized PostgreSQL database;
3. **exposes** an HTTP API to create/read a case and to take it with automatic scoring;
4. **renders** a web UI to take a case and see the result;
5. **measures** the quality of LLM extraction with a separate offline harness.

This is a demonstration project: authentication, roles, multi-tenancy, and medical
certification are out of scope.

## Components

| Component | Technology | Role |
|---|---|---|
| **backend** | Python 3.14, FastAPI, SQLAlchemy 2.0 (async), asyncpg, Alembic, Pydantic v2 | REST API, database schema, migrations, scoring, health/ready |
| **frontend** | Node 24, Next.js (App Router), React 19, TypeScript | Case list and run-through; server-side fetch (RSC) + client-side answer submission |
| **pipeline** | Python 3.14, `google-genai`, httpx | LLM structure extraction + offline accuracy harness; runs as a CLI / Cloud Run Job |
| **infra** | Docker, Docker Compose, GCP Cloud Run | Service images, local stacks, build and deploy scripts |

## Repository layout

```
backend/            FastAPI service: app/{api,domain,data}, tests/, alembic/, pyproject.toml
frontend/           Next.js app: src/{app,modules,lib,components}, package.json
pipeline/           LLM pipeline: app/{client,harness,input,sink,schema}, tests/, pyproject.toml
infra/              Dockerfile.*, docker-compose.{dev,prod}.yml, cloudrun/{build-and-push,deploy}.sh
.github/workflows/  CI (lint, types, tests, build)
docs/               this documentation (en + ru)
```

There is no root `package.json`: this is a monorepo of independent services, each with its
own manifest (`backend/pyproject.toml`, `pipeline/pyproject.toml`, `frontend/package.json`).

## Documentation map

- [Getting started](getting-started.md) — prerequisites, environment variables, local run (dev stack, native, prod-like).
- [Architecture](architecture.md) — backend layers, data model, frontend, pipeline, invariants.
- [Development](development.md) — toolchain, tests, conventions, CI.
- [Deployment](deployment.md) — Docker images, local prod-like stack, GCP Cloud Run, secrets.
- [HTTP API](api.md) — endpoints, request/response schemas, error format.

Russian version: [`docs/ru/`](../ru/index.md).
