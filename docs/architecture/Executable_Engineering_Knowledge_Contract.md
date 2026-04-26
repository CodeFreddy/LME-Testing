
# Proposal Package / Not Current Baseline Architecture

**Status:** Proposal package / future direction  
**Current baseline impact:** None. This document does not change artifact schemas, prompts, models, pipeline behavior, review-session behavior, acceptance status, or roadmap completion claims.  
**Implementation rule:** Any work derived from this proposal must be promoted through the governed roadmap, with explicit contracts, validation, traceability, human review, tests, and rollback notes.

---

# Introduction

```text
Proposal Package:
01_executive_one_pager.md
02_concept_and_operating_model.md
03_mvp_scope_and_delivery_plan.md
04_platform_architecture_proposal.md
05_integration_roadmap.md
06_example_workflow_pack.md
07_risk_control_matrix.md
```

Distribution Recommendations:

| Audience | Recommended Documents |
|---|---|
| Group CTO | 01 + 02 + 05 + 07 |
| Department SVP | 01 + 02 + 03 + 07 |
| Platform Development Team | 02 + 03 + 04 + 05 + 06 |
| BA / QA / Auto / DevOps Lead | 02 + 03 + 06 |

---

# 01 Executive One-Pager

## Title

**Executable Engineering Knowledge Contract**  
**A governed, evidence-backed, human-in-the-loop LLM workflow for enterprise delivery**

---

## 1. Background

Current enterprise delivery projects depend on many documents and tools:

```text
Business Requirement
Function Spec
Architecture Document
Test Plan
Release Plan
Risk Register
JIRA
Zephyr
Confluence / SharePoint
Git Repository
CI/CD Pipeline
Execution Reports
```

However, simply accumulating documents does not automatically create reliable engineering knowledge.

The real challenge is not document storage, but:

```text
- Which document version is the delivery baseline?
- What changed between versions?
- Which requirements are impacted?
- Which tests cover those requirements?
- Which automation assets are affected?
- Which release risks are open?
- Who is responsible for each judgement?
- Which LLM output has been verified and approved?
```

---

## 2. Proposed Direction

We propose an **Evidence-backed Delivery Knowledge Workflow Platform**.

The platform uses:

```text
Documents as evidence
Knowledge Index as context
BDD-style Feature as collaboration contract
Governed Agent Skills as execution capabilities
Maker / Checker as LLM validation pattern
Human roles as final accountable approvers
```

This is not a free-form AI chatbot, and not a simple document repository.

It is a structured workflow model that connects documents, delivery events, responsibilities, LLM-assisted analysis, human approval, and downstream engineering execution.

---

## 3. Core Principle

```text
LLM output is not approved knowledge.
LLM output is a candidate artifact.

Maker LLM generates.
Checker validates.
Human role approves.
Approved output becomes delivery knowledge or project artifact.
```

---

## 4. Strategic Value

This direction can help the group establish a controlled foundation for AI-assisted engineering delivery:

```text
- Convert fragmented delivery documents into structured, traceable knowledge.
- Improve transparency across PM, BA, QA, Automation, DevOps and platform teams.
- Reduce uncontrolled prompt usage.
- Preserve human accountability.
- Build reusable engineering capabilities instead of one-off prompts.
- Connect requirements, tests, automation, CI/CD, JIRA and release readiness over time.
```

---

## 5. Recommended MVP

The MVP should focus on one high-value workflow:

```text
Spec Change → Test Impact → Automation Backlog
```

Initial scope:

```text
Input:
- Function Spec old version
- Function Spec new version
- Test Plan
- Regression Pack Index

Output:
- Change List
- Requirement Ambiguity List
- Test Plan Gap List
- Regression Impact List
- Automation Backlog Draft
- Human Approval Record
```

Initial roles:

```text
BA
QA Lead
Automation Lead
Platform Admin
```

---

## 6. Phased Roadmap

```text
Phase 1: MVP
Document versioning, spec diff, change list, test impact, maker/checker, human approval.

Phase 2: Workflow Expansion
Role-based workflows, decision records, assumption tracking, reusable workflow templates.

Phase 3: System Integration
Integrate with Confluence/SharePoint, JIRA, Zephyr, Git repository, CI/CD, execution reports.

Phase 4: Engineering Intelligence Layer
Build traceability across requirement → test → automation → code → CI/CD → defect → release readiness.

Phase 5: Enterprise Knowledge Governance
Reusable skills, cross-system knowledge index, audit, risk controls, enterprise reporting.
```

