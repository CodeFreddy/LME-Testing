深度对照分析如下。

---

## 1. 新 Roadmap 的核心方法论

### 它的方法论本质：治理契约优先（Governance-Contract-First）

上传的 roadmap 不是功能交付计划，而是一份**执行合约**。它的核心假设是：在一个多 LLM 参与的 repo 里，最大的风险不是"功能做得不够多"，而是"输出不可控、变更不可回滚、Agent 越权修改了结构"。

它的方法论支柱是三条原则，而这三条在现有方案里都是隐含的、未正式化的：

**原则一：LLM 输出必须被治理，不能被信任。** 所有 LLM 产物都要走 schema 验证、prompt 版本记录、artifact hash 追踪。这不是可选项，是 pipeline 的硬门槛。

**原则二：确定性职责与 LLM 辅助职责必须分离。** 这是最有价值的架构洞察，现有方案完全没有明确处理：字段校验、枚举值校验、覆盖率计算、重复检测、执行断言——这些必须由确定性模块拥有，LLM 不能介入。LLM 负责生成建议，代码负责验证结论。

**原则三：Repo 本身就是 Agent 的执行上下文。** 文档、schema、acceptance criteria、benchmark 集合必须足够清晰，让一个 AI coding agent 能从 repo 里读懂任务，而不依赖 chat 状态。

### 它比现有方案更强调什么

| 维度 | 现有方案（UPGRADE_ROADMAP.md） | 上传方案（roadmap.md） |
|------|-------------------------------|----------------------|
| 核心导向 | 功能里程碑交付 | 治理契约建立 |
| LLM 角色边界 | 隐含（靠 schema.py） | 显式架构原则 |
| Agent 贡献规则 | 无 | 有，5条强制规则 |
| Prompt 治理 | 版本化文件 | 版本+owner+changelog+benchmark绑定 |
| 模型兼容性政策 | 无 | 新模型必须过benchmark才能采纳 |
| Checker 稳定性 | 无 | 同基准集跑两次，检测不一致 |
| 上游质量门控 | 里程碑之一 | 整个方案的第一优先级 |
| 回滚政策 | 无 | 明确：模型/prompt变更必须可逆 |

### 它默认了哪些前提

1. **AI coding agent 会修改这个 repo**——它专门写了 agent 贡献规则，这是写给 Cursor/Claude Code/Copilot 的，不是写给人看的。
2. **会换 LLM**——整个模型治理层的存在前提是 provider 会变。
3. **上游提取是当前最大的质量瓶颈**——它把 atomic_rule/semantic_rule 的验证放在 Phase 1 最前面，假设现有提取质量不够稳定。
4. **BDD 应该有中间态表示**——它引入了"BDD contract layer"（独立于 Gherkin 语法的规范化中间表示），这是比现有方案更深的架构假设。

### 它最适合指导谁

**主要受众：AI coding agents + 负责 repo 治理的 tech lead。** 次要受众：开发者。它不太适合测试人员直接使用，因为它缺乏用户视角的输出设计（BA/QA/Automation 视角在它里面完全缺失）。

---

## 2. 上传方案相对现有方案的优势

### 更具体、更可执行的地方

**Checker 稳定性信号（Short-term G）** 是整个对比里最有价值的具体设计——对同一基准集跑两次 checker，统计结论不一致的 case 数量。这直接量化了"同一规则今天阻塞、明天不阻塞"的幻觉问题。现有方案对 LLM 非确定性完全没有防御设计。

**源锚点（paragraph_id）作为 Phase 1 可交付物** 而非可选项。现有方案在 Phase 2 才引入段落 ID，上传方案把它提到 Phase 1——这是正确的，因为没有稳定的段落锚，后续所有溯源都是沙堆上建楼。

**模型兼容性政策** 非常具体：新模型上线前必须通过 schema 合规、benchmark 阈值、checker 稳定性阈值、artifact diff 人工审查。现有方案只说"新增 provider"但没有定义什么时候算安全。

