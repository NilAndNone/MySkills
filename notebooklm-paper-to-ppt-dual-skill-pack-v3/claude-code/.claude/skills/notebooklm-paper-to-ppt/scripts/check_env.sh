#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIN_NLM_VERSION="0.3.5"
report_missing=0

check_cmd() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "[OK] $cmd found: $(command -v "$cmd")"
  else
    echo "[ERR] $cmd not found"
    report_missing=1
  fi
}

extract_semver() {
  python3 - "$1" <<'PY'
import re, sys
text = sys.argv[1]
m = re.search(r'(\d+\.\d+\.\d+)', text)
print(m.group(1) if m else '')
PY
}

version_ge() {
  python3 - "$1" "$2" <<'PY'
import sys
from itertools import zip_longest

def parse(v):
    return [int(x) for x in v.split('.')]

a = parse(sys.argv[1])
b = parse(sys.argv[2])
for x, y in zip_longest(a, b, fillvalue=0):
    if x > y:
        print('1')
        raise SystemExit
    if x < y:
        print('0')
        raise SystemExit
print('1')
PY
}

echo "== basic commands =="
check_cmd uv
check_cmd python3
check_cmd claude
check_cmd nlm
check_cmd notebooklm-mcp

if [ "$report_missing" -ne 0 ]; then
  echo
  echo "Missing commands detected. Fix those first."
  exit 1
fi

echo
echo "== nlm version =="
set +e
version_raw="$(nlm --version 2>&1)"
version_status=$?
set -e
printf '%s\n' "$version_raw"
if [ "$version_status" -ne 0 ]; then
  echo "[WARN] 'nlm --version' returned non-zero."
  exit "$version_status"
fi
version_parsed="$(extract_semver "$version_raw")"
if [ -z "$version_parsed" ]; then
  echo "[WARN] Could not parse a semantic version from nlm output."
  exit 1
fi
if [ "$(version_ge "$version_parsed" "$MIN_NLM_VERSION")" != "1" ]; then
  echo "[WARN] nlm version $version_parsed is older than required minimum $MIN_NLM_VERSION for PPTX slide-deck download."
  exit 1
fi
echo "[OK] nlm version $version_parsed >= $MIN_NLM_VERSION"

echo
echo "== NotebookLM auth =="
if nlm login --check; then
  echo "[OK] NotebookLM login check passed"
else
  echo "[ERR] NotebookLM login check failed"
  echo "Run: nlm login"
  exit 1
fi

echo
echo "== nlm doctor =="
set +e
nlm doctor
doctor_status=$?
set -e
if [ "$doctor_status" -ne 0 ]; then
  echo "[WARN] 'nlm doctor' returned non-zero. Read the output above."
  exit "$doctor_status"
fi

echo
echo "== PPTX postprocess helpers =="
if [ -f "$SCRIPT_DIR/export_pptx_slide_images.py" ]; then
  python3 "$SCRIPT_DIR/export_pptx_slide_images.py" --help >/dev/null
  echo "[OK] export_pptx_slide_images.py is present and runnable"
else
  echo "[WARN] export_pptx_slide_images.py is missing"
  exit 1
fi
if [ -f "$SCRIPT_DIR/inject_pptx_speaker_notes.py" ]; then
  python3 "$SCRIPT_DIR/inject_pptx_speaker_notes.py" --help >/dev/null
  echo "[OK] inject_pptx_speaker_notes.py is present and runnable"
else
  echo "[WARN] inject_pptx_speaker_notes.py is missing"
  exit 1
fi
if [ -f "$SCRIPT_DIR/postprocess_downloaded_pptx.py" ]; then
  python3 "$SCRIPT_DIR/postprocess_downloaded_pptx.py" --help >/dev/null
  echo "[OK] postprocess_downloaded_pptx.py is present and runnable"
else
  echo "[WARN] postprocess_downloaded_pptx.py is missing"
  exit 1
fi
if [ -f "$SCRIPT_DIR/fetch_web_source.py" ]; then
  python3 "$SCRIPT_DIR/fetch_web_source.py" --help >/dev/null
  echo "[OK] fetch_web_source.py is present and runnable"
else
  echo "[WARN] fetch_web_source.py is missing"
  exit 1
fi

echo
echo "== Claude Code MCP visibility =="
set +e
mcp_out="$(claude mcp list 2>&1)"
mcp_status=$?
set -e
printf '%s\n' "$mcp_out"
if [ "$mcp_status" -ne 0 ]; then
  echo "[WARN] 'claude mcp list' returned non-zero."
  exit "$mcp_status"
fi
if printf '%s' "$mcp_out" | grep -Ei 'notebooklm|notebooklm-mcp' >/dev/null 2>&1; then
  echo "[OK] NotebookLM MCP appears in Claude Code"
else
  echo "[WARN] NotebookLM MCP server not found in Claude Code output"
  exit 1
fi

echo
echo "[OK] Claude Code environment looks ready."
