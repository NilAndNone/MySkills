#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIN_NLM_VERSION="0.3.5"

usage() {
  cat <<'EOF'
Usage:
  cli_flow_template.sh [options] <paper.pdf|paper_url> <output.pptx> [notebook_title]

Options:
  --title <name>            Explicit notebook title
  --timeout <sec>           Poll timeout for slide generation (default: 900)
  --interval <sec>          Poll interval seconds (default: 60)
  --query-timeout <sec>     Grounding query timeout seconds (default: 120)
  --non-interactive         Never prompt; fail instead of hanging
  --skip-grounding-query    Skip the readiness sanity-check query
  -h, --help                Show this help

Environment overrides:
  NLM_POLL_TIMEOUT_SEC      Same as --timeout
  NLM_POLL_INTERVAL_SEC     Same as --interval
  NLM_QUERY_TIMEOUT_SEC     Same as --query-timeout

Examples:
  cli_flow_template.sh ./papers/paper.pdf ./out/raw-deck.pptx
  cli_flow_template.sh --non-interactive ./paper.pdf ./out/raw-deck.pptx
EOF
}

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[ERROR] Missing command: $1" >&2
    exit 1
  fi
}

slugify() {
  python3 - "$1" <<'PY'
import re, sys
s = sys.argv[1].strip().lower()
s = re.sub(r'[^a-z0-9]+', '-', s)
s = re.sub(r'-+', '-', s).strip('-')
print(s or 'paper')
PY
}

extract_uuid() {
  python3 - "$1" <<'PY'
import re, sys
text = sys.argv[1]
m = re.search(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', text, re.I)
print(m.group(0) if m else '')
PY
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

ensure_min_nlm_version() {
  local raw ver ok
  set +e
  raw="$(nlm --version 2>&1)"
  local status=$?
  set -e
  if [ "$status" -ne 0 ]; then
    echo "[WARN] 'nlm --version' returned non-zero; skipping version gate." >&2
    return 0
  fi
  ver="$(extract_semver "$raw")"
  if [ -z "$ver" ]; then
    echo "[WARN] Could not parse an nlm version from: $raw" >&2
    return 0
  fi
  ok="$(version_ge "$ver" "$MIN_NLM_VERSION")"
  if [ "$ok" != "1" ]; then
    echo "[ERROR] Detected nlm version $ver, but PPTX slide-deck download needs at least $MIN_NLM_VERSION." >&2
    echo "[ERROR] Upgrade notebooklm-mcp-cli before running this template." >&2
    exit 1
  fi
  echo "[OK] nlm version $ver >= $MIN_NLM_VERSION"
}

extract_slide_artifact_from_json() {
  python3 - "$1" <<'PY'
import json, sys
raw = sys.argv[1].strip()
if not raw:
    print('')
    raise SystemExit
try:
    data = json.loads(raw)
except Exception:
    print('')
    raise SystemExit

completed_status = {'completed', 'done', 'ready', 3, '3'}
best = None

def walk(obj):
    global best
    if isinstance(obj, dict):
        lowered = {str(k).lower(): k for k in obj.keys()}
        artifact_type = obj.get(lowered.get('artifact_type', ''), obj.get('artifact_type'))
        status = obj.get(lowered.get('status', ''), obj.get('status'))
        artifact_id = (
            obj.get(lowered.get('artifact_id', ''), obj.get('artifact_id'))
            or obj.get(lowered.get('id', ''), obj.get('id'))
            or obj.get(lowered.get('uuid', ''), obj.get('uuid'))
        )
        if artifact_type in {'slide_deck', 'slides', 'slideDeck'} and artifact_id and status in completed_status:
            best = artifact_id
        for v in obj.values():
            walk(v)
    elif isinstance(obj, list):
        for item in obj:
            walk(item)

walk(data)
print(best or '')
PY
}

prompt_or_fail() {
  local var_name="$1"
  local message="$2"
  local value=""
  if [ "$NON_INTERACTIVE" -eq 1 ]; then
    echo "[ERROR] $message" >&2
    exit 2
  fi
  read -r -p "$message " value
  printf -v "$var_name" '%s' "$value"
}

SOURCE=""
OUTPUT=""
TITLE=""
NON_INTERACTIVE=0
SKIP_GROUNDING_QUERY=0
POLL_TIMEOUT_SEC="${NLM_POLL_TIMEOUT_SEC:-900}"
POLL_INTERVAL_SEC="${NLM_POLL_INTERVAL_SEC:-60}"
QUERY_TIMEOUT_SEC="${NLM_QUERY_TIMEOUT_SEC:-120}"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --title)
      TITLE="${2:-}"
      shift 2
      ;;
    --timeout)
      POLL_TIMEOUT_SEC="${2:-}"
      shift 2
      ;;
    --interval)
      POLL_INTERVAL_SEC="${2:-}"
      shift 2
      ;;
    --query-timeout)
      QUERY_TIMEOUT_SEC="${2:-}"
      shift 2
      ;;
    --non-interactive)
      NON_INTERACTIVE=1
      shift
      ;;
    --skip-grounding-query)
      SKIP_GROUNDING_QUERY=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "[ERROR] Unknown option: $1" >&2
      usage
      exit 1
      ;;
    *)
      break
      ;;
  esac
