# Prompt Lifecycle

## Purpose

This document defines how governed prompts are created, versioned, reviewed, updated, deprecated, and retired in this repository.

It exists because prompts in this system are not disposable instructions.  
They are long-lived behavioral assets that can materially affect:

- rule extraction support,
- semantic normalization,
- maker outputs,
- checker outputs,
- rewrite behavior,
- planning behavior in future phases,
- and any other model-driven workflow.

Prompt lifecycle governance in this repo is phase-aware. It should make prompt behavior
reviewable and rollback-safe without forcing a heavier process than the current roadmap phase justifies.

This document should be read together with:

- `docs/governance/testing_governance.md`
- `docs/governance/model_governance.md`
- `docs/governance/acceptance.md`
- `docs/governance/agent_guidelines.md`
- `docs/architecture/architecture.md`

---

## Why Prompt Lifecycle Governance Matters

Prompt changes can silently alter behavior even when:
- code does not change,
- schemas do not change,
- CI still passes,
- and outputs look superficially valid.

Because of this, prompts must be managed as governed lifecycle assets rather than informal implementation details.

This document focuses specifically on prompt lifecycle management, while:
- `docs/governance/model_governance.md` governs model/provider behavior,
- `docs/governance/testing_governance.md` governs test operations and prompt-set discipline,
- `docs/governance/acceptance.md` governs release and phase gates.

---

## Scope

This document governs:

- prompt inventory,
- prompt identity,
- prompt categorization,
- prompt dependencies,
- prompt versioning,
- prompt storage conventions,
- prompt updates,
- prompt review,
- prompt deprecation,
- prompt rollback,
- prompt retirement,
- prompt-related artifact expectations.

This document does not replace provider governance or schema governance.

It also does not require a fully centralized prompt platform before the repo has enough governed prompt assets to justify one.

---

## Prompt Governance Principles

### 1. Prompts are governed assets

A prompt used in a repeatable workflow is a governed artifact.

### 2. Prompt identity must remain stable

A prompt should keep a stable identity across revisions so changes can be tracked over time.

### 3. Prompt sets must remain complete

If a workflow depends on a managed prompt set, prompts must not be silently deleted, renumbered, or replaced.

### 4. Prompt changes require evidence

A prompt revision is a behavioral change and must be supported by:
- change notes,
- benchmark evidence,
- and impact awareness.

The evidence required should be proportional to the prompt's role and the active roadmap phase.

### 5. Prompt dependencies must remain visible

If one prompt depends on upstream output or feeds downstream stages, those dependencies must be documented.

### 6. Prompt rollback must be possible

A prompt revision is not safely released unless prior behavior can be restored.

### 7. No prompt should define an ungoverned stage

A prompt may refine an existing governed stage, but it must not silently introduce a new model-driven workflow
whose outputs, contracts, traceability, and review path are undefined.

---

## Prompt Inventory Model

The repo should maintain a discoverable prompt inventory.

Each governed prompt should have a record containing:

- prompt ID
- prompt name
- module or workflow stage
- current version
- status
- owner
- purpose
- input expectations
- output expectations
- upstream dependencies
- downstream consumers
- linked benchmark set
- last updated date

This inventory may live in:
- a registry file,
- a structured metadata file,
- or a documented prompt directory convention.

The exact implementation may evolve, but the inventory must be explicit and version-controlled.
For the current repo phase, lightweight inventory conventions are acceptable if they remain reviewable.

---

## Prompt Identity Rules

## 1. Prompt ID

Every governed prompt must have a stable unique identifier.

Recommended format examples:
- `maker.core`
- `checker.coverage`
- `rewrite.targeted`
- `planner.scenario_family`
- `review.feedback.summary`

The exact naming scheme may vary, but it should be:
- stable,
- human-readable,
- and not tied to a transient experiment label.

## 2. Prompt name

Each prompt should have a readable name that explains its function.

## 3. Prompt status

Each prompt should carry a lifecycle status such as:
- draft
- active
- deprecated
- retired
- experimental

## 4. Prompt ownership

Each governed prompt should identify an owner or responsible area.

---

## Prompt Categories

