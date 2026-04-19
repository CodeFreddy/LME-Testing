# LME Testing — Revised Acceptance Criteria

**版本：** 2.0  
**修订日期：** 2026-04-18  
**修订说明：** 在原有 gate 基础上新增 `Verification Type` 字段，区分三种完成状态。

---

## 验证类型定义

| 类型 | 含义 |
|------|------|
| `code_implementation` | 代码写出来了，逻辑上正确 |
| `stub_verified` | 用 StubProvider 或 POC（≤2条规则）验证通过 |
| `real_data_verified` | 用真实 LLM API 和真实规模数据验证通过 |

**原则：** 只有 `real_data_verified` 才代表功能在生产可信场景下得到验证。`stub_verified` 是必要的但不充分。

---

## 通用验收规则

1. **无证据不完成** — gate 未有明确 Evidence 不得标记完成
2. **契约变更需协调更新** — artifact 格式变更必须同时更新 schema + test + docs + acceptance
3. **模型/prompt 变更需 regression** — 新模型或 prompt 版本必须有 benchmark 证据
4. **不得跨 Phase** — 不得将后阶段工作标记为当前 Phase 完成
5. **结构化输出保持结构化** — 现有 JSON 输出模块不得改为自由文本
6. **新增：governance signal 必须标注数据来源** — `real_api` / `stub` / `no_data`

---

## Phase 1 — Baseline Control and Pipeline Hardening

**完成日期：** 2026-04-13（代码实现）  
**待补完成：** Checker Stability Gate（S1-T03b）

### Gate 1：Artifact Schema Gate

**Verification Type：** `real_data_verified`

Evidence：
- 7 套 schema 文件已提交
- CI schema-validation job 通过
- valid/invalid fixtures 均按预期通过/失败

**状态：** ✅ COMPLETE

---

### Gate 2：Upstream Validation Pipeline Gate

**Verification Type：** `real_data_verified`

Evidence：
- `validate_rules.py` 验证 atomic + semantic rules
- CI upstream-validation job 通过
- 183 条 LME 规则通过验证

**状态：** ✅ COMPLETE

---

### Gate 3：Baseline CI Gate

**Verification Type：** `stub_verified`（smoke test 基于 stub + poc_two_rules）

Evidence：
- 6 个 CI job 在 push/PR 时自动运行
- smoke_test.py 使用 StubProvider 无 API 费用运行

**状态：** ✅ COMPLETE（stub 验证）

**注：** 全量规则集的 smoke 路径未验证，但这超出 CI smoke 的设计范围。

---

### Gate 4：Model and Prompt Metadata Gate

**Verification Type：** `stub_verified`

Evidence：
- maker/checker artifact 包含 provider、model、prompt_version、run_timestamp、pipeline_version
- `check_model_governance.py` 验证通过

**状态：** ✅ COMPLETE

---

### Gate 5：Stable Source Anchor Gate

**Verification Type：** `real_data_verified`

Evidence：
- `paragraph_id` 字段添加到 AtomicRule schema
- `paragraph_ids` 添加到 semantic_rule source 小节
- 183 条 LME 规则已更新 `paragraph_id`
- 唯一性验证在 `validate_rules.py` 中实现

**状态：** ✅ COMPLETE

---

### Gate 6：Checker Stability Gate

**Verification Type：** `real_data_verified`

Evidence（2026-04-18）：
- `scripts/checker_stability.py` 真实 API 双次运行完成
- stability_report: `runs/stability_real/stability_report.json`
- `data_source: "real_api"` ✅
- `total_cases: 0` ⚠️（所有 case 因 schema 验证失败被拒绝）
  - 原因：maker 输出 `case_type: "happy_path"`（不在 checker CASE_TYPES enum）
  - 原因：MiniMax checker 部分响应缺少 `semantic_rule_id` 字段
- `instability_rate: 0.0`（0 valid cases，无法计算有意义的 instability）

**状态：** ⚠️ PARTIALLY COMPLETE — 真实 API 运行完成，但数据质量问题导致 0 valid cases

---

### Gate 7：Documentation Gate

**Verification Type：** `real_data_verified`

Evidence：
- roadmap.md, implementation_plan.md, acceptance.md, architecture.md, model_governance.md, agent_guidelines.md 均已提交
- 本次修订为 v2.0，更新为诚实的状态描述

**状态：** ✅ COMPLETE（已更新至 v2.0）

---

### Phase 1 Exit Criteria