**Repo 文档结构（9个文档）** 的设计思路很好——把 roadmap、implementation plan、architecture、acceptance、model governance、agent guidelines、testing governance、prompt lifecycle、step integration plan 分开。这不是冗余，是关注点分离。

### 更适合直接驱动 LLM/Agent 开发的地方

**AI Agent 贡献规则（5条）** 可以直接放进 `CLAUDE.md` 或 `AGENTS.md`，让任何 agent 在开始工作前先读这个文件。这是现有方案完全没有的设计。

**"每个功能必须附带 acceptance test"的强制规定** 让 agent 无法在没有验证的情况下认为任务完成。现有方案的 acceptance criteria 在里程碑级别，不在功能级别。

**"不绕过 schema""不耦合特定模型""不把结构化输出改成自由文本""不跨阶段扩展范围"** 这四条规则对 agent 来说是非常清晰的边界，而现有方案没有这类约束声明。

### 更适合企业落地的地方

**Long-term 的 Deterministic Oracle Framework** 是企业级的核心设计：把计算验证、字段验证、状态验证从 LLM 判断里剥离出来，形成确定性断言层。这对 LME 金融场景尤其重要——保证金计算的正确性不能由 LLM 说了算。

**Step Definition Registry + Execution Readiness Contract** 提供了一个从 BDD 场景到实际可运行测试的清晰桥梁，包括 environment requirements、setup hooks、linked step definitions。这比现有方案的"生成 step 桩"要成熟得多。

**Hosted Review Service（Long-term D）** 把 review-session 从本地 HTTP 升级为可部署的 web service，有用户角色、审计轨迹、冲突解决——这是多团队协作的必要条件。

---

## 3. 上传方案相对现有方案的不足

### 过重、过细、过早设计的地方

**Review 协作 v1（Mid-term F）——export/import/merge review package** 在当前 single-user review-session 阶段引入这个机制是过早的。基础的 review 功能都还在本地 HTTP，跳到 bundle 导入导出会制造工程负担而没有真实需求。

**Hosted Review & Governance Service（Long-term D）** 的功能描述（RBAC、多用户、comment threads）是 3-5 年的产品愿景，不是 18 个月内的工程计划。把它列为 Long-term 交付物会设置不现实的期望。

**Enterprise Observability（Long-term E）的 9 个指标**（ingestion failure rate、extraction drift、planner change rate 等）在没有 production traffic 的情况下是无意义的指标。这是"为了看起来企业级"的设计，而不是"为了解决真实问题"的设计。

### 会带来架构耦合或维护负担的地方

**9 个 `docs/` 文档** 如果一开始就全部建立并维护同步，代价极高。`docs/architecture/architecture.md`、`docs/planning/implementation_plan.md`、`docs/governance/model_governance.md` 三个文档之间有大量重叠内容，会出现"修改了 schema 但只更新了两个文档"的漂移问题。

**BDD contract layer 作为独立中间表示** 是正确的架构方向，但它没有定义这个中间格式的 schema。如果没有 schema，这个"稳定中间态"本身就是不稳定的。引入它之前必须先定义它的 JSON schema，否则反而会增加一层不受控的转换。

**Test Planning Layer（Mid-term B）** 在 semantic_rules 和 BDD 之间引入 planner 角色，产生 priority/risk level/scenario family/dependency notes。这是正确方向，但它隐含要求 planner 的输出要经过 schema 验证和 human review，而这个 gate 的设计完全没写。如果 planner 输出质量差，后面所有 BDD 都会受影响。

### 与现有 repo 阶段不完全匹配的地方

**"Upstream rule extraction governance is not yet a first-class validation layer"** 这个判断对现有 repo 的评估是准确的，但它的解法（Phase 1 B、C、D）实际上要求先重构 `scripts/extract_matching_rules.py` 的输出格式，这会破坏现有的 `semantic_rules.json` → Maker 的链路，不是一个可以安全增量做的修改。

