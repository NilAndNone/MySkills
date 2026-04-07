from __future__ import annotations

import unittest
from pathlib import Path


class TestNoPluginDependency(unittest.TestCase):
    def test_plugin_bridge_file_is_removed(self) -> None:
        root = Path(__file__).resolve().parents[2]
        self.assertFalse((root / "worldview_runtime_adapter" / "plugin_bridge.py").exists())

    def test_supported_runtime_files_do_not_reference_plugin_paths(self) -> None:
        root = Path(__file__).resolve().parents[2] / "worldview_runtime_adapter"
        forbidden_terms = (
            "plugin_bridge",
            "plugins/worldview-panel-codex",
            "run_worldview_broker.py",
            "worldview_contracts",
            "worldview_round_builder",
        )

        for path in sorted(root.glob("*.py")):
            if path.name in {"__init__.py", "plugin_bridge.py"}:
                continue
            text = path.read_text(encoding="utf-8")
            for term in forbidden_terms:
                self.assertNotIn(
                    term,
                    text,
                    f"{path} should not reference '{term}' after plugin-bridge removal"
                )


if __name__ == "__main__":
    unittest.main()