Prompts may be grouped by architectural role.

Suggested categories include:

### 1. Extraction support prompts
Used to assist extraction or source interpretation where applicable.

### 2. Normalization prompts
Used to shape or refine rule artifacts.

### 3. Generation prompts
Used by maker or future BDD generation modules.

### 4. Evaluation prompts
Used by checker or similar evaluation modules.

### 5. Rewrite prompts
Used to regenerate targeted outputs.

### 6. Planning prompts
Used in planning stages after a governed planner contract exists.

### 7. Review support prompts
Used to summarize, classify, or support human review workflows.

The exact categories may expand, but the purpose of categorization is to improve lifecycle clarity and impact analysis.

---

## Prompt Storage Conventions

Production prompts should not be left as undocumented inline strings.

Recommended storage options:
- `prompts/`
- `prompts/<category>/`
- or another explicit, version-controlled prompt directory.

Each prompt should be stored with:
- prompt content,
- metadata,
- version reference,
- change notes if separated.

Prompt storage should be easy to audit and review in source control.

The storage model should stay proportionate to current repo maturity. A simple explicit directory
structure is preferable to an elaborate prompt management layer introduced too early.

---

## Prompt Metadata

Every governed prompt should have metadata, either embedded or adjacent.

### Minimum metadata

- prompt ID
- prompt name
- version
- status
- owner
- purpose
- input contract summary
- output contract summary
- linked benchmark set
- upstream dependencies
- downstream consumers
- last updated
- change summary

### Optional metadata

- known failure modes
- structured output mode expectations
- recommended model tier
- rollback notes
- deprecation notes

Metadata should stay focused on fields that materially improve review, traceability, and rollback.
Do not require metadata so detailed that prompt upkeep becomes heavier than the prompt change itself.

---

## Prompt Dependency Governance

Prompt dependencies must be visible and governed.

## 1. Upstream dependencies

A prompt may depend on:
- source artifact shape,
- schema assumptions,
- upstream prompt output,
- review state,
- specific artifact metadata.

## 2. Downstream consumers

A prompt may feed:
- another prompt,
- validator logic,
- report logic,
- review templates,
- benchmark checks,
- future execution bindings.

## 3. Dependency rule

If a prompt change alters an input assumption or output structure that affects other stages, that dependency impact must be recorded.

If the prompt belongs to a future or newly introduced stage, the stage contract must already be defined in the repo
before that prompt is treated as a governed default.

## 4. Sequence-sensitive workflows

For workflows where prompts are executed in a defined order, the repo should document:
- required order,
- required handoff artifacts,
- failure points,
- fallback behavior if defined.

---

## Prompt Versioning Policy

Prompt versioning must be explicit.

## 1. Version format

Semantic versioning is recommended where practical:
- major for incompatible behavioral or contract changes,
- minor for meaningful improvements with compatible contracts,
- patch for clarifications or low-risk fixes.

If another versioning format is used, it must still make change magnitude clear.

## 2. Version bump rules

A prompt version must be bumped when:
- content changes meaningfully,
- output behavior may change,
- assumptions or constraints change,
- benchmark expectations change,
- dependency behavior changes.

Purely editorial changes may use the lightest available bump, but they still must not be silent.

## 3. No silent prompt edits

A production prompt must not be edited in place without a recorded version change.

---

## Prompt Change Workflow

Any governed prompt change should follow this workflow.

### Step 1: Identify the prompt
Record:
- prompt ID
- current version
- target version
- category
- owner

### Step 2: Describe the change
Record:
- what changed,
- why it changed,
- expected benefit,
- risk of regression,
- affected modules or stages.

### Step 3: Evaluate dependency impact
Check:
- upstream assumptions,
- downstream consumers,
- schema interaction,
- benchmark impact,
- review/report impact.

### Step 4: Run benchmark or validation checks
Use the linked benchmark set for that prompt category or module.

For the current repo phase, this should usually begin with a small governed baseline set rather than a full-corpus rerun.

### Step 5: Review output differences
Review:
- schema validity,
- artifact structure,
- output completeness,
- checker stability if relevant,
- confidence and review implications if relevant.