---

## 7. Decision Needed

Approval to run a controlled MVP with limited scope, using one release or one representative system, to validate the value of evidence-backed, human-approved, LLM-assisted engineering workflow.

---

# 02 Concept and Operating Model

## Title

**From Document Repository to Executable Engineering Knowledge Contract**

---

## 1. Problem Statement

Enterprise delivery teams already produce many documents, but the knowledge inside them is often fragmented.

Typical problems:

```text
- Function Spec versions are difficult to compare.
- Test Plans are not always clearly mapped to requirement changes.
- Regression impact depends heavily on senior engineers' experience.
- Automation backlog is often manually inferred.
- PM, BA, QA, Auto and DevOps may work from different assumptions.
- LLM usage may produce useful drafts, but without governance it is hard to trust.
```

The problem is not lack of documentation.

The problem is lack of structured relationships between:

```text
Document
Version
Requirement
Change
Test Plan
Regression Pack
Automation Asset
Environment
Release Timeline
Decision
Risk
Owner
Approval
```

---

## 2. Proposed Concept

The proposed model introduces an **Executable Engineering Knowledge Contract**.

A BDD-style Feature file is used as a human-readable collaboration contract.

It expresses:

```text
- Release context
- Baseline documents
- Timeline
- Role responsibilities
- Required deliverables
- LLM-assisted steps
- Review and approval points
```

Each Step does not directly mean a free prompt.

Each Step maps to a governed capability, also called a **Governed Agent Skill**.

---

## 3. Concept Mapping

| Concept | Meaning |
|---|---|
| Document Library | Evidence source |
| Knowledge Index | Structured relationship layer |
| Feature | Engineering collaboration contract |
| Scenario | Role-specific workflow |
| Step | Skill invocation |
| Step Definition | Governed skill contract |
| Prompt Template | Skill implementation detail |
| Maker LLM | Candidate artifact generator |
| Checker | Validation layer |
| Human Reviewer | Accountable approver |
| Approved Artifact | Accepted delivery knowledge |

---

## 4. Operating Principle

The platform should follow this lifecycle:

```text
Upload / connect documents
  ↓
Validate document readiness
  ↓
Parse and version documents
  ↓
Generate structural and semantic diff
  ↓
Generate candidate change list
  ↓
Checker validates evidence, consistency and coverage
  ↓
BA / QA / Auto Lead reviews
  ↓
Approved artifact becomes delivery baseline
  ↓
Downstream workflow continues
```

---

## 5. Role-based Operating Model

| Role | Responsibility | LLM Role | Final Decision |
|---|---|---|---|
| PM | Timeline, milestone, release dependency | Summarize risks and dependencies | PM |
| BA | Requirement meaning and ambiguity | Compare specs, identify requirement changes | BA |
| QA Lead | Test scope, coverage, test approach | Suggest coverage gaps and risk areas | QA Lead |
| Automation Lead | Regression impact and automation backlog | Map changes to automation assets | Automation Lead |
| DevOps | Environment readiness and deployment state | Generate readiness checklist | DevOps |
| Platform Team | Capability, workflow, integration, audit | Provide execution platform | Platform Owner |
| CTO / SVP | Governance and strategic direction | Review reports and metrics | Human leadership |

---

## 6. Maker / Checker / Human Approval

Each LLM-assisted Step should use the following pattern:

```text
Maker:
  Generates candidate output.

Checker:
  Validates evidence, schema, consistency, completeness and possible hallucination.

Human:
  Reviews unresolved ambiguity, applies business judgement, approves or rejects.
```

Checker should not be only another LLM call.

Checker should include:

```text
- Schema validation
- Evidence validation
- Version consistency check
- Required field check
- Coverage check
- LLM semantic review
- Human review
```

---

## 7. Why BDD-style Feature?

BDD is useful here not because this is traditional test automation, but because it provides a readable structure for collaboration.

Example:

```gherkin
@OTC @release_0_8_patch_2 @Auto
Scenario: Automation Lead confirms regression and automation impact
  Given Function Spec "v1.3" has status "signed_off"
  And Function Spec "v1.3" supersedes Function Spec "v1.1"
  And Regression Pack "OTC-Full" is available
  When Maker maps changed requirements to existing regression features
  And Checker verifies coverage mapping against feature index
  Then Automation Lead should approve regression impact assessment
  And Automation Lead should produce automation implementation backlog
```

