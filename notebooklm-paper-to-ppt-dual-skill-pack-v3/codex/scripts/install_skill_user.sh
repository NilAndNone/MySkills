#!/usr/bin/env bash
set -euo pipefail

PACK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$PACK_ROOT/.agents/skills/notebooklm-paper-to-ppt"
DST_ROOT="${HOME}/.agents/skills"
DST="$DST_ROOT/notebooklm-paper-to-ppt"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$DST_ROOT"
if [ -e "$DST" ]; then
  BACKUP="${DST}.bak.${TIMESTAMP}"
  echo "[WARN] Existing Codex skill found. Backing it up to:"
  echo "  $BACKUP"
  mv "$DST" "$BACKUP"
fi
cp -R "$SRC" "$DST"

echo "[OK] Installed Codex user-level skill to:"
echo "  $DST"
echo
echo "Next:"
echo "  bash ~/.agents/skills/notebooklm-paper-to-ppt/scripts/install_notebooklm_mcp_for_codex.sh"
