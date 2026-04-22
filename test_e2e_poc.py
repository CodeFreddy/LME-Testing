"""
端到端测试：验证 Phase 1-3 新功能。
使用 artifacts/poc_two_rules 的现有 maker/checker 产物作为输入，
通过真实 LLM 调用跑 rewrite + 增量 checker，然后断言所有关键行为。

用法：
  python test_e2e_poc.py                              # 用默认 config
  python test_e2e_poc.py --config path/to/config.json
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent
RULES        = ROOT / "artifacts/poc_two_rules/semantic_rules.json"
HUMAN_REVIEWS = ROOT / "artifacts/poc_two_rules/human_reviews.json"
MAKER_CASES  = ROOT / "runs/poc_strict/maker_complete/20260322T170107Z/maker_cases.jsonl"
CHECKER_REVIEWS = ROOT / "runs/poc_strict/checker_complete/20260322T170222Z/checker_reviews.jsonl"
DEFAULT_CONFIG = ROOT / "config/llm_profiles.example.json"


def ok(msg: str) -> None:
    print(f"  [OK] {msg}")


def fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")
    sys.exit(1)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    args = parser.parse_args()
    config_path = Path(args.config)

    from lme_testing.config import load_project_config
    from lme_testing.pipelines import _rewrite_targets, run_rewrite_pipeline, run_checker_pipeline
    from lme_testing.audit_trail import build_audit_trail
    from lme_testing.case_compare import build_case_compare
    from lme_testing.storage import load_json

    config = load_project_config(config_path)

    # ── Section 0: pure-logic assertions (no LLM) ──
    print(f"\n=== [0] _rewrite_targets (pure logic, no LLM) ===")
    human_payload = load_json(HUMAN_REVIEWS)
    targets = _rewrite_targets(human_payload)
    print(f"  targets = {targets}")
    assert "SR-MR-003-01" in targets, "SR-MR-003-01 should be targeted"
    assert set(targets["SR-MR-003-01"]) == {
        "TC-SR-MR-003-01-positive-01",
        "TC-SR-MR-003-01-negative-01",
    }, f"unexpected target cases: {targets['SR-MR-003-01']}"
    assert "SR-MR-004-02" not in targets, "SR-MR-004-02 has only pending → must NOT be targeted"
    ok("_rewrite_targets: only SR-MR-003-01 cases collected, SR-MR-004-02 skipped")

    with tempfile.TemporaryDirectory(prefix="lme_e2e_") as _tmp:
        tmp = Path(_tmp)
        rewrite_out = tmp / "rewrite"
        checker_out = tmp / "checker"

        # ── Section 1: rewrite pipeline ──
        print(f"\n=== [1] run_rewrite_pipeline (case-level rewrite via LLM) ===")
        rewrite_summary = run_rewrite_pipeline(
            config=config,
            semantic_rules_path=RULES,
            maker_cases_path=MAKER_CASES,
            checker_reviews_path=CHECKER_REVIEWS,
            human_reviews_path=HUMAN_REVIEWS,
            output_dir=rewrite_out,
            limit=None,
            batch_size=1,
        )
        print(f"  rewritten_case_ids = {rewrite_summary['rewritten_case_ids']}")

        merged = load_jsonl(Path(rewrite_summary["merged_cases_path"]))
        orig   = load_jsonl(MAKER_CASES)
        orig_by_rule   = {r["semantic_rule_id"]: r for r in orig}
        merged_by_rule = {r["semantic_rule_id"]: r for r in merged}

        # SR-MR-004-02 must be byte-identical (not touched)
        orig_004   = json.dumps(orig_by_rule["SR-MR-004-02"],   ensure_ascii=False, sort_keys=True)
        merged_004 = json.dumps(merged_by_rule["SR-MR-004-02"], ensure_ascii=False, sort_keys=True)
        if orig_004 == merged_004:
            ok("SR-MR-004-02 (untouched rule) is byte-identical in merged output")
        else:
            fail("SR-MR-004-02 changed but should be untouched!")

        # SR-MR-003-01 must still carry both case_ids
        merged_003_scenarios = merged_by_rule["SR-MR-003-01"]["scenarios"]
        assert len(merged_003_scenarios) == 2, \
            f"Expected 2 scenarios in SR-MR-003-01, got {len(merged_003_scenarios)}"
        merged_case_ids = {s["scenario_id"] for s in merged_003_scenarios}
        assert {"TC-SR-MR-003-01-positive-01", "TC-SR-MR-003-01-negative-01"} == merged_case_ids
        ok("SR-MR-003-01: both case_ids preserved in merged output after rewrite")

        rewritten_ids = set(rewrite_summary["rewritten_case_ids"])
        assert rewritten_ids, "rewritten_case_ids must not be empty"
        assert rewritten_ids <= {"TC-SR-MR-003-01-positive-01", "TC-SR-MR-003-01-negative-01"}, \
            f"Unexpected extra ids: {rewritten_ids}"
        ok(f"rewritten_case_ids = {rewritten_ids}")

        # ── Section 2: incremental checker ──
        print(f"\n=== [2] run_checker_pipeline (incremental, only_case_ids={rewritten_ids}) ===")
        checker_summary = run_checker_pipeline(
            config=config,
            semantic_rules_path=RULES,
            maker_cases_path=Path(rewrite_summary["merged_cases_path"]),
            output_dir=checker_out,
            limit=None,
            batch_size=1,
            resume_from=None,
            only_case_ids=rewritten_ids,
            previous_reviews_path=CHECKER_REVIEWS,
        )
        print(f"  new_review_count       = {checker_summary.get('new_review_count')}")
        print(f"  inherited_review_count = {checker_summary.get('inherited_review_count')}")

        assert checker_summary.get("new_review_count") == len(rewritten_ids), \
            f"Expected {len(rewritten_ids)} new reviews, got {checker_summary.get('new_review_count')}"
        assert checker_summary.get("inherited_review_count") == 3, \
            f"Expected 3 inherited (SR-MR-004-02 × 3), got {checker_summary.get('inherited_review_count')}"

        all_reviews = load_jsonl(Path(checker_summary["results_path"]))
        assert len(all_reviews) == 5, f"Final checker_reviews.jsonl must cover all 5 cases, got {len(all_reviews)}"
        ok(f"Incremental checker: {len(rewritten_ids)} LLM-reviewed + 3 inherited = {len(all_reviews)} total in output")

        # SR-MR-004-02 reviews must be identical to previous round
        prev_by_case = {r["case_id"]: r for r in load_jsonl(CHECKER_REVIEWS)}
        new_by_case  = {r["case_id"]: r for r in all_reviews}
        for cid in ["TC-SR-MR-004-02-positive-01", "TC-SR-MR-004-02-boundary-01", "TC-SR-MR-004-02-negative-01"]:
            p, n = prev_by_case.get(cid, {}), new_by_case.get(cid, {})
            if p.get("is_blocking") == n.get("is_blocking") and p.get("overall_status") == n.get("overall_status"):
                ok(f"  {cid}: inherited correctly (is_blocking={n.get('is_blocking')}, overall={n.get('overall_status')})")
            else:
                fail(f"  {cid}: inherited review content mismatch!")

        # ── Section 3a: case_compare ──
        print(f"\n=== [3a] build_case_compare ===")
        compare_out = tmp / "compare_iter_000_vs_001.html"
        cmp = build_case_compare(
            prev_cases_path=MAKER_CASES,
            next_cases_path=Path(rewrite_summary["merged_cases_path"]),
            rewritten_case_ids=rewritten_ids,
            iteration_prev=0,
            iteration_next=1,
            output_html_path=compare_out,
        )
        assert compare_out.exists()
        html = compare_out.read_text(encoding="utf-8")
        assert "TC-SR-MR-003-01" in html, "compare HTML must show the rewritten case"
        assert cmp["compared_case_count"] == len(rewritten_ids)
        ok(f"compare_iter_000_vs_001.html: {cmp['compared_case_count']} case(s), side-by-side diff rendered")

        # ── Section 3b: audit_trail ──
        print(f"\n=== [3b] build_audit_trail (simulated session dir) ===")
        # Build a minimal session directory structure so audit_trail can scan it
        session_sim = tmp / "session_sim"
        iter0 = session_sim / "iterations" / "000"
        (iter0 / "reviews").mkdir(parents=True)
        shutil.copy(CHECKER_REVIEWS, iter0 / "checker_reviews.jsonl")
        (iter0 / "reviews" / "human_reviews_latest.json").write_text(
            HUMAN_REVIEWS.read_text(encoding="utf-8"), encoding="utf-8"
        )

        audit_out = session_sim / "audit_trail.html"
        audit = build_audit_trail(session_sim, audit_out)
        assert audit_out.exists()
        audit_html = audit_out.read_text(encoding="utf-8")

        # TC-SR-MR-003-01-negative-01: checker is_blocking=False + human rewrite → rule (c) divergence
        print(f"  divergent_count = {audit['divergent_count']}")
        assert audit["divergent_count"] >= 1, \
            "Expected ≥1 divergence: checker=not-blocking but human=rewrite on TC-SR-MR-003-01-negative-01"
        assert "TC-SR-MR-003-01-negative-01" in audit_html
        ok(f"audit_trail.html: {audit['divergent_count']} divergence(s) detected and rendered correctly")

        # Persist outputs to runs/ for manual inspection
        out_dir = ROOT / "runs" / "e2e_poc_validation"
        out_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(compare_out, out_dir / "compare_iter_000_vs_001.html")
        shutil.copy(audit_out,   out_dir / "audit_trail.html")
        shutil.copy(Path(rewrite_summary["merged_cases_path"]), out_dir / "merged_cases.jsonl")
        shutil.copy(Path(checker_summary["results_path"]),      out_dir / "checker_reviews.jsonl")
        print(f"\n  Artifacts saved to: {out_dir}")

    print(f"\n{'='*55}")
    print("  ALL ASSERTIONS PASSED — Phase 1-3 e2e OK")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
