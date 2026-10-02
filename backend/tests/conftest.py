"""Test environment defaults.

Settings are constructed lazily from the environment (``get_settings()``), so
tests must provide the required variables even without a local ``backend/.env``
(e.g. on CI). These are test fixtures, not application configuration.
"""

from __future__ import annotations

import os

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("CORS_ORIGINS", '["http://localhost:3000"]')
os.environ.setdefault("POSTGRES_USER", "clinical")
os.environ.setdefault("POSTGRES_PASSWORD", "clinical")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "clinical")
