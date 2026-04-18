# LME Testing — Revised Architecture

**版本：** 2.0  
**修订日期：** 2026-04-18  
**修订原因：** 补充实际验证状态说明，修正若干模块边界描述，新增已知限制和设计约束章节。

---

## 一、系统定位（诚实版）

LME Testing 是一个**文档驱动的 AI 辅助测试设计工具**，面向单一领域（LME 匹配规则）的本地单用户使用场景。

### 当前是什么

- 将 LME 规则文档转化为结构化 BDD 测试场景的流水线工具
- 提供人工审核、重写、报告的完整本地工作流
- 有完整 schema 契约和 CI 验证的框架

### 当前不是什么

- **不是**通用测试生成平台（针对 LME 领域优化）
- **不是**多用户协作平台（明确的单用户设计）
- **不是**测试执行引擎（生成测试设计产物，不执行）
- **不是**已在生产规模验证的系统（全量 183 条规则质量基准尚未建立）

---

## 二、架构原则

以下原则经过实践验证，继续有效：

1. **Artifacts are first-class contracts** — 结构化产物优于自由文本，所有 LLM 输出必须经 Schema 验证
2. **Upstream quality first** — 上游规则质量决定下游一切；无效的 atomic_rule 会污染整个流水线
3. **Deterministic before LLM** — 能确定性验证的（schema check、enum check、字段验证），不依赖 LLM 判断
4. **Human review is a control layer** — 人工审核是架构的必要组成，不是可选功能
5. **Durable context is repo-readable** — 所有可复现行为的控制资产（prompts、schemas、configs）必须在 repo 中

新增原则（基于实践教训）：

6. **Real data before governance claims** — governance 指标必须标注数据来源（`real_api` / `stub` / `no_data`），不用 stub 数据支撑治理声明
7. **Honest capability boundary** — 系统能力边界以最近一次真实验证为准，不外推

---

## 三、当前流水线

### 核心流水线（代码完整，POC 验证通过）

```
Source Documents (PDF/TXT)
        │
        ▼
[extract_matching_rules.py]
        │  atomic_rules.json
        ▼
[generate_semantic_rules.py]
        │  semantic_rules.json
        ▼
[validate_rules.py] ──────── schema validation (blocking)
        │
        ▼
[Maker: LLM-assisted]  ◄─── MAKER_SYSTEM_PROMPT (versioned)
        │  maker_cases.jsonl
        ▼
[BDD Pipeline] ────────────  normalized_bdd.jsonl
        │
        ▼
[BDD Export] ──────────────  .feature files + step_definitions.py
        │
        ▼
[Step Registry] ───────────  step_visibility.json
        │
        ├─────────────────────────────────────┐
        ▼                                     ▼
[Checker: LLM-assisted]              [Human Review]
        │  checker_reviews.jsonl             │  approve / rewrite / reject
        │  coverage_report.json             │
        └──────────────┬──────────────────────┘
                       ▼
              [Rewrite if needed]
                       │
                       ▼
              [HTML Report Generation]
                       │
                       ▼
              [Governance Signals]
```

### 扩展流水线（代码完整，验证状态见备注）

```
semantic_rules.json
        │
        ▼
[Planner: LLM-assisted]  ── planner_results.jsonl
        │                    （验证状态：Stub/POC 通过，全量未验证）
        ▼
[Maker: enriched input]
```

---

## 四、模块边界

### 4.1 Ingestion / Extraction 模块

**拥有：** 文档读取、解析、规则候选提取、source anchor 生成  
**不拥有：** 场景生成策略、provider 逻辑、报告渲染

**已知限制：**
- PDF 解析依赖 `pdfminer` / 标准库，对复杂布局 PDF（表格、多栏、图形）解析质量有限
- 多文档类型支持当前实现为 `DocumentClass` enum + keyword matching，不是真正的结构感知解析框架
- 这是设计上的简化，不是 bug，但不应对外声称"支持任意文档类型"

### 4.2 Rule Normalization 模块

**拥有：** atomic rule 生成、semantic rule 生成、trace 链接、schema 对齐、rule_type 解释  
**不拥有：** review UI、报告、provider 传输细节

**已知限制：**
- `infer_rule_type()` 基于关键词推断，对模糊表述的规则可能分类错误
- duplicate detection 是基于文本相似度的启发式方法，不是语义去重

### 4.3 Generation 模块（Maker / Planner / BDD）

**拥有：** maker 生成、rewrite、planner、normalized BDD 生成、BDD export  
**不拥有：** provider adapter 内部逻辑、schema 注册策略、长期分析逻辑

**已知限制：**
- Maker 输出质量依赖 LLM，概率性。真实质量基准待 S1-T04 建立
- Planner 阶段增加 API 调用成本，当前未量化其对最终 maker 质量的贡献
- BDD style learning 暂缓：无真实 BDD 样本，自循环优化无意义

### 4.4 Evaluation 模块（Checker）