| 条件 | 状态 |
|------|------|
| 核心规则 artifact 在 CI 中 schema 验证 | ✅ |
| 无效 rule_type 硬失败 | ✅ |
| 结构化验证报告可产出并阻止下游执行 | ✅ |
| 可复现的 minimal smoke 存在于 CI | ✅（stub）|
| smoke 路径无真实 LLM API 调用 | ✅ |
| maker/checker artifact 记录模型和 prompt metadata | ✅ |
| checker instability 可在 baseline set 上显示 | ⚠️ 代码存在，真实数据待 S1-T03b |
| stable source anchor 存在于 governed upstream artifact | ✅ |
| 治理文档在 repo 中存在 | ✅ |

**Phase 1 完成度：** ✅ 代码层面完成 / ⚠️ Checker Stability 待真实数据验证

---

## Stage 1 — 真实数据接入（当前阶段）

### Gate S1.1：Schema Signal 数据来源修复

**Verification Type：** `real_data_verified`

**验收标准：**
- `validate_schemas.py --output-json` 产出合法 JSON
- CI 写入 `runs/schema_validation_latest.json`
- `governance_signals.json` 中 `schema_signal_source: "real_validation"`
- 故意引入 invalid fixture 时 `schema_failure_rate > 0`

**Evidence（2026-04-19）：**
- `runs/schema_validation_latest.json` 存在，370 fixtures validated，0 failures
- `compute_governance_signals()` → `schema_signal_source: "real_validation"`
- `test_schema_failure_rate_detects_invalid_fixtures` 测试通过：写入 1 invalid/10 total → `failure_rate = 0.1 > 0`
- `validate_schemas.py --output-json runs/schema_validation_latest.json` 可正常执行

**状态：** ✅ COMPLETE

---

### Gate S1.2：Governance 路径对齐

**Verification Type：** `real_data_verified`

**验收标准：**
- `docs/run_directory_structure.md` 存在
- `governance_signals.json` 中 `runs_analyzed > 0`
- `coverage_signals.total_rules ≥ 180`

**Evidence（2026-04-19）：**
- `docs/run_directory_structure.md` 存在并描述完整 run 类型结构
- `compute_governance_signals()` → `runs_analyzed = 21 > 0`
- `coverage_signals.total_rules = 180 ≥ 180`
- `coverage_signals.latest_coverage_percent = 72.78%`
- 当前 `runs/` 包含 maker_v1.1_full、baseline_full 等全量运行

**状态：** ✅ COMPLETE

---

### Gate S1.3：Checker 真实稳定性

**Verification Type 目标：** `real_data_verified`

**验收标准：**
- `stability_report.json` 包含 `data_source: "real_api"`
- `docs/acceptance.md` Gate 6 更新为真实数字
- 若 instability > 5%：`model_governance.md` 有分析记录

**当前 instability_rate：** TBD（待 S1-T03b）

**状态：** ❌ NOT STARTED

---

### Gate S1.4：全量规则质量基准

**Verification Type 目标：** `real_data_verified`

**验收标准：**
- `coverage_report.json` 包含 ≥ 180 条规则
- `docs/releases/BASELINE-183-RULES.md` 存在（含人工抽查记录）
- coverage 数字如实记录（不掩盖低覆盖率）

**当前 coverage（全量）：** TBD

**状态：** ❌ NOT STARTED

---

### Gate S1.5：状态声明诚实性

**Verification Type：** `real_data_verified`

**验收标准：**
- README 无 "All Phases Complete" 表述
- 所有 "100%" 声明注明数据基础
- acceptance.md 每个 gate 有 Verification Type

**Evidence（2026-04-19）：**
- README.md Verification Status 表格已更新：S1.1 ✅ Complete, S1.2 ✅ Complete
- README.md 无 "All Phases Complete" 表述
- acceptance.md 每个 gate（含 Stage 1 S1.1/S1.2）有 Verification Type

**状态：** ✅ COMPLETE

---

## Phase 2 — Planned Test Design and Normalized BDD

**完成日期：** 2026-04-13（代码实现）  
**注意：** 所有 gate 基于 poc_two_rules（2条规则）验证，全量质量待 Stage 1 建立基准后评估。

### Gate 2.1：Multi-Document Ingestion

**Verification Type：** `stub_verified`

Evidence：
- `scripts/document_classes.py`：DocumentClass enum, 4 种 parsing strategy
- poc_two_rules 端到端通过

**已知限制：**
- 实现为 enum + keyword matching，不是结构感知的文档解析框架
- 复杂布局 PDF 提取质量未验证

**状态：** ✅ COMPLETE（stub 验证）/ ⚠️ 复杂文档质量未知

---

### Gate 2.2：Planning Layer

**Verification Type：** `stub_verified`

Evidence：
- `schemas/planner_output.schema.json` 存在
- `run_planner_pipeline` 实现
- poc_two_rules planner 运行验证通过