This is not just a test scenario.

It is a role-based engineering workflow.

---

## 8. Important Boundary

The Feature file should not become the knowledge database.

Correct boundary:

```text
Feature = workflow contract
Knowledge Index = facts and relationships
Document Library = evidence
Artifact Repository = generated and approved outputs
Audit Log = execution and review history
```

---

# 03 MVP Scope and Delivery Plan

## Title

**MVP: Spec Change to Test Impact Workflow**

---

## 1. MVP Objective

The MVP should prove one core value:

> Can we use document evidence, governed LLM skills, maker/checker validation and human approval to reliably convert Function Spec changes into test and automation impact?

---

## 2. MVP Scope

### In Scope

```text
1. Upload or register Function Spec old version.
2. Upload or register Function Spec new version.
3. Upload or register Test Plan.
4. Upload or register Regression Pack Index.
5. Validate document metadata and readiness.
6. Compare spec versions.
7. Generate change list.
8. Identify ambiguous requirement changes.
9. Map changes to Test Plan.
10. Map changes to Regression Pack.
11. Generate automation impact assessment.
12. Run maker/checker workflow.
13. Capture human review and approval.
14. Store approved artifacts.
15. Provide a role-friendly review and decision UI so BA, QA Lead and Automation Lead can record decisions without editing Markdown or raw YAML.
```

### Out of Scope for MVP

```text
- Full enterprise knowledge graph
- Full permission model
- Full JIRA integration
- Full Zephyr integration
- Full Git repository scanning
- Full CI/CD integration
- Fully automated decision making
- Automatic update of test cases
- Automatic code generation
- Enterprise-wide deployment
```

---

## 3. MVP Input

```text
Function Spec v1.1
Function Spec v1.3
Test Plan v2.6
Regression Pack Index
Optional: Existing automation feature index
```

---

## 4. MVP Output

```text
Change List
Requirement Ambiguity List
Test Plan Gap List
Regression Impact List
Automation Backlog Draft
Checker Report
Human Review Record
Approved Impact Assessment
```

---

## 5. MVP Core Capabilities

| Capability | Type | Owner |
|---|---|---|
| Document readiness check | Deterministic + human review | Platform / BA |
| Document version comparison | Tool + LLM summary | Platform |
| Change list generation | Maker LLM | BA |
| Change list verification | Checker | BA / QA |
| Requirement ambiguity detection | LLM-assisted | BA |
| Requirement-to-test mapping | LLM-assisted + evidence check | QA Lead |
| Requirement-to-regression mapping | LLM-assisted | Automation Lead |
| Automation backlog generation | LLM-assisted | Automation Lead |
| Human approval | Human workflow | BA / QA / Auto |

---

## 6. MVP Workflow

```text
Step 1: Register documents
Step 2: Validate metadata
Step 3: Parse documents
Step 4: Generate structural diff
Step 5: Maker generates semantic change list
Step 6: Checker validates evidence and coverage
Step 7: BA reviews requirement meaning
Step 8: QA Lead maps changes to Test Plan
Step 9: Automation Lead maps changes to regression pack
Step 10: Generate automation backlog draft
Step 11: Human approval
Step 12: Store approved artifacts
```

---

## 7. MVP Example Feature

```gherkin
@OTC @release_0_8_patch_2 @mvp
Feature: Spec Change to Test Impact Workflow

  Background:
    Given System "OTC" is selected
    And Release "0.8 Patch 2" is selected
    And Function Spec "v1.3" has status "signed_off"
    And Function Spec "v1.3" supersedes Function Spec "v1.1"
    And Test Plan "v2.6" is the approved test baseline

  @BA
  Scenario: BA confirms requirement changes
    When Maker generates change list from Function Spec "v1.1" to "v1.3"
    And Checker verifies the change list against source documents
    Then BA should review unresolved ambiguities
    And BA should approve requirement interpretation

  @QA
  Scenario: QA Lead confirms test impact
    Given BA has approved requirement change list
    When Maker maps changed requirements to Test Plan "v2.6"
    And Checker verifies requirement-to-test evidence
    Then QA Lead should approve test impact assessment

  @Auto
  Scenario: Automation Lead confirms automation impact
    Given QA Lead has approved test impact assessment
    And Regression Pack "OTC-Full" is available
    When Maker maps changed requirements to existing regression features
    And Checker verifies coverage mapping against feature index
    Then Automation Lead should approve regression impact assessment
    And Automation Lead should produce automation backlog draft
```

