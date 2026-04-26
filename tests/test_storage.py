"""Unit tests for lme_testing/storage.py."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lme_testing import storage


class StorageTests(unittest.TestCase):
    """Tests for all public functions in lme_testing/storage.py."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.work_dir = Path(self.tmpdir.name)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_timestamp_slug_returns_valid_format(self) -> None:
        # Call multiple times; at least one should be unique if time advances
        slugs = [storage.timestamp_slug() for _ in range(5)]
        for slug in slugs:
            self.assertRegex(slug, r"^\d{8}T\d{6}(Z|[+-]\d{4})$")

    def test_ensure_dir_creates_directory_and_parents(self) -> None:
        nested = self.work_dir / "a" / "b" / "c"
        result = storage.ensure_dir(nested)
        self.assertTrue(nested.exists())
        self.assertTrue(nested.is_dir())
        self.assertEqual(result, nested)

    def test_ensure_dir_returns_existing_directory(self) -> None:
        result = storage.ensure_dir(self.work_dir)
        self.assertTrue(self.work_dir.exists())
        self.assertEqual(result, self.work_dir)

    def test_load_json_round_trips(self) -> None:
        data = {"key": "value", "number": 42, "list": [1, 2, 3]}
        path = self.work_dir / "data.json"
        storage.write_json(path, data)
        loaded = storage.load_json(path)
        self.assertEqual(loaded, data)

    def test_load_json_raises_on_invalid_json(self) -> None:
        path = self.work_dir / "invalid.json"
        path.write_text("{not valid json", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            storage.load_json(path)

    def test_load_json_raises_on_missing_file(self) -> None:
        path = self.work_dir / "missing.json"
        with self.assertRaises(FileNotFoundError):
            storage.load_json(path)

    def test_load_jsonl_parses_jsonl(self) -> None:
        lines = [
            {"id": 1, "name": "alice"},
            {"id": 2, "name": "bob"},
        ]
        path = self.work_dir / "data.jsonl"
        path.write_text("\n".join(json.dumps(l) for l in lines), encoding="utf-8")
        loaded = storage.load_jsonl(path)
        self.assertEqual(loaded, lines)

    def test_load_jsonl_skips_empty_lines(self) -> None:
        lines = [
            {"id": 1},
            "",
            {"id": 2},
            "   ",
        ]
        path = self.work_dir / "data.jsonl"
        path.write_text("\n".join(l if isinstance(l, str) else json.dumps(l) for l in lines), encoding="utf-8")
        loaded = storage.load_jsonl(path)
        self.assertEqual(loaded, [{"id": 1}, {"id": 2}])

    def test_load_jsonl_raises_on_malformed_line(self) -> None:
        path = self.work_dir / "bad.jsonl"
        path.write_text('{"id": 1}\n{invalid}\n', encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            storage.load_jsonl(path)

    def test_write_json_creates_file(self) -> None:
        data = {"key": "value"}
        path = self.work_dir / "out.json"
        storage.write_json(path, data)
        self.assertTrue(path.exists())
        loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(loaded, data)

    def test_write_json_raises_without_parent_dir(self) -> None:
        data = {"key": "value"}
        path = self.work_dir / "subdir" / "out.json"
        with self.assertRaises(FileNotFoundError):
            storage.write_json(path, data)

    def test_append_jsonl_appends_records(self) -> None:
        path = self.work_dir / "out.jsonl"
        storage.append_jsonl(path, [{"id": 1}])
        storage.append_jsonl(path, [{"id": 2}, {"id": 3}])
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        self.assertEqual(len(lines), 3)
        self.assertEqual(json.loads(lines[0]), {"id": 1})
        self.assertEqual(json.loads(lines[2]), {"id": 3})

    def test_append_jsonl_skips_empty_list(self) -> None:
        path = self.work_dir / "out.jsonl"
        path.write_text('{"id": 1}\n', encoding="utf-8")
        storage.append_jsonl(path, [])
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        self.assertEqual(len(lines), 1)

    def test_append_jsonl_creates_file_if_missing(self) -> None:
        path = self.work_dir / "new.jsonl"
        storage.append_jsonl(path, [{"id": 1}])
        self.assertTrue(path.exists())

    def test_append_jsonl_raises_without_parent_dir(self) -> None:
        path = self.work_dir / "newsub" / "new.jsonl"
        with self.assertRaises(FileNotFoundError):
            storage.append_jsonl(path, [{"id": 1}])


if __name__ == "__main__":
    unittest.main()

