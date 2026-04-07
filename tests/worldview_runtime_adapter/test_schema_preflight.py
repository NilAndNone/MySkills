from __future__ import annotations

import unittest

from worldview_runtime_adapter import schema_preflight, schema_store


class TestSchemaPreflight(unittest.TestCase):
    def test_schema_store_loads_worldview_worker_schema(self) -> None:
        schema = schema_store.load_worker_schema("worldview_worker_result_v1")

        self.assertEqual(schema["$id"], "worldview_worker_result_v1")

    def test_schema_store_loads_missing_schema_fails(self) -> None:
        with self.assertRaises(FileNotFoundError):
            schema_store.load_worker_schema("missing_schema_name")

    def test_preflight_repairs_root_and_nested_object_contract(self) -> None:
        raw_schema = schema_store.load_worker_schema("worldview_worker_result_v1")

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

    def test_preflight_adds_explicit_type_for_const_only_schema_version(self) -> None:
        raw_schema = schema_store.load_worker_schema("worldview_worker_result_v1")

        outcome = schema_preflight.prepare_output_schema(
            raw_schema,
            schema_version="worldview_worker_result_v1",
        )

        schema_version_schema = outcome["effective_schema"]["properties"]["schema_version"]
        self.assertEqual(schema_version_schema["const"], "worldview_worker_result_v1")
        self.assertEqual(schema_version_schema["type"], "string")

    def test_preflight_rejects_unknown_schema_without_overlay(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported runtime schema"):
            schema_preflight.prepare_output_schema({"type": "object"}, schema_version="unknown_schema_v9")


if __name__ == "__main__":
    unittest.main()
