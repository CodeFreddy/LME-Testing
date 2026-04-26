# Reference Policy

## Purpose

This document defines how non-normative materials should be stored and used in this repository.

It exists to keep a clear boundary between:

- official repository governance documents
- reference materials that informed design decisions
- and source materials used by extraction, benchmarking, or testing flows

Without this distinction, contributors may confuse:

- draft thinking with approved policy
- source inputs with current repo standards
- or historical materials with active implementation guidance

---

## Policy Summary

Materials stored in the repo do not all have the same authority.

The repository should distinguish between three categories:

### 1. Official governance documents

These are the current source of truth for how the repo should operate.

Examples:

- `AGENTS.md`
- `docs/README.md`
- `docs/index.md`
- `docs/planning/roadmap.md`
- `docs/planning/implementation_plan.md`
- `docs/architecture/architecture.md`
- `docs/governance/acceptance.md`
- `docs/governance/model_governance.md`
- `docs/governance/agent_guidelines.md`
- `docs/governance/testing_governance.md`
- `docs/governance/prompt_lifecycle.md`
- `docs/planning/step_integration_plan.md`

These documents are normative within the scope they define.

### 2. Reference materials

These are inputs, inspirations, external proposals, archived notes, or historical design sources that may have informed the official docs.

Examples:

- external roadmap PDFs
- reviewer notes
- draft chat-derived planning docs
- perspective documents from different stakeholders
- exploratory prompt collections
- archived analysis files

These files are useful, but they are not automatically normative.

### 3. Source materials

These are primary inputs consumed by the repo or used to derive governed artifacts.

Examples:

- `docs/materials/LME_Matching_Rules_Aug_2022.md`
- source PDFs
- fixture inputs used for extraction, maker, checker, or benchmark runs

Source materials are not governance policy either, but they differ from references:

- references inform design thinking
- source materials feed governed pipelines

---

## Recommended Storage Locations

### Reference materials

Reference materials should normally be stored under:

`docs/references/`

Suggested examples:

- `docs/references/ROADMAP.pdf`
- `docs/references/chat_prompt.md`
- `docs/references/tester-perspective-notes.md`

This helps the repo:

- preserve context
- retain historical comparison points
- support traceability of design thinking
- and avoid mixing references with active governance docs

### Source materials

Source materials should remain under source-oriented locations such as:

- `docs/materials/`
- governed fixture directories
- artifact input directories

This keeps source inputs discoverable without making them look like policy.

---

## Usage Rules

### Rule 1: Official docs define current policy

If a question is about how the repo should operate now, the official governance docs win.

### Rule 2: References are informative, not authoritative

A reference file may inform decisions, but it does not override the current official docs.

### Rule 3: Source materials are inputs, not policy

Source documents may drive extraction, benchmarking, or testing, but they do not define repo governance rules by themselves.

### Rule 4: Official docs win on conflict

If a reference or source material appears to conflict with:

- `roadmap.md`
- `architecture.md`
- `acceptance.md`
- `model_governance.md`
- or other approved governance docs

then the approved governance docs take precedence for repo behavior.

### Rule 5: Important reference insights should be absorbed into official docs

If a reference contains ideas worth preserving, those ideas should be rewritten into the official docs rather than requiring contributors to interpret the raw source every time.

### Rule 6: References should remain identifiable as references

Do not rename or place reference files in a way that makes them look like official policy by accident.

### Rule 7: References should be indexed

If important references are stored in the repo, they should be listed in:

- `docs/index.md`
- or `docs/references/README.md`

so contributors understand their role.

### Rule 8: References should not become hidden implementation contracts

If an implementation decision depends on a reference strongly enough that contributors or agents must consult it, the relevant rule should be promoted into the official docs.

---

## Promotion Rule

A reference file becomes part of the official governance system only when its relevant content is intentionally incorporated into the official docs.

That means the content has been:

- reviewed
- rewritten as repo policy
- placed in the correct document
- and governed by the same update expectations as other docs

Raw reference files should not be treated as "shadow policy."

---

## Suggested Contributor Guidance

Contributors should use this decision order:

1. Read the official docs first.
2. Use reference materials only for context, history, or comparison.
3. Use source materials as inputs for scripts, benchmarks, or artifact generation.
4. If a reference contains better ideas, propose doc updates to the official docs.
5. Do not implement directly from a reference file if it conflicts with current repo docs.
6. Do not confuse source inputs with repo governance policy.

---

## AI Agent Guidance

AI coding agents should follow the same rule:

- official docs define current constraints
- references provide context only
- source materials provide inputs, not policy
- implementation must not be driven solely by raw reference materials
- implementation must not be driven solely by source materials without checking current governance docs
- if a reference suggests a better design, the agent should surface that as a proposal, not silently treat it as current policy

---

## Review Questions

When adding a new reference file, reviewers should ask:

- Is this file clearly marked as reference material?
- Does its location make that obvious?
- Is it listed in the index?
- Does it conflict with current official docs?
- If it contains important ideas, have those ideas already been absorbed into official policy?
- Could it be confused with a source input or a current implementation contract?

---

## Summary

Reference materials are valuable, but they should not compete with official repo governance documents.

The correct pattern is:

- keep references for context and historical traceability
- keep source materials for governed pipeline inputs
- keep official docs as the source of truth
- and promote good ideas from references into the official docs through explicit updates