**拥有：** checker 评估、benchmark 比较、stability 比较  
**不拥有：** 人工决策工作流、runtime 执行 pass/fail 真值、provider 传输

**已知限制（关键）：**
- Checker 本身是 LLM，其输出概率性，不是确定性真值
- 当前 `checker_instability_rate = 0%` 基于 StubProvider，**不代表真实 LLM 行为**
- 真实 MiniMax instability 率在 S1-T03b 完成后才能知晓

### 4.5 Review 模块

**拥有：** review 状态、决策存储、人工工作流控制（approve/rewrite/reject）、session snapshot  
**不拥有：** 规则提取、provider 逻辑、确定性执行断言

**设计约束（明确）：**
- **单用户设计**：Web UI 运行在 localhost:8765，无认证，无多用户并发支持
- Session snapshot 使用原子写入（S1-T03 完成后）
- 不支持跨 session 共享状态

### 4.6 Reporting 模块

**拥有：** HTML 报告生成、CSV 导出、coverage 聚合、traceability 视图、audit-style 运行摘要  
**不拥有：** 业务规则生成逻辑、provider 选择、schema 迁移策略

### 4.7 Provider / Model Strategy 模块

**拥有：** provider-specific API 调用、retry、structured output、metadata capture  
**不拥有：** 场景生成业务逻辑、报告渲染、review 工作流

**当前支持的 Provider：**

| Provider | Tier | 验证状态 | 适用 Role |
|----------|------|---------|-----------|
| stub | 1 | ✅ CI/Smoke | maker/checker/planner |
| minimax/MiniMax-M2.7 | 1 | ✅ POC（2条规则），全量质量待测 | maker/checker/planner |
| qwen/qwen3.5-plus | 2 | ⚠️ Experimental | maker only |

**注意：** compatibility_matrix.json 中标注的 "all phases compatible" 是基于代码兼容性，不代表输出质量已验证。

### 4.8 Schema / Contract 模块

**拥有：** artifact 结构定义、schema 验证、契约演进支持  
**不拥有：** provider 调用、文档解析、UI 工作流

**当前 Schema 清单（7套，CI 验证）：**
- `atomic_rule.schema.json`
- `semantic_rule.schema.json`
- `maker_output.schema.json`
- `checker_output.schema.json`
- `planner_output.schema.json`
- `normalized_bdd.schema.json`
- `executable_scenario.schema.json`

### 4.9 Oracle 模块

**拥有：** 8 个确定性断言模块（field_validation、state_validation、calculation_validation、deadline_check、event_sequence、pass_fail_accounting、null_check、compliance_check）  
**不拥有：** LLM 判断逻辑、场景生成

**已知限制：**
- 8 个 oracle 存在且有单元测试，但**尚未在真实 LME 规则场景上运行验证**
- `@register_oracle` 自动注册机制是提前设计的框架抽象，在真实场景验证之前不应扩展
- Oracle 适用规则类型（哪些 LME 规则适合确定性验证）待 S1-T04 基准建立后识别

### 4.10 Governance Signals 模块

**拥有：** 4 类信号计算（schema / instability / coverage / step binding）、JSON 输出  
**不拥有：** 实时监控、告警、持久化数据库

**当前信号数据来源状态：**

| 信号 | 当前数据来源 | 可信度 | 修复任务 |
|------|------------|--------|---------|
| schema_failure_rate | `runs/schema_validation_latest.json` (from CI schema-validation job) | ✅ 真实数据 | S1-T01 |
| checker_instability_rate | StubProvider 运行 | ⚠️ 不代表真实 LLM | S1-T03b |
| coverage_percent | `runs/checker/<run_id>/coverage_report.json` via `--runs-dir` | 🔄 全量数据待写入 | S1-T02 + S1-T04 |
| step_binding_success_rate | 模拟 step library | ⚠️ 不代表真实 LME | Stage 3 |

---

## 五、Artifact 契约

### Artifact 生命周期

```
Source → atomic_rule → semantic_rule → [planner_output] → maker_output
       → normalized_bdd → [executable_scenario] → checker_output
       → human_review → report
```

### 关键 Artifact 属性

每个 governed artifact 必须包含：
- `provider`, `model`, `prompt_version`, `run_timestamp`, `pipeline_version`

每个 rule-level artifact 必须包含：
- `paragraph_id`（stable source anchor）
- `rule_type`（controlled enum）
- `source.atomic_rule_ids`（traceability）

### Artifact 修改规则

修改任何 artifact schema 必须同时更新：
- schema 文件
- 对应 fixture（valid + invalid）
- 相关单元测试
- `docs/acceptance.md` 对应 gate 的 Evidence

---

## 六、Traceability 模型

### 当前可追溯路径

