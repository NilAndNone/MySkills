from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SECTION_HEADER_RE = re.compile(r"^\[(?P<name>[^\]]+)\]\s*$")


def build_round_payload(round_root: Path) -> dict[str, Any]:
    final_panel = _read_json(round_root / "synthesis" / "final_panel.json")
    personas: list[dict[str, Any]] = []
    question: str | None = None

    for persona_name in final_panel["personas"]:
        persona_payload = _build_persona_payload(round_root, persona_name)
        personas.append(persona_payload)
        if question is None:
            question = persona_payload["question"]

    return {
        "round_id": final_panel["run_id"],
        "question": question or "",
        "persona_count": len(personas),
        "personas": personas,
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


def _build_persona_payload(round_root: Path, persona: str) -> dict[str, Any]:
    packet_path = round_root / "packets" / persona / "packet.txt"
    ticket_path = round_root / "tickets" / f"{persona}.json"
    result_root = round_root / "results" / persona
    raw_result_path = result_root / "raw_result.json"
    attestation_path = result_root / "attestation.json"
    certified_path = result_root / "technical_certified_result.json"

    packet_text = packet_path.read_text(encoding="utf-8")
    ticket = _read_json(ticket_path)
    raw_result = _read_json(raw_result_path)
    attestation = _read_json(attestation_path)
    certified = _read_json(certified_path)

    parsed_packet = _parse_packet(packet_text)
    round_input = parsed_packet.get("round_input", {})

    return {
        "persona": persona,
        "profile_id": round_input.get("profile_id") or ticket.get("profile_id", ""),
        "question": round_input.get("question", ""),
        "packet_fingerprint": ticket.get("packet_fingerprint", ""),
        "packet_length": ticket.get("packet_length", len(packet_text)),
        "hard_constraints": parsed_packet.get("hard_constraints", []),
        "packet_text": packet_text,
        "packet_sections": parsed_packet,
        "raw_result": raw_result,
        "raw_result_text": raw_result_path.read_text(encoding="utf-8"),
        "attestation_text": attestation_path.read_text(encoding="utf-8"),
        "ticket_text": ticket_path.read_text(encoding="utf-8"),
        "certified_text": certified_path.read_text(encoding="utf-8"),
        "paths": {
            "packet": str(packet_path),
            "ticket": str(ticket_path),
            "raw_result": str(raw_result_path),
            "attestation": str(attestation_path),
            "certified": str(certified_path),
        },
        "evidence": {
            "ticket": ticket,
            "attestation": attestation,
            "certified": certified,
        },
        "status": certified.get("technical_status", raw_result.get("technical_status", "UNKNOWN")),
    }


def _parse_packet(packet_text: str) -> dict[str, Any]:
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for raw_line in packet_text.splitlines():
        match = SECTION_HEADER_RE.match(raw_line.strip())
        if match:
            current = match.group("name")
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(raw_line)

    parsed: dict[str, Any] = {}
    if "round_input" in sections:
        parsed["round_input"] = _parse_key_value_section(sections["round_input"])
    if "hard_constraints" in sections:
        parsed["hard_constraints"] = _parse_bullets(sections["hard_constraints"])
    if "external_materials" in sections:
        parsed["external_materials"] = "\n".join(sections["external_materials"]).strip()
    if "persona_material" in sections:
        parsed["persona_material"] = "\n".join(sections["persona_material"]).strip()
    return parsed


def _parse_key_value_section(lines: list[str]) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        pairs[key.strip()] = value.strip()
    return pairs


def _parse_bullets(lines: list[str]) -> list[str]:
    bullets: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
    return bullets


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _render_html_shell() -> str:
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Worldview Round Viewer</title>
  <style>
    :root {
      --bg: #f3f8ff;
      --bg-soft: #f8fbff;
      --surface: rgba(255, 255, 255, 0.86);
      --surface-strong: #ffffff;
      --line: rgba(42, 106, 255, 0.14);
      --line-strong: rgba(42, 106, 255, 0.24);
      --text: #12203a;
      --text-soft: #5d6d8a;
      --accent: #2d6bff;
      --accent-soft: rgba(45, 107, 255, 0.1);
      --ok: #1e9a67;
      --shadow: 0 18px 40px rgba(37, 76, 150, 0.08);
      --mono: "JetBrains Mono", "DejaVu Sans Mono", monospace;
      --sans: "IBM Plex Sans", "Noto Sans", "Segoe UI", sans-serif;
    }

    * { box-sizing: border-box; }
    html, body { margin: 0; min-height: 100%; }
    body {
      font-family: var(--sans);
      color: var(--text);
      background:
        radial-gradient(circle at top right, rgba(90, 146, 255, 0.17), transparent 32%),
        linear-gradient(180deg, #f8fbff 0%, #eef5ff 100%);
    }

    .shell {
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto 1fr;
    }

    .question-strip {
      position: sticky;
      top: 0;
      z-index: 20;
      backdrop-filter: blur(18px);
      background: rgba(248, 251, 255, 0.88);
      border-bottom: 1px solid var(--line);
      box-shadow: 0 8px 30px rgba(68, 108, 190, 0.06);
    }

    .question-inner {
      max-width: 1600px;
      margin: 0 auto;
      padding: 24px 28px 22px;
    }

    .eyebrow {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
      margin-bottom: 10px;
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--text-soft);
    }

    .eyebrow .pill {
      padding: 5px 10px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      font-weight: 600;
    }

    .question-body {
      font-size: clamp(20px, 2.2vw, 30px);
      line-height: 1.35;
      font-weight: 650;
      max-width: 1100px;
      letter-spacing: -0.02em;
    }

    .workspace {
      max-width: 1600px;
      width: 100%;
      margin: 0 auto;
      padding: 24px 28px 32px;
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr);
      gap: 24px;
    }

    .persona-rail,
    .panel,
    .evidence-panel details {
      background: var(--surface);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
    }

    .persona-rail {
      border-radius: 24px;
      overflow: hidden;
      align-self: start;
      position: sticky;
      top: 154px;
    }

    .persona-list {
      display: flex;
      flex-direction: column;
    }

    .persona-button {
      width: 100%;
      border: 0;
      border-bottom: 1px solid var(--line);
      background: transparent;
      text-align: left;
      padding: 14px 16px 14px 18px;
      cursor: pointer;
      transition: background 180ms ease, transform 180ms ease;
      position: relative;
      color: inherit;
    }

    .persona-button:hover {
      background: rgba(45, 107, 255, 0.05);
    }

    .persona-button.active {
      background: linear-gradient(90deg, rgba(45, 107, 255, 0.12), rgba(45, 107, 255, 0.03));
    }

    .persona-button.active::before {
      content: "";
      position: absolute;
      left: 0;
      top: 10px;
      bottom: 10px;
      width: 3px;
      border-radius: 999px;
      background: var(--accent);
    }

    .persona-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 6px;
    }

    .persona-name {
      font-size: 14px;
      font-weight: 650;
      letter-spacing: -0.01em;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--ok);
      box-shadow: 0 0 0 5px rgba(30, 154, 103, 0.12);
      flex: none;
    }

    .persona-subtitle {
      font-size: 12px;
      color: var(--text-soft);
      font-family: var(--mono);
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .content-stack {
      display: flex;
      flex-direction: column;
      gap: 18px;
      min-width: 0;
    }

    .io-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }

    .panel {
      border-radius: 26px;
      overflow: hidden;
      min-height: 420px;
    }

    .panel-head {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 12px;
      padding: 18px 22px 12px;
      border-bottom: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(246, 250, 255, 0.86));
    }

    .panel-title {
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--accent);
    }

    .panel-meta {
      font-size: 12px;
      color: var(--text-soft);
      font-family: var(--mono);
    }

    .panel-body {
      padding: 18px 22px 22px;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }

    .summary-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px 14px;
    }

    .summary-item {
      padding: 10px 12px;
      border-radius: 16px;
      background: var(--bg-soft);
      border: 1px solid var(--line);
    }

    .summary-label {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-soft);
      margin-bottom: 6px;
    }

    .summary-value {
      font-size: 13px;
      line-height: 1.5;
      word-break: break-word;
    }

    .summary-value.mono {
      font-family: var(--mono);
      font-size: 12px;
    }

    .section-block {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .section-block h3 {
      margin: 0;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-soft);
    }

    .text-block {
      margin: 0;
      font-size: 14px;
      line-height: 1.72;
      color: var(--text);
      white-space: pre-wrap;
      word-break: break-word;
    }

    .list-block {
      margin: 0;
      padding-left: 18px;
      display: grid;
      gap: 8px;
      color: var(--text);
    }

    .source-box {
      border-radius: 18px;
      border: 1px solid var(--line);
      background: #fbfdff;
      overflow: hidden;
    }

    .source-label {
      padding: 10px 14px;
      border-bottom: 1px solid var(--line);
      font-size: 12px;
      color: var(--text-soft);
      font-family: var(--mono);
    }

    pre {
      margin: 0;
      padding: 16px 18px 18px;
      overflow: auto;
      font-family: var(--mono);
      font-size: 12px;
      line-height: 1.6;
      color: #173056;
      white-space: pre-wrap;
      word-break: break-word;
    }

    .evidence-panel {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .evidence-panel > header {
      padding: 4px 2px;
    }

    .evidence-panel h2 {
      margin: 0 0 6px;
      font-size: 18px;
      letter-spacing: -0.02em;
    }

    .evidence-panel p {
      margin: 0;
      color: var(--text-soft);
      font-size: 13px;
      line-height: 1.6;
    }

    .evidence-panel details {
      border-radius: 20px;
      overflow: hidden;
    }

    .evidence-panel summary {
      list-style: none;
      cursor: pointer;
      padding: 16px 18px;
      font-weight: 650;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }

    .evidence-panel summary::-webkit-details-marker { display: none; }

    .path-line {
      font-family: var(--mono);
      font-size: 11px;
      color: var(--text-soft);
      word-break: break-all;
    }

    .empty {
      padding: 30px;
      color: var(--text-soft);
      font-size: 14px;
    }

    @media (max-width: 1100px) {
      .workspace {
        grid-template-columns: 1fr;
      }

      .persona-rail {
        position: static;
      }

      .persona-list {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      }

      .persona-button {
        border-right: 1px solid var(--line);
      }

      .io-grid {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 720px) {
      .question-inner,
      .workspace {
        padding-left: 16px;
        padding-right: 16px;
      }

      .summary-grid {
        grid-template-columns: 1fr;
      }

      .panel-body {
        padding: 16px;
      }

      pre {
        padding: 14px;
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <header class="question-strip">
      <div class="question-inner">
        <div class="eyebrow">
          <span class="pill">Worldview Round Viewer</span>
          <span id="round-id">Loading...</span>
          <span id="persona-count"></span>
        </div>
        <div class="question-body" id="question-body">Loading question...</div>
      </div>
    </header>
    <main class="workspace">
      <aside class="persona-rail">
        <div class="persona-list" id="persona-list"></div>
      </aside>
      <section class="content-stack">
        <div class="io-grid">
          <section class="panel">
            <div class="panel-head">
              <div class="panel-title">Input</div>
              <div class="panel-meta" id="input-path"></div>
            </div>
            <div class="panel-body" id="input-panel"></div>
          </section>
          <section class="panel">
            <div class="panel-head">
              <div class="panel-title">Output</div>
              <div class="panel-meta" id="output-path"></div>
            </div>
            <div class="panel-body" id="output-panel"></div>
          </section>
        </div>
        <section class="evidence-panel">
          <header>
            <h2>Evidence</h2>
            <p>下面放不方便读但需要核对的原始材料。</p>
          </header>
          <div id="evidence-panel"></div>
        </section>
      </section>
    </main>
  </div>

  <script>
    const state = { data: null, selectedIndex: 0 };

    function escapeHtml(text) {
      return String(text)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
    }

    function renderHeader() {
      document.getElementById('round-id').textContent = state.data.round_id;
      document.getElementById('persona-count').textContent = `${state.data.persona_count} personas`;
      document.getElementById('question-body').textContent = state.data.question;
    }

    function renderPersonaList() {
      const list = document.getElementById('persona-list');
      list.innerHTML = state.data.personas.map((persona, index) => `
        <button class="persona-button ${index === state.selectedIndex ? 'active' : ''}" data-index="${index}">
          <div class="persona-top">
            <div class="persona-name">${escapeHtml(persona.persona)}</div>
            <span class="status-dot" title="${escapeHtml(persona.status)}"></span>
          </div>
          <div class="persona-subtitle">${escapeHtml(persona.profile_id || '')}</div>
        </button>
      `).join('');

      list.querySelectorAll('.persona-button').forEach((button) => {
        button.addEventListener('click', () => {
          state.selectedIndex = Number(button.dataset.index);
          renderPersonaList();
          renderSelectedPersona();
        });
      });
    }

    function renderSelectedPersona() {
      const persona = state.data.personas[state.selectedIndex];
      document.getElementById('input-path').textContent = persona.paths.packet;
      document.getElementById('output-path').textContent = persona.paths.raw_result;
      renderInput(persona);
      renderOutput(persona);
      renderEvidence(persona);
    }

    function renderInput(persona) {
      const panel = document.getElementById('input-panel');
      const constraints = (persona.hard_constraints || []).map((item) => `<li>${escapeHtml(item)}</li>`).join('');
      panel.innerHTML = `
        <div class="summary-grid">
          <div class="summary-item">
            <div class="summary-label">Persona</div>
            <div class="summary-value">${escapeHtml(persona.persona)}</div>
          </div>
          <div class="summary-item">
            <div class="summary-label">Profile</div>
            <div class="summary-value mono">${escapeHtml(persona.profile_id || '')}</div>
          </div>
          <div class="summary-item">
            <div class="summary-label">Question</div>
            <div class="summary-value">${escapeHtml(persona.question || '')}</div>
          </div>
          <div class="summary-item">
            <div class="summary-label">Packet Fingerprint</div>
            <div class="summary-value mono">${escapeHtml(persona.packet_fingerprint || '')}</div>
          </div>
        </div>
        <div class="section-block">
          <h3>Hard Constraints</h3>
          <ul class="list-block">${constraints || '<li>None</li>'}</ul>
        </div>
        <div class="source-box">
          <div class="source-label">${escapeHtml(persona.paths.packet)}</div>
          <pre>${escapeHtml(persona.packet_text)}</pre>
        </div>
      `;
    }

    function renderOutput(persona) {
      const panel = document.getElementById('output-panel');
      const result = persona.raw_result || {};
      const judgment = result.judgment || {};
      const diagnosis = (result.diagnosis || []).map((item) => `<li>${escapeHtml(item)}</li>`).join('');
      const actions = (result.recommended_actions || []).map((item) => `<li>${escapeHtml(item)}</li>`).join('');
      panel.innerHTML = `
        <div class="summary-grid">
          <div class="summary-item">
            <div class="summary-label">Signature</div>
            <div class="summary-value">${escapeHtml(result.signature_line || '')}</div>
          </div>
          <div class="summary-item">
            <div class="summary-label">Confidence</div>
            <div class="summary-value mono">${escapeHtml(result.confidence ?? '')}</div>
          </div>
        </div>
        <div class="section-block">
          <h3>Factual</h3>
          <p class="text-block">${escapeHtml(judgment.factual || '')}</p>
        </div>
        <div class="section-block">
          <h3>Value</h3>
          <p class="text-block">${escapeHtml(judgment.value || '')}</p>
        </div>
        <div class="section-block">
          <h3>Strategy</h3>
          <p class="text-block">${escapeHtml(judgment.strategy || '')}</p>
        </div>
        <div class="section-block">
          <h3>Diagnosis</h3>
          <ul class="list-block">${diagnosis || '<li>None</li>'}</ul>
        </div>
        <div class="section-block">
          <h3>Recommended Actions</h3>
          <ul class="list-block">${actions || '<li>None</li>'}</ul>
        </div>
        <div class="source-box">
          <div class="source-label">${escapeHtml(persona.paths.raw_result)}</div>
          <pre>${escapeHtml(persona.raw_result_text)}</pre>
        </div>
      `;
    }

    function renderEvidence(persona) {
      const evidence = document.getElementById('evidence-panel');
      const items = [
        ['ticket.json', persona.paths.ticket, persona.ticket_text],
        ['attestation.json', persona.paths.attestation, persona.attestation_text],
        ['technical_certified_result.json', persona.paths.certified, persona.certified_text],
      ];
      evidence.innerHTML = items.map(([label, path, text]) => `
        <details>
          <summary>
            <span>${escapeHtml(label)}</span>
            <span class="path-line">${escapeHtml(path)}</span>
          </summary>
          <pre>${escapeHtml(text)}</pre>
        </details>
      `).join('');
    }

    async function bootstrap() {
      const response = await fetch('./data.json', { cache: 'no-store' });
      state.data = await response.json();
      renderHeader();
      renderPersonaList();
      renderSelectedPersona();
    }

    bootstrap().catch((error) => {
      const target = document.getElementById('question-body');
      target.textContent = `Viewer failed to load: ${error.message}`;
      document.getElementById('persona-list').innerHTML = '<div class="empty">Unable to load personas.</div>';
    });
  </script>
</body>
</html>
"""