---

## 8. MVP Success Criteria

| Area | Success Criteria |
|---|---|
| Traceability | Each change item links to source document evidence |
| Quality | Checker identifies missing evidence or ambiguity |
| Human control | BA / QA / Auto approval is captured |
| Reuse | Same workflow can be reused for another spec version |
| Efficiency | Manual spec comparison effort is reduced |
| Transparency | PM / SVP can see status, owner, artifact and pending decision |
| Governance | No LLM output becomes approved knowledge without human approval |

---

## 9. Role-Friendly Review and Decision UI Requirement

Human approval should not depend on BA, QA Lead, Automation Lead or PM editing Markdown files directly.

The platform should provide a friendly review UI for role owners to:

```text
- view source evidence and deterministic diff candidates,
- review checker findings and open ambiguities,
- classify candidate changes,
- approve, reject, defer or request rework,
- add decision rationale and comments,
- record reviewer role, reviewer name and timestamp,
- export the approved decision record into the governed artifact repository.
```

The UI should support at least:

| Role | Primary decisions captured |
|---|---|
| BA | Requirement meaning, ambiguity, business interpretation |
| QA Lead | Test impact, test plan gap, coverage risk |
| Automation Lead | Regression impact, automation backlog scope |
| PM / Release Owner | Readiness risk and unresolved dependency |

The UI is an interaction layer over governed artifacts. It must not become the source of truth by itself. Decisions captured through the UI must be persisted as structured review records and linked back to source evidence, checker reports and generated artifacts.

For early MVP, this can be implemented as a local, single-user review form or table view. Full role-based access control, hosted workflow collaboration and enterprise permissions remain later-phase work.

---

# 04 Platform Architecture Proposal

## Title

**Architecture Proposal for Evidence-backed Delivery Knowledge Workflow Platform**

---

## 1. System Positioning

This platform is not:

```text
- A generic document management system
- A free-form AI chatbot
- A traditional test automation framework
- A replacement for JIRA, Zephyr, Git or CI/CD
- A pure RAG search application
```

This platform is:

```text
An engineering knowledge workflow orchestration layer.
```

It connects:

```text
Documents
Requirements
Decisions
Workflow
Governed skills
Human approval
Engineering systems
```

---

## 2. Target Architecture

```text
Document Sources
  - SharePoint
  - Confluence
  - Word / PDF / Excel
  - Git markdown docs

        ↓

Evidence Layer
  - document metadata
  - version control
  - evidence anchors
  - document readiness check
  - structural diff

        ↓

Knowledge Index
  - requirement
  - change item
  - release
  - system
  - component
  - risk
  - decision
  - assumption
  - open question
  - coverage relation

        ↓

Workflow Layer
  - BDD Feature
  - role scenario
  - workflow template
  - project instance
  - state machine

        ↓

Capability Layer
  - governed agent skill
  - prompt template
  - deterministic validator
  - maker/checker policy
  - schema validation

        ↓

Governance Layer
  - human review
  - approval
  - audit trail
  - lifecycle
  - evidence level
  - risk controls

        ↓

Artifact Layer
  - change list
  - test impact report
  - automation backlog
  - decision record
  - release readiness summary
```

---

## 3. Core Modules

| Module | Responsibility |
|---|---|
| Document Library | Store or reference documents and versions |
| Document Parser | Extract structure, headings, tables and anchors |
| Document Readiness Checker | Validate metadata and baseline quality |
| Diff Engine | Compare versions structurally and semantically |
| Knowledge Index | Store relationships and approved knowledge |
| Capability Registry | Manage governed skills and Step Definitions |
| Workflow Composer | Create role-based Feature workflows |
| Execution Engine | Run maker/checker/deterministic steps |
| Review Center | Manage human review and approval |
| Artifact Repository | Store generated and approved outputs |
| Audit Trail | Record inputs, outputs, prompts, model versions and approvals |
| Integration Layer | Connect JIRA, Zephyr, Git, CI/CD and reporting systems |

---

## 4. Core Domain Objects

