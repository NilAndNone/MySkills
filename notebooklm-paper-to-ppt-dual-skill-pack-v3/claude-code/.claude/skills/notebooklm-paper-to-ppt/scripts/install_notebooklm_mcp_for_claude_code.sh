#!/usr/bin/env bash
set -euo pipefail

SERVER_NAME="${SERVER_NAME:-notebooklm}"
DEFAULT_LANG="${NOTEBOOKLM_HL:-en}"

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[ERROR] Missing command: $1" >&2
    exit 1
  fi
}

server_exists() {
  set +e
  local out
  out="$(claude mcp list 2>&1)"
  local status=$?
  set -e
  if [ "$status" -ne 0 ]; then
    return 1
  fi
  printf '%s' "$out" | grep -Ei 'notebooklm|notebooklm-mcp' >/dev/null 2>&1
}

echo "[1/5] Checking prerequisites..."
need_cmd uv
need_cmd claude

echo "[2/5] Installing/upgrading notebooklm-mcp-cli..."
if uv tool install notebooklm-mcp-cli >/dev/null 2>&1; then
  echo "  Installed notebooklm-mcp-cli"
else
  echo "  Install returned non-zero; trying upgrade..."
  uv tool upgrade notebooklm-mcp-cli
fi

need_cmd nlm
need_cmd notebooklm-mcp

echo "[3/5] Checking NotebookLM auth..."
if nlm login --check >/dev/null 2>&1; then
  echo "  NotebookLM login is already valid"
else
  echo "  Launching browser login via 'nlm login'..."
  nlm login
fi

echo "[4/5] Configuring MCP for Claude Code..."
set +e
nlm setup add claude-code >/tmp/nlm_setup_claude.out 2>/tmp/nlm_setup_claude.err
setup_status=$?
set -e

if [ "$setup_status" -eq 0 ]; then
  echo "  Configured via 'nlm setup add claude-code'"
else
  echo "  'nlm setup add claude-code' failed; trying manual Claude MCP registration..."
  set +e
  claude mcp add --transport stdio --scope user --env NOTEBOOKLM_HL="$DEFAULT_LANG" "$SERVER_NAME" -- uvx --from notebooklm-mcp-cli notebooklm-mcp
  manual_status=$?
  set -e
  if [ "$manual_status" -ne 0 ]; then
    if server_exists; then
      echo "  Claude Code already appears to have a NotebookLM MCP server. Treating as success."
    else
      echo "[ERROR] Could not configure Claude Code MCP." >&2
      echo "--- nlm setup stderr ---" >&2
      cat /tmp/nlm_setup_claude.err >&2 || true
      echo "--- nlm setup stdout ---" >&2
      cat /tmp/nlm_setup_claude.out >&2 || true
      exit "$manual_status"
    fi
  fi
fi

echo "[5/5] Verifying MCP visibility..."
set +e
claude mcp list
verify_status=$?
set -e
if [ "$verify_status" -ne 0 ]; then
  echo "[WARN] 'claude mcp list' returned non-zero. Check your Claude Code version."
fi

echo
echo "[OK] Claude Code MCP setup finished."
echo "Recommended next step:"
echo "  bash .claude/skills/notebooklm-paper-to-ppt/scripts/check_env.sh"
