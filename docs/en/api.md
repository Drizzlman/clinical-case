# HTTP API

Base URL locally: `http://localhost:8000`. The interaction is JSON; errors use the
`application/problem+json` format. The public contract is defined by Pydantic models
(`backend/app/api/schemas.py`) and changes only in a backward-compatible way (INV-2). The
OpenAPI snapshot lives in `backend/tests/openapi.json`; the frontend TypeScript types are
generated from it ([INV-5](architecture.md)).

CORS: methods `GET`/`POST`, header `Content-Type`, and origins from `CORS_ORIGINS`.

## Endpoints

| Method | Path | Purpose | Success |
|---|---|---|---|
| `GET` | `/health` | liveness (process up, no dependencies) | `200 {"status":"ok"}` |
| `GET` | `/ready` | readiness (DB reachable) | `200 {"status":"ready"}` / `503 {"status":"unavailable"}` |
| `GET` | `/cases` | list cases (summaries) | `200 [CaseSummary]` |
| `POST` | `/cases` | create a case | `201 Case` |
| `GET` | `/cases/{case_id}` | get a full case | `200 Case` |
| `POST` | `/cases/{case_id}/submissions` | submit answers, get the score | `201 SubmissionResult` |
| `GET` | `/submissions/{submission_id}` | get a submission result | `200 SubmissionResult` |

## Schemas

### Create case — `POST /cases`

```json
{
  "title": "Myocardial infarction",
  "description": "58-year-old with chest pain",
  "questions": [
    {
      "text": "Most likely diagnosis?",
      "kind": "single_choice",
      "position": 1,
      "options": [
        { "text": "MI", "score": 1, "position": 1 },
        { "text": "Angina", "score": 0, "position": 2 }
      ]
    }
  ]
}
```

Rules: `title` non-empty; at least one question; each question has at least **two** options;
`score ≥ 0`; `kind` defaults to `single_choice`; `position` is optional (default order is the
request order; positions are unique within a case).

### Case — `Case` (`GET /cases/{id}`, `POST /cases` response)

```json
{
  "id": 1,
  "title": "Myocardial infarction",
  "description": "58-year-old with chest pain",
  "questions": [
    {
      "id": 1,
      "text": "Most likely diagnosis?",
      "kind": "single_choice",
      "position": 1,
      "options": [
        { "id": 1, "text": "MI", "score": 1, "position": 1 },
        { "id": 2, "text": "Angina", "score": 0, "position": 2 }
      ]
    }
  ]
}
```

### Case summary — `CaseSummary` (item of `GET /cases`)

```json
{ "id": 1, "title": "Myocardial infarction", "description": "58-year-old with chest pain", "question_count": 3 }
```

### Submit answers — `POST /cases/{case_id}/submissions`

```json
{ "answers": [ { "question_id": 1, "option_id": 1 } ] }
```

Answers must cover **exactly** all of the case's questions; each question at most once; and
each `option_id` must belong to the given `question_id`.

### Result — `SubmissionResult`

```json
{
  "id": 1,
  "case_id": 1,
  "earned": 1,
  "maximum": 1,
  "percentage": 100.0,
  "per_question": [
    { "question_id": 1, "selected_option_id": 1, "score": 1, "max_score": 1 }
  ]
}
```

Scores are `Decimal`; `percentage = earned / maximum * 100` (2 decimals, `ROUND_HALF_UP`;
`0` when `maximum == 0`). See [Architecture → Scoring](architecture.md#scoring).

## Errors

The error body is `application/problem+json`:

```json
{ "type": "validation_error", "title": "Request validation failed", "errors": [ ... ] }
```

| Status | `type` | Cause |
|---|---|---|
| `422` | `validation_error` | Pydantic request-body validation failed |
| `422` | `domain_validation_error` | a domain rule was violated (incomplete/incorrect answers) |
| `404` | `not_found` | case/submission not found |

## Examples

```bash
# create a case
curl -s -X POST http://localhost:8000/cases \
  -H 'content-type: application/json' \
  -d '{"title":"MI","questions":[{"text":"Diagnosis?","options":[{"text":"MI","score":1},{"text":"Angina","score":0}]}]}'

# read a case
curl -s http://localhost:8000/cases/1

# submit answers
curl -s -X POST http://localhost:8000/cases/1/submissions \
  -H 'content-type: application/json' \
  -d '{"answers":[{"question_id":1,"option_id":1}]}'
```