```text
Document
DocumentVersion
EvidenceAnchor
Requirement
ChangeItem
Release
System
Component
TestPlan
RegressionPack
AutomationFeature
DecisionRecord
Assumption
OpenQuestion
Capability
StepDefinition
PromptTemplate
WorkflowTemplate
WorkflowInstance
Scenario
StepExecution
MakerResult
CheckerReport
HumanReview
ApprovedArtifact
AuditRecord
```

---

## 5. Step Type Classification

To avoid semantic confusion, each Step must have a type.

| Step Type | Example |
|---|---|
| Fact Step | Function Spec v1.3 has status signed_off |
| Deterministic Step | Validate document metadata |
| LLM Skill Step | Generate change list |
| Checker Step | Verify evidence completeness |
| Human Review Step | BA reviews ambiguity |
| Approval Step | QA Lead approves test impact |
| Artifact Step | Produce automation backlog |
| External Tool Step | Create JIRA draft ticket |

---

## 6. Capability Definition Example

```yaml
capability_id: generate_spec_change_list
name: Generate Function Spec Change List
type: llm_assisted_analysis
risk_level: medium

inputs:
  old_spec:
    type: document_version
    required: true
  new_spec:
    type: document_version
    required: true

outputs:
  change_list:
    type: structured_table
  ambiguity_list:
    type: structured_table
  evidence_map:
    type: citation_map

maker:
  prompt_template: prompts/maker/generate_spec_change_list.md
  output_schema: schemas/change_list.schema.json

checker:
  checks:
    - schema_validation
    - evidence_required
    - version_consistency
    - missing_section_check
    - hallucination_check
  prompt_template: prompts/checker/verify_spec_change_list.md

human_review:
  required: true
  reviewer_role: BA
  approver_role: BA Lead

acceptance_criteria:
  - every change item must have source evidence
  - wording-only changes must be separated from semantic changes
  - assumptions must be marked
  - unresolved ambiguity must be listed
```

---

## 7. State Model

Each Step Execution should have a lifecycle:

```text
Not Started
Ready
Maker Running
Maker Completed
Checker Running
Checker Passed
Checker Failed
Human Review Pending
Approved
Rejected
Rework Required
Frozen
Superseded
```

Each Artifact should have a lifecycle:

```text
Draft
Candidate
Checked
Review Pending
Approved
Rejected
Superseded
Archived
```

---

# 05 Integration Roadmap

## Title

**Integration Roadmap: From MVP to Enterprise Engineering Knowledge Workflow**

---

## Phase 1: MVP — Local Evidence-backed Workflow

### Goal

Prove the core value using controlled documents and limited workflow.

### Scope

```text
- Manual document upload
- Document metadata
- Version comparison
- Change list
- Test impact
- Automation backlog draft
- Maker/checker
- Human approval
```

### Main Users

```text
BA
QA Lead
Automation Lead
Platform Admin
```

### Systems Involved

```text
Platform standalone
Manual document upload
Optional local feature index
```

---

## Phase 2: Workflow Expansion

### Goal

Expand from one workflow to reusable delivery workflow templates.

### New Capabilities

```text
- Workflow templates
- Project workflow instances
- Role-based dashboards
- Decision records
- Assumption and open question tracking
- Evidence level classification
- Artifact lifecycle
```

### Example Workflow Templates

```text
Spec Change to Test Impact
Release Readiness Review
Environment Readiness Review
Regression Readiness Review
Go/No-Go Preparation
Automation Backlog Planning
```

---

## Phase 3: Document System Integration

### Goal

Stop relying only on manual uploads. Connect to existing document sources.

### Integration Targets

```text
SharePoint
Confluence
Teams / M365 document storage
Git markdown docs
Network shared folders
```

### Capabilities

```text
- Document reference instead of duplication
- Version sync
- Metadata sync
- Document status sync
- Evidence anchor generation
- Change detection
```

### Key Principle

The platform should not replace SharePoint or Confluence.

It should treat them as document evidence sources.

---

## Phase 4: Test Management Integration

### Goal

Connect requirement changes with test design and execution assets.

### Integration Targets

```text
Zephyr
Existing Cucumber feature repository
Regression pack index
Manual test case repository
```

### Capabilities

```text
- Map requirement change to test cases
- Identify missing test coverage
- Suggest test case update candidates
- Link approved impact assessment to Zephyr
- Write back references to test cases
- Generate candidate test update tasks
```

### Important Boundary

