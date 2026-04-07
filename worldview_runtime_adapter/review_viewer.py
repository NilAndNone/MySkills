from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_round_payload(round_root: Path) -> dict[str, Any]:
    round_input = _read_json_if_exists(round_root / "round_input.json")
    run_summary = _read_json_if_exists(round_root / "runtime_adapter" / "run_summary.json")
    failure_summary = _read_json_if_exists(round_root / "runtime_adapter" / "failure_summary.json")
    run_summary_result_grade = str(run_summary.get("result_grade") or "")
    run_summary_panel_emitted = run_summary.get("panel_emitted")
    is_blocked_run = run_summary_result_grade == "blocked" or run_summary_panel_emitted is False
    execution = {}
    if is_blocked_run:
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
    panel_emitted = bool(run_summary_panel_emitted if run_summary_panel_emitted is not None else current_result_grade != "blocked")
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
    :root {
      --paper: #f4efe4;
      --paper-shadow: rgba(31, 42, 68, 0.08);
      --panel: rgba(255, 252, 246, 0.94);
      --panel-strong: rgba(255, 255, 255, 0.96);
      --ink: #172033;
      --muted: #5d687d;
      --line: rgba(23, 32, 51, 0.12);
      --accent: #275fcb;
      --accent-soft: rgba(39, 95, 203, 0.11);
      --accent-strong: rgba(39, 95, 203, 0.2);
      --success-soft: rgba(24, 84, 58, 0.08);
    }
    * {
      box-sizing: border-box;
    }
    body {
      margin: 0;
      font-family: "IBM Plex Sans", "Noto Sans", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top, rgba(39, 95, 203, 0.08), transparent 34%),
        linear-gradient(180deg, #f7f2e8 0%, #efe7d8 100%);
    }
    main {
      max-width: 1180px;
      margin: 0 auto;
      padding: 28px 20px 48px;
    }
    h1, h2, h3, h4, p {
      margin: 0;
    }
    .workbench {
      display: grid;
      gap: 18px;
    }
    .topbar,
    .surface-panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 24px;
      box-shadow: 0 20px 48px var(--paper-shadow);
      backdrop-filter: blur(12px);
    }
    .topbar {
      display: grid;
      gap: 20px;
      padding: 24px;
    }
    .eyebrow,
    .section-kicker,
    .metric-label {
      font-size: 12px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
    }
    .header-copy {
      display: grid;
      gap: 10px;
    }
    #question-title {
      font-family: "Iowan Old Style", "Noto Serif", serif;
      font-size: clamp(32px, 4vw, 46px);
      line-height: 1.04;
      letter-spacing: -0.03em;
    }
    .header-summary {
      max-width: 760px;
      color: var(--muted);
      line-height: 1.6;
    }
    .topbar-meta {
      display: grid;
      gap: 14px;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      align-items: end;
    }
    .metric {
      display: grid;
      gap: 6px;
      padding: 14px 16px;
      border-radius: 18px;
      background: var(--panel-strong);
      border: 1px solid rgba(23, 32, 51, 0.08);
    }
    .metric-value {
      font-size: 15px;
      font-weight: 600;
    }
    .surface-switcher {
      display: inline-flex;
      gap: 8px;
      align-items: center;
      padding: 6px;
      border-radius: 999px;
      background: rgba(23, 32, 51, 0.06);
      width: fit-content;
    }
    .surface-toggle {
      border: 0;
      border-radius: 999px;
      padding: 10px 16px;
      background: transparent;
      color: var(--muted);
      font: inherit;
      font-weight: 600;
      cursor: pointer;
      transition: background-color 160ms ease, color 160ms ease, transform 160ms ease;
    }
    .surface-toggle:hover:not(:disabled) {
      transform: translateY(-1px);
    }
    .surface-toggle.is-active {
      background: var(--accent);
      color: white;
      box-shadow: 0 10px 24px rgba(39, 95, 203, 0.24);
    }
    .surface-toggle:disabled {
      cursor: not-allowed;
      opacity: 0.45;
    }
    .surface-stack {
      display: grid;
      gap: 18px;
    }
    .surface-panel {
      display: none;
      padding: 22px;
    }
    .surface-panel.is-active {
      display: grid;
      gap: 18px;
      animation: surface-enter 220ms ease;
    }
    .surface-panel[hidden] {
      display: none;
    }
    .surface-header {
      display: grid;
      gap: 10px;
      padding-bottom: 4px;
    }
    .surface-title-row {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
    }
    .surface-title {
      font-size: 26px;
      font-family: "Iowan Old Style", "Noto Serif", serif;
      letter-spacing: -0.02em;
    }
    .surface-status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 7px 12px;
      border-radius: 999px;
      background: var(--success-soft);
      color: #194a35;
      font-size: 13px;
      font-weight: 600;
    }
    .surface-caption {
      color: var(--muted);
      line-height: 1.6;
    }
    .studio-layout {
      display: grid;
      gap: 18px;
    }
    .studio-grid {
      display: grid;
      gap: 18px;
      grid-template-columns: minmax(0, 1.5fr) minmax(280px, 0.9fr);
    }
    .content-block,
    .support-block,
    .audit-pane {
      background: var(--panel-strong);
      border: 1px solid rgba(23, 32, 51, 0.08);
      border-radius: 20px;
      padding: 18px;
    }
    .content-block {
      display: grid;
      gap: 14px;
    }
    .section-heading {
      display: grid;
      gap: 6px;
      padding-bottom: 10px;
      border-bottom: 1px solid var(--line);
    }
    .section-title {
      font-size: 22px;
      font-family: "Iowan Old Style", "Noto Serif", serif;
      letter-spacing: -0.02em;
    }
    .section-note {
      color: var(--muted);
      line-height: 1.55;
    }
    .judgment-line {
      font-size: 24px;
      line-height: 1.3;
      letter-spacing: -0.02em;
    }
    .fact-list,
    .trace-list,
    .outline-list {
      margin: 0;
      padding-left: 18px;
      display: grid;
      gap: 8px;
      color: var(--ink);
      line-height: 1.6;
    }
    .empty {
      color: var(--muted);
    }
    .detail-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    }
    .detail-item {
      display: grid;
      gap: 6px;
      padding: 12px 14px;
      border-radius: 16px;
      background: rgba(39, 95, 203, 0.05);
      border: 1px solid rgba(39, 95, 203, 0.08);
    }
    .detail-item strong {
      font-size: 15px;
    }
    .axis-grid,
    .perspective-grid,
    .creation-grid {
      display: grid;
      gap: 14px;
    }
    .axis-grid,
    .creation-grid {
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }
    .axis-card,
    .persona-card,
    .creation-column {
      display: grid;
      gap: 10px;
      padding: 15px;
      border-radius: 18px;
      border: 1px solid rgba(23, 32, 51, 0.08);
      background: rgba(250, 247, 241, 0.88);
    }
    .axis-section {
      display: grid;
      gap: 6px;
    }
    .mini-label {
      font-size: 11px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
    }
    .persona-card-header {
      display: grid;
      gap: 4px;
    }
    .persona-role {
      font-size: 18px;
    }
    .persona-signature {
      color: var(--muted);
      line-height: 1.55;
    }
    .persona-meta {
      display: grid;
      gap: 10px;
    }
    .trace-panel {
      border-radius: 18px;
      border: 1px solid rgba(23, 32, 51, 0.08);
      background: rgba(250, 247, 241, 0.88);
      padding: 4px 16px 16px;
    }
    .trace-panel summary {
      list-style: none;
      cursor: pointer;
      padding: 14px 0;
      font-weight: 600;
    }
    .trace-panel summary::-webkit-details-marker {
      display: none;
    }
    .trace-grid {
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }
    .audit-layout {
      display: grid;
      gap: 18px;
      grid-template-columns: minmax(0, 0.85fr) minmax(0, 1.15fr);
    }
    .audit-pane {
      display: grid;
      gap: 14px;
    }
    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      background: #f2eee5;
      border-radius: 16px;
      border: 1px solid rgba(23, 32, 51, 0.08);
      padding: 16px;
      font-size: 13px;
      line-height: 1.6;
      color: #21304d;
      overflow: auto;
    }
    @keyframes surface-enter {
      from {
        opacity: 0;
        transform: translateY(8px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
    @media (max-width: 820px) {
      main {
        padding: 18px 14px 32px;
      }
      .topbar,
      .surface-panel {
        border-radius: 20px;
        padding: 18px;
      }
      .studio-grid,
      .audit-layout {
        grid-template-columns: 1fr;
      }
      .surface-switcher {
        width: 100%;
        justify-content: space-between;
      }
      .surface-toggle {
        flex: 1 1 0;
      }
    }
  </style>
</head>
<body>
  <main>
    <div class="workbench">
      <header class="topbar">
        <div class="header-copy">
          <p class="eyebrow">Stage Three Viewer</p>
          <h1 id="question-title">Loading...</h1>
          <p class="header-summary" id="header-summary">Preparing the round surfaces.</p>
        </div>
        <div class="topbar-meta">
          <div class="metric">
            <span class="metric-label">Run State</span>
            <strong class="metric-value" id="run-status">-</strong>
          </div>
          <div class="metric">
            <span class="metric-label">Result Grade</span>
            <strong class="metric-value" id="result-grade">-</strong>
          </div>
          <div class="metric">
            <span class="metric-label">Surface</span>
            <div class="surface-switcher" id="surface-switcher" role="tablist" aria-label="Surface switcher">
              <button class="surface-toggle" id="surface-toggle-studio" type="button" data-surface="studio">Studio</button>
              <button class="surface-toggle" id="surface-toggle-audit" type="button" data-surface="audit">Audit</button>
            </div>
          </div>
        </div>
      </header>

      <div class="surface-stack">
        <section class="surface-panel" id="studio-surface" data-surface-panel="studio" data-view="studio-summary" hidden>
          <div class="surface-header">
            <div class="surface-title-row">
              <div>
                <p class="section-kicker">Primary Surface</p>
                <h2 class="surface-title">Studio</h2>
              </div>
              <div class="surface-status" id="studio-status">-</div>
            </div>
            <p class="surface-caption" id="studio-caption">Product-first briefing surface for judgment, tension, and creation direction.</p>
          </div>

          <div class="studio-layout">
            <section class="content-block" aria-labelledby="executive-judgment-heading">
              <div class="section-heading">
                <p class="section-kicker">Executive Judgment</p>
                <h3 class="section-title" id="executive-judgment-heading">Executive Judgment</h3>
                <p class="section-note">Start from the strongest judgment before drilling into supporting premises.</p>
              </div>
              <p class="judgment-line" id="judgment-line"></p>
              <div class="detail-grid" id="judgment-details"></div>
              <div>
                <p class="mini-label">Premises</p>
                <div id="judgment-premises"></div>
              </div>
            </section>

            <div class="studio-grid">
              <section class="content-block" aria-labelledby="tension-map-heading">
                <div class="section-heading">
                  <p class="section-kicker">Tension Map</p>
                  <h3 class="section-title" id="tension-map-heading">Tension Map</h3>
                  <p class="section-note">Separate alignment, conflict, and minority pressure so disagreement stays legible.</p>
                </div>
                <div class="axis-grid" id="tension-map"></div>
              </section>

              <aside class="support-block" aria-labelledby="perspective-cards-heading">
                <div class="section-heading">
                  <p class="section-kicker">Perspective Cards</p>
                  <h3 class="section-title" id="perspective-cards-heading">Perspective Cards</h3>
                  <p class="section-note">Compact signatures for the voices that most shaped the round.</p>
                </div>
                <div class="perspective-grid" id="studio-cards"></div>
              </aside>
            </div>

            <section class="content-block" aria-labelledby="creation-layer-heading">
              <div class="section-heading">
                <p class="section-kicker">Creation Layer</p>
                <h3 class="section-title" id="creation-layer-heading">Creation Layer</h3>
                <p class="section-note">Turn the synthesis into publishable angles, outlines, and next research moves.</p>
              </div>
              <div class="creation-grid" id="creation-layer"></div>
            </section>

            <details class="trace-panel" id="trace-panel">
              <summary>Expandable Trace</summary>
              <div class="trace-grid" id="trace-grid"></div>
            </details>
          </div>
        </section>

        <section class="surface-panel" id="audit-surface" data-surface-panel="audit" data-view="audit-panel" hidden>
          <div class="surface-header">
            <div class="surface-title-row">
              <div>
                <p class="section-kicker">Secondary Surface</p>
                <h2 class="surface-title">Audit</h2>
              </div>
              <div class="surface-status" id="audit-status">-</div>
            </div>
            <p class="surface-caption" id="audit-caption">Execution evidence, failure details, and full review payload for checking the round.</p>
          </div>
          <div class="audit-layout">
            <aside class="audit-pane">
              <div class="section-heading">
                <p class="section-kicker">Audit Summary</p>
                <h3 class="section-title">Review Frame</h3>
                <p class="section-note">Use this pane to inspect runtime state before trusting the Studio surface.</p>
              </div>
              <div class="detail-grid" id="audit-summary"></div>
            </aside>
            <section class="audit-pane">
              <div class="section-heading">
                <p class="section-kicker">Evidence Payload</p>
                <h3 class="section-title">Audit Payload</h3>
                <p class="section-note">Raw review data stays visible here in a readable, non-interpolated form.</p>
              </div>
              <pre id="audit-json"></pre>
            </section>
          </div>
        </section>
      </div>
    </div>
  </main>
  <script>
    function safeText(value, fallback) {
      if (value === null || value === undefined || value === "") {
        return fallback || "";
      }
      return String(value);
    }

    function resetNode(node) {
      while (node.firstChild) {
        node.removeChild(node.firstChild);
      }
    }

    function appendList(root, items, className, emptyLabel) {
      const list = document.createElement("ul");
      if (className) {
        list.className = className;
      }
      const normalized = Array.isArray(items) ? items : [];
      if (normalized.length === 0) {
        const empty = document.createElement("li");
        empty.className = "empty";
        empty.textContent = emptyLabel;
        list.appendChild(empty);
      } else {
        normalized.forEach((item) => {
          const line = document.createElement("li");
          line.textContent = typeof item === "string" ? item : JSON.stringify(item);
          list.appendChild(line);
        });
      }
      root.appendChild(list);
    }

    function appendDetailItems(root, entries) {
      resetNode(root);
      entries.forEach((entry) => {
        const value = safeText(entry.value, "");
        if (!value) {
          return;
        }
        const item = document.createElement("div");
        item.className = "detail-item";
        const label = document.createElement("span");
        label.className = "mini-label";
        label.textContent = entry.label;
        const body = document.createElement("strong");
        body.textContent = value;
        item.appendChild(label);
        item.appendChild(body);
        root.appendChild(item);
      });
      if (!root.childNodes.length) {
        const empty = document.createElement("p");
        empty.className = "empty";
        empty.textContent = "No additional details provided.";
        root.appendChild(empty);
      }
    }

    function renderAxisMap(axisRoot, tensionMap) {
      resetNode(axisRoot);
      const axes = [
        ["Fact Axis", tensionMap.fact_axis || {}],
        ["Value Axis", tensionMap.value_axis || {}],
        ["Strategy Axis", tensionMap.strategy_axis || {}],
      ];
      axes.forEach(([name, axis]) => {
        const card = document.createElement("article");
        card.className = "axis-card";
        const title = document.createElement("h3");
        title.textContent = name;
        card.appendChild(title);
        [
          ["Consensus", axis.consensus || []],
          ["Conflicts", axis.conflicts || []],
          ["Minority Alerts", axis.minority_alerts || []],
        ].forEach(([labelText, items]) => {
          const section = document.createElement("section");
          section.className = "axis-section";
          const label = document.createElement("p");
          label.className = "mini-label";
          label.textContent = labelText;
          section.appendChild(label);
          appendList(section, items, "fact-list", "No signal captured.");
          card.appendChild(section);
        });
        axisRoot.appendChild(card);
      });
    }

    function renderPerspectiveCards(cardRoot, cards) {
      resetNode(cardRoot);
      if (!Array.isArray(cards) || cards.length === 0) {
        const empty = document.createElement("p");
        empty.className = "empty";
        empty.textContent = "No perspective cards were generated for this round.";
        cardRoot.appendChild(empty);
        return;
      }
      cards.forEach((card) => {
        const article = document.createElement("article");
        article.className = "persona-card";
        const header = document.createElement("div");
        header.className = "persona-card-header";
        const title = document.createElement("h3");
        title.className = "persona-role";
        title.textContent = safeText(card.persona, "Unknown persona");
        const body = document.createElement("p");
        body.className = "persona-signature";
        body.textContent = safeText(card.signature_line, "No signature line recorded.");
        header.appendChild(title);
        header.appendChild(body);
        article.appendChild(header);

        const meta = document.createElement("div");
        meta.className = "persona-meta";
        [
          ["Strongest Insight", card.strongest_insight],
          ["Largest Blind Spot", card.largest_blind_spot],
          ["Fit Condition", card.fit_condition],
        ].forEach(([labelText, value]) => {
          if (!value) {
            return;
          }
          const item = document.createElement("div");
          item.className = "detail-item";
          const label = document.createElement("span");
          label.className = "mini-label";
          label.textContent = labelText;
          const line = document.createElement("strong");
          line.textContent = safeText(value, "");
          item.appendChild(label);
          item.appendChild(line);
          meta.appendChild(item);
        });
        article.appendChild(meta);
        cardRoot.appendChild(article);
      });
    }

    function renderCreationLayer(root, creationLayer) {
      resetNode(root);
      const groups = [
        ["Recommended Angle", [safeText(creationLayer.recommended_angle, "")]],
        ["Article Outline", creationLayer.article_outline || []],
        ["Video Outline", creationLayer.video_outline || []],
        ["Thread Outline", creationLayer.thread_outline || []],
        ["Research Gaps", creationLayer.research_gaps || []],
      ];
      groups.forEach(([titleText, items]) => {
        const column = document.createElement("section");
        column.className = "creation-column";
        const title = document.createElement("h3");
        title.textContent = titleText;
        column.appendChild(title);
        const normalized = Array.isArray(items) ? items.filter(Boolean) : [];
        appendList(column, normalized, "outline-list", "No material captured.");
        root.appendChild(column);
      });
    }

    function renderTrace(root, trace) {
      resetNode(root);
      [
        ["Claims", trace.claims || []],
        ["Materials", trace.materials || []],
      ].forEach(([titleText, items]) => {
        const column = document.createElement("section");
        const title = document.createElement("h3");
        title.textContent = titleText;
        column.appendChild(title);
        appendList(column, items, "trace-list", "No trace material recorded.");
        root.appendChild(column);
      });
    }

    function renderAuditSummary(root, payload, audit) {
      appendDetailItems(root, [
        { label: "Question", value: payload.question },
        { label: "Run State", value: payload.run_status },
        { label: "Result Grade", value: audit.status && audit.status.result_grade },
        { label: "Policy", value: audit.execution && audit.execution.execution_policy },
        {
          label: "Successful Personas",
          value: Array.isArray(audit.execution && audit.execution.successful_personas)
            ? String(audit.execution.successful_personas.length)
            : "",
        },
        {
          label: "Failed Personas",
          value: Array.isArray(audit.execution && audit.execution.failed_personas)
            ? String(audit.execution.failed_personas.length)
            : "",
        },
      ]);
    }

    function activateSurface(surface) {
      const target = surface === "studio" ? "studio" : "audit";
      document.querySelectorAll("[data-surface-panel]").forEach((panel) => {
        const isActive = panel.getAttribute("data-surface-panel") === target;
        panel.hidden = !isActive;
        panel.classList.toggle("is-active", isActive);
      });
      document.querySelectorAll("[data-surface]").forEach((button) => {
        const isActive = button.getAttribute("data-surface") === target;
        button.classList.toggle("is-active", isActive);
        button.setAttribute("aria-selected", isActive ? "true" : "false");
      });
    }

    fetch("./data.json")
      .then((response) => response.json())
      .then((payload) => {
        const studio = payload.studio || null;
        const audit = payload.audit || {};
        const hasStudio = Boolean(studio);
        const defaultSurface = payload.default_surface === "audit" || !hasStudio ? "audit" : "studio";

        document.getElementById("question-title").textContent = safeText(payload.question, "未找到议题");
        document.getElementById("header-summary").textContent = hasStudio
          ? "Studio keeps the round readable first. Audit stays available for evidence, execution, and reviewer checks."
          : "Studio is unavailable for this round, so the viewer defaults to the audit surface and keeps the failure summary readable.";
        document.getElementById("run-status").textContent = safeText(payload.run_status, "unknown");
        document.getElementById("result-grade").textContent = safeText(
          (studio && studio.status && studio.status.result_grade) || (audit.status && audit.status.result_grade),
          "unknown"
        );

        const studioButton = document.getElementById("surface-toggle-studio");
        studioButton.disabled = !hasStudio;
        document.getElementById("surface-toggle-audit").disabled = false;

        document.getElementById("studio-status").textContent = safeText(
          studio && studio.status && studio.status.label,
          hasStudio ? "Studio ready" : "Studio unavailable"
        );
        document.getElementById("studio-caption").textContent = hasStudio
          ? "Product-first briefing surface for judgment, tension, and creation direction."
          : "This round did not produce a usable Studio surface. Review the Audit surface for the failure summary and execution evidence.";
        document.getElementById("judgment-line").textContent = safeText(
          studio && studio.executive_judgment && studio.executive_judgment.one_line_judgment,
          hasStudio ? "No executive judgment recorded." : "Studio output is unavailable for blocked rounds."
        );
        appendDetailItems(document.getElementById("judgment-details"), [
          {
            label: "Best Use",
            value: studio && studio.executive_judgment && studio.executive_judgment.best_use,
          },
          {
            label: "Largest Risk",
            value: studio && studio.executive_judgment && studio.executive_judgment.largest_risk,
          },
        ]);
        const premiseRoot = document.getElementById("judgment-premises");
        resetNode(premiseRoot);
        appendList(
          premiseRoot,
          (studio && studio.executive_judgment && studio.executive_judgment.premises) || [],
          "fact-list",
          hasStudio ? "No premises recorded." : "No premises available because Studio was not emitted."
        );
        renderAxisMap(document.getElementById("tension-map"), (studio && studio.tension_map) || {});
        renderPerspectiveCards(document.getElementById("studio-cards"), (studio && studio.perspective_cards) || []);
        renderCreationLayer(document.getElementById("creation-layer"), (studio && studio.creation_layer) || {});
        renderTrace(document.getElementById("trace-grid"), (studio && studio.expandable_trace) || {});

        document.getElementById("audit-status").textContent = safeText(
          audit.status && audit.status.label,
          "Audit ready"
        );
        document.getElementById("audit-caption").textContent = hasStudio
          ? "Execution evidence, failure details, and full review payload for checking the round."
          : "Audit stays primary for blocked rounds so failure details remain readable without stale product surfaces.";
        renderAuditSummary(document.getElementById("audit-summary"), payload, audit);
        document.getElementById("audit-json").textContent = JSON.stringify(audit, null, 2);

        document.querySelectorAll("[data-surface]").forEach((button) => {
          button.addEventListener("click", () => {
            if (button.disabled) {
              return;
            }
            activateSurface(button.getAttribute("data-surface"));
          });
        });
        activateSurface(defaultSurface);
      })
      .catch(() => {
        document.getElementById("question-title").textContent = "无法加载 round 数据";
        document.getElementById("header-summary").textContent = "The viewer could not read data.json. Check the output directory and try again.";
        document.getElementById("run-status").textContent = "error";
        document.getElementById("result-grade").textContent = "unknown";
        document.getElementById("studio-status").textContent = "Studio unavailable";
        document.getElementById("audit-status").textContent = "Audit unavailable";
        document.getElementById("audit-json").textContent = "{}";
        activateSurface("audit");
      });
  </script>
</body>
</html>
"""
