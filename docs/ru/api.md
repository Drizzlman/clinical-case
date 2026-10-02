# HTTP API

Базовый URL локально: `http://localhost:8000`. Взаимодействие — JSON; формат ошибок —
`application/problem+json`. Публичный контракт задаётся Pydantic-моделями
(`backend/app/api/schemas.py`) и меняется только обратно совместимо (INV-2). Снимок
OpenAPI лежит в `backend/tests/openapi.json`, из него генерируются TypeScript-типы фронта
([INV-5](architecture.md)).

CORS: разрешены методы `GET`/`POST`, заголовок `Content-Type`, origin'ы — из
`CORS_ORIGINS`.

## Эндпоинты

| Метод | Путь | Назначение | Успех |
|---|---|---|---|
| `GET` | `/health` | liveness (процесс жив, без зависимостей) | `200 {"status":"ok"}` |
| `GET` | `/ready` | readiness (БД доступна) | `200 {"status":"ready"}` / `503 {"status":"unavailable"}` |
| `GET` | `/cases` | список кейсов (кратко) | `200 [CaseSummary]` |
| `POST` | `/cases` | создать кейс | `201 Case` |
| `GET` | `/cases/{case_id}` | получить кейс целиком | `200 Case` |
| `POST` | `/cases/{case_id}/submissions` | отправить ответы, получить балл | `201 SubmissionResult` |
| `GET` | `/submissions/{submission_id}` | получить результат попытки | `200 SubmissionResult` |

## Схемы

### Создание кейса — `POST /cases`

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

Правила: `title` непустой; минимум один вопрос; у вопроса минимум **два** варианта;
`score ≥ 0`; `kind` по умолчанию `single_choice`; `position` опционален (порядок по
умолчанию — как в запросе; в рамках кейса позиции уникальны).

### Кейс — `Case` (`GET /cases/{id}`, ответ на `POST`)

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

### Краткий кейс — `CaseSummary` (элемент `GET /cases`)

```json
{ "id": 1, "title": "Myocardial infarction", "description": "58-year-old with chest pain", "question_count": 3 }
```

### Отправка ответов — `POST /cases/{case_id}/submissions`

```json
{ "answers": [ { "question_id": 1, "option_id": 1 } ] }
```

Ответы должны покрывать **ровно** все вопросы кейса; каждый вопрос — не более одного раза;
`option_id` должен принадлежать указанному `question_id`.

### Результат — `SubmissionResult`

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

Баллы — `Decimal`; `percentage = earned / maximum * 100` (2 знака, `ROUND_HALF_UP`; при
`maximum == 0` → `0`). Подробнее — [Архитектура → Подсчёт баллов](architecture.md#подсчёт-баллов).

## Ошибки

Тело ошибки — `application/problem+json`:

```json
{ "type": "validation_error", "title": "Request validation failed", "errors": [ ... ] }
```

| Статус | `type` | Причина |
|---|---|---|
| `422` | `validation_error` | не прошла валидация тела запроса Pydantic |
| `422` | `domain_validation_error` | нарушено доменное правило (неполные/некорректные ответы) |
| `404` | `not_found` | кейс/сабмишен не найден |

## Примеры

```bash
# создать кейс
curl -s -X POST http://localhost:8000/cases \
  -H 'content-type: application/json' \
  -d '{"title":"MI","questions":[{"text":"Diagnosis?","options":[{"text":"MI","score":1},{"text":"Angina","score":0}]}]}'

# прочитать кейс
curl -s http://localhost:8000/cases/1

# отправить ответы
curl -s -X POST http://localhost:8000/cases/1/submissions \
  -H 'content-type: application/json' \
  -d '{"answers":[{"question_id":1,"option_id":1}]}'
```
