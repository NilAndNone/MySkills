#!/usr/bin/env bash
set -euo pipefail
PACK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec bash "$PACK_ROOT/.agents/skills/notebooklm-paper-to-ppt/scripts/install_notebooklm_mcp_for_codex.sh"
