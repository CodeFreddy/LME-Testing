# vendor/master-branch — Master Branch Archive

**Archived:** 2026-04-19  
**Purpose:** Preserved snapshot of the original master branch (CodeFreddy/LME-Testing) for cherry-pick reference and merge analysis.  
**Not part of main import paths.**

---

## Cherry-Pick Status

All有价值 improvements from this branch have been merged into main. The broken imports (audit_trail/case_compare) are tracked as Stage 2 tasks.

| Item | Source File | Cherry-Pick Status | Notes |
|------|-------------|-------------------|-------|
| **SM-T01** | vendor/README | ✅ Completed (this file) | Archive documentation |
| **SM-T02** | storage.py | ✅ Merged into main | UTC timestamp with Z suffix — main already has this |
| **SM-T03** | workflow_session.py | ✅ Merged into main | KeyboardInterrupt + progress output — main has MORE than master |
| **SM-T04** | config.py | 🧊 Deferred | `max_retries`/`retry_backoff_seconds` — already in main's RoleDefaults |
| **audit_trail.py** | review_session.py import | ❌ Broken in master | Stage 2 task: S2-B1 |
| **case_compare.py** | review_session.py import | ❌ Broken in master | Stage 2 task: S2-B2 |
| providers.py | providers.py | ❌ Not merged | Encoding damage (??? UTF-8 corruption); main has StubProvider |
| pipelines.py (639L) | pipelines.py | ❌ Not merged | Older version; main has planner+BDD pipeline |
| review_session.py BDD | review_session.py | ❌ Not merged | Main's BDD tab is the primary new feature |

---

## What Was NOT Merged

| File | Reason |
|------|--------|
| `providers.py` (135 lines) | UTF-8 encoding damage + missing StubProvider |
| `pipelines.py` (639 lines) | Pre-dates main's planner/BDD pipeline; incompatible |
| `review_session.py` | Main's version has BDD tab and more features; master version would regress |
| `prompts.py` | No version control in master; main has versioned prompts |
| `docs/` (4 files) | Master docs are subset of main docs; no new content |

---

## Broken Imports (Stage 2)

Master's `review_session.py` imports two modules that do not exist in either branch:

```python
from .audit_trail import build_audit_trail   # Does not exist
from .case_compare import build_case_compare  # Does not exist
```

These are documented in `docs/stage2_planned_modules.md` as Stage 2 tasks B.1 and B.2.

---

## For Reference

- Merge analysis: `docs/archives/MERGE_STRATEGY.md`
- Stage 2 tasks: `docs/stage2_planned_modules.md`
- Full TODO: `TODO.md` (Stage M section)
