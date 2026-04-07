from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_round_payload(round_root: Path) -> dict[str, Any]:
    round_input = _read_json_if_exists(round_root / "round_input.json")
    run_summary = _read_json_if_exists(round_root / "runtime_adapter" / "run_summary.json")
    failure_summary = _read_json_if_exists(round_root / "runtime_adapter" / "failure_summary.json")
    run_summary_result_grade = str(run_summary.get("result_grade") or "")
    execution = {}
    if run_summary_result_grade == "blocked":
        current_result_grade = "blocked"
        content_brief = {}
    else:
        content_brief = _read_json_if_exists(round_root / "content_brief.json")
        execution = content_brief.get("meta", {}).get("execution_summary", {})
        current_result_grade = str(execution.get("result_grade") or run_summary_result_grade or "blocked")
    issue = content_brief.get("issue", {})
    if isinstance(issue, dict):
        question = str(issue.get("question") or issue.get("title") or round_input.get("issue") or "")
    else:
        question = str(issue or round_input.get("issue") or "")
    execution_policy = str(execution.get("execution_policy") or run_summary.get("execution_policy") or "adaptive")
    panel_emitted = bool(run_summary.get("panel_emitted", current_result_grade != "blocked"))
    blocked_audit = {
        "status": {"label": _blocked_status_label(execution_policy), "result_grade": "blocked"},
        "execution": {
            "run_status": str(execution.get("run_status") or run_summary.get("run_status") or ""),
            "execution_policy": execution_policy,
            "successful_personas": list(execution.get("successful_personas", [])),
            "failed_personas": _normalize_failed_personas(failure_summary.get("failed_personas", [])),
        },
        "failure_summary": failure_summary or None,
    }
    if current_result_grade != "blocked":
        studio_surface = _read_json_if_exists(round_root / "studio_surface.json")
        audit_surface = _read_json_if_exists(round_root / "audit_surface.json")
    else:
        studio_surface = {}
        audit_surface = {}

    return {
        "round_id": str(execution.get("run_id") or run_summary.get("run_id") or round_root.name),
        "question": question,
        "default_surface": "studio" if studio_surface else "audit",
        "studio": studio_surface or None,
        "audit": audit_surface or blocked_audit,
        "run_status": str(execution.get("run_status") or run_summary.get("run_status") or ""),
        "panel_emitted": panel_emitted,
        "failure_summary": failure_summary or None,
    }


def write_static_viewer(round_root: Path, output_dir: Path) -> Path:
    payload = build_round_payload(round_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "data.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "index.html").write_text(_render_html_shell(), encoding="utf-8")
    return output_dir / "index.html"


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _blocked_status_label(execution_policy: str) -> str:
    return "strict fail closed" if execution_policy == "strict" else "quorum failed"


def _normalize_failed_personas(raw_failed_personas: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_failed_personas, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in raw_failed_personas:
        if isinstance(item, dict):
            persona = str(item.get("persona", "")).strip()
            if not persona:
                continue
            normalized.append(
                {
                    "persona": persona,
                    "failure_reason": str(item.get("failure_reason", "")).strip(),
                    "failure_class": str(item.get("failure_class", "")).strip(),
                }
            )
            continue
        persona = str(item).strip()
        if persona:
            normalized.append({"persona": persona, "failure_reason": "", "failure_class": ""})
    return normalized


def _render_html_shell() -> str:
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Worldview Round Viewer</title>
  <style>
    body {
      margin: 0;
      font-family: "IBM Plex Sans", "Noto Sans", sans-serif;
      color: #11213e;
      background: linear-gradient(180deg, #f8fbff 0%, #eef4ff 100%);
    }
    main {
      max-width: 1080px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }
    section {
      background: rgba(255, 255, 255, 0.88);
      border: 1px solid rgba(32, 88, 194, 0.14);
      border-radius: 20px;
      box-shadow: 0 18px 40px rgba(18, 47, 110, 0.08);
      padding: 20px;
      margin-top: 18px;
    }
    h1, h2, h3, p { margin: 0; }
    .label {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 999px;
      background: rgba(42, 106, 255, 0.12);
      color: #1a4dc7;
      font-size: 13px;
      margin-top: 12px;
    }
    ul { margin: 10px 0 0; padding-left: 20px; }
    .grid {
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      background: #f6f8fc;
      border-radius: 14px;
      padding: 14px;
      margin-top: 12px;
      font-size: 13px;
    }
  </style>
</head>
<body>
  <main>
    <section>
      <h1 id="question-title">Loading...</h1>
      <p id="run-status"></p>
      <div class="label" id="studio-status"></div>
    </section>
    <section id="studio-summary">
      <h2>Studio</h2>
      <p id="studio-headline"></p>
      <div class="grid" id="studio-cards"></div>
    </section>
    <section id="audit-panel">
      <h2>Audit</h2>
      <pre id="audit-json"></pre>
    </section>
  </main>
  <script>
    fetch("./data.json")
      .then((response) => response.json())
      .then((payload) => {
        document.getElementById("question-title").textContent = payload.question || "未找到议题";
        document.getElementById("run-status").textContent = payload.run_status || "";
        document.getElementById("studio-status").textContent = payload.studio?.status?.label || "";
        document.getElementById("studio-headline").textContent = payload.studio?.executive_judgment?.one_line_judgment || "";
        const cards = payload.studio?.perspective_cards || [];
        const cardRoot = document.getElementById("studio-cards");
        cardRoot.textContent = "";
        cards.forEach((card) => {
          const section = document.createElement("section");
          const title = document.createElement("h3");
          title.textContent = card.persona || "";
          const body = document.createElement("p");
          body.textContent = card.signature_line || "";
          section.appendChild(title);
          section.appendChild(body);
          cardRoot.appendChild(section);
        });
        document.getElementById("audit-json").textContent = JSON.stringify(payload.audit || {}, null, 2);
      });
  </script>
</body>
</html>
"""