The platform should not automatically rewrite official test cases in MVP.

It should generate candidate updates for human review.

---

## Phase 5: JIRA Integration

### Goal

Connect approved analysis outputs to delivery tracking.

### Integration Targets

```text
JIRA Epic
JIRA Story
JIRA Task
JIRA Bug
JIRA Risk / Action item
```

### Capabilities

```text
- Create draft JIRA tasks from approved backlog
- Link change items to JIRA stories
- Link open questions to BA clarification tickets
- Link automation backlog to implementation tasks
- Track status back into workflow dashboard
```

### Example

```text
Approved automation impact item
  ↓
Create JIRA draft task
  ↓
Automation Lead reviews
  ↓
Task assigned to sprint
  ↓
JIRA status syncs back to workflow
```

---

## Phase 6: Code Repository Integration

### Goal

Connect requirement and test impact to actual engineering assets.

### Integration Targets

```text
Git repository
Cucumber feature files
Automation framework code
Test data repository
Configuration repository
```

### Capabilities

```text
- Index existing feature files
- Map requirements to feature/scenario tags
- Detect impacted automation areas
- Identify missing feature coverage
- Suggest candidate feature updates
- Link approved backlog to repo changes
- Track PRs against approved automation tasks
```

### Future Extension

```text
Approved backlog item
  ↓
Generate implementation guidance
  ↓
Create branch or PR draft
  ↓
Developer / Automation Engineer reviews
  ↓
CI validates
  ↓
Merge status syncs back
```

Important boundary:

```text
LLM may generate draft code or draft feature updates,
but repo changes require engineer review and normal PR process.
```

---

## Phase 7: CI/CD and Execution Platform Integration

### Goal

Close the loop from requirement impact to test execution evidence.

### Integration Targets

```text
Bamboo
Jenkins
GitHub Actions
GitLab CI
Allure reports
JUnit reports
Custom execution dashboard
```

### Capabilities

```text
- Link approved test impact to CI execution plan
- Trigger selected regression pack
- Track execution result
- Link failed tests to change items
- Link report URL to release readiness workflow
- Feed execution evidence back into knowledge workflow
```

### Example Flow

```text
Approved regression impact
  ↓
Generate execution plan
  ↓
CI/CD executes selected pack
  ↓
Allure / JUnit report collected
  ↓
Result linked to change items
  ↓
QA Lead reviews readiness
```

---

## Phase 8: Enterprise Engineering Intelligence

### Goal

Build full traceability across the delivery lifecycle.

### End-to-end Traceability

```text
Requirement
  ↓
Function Spec Change
  ↓
Test Plan Impact
  ↓
Regression Feature
  ↓
Automation Code
  ↓
JIRA Task
  ↓
Pull Request
  ↓
CI/CD Execution
  ↓
Test Report
  ↓
Defect
  ↓
Release Readiness Decision
```

This is the long-term strategic value.

The platform becomes a controlled engineering knowledge layer across delivery systems.

---

# 06 Example Workflow Pack

## Example Feature

```gherkin
@hkex_risk @hkex_tcoe @OTC @release_0_8_patch_2
Feature: OTC Release 0.8 Patch 2 Engineering Knowledge Contract

  Background:
    Given System "OTC" is selected
    And Release "0.8 Patch 2" targets production date "Oct.2026"
    And Function Spec "v1.3" has status "signed_off"
    And Function Spec "v1.3" supersedes Function Spec "v1.1"
    And Test Plan "v2.6" is the approved testing baseline
    And Regression Pack "OTC-Full" is available

  @BA
  Scenario: BA confirms requirement baseline
    When Maker generates change list from Function Spec "v1.1" to "v1.3"
    And Checker verifies the change list against source documents
    Then BA should review unresolved ambiguities
    And BA should approve requirement interpretation

  @QA
  Scenario: QA Lead confirms test impact
    Given BA has approved requirement change list
    When Maker maps changed requirements to Test Plan "v2.6"
    And Checker verifies requirement-to-test evidence
    Then QA Lead should approve test impact assessment
    And QA Lead should identify missing test coverage

  @Auto
  Scenario: Automation Lead confirms automation impact
    Given QA Lead has approved test impact assessment
    When Maker maps changed requirements to Regression Pack "OTC-Full"
    And Checker verifies coverage mapping against automation feature index
    Then Automation Lead should approve regression impact assessment
    And Automation Lead should produce automation backlog draft

  @PM
  Scenario: PM reviews release readiness evidence
    Given BA has approved requirement interpretation
    And QA Lead has approved test impact assessment
    And Automation Lead has approved automation impact assessment
    When Maker summarizes release readiness risks
    And Checker verifies all risks have owners and evidence
    Then PM should review unresolved dependencies
    And PM should approve release readiness summary
```

