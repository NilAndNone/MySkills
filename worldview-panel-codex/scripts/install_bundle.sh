#!/bin/sh
set -eu

SCRIPT_NAME="install_bundle.sh"
DEFAULT_REPO="NilAndNone/MySkills"
# This bundle currently ships from a feature branch. Switch back to main after merge.
DEFAULT_REF="dissociative_identity_disorder"
DEFAULT_SUBDIR="worldview-panel-codex"
START_MARKER="# >>> worldview-panel-codex managed block >>>"
END_MARKER="# <<< worldview-panel-codex managed block <<<"

usage() {
  cat <<'EOF'
Install the worldview-panel-codex bundle into the current user's Codex home.

Usage:
  sh install_bundle.sh [options]

Options:
  --source-dir PATH   Install from a local checkout instead of GitHub.
  --dest-home PATH    Destination home directory. Defaults to $HOME.
  --repo OWNER/REPO   GitHub repo for remote installs. Default: NilAndNone/MySkills
  --ref REF           Git ref for remote installs. Default: dissociative_identity_disorder
  --subdir PATH       Repo subdirectory containing this bundle. Default: worldview-panel-codex
  --force             Overwrite existing installed skill and agent files.
  --dry-run           Print actions without writing files.
  --help              Show this help text.
EOF
}

die() {
  echo "error: $*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

ensure_dir_writable() {
  dir_path=$1

  if [ -d "$dir_path" ]; then
    [ -w "$dir_path" ] || die "destination directory is not writable: $dir_path"
    return
  fi

  mkdir -p "$dir_path" 2>/dev/null || die "failed to create destination directory: $dir_path"
  [ -w "$dir_path" ] || die "destination directory is not writable: $dir_path"
}

fetch_remote_to_file() {
  rel_path=$1
  dest_path=$2
  url="https://raw.githubusercontent.com/$REPO/$REF/$SUBDIR/$rel_path"

  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$url" -o "$dest_path"
    return
  fi

  if command -v wget >/dev/null 2>&1; then
    wget -qO "$dest_path" "$url"
    return
  fi

  die "need curl or wget for remote installs"
}

copy_file() {
  src_path=$1
  dest_path=$2
  dest_dir=$(dirname "$dest_path")

  if [ "$DRY_RUN" -eq 1 ]; then
    echo "copy $src_path -> $dest_path"
    return
  fi

  ensure_dir_writable "$dest_dir"
  cp "$src_path" "$dest_path"
}

prepare_source_file() {
  rel_path=$1

  if [ -n "$SOURCE_DIR" ]; then
    src_path="$SOURCE_DIR/$rel_path"
    [ -f "$src_path" ] || die "missing source file: $src_path"
    printf '%s\n' "$src_path"
    return
  fi

  mkdir -p "$TMP_DIR/cache/$(dirname "$rel_path")"
  cached_path="$TMP_DIR/cache/$rel_path"
  fetch_remote_to_file "$rel_path" "$cached_path"
  printf '%s\n' "$cached_path"
}

managed_block_content() {
  snippet_file=$1
  printf '%s\n' "$START_MARKER"
  cat "$snippet_file"
  printf '\n%s\n' "$END_MARKER"
}

update_managed_snippet() {
  snippet_file=$1
  target_file=$2
  target_dir=$(dirname "$target_file")

  if [ "$DRY_RUN" -eq 1 ]; then
    echo "update managed block in $target_file from $snippet_file"
    return
  fi

  ensure_dir_writable "$target_dir"
  new_block="$TMP_DIR/managed_block.txt"
  managed_block_content "$snippet_file" >"$new_block"

  if [ ! -f "$target_file" ]; then
    cp "$new_block" "$target_file"
    return
  fi

  awk -v start="$START_MARKER" -v end="$END_MARKER" '
    BEGIN { skip = 0; replaced = 0 }
    $0 == start {
      skip = 1
      replaced = 1
      next
    }
    $0 == end {
      skip = 0
      next
    }
    skip == 0 { print }
    END { exit 0 }
  ' "$target_file" >"$TMP_DIR/original_without_block.txt"

  cp "$TMP_DIR/original_without_block.txt" "$TMP_DIR/merged_override.txt"
  if [ -s "$TMP_DIR/merged_override.txt" ]; then
    printf '\n' >>"$TMP_DIR/merged_override.txt"
  fi
  cat "$new_block" >>"$TMP_DIR/merged_override.txt"
  cp "$TMP_DIR/merged_override.txt" "$target_file"
}

SOURCE_DIR=""
DEST_HOME=${HOME:-}
REPO=$DEFAULT_REPO
REF=$DEFAULT_REF
SUBDIR=$DEFAULT_SUBDIR
FORCE=0
DRY_RUN=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --source-dir)
      [ "$#" -ge 2 ] || die "--source-dir requires a value"
      SOURCE_DIR=$2
      shift 2
      ;;
    --dest-home)
      [ "$#" -ge 2 ] || die "--dest-home requires a value"
      DEST_HOME=$2
      shift 2
      ;;
    --repo)
      [ "$#" -ge 2 ] || die "--repo requires a value"
      REPO=$2
      shift 2
      ;;
    --ref)
      [ "$#" -ge 2 ] || die "--ref requires a value"
      REF=$2
      shift 2
      ;;
    --subdir)
      [ "$#" -ge 2 ] || die "--subdir requires a value"
      SUBDIR=$2
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

