from __future__ import annotations

import json
from pathlib import Path


SCHEMA_ROOT = Path(__file__).resolve().parent / "schemas"


def load_worker_schema(schema_version: str) -> dict:
    schema_path = SCHEMA_ROOT / f"{schema_version}.json"
    if not schema_path.is_file():
        raise FileNotFoundError(f"worker schema not found: {schema_version}")
    return json.loads(schema_path.read_text(encoding="utf-8"))