---

## Example Step Definition

```yaml
step_id: map_changed_requirements_to_regression_pack
gherkin_pattern: Maker maps changed requirements to Regression Pack "{regression_pack}"

step_type: llm_skill
capability_id: map_requirement_to_regression

inputs:
  approved_change_list:
    type: approved_artifact
    required: true
  regression_pack:
    type: regression_pack_index
    required: true

outputs:
  regression_impact_list:
    type: structured_table
  missing_coverage_list:
    type: structured_table
  evidence_map:
    type: citation_map

maker:
  prompt_template: prompts/maker/map_requirement_to_regression.md
  output_schema: schemas/regression_impact.schema.json

checker:
  deterministic_checks:
    - output_schema_valid
    - every_item_has_change_reference
    - every_impacted_feature_exists_in_index
  llm_checks:
    - semantic_mapping_reasonable
    - possible_missing_coverage
    - unsupported_assumption_detection

human_review:
  required: true
  reviewer_role: Automation Lead

approval:
  required: true
  approver_role: Automation Lead

audit:
  record_input_artifacts: true
  record_prompt_version: true
  record_model_version: true
  record_checker_report: true
  record_human_decision: true
```

---

## Example Output: Change List

| Change ID | Requirement / Area | Change Type | Evidence | Impact | Status |
|---|---|---|---|---|---|
| C-001 | Margin Calculation | Semantic Change | FSD v1.3 Section 4.2 | Test Plan update required | BA Review |
| C-002 | CICE Compatibility | Version Scope Change | FSD v1.3 Section 7.1 | Regression impact | QA Review |
| C-003 | Reporting Field | Wording Change | FSD v1.3 Section 9.4 | Low impact | Checker Passed |

---

## Example Checker Report

```yaml
checker_report:
  status: passed_with_warnings
  findings:
    - id: CK-001
      type: missing_evidence
      severity: medium
      description: CICE compatibility impact is inferred but not directly stated.
      required_action: BA or QA Lead should confirm.
    - id: CK-002
      type: ambiguity
      severity: high
      description: The phrase "existing clients" is not clearly defined.
      required_action: BA clarification required.
```

---

## Example Human Review Record

```yaml
human_review:
  artifact: change_list_v0.1
  reviewer: BA
  decision: approved_with_clarification
  approved_items:
    - C-001
    - C-003
  clarification_required:
    - C-002
  comments: CICE impact needs confirmation from system owner.
  review_date: 2026-04-24
```

---

# 07 Risk Control Matrix

| Risk | Description | Control |
|---|---|---|
| LLM hallucination | LLM generates unsupported content | Evidence required for each output item |
| Wrong requirement interpretation | LLM misunderstands business rule | BA approval mandatory |
| Version confusion | Old and new document versions mixed | Document version resolver and metadata validation |
| Weak checker | Checker only repeats maker logic | Use deterministic checks plus LLM checker plus human review |
| Knowledge pollution | Draft output becomes trusted knowledge | Candidate artifact cannot enter knowledge index without approval |
| Prompt sprawl | Users create uncontrolled prompts | Use governed capability registry |
| Workflow overload | Feature file becomes too complex | Feature only stores workflow contract, not full knowledge |
| User adoption failure | PM / BA do not want to write Gherkin | Provide form view, table view and generated Feature view |
| Tool overlap | Platform seen as replacing JIRA/Confluence/Zephyr | Position as orchestration layer, not replacement |
| Audit failure | Cannot reproduce LLM output | Store input docs, prompt version, model version, output, checker report and approval |
| Over-automation | LLM makes decisions | Human role remains final accountable approver |
| Stale knowledge | Old documents still influence decisions | Lifecycle: active, superseded, deprecated, archived |

---

# Recommendation Path

## Phase 0：Concept Alignment

### Goal

Align group CTO, SVP, and platform development team on the direction of the project.

### Deliverables

```text
Executive One-Pager
Concept Paper
Example Feature
MVP Scope
Risk Control Matrix
```

