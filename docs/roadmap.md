# LME Testing — Revised Roadmap

**版本：** 2.0  
**修订日期：** 2026-04-18  
**修订原因：** 原 roadmap 基于理想演进时间线编写，实际情况是 AI 代理在 48 小时内完成了框架实现但跳过了真实规模验证。本文档基于 repo 实际状态重新制定演进路径。

---

## 一、诚实的现状声明

在阅读本 roadmap 之前，需要理解当前 repo 的真实状态：

| 维度 | 实际状态 |
|------|---------|
| 框架代码 | ✅ 完整实现（maker / checker / BDD / oracle / governance signals） |
| Schema 契约 | ✅ 7 套 JSON Schema，CI 验证通过 |
| 小规模 POC | ✅ 2 条规则端到端跑通 |
| **全量规则质量基准** | **🔄 数据存在但 governance 系统无法读取** |
| **Checker 真实稳定性** | **❓ 未知，当前 0% 基于 stub** |
| **Governance signals** | **⚠️ schema failure rate 和 instability 信号数据为空** |
| 真实 LME API 接入 | ⏳ 无访问权限，ETA 未知 |
| 多用户协作 | ❌ 非当前阶段目标 |

**这不是失败，这是一个诚实的原型。** 框架设计是有价值的资产，但"All Phases Complete"的表述已不适用，本文档以此为起点重新规划。

---

## 二、核心原则（与原 roadmap 保持一致）

以下原则经过实践验证，继续沿用：

1. **Governance-contract-first** — LLM 输出必须被 schema、prompt 版本、benchmark 控制
2. **Deterministic before LLM** — 能确定性验证的，不依赖 LLM 判断
3. **Upstream quality first** — 上游规则质量决定下游一切
4. **Artifacts are first-class** — 结构化产物优于自由文本
5. **Human review is a control layer** — 人工审核是架构的一部分，不是可选功能

新增原则（基于本次实践教训）：

6. **Real data before governance claims** — governance 指标必须有真实数据支撑，不接受 stub 数据作为治理证据
7. **Honest capability boundary** — 系统能力边界必须明确声明，不夸大"完成"范围

---

## 三、Phase 重新定义

### 当前实际所处阶段

```
原 roadmap 定义的阶段：Phase 1 → Phase 2 → Phase 3
实际情况：框架代码覆盖 Phase 1-3，但验证深度仅到 Phase 1 POC 水平
```

**本 roadmap 将演进路径重新定义为 4 个阶段：**

```
Stage 0（当前）：框架已建，地基待验
Stage 1（接下来）：真实数据接入，建立可信基准
Stage 2（中期）：规模化质量提升
Stage 3（长期，有外部依赖）：真实执行环境接入
```

---

## Stage 0 — 框架实现完成（已完成，存档）

**时间：** 2026-04-13 至 2026-04-14（AI 代理实现）  
**状态：** ✅ 代码层面完成

**已实现的内容（代码存在）：**
- 完整 maker → checker → review → report 流水线
- BDD 规范化生成（normalized BDD schema）
- Planner 阶段（semantic rules → test objectives）
- Step registry（步骤定义可见性）
- 8 个 deterministic oracle 模块
- Governance signals 框架（4 类信号）
- Web review UI（localhost:8765）
- CI 流水线（6 个 job）
- 6 套治理文档

**存在的已知问题（不再掩盖）：**
- governance signals 中 2/4 信号无真实数据
- checker stability 基于 stub 测量，不代表真实 LLM 行为
- step library 基于模拟 API，不对应真实 LME 系统
- session snapshot 无并发保护
- 全量 183 条规则运行数据未对齐到 governance 系统

---

## Stage 1 — 真实数据接入与可信基准建立

**时间预估：** 2-4 周  
**目标：** 让 governance 系统消费真实数据，建立第一个可信的质量基准

**不在 Stage 1 范围内：**
- 新功能开发
- 多用户协作
- 真实 LME API 接入
- Oracle 框架扩展

### Gate 1.1 — Governance 数据源修复

**目标：** schema failure rate 和 checker instability 信号有真实数据支撑

交付物：
- `validate_schemas.py --output-json` 参数，产出持久化验证结果
- `_compute_schema_signals()` 读取真实验证结果而非推断
- CI schema-validation job 写入 `runs/schema_validation_latest.json`

验收：故意引入 invalid fixture 时 `schema_failure_rate > 0`

### Gate 1.2 — 全量运行数据路径对齐

**目标：** 全量 183 条规则的已有运行结果可被 governance 读取

交付物：
- `docs/run_directory_structure.md`：标准运行输出路径文档
- `compute_governance_signals()` 扫描逻辑与实际输出路径对齐
- `governance_signals.json` 中 `coverage_signals.total_rules ≈ 183`

验收：`runs_analyzed > 0`，`total_rules` 接近 183

### Gate 1.3 — Checker 真实稳定性测量

**目标：** 用真实 MiniMax API 测量 checker 在同一批 case 上的重复一致性

交付物：
- 真实双次 checker 运行（poc_two_rules baseline）
- `stability_report.json` 包含真实 instability_rate
- `docs/acceptance.md` Phase 1 Gate 6 的 Evidence 更新为真实数字
- 若 instability > 5%：`docs/model_governance.md` 新增实测记录和分析

验收：stability_report 被 governance signals 系统正确读取

