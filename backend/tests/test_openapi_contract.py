"""INV-2: the public OpenAPI contract is frozen by a committed snapshot."""

import json
from pathlib import Path

from app.main import create_app

SNAPSHOT_PATH = Path(__file__).resolve().parent / "openapi.json"


def test_openapi_contract_matches_snapshot() -> None:
    current = json.loads(json.dumps(create_app().openapi(), sort_keys=True))
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))

    assert current == snapshot, (
        "OpenAPI contract changed. If the change is intentional and additive, "
        "regenerate with `python scripts/export_openapi.py` (from backend/)."
    )
