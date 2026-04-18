# LME Testing — TODO

**修订日期：** 2026-04-18  
**说明：** 本文档区分三种完成状态：代码实现完成 / Stub 验证完成 / 真实数据验证完成。历史版本将"代码实现完成"等同于"全部完成"，本文档修正这一问题。

---

## 状态图例

| 标记 | 含义 |
|------|------|
| ✅ Code | 代码实现完成 |
| ✅ Stub | Stub/POC 验证通过（2条规则） |
| ✅ Real | 真实数据验证完成 |
| 🔄 In Progress | 进行中 |
| ⏳ Blocked | 等待外部条件 |
| ❌ Not Started | 未开始 |
| 🧊 Frozen | 暂缓，等待前置条件 |

---

## Stage 1 — 真实数据接入（当前阶段）

### S1-T01：Schema Failure Rate 数据源修复

- [ ] `validate_schemas.py` 新增 `--output-json` 参数
- [ ] CI schema-validation job 写入 `runs/schema_validation_latest.json`
- [ ] `_compute_schema_signals()` 读取真实验证文件
- [ ] `GovernanceSignals.to_dict()` 新增 `schema_signal_source` 字段
- [ ] 验证：故意引入 invalid fixture 时 `schema_failure_rate > 0`

**当前状态：** ❌ Not Started

### S1-T02：全量运行数据路径对齐

- [ ] 手动定位全量 183 条规则的实际运行输出目录
- [ ] 创建 `docs/run_directory_structure.md`
- [ ] 修复 `compute_governance_signals()` 扫描路径
- [ ] 新增 `--runs-dir` 参数到 `governance-signals` 命令
- [ ] 验证：`runs_analyzed > 0`，`total_rules ≈ 183`

**当前状态：** ❌ Not Started

### S1-T03：Session Snapshot 原子写入

- [ ] `storage.py` 新增 `atomic_write_json()` 函数
- [ ] `review_session.py` 所有 snapshot 写入替换为 `atomic_write_json()`
- [ ] `docs/architecture.md` 声明单用户设计约束
- [ ] 验证：快速连续 Save 后 snapshot 文件不损坏

**当前状态：** ❌ Not Started

### S1-T03b：Checker 真实稳定性测量

- [ ] 用真实 MiniMax API 对 poc_two_rules 运行 checker 两次
- [ ] 产出 `runs/stability_real/stability_report.json`（含 `data_source: "real_api"`）
- [ ] 更新 `docs/acceptance.md` Phase 1 Gate 6 Evidence 为真实数字
- [ ] 更新 `governance_signals.json` checker instability 数据源
- [ ] 若 instability > 5%：`docs/model_governance.md` 新增分析记录

**当前状态：** ❌ Not Started

### S1-T04：全量规则集质量基准建立

- [ ] 全量 183 条规则 maker 运行（分批，`--batch-size 8`）
- [ ] 全量 checker 运行
- [ ] 生成 `reports/baseline_full_<date>.html`
- [ ] 人工随机抽查 ≥ 10 条规则，评估 maker 输出质量
- [ ] 创建 `docs/releases/BASELINE-183-RULES.md`（含所有必需章节）
- [ ] `governance_signals.json` 中 `coverage_signals.total_rules ≥ 180`

**当前状态：** ❌ Not Started

### S1-T05：项目状态声明重写

- [ ] `README.md` Project Status 小节用真实数字重写
- [ ] `TODO.md`（本文档）区分代码完成 vs 验证完成
- [ ] `docs/acceptance.md` 每个 gate 新增 `Verification Type` 标注
- [ ] 消除所有没有数据支撑的"100%"和"Complete"声明

**当前状态：** 🔄 In Progress（本文档是 S1-T05 的一部分）

---

## Stage 0 — 框架实现（已完成，存档）

以下为 AI 代理在 2026-04-13/14 完成的代码实现。代码层面完成，验证深度如注。

### Phase 1 实现（✅ Code，✅ Stub，部分 ✅ Real 待确认）

- [x] ✅ Code ✅ Stub　Artifact Schema Gate — 7 套 JSON Schema
- [x] ✅ Code ✅ Stub　Upstream Validation Pipeline Gate — validate_rules.py
- [x] ✅ Code ✅ Stub　Baseline CI Gate — 6 个 CI job
- [x] ✅ Code ✅ Stub　Model and Prompt Metadata Gate — prompt/pipeline 版本记录
- [x] ✅ Code ✅ Stub　Stable Source Anchor Gate — paragraph_id 字段
- [x] ✅ Code ⚠️ Stub-only　Checker Stability Gate — stability_report 基于 stub（S1-T03b 修复）
- [x] ✅ Code ✅ Real　Documentation Gate — 6 套治理文档

