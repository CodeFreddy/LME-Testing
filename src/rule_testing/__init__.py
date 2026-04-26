"""Backward-compatible alias for the renamed lme_testing package.

New code should import from lme_testing. This alias keeps older scripts,
saved patch targets, and historical commands from failing during migration.
"""

from __future__ import annotations

import importlib
import sys


_module = importlib.import_module("lme_testing")
sys.modules[__name__] = _module