**"Checker stability signal（同基准集跑两次）"** 对应现有 repo 实际上有成本：需要两次 API 调用来产出一个"不稳定性分数"，而 token 成本和时间成本没有被讨论。在 POC 阶段可行，但在 200+ 规则的完整集上这会让开发成本翻倍。需要采样策略。

**Regression baseline（Checker twice + benchmark set）** 的建立需要有一个"已知正确"的 ground truth 集。现有 `poc_two_rules` 是唯一的接近 ground truth 的样本，而它只有两条规则。在 ground truth 不够的情况下，baseline 只能检测结构性崩溃，检测不了内容质量退化。

---

## 4. 取长补短建议

### 应该吸收进现有 roadmap 的内容

**立即吸收（改变认知框架）：**

1. **确定性/LLM 职责分离原则** 应该成为现有 roadmap 的 Principle 0，而不是隐含的。`schemas.py` 的定位从"验证器"升级为"确定性职责边界的物化"。
2. **Checker 稳定性信号** 应该并入 Phase 1 Milestone 1.1——在 convergence controller 里加一个 `StabilityMonitor`，对 poc 基准集每次 checker 跑完后记录一次，两次结果不一致的 case 自动标记。
3. **AI Agent 贡献规则（5条）** 应该直接写进 `AGENTS.md` 或 `CLAUDE.md`，现在就做，不用等到任何 phase。
4. **模型兼容性政策** 应该并入 Phase 1 的 `docs/governance/model_governance.md`——新 provider 上线前必须过 poc 基准集的 schema 合规检测。
5. **源锚点（paragraph_id）作为 Phase 1 必交付物** 而非 Phase 2——把它从现有方案的 Milestone 2.1 提前到 Phase 1 的 Milestone 1.3 附近（但作为提取脚本的输出增强，而非全新模块）。

**Phase 2 重要吸收：**

6. **Test Planning Layer** 应该在 Phase 2 引入，放在 Milestone 2.3（semantic rule synthesis）之后——作为 semantic_rules → planner（新 LLM 角色）→ test_objectives.json → BDD generation 的新阶段。但 planner 的 schema 必须在引入前定义好。
7. **BDD contract layer（规范化中间表示）** 应该在 Phase 2 Milestone 2.4 之前插入——先定义 `BDDScenario` 的 JSON schema，再从它生成 `.feature` 语法，而不是直接生成 Gherkin。

**Long-term 重要吸收：**

8. **Deterministic Oracle Framework** 应该进入 Phase 3，但不作为通用框架，而是针对 LME 金融规则的具体断言（保证金计算结果、截止时间窗口、头寸状态转换）。
9. **Step Definition Registry** 设计思路应该合并进现有方案的 Milestone 2.5，但执行层（exact match、parameterized match、reuse score）推迟到 Phase 3。

### 不应直接采纳、应降级为可选项或后期项的内容

| 内容 | 原因 | 建议处理 |
|------|------|---------|
| Review package export/import/merge | 超前于当前 single-user 阶段 | 降为 Phase 3 可选项，前提是 review-session 已稳定运行 3+ 月 |
| Hosted review service（RBAC+多用户） | 是产品愿景不是工程计划 | 移出 roadmap，放进 `docs/future_vision.md` |
| Enterprise observability（9 个指标） | 没有 production traffic 时无意义 | 保留 3 个核心指标（block rate、coverage %、checker instability rate），其余删除 |
| 9 个 docs/ 文档同时建立 | 维护同步成本高 | Phase 1 只建 4 个（roadmap、acceptance、model_governance、agent_guidelines），其余按需添加 |
| Checker 跑两次（完整规则集） | Token 成本翻倍 | 仅在 poc 基准集（< 10 条规则）上跑两次，作为采样稳定性检测 |
| Planner stage 无 schema 定义 | 引入不可控中间层 | 先定义 `test_objectives.json` schema，再引入 planner LLM |

---

## 5. 合并后的推荐版本

### 保留项（两个方案都有，继续保留）