If the prompt affects a future governed stage such as planning or normalized BDD generation, review should also confirm
that the stage contract still holds and that downstream traceability remains intact.

### Step 6: Approve, reject, or keep experimental
If evidence is insufficient, do not promote to active default.

---

## Prompt Change Record

Each meaningful prompt change should leave a record containing:

- date
- author
- prompt ID
- old version
- new version
- summary of change
- affected workflow
- downstream impact
- validation performed
- benchmark results
- rollback notes

This record may live in:
- changelog files,
- prompt metadata,
- PR descriptions,
- or a dedicated prompt governance log.

---

## Prompt Review Expectations

Before approving a prompt revision, reviewers should ask:

- Did the prompt identity remain stable?
- Was the version updated?
- Is the change documented?
- Were downstream dependencies reviewed?
- Was benchmark evidence attached?
- Did output structure change?
- Does rollback remain possible?
- Does the prompt still belong to the same lifecycle status?
- Is this prompt still operating inside an already governed stage?

If these cannot be answered clearly, the prompt change is not review-ready.

---

## Prompt Set Integrity Rules

These rules apply when a workflow depends on multiple prompts.

### 1. No silent prompt removal
Removing a prompt from a governed set requires:
- explicit decision,
- change note,
- dependency review,
- acceptance impact review if relevant.

### 2. No silent prompt renumbering or re-identification
Prompt identity should remain stable unless a reviewed migration is performed.

### 3. No silent substitution
A new prompt must not silently replace an existing governed prompt without:
- lifecycle record,
- benchmark evidence,
- compatibility review.

### 4. No partial update without inventory awareness
If only part of a prompt set is updated, the repo must still preserve awareness of:
- set completeness,
- version mix,
- dependency coherence.

This does not require a heavyweight prompt-set platform in the current repo phase; it requires only that the set
remain explicit and reviewable.

---

## Prompt Output Governance

Prompt lifecycle governance also applies to expected outputs.

For major prompts, the repo should document:
- expected output artifact type,
- required structure,
- naming or storage convention if stable,
- validation rule,
- downstream consumer,
- required review or benchmark coverage.

This helps ensure prompt evolution is connected to observable artifact behavior.

For prompts attached to structured intermediate artifacts, output governance should point to the governing schema or contract,
not just describe the intended prose format.

---

## Prompt Validation Policy

Prompt updates should be validated using a mix of:

- benchmark comparison,
- schema conformance,
- artifact diff review,
- stability comparison,
- targeted edge cases,
- integration path review where sequence matters.

A prompt should not be accepted purely because one example output looked better.

Validation depth should remain phase-appropriate. The repo should not require a testing program heavier than the
current roadmap phase justifies just to approve a small prompt improvement.

---

## Experimental Prompt Policy

Some prompts may exist only for exploration.

### Experimental prompts must:
- be labeled clearly,
- not silently become defaults,
- be tagged as experimental in metadata,
- use isolated benchmark interpretation where needed.

### Experimental prompts must not:
- overwrite default governed prompt behavior without review,
- be confused with active production prompts.

Experimental prompts also must not be used to backdoor a new model-driven stage into the baseline workflow.

---

## Deprecation Policy

A prompt may be deprecated when:
- it has been replaced by a newer governed prompt,
- the workflow no longer requires it,
- the architecture changed and the prompt no longer belongs to the active design.

### Deprecation requirements
When deprecating a prompt:
- mark status as deprecated,
- identify replacement if any,
- document reason,
- preserve historical trace if needed,
- document rollback implications if still relevant.

Deprecated prompts should not disappear without record.

---

## Retirement Policy

A prompt may be retired when it no longer needs to remain available for active or rollback use.

### Retirement requirements
Before retirement:
- confirm no active workflow depends on it,
- confirm rollback policy no longer requires it,
- preserve historical change record,
- update inventory.

Retirement should be rarer than deprecation.

---

## Rollback Policy for Prompts

Every important prompt revision should be rollback-aware.

### Rollback notes should clarify:
- prior active version,
- how to restore it,
- whether dependent prompts are affected,
- whether benchmark baselines need to be rerun,
- whether generated artifacts from the newer version remain valid.

