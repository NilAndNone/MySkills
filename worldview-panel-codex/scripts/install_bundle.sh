#!/bin/sh
set -eu

SCRIPT_NAME="install_bundle.sh"
DEFAULT_REPO="NilAndNone/MySkills"
# This bundle currently ships from a feature branch. Switch back to main after merge.
DEFAULT_REF="dissociative_identity_disorder"
DEFAULT_SUBDIR="worldview-panel-codex"

log() {
  echo "[$SCRIPT_NAME] $*" >&2
}

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

  log "fetching $rel_path from $url"

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

  log "installing $dest_path"

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
    log "using local source $src_path"
    printf '%s\n' "$src_path"
    return
  fi

  mkdir -p "$TMP_DIR/cache/$(dirname "$rel_path")"
  cached_path="$TMP_DIR/cache/$rel_path"
  fetch_remote_to_file "$rel_path" "$cached_path"
  printf '%s\n' "$cached_path"
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
  SOURCE_DESC="local source $SOURCE_DIR"
else
  SOURCE_DESC="remote source $REPO@$REF/$SUBDIR"
fi

if [ "$DRY_RUN" -eq 1 ]; then
  MODE_DESC="dry-run"
else
  MODE_DESC="apply"
fi

log "starting install in $MODE_DESC mode"
log "destination home: $DEST_HOME"
log "bundle source: $SOURCE_DESC"
if [ "$FORCE" -eq 1 ]; then
  log "force overwrite enabled"
fi

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
log "created temp dir $TMP_DIR"

if [ "$DRY_RUN" -ne 1 ]; then
  ensure_dir_writable "$DEST_HOME"
  log "destination is writable"
fi

if [ -n "$SOURCE_DIR" ]; then
  MANIFEST_FILE="$SOURCE_DIR/scripts/install/manifest.txt"
  [ -f "$MANIFEST_FILE" ] || die "missing manifest: $MANIFEST_FILE"
else
  MANIFEST_FILE="$TMP_DIR/manifest.txt"
  fetch_remote_to_file "scripts/install/manifest.txt" "$MANIFEST_FILE"
fi
log "loaded manifest $MANIFEST_FILE"

SKILL_COUNT=0
AGENT_COUNT=0
LEGACY_WORLDVIEW_CORE_PRESENT=0

if [ -e "$DEST_HOME/.codex/skills/worldview-core" ]; then
  LEGACY_WORLDVIEW_CORE_PRESENT=1
fi

log "validating manifest targets"

while IFS='|' read -r entry_kind source_rel dest_rel; do
  [ -n "$entry_kind" ] || continue

  case "$entry_kind" in
    copy)
      target_path="$DEST_HOME/$dest_rel"
      if [ -e "$target_path" ] && [ "$FORCE" -ne 1 ]; then
        die "target already exists: $target_path (rerun with --force to overwrite)"
      fi
      log "validated target $target_path"
      case "$dest_rel" in
        .codex/skills/worldview-panel-codex/*)
          SKILL_COUNT=1
          ;;
        .codex/agents/*.toml)
          AGENT_COUNT=$((AGENT_COUNT + 1))
          ;;
      esac
      ;;
    *)
      die "unknown manifest entry kind: $entry_kind"
      ;;
  esac
done <"$MANIFEST_FILE"

log "starting file install pass"

while IFS='|' read -r entry_kind source_rel dest_rel; do
  [ -n "$entry_kind" ] || continue

  source_path=$(prepare_source_file "$source_rel")
  target_path="$DEST_HOME/$dest_rel"

  case "$entry_kind" in
    copy)
      copy_file "$source_path" "$target_path"
      ;;
  esac
done <"$MANIFEST_FILE"

echo
SKILL_LABEL="skills"
if [ "$SKILL_COUNT" -eq 1 ]; then
  SKILL_LABEL="skill"
fi
echo "Installed $SKILL_COUNT $SKILL_LABEL into $DEST_HOME/.codex/skills"
echo "Installed $AGENT_COUNT persona agents into $DEST_HOME/.codex/agents"
if [ "$LEGACY_WORLDVIEW_CORE_PRESENT" -eq 1 ]; then
  echo "Legacy $DEST_HOME/.codex/skills/worldview-core was not modified."
  echo "Remove it manually if you want a clean single-skill install."
fi
echo "The installer does not modify generic built-in agents or ~/.codex/AGENTS.override.md."
echo "Project-level .codex/config.toml was not installed."
echo "Restart Codex to pick up new skills."