### Gate 1.4 — 全量规则集质量基准

**目标：** 建立第一个有文档记录的全量基准运行

交付物：
- `runs/baseline_full/` 下的完整 maker + checker 输出
- `reports/baseline_full.html` 可视化报告
- `docs/releases/BASELINE-183-RULES.md`：基准运行记录，包含 coverage %、人工抽查结论、已知低质量规则类型

验收：
- `coverage_report.json` 包含 183 条规则状态
- 人工随机抽查 ≥ 10 条规则，质量评估记录在案
- coverage < 80% 时，失败模式分类记录（不掩盖）

### Gate 1.5 — 项目状态声明重写

**目标：** 消除误导性"All Phases Complete"声明

交付物：
- `README.md` Project Status 小节反映真实状态
- `TODO.md` 区分"代码实现完成"vs"真实验证完成"
- `docs/acceptance.md` 每个 gate 标注验证类型

**Stage 1 Exit：** 所有 Gate 1.1-1.5 完成，governance signals 有真实数据支撑

---

## Stage 2 — 规模化质量提升

**前置条件：** Stage 1 全部完成  
**时间预估：** 4-8 周（取决于 Stage 1 发现的问题数量）  
**目标：** 基于真实质量数字，有针对性地提升系统能力

**此阶段的工作内容取决于 Stage 1 的发现。** 本 roadmap 只定义框架，具体任务在 Stage 1 完成后更新。

### 可能的方向（待 Stage 1 数据确认后选择）

**方向 A：Prompt 质量提升**（如果 maker 生成质量低）
- 基于失败模式分析改进 MAKER_SYSTEM_PROMPT
- 遵循 `docs/model_governance.md` 的 prompt 变更流程
- 需要 benchmark 证据支撑 prompt 变更

**方向 B：Checker 稳定性改进**（如果 instability > 10%）
- 分析不稳定的 case 类型
- 改进 CHECKER_SYSTEM_PROMPT 的判断一致性
- 考虑对高频不稳定规则类型引入更多 deterministic oracle 替代

**方向 C：Oracle 框架实测**（如果某些规则类型适合确定性验证）
- 选择 2-3 个 oracle 在真实规则场景上运行
- 测量 oracle 与 LLM checker 判断的一致性
- 决定是否扩展 oracle 覆盖范围

**不在 Stage 2 范围内（无论 Stage 1 结果如何）：**
- BDD style learning（无真实样本）
- Multi-user portal
- 真实 LME API 接入（外部依赖）

---

## Stage 3 — 真实执行环境接入

**前置条件：** Stage 2 完成 + 获得 LME 内部 VM 访问权限  
**时间预估：** 未知（取决于外部依赖）  
**目标：** 将 step definitions 从模拟实现替换为真实 LME API 调用

**此阶段完全依赖外部条件（LME VM 访问权限），在条件具备前不制定详细计划。**

需要完成的核心工作：
- 用真实 LME API 替换 `samples/ruby_cucumber/lib/lme_*.rb` 中的模拟实现
- 重建 `lme_testing/step_library.py` 基于真实 API 模式
- 重新测量 step binding rate（目前 35.4% 基于模拟）
- 在真实环境中执行至少部分 BDD 场景并验证结果

**Stage 3 的"执行就绪"才是 Phase 3 Gate 2 真正意义上的完成。**

---

## 四、永久冻结项（不在任何阶段规划中）

| 项目 | 冻结原因 |
|------|---------|
| BDD style learning | 无真实 BDD 样本可学习，自循环优化无意义 |
| Multi-user hosted review platform | 超出当前工具定位，单用户路径本身未完全稳定 |
| Autonomous end-to-end execution without approval gates | 与架构原则"human review is a control layer"冲突 |
| 用 AI 代理快速通过 acceptance gate | 本次教训，不重复 |

---

## 五、当前能力边界声明（诚实版）

### 当前可以做的
- 从格式规整的 PDF/TXT 提取规则并生成 atomic/semantic rules
- 用 LLM maker 为 semantic rules 生成 BDD 测试场景
- 用 LLM checker 评估场景质量（稳定性待测量）
- 生成 HTML 可视化审核报告
- 本地 Web UI 进行人工审核、BDD 编辑、重写触发
- 通过 JSON Schema 验证 artifact 契约
- 用 StubProvider 进行无 API 费用的 CI 回归测试

### 有条件可以做的
- 全量 183 条规则的 maker/checker 运行（已有代码，质量待验证）
- 确定性 oracle 验证（8 个 oracle 存在，真实场景验证待完成）
- Governance signals 监控（框架存在，数据源修复后可用）

### 当前不能做的
- 在真实 LME 生产环境中执行测试
- 多用户并发审核
- 自动执行生成的测试场景
- 在复杂布局 PDF 上可靠提取规则

---

## 六、AI 代理操作规则（基于本次经验更新）

在原 `AGENTS.md` 基础上新增：

1. **不得以"acceptance gate 脚本通过"代替"功能在真实数据上验证"**
2. **不得将 stub 运行的 governance signal 作为真实质量证据**
3. **不得在 acceptance.md 中标注 gate 完成，除非有真实数据支撑的 Evidence**
4. **所有 governance signal 必须标注数据来源：`stub` / `real_api` / `no_data`**
5. **roadmap phase 完成声明需要人工确认，不由 AI 代理自行宣告**
