from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "src" / "skills" / "worldview-panel-codex" / "tools"
PANEL_LOG_CLI = TOOLS_DIR / "panel_log.py"
PERSONA_MATERIALS_CLI = TOOLS_DIR / "persona_materials.py"
PREPARE_CONTEXT_CLI = TOOLS_DIR / "prepare_context_packets.py"
EXPORT_CACHE_CLI = TOOLS_DIR / "export_panel_cache.py"
RENDER_SITE_CLI = TOOLS_DIR / "render_panel_site.py"
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "context_packets" / "round_input.json"


def total_log_path(codex_home: Path) -> Path:
    return codex_home / "log" / "worldview-panel-codex.log"


def run_log_path(codex_home: Path, run_id: str) -> Path:
    return codex_home / "log" / "worldview-panel-codex" / "runs" / f"{run_id}.log"


def base_env(codex_home: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)
    return env


class PanelLoggingIntegrationTests(unittest.TestCase):
    def test_panel_log_cli_appends_to_total_log_and_run_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            codex_home = Path(tmpdir) / ".codex"
            run_id = "panel-demo"

            first = subprocess.run(
                [
                    "python3",
                    str(PANEL_LOG_CLI),
                    "--component",
                    "worldview_panel",
                    "--run-id",
                    run_id,
                    "--stage",
                    "run_start",
                    "--status",
                    "started",
                    "--message",
                    "starting panel run",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=base_env(codex_home),
            )
            second = subprocess.run(
                [
                    "python3",
                    str(PANEL_LOG_CLI),
                    "--component",
                    "worldview_panel",
                    "--run-id",
                    run_id,
                    "--stage",
                    "run_end",
                    "--status",
                    "completed",
                    "--message",
                    "panel run finished",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=base_env(codex_home),
            )

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertTrue(total_log_path(codex_home).is_file())
            self.assertTrue(run_log_path(codex_home, run_id).is_file())

            total_text = total_log_path(codex_home).read_text(encoding="utf-8")
            run_text = run_log_path(codex_home, run_id).read_text(encoding="utf-8")
            self.assertIn("run=panel-demo", total_text)
            self.assertIn("stage=run_start", total_text)
            self.assertIn("stage=run_end", total_text)
            self.assertIn("status=completed", total_text)
            self.assertIn("starting panel run", run_text)
            self.assertIn("panel run finished", run_text)

    def test_persona_materials_cli_writes_success_logs_with_matching_run_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            codex_home = Path(tmpdir) / ".codex"
            run_id = "materials-demo"
            proc = subprocess.run(
                [
                    "python3",
                    str(PERSONA_MATERIALS_CLI),
                    "--persona",
                    "techno_optimist",
                    "--domain",
                    "career",
                    "--json",
                    "--run-id",
                    run_id,
                ],
                check=False,
                capture_output=True,
                text=True,
                env=base_env(codex_home),
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["persona"], "techno_optimist")

            total_text = total_log_path(codex_home).read_text(encoding="utf-8")
            run_text = run_log_path(codex_home, run_id).read_text(encoding="utf-8")
            self.assertIn("component=persona_materials", total_text)
            self.assertIn("stage=material_prepare", total_text)
            self.assertIn("status=started", total_text)
            self.assertIn("status=completed", total_text)
            self.assertIn("persona=techno_optimist", run_text)
            self.assertIn("domain=career", run_text)

    def test_prepare_context_packets_cli_writes_success_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            codex_home = Path(tmpdir) / ".codex"
            output_root = Path(tmpdir) / "round-output"
            run_id = "prep-demo"
            proc = subprocess.run(
                [
                    "python3",
                    str(PREPARE_CONTEXT_CLI),
                    "--input",
                    str(FIXTURE_PATH),
                    "--stage",
                    "all",
                    "--output-root",
                    str(output_root),
                    "--json",
                    "--run-id",
                    run_id,
                ],
                check=False,
                capture_output=True,
                text=True,
                env=base_env(codex_home),
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertTrue(Path(payload["round_root"]).is_dir())

            total_text = total_log_path(codex_home).read_text(encoding="utf-8")
            run_text = run_log_path(codex_home, run_id).read_text(encoding="utf-8")
            self.assertIn("component=prepare_context_packets", total_text)
            self.assertIn("stage=context_prepare", total_text)
            self.assertIn("status=completed", total_text)
            self.assertIn("personas=2", run_text)

    def test_export_panel_cache_cli_logs_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            codex_home = Path(tmpdir) / ".codex"
            invalid_json = Path(tmpdir) / "invalid.json"
            invalid_json.write_text("{not json}", encoding="utf-8")
            run_id = "export-fail-demo"
            proc = subprocess.run(
                [
                    "python3",
                    str(EXPORT_CACHE_CLI),
                    "--input",
                    str(invalid_json),
                    "--run-id",
                    run_id,
                ],
                check=False,
                capture_output=True,
                text=True,
                env=base_env(codex_home),
            )

            self.assertEqual(proc.returncode, 1)
            total_text = total_log_path(codex_home).read_text(encoding="utf-8")
            run_text = run_log_path(codex_home, run_id).read_text(encoding="utf-8")
            self.assertIn("component=export_panel_cache", total_text)
            self.assertIn("stage=cache_export", total_text)
            self.assertIn("status=failed", total_text)
            self.assertIn("input JSON is invalid", run_text)

    def test_render_panel_site_cli_logs_validation_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            codex_home = Path(tmpdir) / ".codex"
            invalid_root = Path(tmpdir) / "empty-md-root"
            invalid_root.mkdir()
            run_id = "render-fail-demo"
            proc = subprocess.run(
                [
                    "python3",
                    str(RENDER_SITE_CLI),
                    "--md-root",
                    str(invalid_root),
                    "--validate-only",
                    "--run-id",
                    run_id,
                ],
                check=False,
                capture_output=True,
                text=True,
                env=base_env(codex_home),
            )

            self.assertEqual(proc.returncode, 1)
            total_text = total_log_path(codex_home).read_text(encoding="utf-8")
            run_text = run_log_path(codex_home, run_id).read_text(encoding="utf-8")
            self.assertIn("component=render_panel_site", total_text)
            self.assertIn("stage=site_validate", total_text)
            self.assertIn("status=failed", total_text)
            self.assertIn("validation failed", run_text)


if __name__ == "__main__":
    unittest.main()
