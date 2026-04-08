# Testing Governance

## Purpose

This document defines the testing-governance layer for the repository.

It complements the architecture, roadmap, acceptance, and model governance documents by introducing the perspective that test teams need in order to operate the system safely and consistently.

This document exists to ensure that:

- prompt-driven workflows are treated as governed test assets,
- review and validation are structured and repeatable,
- changes are auditable,
- failure analysis is preserved,
- execution order and dependencies remain explicit,
- and testing quality does not drift as the framework evolves.

This document should be read together with:

- `docs/roadmap.md`
- `docs/implementation_plan.md`
- `docs/acceptance.md`
- `docs/model_governance.md`
- `docs/agent_guidelines.md`
- `docs/architecture.md`
- `docs/prompt_lifecycle.md`

---

## Why This Document Exists

The repository already has a strong engineering view of the system:
- pipeline stages,
- artifact contracts,
- phase roadmap,
- model governance,
- and architecture boundaries.

This document adds the **test-operations and test-asset governance view**.

In practical terms:

- architecture documents define how the system is built,
- testing governance defines how the system is validated, reviewed, and controlled as a testing asset.

Both are required for enterprise AI testing.

---

## Scope

This document governs:

- prompt inventory and lifecycle,
- review and feedback processes,
- confidence assessment,
- failure analysis,
- pre-run and post-run validation,
- integration test procedures,
- change impact tracking,
- rollback expectations,
- incremental update expectations,
- parallel execution expectations,
- error recovery expectations,
- testing-related performance metrics,
- minimum governance artifacts for reviewable runs.

It does **not** replace:
- architecture design,
- provider integration rules,
- roadmap sequencing,
- or schema contract definitions.

---

## Core Testing Governance Principles

### 1. Prompt sets are governed test assets

Prompts used in the system are not temporary instructions.  
They are governed assets that can affect downstream quality and must therefore be managed with the same discipline as schemas, configs, and test fixtures.

### 2. Completeness matters

A managed prompt set must not silently lose members, numbering, or dependency links.

### 3. Every meaningful change must leave an audit trail

Changes to prompts, review templates, test flow definitions, or output structures must include update records and impact notes.

### 4. Validation must exist both before and after execution

A testing workflow is not governed if it validates only the final output.  
Pre-run checks and post-run checks are both required.

### 5. Review quality must be explicit

Testing workflows should not stop at “pass/fail”.  
They should preserve:
- review comments,
- confidence judgments,
- failure analysis,
- and known limitations.

### 6. Failure must be analyzable

When outputs are poor, incomplete, or inconsistent, the system must capture why that happened and what should be improved.

### 7. Operational qualities are part of testing governance

Incremental updates, parallel execution, error recovery, and performance visibility are not optional implementation details.  
They are part of the quality envelope of the testing system.

### 8. Governed testing behavior must be repo-readable

If a workflow is intended to be repeatable and auditable, the controlling rules must live in repo-readable artifacts such as:
- prompts,
- review templates,
- validation checklists,
- integration procedures,
- acceptance rules,
- governance records.

---

## Test Asset Governance Model

## 1. Governed test assets

The following are considered governed test assets in this repo:

- prompt collections,
- prompt templates,
- review templates,
- feedback templates,
- confidence assessment templates,
- failure analysis templates,
- validation checklists,
- integration test procedures,
- benchmark cases,
- output file conventions,
- execution logs used for testing evidence,
- audit-style run records.

## 2. Minimum governance expectations

Every governed test asset should have, where applicable:

- stable identifier,
- version or revision trace,
- owner,
- scope,
- dependencies,
- update history,
- validation expectations,
- rollback notes if materially changed.

---

## Prompt Set Governance

This section adapts the strongest ideas from the tester-oriented workflow into repo-friendly governance rules.

## 1. Prompt set completeness

If the project maintains a defined prompt collection for a workflow, the collection must remain complete unless a reviewed decision explicitly changes it.

### Required
- no silent prompt deletion,
- no silent renumbering,
- no silent dependency breakage,
- no silent replacement of one governed prompt by another.

### Implication
An agent or developer must not reduce the governed prompt set just because a smaller set “seems enough”.

## 2. Prompt identifiers

Each governed prompt should have:
- a stable prompt ID,
- a human-readable name,
- version information,
- scope description,
- upstream dependencies,
- downstream consumers.

## 3. Prompt dependency awareness

Where prompts form a sequence, the repo should document:
- execution order,
- required inputs,
- generated outputs,
- downstream dependencies,
- and which prompts are foundational.

## 4. Prompt output expectations

For major prompts, the repo should define:
- expected output artifacts,
- output location,
- validation requirements,
- review artifacts if required,
- and whether README or index files must be updated.

## 5. Prompt lifecycle records

A prompt change record should capture:
- date,
- author,
- description,
- downstream impact,
- validation performed.

This applies especially to prompts used in repeatable workflows, not only to exploratory experimentation.

---

## Review and Feedback Governance

## 1. Review is a governed control layer

Review outputs are not casual notes.  
They are controlled testing artifacts that help determine whether generated outputs are fit for use.

