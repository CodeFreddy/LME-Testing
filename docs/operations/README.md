# Operations Documents

**Status:** Active operations index
**Date:** 2026-05-08
**Canonical owner:** `docs/index.md` and `docs/governance/docs_housekeeping.md`
**Scope:** Local index for session continuity, handoff, and checkpoint records.

---

## Purpose

This folder preserves operational continuity for humans and agents working across sessions.

Operations records are not general planning notes. They capture recoverable task state, current handoff context, and constraints that should survive context compaction or a fresh chat.

---

## Files

| File | Role | Cleanup Rule |
|------|------|--------------|
| `session_handoff.md` | Current handoff summary for the latest working state. | Refresh during commit handoff or substantial session closeout. |
| `checkpoints.md` | Historical checkpoint and resume-prompt records. | Preserve older checkpoints unless a human explicitly asks to prune them. |

---

## Use Guidance

Read `session_handoff.md` when:

- preparing a commit handoff,
- resuming recent work,
- checking the active repo state before a new substantial task.

Read `checkpoints.md` when:

- recovering from context compaction,
- starting from a fresh chat,
- continuing a partially completed task,
- reconstructing constraints and next actions from a prior session.

---

## Maintenance Rules

- Keep the latest checkpoint easy to find at the top of `checkpoints.md`.
- Preserve older checkpoints below the latest record.
- Do not archive or delete checkpoint history unless a human explicitly asks.
- Refresh `session_handoff.md` according to the repository handoff rule before commits or substantial handoff points.
- Do not treat operations notes as canonical roadmap approval; use planning, governance, and architecture docs for that.

---

## Related Rules

- `docs/governance/docs_housekeeping.md`
- `docs/governance/agent_guidelines.md`
- `../AGENTS.md`
