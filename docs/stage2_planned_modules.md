# Stage 2 Planned Modules

**Created:** 2026-04-19  
**Stage:** Stage M → Stage 2 entry requirement  
**Purpose:** Document the two missing modules identified from master branch analysis.

---

## 1. `lme_testing/audit_trail.py`

**Status:** Planned (not implemented)

### Purpose
Generate an audit trail HTML view that records the complete decision chain for each rule:
`maker output → checker judgment → human review decision`

### Input
- `session_dir/` containing all iterations of:
  - `maker_cases.jsonl`
  - `checker_reviews.jsonl`
  - Human review decisions from `review_session.py`

### Output
- `audit_trail.html` — Timeline view with:
  - Rule ID header
  - Maker scenario cards (with evidence quotes)
  - Checker review cards (scores, findings)
  - Human decision with timestamp
  - Decision chain visualization

### API Route (already stubbed in `review_session.py`)
- `GET /api/audit_trail` — Returns audit trail HTML for current session

### Acceptance Criteria
- [ ] `lme_testing/audit_trail.py` module exists with `build_audit_trail(session_dir: Path) -> Path` function
- [ ] HTML output shows maker → checker → human decision chain per rule
- [ ] Works with existing `review_session.py` without modification

---

## 2. `lme_testing/case_compare.py`

**Status:** Planned (not implemented)

### Purpose
Generate a side-by-side comparison view showing how a rule's cases changed between iterations (e.g., after a `rewrite` decision).

### Input
- `session_dir/` with multiple iteration subdirectories:
  - `iteration_1/maker_cases.jsonl`
  - `iteration_2/maker_cases.jsonl`

### Output
- `case_compare.html` — Comparison view with:
  - Rule ID header
  - Left panel: iteration N cases
  - Right panel: iteration N+1 cases
  - Diff highlighting (added/removed/changed scenarios)

### API Route (already stubbed in `review_session.py`)
- `POST /api/case_compare` — Triggered after `/api/submit` when rewrite decisions exist

### Acceptance Criteria
- [ ] `lme_testing/case_compare.py` module exists with `build_case_compare(session_dir: Path, iteration_a: int, iteration_b: int) -> Path` function
- [ ] HTML output highlights differences between two iterations
- [ ] Works with existing `review_session.py` without modification

---

## Dependencies

Both modules are independent of each other but share:
- Input from `review_session.py` session data format
- Output to HTML (similar structure to existing `reporting.py`)

Neither module should modify `review_session.py` core logic — they extend existing stub routes.

## Stage 2 Priority

These modules are **B.1** and **B.2** in Stage 2 roadmap (Direction B: Master 缺失模块实现).
