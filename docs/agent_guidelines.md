# AI Agent Contribution Guidelines

## Purpose

This document defines how AI coding agents are allowed to operate in this repository.

The goal is not to restrict useful automation.
The goal is to make AI-assisted development safe, reviewable, and aligned with the roadmap, acceptance gates, and model governance rules.

This document applies to any AI agent that:
- writes or edits code,
- modifies prompts,
- changes schemas,
- updates docs,
- adds tests,
- changes model configuration,
- or generates artifacts intended for use in the repo.

This document should be read together with:
- `docs/roadmap.md`
- `docs/acceptance.md`
- `docs/model_governance.md`
- `docs/architecture.md`

---

## Core Principles

### 1. The agent works within contracts

The agent must treat schemas, module boundaries, benchmark gates, and acceptance criteria as source-of-truth constraints.

The agent may not assume that a plausible change is acceptable unless it also satisfies the documented contract.

### 2. The agent may assist implementation, not redefine scope

The roadmap defines scope.
The agent may accelerate scoped work, but it may not silently pull later-phase work into the current phase.

### 3. Structured systems must stay structured

If the pipeline currently depends on structured artifacts, the agent must preserve structured contracts.

Free-form output must not replace schema-governed output without an explicit architectural decision.

### 4. Deterministic checks take priority where possible

If a validation or rule can be implemented deterministically, the agent must prefer that over adding another model-dependent judgment layer.

### 5. No silent changes

Any change that affects behavior, contract, prompts, model defaults, or acceptance criteria must be clearly documented.

---

## What the Agent Is Allowed to Do

The agent may:

- implement roadmap items that are already approved,
- add tests, fixtures, and CI checks,
- improve schema validation,
- improve traceability,
- add benchmark coverage,
- improve logging and observability,
- refactor code without changing behavior,
- improve docs when the docs remain aligned with actual implementation,
- add deterministic validation modules,
- add provider adapters behind existing abstractions,
- improve reporting without breaking artifact contracts.

The agent may also generate implementation suggestions or code drafts for:
- planner modules,
- BDD normalization,
- step binding suggestions,
- review export/import logic,
- governance automation,

but only when those changes remain inside the currently approved roadmap phase or are explicitly approved.

---

## What the Agent Must Not Do

The agent must not:

- change artifact schemas silently,
- bypass validation gates,
- replace structured JSON with free-form text,
- switch default models or prompts without governance updates,
- hardcode provider-specific behavior into business logic,
- merge future-phase scope into current-phase work without approval,
- declare work complete without evidence,
- add hidden fallback logic that masks invalid outputs,
- silently weaken acceptance criteria,
- invent undocumented pipeline stages as if they already existed.

The agent must also not treat "the model usually does this correctly" as an acceptable substitute for explicit validation.

---

## Required Workflow for Any Meaningful Change

Any meaningful change must follow this workflow.

### Step 1: Identify scope

Before making a change, the agent must determine:
- which roadmap phase the change belongs to,
- which modules are affected,
- whether the change impacts schemas, prompts, models, reports, or acceptance criteria.

### Step 2: Check contracts

The agent must review relevant contracts before editing:
- schema definitions,
- acceptance criteria,
- model governance rules,
- module boundaries,
- existing tests and fixtures.

### Step 3: Implement with minimal scope

The agent should prefer the smallest change that satisfies the intended requirement.

The agent should not combine unrelated refactors with behavior changes unless explicitly requested.

### Step 4: Add or update evidence

If the behavior changes, the agent must also update:
- tests,
- fixtures,
- docs,
- benchmark references,
- acceptance references where applicable.

### Step 5: Summarize the change

The final output of the change should make clear:
- what changed,
- why it changed,
- which files were affected,
- what evidence supports it,
- what remains out of scope.

---

## Required Workflow for Schema Changes

Artifact schemas are high-risk changes.

If the agent changes any schema or artifact contract, it must also update:
- schema files,
- artifact fixtures,
- validation tests,
- migration notes,
- docs that describe the artifact,
- acceptance references if phase gates depend on that artifact.

### Schema change checklist

Before considering a schema change complete, confirm:
- Is the new schema versioned?
- Are valid fixtures updated?
- Are invalid fixtures updated?
- Does CI validate the new contract?
- Are downstream consumers reviewed?
- Is migration impact documented?

If the answer to any of these is no, the schema change is incomplete.

---

## Required Workflow for Prompt Changes

Prompts are governed assets.

If the agent changes a prompt, it must also update:
- prompt version,
- prompt change summary,
- linked benchmark evidence,
- prompt ownership metadata if required,
- docs if the operational behavior changed.

### Prompt change checklist

Before considering a prompt change complete, confirm:
- Is the prompt version updated?
- Is benchmark evidence available?
- Are output diffs reviewed?
- Is rollback straightforward?
- Is any new failure mode introduced?

---

## Required Workflow for Model Changes

Model changes include:
- switching providers,
- switching model names,
- switching default models,
- changing decoding settings that materially affect behavior.

If the agent makes or proposes a model change, it must also include:
- benchmark evidence,
- compatibility notes,
- rollback notes,
- affected module list,
- governance updates if defaults change.

