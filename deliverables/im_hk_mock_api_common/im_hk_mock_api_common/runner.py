"""Minimal reusable Gherkin runner for Initial Margin feature files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable


STEP_PREFIXES = ("Given ", "When ", "Then ", "And ")


def iter_step_lines(feature_path: Path) -> list[tuple[int, str]]:
    steps: list[tuple[int, str]] = []
    for line_no, raw in enumerate(feature_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw.strip()
        for prefix in STEP_PREFIXES:
            if stripped.startswith(prefix):
                steps.append((line_no, stripped[len(prefix):].strip()))
                break
    return steps


def run_feature(path: Path, context_factory: Callable[[], object], dispatch: Callable[[object, str], None]) -> tuple[int, int]:
    passed = 0
    failed = 0
    context = context_factory()
    print(f"\nFeature file: {path}")
    for line_no, step_text in iter_step_lines(path):
        try:
            dispatch(context, step_text)
            print(f"  PASS line {line_no}: {step_text}")
            passed += 1
        except Exception as exc:
            print(f"  FAIL line {line_no}: {step_text}")
            print(f"       {exc}")
            failed += 1
    return passed, failed


def main(
    *,
    description: str,
    default_feature_dir: str,
    context_factory: Callable[[], object],
    dispatch: Callable[[object, str], None],
) -> int:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "features",
        nargs="*",
        default=[default_feature_dir],
        help=f"Feature files or directories. Default: {default_feature_dir}",
    )
    args = parser.parse_args()

    feature_files: list[Path] = []
    for item in args.features:
        path = Path(item)
        if path.is_dir():
            feature_files.extend(sorted(path.glob("*.feature")))
        else:
            feature_files.append(path)

    if not feature_files:
        print("No .feature files found.")
        return 2

    total_passed = 0
    total_failed = 0
    for feature in feature_files:
        passed, failed = run_feature(feature, context_factory, dispatch)
        total_passed += passed
        total_failed += failed

    print(f"\nSummary: {total_passed} passed, {total_failed} failed")
    return 1 if total_failed else 0


def exit_main(**kwargs: object) -> None:
    sys.exit(main(**kwargs))
