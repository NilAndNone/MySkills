from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = PLUGIN_ROOT / "scripts" / "install_local_plugin.py"
UNINSTALLER = PLUGIN_ROOT / "scripts" / "uninstall_local_plugin.py"
PERSONA_INDEX = json.loads((PLUGIN_ROOT / "runtime" / "persona-index.json").read_text(encoding="utf-8"))
STALE_AGENT_FILENAMES = [f"{persona['name']}.toml" for persona in PERSONA_INDEX]


class LocalPluginInstallTests(unittest.TestCase):
    def test_install_local_plugin_sets_up_plugin_skills_without_static_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_home = Path(tmpdir) / "home"
            proc = subprocess.run(
                [
                    "python3",
                    str(INSTALLER),
                    "--dest-home",
                    str(dest_home),
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            installed_plugin = dest_home / "plugins" / "worldview-panel-codex"
            self.assertTrue(installed_plugin.is_dir())
            self.assertTrue((installed_plugin / ".codex-plugin" / "plugin.json").is_file())
            self.assertFalse((installed_plugin / "runtime" / "agents").exists())
            self.assertFalse((installed_plugin / "scripts" / "rebuild_agents.py").exists())

            skills_link = dest_home / ".agents" / "skills" / "worldview-panel-codex"
            self.assertTrue(skills_link.exists())
            self.assertTrue(skills_link.is_symlink())
            self.assertEqual(skills_link.resolve(), (installed_plugin / "skills").resolve())

            codex_agents = dest_home / ".codex" / "agents"
            self.assertFalse(codex_agents.exists())

    def test_install_local_plugin_removes_stale_agent_files_from_destination_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_home = Path(tmpdir) / "home"
            codex_agents = dest_home / ".codex" / "agents"
            codex_agents.mkdir(parents=True, exist_ok=True)
            stale_agent = codex_agents / STALE_AGENT_FILENAMES[0]
            stale_agent.write_text("stale\n", encoding="utf-8")
            unrelated_agent = codex_agents / "unrelated.toml"
            unrelated_agent.write_text("keep\n", encoding="utf-8")

            proc = subprocess.run(
                [
                    "python3",
                    str(INSTALLER),
                    "--dest-home",
                    str(dest_home),
                    "--force",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse(stale_agent.exists())
            self.assertTrue(unrelated_agent.exists())

    def test_uninstall_local_plugin_removes_plugin_symlink_and_leaves_no_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_home = Path(tmpdir) / "home"
            install = subprocess.run(
                [
                    "python3",
                    str(INSTALLER),
                    "--dest-home",
                    str(dest_home),
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
            )
            self.assertEqual(install.returncode, 0, install.stderr)

            codex_agents = dest_home / ".codex" / "agents"
            codex_agents.mkdir(parents=True, exist_ok=True)
            stale_agent = codex_agents / STALE_AGENT_FILENAMES[1]
            stale_agent.write_text("stale\n", encoding="utf-8")
            unrelated_agent = codex_agents / "unrelated.toml"
            unrelated_agent.write_text("keep\n", encoding="utf-8")

            uninstall = subprocess.run(
                [
                    "python3",
                    str(UNINSTALLER),
                    "--dest-home",
                    str(dest_home),
                ],
                check=False,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
            )

            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)
            self.assertFalse((dest_home / "plugins" / "worldview-panel-codex").exists())
            self.assertFalse((dest_home / ".agents" / "skills" / "worldview-panel-codex").exists())
            self.assertFalse(stale_agent.exists())
            self.assertTrue(unrelated_agent.exists())


if __name__ == "__main__":
    unittest.main()
