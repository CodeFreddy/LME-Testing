# AI Agent Guidelines

## Purpose

This document defines how AI coding agents are allowed to operate in this repository.

It exists to ensure that AI-assisted development remains:

- safe,
- traceable,
- phase-aligned,
- schema-respecting,
- benchmark-governed,
- and reviewable by humans.

This document applies to any AI agent that:
- writes code,
- edits prompts,
- changes schemas,
- updates tests,
- modifies docs,
- changes model configuration,
- or proposes workflow changes.

This document should be read together with:

- `docs/roadmap.md`
- `docs/acceptance.md`
- `docs/model_governance.md`
- `docs/architecture.md`

---

## Guiding Principle

AI agents may accelerate implementation, but they must not become an uncontrolled source of architecture drift.

Agents are allowed to help implement the roadmap.  
Agents are not allowed to redefine the roadmap implicitly through code changes.

## Task Session Protocol

For any non-trivial implementation request, an agent should work in this order:

1. identify the roadmap phase and task ID,
2. read the task input contract,
3. read the task acceptance criteria,
4. check whether prerequisite tasks or earlier phase gates have been satisfied,
5. implement only the scoped task work,
6. produce the required output artifacts,
7. end with a structured self-evaluation.

If any listed prerequisite, contract input, or required gate is missing, the agent should stop and surface the dependency rather than fabricate inputs.

### Required session closeout

A substantial implementation session should end with a self-evaluation against the task acceptance criteria using a status such as:
- PASS
- PARTIAL
- FAIL

If any criterion is FAIL, the work should not be described as complete.

---

## Core Working Rules

### 1. Work against explicit contracts

An agent must prefer existing contracts over inferred intent.

Contracts include:
- schemas,
- module boundaries,
- documented pipeline stages,
- phase scope,
- acceptance criteria,
- model governance rules.

If a documented contract conflicts with an inferred improvement idea, the documented contract wins unless a human explicitly changes it.

### 2. Do not treat current behavior as automatically correct

Existing code may contain prototype assumptions.  
Agents should preserve behavior only when that behavior is consistent with:
- repo docs,
- schemas,
- acceptance gates,
- roadmap phase boundaries.

### 2A. Durable behavior must live in repo-readable files

AI agents must not rely on hidden chat context as a substitute for repository contracts.

If a workflow depends on:
- prompts,
- config,
- schemas,
- task contracts,
- benchmark rules,
- or acceptance requirements,

those dependencies should live in version-controlled repo-readable files rather than being left implicit in a conversation.

### 3. Prefer minimal, auditable changes

Agents should prefer:
- small scoped changes,
- isolated refactors,
- explicit tests,
- documented migration notes.

Avoid broad, implicit rewrites unless the change is explicitly requested and acceptance criteria are updated.

### 4. Keep structured outputs structured

If a module currently emits structured JSON or schema-governed artifacts, an agent must not replace that with free-form text output unless the contract is intentionally revised.

### 5. Deterministic validation takes priority

If something can be validated deterministically, the agent should prefer deterministic validation over additional LLM judgment.

---

## What Agents May Do

Agents may:

- add or update tests,
- implement roadmap items inside the active phase,
- add schema validation,
- improve traceability,
- add benchmark tooling,
- improve CI,
- improve error handling,
- improve docs,
- add structured metadata,
- improve provider abstractions,
- improve report generation,
- add migration notes when contracts change.

Agents may also propose, but not silently force:
- schema extensions,
- prompt updates,
- new benchmark cases,
- stricter acceptance gates,
- internal refactors.

---

## What Agents Must Not Do

Agents must not:

- silently change artifact contracts,
- silently switch default models,
- bypass schemas,
- hardcode provider-specific behavior into business modules,
- introduce undocumented prompt changes,
- merge later-phase scope into earlier-phase work,
- remove tests or benchmarks without replacement,
- replace deterministic checks with LLM-only logic,
- hide failures by swallowing validation errors,
- silently coerce malformed structured output into valid artifacts.

