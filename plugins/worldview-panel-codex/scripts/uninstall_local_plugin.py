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
    agents_dest = dest_home / ".codex" / "agents"
    installed_root = plugin_dest if plugin_dest.is_dir() else Path(__file__).resolve().parents[1]
    agent_files = sorted((installed_root / "runtime" / "agents").glob("*.toml"))

    actions = [f"remove {plugin_dest}", f"remove {skills_link}"] + [f"remove {agents_dest / agent.name}" for agent in agent_files]
    if args.dry_run:
        print("\n".join(actions))
        return 0

    remove_path(plugin_dest)
    remove_path(skills_link)
    for agent_file in agent_files:
        remove_path(agents_dest / agent_file.name)

    print(f"Removed local plugin from {dest_home}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
