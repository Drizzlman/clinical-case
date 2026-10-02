# Архитектура

## Обзор

Три независимых сервиса в одном монорепозитории:

```
                       ┌─────────────────────────┐
   сырой текст  ─────▶ │  pipeline (LLM+harness) │ ──POST /cases──┐
                       └─────────────────────────┘                │
                                                                  ▼
   браузер ──▶ frontend (Next.js) ──RSC/HTTP──▶ backend (FastAPI) ──▶ PostgreSQL
                       ▲                          (scoring, API)
                       └──── GET/POST ────────────┘
```

- **backend** — единственный владелец схемы БД и правил подсчёта баллов.
- **frontend** — рендерит кейс (серверно, RSC) и отправляет ответы (клиентски).
- **pipeline** — извлекает кейс из текста и измеряет качество извлечения; не имеет своей БД.

## Backend — ports & adapters

Слои строго направлены: `api → domain → data`. Зависимости идут внутрь, домен не знает
о фреймворках.

| Слой | Каталог | Ответственность |
|---|---|---|
| API | `backend/app/api/` | маршруты, Pydantic-схемы, DI, маппинг, обработка ошибок |
| Domain | `backend/app/domain/` | сущности, use cases, правила подсчёта, порты (Protocol). **Без** FastAPI/SQLAlchemy/Pydantic |
| Data | `backend/app/data/` | SQLAlchemy-модели, репозитории-адаптеры, сессии, health-probe |

- **Порты** — протоколы в `domain/ports.py` (`CaseRepository`, `SubmissionRepository`,
  `HealthProbe`). **Адаптеры** — SQLAlchemy-реализации в `data/repositories.py`.
- **Композиция** — `api/deps.py` связывает конкретные адаптеры с use case'ами через
  FastAPI `Depends`; каждый use case получает репозиторий в конструктор.
- **Use cases** (`domain/use_cases/`): `CreateCase`, `GetCase`, `ListCases`,
  `SubmitAnswers`, `GetSubmission`.
- **Тесты use-case** используют in-memory адаптеры (`backend/tests/fakes.py`) — без БД и
  Docker. Границы слоёв проверяет `import-linter` (см. `backend/pyproject.toml`).

## Модель данных

Нормализованная схема (миграция `backend/alembic/versions/0001_initial.py`):

```
cases ──< questions ──< answer_options
  └──< submissions ──< submission_answers ──(FK)──> answer_options
```

| Таблица | Ключевые поля |
|---|---|
| `cases` | `id`, `title`, `description`, `created_at`, `updated_at` |
| `questions` | `id`, `case_id`, `text`, `kind`, `position` (уникально в рамках кейса) |
| `answer_options` | `id`, `question_id`, `text`, `score ≥ 0`, `position` |
| `submissions` | `id`, `case_id`, `created_at` |
| `submission_answers` | `id`, `submission_id`, `question_id`, `option_id` |

Ключевая защита на уровне БД: составной внешний ключ
`submission_answers(option_id, question_id) → answer_options(id, question_id)` —
выбранный вариант **гарантированно** принадлежит своему вопросу, независимо от кода
приложения. Плюс `CHECK (score >= 0)` и уникальности `(case_id, position)` /
`(question_id, position)`.

## Подсчёт баллов

Правила — в `domain/scoring.py` (чистая функция, без фреймворков):

- по каждому вопросу берётся балл выбранного варианта (`score`);
- максимум вопроса — максимальный балл среди его вариантов;
- итог: `earned`, `maximum`, `percentage = earned / maximum * 100` (округление
  `ROUND_HALF_UP` до 2 знаков; при `maximum == 0` → `0`);
- ответы обязаны покрывать **ровно** вопросы кейса, вариант — принадлежать своему вопросу,
  иначе `DomainValidationError`.

## Обработка ошибок (API)

Единый формат `application/problem+json` (RFC 7807-совместимо), `backend/app/api/errors.py`:

