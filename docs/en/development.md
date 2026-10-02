# Development

## Toolchain

| Service | Lint | Types | Tests | Build |
|---|---|---|---|---|
| backend | `ruff check --config backend/pyproject.toml backend` | `mypy --config-file backend/pyproject.toml backend` | `pytest -c backend/pyproject.toml backend/tests` | — |
| backend (boundaries) | `lint-imports` (from `backend/`) | | | |
| pipeline | `ruff check --config pipeline/pyproject.toml pipeline` | `mypy --config-file pipeline/pyproject.toml pipeline` | `pytest -c pipeline/pyproject.toml pipeline/tests` | — |
| pipeline (boundaries) | `lint-imports` (from `pipeline/`) | | | |
| frontend | `npm run lint` | `npm run typecheck` | `npm test` | `npm run build` |

Install the environments:

```bash
pip install -e "backend[dev]"
pip install -e "pipeline[dev]"

cd frontend && npm ci
```

## Tests

The tests are **hermetic**: they need neither PostgreSQL, nor Docker, nor a running backend.

- **backend / unit** — business logic on in-memory repositories (`backend/tests/fakes.py`),
  no database.
- **backend / api** — the real ASGI app through `httpx.ASGITransport`, with
  `get_case_repository` overridden by an in-memory adapter (`dependency_overrides`).
- **backend / migration** — the migration is rendered to DDL offline (`alembic upgrade
  --sql`); it asserts the tables, the `CHECK (score >= 0)`, and the composite foreign key.
- **backend / conftest** — provides the required env variables via `os.environ.setdefault`
  so tests run without `backend/.env`.
- **frontend** — vitest + jsdom + `@testing-library/react`; `npm test` also runs the API-type
  drift check.
- **pipeline** — CLI, extraction (valid/repair/error), harness, sinks, and the Vertex adapter
  with an injected client (no network).

Offline extraction-quality harness (mock adapter, no GCP):

```bash
cd pipeline
.venv/Scripts/python.exe -m app.harness.runner --golden tests/golden --out report.json
```

Expected: a table `case / q_P q_R q_F1 / o_P o_R o_F1 / score` and an `AGGREGATE` row with
values `1.000` (mock returns the reference fixtures).

## API type generation (INV-5)

The backend contract is the OpenAPI snapshot `backend/tests/openapi.json`. Client types are
generated from it, not written by hand:

```bash
cd frontend
npm run gen:api      # regenerate src/lib/api-types.ts
npm run check:api    # verify the file has not drifted from the contract (part of npm test)
```

When the public backend contract changes, regenerate the snapshot and the types, otherwise
`check:api` fails in CI.

## Conventions

- **Backend** — layers `api → domain → data`; ORM only in `data`; the domain stays
  framework-free. `ruff` (line-length 100) + `mypy` strict + `import-linter` contracts. New
  use cases come with tests on in-memory adapters.
- **Frontend** — strict TypeScript, ESLint with a mandatory
  `explicit-function-return-type`; components are presentational, logic lives in
  domain/use-case, and networking only in the data repository; alias `@/*` → `src/*`.
- **Pipeline** — the provider SDK is isolated in `client/vertex.py` (INV-6); errors are typed
  (`PipelineError` and subclasses), and raw text and secrets never reach the logs.

## Continuous integration (CI)

`.github/workflows/ci.yml` runs on push to `main` and on pull requests. Jobs:

| Job | Runtime | Steps |
|---|---|---|
| `secrets` | ubuntu | `gitleaks` — secret-leak scan |
| `backend` | Python **3.12** | `pip install -e "backend[dev]"` → ruff → mypy → `lint-imports` → pytest |
| `pipeline` | Python **3.12** | `pip install -e "pipeline[dev]"` → ruff → mypy → `lint-imports` → pytest |
| `frontend` | Node **22** | `npm ci` → lint → typecheck → test → build |

> CI intentionally tests the **minimum supported** Python (`requires-python >=3.12`) and
> Node 22, whereas the Docker images and the local dev stack are built on Python 3.14 and
> Node 24. If you change the minimum version, update the CI matrix too.

## Local check before committing

Repeat the CI job steps for the services you touched (commands from the "Toolchain" and
"CI" tables). For the frontend, `npm test` (includes the drift check) + `npm run build` is
enough; for the backend, `pytest` + linters; for the pipeline, `pytest` + linters.
