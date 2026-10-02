# Начало работы

## Предусловия

- **Docker Desktop** (движок запущен) — `docker version`, `docker compose version`.
- **Python 3.14** (для нативного запуска и тестов) — `python --version`.
- **Node 24 + npm** — `node --version`.
- **Git Bash** на Windows — все `.sh`-скрипты запускать из него, не из PowerShell и не из WSL.
- _(опционально, для деплоя и реального LLM)_ **Google Cloud SDK** — `gcloud --version`.

## Переменные окружения

Значения не захардкожены в коде: каждый сервис читает свои переменные через
`pydantic-settings`. Обязательные переменные отсутствуют → сервис падает при старте
(fail-fast), а не поднимается с неверной конфигурацией.

### Backend (`backend/.env`)

```bash
cp backend/.env.example backend/.env
```

| Переменная | Назначение |
|---|---|
| `ENVIRONMENT` | окружение (`development` / `production` / `test`) |
| `CORS_ORIGINS` | JSON-массив разрешённых origin'ов, напр. `["http://localhost:3000"]` |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_HOST` / `POSTGRES_PORT` / `POSTGRES_DB` | разрозненные части подключения к БД (локально/compose) |
| `DATABASE_URL` | единая строка `postgresql+asyncpg://...`; приоритетнее `POSTGRES_*` (прод/Secret Manager) |

Должен быть задан либо `DATABASE_URL`, либо **все** `POSTGRES_*`.

### Pipeline (`pipeline/.env`)

```bash
cp pipeline/.env.example pipeline/.env
```

| Переменная | Назначение |
|---|---|
| `GCP_PROJECT`, `GCP_LOCATION`, `LLM_MODEL` | параметры провайдера LLM |
| `LLM_CLIENT` | `mock` (офлайн-фикстуры) или `vertex` (реальный Gemini) |
| `BACKEND_URL` | база backend для отправки кейса (`--post`) |
| `GEMINI_API_KEY` | опционально: Developer API-ключ для локальной разработки без ADC |

### Frontend

| Переменная | Назначение |
|---|---|
| `BACKEND_URL` | URL backend для **серверных** запросов (RSC); в Docker — `http://backend:8080` |
| `NEXT_PUBLIC_API_URL` | URL backend для **браузерных** запросов; в браузере — `http://localhost:8000` |
| `MIN_PAGE_LOAD_MS` | опционально: минимальная длительность загрузки страницы (дефолт `2000`) |

### Корневой `.env` (для Docker Compose)

Compose подставляет переменные из корневого `.env`. Ключевая переменная —
**`POSTGRES_PASSWORD`**: она обязательна, дефолта нет (слабый пароль не подставится
молча). Пример для локальной разработки:

```bash
POSTGRES_USER=clinical
POSTGRES_PASSWORD=clinical
POSTGRES_DB=clinical
```

Не коммить реальные `.env` — они в `.gitignore`.

## Режим 1 — полный dev-стек в Docker (рекомендуется)

Одна команда поднимает PostgreSQL + backend (`uvicorn --reload`) + frontend (`next dev`).
Исходники смонтированы в контейнеры, правки подхватываются без пересборки.

```bash
POSTGRES_PASSWORD=clinical docker compose -f infra/docker-compose.dev.yml up --build
```

Проверка:

```bash
curl -s http://localhost:8000/health        # {"status":"ok"}
curl -s http://localhost:8000/ready         # {"status":"ready"} (БД доступна)
curl -s http://localhost:8000/cases         # 2 демо-кейса (сидер на старте backend)
open http://localhost:3000                  # Windows: start http://localhost:3000
```

Остановить:

```bash
docker compose -f infra/docker-compose.dev.yml down        # данные сохраняются
docker compose -f infra/docker-compose.dev.yml down -v     # + удалить volume БД
```

Переопределяемые порты: `POSTGRES_PORT` (5432), `BACKEND_PORT` (8000), `FRONTEND_PORT`
(3000). Внутри Docker frontend обращается к backend по `http://backend:8080`.

Нужна только БД (а backend/frontend — нативно, см. режим 2):

```bash
POSTGRES_PASSWORD=clinical docker compose -f infra/docker-compose.dev.yml up -d postgres
```

## Режим 2 — нативный запуск (быстрый цикл для IDE)

Приложение работает на хосте, в Docker поднимается только PostgreSQL.

```bash
# 1. База данных
POSTGRES_PASSWORD=clinical docker compose -f infra/docker-compose.dev.yml up -d postgres

# 2. Backend
cd backend
python -m venv .venv                                   # если .venv ещё нет
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m alembic upgrade head       # схема БД
.venv/Scripts/python.exe -m app.seed                   # 2 демо-кейса (идемпотентно)
.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000

# 3. Frontend (в отдельном терминале)
cd frontend
npm install
npm run dev                                            # http://localhost:3000
```

На Linux/macOS интерпретатор лежит в `.venv/bin/python` вместо `.venv/Scripts/python.exe`.

## Режим 3 — prod-like стек (реальные образы)

Собирает backend и frontend из Dockerfile'ов, накатывает миграции, сеет демо-данные и
запускает сервисы — максимально близко к продакшену.

```bash
POSTGRES_PASSWORD=clinical docker compose -f infra/docker-compose.prod.yml up --build
```

Детали, проверка «в образе нет секретов», чек-лист и troubleshooting — в разделе
[Развёртывание](deployment.md).

## Ручной E2E-сценарий

1. Открой `http://localhost:3000` — должен появиться список демо-кейсов.
2. Открой кейс → ответь на вопросы → **Submit**.
3. Ожидаемо: страница переходит в review-режим, показывает известный балл и подсвечивает
   верные/неверные варианты.
4. Проверь узкий viewport (DevTools → мобильное устройство): горизонтального скролла нет.

## Что дальше

- Устройство системы — [Архитектура](architecture.md).
- Как запускать тесты и линтеры — [Разработка](development.md).
- Деплой на GCP — [Развёртывание](deployment.md).