done

if [ ! -t 0 ]; then
  NON_INTERACTIVE=1
fi

if [ "${1:-}" = "" ] || [ "${2:-}" = "" ]; then
  usage
  exit 1
fi

SOURCE="$1"
OUTPUT="$2"
if [ -z "$TITLE" ]; then
  TITLE="${3:-}"
fi

need_cmd nlm
need_cmd python3
ensure_min_nlm_version

mkdir -p "$(dirname "$OUTPUT")"

if [ -z "$TITLE" ]; then
  base_name="$(basename "$SOURCE")"
  TITLE="${base_name%.*}"
fi

case "$POLL_TIMEOUT_SEC" in
  ''|*[!0-9]*)
    echo "[ERROR] --timeout must be an integer number of seconds" >&2
    exit 1
    ;;
esac
case "$POLL_INTERVAL_SEC" in
  ''|*[!0-9]*)
    echo "[ERROR] --interval must be an integer number of seconds" >&2
    exit 1
    ;;
esac
case "$QUERY_TIMEOUT_SEC" in
  ''|*[!0-9]*)
    echo "[ERROR] --query-timeout must be an integer number of seconds" >&2
    exit 1
    ;;
esac

MAX_ATTEMPTS=$(( (POLL_TIMEOUT_SEC + POLL_INTERVAL_SEC - 1) / POLL_INTERVAL_SEC ))
if [ "$MAX_ATTEMPTS" -lt 1 ]; then
  MAX_ATTEMPTS=1
fi

SLUG="$(slugify "$TITLE")"
ALIAS="ppt_${SLUG}_$RANDOM"

echo "[1/7] Checking NotebookLM auth..."
if ! nlm login --check >/dev/null 2>&1; then
  echo "NotebookLM login is invalid. Run: nlm login" >&2
  exit 1
fi

echo "[2/7] Creating notebook..."
create_output="$( (nlm notebook create "$TITLE" --quiet 2>/dev/null || nlm notebook create "$TITLE") 2>&1 )"
NOTEBOOK_ID="$(extract_uuid "$create_output")"

if [ -z "$NOTEBOOK_ID" ]; then
  echo "[WARN] Could not auto-parse notebook id from create output."
  echo "$create_output"
  prompt_or_fail NOTEBOOK_ID "Paste notebook id:"
fi

echo "Notebook id: $NOTEBOOK_ID"
nlm alias set "$ALIAS" "$NOTEBOOK_ID"