### Phase 2 实现（✅ Code，✅ Stub）

- [x] ✅ Code ✅ Stub　Multi-Document Ingestion — DocumentClass enum + keyword matching（**注意：这是简化实现，不是完整文档解析框架**）
- [x] ✅ Code ✅ Stub　Planning Layer — planner_output schema + run_planner_pipeline
- [x] ✅ Code ✅ Stub　Normalized BDD Contract — normalized_bdd.schema.json + BDD pipeline
- [x] ✅ Code ✅ Stub　Traceability Gate — paragraph_ids 贯穿全流水线
- [x] ✅ Code ✅ Stub　Step Visibility Gate — step_registry.py（**注意：step library 基于模拟 API**）
- [x] ✅ Code ✅ Stub　Quality and Drift Reporting Gate — generate_trend_report.py
- [x] ✅ Code ✅ Stub　Model Governance Enforcement Gate — check_model_governance.py

### Phase 3 实现（✅ Code，✅ Stub，**执行层面未验证**）

- [x] ✅ Code ✅ Stub　Step Definition Integration — 3-tier matching（**step lib 基于模拟**）
- [x] ✅ Code ✅ Stub　Execution Readiness — executable_scenario.schema.json（**无真实消费者**）
- [x] ✅ Code ✅ Stub　Deterministic Oracle — 8 个 oracle 模块（**未在真实规则场景验证**）
- [x] ✅ Code ⚠️ Stub-only　Governance Signals — signals 框架（**2/4 信号无真实数据**）
- [x] ✅ Code ✅ Stub　Release Governance — approved_providers.json + compatibility_matrix（**benchmark 证据基于 stub**）

### 近期 Bug 修复（2026-04-17/18，✅ Code）

- [x] ✅ Code　review_session.py：issueOptionMap 孤立语句修复
- [x] ✅ Code　review_session.py：saveScriptsEdits 缺失 `}` 修复
- [x] ✅ Code　step_registry.py：StepEntry match metadata 字段补全
- [x] ✅ Code　step_library.py：`_build_decorated_code()` 函数体缩进修复
- [x] ✅ Code　bdd_export.py：Python step definitions 迁移（从 Ruby）
- [x] ✅ Code　governance-signals CI job 接入
- [x] ✅ Code　report UX：Rule ID 跳转、覆盖率 pill、dropdown 过滤器

---

## Stage 2 — 规模化质量提升（冻结，待 Stage 1 数据）

以下任务在 Stage 1 全部完成后，基于真实数字决定是否执行和如何执行。

- 🧊 Maker prompt 质量提升（触发条件：coverage < 80% 或人工抽查 Poor 率 > 30%）
- 🧊 Checker 稳定性改进（触发条件：instability > 10%）
- 🧊 Oracle 框架实测验证（触发条件：识别出高频确定性规则类型）
- 🧊 全量规则 BDD 生成质量评估
- 🧊 BDD style learning（**永久低优先级：无真实 BDD 样本可学习**）

---

## Stage 3 — 真实执行环境（阻塞于外部依赖）

- ⏳ 获得 LME 内部 VM 访问权限（ETA：未知）
- ⏳ 用真实 LME API 替换 `samples/ruby_cucumber/lib/lme_*.rb`
- ⏳ 重建 `lme_testing/step_library.py`（基于真实 API 模式）
- ⏳ 重新测量 step binding rate（当前 35.4% 基于模拟）
- ⏳ 在真实环境中执行 BDD 场景并验证

---

## 永久搁置（不在任何阶段规划中）

- ❌ BDD style learning（无真实样本，自循环优化无意义）
- ❌ Multi-user hosted review platform（超出工具定位）
- ❌ Autonomous execution without approval gates（违反架构原则）
- ❌ 用 AI 代理快速通过 acceptance gate（本次教训）

---

## Darcy 的个人任务（原 TODO_Darcy.md，更新状态）

- [x] ✅ Code　创建 Ruby Cucumber prototype（`samples/ruby_cucumber/`）
- [x] ✅ Code　BDD tab：显示 normalized BDD，支持 Given/When/Then 编辑
- [x] ✅ Code　Scripts tab：显示 step registry visibility（display 完成）
- [ ] ❌ Scripts tab 完整 edit workflow（save → downstream wiring）→ 降级到 S1-T03 后
- [ ] ⏳ 真实 LME API 接入（Stage 3，依赖 VM 权限）
- [ ] 🧊 TEMPLATE_REGISTRY 补充真实 LME API 模式（Stage 3 前置）
- [ ] 🧊 如何让 prototype 代码动态演进的设计（待架构讨论）
