"""Test package setup for the src-layout workspace."""

from __future__ import annotations

import shutil
import sys
import tempfile
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class WorkspaceTemporaryDirectory:
    """TemporaryDirectory replacement that avoids sandbox-denied temp dirs."""

    def __init__(self, suffix: str | None = None, prefix: str | None = None, dir: str | None = None):
        base = Path(dir) if dir is not None else ROOT / ".tmp_test"
        base.mkdir(parents=True, exist_ok=True)
        name_prefix = prefix or "tmp"
        name_suffix = suffix or ""
        self.name = str(base / f"{name_prefix}{uuid.uuid4().hex}{name_suffix}")
        Path(self.name).mkdir(parents=False, exist_ok=False)

    def cleanup(self) -> None:
        shutil.rmtree(self.name, ignore_errors=True)

    def __enter__(self) -> str:
        return self.name

    def __exit__(self, exc_type, exc, tb) -> None:
        self.cleanup()


tempfile.TemporaryDirectory = WorkspaceTemporaryDirectory
