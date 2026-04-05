from __future__ import annotations

import unittest

from worldview_runtime_adapter import plugin_bridge, schema_preflight


class TestSchemaPreflight(unittest.TestCase):
    def test_plugin_bridge_loads_worldview_worker_schema(self) -> None:
        schema = plugin_bridge.load_worker_schema("worldview_worker_result_v1")

        self.assertEqual(schema["$id"], "worldview_worker_result_v1")

    def test_preflight_repairs_root_and_nested_object_contract(self) -> None:
        raw_schema = plugin_bridge.load_worker_schema("worldview_worker_result_v1")

        outcome = schema_preflight.prepare_output_schema(
            raw_schema,
            schema_version="worldview_worker_result_v1",
        )

        self.assertEqual(outcome["status"], "repaired_in_memory")
        self.assertFalse(outcome["effective_schema"]["additionalProperties"])
        self.assertFalse(outcome["effective_schema"]["properties"]["judgment"]["additionalProperties"])
        self.assertEqual(
            outcome["effective_schema"]["properties"]["judgment"]["required"],
            ["factual", "value", "strategy"],
        )

    def test_preflight_rejects_unknown_schema_without_overlay(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported runtime schema"):
            schema_preflight.prepare_output_schema({"type": "object"}, schema_version="unknown_schema_v9")


if __name__ == "__main__":
    unittest.main()
