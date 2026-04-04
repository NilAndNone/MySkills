#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


PLUGIN_NAME = "worldview-panel-codex"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Uninstall the local worldview-panel-codex trial plugin.")
    parser.add_argument("--dest-home", default=os.environ.get("HOME"), help="Destination home directory.")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without removing files.")
    return parser.parse_args()


def remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
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
    actions = [f"remove {plugin_dest}", f"remove {skills_link}"]
    if args.dry_run:
        print("\n".join(actions))
        return 0

    remove_path(plugin_dest)
    remove_path(skills_link)

    print(f"Removed local plugin from {dest_home}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
