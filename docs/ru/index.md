# Clinical Case Scoring Platform

Документация проекта для разработчиков и сопровождающих. Здесь описано, что это за
система, из чего она состоит, как её поднять локально, как она устроена внутри, как
тестируется и как деплоится.

## Что это

Сервис для работы с клиническими кейсами. Он:

1. **извлекает** структурированный кейс (заголовок, вопросы, варианты ответов с весами)
   из сырого клинического текста с помощью LLM;
2. **хранит** кейс в нормализованной PostgreSQL;
3. **отдаёт** HTTP API для создания/чтения кейса и прохождения с автоматическим подсчётом
   баллов;
4. **показывает** веб-интерфейс для прохождения кейса и просмотра результата;
5. **измеряет** качество LLM-извлечения отдельным офлайн-харнесом.

Продукт учебно-демонстрационный: вне скоупа аутентификация, роли, мультитенантность,
медицинская сертификация.

## Компоненты

| Компонент | Технологии | Роль |
|---|---|---|
| **backend** | Python 3.14, FastAPI, SQLAlchemy 2.0 (async), asyncpg, Alembic, Pydantic v2 | REST API, схема БД, миграции, подсчёт баллов, health/ready |
| **frontend** | Node 24, Next.js (App Router), React 19, TypeScript | Список кейсов и прохождение, серверный fetch (RSC) + клиентская отправка ответов |
| **pipeline** | Python 3.14, `google-genai`, httpx | LLM-извлечение структуры из текста + офлайн-харнес точности; запускается как CLI/Cloud Run Job |
| **infra** | Docker, Docker Compose, GCP Cloud Run | Образы сервисов, локальные стеки, скрипты сборки и деплоя |

## Структура репозитория

```
backend/            FastAPI-сервис: app/{api,domain,data}, tests/, alembic/, pyproject.toml
frontend/           Next.js-приложение: src/{app,modules,lib,components}, package.json
pipeline/           LLM-пайплайн: app/{client,harness,input,sink,schema}, tests/, pyproject.toml
infra/              Dockerfile.*, docker-compose.{dev,prod}.yml, cloudrun/{build-and-push,deploy}.sh
.github/workflows/  CI (lint, типы, тесты, сборка)
docs/               эта документация (ru + en)
```

Корневого `package.json` нет: это монорепозиторий с независимыми сервисами, каждый со
своим манифестом (`backend/pyproject.toml`, `pipeline/pyproject.toml`,
`frontend/package.json`).

## Карта документации

- [Начало работы](getting-started.md) — предусловия, переменные окружения, локальный запуск (dev-стек, нативный, prod-like).
- [Архитектура](architecture.md) — слои backend, модель данных, frontend, pipeline, инварианты.
- [Разработка](development.md) — тулчейн, тесты, конвенции, CI.
- [Развёртывание](deployment.md) — Docker-образы, локальный prod-like стек, GCP Cloud Run, секреты.
- [HTTP API](api.md) — эндпоинты, схемы запросов/ответов, формат ошибок.

Английская версия: [`docs/en/`](../en/index.md).
