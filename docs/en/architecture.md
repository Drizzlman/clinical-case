# Architecture

## Overview

Three independent services in one monorepo:

```
                       ┌─────────────────────────┐
   raw text   ───────▶ │  pipeline (LLM+harness) │ ──POST /cases──┐
                       └─────────────────────────┘                │
                                                                  ▼
   browser ──▶ frontend (Next.js) ──RSC/HTTP──▶ backend (FastAPI) ──▶ PostgreSQL
                       ▲                          (scoring, API)
                       └──── GET/POST ────────────┘
```

- **backend** — the single owner of the database schema and the scoring rules.
- **frontend** — renders the case (server-side, RSC) and submits answers (client-side).
- **pipeline** — extracts a case from text and measures extraction quality; it has no
  database of its own.

## Backend — ports & adapters

Layers point strictly inward: `api → domain → data`. The domain knows nothing about the
frameworks.

| Layer | Directory | Responsibility |
|---|---|---|
| API | `backend/app/api/` | routes, Pydantic schemas, DI, mapping, error handling |
| Domain | `backend/app/domain/` | entities, use cases, scoring rules, ports (Protocol). **No** FastAPI/SQLAlchemy/Pydantic |
| Data | `backend/app/data/` | SQLAlchemy models, repository adapters, sessions, health probe |

- **Ports** — protocols in `domain/ports.py` (`CaseRepository`, `SubmissionRepository`,
  `HealthProbe`). **Adapters** — SQLAlchemy implementations in `data/repositories.py`.
- **Composition** — `api/deps.py` wires concrete adapters to use cases via FastAPI
  `Depends`; each use case receives its repository through the constructor.
- **Use cases** (`domain/use_cases/`): `CreateCase`, `GetCase`, `ListCases`,
  `SubmitAnswers`, `GetSubmission`.
- **Use-case tests** use in-memory adapters (`backend/tests/fakes.py`) — no database, no
  Docker. Layer boundaries are checked by `import-linter` (see `backend/pyproject.toml`).

## Data model

Normalized schema (migration `backend/alembic/versions/0001_initial.py`):

```
cases ──< questions ──< answer_options
  └──< submissions ──< submission_answers ──(FK)──> answer_options
```

| Table | Key columns |
|---|---|
| `cases` | `id`, `title`, `description`, `created_at`, `updated_at` |
| `questions` | `id`, `case_id`, `text`, `kind`, `position` (unique per case) |
| `answer_options` | `id`, `question_id`, `text`, `score ≥ 0`, `position` |
| `submissions` | `id`, `case_id`, `created_at` |
| `submission_answers` | `id`, `submission_id`, `question_id`, `option_id` |

Key database-level protection: the composite foreign key
`submission_answers(option_id, question_id) → answer_options(id, question_id)` guarantees
that the selected option **belongs** to its question, regardless of application code. Plus
`CHECK (score >= 0)` and the unique constraints on `(case_id, position)` /
`(question_id, position)`.

## Scoring

The rules live in `domain/scoring.py` (a pure, framework-free function):

- for each question, the selected option's score is taken;
- a question's maximum is the highest score among its options;
- totals: `earned`, `maximum`, `percentage = earned / maximum * 100` (rounded
  `ROUND_HALF_UP` to 2 decimals; when `maximum == 0` → `0`);
- answers must cover **exactly** the case's questions and reference options that belong to
  their question, otherwise `DomainValidationError`.

## Error handling (API)

A single `application/problem+json` format (RFC 7807-compatible),
`backend/app/api/errors.py`:

| Status | `type` | When |
|---|---|---|
| `422` | `validation_error` | Pydantic request-body validation failed |
| `422` | `domain_validation_error` | a domain rule was violated (incomplete/incorrect answers) |
| `404` | `not_found` | case/submission not found |

## Frontend — FSD + Clean layers

Feature modules: `src/modules/{common,case}/{data,domain,ui}`. Data flows one way:
`ui → domain → data`.

- **data** — the only place that calls `fetch` (`modules/case/data/case-repository.ts`); the
  base URL is chosen in `modules/common/data/api-base-url.ts`:
  - on the server (RSC) → `BACKEND_URL ?? NEXT_PUBLIC_API_URL ?? http://localhost:8000`;
  - in the browser → `NEXT_PUBLIC_API_URL ?? http://localhost:8000`.
- **domain** — models, use cases (`list-cases`, `get-case`, `submit-answers`), facade.
- **ui** — presentational components (`CaseList`, `CaseRunner`, `QuestionCard`,
  `AttemptPanel`, `ResultPanel`) and the view model `use-case-runner-vm.ts`; primitives live
  in `modules/common/ui/*`.

Operation results are an `OperationResult` (`Success` / `Failure`); exceptions do not cross
the repository boundary, and `Failure.status` (e.g. 404) is handled by the caller. The
server loader `modules/case/server/load.ts` wraps use cases in `React.cache()` (dedupes
`generateMetadata` and the page) and in `withMinimumDelay` (minimum load time so the
skeleton does not flicker).

Pages (`src/app/`) are server components with `export const dynamic = "force-dynamic"`; the
single client island is `CaseRunner` (data arrives as props).

## Pipeline

The provider-agnostic `LLMClient` port (`app/client/base.py`) is the only way to reach an
LLM. Adapters:

- `MockLLMClient` — reads deterministic fixtures from `tests/golden/` (offline);
- `VertexLLMClient` — Google Gen AI (Vertex AI via ADC by default; Developer API when
  `GEMINI_API_KEY` is set). The `google-genai` SDK is imported **only** here.

Orchestration `extract_case` (`app/extract.py`): call the LLM → validate the schema → one
repair attempt driven by the validation error → on failure a typed `ExtractionError` (a
partial result is never returned).

The harness (`app/harness/runner.py`) runs the client over the golden set and computes
per-field precision/recall/F1 for questions and options plus `score_accuracy`. The CLI
`python -m app.cli` supports `extract` (input: file/stdin, optional `--post` to the backend)
and `harness`.

## Configuration

`pydantic-settings`, with `env_file` set to an absolute path derived from `__file__` (not the
CWD) so configuration does not depend on the working directory. Construction is lazy
(`@lru_cache get_settings()`), so importing a module does not require env; in tests the
variables are provided via `os.environ.setdefault` (`backend/tests/conftest.py`).

## Invariants

| ID | Requirement | Checked by |
|---|---|---|
| INV-1 | all DB access goes through the data/repository layer; no raw SQL in the API | `import-linter`, review |
| INV-2 | the public JSON contract (Pydantic) changes only additively | OpenAPI snapshot test |
| INV-3 | secrets only from env/Secret Manager, never in code or logs | `gitleaks` in CI |
| INV-4 | no blocking I/O in async paths (no sync DB driver) | dependencies/review |
| INV-5 | API types for the frontend are generated from OpenAPI, not hand-written | `npm run check:api` |
| INV-6 | all LLM calls go through `LLMClient`; the provider SDK lives only in the adapter | `import-linter` (pipeline) |