[ -n "$DEST_HOME" ] || die "HOME is not set; pass --dest-home"

if [ -n "$SOURCE_DIR" ]; then
  [ -d "$SOURCE_DIR" ] || die "missing source directory: $SOURCE_DIR"
else
  if ! command -v curl >/dev/null 2>&1 && ! command -v wget >/dev/null 2>&1; then
    die "need curl or wget for remote installs"
  fi
fi

require_cmd cp
require_cmd dirname
require_cmd mktemp

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT INT TERM

if [ "$DRY_RUN" -ne 1 ]; then
  ensure_dir_writable "$DEST_HOME"
fi

if [ -n "$SOURCE_DIR" ]; then
  MANIFEST_FILE="$SOURCE_DIR/install/manifest.txt"
  [ -f "$MANIFEST_FILE" ] || die "missing manifest: $MANIFEST_FILE"
else
  MANIFEST_FILE="$TMP_DIR/manifest.txt"
  fetch_remote_to_file "install/manifest.txt" "$MANIFEST_FILE"
fi

SKILL_WORLDVIEW_CORE=0
SKILL_WORLDVIEW_PANEL=0
AGENT_COUNT=0
SNIPPET_PRESENT=0

while IFS='|' read -r entry_kind source_rel dest_rel; do
  [ -n "$entry_kind" ] || continue

  case "$entry_kind" in
    copy)
      target_path="$DEST_HOME/$dest_rel"
      if [ -e "$target_path" ] && [ "$FORCE" -ne 1 ]; then
        die "target already exists: $target_path (rerun with --force to overwrite)"
      fi
      case "$dest_rel" in
        .codex/skills/worldview-core/*)
          SKILL_WORLDVIEW_CORE=1
          ;;
        .codex/skills/worldview-panel-codex/*)
          SKILL_WORLDVIEW_PANEL=1
          ;;
        .codex/agents/*.toml)
          AGENT_COUNT=$((AGENT_COUNT + 1))
          ;;
      esac
      ;;
    managed_snippet)
      SNIPPET_PRESENT=1
      ;;
    *)
      die "unknown manifest entry kind: $entry_kind"
      ;;
  esac
done <"$MANIFEST_FILE"

while IFS='|' read -r entry_kind source_rel dest_rel; do
  [ -n "$entry_kind" ] || continue

  source_path=$(prepare_source_file "$source_rel")
  target_path="$DEST_HOME/$dest_rel"

  case "$entry_kind" in
    copy)
      copy_file "$source_path" "$target_path"
      ;;
    managed_snippet)
      update_managed_snippet "$source_path" "$target_path"
      ;;
  esac
done <"$MANIFEST_FILE"

SKILL_COUNT=$((SKILL_WORLDVIEW_CORE + SKILL_WORLDVIEW_PANEL))

echo
echo "Installed $SKILL_COUNT skills into $DEST_HOME/.codex/skills"
echo "Installed $AGENT_COUNT agents into $DEST_HOME/.codex/agents"
if [ "$SNIPPET_PRESENT" -eq 1 ]; then
  echo "Updated $DEST_HOME/.codex/AGENTS.override.md"
fi
echo "Project-level .codex/config.toml was not installed."
echo "Restart Codex to pick up new skills."
