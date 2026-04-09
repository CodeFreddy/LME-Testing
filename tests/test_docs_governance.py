from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.governance_checks import (
    check_artifact_governance,
    check_docs_governance,
)


class DocsGovernanceTests(unittest.TestCase):
    def test_docs_governance_requires_relative_local_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs_dir = root / "docs"
            docs_dir.mkdir()
            good = docs_dir / "good.md"
            good.write_text(
                "[local](./file.md)\n"
                "[parent](../README.md)\n"
                "[anchor](#section)\n"
                "[web](https://example.com)\n",
                encoding="utf-8",
            )
            bad = docs_dir / "bad.md"
            bad.write_text(
                "[bad1](/C:/repo/docs/file.md)\n"
                "[bad2](file://C:/repo/docs/file.md)\n"
                "[bad3](/F:/repo/docs/file.md)\n",
                encoding="utf-8",
            )

            violations = check_docs_governance(root)

            self.assertEqual(len(violations), 3)
            self.assertTrue(all("bad.md" in item for item in violations))

    def test_artifact_governance_requires_minimum_baseline_shape(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent
        self.assertEqual(check_artifact_governance(repo_root), [])


if __name__ == "__main__":
    unittest.main()
