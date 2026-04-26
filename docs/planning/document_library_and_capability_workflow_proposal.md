# Document Library and Capability Workflow Proposal

**Status:** Proposal / future direction  
**Created:** 2026-04-26  
**Current baseline impact:** None. This document does not change artifact schemas, prompts, models, pipeline behavior, review-session behavior, or roadmap completion claims.

---

## Purpose

This proposal captures a future workflow direction for handling multiple engineering documents, document versions, and LLM-assisted knowledge work in a governed way.

The core idea is not to build a generic document dump or RAG chat interface. The goal is to make engineering knowledge traceable:

> Documents provide evidence, knowledge records capture reviewed meaning, capability steps perform governed work, LLMs produce candidate artifacts, and humans approve business judgment.

This aligns with the repository's existing principles:

- artifacts are first-class contracts,
- deterministic validation comes before LLM judgment,
- LLM output is probabilistic and must be reviewed,
- source anchors and provenance must remain visible,
- human review is a control layer.

This document is aligned with the broader proposal package in `docs/architecture/Executable_Engineering_Knowledge_Contract.md`. That package defines the general MVP spine as:

```text
Spec Change -> Test Impact -> Automation Backlog
```

For this repository, the immediate pilot slice should remain narrower and domain-specific:

```text
Initial Margin HKv13 -> HKv14 -> Governed Diff -> Impact Assessment -> Downstream Bridge Decision
```

---

## Problem

The project currently handles governed artifacts derived from a small number of source documents. In real project use, teams will receive many document types from different owners and phases, including:

- business requirements,
- functional specifications,
- architecture documents,
- calculation guides,
- test plans,
- release plans,
- regression pack indexes,
- defect or risk records,
- signoff and decision records.

Simply storing these documents does not automatically increase usable knowledge for either humans or LLMs. The system needs to preserve:

- which document version is authoritative,
- what changed between versions,
- which requirement or rule each statement comes from,
- which team or role owns interpretation,
- which artifacts were generated from the evidence,
- which outputs were reviewed and approved.

---

## Conceptual Model

The proposed model separates four layers.

### 1. Document Assets

Original source materials and parsed document units.

Examples:

- `Initial Margin Calculation Guide HKv13.pdf`
- `Initial Margin Calculation Guide HKv14.pdf`
- parsed page text,
- clauses,
- tables,
- source anchors,
- document metadata.

Required metadata should include at least:

- document id,
- title,
- version,
- document class,
- owner or source,
- status,
- effective date if known,
- supersedes relationship if known,
- source file path,
- parsing timestamp or artifact generation timestamp.

### 2. Knowledge Assets

Reviewed facts, rules, relationships, or decisions extracted from documents.

Examples:

- a calculation rule,
- a validation condition,
- a release date,
- a signoff status,
- a version relationship,
- a reviewed interpretation of ambiguous source text.

Knowledge assets should not be created directly from LLM output without review. LLM output should first be treated as a candidate artifact.

### 3. Capability Assets

Reusable governed actions that can be invoked by workflows.

Examples:

- compare two document versions,
- generate a change list,
- map changed requirements to test plan coverage,
- identify regression impact,
- produce an impact assessment for review.

Each capability should eventually have a formal definition:

- stable capability id,
- allowed roles,
- input contract,
- output contract,
- validation rules,
- prompt template and prompt version if LLM-backed,
- maker/checker policy if LLM-backed,
- required human review role,
- audit metadata.

### 4. Workflow Assets

Human-readable and machine-resolvable workflow definitions, potentially using a BDD/Gherkin style.

In this proposal, BDD is not only a test-case syntax. It can also act as a knowledge workflow DSL that composes controlled capability steps.

Example future workflow:

```gherkin
@initial_margin @hk_v14 @impact_review
Scenario: Assess Initial Margin guide version impact
  Given document "im_hk_v14" supersedes document "im_hk_v13"
  When the Initial Margin guide version impact is reviewed
  Then compare governed rules between "im_hk_v13" and "im_hk_v14"
  And identify changed calculation behavior
  And produce an impact assessment for human review
```

This kind of workflow should resolve to governed capability definitions, not arbitrary free-form prompts.

---

## Proposed Architecture Direction

The long-term architecture can be described as these modules:

| Module | Responsibility |
| --- | --- |
| Document Library | Store source files, metadata, versions, statuses, and relationships. |
| Document Parser | Convert PDF, Word, Excel, Markdown, or other source formats into anchored document units. |
| Version Diff Engine | Compare raw text, structure, semantic rules, source anchors, and downstream impact. |
| Knowledge Registry | Store reviewed knowledge items and relationships between documents, rules, releases, systems, tests, and decisions. |
| Capability Registry | Store governed step definitions, prompt-backed capabilities, schemas, validation rules, and review policy. |
| Workflow Composer | Let users assemble role-oriented workflows from registered capability steps. |
| Execution Engine | Run deterministic or LLM-backed capabilities and save candidate artifacts with provenance. |
| Review and Governance | Route candidate artifacts through checker and human review before acceptance. |
| Artifact Repository | Store approved change lists, impact assessments, BDD, scripts, reports, and audit records. |

