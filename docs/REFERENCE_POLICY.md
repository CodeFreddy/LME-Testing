# Reference Policy

## Purpose

This document defines how external or historical reference materials should be stored and used in this repository.

It exists to keep a clear boundary between:

- **official repository governance documents**, and
- **reference inputs** that informed those documents.

Without this distinction, contributors may confuse:
- draft thinking with approved policy,
- source material with current repo standards,
- or historical inputs with active implementation guidance.

---

## Policy Summary

Reference materials may be stored in the repository, but they must **not** be treated as first-class governance documents unless they are explicitly promoted into the main docs system.

The repository should distinguish between:

### 1. Official governance documents
These are the current source of truth for how the repo should operate.

Examples:
- `docs/roadmap.md`
- `docs/implementation_plan.md`
- `docs/architecture.md`
- `docs/acceptance.md`
- `docs/model_governance.md`
- `docs/agent_guidelines.md`
- `docs/testing_governance.md`
- `docs/prompt_lifecycle.md`
- `docs/step_integration_plan.md`

### 2. Reference materials
These are inputs, inspirations, external proposals, archived notes, or historical design sources that may have informed the official docs.

Examples:
- external roadmap PDFs
- reviewer notes
- draft chat-derived planning docs
- perspective documents from different stakeholders
- exploratory prompt collections
- archived analysis files

These files are useful, but they are **not automatically normative**.

---

## Recommended Storage Location

Reference materials should be stored under:

`docs/references/`

Suggested examples:
- `docs/references/ROADMAP.pdf`
- `docs/references/chat_prompt.md`
- `docs/references/tester-perspective-notes.md`

This allows the repository to:
- preserve traceability,
- retain context,
- support historical comparison,
- and avoid mixing references with active governance docs.

---

## Usage Rules

### Rule 1: Reference materials are informative, not authoritative
A reference file may inform decisions, but it does not override the current official docs.

### Rule 2: Official docs win on conflict
If a reference file conflicts with:
- `roadmap.md`
- `architecture.md`
- `acceptance.md`
- `model_governance.md`
- or other approved governance docs

then the approved governance docs take precedence.

### Rule 3: Important reference insights should be absorbed into official docs
If a reference material contains ideas worth preserving, those ideas should be rewritten into the official docs rather than requiring contributors to interpret the raw source every time.

### Rule 4: References should remain identifiable as references
Do not rename reference files in a way that makes them look like official policy by accident.

### Rule 5: References should be indexed
If important references are stored in the repo, they should be listed in:
- `docs/index.md`
- or `docs/references/README.md`

so contributors understand their role.

---

## Promotion Rule

A reference file becomes part of the official governance system only when its relevant content is intentionally incorporated into the official docs.

That means:
- reviewed,
- rewritten as repo policy,
- placed in the correct document,
- and governed by the same update expectations as other docs.

Raw reference files should not be treated as “shadow policy”.

---

## Suggested Contributor Guidance

Contributors should use this decision order:

1. Read the official docs first.
2. Use reference materials only for context, history, or comparison.
3. If a reference contains better ideas, propose doc updates to the official docs.
4. Do not implement directly from a reference file if it conflicts with current repo docs.

---

## AI Agent Guidance

AI coding agents should follow the same rule:

- official docs define current constraints,
- references provide context only,
- implementation must not be driven solely by raw reference materials,
- if a reference suggests a better design, the agent should surface that as a proposal, not silently treat it as current policy.

---

## Review Questions

When adding a new reference file, reviewers should ask:

- Is this file clearly marked as reference material?
- Does its location make that obvious?
- Is it listed in the index?
- Does it conflict with current official docs?
- If it contains important ideas, have those ideas already been absorbed into official policy?

---

## Summary

Reference materials are valuable, but they should not compete with official repo governance documents.

The correct pattern is:

- keep references for traceability and context,
- keep official docs as the source of truth,
- and promote good ideas from references into the official docs through explicit updates.
