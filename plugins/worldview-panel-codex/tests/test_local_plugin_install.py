from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = PLUGIN_ROOT / "scripts" / "install_local_plugin.py"
UNINSTALLER = PLUGIN_ROOT / "scripts" / "uninstall_local_plugin.py"


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
            self.assertFalse((dest_home / ".codex" / "agents").exists())


if __name__ == "__main__":
    unittest.main()