| Статус | `type` | Когда |
|---|---|---|
| `422` | `validation_error` | не прошла валидация Pydantic (тело запроса) |
| `422` | `domain_validation_error` | нарушено доменное правило (неполные/некорректные ответы) |
| `404` | `not_found` | кейс/сабмишен не найден |

## Frontend — FSD + Clean-слои

Модули по фичам: `src/modules/{common,case}/{data,domain,ui}`. Поток данных
однонаправленный: `ui → domain → data`.

- **data** — единственное место `fetch` (`modules/case/data/case-repository.ts`); базовый
  URL выбирается в `modules/common/data/api-base-url.ts`:
  - на сервере (RSC) → `BACKEND_URL ?? NEXT_PUBLIC_API_URL ?? http://localhost:8000`;
  - в браузере → `NEXT_PUBLIC_API_URL ?? http://localhost:8000`.
- **domain** — модели, use case'ы (`list-cases`, `get-case`, `submit-answers`), фасад.
- **ui** — чистые компоненты (`CaseList`, `CaseRunner`, `QuestionCard`, `AttemptPanel`,
  `ResultPanel`) и view-model `use-case-runner-vm.ts`; примитивы — `modules/common/ui/*`.

Результат операций — `OperationResult` (`Success` / `Failure`); исключения через границу
репозитория не пробрасываются, `Failure.status` (напр. 404) обрабатывается вызывающим
кодом. Серверный загрузчик `modules/case/server/load.ts` оборачивает use case'ы в
`React.cache()` (дедуп между `generateMetadata` и страницей) и в `withMinimumDelay`
(минимальная длительность загрузки, чтобы скелетон не мигал).

Страницы (`src/app/`) — серверные компоненты с `export const dynamic = "force-dynamic"`;
единственный клиентский остров — `CaseRunner` (данные приходят пропсами).

## Pipeline

Провайдер-агностичный порт `LLMClient` (`app/client/base.py`) — единственный способ
дотянуться до LLM. Адаптеры:

- `MockLLMClient` — читает детерминированные фикстуры из `tests/golden/` (офлайн);
- `VertexLLMClient` — Google Gen AI (Vertex AI через ADC по умолчанию; Developer API по
  `GEMINI_API_KEY`). SDK `google-genai` импортируется **только** здесь.

Оркестрация `extract_case` (`app/extract.py`): вызов LLM → валидация схемы → один ремонт
по подсказке об ошибке → при неудаче типизированная `ExtractionError` (частичный результат
не возвращается).

Харнес (`app/harness/runner.py`) прогоняет клиент по golden-набору и считает per-field
precision/recall/F1 для вопросов и вариантов + `score_accuracy`. CLI `python -m app.cli`
поддерживает `extract` (вход: файл/stdin, опц. `--post` в backend) и `harness`.

## Конфигурация

`pydantic-settings`, `env_file` — абсолютный путь от `__file__` (не от CWD), чтобы
конфигурация не зависела от рабочего каталога. Construction ленивый (`@lru_cache
get_settings()`), поэтому импорт модуля не требует env; в тестах переменные задаются
через `os.environ.setdefault` (`backend/tests/conftest.py`).

## Инварианты

| ID | Требование | Где проверяется |
|---|---|---|
| INV-1 | весь доступ к БД — через data/repository-слой; в API нет сырого SQL | `import-linter`, ревью |
| INV-2 | публичный JSON-контракт (Pydantic) меняется только additive | snapshot OpenAPI в тестах |
| INV-3 | секреты только из env/Secret Manager, не в коде и логах | `gitleaks` в CI |
| INV-4 | нет блокирующего I/O в async-путях (без sync-драйвера БД) | зависимости/ревью |
| INV-5 | типы API для фронта генерируются из OpenAPI, не дублируются | `npm run check:api` |
| INV-6 | все вызовы LLM — через `LLMClient`; SDK провайдера только в адаптере | `import-linter` (pipeline) |
