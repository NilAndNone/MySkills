from __future__ import annotations

import json
import importlib.util
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "worldview-panel-codex"
TOOLS_DIR = PLUGIN_ROOT / "tools"
SCHEMAS_DIR = PLUGIN_ROOT / "schemas"


def plugin_root() -> Path:
    return PLUGIN_ROOT


def tools_dir() -> Path:
    return TOOLS_DIR


def load_plugin_module(module_name: str) -> Any:
    module_path = TOOLS_DIR / f"{module_name}.py"
    if not module_path.is_file():
        raise FileNotFoundError(f"plugin module not found: {module_name}")

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load plugin module spec: {module_name}")

    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(TOOLS_DIR))
    try:
        spec.loader.exec_module(module)
    finally:
        if sys.path and sys.path[0] == str(TOOLS_DIR):
            sys.path.pop(0)
    return module


def load_worker_schema(schema_version: str) -> dict[str, Any]:
    schema_path = SCHEMAS_DIR / f"{schema_version}.json"
    if not schema_path.is_file():
        raise FileNotFoundError(f"worker schema not found: {schema_version}")
    return json.loads(schema_path.read_text(encoding="utf-8"))


def load_contracts_module() -> Any:
    return load_plugin_module("worldview_contracts")


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path


def build_round_from_input(round_input_path: str | Path, *, output_root: str | Path | None = None) -> Path:
    round_builder = load_plugin_module("worldview_round_builder")
    return round_builder.build_round_from_input(Path(round_input_path), output_root=Path(output_root) if output_root is not None else None)


def load_dispatch_job(dispatch_job_path: str | Path) -> dict[str, Any]:
    contracts = load_contracts_module()
    return contracts.validate_dispatch_job(load_json(dispatch_job_path))


def load_ticket(round_root: str | Path, persona: str) -> dict[str, Any]:
    return load_json(Path(round_root) / "tickets" / f"{persona}.json")


def load_profile(round_root: str | Path, persona: str) -> dict[str, Any]:
    return load_json(Path(round_root) / "identities" / persona / "profile.json")


def load_packet_text(ticket: dict[str, Any]) -> str:
    return Path(ticket["packet_path"]).read_text(encoding="utf-8")


def resolve_skill_path(round_root: str | Path, profile: dict[str, Any]) -> Path:
    return (Path(round_root) / profile["skill_path"]).resolve()