Agents must not expand the architectural scope of a task just because it seems beneficial.

---

## Phase Discipline

Agents must respect the roadmap phase boundaries.

### Short-term phase work
Allowed focus:
- schema validation,
- rule validation,
- CI,
- prompt metadata,
- artifact metadata,
- checker stability visibility,
- governance docs.

Not allowed unless explicitly requested:
- hosted review platform,
- execution engine,
- step definition integration,
- full planning platform.

### Mid-term phase work
Allowed focus:
- multi-document ingestion,
- planner stage,
- normalized BDD contract,
- traceability,
- review package exchange,
- richer dashboards.

Not allowed unless explicitly requested:
- full enterprise hosted platform,
- unrestricted execution automation,
- cross-team production platform assumptions.

### Long-term phase work
Allowed focus:
- step binding,
- execution-ready contracts,
- deterministic oracle framework,
- hosted review service,
- enterprise observability.

Not allowed:
- free-form autonomous behavior without approval gates,
- undocumented execution logic.

If a requested change crosses phase boundaries, the agent must label that clearly in its change summary.

---

## Required Change Behavior

### 1. Explain the intended scope of the change
For every non-trivial change, the agent should be able to state:
- what is being changed,
- which roadmap task or equivalent work unit it maps to,
- why it belongs to the current phase,
- which acceptance items it addresses,
- whether earlier phase gates or prerequisites are already satisfied.

### 2. Update related artifacts when needed
If a change affects a contract, the agent must update:
- schema,
- tests,
- docs,
- acceptance references,
- migration notes if needed.

### 3. Preserve backward clarity
If backward compatibility is broken, the agent must make that explicit.

### 4. Keep failure visible
If validation fails, the pipeline should fail visibly.  
Agents must not hide structural problems just to keep flows passing.

---

## Required Output for AI-Generated Changes

For any substantial change, the agent should provide a structured change summary containing:

- **Change summary**
- **Why this change is needed**
- **Roadmap phase**
- **Acceptance items addressed**
- **Files added or changed**
- **Tests added or run**
- **Schema or prompt impact**
- **Known limitations**
- **Rollback considerations**

This can be included in:
- PR descriptions,
- patch summaries,
- implementation notes,
- or structured change logs.

---

## Schema Rules for Agents

### 1. No schema change without coordinated updates
If an artifact schema changes, the agent must update:
- schema definitions,
- fixtures,
- validations,
- docs,
- acceptance references.

### 2. Do not widen enums casually
Adding a new enum value changes downstream interpretation and must be treated as a governed change.

### 3. Do not remove required fields without migration support
Any weakening of a schema must be explicitly justified and documented.

### 4. Prefer additive evolution
When possible, extend contracts in backward-tolerant ways.

---

## Prompt Rules for Agents

### 1. Prompts must be versioned
No agent may change a production prompt without:
- updating prompt version,
- recording the change,
- linking benchmark evidence.

### 2. Prompt edits are governed changes
A prompt change is not “just text”; it is a behavioral change.

### 3. Do not optimize prompts only for a narrow happy path
Prompt changes must be evaluated against benchmark coverage, not only an example that happens to improve.

---

## Model Rules for Agents

### 1. Do not switch default model behavior silently
Any default model change must update:
- config,
- docs,
- benchmark evidence,
- rollback notes.

### 2. Keep provider quirks isolated
Provider-specific logic belongs in adapter or strategy layers.

### 3. Prefer compatibility over cleverness
Do not rely on undocumented provider quirks as if they were stable platform features.

---

## Testing Rules for Agents

### 1. Every feature requires a testable acceptance outcome
If a change cannot be tied to a test or acceptance check, it is incomplete.

### 2. Do not remove failing tests to make CI green
Fix root causes or explicitly document why a test is being replaced.

### 3. Add benchmark cases when fixing important regressions
If a defect reveals a missing benchmark scenario, add it.

### 4. Protect critical paths first
Priority test coverage should protect:
- schema validation,
- rule validation,
- maker output validity,
- checker output validity,
- report generation,
- benchmark reproducibility.