**状态：** ✅ COMPLETE（stub 验证）

---

### Gate 2.3：Normalized BDD Contract

**Verification Type：** `stub_verified`

Evidence：
- `schemas/normalized_bdd.schema.json` 存在
- `run_bdd_pipeline` 实现
- BDD export 产出 .feature 文件
- poc_two_rules 验证通过

**状态：** ✅ COMPLETE（stub 验证）

---

### Gate 2.4：Traceability

**Verification Type：** `stub_verified`

Evidence：
- paragraph_ids 贯穿 planner → maker → BDD 流水线
- HTML report 可点击 rule ID 跳转

**状态：** ✅ COMPLETE（stub 验证）

---

### Gate 2.5：Step Visibility

**Verification Type：** `stub_verified`

Evidence：
- `lme_testing/step_registry.py` 实现 3-tier matching
- poc_two_rules step visibility 报告生成

**已知限制：**
- step library 基于模拟 LME API，step binding rate 35.4% 无实际意义
- 真实 binding rate 待 Stage 3 接入真实 API 后测量

**状态：** ✅ COMPLETE（stub 验证）/ ⚠️ 真实 binding rate 未知

---

### Gate 2.6：Quality and Drift Reporting

**Verification Type：** `stub_verified`

Evidence：
- `scripts/generate_trend_report.py` 实现
- HTML report 有 coverage trend、dropdown 过滤器、rule ID 跳转

**状态：** ✅ COMPLETE（stub 验证）

---

### Gate 2.7：Model Governance Enforcement

**Verification Type：** `stub_verified`

Evidence：
- `scripts/check_model_governance.py` 实现
- `config/approved_providers.json` 存在

**状态：** ✅ COMPLETE（stub 验证）

---

## Phase 3 — Execution Readiness

**完成日期：** 2026-04-14（代码实现）  
**注意：** 以下 gate 的"完成"均为代码层面，执行层面核心价值（真实 LME API 接入）待 Stage 3。

### Gate 3.1：Step Definition Integration

**Verification Type：** `stub_verified`（⚠️ step library 基于模拟 API）

**状态：** ✅ COMPLETE（stub 验证）/ ⚠️ 真实执行能力待 Stage 3

---

### Gate 3.2：Execution Readiness

**Verification Type：** `code_implementation`（无真实消费者验证）

Evidence：
- `schemas/executable_scenario.schema.json` 存在
- 14 个 schema 测试通过

**已知限制：** 没有任何系统真实消费 ExecutableScenario 产出并执行测试

**状态：** ✅ COMPLETE（code only）/ ⚠️ 无真实执行验证

---

### Gate 3.3：Deterministic Oracle

**Verification Type：** `stub_verified`（⚠️ 未在真实 LME 规则场景验证）

Evidence：
- 8 个 oracle 模块，38 个单元测试通过

**已知限制：** oracle 单元测试使用人工构造的测试数据，未在真实 LME checker 场景中验证

**状态：** ✅ COMPLETE（stub 验证）/ ⚠️ 真实场景验证待 Stage 2

---

### Gate 3.4：Governance Signals

**Verification Type：** `code_implementation`（2/4 信号数据为空或 stub）

Evidence：
- signals 框架实现，4 类信号数据结构
- CI governance-signals job 运行

**当前信号可信度：**

| 信号 | 数据来源 | 可信度 |
|------|---------|--------|
| schema_failure_rate | 无（推断）| ⚠️ 假数据 |
| checker_instability | StubProvider | ⚠️ 不代表真实 LLM |
| coverage_percent | 全量运行（路径未对齐）| 🔄 待对齐 |
| step_binding_rate | 模拟 step lib | ⚠️ 无实际意义 |

**状态：** ✅ COMPLETE（code only）/ ⚠️ 信号数据待 Stage 1 修复

---

### Gate 3.5：Release Governance

**Verification Type：** `stub_verified`

Evidence：
- `config/approved_providers.json`, `config/compatibility_matrix.json`, `config/benchmark_thresholds.json`
- `docs/releases/RELEASES.md`
- `scripts/check_release_governance.py` 通过

**已知限制：** benchmark evidence 基于 stub/poc_two_rules，全量质量基准待 Stage 1

**状态：** ✅ COMPLETE（stub 验证）

---

## 证据模板

每个完成的 roadmap 项应提供：

```
变更摘要：
修改文件：
验证类型：[code_implementation / stub_verified / real_data_verified]
数据来源：[stub / real_api / no_data]（适用于 governance signals）
已测试项：
产生的 artifacts：
已知限制：
回滚影响：
```
