# Развёртывание

## Docker-образы

Три образа собираются из корня репозитория (build context = корень, см.
`.dockerignore`). Все — multi-stage, запускаются от непривилегированного пользователя и
слушают порт **8080**.

| Образ | Dockerfile | Роль |
|---|---|---|
| `clinical-backend` | `infra/Dockerfile.backend` | FastAPI + uvicorn |
| `clinical-frontend` | `infra/Dockerfile.frontend` | Next.js standalone-server |
| `clinical-pipeline` | `infra/Dockerfile.pipeline` | Cloud Run Job: CLI извлечения/харнес |

Сборка вручную:

```bash
docker build -f infra/Dockerfile.backend  -t clinical-backend  .
docker build -f infra/Dockerfile.frontend --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 -t clinical-frontend .
docker build -f infra/Dockerfile.pipeline -t clinical-pipeline .
```

`NEXT_PUBLIC_API_URL` вшивается в клиентский бандл **на этапе сборки**; `BACKEND_URL`
читается серверными компонентами **в рантайме**. Это важно для порядка деплоя (ниже).

## Локальный prod-like стек

Собирает backend и frontend из Dockerfile'ов, поднимает PostgreSQL, накатывает миграции,
сеет демо-данные и запускает оба сервиса:

```bash
POSTGRES_PASSWORD=clinical docker compose -f infra/docker-compose.prod.yml up --build
```

Проверка:

```bash
curl -s http://localhost:8000/health        # {"status":"ok"}
curl -s http://localhost:8000/ready         # {"status":"ready"}
curl -s http://localhost:8000/cases         # 2 кейса после сидинга
open http://localhost:3000                  # Windows: start http://localhost:3000
```

Остановить:

```bash
docker compose -f infra/docker-compose.prod.yml down        # данные сохраняются
docker compose -f infra/docker-compose.prod.yml down -v     # + удалить volume PostgreSQL
```

## Секреты

Секреты (строка подключения к БД, креды провайдера) подаются **только** через окружение
или Secret Manager и никогда не попадают в образ. Проверка:

```bash
docker run --rm clinical-backend sh -c 'env | grep -iE "password|secret|database_url" || echo "no secrets in env"'
docker image history clinical-backend      # без строк с секретами
```

Локально/compose подключение к БД задаётся разрозненно (`POSTGRES_USER`,
`POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`); в проде — единым
`DATABASE_URL` (Secret Manager). Оба варианта поддерживаются, `DATABASE_URL` приоритетнее.
Если обязательная конфигурация отсутствует — сервис падает при старте (fail-fast), а не
поднимается с дефолтом `localhost`.

## Деплой на GCP Cloud Run

### 0. Подготовка проекта

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
export GCP_PROJECT=YOUR_PROJECT_ID

gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com aiplatform.googleapis.com --project "$GCP_PROJECT"
```

### 1. Секрет с URL базы (Secret Manager)

`DATABASE_URL` указывает на внешнюю managed-PostgreSQL (Cloud SQL/Neon и т.п.) — она не
входит в образы.

```bash
printf '%s' 'postgresql+asyncpg://USER:PASSWORD@HOST:5432/clinical' | \
  gcloud secrets create clinical-database-url \
    --project "$GCP_PROJECT" --replication-policy automatic --data-file=-
```

Выдай сервисному аккаунту Cloud Run доступ к секрету:

```bash
gcloud secrets add-iam-policy-binding clinical-database-url \
  --project "$GCP_PROJECT" \
  --member "serviceAccount:YOUR_COMPUTE_SA@$GCP_PROJECT.iam.gserviceaccount.com" \
  --role roles/secretmanager.secretAccessor
```

> Дефолтный compute service account имеет доступ по умолчанию; отдельный IAM нужен, если
> задан собственный `--service-account`.

### 2. Сборка и пуш образов

```bash
GCP_PROJECT=YOUR_PROJECT_ID GCP_REGION=europe-west1 TAG=v1 \
  bash infra/cloudrun/build-and-push.sh
```

Скрипт создаёт Artifact Registry репозиторий `clinical-case` (если нет), собирает и пушит
`backend`, `frontend`, `pipeline` с тегом `TAG`. Для frontend в образ вшивается
`NEXT_PUBLIC_API_URL` (по умолчанию `http://localhost:8000` — для продакшена его нужно
задать явно).

