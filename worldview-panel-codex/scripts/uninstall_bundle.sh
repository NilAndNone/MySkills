#!/bin/sh
set -eu

SCRIPT_NAME="uninstall_bundle.sh"
DEFAULT_REPO="NilAndNone/MySkills"
DEFAULT_REF="dissociative_identity_disorder"
DEFAULT_SUBDIR="worldview-panel-codex"

log() {
  echo "[$SCRIPT_NAME] $*" >&2
}

usage() {
  cat <<'EOF'
Uninstall the worldview-panel-codex bundle from the current user's Codex home.

Usage:
  sh uninstall_bundle.sh [options]

Options:
  --source-dir PATH   Read the manifest from a local checkout instead of GitHub.
  --dest-home PATH    Destination home directory. Defaults to $HOME.
  --repo OWNER/REPO   GitHub repo for remote uninstalls. Default: NilAndNone/MySkills
  --ref REF           Git ref for remote uninstalls. Default: dissociative_identity_disorder
  --subdir PATH       Repo subdirectory containing this bundle. Default: worldview-panel-codex
  --force             Remove bundle files even if they differ from the bundled versions.
  --dry-run           Print actions without removing files.
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

  die "need curl or wget for remote uninstalls"
}

prepare_source_file() {
  rel_path=$1
  cached_dir="$TMP_DIR/cache/$(dirname "$rel_path")"
  cached_path="$TMP_DIR/cache/$rel_path"

  mkdir -p "$cached_dir"

  if [ -n "$SOURCE_DIR" ]; then
    src_path="$SOURCE_DIR/$rel_path"
    if [ -f "$src_path" ] && [ -r "$src_path" ]; then
      log "using local source $src_path"
      printf '%s\n' "$src_path"
      return
    fi

    if command -v git >/dev/null 2>&1 && git -C "$SOURCE_DIR" rev-parse --show-toplevel >/dev/null 2>&1; then
      log "reading tracked source $rel_path from git"
      git -C "$SOURCE_DIR" show "HEAD:$SUBDIR/$rel_path" >"$cached_path" 2>/dev/null || die "missing source file: $src_path"
      printf '%s\n' "$cached_path"
      return
    fi

    if [ -e "$src_path" ]; then
      die "source file is not readable: $src_path"
    fi
    die "missing source file: $src_path"
  fi

  fetch_remote_to_file "$rel_path" "$cached_path"
  printf '%s\n' "$cached_path"
}

ensure_parent_writable() {
  target_path=$1
  parent_dir=$(dirname "$target_path")

  [ -d "$parent_dir" ] || die "missing destination directory: $parent_dir"
  [ -w "$parent_dir" ] || die "destination directory is not writable: $parent_dir"
}

prune_empty_parent_dirs() {
  dir_path=$1
  stop_dir="$DEST_HOME/.codex"

  while [ "$dir_path" != "$stop_dir" ] && [ "$dir_path" != "/" ]; do
    rmdir "$dir_path" 2>/dev/null || break
    dir_path=$(dirname "$dir_path")
  done
}

remove_bundle_file() {
  source_path=$1
  target_path=$2

  log "checking $target_path"

  [ -e "$target_path" ] || return 1
  [ ! -d "$target_path" ] || die "expected file but found directory: $target_path"

  if [ "$FORCE" -ne 1 ] && ! cmp -s "$source_path" "$target_path"; then
    echo "skip modified file: $target_path" >&2
    SKIPPED_MODIFIED=$((SKIPPED_MODIFIED + 1))
    return 1
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    echo "remove $target_path"
    return 0
  fi

  ensure_parent_writable "$target_path"
  log "removing file $target_path"
  rm -f "$target_path"
  prune_empty_parent_dirs "$(dirname "$target_path")"
  return 0
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

log "starting uninstall in $MODE_DESC mode"
log "destination home: $DEST_HOME"
log "bundle source: $SOURCE_DESC"
if [ "$FORCE" -eq 1 ]; then
  log "force removal enabled"
fi

if [ -n "$SOURCE_DIR" ]; then
  [ -d "$SOURCE_DIR" ] || die "missing source directory: $SOURCE_DIR"
else
  if ! command -v curl >/dev/null 2>&1 && ! command -v wget >/dev/null 2>&1; then
    die "need curl or wget for remote uninstalls"
  fi
fi

require_cmd awk
require_cmd cmp
require_cmd dirname
require_cmd grep
require_cmd mktemp
require_cmd mv
require_cmd rm

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT INT TERM
log "created temp dir $TMP_DIR"

MANIFEST_FILE=$(prepare_source_file "scripts/install/manifest.txt")
log "loaded manifest $MANIFEST_FILE"

SKILL_FILE_COUNT=0
AGENT_COUNT=0
SKIPPED_MODIFIED=0

log "starting uninstall pass"

while IFS='|' read -r entry_kind source_rel dest_rel; do
  [ -n "$entry_kind" ] || continue
  target_path="$DEST_HOME/$dest_rel"

  case "$entry_kind" in
    copy)
      source_path=$(prepare_source_file "$source_rel")
      if remove_bundle_file "$source_path" "$target_path"; then
        case "$dest_rel" in
          .codex/skills/worldview-panel-codex/*)
            SKILL_FILE_COUNT=$((SKILL_FILE_COUNT + 1))
            ;;
          .codex/agents/*.toml)
            AGENT_COUNT=$((AGENT_COUNT + 1))
            ;;
        esac
      fi
      ;;
    *)
      die "unknown manifest entry kind: $entry_kind"
      ;;
  esac
done <"$MANIFEST_FILE"

echo
echo "Removed $SKILL_FILE_COUNT skill files from $DEST_HOME/.codex/skills/worldview-panel-codex"
echo "Removed $AGENT_COUNT persona agents from $DEST_HOME/.codex/agents"
if [ "$SKIPPED_MODIFIED" -gt 0 ]; then
  echo "Skipped $SKIPPED_MODIFIED modified files. Rerun with --force to remove them."
fi
echo "Uninstall does not modify generic built-in agents or ~/.codex/AGENTS.override.md."
echo "Uninstall does not restore files that were overwritten during install."
echo "Restart Codex to pick up removed skills and agents."