### Model change checklist

Before considering a model change complete, confirm:
- Does it pass benchmark gates?
- Does it preserve structured output requirements?
- Does checker stability remain within allowed range?
- Is provider-specific behavior isolated?
- Is rollback documented?

---

## Required Workflow for Acceptance-Critical Changes

If a change affects a roadmap acceptance item, the agent must explicitly link the change to:
- the roadmap phase,
- the acceptance item,
- the evidence produced,
- any remaining limitations.

A code change is not complete merely because it compiles or looks reasonable.
It must satisfy the acceptance gate it claims to advance.

---

## Testing Rules for Agents

### 1. Every meaningful change requires tests or explicit rationale

If a change affects behavior, the agent must add or update tests.

If tests are not added, the agent must explain why not.

### 2. Prefer narrow tests plus one flow check

The agent should usually add:
- focused tests for changed logic,
- plus at least one flow-level check if the change affects pipeline behavior.

### 3. Preserve benchmark relevance

If a change affects model-facing logic, benchmark or baseline coverage should be reviewed and updated when necessary.

### 4. Do not rely on manual inspection alone

Manual reading of generated outputs is useful, but it is not sufficient evidence for completion.

---

## Documentation Rules for Agents

The agent must update docs when:
- workflow changes,
- schema changes,
- governance rules change,
- acceptance gates change,
- model defaults change,
- new required developer steps are introduced.

Docs must describe real behavior, not desired future behavior, unless clearly labeled as roadmap content.

---

## Phase Discipline Rules

The roadmap is phase-based. The agent must respect that.

### Short-term phase

The agent may focus on:
- schema validation,
- extraction validation,
- CI,
- metadata capture,
- checker stability visibility,
- governance docs.

The agent must not quietly expand short-term work into:
- full planner systems,
- full hosted collaboration platforms,
- full execution engines,
- full step integration.

### Mid-term phase

The agent may focus on:
- multi-document ingestion,
- planning layer,
- BDD normalization,
- traceability,
- review exchange and merge,
- quality dashboards.

The agent must not quietly expand mid-term work into:
- unrestricted enterprise execution orchestration,
- production multi-tenant governance layers beyond approved scope.

### Long-term phase

The agent may focus on:
- step definition mapping,
- executable scenario contracts,
- deterministic oracle layers,
- hosted review service,
- enterprise observability.

The agent must still preserve schema and governance discipline.

---

## Preferred Engineering Behaviors

The agent should prefer:
- small, reviewable commits,
- explicit interfaces,
- stable contracts,
- deterministic validation,
- machine-readable outputs,
- simple rollback paths,
- visible failure over hidden coercion,
- narrow provider adapters,
- traceable artifacts.

The agent should avoid:
- broad speculative refactors,
- hidden heuristics,
- undocumented fallback behavior,
- mixing roadmap phases,
- changing multiple contracts at once without need,
- overfitting to one provider.

---

## Output Requirements for Agent-Generated Changes

When the agent proposes or completes a change, the summary should include:
- **Scope**
- **Roadmap phase**
- **Files changed**
- **Behavior change**
- **Schema impact**
- **Prompt/model impact**
- **Tests added or updated**
- **Acceptance items addressed**
- **Known limitations**
- **Rollback notes** if applicable

This keeps changes reviewable by humans and comparable across model providers.

---

## Red Flags That Require Human Review

The agent should not proceed without explicit human review when:
- an artifact schema must change,
- a default model must change,
- a prompt causes materially different outputs,
- acceptance criteria would need to be weakened,
- a fallback is proposed for invalid structured outputs,
- execution behavior becomes less deterministic,
- review decisions could become less auditable,
- traceability fields are removed or weakened.

---

## Escalation Guidelines

If the agent detects uncertainty, it should prefer escalation over silent assumption.

Examples:
- unclear schema ownership,
- ambiguous acceptance gate interpretation,
- unclear roadmap phase fit,
- conflicting provider behaviors,
- missing migration strategy.

The correct behavior is to surface the uncertainty clearly, not to hide it behind broad code changes.

---

## Minimal Definition of Done for Agent Work

A change should not be considered done unless:
- the scope is clear,
- the contract is preserved or intentionally versioned,
- tests or evidence exist,
- docs are updated if needed,
- acceptance impact is stated,
- rollback is considered for risky changes.

---

## Suggested Labels or Change Categories

If the repo later uses labels, the following categories are recommended:
- `phase-short-term`
- `phase-mid-term`
- `phase-long-term`
- `schema-change`
- `prompt-change`
- `model-change`
- `benchmark-impact`
- `acceptance-impact`
- `docs-only`
- `deterministic-validation`
- `review-required`

These labels are optional, but they help keep agent-generated work visible and governable.

---

## Summary

AI coding agents can accelerate this repository significantly, but only if they operate inside explicit contracts.

Agents should:
- preserve schemas,
- respect roadmap phases,
- attach evidence,
- keep model changes governed,
- prefer deterministic validation where possible,
- and avoid silent behavior changes.

The purpose of this document is not to slow development down.
It is to make multi-model, AI-assisted development reliable enough for an enterprise AI testing roadmap.