### 3. Деплой сервисов и job

```bash
GCP_PROJECT=YOUR_PROJECT_ID GCP_REGION=europe-west1 TAG=v1 \
  DATABASE_URL='postgresql+asyncpg://...' \
  bash infra/cloudrun/deploy.sh
```

Скрипт:

1. создаёт секрет (если его нет) из `DATABASE_URL`;
2. деплоит backend (`--allow-unauthenticated`, `--set-secrets DATABASE_URL=...:latest`);
3. печатает backend URL;
4. деплоит frontend с `BACKEND_URL=<backend-url>`;
5. деплоит Cloud Run **Job** `clinical-pipeline` с env `GCP_PROJECT`, `GCP_LOCATION`,
   `LLM_MODEL`, `LLM_CLIENT=vertex`, `BACKEND_URL`.

### Two-pass frontend build

Так как `NEXT_PUBLIC_API_URL` вшивается при сборке, а URL backend заранее неизвестен:

```bash
# 1. узнать URL backend (после деплоя backend)
BACKEND_URL=$(gcloud run services describe clinical-backend --region europe-west1 \
  --format 'value(status.url)')

# 2. пересобрать/запушить frontend с этим URL и задеплоить его
GCP_PROJECT=YOUR_PROJECT_ID NEXT_PUBLIC_API_URL="$BACKEND_URL" TAG=v1 \
  bash infra/cloudrun/build-and-push.sh
GCP_PROJECT=YOUR_PROJECT_ID TAG=v1 bash infra/cloudrun/deploy.sh
```

### 4. Проверка деплоя

```bash
curl -fsS "$(gcloud run services describe clinical-backend --region europe-west1 --format 'value(status.url)')/health"

gcloud run jobs execute clinical-pipeline --region europe-west1 --wait
gcloud run jobs executions list --job clinical-pipeline --region europe-west1
```

Ожидаемо: `/health` → `200 {"status":"ok"}`; job завершается с кодом 0 и печатает таблицу
харнеса в логи (`gcloud run jobs executions logs <execution>`).

## Чек-лист приёмки

- [ ] линтеры/типы/тесты/сборка зелёные (см. [Разработка](development.md) и CI)
- [ ] backend: `GET /health` → 200, `GET /ready` → 200 при живой БД
- [ ] `POST /cases` → `GET /cases/{id}` → `POST /cases/{id}/submissions` возвращает балл
- [ ] frontend: список кейсов → прохождение → результат, адаптивность без горизонтального скролла
- [ ] `python -m app.harness.runner` печатает per-field P/R/F1 (на mock = `1.000`)
- [ ] локально `POSTGRES_PASSWORD=clinical docker compose -f infra/docker-compose.prod.yml up --build` поднимает стек
- [ ] образы не содержат секретов; `/health` отвечает на Cloud Run
- [ ] `gcloud run jobs execute clinical-pipeline` завершается успешно

## Troubleshooting

- **`/ready` → 503** — PostgreSQL недоступен или неверный `DATABASE_URL`/`POSTGRES_*`.
  Проверь `docker compose ps` и строку подключения.
- **Frontend пустой или 500 на RSC** — не задан `BACKEND_URL` (в Cloud Run — env сервиса
  frontend; локально по умолчанию `http://localhost:8000`).
- **Клиентские запросы с фронта идут не туда** — `NEXT_PUBLIC_API_URL` вшит при сборке;
  пересобери frontend (см. Two-pass).
- **`DATABASE_URL must be provided` при старте** — это fail-fast: задай секрет и
  `--set-secrets`; сервис намеренно не стартует с дефолтным localhost.
- **`docker build` падает на `COPY .../public`** — в репозитории есть `frontend/public/`
  (с `.gitkeep`); не удаляй её.
- **Windows: `bash` запускает WSL** — используй полный путь к Git Bash
  (`...\Git\bin\bash.exe`), а не `bash script.sh`.
- **Compose: `POSTGRES_PASSWORD must be set`** — задай `POSTGRES_PASSWORD` (в окружении
  или корневом `.env`); дефолта у него нет.
