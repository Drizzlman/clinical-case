# Разработка

## Тулчейн

| Сервис | Линт | Типы | Тесты | Сборка |
|---|---|---|---|---|
| backend | `ruff check --config backend/pyproject.toml backend` | `mypy --config-file backend/pyproject.toml backend` | `pytest -c backend/pyproject.toml backend/tests` | — |
| backend (границы) | `lint-imports` (из `backend/`) | | | |
| pipeline | `ruff check --config pipeline/pyproject.toml pipeline` | `mypy --config-file pipeline/pyproject.toml pipeline` | `pytest -c pipeline/pyproject.toml pipeline/tests` | — |
| pipeline (границы) | `lint-imports` (из `pipeline/`) | | | |
| frontend | `npm run lint` | `npm run typecheck` | `npm test` | `npm run build` |

Установка окружений:

```bash
pip install -e "backend[dev]"
pip install -e "pipeline[dev]"

cd frontend && npm ci
```

## Тесты

Тесты **герметичны**: им не нужны ни PostgreSQL, ни Docker, ни запущенный backend.

- **backend / unit** — бизнес-логика на in-memory репозиториях
  (`backend/tests/fakes.py`), без БД.
- **backend / api** — реальное ASGI-приложение через `httpx.ASGITransport`, где
  `get_case_repository` подменяется in-memory адаптером (`dependency_overrides`).
- **backend / migration** — миграция рендерится в DDL офлайн (`alembic upgrade --sql`),
  проверяются таблицы, `CHECK (score >= 0)` и составной внешний ключ.
- **backend / conftest** — задаёт обязательные env-переменные через
  `os.environ.setdefault`, чтобы тесты работали без `backend/.env`.
- **frontend** — vitest + jsdom + `@testing-library/react`; в `npm test` также включён
  drift-check типов API.
- **pipeline** — CLI, извлечение (валид/ремонт/ошибка), харнес, sink'и, Vertex-адаптер с
  инъекцией клиента (без сети).

Отдельно, офлайн-харнес качества извлечения (mock-адаптер, без GCP):

```bash
cd pipeline
.venv/Scripts/python.exe -m app.harness.runner --golden tests/golden --out report.json
```

Ожидаемо: таблица `case / q_P q_R q_F1 / o_P o_R o_F1 / score` и строка `AGGREGATE` со
значениями `1.000` (mock возвращает эталонные фикстуры).

## Генерация типов API (INV-5)

Контракт backend — OpenAPI-снимок `backend/tests/openapi.json`. Типы клиента генерируются
из него, а не пишутся руками:

```bash
cd frontend
npm run gen:api      # перегенерировать src/lib/api-types.ts
npm run check:api    # проверить, что файл не разошёлся с контрактом (входит в npm test)
```

При изменении публичного контракта backend перегенерируй снимок и типы, иначе `check:api`
упадёт в CI.

## Конвенции

- **Backend** — слои `api → domain → data`; ORM только в `data`; домен без фреймворков.
  `ruff` (line-length 100) + `mypy` strict + `import-linter` контракты. Новые use case'ы
  покрываются тестами на in-memory адаптерах.
- **Frontend** — строгий TypeScript, ESLint с обязательным
  `explicit-function-return-type`; компоненты — чистые, логика — в domain/use-case, сеть —
  только в data-репозитории; псевдоним `@/*` → `src/*`.
- **Pipeline** — провайдерский SDK изолирован в `client/vertex.py` (INV-6); ошибки
  типизированы (`PipelineError` и потомки), сырой текст и секреты в логи не попадают.

## Непрерывная интеграция (CI)

`.github/workflows/ci.yml` на push в `main` и на pull request. Джобы:

| Джоб | Рантайм | Шаги |
|---|---|---|
| `secrets` | ubuntu | `gitleaks` — скан утечек секретов |
| `backend` | Python **3.12** | `pip install -e "backend[dev]"` → ruff → mypy → `lint-imports` → pytest |
| `pipeline` | Python **3.12** | `pip install -e "pipeline[dev]"` → ruff → mypy → `lint-imports` → pytest |
| `frontend` | Node **22** | `npm ci` → lint → typecheck → test → build |

> CI намеренно тестирует **минимально поддерживаемую** версию Python (`requires-python
> >=3.12`) и Node 22, тогда как Docker-образы и локальный dev-стек собраны на Python 3.14
> и Node 24. Если меняешь минимальную версию — обнови и матрицу CI.

## Локальная проверка перед коммитом

Повтори шаги CI-джобов для затронутых сервисов (команды из таблицы «Тулчейн» и «CI»).
Для frontend достаточно `npm test` (включает drift-check) + `npm run build`; для backend —
`pytest` + линтеры; для pipeline — `pytest` + линтеры.