A prompt change is not safely promoted without rollback clarity.

For baseline prompts, rollback expectations should be concrete enough that an agent or reviewer can restore the prior state
without reconstructing hidden chat context.

---

## Prompt Lifecycle States

Suggested lifecycle states:

### Draft
Prompt is being developed and is not ready for governed use.

### Experimental
Prompt may be tested in isolated runs but is not approved as default.

### Active
Prompt is approved for normal governed use.

### Deprecated
Prompt is no longer preferred but remains available for compatibility or rollback.

### Retired
Prompt is no longer in active use and has been formally removed from normal operations.

The repo should make status visible enough that humans and agents do not confuse experimental prompts with active defaults.

---

## Integration with Other Governance Documents

## With `docs/governance/model_governance.md`
Prompt lifecycle governs:
- prompt identity,
- prompt version,
- prompt dependency,
- prompt state.

Model governance governs:
- provider behavior,
- model adoption,
- benchmark thresholds,
- rollout and rollback across model APIs.

Prompt lifecycle should not duplicate model governance. It should describe prompt identity and change control,
while deferring cross-model policy and release thresholds to `docs/governance/model_governance.md`.

## With `docs/governance/testing_governance.md`
Prompt lifecycle governs prompt assets directly.

Testing governance governs:
- review structures,
- validation discipline,
- failure analysis,
- prompt set completeness as a testing-quality concern.

## With `docs/governance/acceptance.md`
Acceptance defines the gates that prompt-related changes must pass before release.

## With `docs/governance/agent_guidelines.md`
Agent guidelines define how AI coding agents must behave when changing prompts.

---

## AI Agent Rules for Prompt Lifecycle

Any AI coding agent modifying prompt assets must follow these rules.

### 1. Do not silently edit production prompts
Prompt edits require version changes and change notes.

### 2. Do not silently remove prompts from governed sets
Removal requires explicit lifecycle action.

### 3. Do not silently renumber or rename prompt IDs
Identity stability matters for traceability.

### 4. Do not ignore dependency impact
If a prompt affects downstream stages, that impact must be documented.

### 5. Do not promote experimental prompts without evidence
Benchmark and review gates still apply.

### 6. Keep prompt metadata aligned with prompt content
Metadata drift is a governance defect.

### 7. Do not use prompt edits to expand phase scope silently
Prompt work must stay inside the currently governed roadmap phase unless the new stage contract is explicitly introduced.

### 8. Do not treat a syntax-specific rendering prompt as the canonical contract
If the architecture defines a governed intermediate artifact, prompt changes must preserve that boundary.

---

## Suggested Repository Additions

To support prompt lifecycle governance, the repo should consider maintaining:

- `docs/governance/prompt_lifecycle.md`
- `prompts/`
- `prompts/registry.*`
- `prompts/changelog.*`
- benchmark cases linked to major prompt categories

The exact file format may vary, but lifecycle information must remain explicit and reviewable.
These additions are optional until the active prompt inventory is large enough to justify them.

---

## Review Checklist

Use this checklist before approving a prompt change.

### Required
- Is the prompt ID stable?
- Is the version updated?
- Is the change documented?
- Are dependencies reviewed?
- Is benchmark evidence attached?
- Are output expectations still correct?
- Is rollback clear?

### Recommended
- Were artifact diffs reviewed?
- Were edge cases checked?
- Was checker stability reviewed if applicable?
- Was lifecycle status confirmed?

---

## Summary

Prompt lifecycle governance ensures that prompts remain stable, reviewable, and rollback-safe assets rather than drifting implementation details.

In this repository, prompt governance should preserve:
- stable identity,
- complete prompt sets,
- visible dependencies,
- explicit versioning,
- benchmark-backed changes,
- and controlled deprecation and rollback.

This is essential for any AI testing framework that expects to evolve safely across multiple models, workflows, and contributors.

In the current repo phase, the practical goal is narrower: keep prompt changes explicit, benchmarked on a small governed baseline,
aligned with stage contracts, and safe for both humans and AI coding agents to review.
