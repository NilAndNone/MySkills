from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


LOG_DIR_NAME = "log"
TOTAL_LOG_NAME = "worldview-panel-codex.log"
RUN_LOG_DIR = "worldview-panel-codex/runs"


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".codex").resolve()


def total_log_path() -> Path:
    return codex_home() / LOG_DIR_NAME / TOTAL_LOG_NAME


def run_logs_root() -> Path:
    return codex_home() / LOG_DIR_NAME / RUN_LOG_DIR


def new_run_id() -> str:
    return f"run-{uuid4().hex}"


def sanitize_log_value(value: Any) -> str:
    return str(value).replace("\n", "\\n").replace("|", "/").strip()


def _ensure_log_dirs() -> None:
    total_log_path().parent.mkdir(parents=True, exist_ok=True)
    run_logs_root().mkdir(parents=True, exist_ok=True)


def run_log_path(run_id: str) -> Path:
    return run_logs_root() / f"{sanitize_log_value(run_id)}.log"


def format_log_line(
    *,
    timestamp: datetime,
    run_id: str,
    component: str,
    stage: str,
    status: str,
    message: str,
    fields: dict[str, Any] | None = None,
) -> str:
    parts = [
        timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        f"run={sanitize_log_value(run_id)}",
        f"component={sanitize_log_value(component)}",
        f"stage={sanitize_log_value(stage)}",
        f"status={sanitize_log_value(status)}",
    ]

    if fields:
        for key in sorted(fields):
            value = fields[key]
            if value is None:
                continue
            parts.append(f"{sanitize_log_value(key)}={sanitize_log_value(value)}")

    parts.append(f"message={sanitize_log_value(message)}")
    return " | ".join(parts)


def append_log_line(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def log_event(
    *,
    component: str,
    stage: str,
    status: str,
    message: str,
    run_id: str | None = None,
    detail_only: bool = False,
    fields: dict[str, Any] | None = None,
) -> dict[str, str]:
    _ensure_log_dirs()
    effective_run_id = run_id or new_run_id()
    line = format_log_line(
        timestamp=datetime.now(),
        run_id=effective_run_id,
        component=component,
        stage=stage,
        status=status,
        message=message,
        fields=fields,
    )

    run_path = run_log_path(effective_run_id)
    append_log_line(run_path, line)
    if not detail_only:
        append_log_line(total_log_path(), line)

    return {
        "run_id": effective_run_id,
        "line": line,
        "run_log_path": str(run_path),
        "total_log_path": str(total_log_path()),
    }


@dataclass(slots=True)
class PanelLogger:
    component: str
    run_id: str | None = None
    detail: bool = False
    _effective_run_id: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._effective_run_id = self.run_id or new_run_id()

    @property
    def effective_run_id(self) -> str:
        return self._effective_run_id

    def log(
        self,
        *,
        stage: str,
        status: str,
        message: str,
        detail_only: bool = False,
        **fields: Any,
    ) -> dict[str, str]:
        return log_event(
            component=self.component,
            run_id=self._effective_run_id,
            stage=stage,
            status=status,
            message=message,
            detail_only=detail_only,
            fields=fields,
        )