This is a future direction. It should not be implemented as one large platform change.

---

## LLM Governance Model

For any LLM-backed capability, the default control pattern should be:

```text
Maker LLM -> candidate artifact
Checker LLM or deterministic validator -> quality/evidence review
Human reviewer -> final approval/reject/rework decision
```

Key rules:

- LLM output is not accepted knowledge.
- Checker should not simply regenerate the same answer; it should verify evidence, completeness, consistency, missing changes, hallucination risk, and ambiguity.
- High-risk decisions such as go/no-go, business interpretation, and production readiness must remain human-owned.
- Every model-driven capability must record prompt version, model/provider metadata, source artifact hashes, and review status.

This extends the existing maker/checker/human pattern already used in the repository.

---

## Risks

### BDD Becomes Free-Form Chat

If steps are not backed by a registry and contracts, workflows can degrade into vague prompts such as "review everything" or "analyze the project."

Mitigation: only allow registered capability steps in governed workflows.

### Metadata Quality Is Weak

Document versioning and diffing become unreliable if uploaded documents lack status, owner, version, source, or supersedes relationships.

Mitigation: enforce a document metadata schema before downstream processing.

### LLM Output Is Treated as Fact

The system would become unsafe if candidate outputs automatically became trusted knowledge.

Mitigation: separate candidate artifacts from approved knowledge and require review gates for promotion.

### Scope Expands Too Early

A complete document platform, GUI, knowledge graph, workflow engine, and role system would exceed the current roadmap.

Mitigation: implement only small governed slices that serve current phase goals.

---

## Recommended MVP

The broader proposal package defines the MVP as:

> **Spec Change -> Test Impact -> Automation Backlog**

That MVP is a good general delivery workflow because it has clear inputs, outputs, role approvals, and artifact states. For this repository, the recommended first implementation slice is a smaller version of the same pattern:

> **S2-C3: Initial Margin HKv14 Intake and HKv13/HKv14 Governed Diff**

This maps the broader MVP into the current project without introducing a generic document library, GUI workflow composer, or new prompt-backed capability registry.

| General MVP Concept | Repo-Local Pilot |
| --- | --- |
| Old spec version | Initial Margin HKv13 guide and governed artifacts |
| New spec version | Initial Margin HKv14 guide and governed artifacts |
| Change list | HKv13/HKv14 governed diff report |
| Ambiguity list | Changed or unclear source-anchor/rule interpretation list |
| Test impact | Maker/checker/BDD/mock API impact summary |
| Automation backlog draft | Recommendation on whether an HKv14 mock API bridge or BDD updates are needed |
| Human approval record | Review note or planning record before downstream implementation |

The MVP should not build a generic document library UI. It should produce a deterministic, reviewable version intake and diff workflow for one concrete document family.

### Inputs

- `docs/materials/Initial Margin Calculation Guide HKv13.pdf`
- `docs/materials/Initial Margin Calculation Guide HKv14.pdf`
- `artifacts/im_hk_v13/`
- `artifacts/im_hk_v14/`

### Expected Outputs

- complete governed HKv14 artifacts under `artifacts/im_hk_v14/`,
- HKv14 validation report,
- HKv13/HKv14 diff report,
- source-anchor comparison,
- changed rule summary,
- downstream impact summary for maker/checker/BDD/mock API,
- recommendation on whether `deliverables/im_hk_v14_mock_api/` is needed.

### Acceptance Direction

The MVP should pass when:

- HKv14 artifacts validate deterministically,
- HKv13 remains preserved as baseline,
- HKv13/HKv14 differences are visible and reviewable,
- no artifact schema or prompt/model default is changed silently,
- any downstream mock API work is justified by documented differences.

---

## Non-Goals For Now

The following are explicitly out of scope for the near-term MVP:

- generic multi-user document upload GUI,
- full knowledge graph database,
- role-based access control,
- enterprise workflow composer,
- prompt-backed capability registry as production behavior,
- new LLM-driven stage without schemas and acceptance criteria,
- replacing existing maker/checker/BDD contracts,
- treating BDD workflow files as canonical knowledge without reviewed artifacts.

---

## Rollback Considerations

Because this proposal is documentation-only, rollback is simple:

- remove this proposal document,
- keep existing HKv13 artifacts and deliverables unchanged,
- continue using current pipeline and governance documents as baseline.

Any future implementation based on this proposal must define its own rollback plan before changing schemas, prompts, models, or pipeline behavior.

---

## Self-Evaluation

| Item | Status | Notes |
| --- | --- | --- |
| Preserves current roadmap boundaries | PASS | Proposal is explicitly non-baseline and future-facing. |
| Avoids silent schema or prompt changes | PASS | No schema, prompt, model, or pipeline change is proposed as active behavior. |
| Maps to concrete near-term work | PASS | Recommends HKv14 intake and HKv13/HKv14 governed diff as the first slice. |
| Keeps LLM role governed | PASS | Candidate artifact, checker, and human approval boundaries are explicit. |
| Avoids oversized platform scope | PASS | Full GUI, knowledge graph, and workflow engine are listed as non-goals. |