- Provider 抽象层 + 多 LLM 支持
- Prompt 版本管理（文件化）
- Schema 验证作为硬门槛
- Convergence controller（Phase 1）
- 并发批处理（Phase 1）
- Few-shot exemplar registry（Phase 1）
- 覆盖率趋势报告（Phase 1）
- 文档摄入 → atomic rule → semantic rule 链路（Phase 2）
- BDD `.feature` 文件生成（Phase 2）
- Step 桩代码生成（Phase 2）
- CI/CD 集成（Phase 3）

### 修改项（一个方案有，另一个方案补强）

**Phase 1 新增/增强：**
- `AGENTS.md`：立即创建，直接采用上传方案的 5 条 Agent 贡献规则
- `docs/governance/model_governance.md`：Phase 1 必交付，内容来自上传方案的 Cross-Model Governance 章节
- `docs/governance/acceptance.md`：把现有方案的 acceptance gate 表格独立成文档
- **Checker 稳定性监控**：并入 Milestone 1.1 的 convergence controller，但仅对 poc 基准集（≤ 10 条规则）采样运行两次
- **源锚点（paragraph_id）提前到 Phase 1**：作为提取脚本的增量增强，不新建模块

**Phase 2 结构调整：**
- **新增 BDD contract layer**（Milestone 2.4 之前）：定义 `BDDScenario` JSON schema 作为 Gherkin 的上游中间表示，schema 必须先于 LLM 调用定义
- **新增 Test Planning Layer**（Milestone 2.3 之后）：`semantic_rules → planner LLM → test_objectives.json → BDD generator`，planner schema 定义为 Phase 2 前置条件
- **Step definition registry**（合并进 Milestone 2.5）：仅做 step 文本到桩函数的映射记录，不实现 exact/parameterized match（那是 Phase 3）

**Phase 3 结构调整：**
- **Deterministic Oracle Framework** 范围收窄：只针对 LME 核心规则类型（deadline、calculation、data_constraint），不搞通用框架
- **Hosted review service** 降级为 Phase 3 可选项，前提条件是 review-session 本地版稳定运行 6+ 月

### 延后项（超前于当前阶段，移至 Phase 3 末尾或 future_vision.md）

- Review package export/import/merge → Phase 3 末尾，可选
- Hosted review service with RBAC → `docs/future_vision.md`
- Enterprise observability（全套 9 指标）→ Phase 3 末尾，仅保留 3 核心指标作为 Phase 2 交付
- Multi-tenant platform → `docs/future_vision.md`
- Copilot Skill export（来自现有方案）→ Phase 3 末尾，可选（依赖企业是否使用 GitHub Copilot）

### 删除项（两个方案都有但不应保留的内容）

- 现有方案中 Phase 2 的用户类型输出 Profile（BA/QA/Automation/Mixed）——这是 `chat-prompt.md` 的设计，放进 repo roadmap 会引入测试人员工具链和开发者工具链的耦合。改为在 `reporting.py` 里提供 `--verbosity [minimal|standard|full]` 标志，而不是面向用户角色设计输出格式。
- 上传方案中 Phase 1 的 9 个 docs 文件同时建立——改为按需建立，Phase 1 只建 4 个核心文档。
- 上传方案中 Enterprise observability 的所有超出 3 个核心指标的内容。

---

### 文档级落点

合并后的 repo 文档结构建议：

```
docs/
  roadmap.md              ← 合并后的本文档
  acceptance.md           ← 各阶段验收标准（来自现有方案的 gate 表格）
  model_governance.md     ← 来自上传方案的 Cross-Model Governance 章节
  agent_guidelines.md     ← 来自上传方案的 AI Agent Contribution Rules
  architecture.md         ← Phase 2 建立，定义确定性/LLM 职责边界
  prompt_lifecycle.md     ← Phase 2 建立，当 prompts/ 目录超过 6 个文件时
  step_integration_plan.md ← Phase 3 建立，定义 step 绑定策略
  future_vision.md        ← 存放被延后的超前设计

AGENTS.md                 ← repo 根目录，立即创建，供 AI agent 读取