## 2. Minimum review categories

The governance system should support structured review categories such as:

- skill-related review,
- test-related review,
- code-related review,
- documentation review,
- framework review,
- governance review.

The exact folder layout may evolve, but category-based review templates are encouraged because they improve consistency.

## 3. Review deliverables

For significant governed workflows, review output should ideally preserve:

- review result,
- structured feedback,
- confidence assessment,
- failure analysis,
- reviewer identity or role,
- reviewed artifact reference,
- timestamp.

## 4. Feedback templates

Feedback should not be completely ad hoc for governed flows.  
The repo should support reusable feedback structures for:
- correctness issues,
- coverage gaps,
- formatting inconsistencies,
- dependency problems,
- confidence concerns,
- failure root causes.

---

## Confidence Assessment Governance

## 1. Confidence is separate from pass/fail

A generated artifact may be acceptable yet still have low confidence.  
Confidence should therefore be tracked as a separate signal where valuable.

## 2. Confidence inputs

Confidence may be informed by:
- schema validity,
- review quality,
- traceability completeness,
- stable source-anchor completeness where applicable,
- consistency across multiple runs,
- checker stability,
- known ambiguity level,
- quality of supporting evidence.

## 3. Confidence output usage

Confidence should be used to:
- prioritize human review,
- identify unstable workflows,
- highlight risky outputs,
- guide future benchmark expansion.

Confidence should not be treated as a substitute for actual validation.

---

## Failure Analysis Governance

## 1. Failure analysis is mandatory for important workflow failures

When a governed workflow fails materially, the failure should produce a structured analysis.

## 2. Failure analysis should capture

At minimum:
- what failed,
- where it failed,
- likely root cause,
- affected downstream artifacts,
- whether recovery was attempted,
- whether rollback is needed,
- recommended next action.

## 3. Failure categories

Suggested categories:
- source/input failure,
- extraction failure,
- schema/contract failure,
- prompt or model behavior failure,
- review workflow failure,
- reporting failure,
- integration failure.

## 4. Retention

Failure analyses should be retained as learning artifacts, not discarded after the immediate issue is closed.

---

## Pre-Run and Post-Run Validation

## 1. Pre-run validation

Before a governed workflow executes, validate:

- source availability,
- source readability,
- required directories and paths,
- permission assumptions,
- risk of accidental overwrite,
- required dependencies,
- stable source-anchor generation expectations where relevant,
- space or environment prerequisites when relevant.

## 2. Post-run validation

After execution, validate:

- required artifacts exist,
- naming conventions are respected,
- schema constraints pass,
- traceability references resolve,
- stable source anchors are preserved where applicable,
- index or summary outputs are updated if required,
- review outputs are generated if required,
- logs and metadata are present.

## 3. Architectural alignment

Pre-run and post-run validation should be treated as part of the testing architecture, not as optional operational scripts.

---

## Change Impact and Rollback Governance

## 1. Change impact notes

Before significant workflow changes, document:

- what is changing,
- which assets are affected,
- which downstream prompts or modules may be affected,
- whether traceability changes,
- whether review or reporting expectations change.

## 2. Change execution records

After significant workflow changes, record:

- files changed,
- generated outputs,
- validation status,
- exceptions or deviations,
- reviewer observations,
- unresolved follow-up items.

## 3. Rollback expectations

For important prompt, template, review, or flow changes, define rollback expectations.

Rollback notes should clarify:
- what to revert,
- what generated artifacts may need restoration,
- whether documentation must also be reverted,
- whether review artifacts remain valid after rollback.

---

## Integration Test Governance

## 1. Integration tests are required for governed workflow chains

If a workflow depends on sequence, dependency, or output handoff between stages, there should be integration tests or integration test procedures.

## 2. Integration test procedures should define

- scenario name,
- purpose,
- prerequisites,
- steps,
- expected outputs,
- expected review artifacts,
- expected validation checks.

## 3. Integration test focus areas

For this framework, integration governance should especially cover:
- extraction to rule artifacts,
- rule artifacts to maker output,
- maker output to checker output,
- checker output to review workflow,
- review decisions to rewrite flow,
- report generation from final artifacts.

## 4. Sequential dependency awareness

If one prompt or stage is foundational to others, integration tests should confirm sequence integrity.

---

## Incremental Update Governance

## 1. Incremental update support is a quality requirement

If a workflow claims to support partial updates, that claim must be testable and governed.

## 2. Required controls

Incremental update support should include:
- change detection,
- changed-scope tracking,
- update logging,
- validation of updated subset,
- traceability preservation.

## 3. Risk

Incremental updates can silently create mixed-version artifacts.  
Testing governance must therefore ensure that updated and untouched outputs remain coherent together.

---

## Parallel Execution Governance

## 1. Parallel execution must preserve correctness

If tasks are processed in parallel, governance must ensure that:
- identifiers remain unique,
- outputs do not overwrite each other,
- logging remains attributable,
- traceability remains intact,
- stable source anchors remain attributable,
- failure isolation works as expected.