### Decision Points

```text
Is a small scope MVP approved?
Which system / release is the pilot?
Which roles are involved?
```

---

## Phase 1：MVP

### Goal

Verify core loop:

```text
Spec Change → Test Impact → Automation Backlog
```

### Capabilities

```text
Document metadata
Document readiness check
Version diff
Change list generation
Maker/checker
Human approval
Artifact storage
```

### Success Criteria

```text
Each change item has evidence
BA can review requirement interpretation
QA can review test impact
Automation Lead can review automation impact
Output can be converted to backlog draft
```

---

## Phase 2：Workflow Template Conversion

### Goal

Turn one-time MVP into reusable workflow.

### Capabilities

```text
Workflow Template
Workflow Instance
Role-based Scenario
Decision Record
Assumption / Open Question
Evidence Level
Artifact Lifecycle
```

### Example Workflow Template  

```text
Spec Change Impact
Release Readiness
Environment Readiness
Regression Readiness
Go/No-Go Review
```

---

## Phase 3：Document Source Integration

### Goal

Connect existing document systems.

### Integration Objects

```text
SharePoint
Confluence
M365 document storage
Git markdown docs
Network folder
```

### Capabilities

```text
Document reference
Version sync
Metadata sync
Evidence anchor
Change detection
```

---

## Phase 4：JIRA / Zephyr Integration

### Goal

Connect approved analysis results to actual delivery management and test management.

### JIRA Capabilities

```text
Create draft task
Link change item to story
Link ambiguity to clarification task
Sync task status
```

### Zephyr Capabilities

```text
Map requirements to test cases
Identify missing coverage
Attach approved impact assessment
Suggest candidate test case updates
```

---

## Phase 5：Repo / Coding Platform Integration

### Goal

Connect automation assets and code assets.

### Integration Objects

```text
Git repository
Cucumber feature files
Automation framework code
Test data
Config files
Pull request workflow
```

### Capabilities

```text
Index feature files
Map requirement to scenario
Detect impacted automation area
Generate draft implementation guidance
Link JIRA task to PR
Track PR status
```

---

## Phase 6：CI/CD / Execution Platform Integration 

### Goal

Create a loop from requirement change to execution evidence.

### Integration Objects

```text
Bamboo
Jenkins
GitHub Actions
Allure
JUnit report
Custom execution dashboard
```

### Capabilities

```text
Generate execution plan
Trigger selected regression
Collect test result
Link result to requirement change
Feed execution evidence into release readiness
```

---

## Phase 7：Enterprise Engineering Intelligence

### Goal

Build cross-system engineering knowledge loop.

### Final Loop

```text
Requirement
  → Spec Change
  → Test Plan Impact
  → Regression Feature
  → Automation Code
  → JIRA Task
  → Pull Request
  → CI/CD Execution
  → Test Report
  → Defect
  → Release Readiness Decision
```

---

# CTO / SVP

> The issue today is not lack of documentation, but the lack of structural relationships between documents, requirements, tests, automation, defects, execution results, and release decisions.  
>   
> We recommend starting with a small-scale MVP to establish an evidence-based delivery knowledge workflow. Documentation serves as evidence, BDD-style workflow as cross-role collaboration contract, LLMs only as maker/checker assistive tools, with human roles retaining final judgment and approval authority.  
>   
> Phase 1 only validates the closed loop from Spec Change to Test Impact. Then we incrementally connect SharePoint/Confluence, JIRA, Zephyr, Git Repos, CI/CD, and test reports, ultimately forming a traceable engineering knowledge link from requirement to release readiness.

---

# Platform Engineering Team

> This platform is not about rebuilding Confluence, JIRA, Zephyr, or CI/CD—it's about establishing an engineering knowledge orchestration layer on top of these existing systems.  
>   
> Phase 1 scope is limited to: controlled document ingestion, version diffing, capability registry, maker/checker execution, human review, and an artifact repository.  
>   
> BDD Feature is not a knowledge database, it's a workflow contract. Step is not a prompt, it's a governed skill invocation. Prompts are merely implementation details of skills. All LLM outputs must pass checker review and human approval before entering the approved artifact set or knowledge index.

---

# Final Statement

> **This platform turns fragmented delivery evidence into executable engineering knowledge workflows, where governed agent skills assist analysis, maker/checker controls quality, and human roles retain final accountability.**