echo "[3/7] Adding source and waiting for ingestion..."
set +e
if [[ "$SOURCE" =~ ^https?:// ]]; then
  source_out="$(nlm source add "$ALIAS" --url "$SOURCE" --wait 2>&1)"
else
  source_out="$(nlm source add "$ALIAS" --file "$SOURCE" --wait 2>&1)"
fi
source_status=$?
set -e

if [ "$source_status" -ne 0 ]; then
  echo "[WARN] Source add failed on first attempt."
  echo "$source_out"
  echo "[INFO] Re-checking auth and retrying once..."
  nlm login --check >/dev/null 2>&1 || nlm login
  set +e
  if [[ "$SOURCE" =~ ^https?:// ]]; then
    source_out="$(nlm source add "$ALIAS" --url "$SOURCE" --wait 2>&1)"
  else
    source_out="$(nlm source add "$ALIAS" --file "$SOURCE" --wait 2>&1)"
  fi
  source_status=$?
  set -e
  if [ "$source_status" -ne 0 ]; then
    echo "[ERROR] Source add failed after one retry." >&2
    echo "$source_out" >&2
    exit "$source_status"
  fi
fi

if [ "$SKIP_GROUNDING_QUERY" -eq 0 ]; then
  echo "[4/7] Running grounding query..."
  set +e
  query_out="$(nlm notebook query "$ALIAS" "What is the paper's main contribution in one sentence?" --timeout "$QUERY_TIMEOUT_SEC" 2>&1)"
  query_status=$?
  set -e
  if [ "$query_status" -ne 0 ]; then
    echo "[ERROR] Grounding query failed." >&2
    echo "$query_out" >&2
    exit "$query_status"
  fi
  stripped="$(printf '%s' "$query_out" | tr -d '[:space:]')"
  if [ -z "$stripped" ]; then
    echo "[ERROR] Grounding query returned empty output; ingestion may not be ready." >&2
    exit 1
  fi
fi

echo "[5/7] Creating slide deck..."
nlm slides create "$ALIAS" --confirm

echo "[6/7] Polling status for a completed slide deck..."
ARTIFACT_ID=""
LAST_STATUS_OUT=""
for i in $(seq 1 "$MAX_ATTEMPTS"); do
  echo "  Poll attempt $i/$MAX_ATTEMPTS ..."
  LAST_STATUS_OUT="$( (nlm studio status "$ALIAS" --json 2>/dev/null || nlm studio status "$ALIAS") 2>&1 )"
  ARTIFACT_ID="$(extract_slide_artifact_from_json "$LAST_STATUS_OUT")"
  if [ -n "$ARTIFACT_ID" ]; then
    break
  fi
  sleep "$POLL_INTERVAL_SEC"
done

if [ -z "$ARTIFACT_ID" ]; then
  echo "[ERROR] Timed out waiting for a completed slide deck after ${POLL_TIMEOUT_SEC}s." >&2
  echo "Last status output:" >&2
  echo "$LAST_STATUS_OUT" >&2
  exit 1
fi

echo "Artifact id: $ARTIFACT_ID"

echo "[7/7] Downloading PPTX..."
nlm download slide-deck "$ALIAS" "$ARTIFACT_ID" --format pptx --output "$OUTPUT"

if [ ! -f "$OUTPUT" ]; then
  echo "[ERROR] Download command finished but output file is missing: $OUTPUT" >&2
  exit 1
fi

echo
echo "[OK] Finished."
echo "Notebook alias    : $ALIAS"
echo "Notebook id       : $NOTEBOOK_ID"
echo "Artifact id       : $ARTIFACT_ID"
echo "Downloaded deck   : $OUTPUT"
echo "Postprocess step  : python3 \"$SCRIPT_DIR/postprocess_downloaded_pptx.py\" prepare-context --input \"$OUTPUT\" --source-pdf <paper.pdf>"
echo
echo "This CLI template only downloads the PPTX. The Claude skill performs source-aware notes generation separately."