## 2. Parallel execution checks

Where relevant, validate:
- task partitioning,
- output isolation,
- progress tracking,
- race condition avoidance,
- resource management behavior.

---

## Error Recovery Governance

## 1. Recovery must be bounded and observable

Automatic recovery is allowed only if:
- recovery logic is documented,
- recovery attempts are logged,
- recovered outputs remain traceable,
- unrecoverable cases fail visibly.

## 2. Recovery records

Recovery logs should capture:
- error type,
- stage,
- recovery action,
- success/failure,
- time spent,
- impact on final outputs.

## 3. Governance rule

Recovery should never hide that an error occurred.

---

## Performance and Operational Metrics

Testing governance should include metrics beyond correctness.

## Minimum recommended metrics

### Execution metrics
- start time
- end time
- total duration
- per-stage duration

### Resource metrics
- memory use where measurable
- CPU use where measurable
- I/O heavy operation timing where relevant

### Quality metrics
- artifacts generated
- schema pass rate
- traceability completeness
- stable source-anchor completeness where applicable
- review completion rate
- checker instability rate

### Error metrics
- error count
- error category distribution
- recovery attempt count
- recovery success rate

### Update metrics
- changed scope count
- update duration
- change detection accuracy where measured

### Parallel metrics
- number of concurrent tasks
- parallel execution duration
- resource utilization observations

These do not all need to be implemented immediately, but they should remain part of the long-term testing governance model.

---

## Minimum Governance Artifacts

A governed testing workflow should be able to produce or preserve, where relevant:

- run summaries,
- review summaries,
- confidence summaries,
- failure analyses,
- drift comparison outputs,
- checker instability summaries,
- change impact notes,
- rollback notes,
- integration test evidence,
- audit-style execution records.

The exact repo structure may evolve, but these artifacts should remain repo-readable and reviewable.

---

## Recommended Repository Additions

To fully absorb the testing perspective into the repo, the following patterns are recommended.

## 1. Testing governance document
This document itself should exist as:
- `docs/testing_governance.md`

## 2. Optional prompt lifecycle document
If the repo formalizes a stable prompt inventory, add:
- `docs/prompt_lifecycle.md`

That document may include:
- prompt inventory,
- prompt IDs,
- dependencies,
- output expectations,
- lifecycle state,
- deprecation rules.

## 3. Review template organization
Review templates may be organized by category and workflow type to improve consistency.

## 4. Output naming conventions
Prompt- or stage-specific output naming conventions should be documented if they are intended to be stable operating rules.

---

## What Should Be Merged into Existing Docs

This testing-governance perspective should strengthen, not replace, the existing repo docs.

### Into `docs/architecture.md`
Add or preserve emphasis on:
- pre-run and post-run validation,
- stable source anchors,
- incremental and parallel execution as governed quality concerns,
- prompt/template assets as governed artifacts.

### Into `docs/acceptance.md`
Add or preserve:
- confidence evidence,
- failure analysis evidence,
- integration test evidence,
- rollback verification,
- stable source-anchor evidence where applicable.

### Into `docs/model_governance.md`
Add or preserve:
- prompt dependency awareness,
- prompt collection completeness expectations,
- prompt change impact analysis.

### Into `docs/agent_guidelines.md`
Add or preserve:
- no silent prompt deletion,
- no silent prompt renumbering,
- no silent dependency breakage,
- mandatory update record behavior for governed prompt assets.

---

## AI Agent Rules for Testing Governance

Any AI coding agent working with test-governed assets must follow these rules.

### 1. Do not silently delete governed prompts or templates
If a governed prompt or review template is removed, the change must be explicit, justified, and documented.

### 2. Do not silently renumber prompt sets
Prompt identity must remain stable unless a reviewed migration is performed.

### 3. Do not break dependency chains without documentation
If a prompt or workflow stage changes upstream or downstream dependencies, that must be recorded.

### 4. Do not skip update records for governed test assets
Changes to governed prompt sets, review templates, or validation templates require traceable update notes.

### 5. Do not treat review, confidence, or failure analysis outputs as optional when a governed workflow requires them
If a workflow contract expects them, they are part of completion.

---

## Review Questions

Use these questions when reviewing testing-governance changes:

- Does this change preserve governed prompt set integrity?
- Are update records and impacts documented?
- Are pre-run and post-run validations still clear?
- Does the change weaken review rigor?
- Does it reduce confidence visibility?
- Does it remove failure-analysis capability?
- Does it weaken rollback clarity?
- Does it affect integration-test sequencing?
- Does it preserve incremental and parallel execution expectations where relevant?
- Does it preserve stable source-anchor handling where applicable?

---

## Summary

Testing governance adds the operational quality layer that architecture alone cannot provide.

In this repository:
- architecture defines the system skeleton,
- model governance controls probabilistic dependencies,
- acceptance defines gates,
- agent guidelines define implementation discipline,
- and testing governance ensures that prompts, review, validation, confidence, failure analysis, and operational test quality remain controlled.

This is the layer that helps turn a promising AI testing framework into a system that test teams can actually trust and operate.