```
source document
  → paragraph_id（stable anchor）
    → atomic_rule（rule_id, paragraph_id）
      → semantic_rule（semantic_rule_id, atomic_rule_ids, paragraph_ids）
        → maker_output（semantic_rule_id, paragraph_ids）
          → checker_output（case_id, semantic_rule_id）
            → coverage_report（rule_coverage_status per semantic_rule_id）
              → HTML report（clickable rule ID → scenario detail）
```

### 当前 traceability 的已知缺口

- planner_output → maker_output 的 traceability 存在于代码，但未在 HTML report 中可视化
- normalized_bdd → executable_scenario 的链接存在于 schema，但无真实消费者验证
- step_visibility → step_definitions 的链接基于模拟 step library，不对应真实 LME API

---

## 七、验证架构

### 验证层次

| 层次 | 验证内容 | 实现状态 |
|------|---------|---------|
| Source ingestion | 可读性、格式、anchor 唯一性 | ✅ 实现 |
| Rule artifact | Schema、enum、required fields、traceability | ✅ 实现，CI 验证 |
| Generation artifact | Structured output、rule references、metadata | ✅ 实现 |
| Review artifact | Decision format、action values | ✅ 实现 |
| Reporting artifact | Completeness、metrics 一致性 | ✅ 实现 |

### CI 验证矩阵

| CI Job | 验证内容 | 当前状态 |
|--------|---------|---------|
| docs-governance | *.md 中无绝对路径 | ✅ 有效 |
| artifact-governance | artifact 结构和 rule_type enum | ✅ 有效 |
| schema-validation | JSON Schema fixtures + persistent output to `runs/schema_validation_latest.json` | ✅ 有效 |
| upstream-validation | atomic + semantic rules 完整性 | ✅ 有效 |
| unit-tests | 78 个单元测试 | ✅ 有效（基于 stub）|
| smoke-test | E2E 端到端冒烟 | ✅ 有效（stub，2条规则）|
| governance-signals | 计算 governance 指标 | ⚠️ 输出数字部分为空/stub |
| release-governance | release 文件完整性检查 | ✅ 有效（结构检查）|

---

## 八、失败模型

### 失败类别

1. **Source failure** — 文档不可读、格式不支持、提取失败
2. **Contract failure** — Schema 无效、enum 非法、trace 引用断裂
3. **Model failure** — timeout、malformed structured output、不稳定输出
4. **Review failure** — session snapshot 损坏（S1-T03 修复后降低概率）
5. **Reporting failure** — 缺少必需 artifact、汇总生成失败

### 架构规则

失败必须：可见、可分类、可归因到阶段、可恢复（在可能的情况下）、**不得隐藏为成功输出**

---

## 九、已知架构限制（当前不计划解决）

| 限制 | 影响范围 | 接受原因 |
|------|---------|---------|
| 单用户 Web UI | 不支持团队并发使用 | 当前工具定位为单用户 |
| PDF 解析依赖文档规整度 | 复杂布局 PDF 提取质量低 | 超出当前阶段范围 |
| Step library 基于模拟 API | step binding rate 无实际意义 | 等待 Stage 3 外部条件 |
| Checker 是 LLM，输出概率性 | 无法保证 checker 判断一致性 | 通过 stability 测量和 oracle 部分缓解 |
| Windows + PowerShell 工具链 | Linux/macOS 开发者无法使用 session handoff | 单人开发现状，跨平台支持非当前优先级 |
| 无认证/授权 | Web UI 对本地网络开放 | 设计为本地工具，不面向网络部署 |

---

## 十、架构评审检查清单（每次重大变更前）

- [ ] 这个变更是否保留了 artifact 契约？
- [ ] 是否改善或削弱了 traceability？
- [ ] provider 逻辑是否保持隔离？
- [ ] 是否模糊了模块边界？
- [ ] 是否将确定性职责移入了纯 LLM 逻辑？
- [ ] 是否引入了新的 LLM-driven 阶段而没有定义契约？
- [ ] 是否将 governance signal 的数据来源标注清楚（real_api / stub / no_data）？
- [ ] 是否与当前 roadmap 阶段一致？
- [ ] 是否保留了 rollback 清晰度？

---

## 附录：目录职责

| 目录 | 职责 |
|------|------|
| `docs/` | 架构、roadmap、治理、验收规则、代理规则 |
| `schemas/` | artifact schemas、fixtures、schema 演进支持 |
| `lme_testing/` | 核心 Python 包：pipelines、providers、oracles、signals |
| `scripts/` | 提取脚本、治理检查脚本 |
| `config/` | provider 配置、approved_providers、benchmark_thresholds |
| `artifacts/` | 规则 artifacts（lme_rules_v2_2、poc_two_rules） |
| `runs/` | pipeline 运行输出（gitignored，路径结构见 run_directory_structure.md） |
| `reports/` | HTML 报告输出 |
| `tests/` | 单元测试（78 个） |
| `samples/ruby_cucumber/` | Ruby Cucumber 原型（存档，非主路径） |

**`runs/` 目录结构：** 见 `docs/run_directory_structure.md`