---

## Documentation Rules for Agents

### 1. Update docs when behavior changes
If a workflow, schema, benchmark rule, or model policy changes, docs must be updated in the same change.

### 2. Prefer explicit documentation over tribal knowledge
If an agent depends on an operational rule, that rule should live in the repo.

### 3. Keep docs aligned with the active roadmap phase
Do not document aspirational behavior as if it already exists.

---

## Safe Refactoring Rules

Agents may refactor, but safe refactoring means:

- no silent behavior change,
- no contract change without docs/tests,
- no phase scope expansion,
- no hidden provider coupling,
- no removal of observability.

If a refactor changes behavior intentionally, it must be labeled as behavior-changing work, not hidden inside cleanup.

---

## Failure Handling Rules

### 1. Surface validation failures clearly
Schema and contract failures must remain visible.

### 2. Do not silently auto-heal structural corruption
Bounded recovery is allowed only if:
- documented,
- test-covered,
- logged,
- and metadata captures that recovery happened.

### 3. Prefer explicit fallback strategies
If a model fails or a provider behaves differently, fallback logic must be documented and observable.

---

## Review Expectations for Agent Changes

A human reviewer should be able to answer the following after reading an agent-generated change:

- What changed?
- Why was it changed?
- Which roadmap phase does it belong to?
- Which acceptance criteria does it satisfy?
- Did it alter a schema, prompt, or model behavior?
- Were tests and docs updated?
- Can it be rolled back safely?

If these answers are not clear, the change is not review-ready.

---

## Escalation Conditions

An agent should flag a change for explicit human review if it involves:

- schema contract changes,
- new enum values,
- prompt behavior changes,
- default model changes,
- benchmark threshold changes,
- rollback policy changes,
- cross-phase architecture expansion,
- missing prerequisite tasks or missing earlier phase gate sign-off,
- new execution semantics,
- review workflow changes with merge implications.

---

## Suggested Working Flow for Agents

Recommended sequence for non-trivial changes:

1. identify the roadmap phase,
2. identify the acceptance criteria,
3. locate affected contracts,
4. implement minimal scoped change,
5. update tests,
6. update docs,
7. run or define benchmark evidence,
8. produce structured change summary,
9. end with PASS / PARTIAL / FAIL self-evaluation.

This sequence helps prevent uncontrolled drift.

---

## Anti-Patterns

Agents should explicitly avoid these anti-patterns:

- “The current model seemed better in my quick test, so I switched the default.”
- “The schema was restrictive, so I relaxed it without updating downstream logic.”
- “The JSON parser was failing, so I accepted malformed output automatically.”
- “The roadmap did not mention this, but I implemented a bigger platform feature while I was here.”
- “The test was flaky, so I removed it.”
- “The prompt changed, but no version bump was needed.”
- “The docs were outdated, so I ignored them instead of updating them.”

---

## Required Self-Evaluation

For any substantial implementation task, an agent should finish with a structured self-evaluation against the relevant acceptance criteria.

The self-evaluation should:
- list each relevant acceptance item,
- mark it as PASS, PARTIAL, or FAIL,
- provide short reasoning,
- identify missing prerequisites or blockers if any remain.

This requirement is especially important when different LLM APIs are used, because it makes completion reviewable without relying on hidden conversation state.

---

## Minimum Definition of Done for Agent Work

Agent-generated work is only done when all of the following are true:

- scope is clear,
- roadmap phase is identified,
- acceptance criteria are addressed,
- tests are present or updated,
- docs are updated,
- schema/prompt/model impacts are explicit,
- rollback impact is understood,
- a self-evaluation has been produced.

---

## Summary

AI agents are allowed to accelerate this repository, but only inside governed boundaries.

The repository should evolve through:
- explicit contracts,
- phase discipline,
- deterministic validation,
- benchmark-governed model use,
- and auditable change summaries.

Agent speed is valuable only when it preserves architectural clarity and trust.
