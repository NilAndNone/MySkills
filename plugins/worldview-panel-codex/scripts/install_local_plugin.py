#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


PLUGIN_NAME = "worldview-panel-codex"
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
IGNORE_NAMES = shutil.ignore_patterns(".DS_Store", ".pytest_cache", "__pycache__", ".superpowers", "archive")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install the local worldview-panel-codex plugin for trial use.")
    parser.add_argument("--dest-home", default=os.environ.get("HOME"), help="Destination home directory.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing local trial install.")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing files.")
    return parser.parse_args()


def ensure_absent(path: Path, *, force: bool) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if not force:
        raise FileExistsError(f"target already exists: {path} (rerun with --force to overwrite)")
    if path.is_symlink() or path.is_file():
        path.unlink()
    else:
        shutil.rmtree(path)


def main() -> int:
    args = parse_args()
    if not args.dest_home:
        raise SystemExit("error: destination home is required")

    dest_home = Path(args.dest_home).expanduser().resolve()
    plugin_dest = dest_home / "plugins" / PLUGIN_NAME
    skills_link = dest_home / ".agents" / "skills" / PLUGIN_NAME
    actions = [
        f"copy {PLUGIN_ROOT} -> {plugin_dest}",
        f"symlink {skills_link} -> {plugin_dest / 'skills'}",
    ]
    if args.dry_run:
        print("\n".join(actions))
        return 0

    plugin_dest.parent.mkdir(parents=True, exist_ok=True)
    skills_link.parent.mkdir(parents=True, exist_ok=True)

    ensure_absent(plugin_dest, force=args.force)
    ensure_absent(skills_link, force=args.force)

    shutil.copytree(PLUGIN_ROOT, plugin_dest, ignore=IGNORE_NAMES)
    skills_link.symlink_to((plugin_dest / "skills").resolve(), target_is_directory=True)

    print(f"Installed local plugin to {plugin_dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
