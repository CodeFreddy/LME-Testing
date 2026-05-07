# LME Testing — Architecture v3.1

**修订日期：** 2026-04-26
**变更说明：** 整合 HKv14 POC governed intake、deterministic diff evidence and modular mock API bridge，同时保持 HKv14 POC/mock/stub boundary。

---

## 一、系统定位

LME Testing 是一个**文档驱动的 AI 辅助测试设计工具**，面向单一领域（LME 匹配规则），当前为本地单用户使用。

### 当前是什么
- 将 LME 规则文档转化为结构化 BDD 测试场景的 AI 流水线
- 提供人工审核、重写、BDD 编辑、报告的完整本地工作流
- 有完整 schema 契约和 CI 验证的 governance 框架
- 多人协作的代码库（main + master 分支合并中）

### 当前不是什么
- **不是**通用测试生成平台
- **不是**多用户协作平台（明确单用户设计）
- **不是**测试执行引擎（生成设计产物，不执行）
- **不是**已在生产规模验证的系统

---

## 二、架构原则（v3.0 新增第 8 条）

1. Artifacts are first-class contracts
2. Upstream quality first
3. Deterministic before LLM
4. Human review is a control layer
5. Durable context is repo-readable
6. Real data before governance claims
7. Honest capability boundary
8. **Merge by understanding, not by overwriting** — 多人协作时，分支合并基于逐文件分析，不盲目覆盖；破损的 import 记录为新任务，不直接合并进主路径

---

## 三、当前流水线（Main 版本，包含 BDD 层）

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
[validate_rules.py] ─────────── schema validation (blocking)
        │
        ├──── [Planner: LLM] ── planner_results.jsonl（可选）
        │
        ▼
[Maker: LLM] ◄──────────────── MAKER_SYSTEM_PROMPT v1.1
        │  maker_cases.jsonl
        ▼
[BDD Pipeline: LLM] ◄────────── BDD_SYSTEM_PROMPT v3.0
        │  normalized_bdd.jsonl
        ▼
[BDD Export] ────────────────── .feature files + step_definitions.py
        │
        ▼
[Step Registry] ─────────────── step_visibility.json（35.4% binding，模拟 API）
        │
        ├──────────────────────────────────────┐
        ▼                                      ▼
[Checker: LLM] ◄──────────────        [Human Review UI]
        │  checker_reviews.jsonl        localhost:8765
        │  coverage_report.json         /api/reviews/save
        │                               /api/bdd（BDD tab）
        └──────────────┬────────────────/api/scripts（Scripts tab）
                       ▼               /api/stage（stage gates）
              [Rewrite if needed]
                       │
                       ▼
              [HTML Report + CSV]
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

待实现（Stage 2）：
[audit_trail.html] ◄──────────── audit_trail.py（来自 master 概念）
[case_compare.html] ◄─────────── case_compare.py（来自 master 概念）
```

### Mock API execution bridge（S2-C1）

在真实 LME VM/API 不可用时，`deliverables/lme_mock_api/` 提供一个独立 HTTP mock API 和可执行 BDD sample：

```
BDD feature
    │
    ▼
[Python step definitions]
    │ HTTP
    ▼
[mock_lme_api.server]
    │
    ▼
[deterministic rule checks]
```

该 bridge 用于证明 BDD/script 可以调用 API under test；它不替代 Stage 3 的真实 LME API 接入，也不改变主流水线 artifact contract。

### Initial Margin HKv13 mock API execution bridge（S2-C2）

`deliverables/im_hk_v13_mock_api/` 提供一个独立 HTTP mock API 和可执行 BDD sample，用于 Initial Margin HKv13 计算指南领域：

```
BDD feature
    │
    ▼
[Python step definitions]
    │ HTTP
    ▼
[mock_im_api.server]
    │
    ▼
[deterministic calculation and validation checks]
```

该 bridge 覆盖 RPF validation、position normalization、market risk components、MTM split、margin aggregation、corporate actions、cross-day netting、cross-currency netting 和 intraday MTM treatment。它只验证脚本到 HTTP mock API 的闭环，不代表真实 VaR Platform/HKSCC/HKEX execution readiness，也不改变主流水线 artifact contract。

### Initial Margin HKv14 POC modular mock API bridge（S2-C3）

`artifacts/im_hk_v14/` contains governed HKv14 intake generated from `docs/materials/Initial Margin Calculation Guide HKv14.pdf`. `evidence/im_hk_v14_diff/` preserves deterministic HKv13→HKv14 diff evidence, and `docs/planning/im_hk_v14_downstream_decision.md` records the POC decision to accept all deterministic diff candidates.

The mock API implementation is split into:

```
deliverables/im_hk_mock_api_common/
    │
    ├── shared deterministic implementation
    │
    ▼
deliverables/im_hk_v14_mock_api/
    │
    └── thin HKv14 wrapper, labels, data, BDD sample, tests
```

This bridge proves wrapper reuse for HKv14 POC validation. It does not claim HKv14 production downstream automation readiness, does not alter main pipeline schemas/prompts/models, and does not overwrite `deliverables/im_hk_v13_mock_api/`.

### Review UI automation assurance（S2-D1）

`tests/test_review_session_browser.py` 启动真实 local review-session HTTP server，并通过 Chrome DevTools Protocol 驱动本机 Chrome/Edge，验证：

```
Scenario Review tab
    │
    ▼
BDD Review tab
    │  save BDD edits
    ▼
Scripts tab
    │  refreshed visible match metrics
    ▼
Save Scripts edits
```

该测试层只验证现有 UI 与 governed artifacts 的浏览器交互，不新增产品 scope、不调用 live LLM provider、不改变 artifact contract。

### Rule extraction review workflow（S2-F4）

`src/lme_testing/rule_workflow_session.py` adds a local workflow server for document intake and business-friendly rule artifact review:

```
Source document or artifact folder
    │
    ▼
[rule_extraction.py]
    │  atomic_rules.json + semantic_rules.json
    ▼
[Rule Workflow Review UI]
    │  reviewed_atomic_rules.json + reviewed_semantic_rules.json
    ▼
[optional existing maker/checker/BDD/review-session path]
```

This was integrated from CodeFreddy's `feature/rule-extraction-review` branch as a controlled merge slice. The slice keeps schema, prompt, and default model impact at none; concurrent pipeline execution and CodeFreddy's review-decision contract changes remain out of scope unless separately governed.

As of 2026-05-06, the slice is on `main` and pushed to both `origin/main` and CodeFreddy's `feature/rule-extraction-review` branch. The GUI startup path falls back to the committed stub LLM config when `config/llm_profiles.json` is absent, and PDF upload/extract uses `pypdf` before falling back to `pdftotext`. HKv14 PDF extraction and the rule-to-scenario review smoke path were exercised through the GUI.

---

## 四、模块目录（Main 完整版）

### 主要模块

| 模块 | 职责 | 来源 | 状态 |
|------|------|------|------|
| `src/lme_testing/pipelines.py` | maker/checker/planner/BDD 流水线 | Main | ✅ 910行 |
| `src/lme_testing/providers.py` | LLM API 调用，StubProvider | Main | ✅ 442行 |
| `src/lme_testing/prompts.py` | 所有系统 prompt 和版本号 | Main | ✅ 310行，带版本控制 |
| `src/lme_testing/review_session.py` | Web UI 服务，所有 API 路由 | Main | ✅ 1251行，含 BDD tabs |
| `src/lme_testing/workflow_session.py` | 全流程编排 | Main+Cherry-pick | ✅ SM-T03 加中断处理 |
| `src/lme_testing/storage.py` | 文件 I/O 工具 | Main+Cherry-pick | ✅ SM-T02 UTC 时间戳 |
| `src/lme_testing/bdd_export.py` | BDD 产物导出（.feature, step defs）| Main | ✅ |
| `src/lme_testing/step_registry.py` | Step 可见性注册与匹配 | Main | ✅ |
| `src/lme_testing/step_library.py` | Step 定义库（模拟 LME API）| Main | ⚠️ 模拟实现 |

**Scripts Tab 工作流（Review Session）**

Review Session 启动时传入 `--step-registry step_visibility.json`，Scripts tab 显示三类 step 状态：

| 状态 | 含义 | UI 显示 |
|------|------|---------|
| `exact` | BDD step text 与 library 精确匹配 | 绿色 badge |
| `parameterized` | 正则 capture group 兼容匹配 | 蓝色 badge |
| `candidate` | 相似但非精确匹配（TF-IDF similarity） | 黄色 badge，下方显示 Suggestions |
| `unmatched` / GAP | BDD step 在 library 中无匹配 | 红色 GAP section |

**采用候选实现的步骤：**

1. 在 matched step 的 Suggestions 列表中，找到合适的 library step text（标注相似度 %）
2. 在页面底部红色 **GAP** section 中找到对应的未实现 step
3. 将 library step text 填入 GAP step 的 textarea
4. 点击 **Save Scripts Edits** → 保存到 `human_scripts_edits_latest.json`
5. 下次 Rewrite 时，`apply_human_step_edits()` 读取该文件，用 library 实现替换 pending stub

**注意：** GAP section 的 step 是原始 BDD step，Suggestions 来自 library。直接编辑 GAP textarea 即表示"我要用这条 library text 替代原始 BDD text"。
| `src/lme_testing/human_review.py` | Human review HTML 渲染 | Main | ✅ |
| `src/lme_testing/schemas.py` | Schema 验证工具 | Main | ✅ |
| `src/lme_testing/config.py` | 配置加载与类型定义 | Main+Cherry-pick | ✅ SM-T04 重试配置 |
| `src/lme_testing/signals/__init__.py` | Governance signals 计算 | Main | ⚠️ 2/4 信号数据为空 |
| `src/lme_testing/oracles/` | 8 个确定性验证模块 | Main | ✅（未在真实场景验证）|
| `src/lme_testing/audit_trail.py` | 审计跟踪 HTML 生成 | Main | ✅ 已实现并集成入 `review_session.py` |
| `src/lme_testing/case_compare.py` | Case 对比视图 | Main | ✅ 已实现并集成入 `review_session.py` |
| `src/lme_testing/rule_extraction.py` | Deterministic source-to-rule artifact extraction for rule review workflow; `pypdf` primary PDF extraction, `pdftotext` fallback | CodeFreddy merge slice + GUI fix | ✅ S2-F4 integrated |
| `src/lme_testing/rule_workflow_session.py` | Local document intake and rule artifact review server | CodeFreddy merge slice | ✅ S2-F4 integrated |

### Master 分支额外实现（已分析，部分 cherry-pick）

| Master 模块/特性 | 处理方式 | 原因 |
|----------------|---------|------|
| UTC 时间戳 | ✅ Cherry-pick（SM-T02）| 更规范 |
| KeyboardInterrupt 处理 | ✅ Cherry-pick（SM-T03）| 改善 UX |
| max_retries 配置 | 🧊 可选 Cherry-pick（SM-T04）| 待验证是否需要 |
| audit_trail 调用点 | ✅ 已实现并集成（S2-B1）| 模块已实现 |
| case_compare 调用点 | ✅ 已实现并集成（S2-B2）| 模块已实现 |
| 旧版 providers.py（135行）| ❌ 不合并 | 编码损坏，缺 StubProvider |
| 旧版 pipelines.py（639行）| ❌ 不合并 | 缺 planner/BDD pipeline |
| 旧版 prompts.py（无版本）| ❌ 不合并 | 无版本控制 |

---

## 五、Web UI 路由映射（Main 完整版）

### GET 路由

| 路径 | 功能 |
|------|------|
| `/` | 主界面 HTML |
| `/api/session` | 当前 session 状态 |
| `/api/history` | 迭代历史 |
| `/api/bdd` | BDD scenarios（normalized_bdd）|
| `/api/scripts` | Step definitions 可见性 |
| `/api/stage` | Stage gates 状态 |
| `/api/status/<job_id>` | 异步任务状态 |
| `/report.html` | HTML 报告 |
| `/maker_readable.html` | Maker 输出可读视图 |
| `/checker_readable.html` | Checker 输出可读视图 |
| `/coverage.csv` | Coverage 导出 |
| `/files` | 文件浏览器 |

### POST 路由

| 路径 | 功能 |
|------|------|
| `/api/reviews/save` | 保存人工审核决策（atomic_write）|
| `/api/bdd/save` | 保存 BDD 编辑（atomic_write）|
| `/api/scripts/save` | 保存 step definitions 编辑 |
| `/api/stage/advance` | 推进 stage gate |
| `/api/submit` | 提交触发 checker/rewrite |
| `/api/finalize` | 最终确认，触发 audit_trail 生成（待 S2-B1 实现）|

**Master 版路由对比（仅供参考）：**

| Master 路由 | Main 等价路由 | 说明 |
|------------|-------------|------|
| `/api/audit_trail` | ✅ 已实现（S2-B1）| 集成入 `finalize_session()` |
| `/api/reviews/save` | `/api/reviews/save` | 相同 |
| `/api/submit` | `/api/submit` | 相同 |
| `/api/finalize` | `/api/finalize` | 相同 |
| 无 | `/api/bdd` | Main 新增（BDD tab）|
| 无 | `/api/scripts` | Main 新增（Scripts tab）|
| 无 | `/api/stage` | Main 新增（Stage gates）|

---

## 六、Governance Signals 数据来源（v3.0 更新）

| 信号 | 数据来源 | 可信度 | 修复任务 |
|------|---------|--------|---------|
| `schema_failure_rate` | 无（从 coverage 推断）| ⚠️ 假数据 | S1-T01 |
| `checker_instability_rate` | 真实 API 测量（MiniMax-M2.7）：v1/v2 14 cases → 71% instability；v3/v4 10 cases → 60% instability（delta 主要=1）；retry logic 已实现，但 API 随机断开阻止全量 322-case 测量 | ⚠️ 高 instability，但样本小且非全量；S2-T01 blocked by API 可靠性
| `coverage_percent` | 全量运行数据（路径未对齐）| 🔄 待对齐 | S1-T02 |
| `step_binding_success_rate` | 模拟 step library | ⚠️ 无实际意义 | Stage 3（待 LME VM）|

---

## 七、目录结构

| 目录 | 职责 |
|------|------|
| `src/lme_testing/` | LME matching-rule 核心 Python 包（主路径）|
| `src/hkex_testing/` | HKEX Initial Margin 领域命名空间；当前对应 `artifacts/im_hk_v13/` |
| `src/rule_testing/` | 旧导入路径兼容别名；新代码应使用 `lme_testing` |
| `scripts/` | 提取脚本、治理检查脚本 |
| `schemas/` | 7 套 artifact schemas + fixtures |
| `config/` | provider 配置、governance 配置 |
| `artifacts/` | 规则 artifacts（183条）|
| `docs/` | 核心契约文档：roadmap、implementation plan、acceptance、architecture、model governance、agent guidelines |
| `docs/governance/` | 支撑治理政策：prompt lifecycle、testing governance、reference policy |
| `docs/planning/` | 阶段计划、验证计划、覆盖率分析、UI/mock/step integration 计划 |
| `docs/architecture/` | 架构支撑细节：run directory structure、rule model/parsing design |
| `docs/guides/` | 操作和开发指南 |
| `docs/operations/` | session handoff 和 checkpoint/resume 状态 |
| `docs/releases/` | Release notes 和 baseline records |
| `docs/materials/` | 源材料和转换后的材料 |
| `docs/references/` | 历史/外部参考材料 |
| `docs/archives/` | 已完成或归档的规划记录 |
| `tests/` | 15 个测试文件（78 个测试）|
| `evidence/` | 关键运行证据（versioned）：stability、baseline、governance signals |
| `runs/` | pipeline 运行输出（gitignored）|
| `deliverables/lme_mock_api/` | S2-C1 mock API execution bridge（独立交付物，不改变主包契约）|
| `deliverables/im_hk_v13_mock_api/` | S2-C2 Initial Margin HKv13 mock API execution bridge（独立交付物，不改变主包契约）|
| `deliverables/im_hk_mock_api_common/` | S2-C3 shared Initial Margin mock API implementation for bounded POC wrappers |
| `deliverables/im_hk_v14_mock_api/` | S2-C3 Initial Margin HKv14 POC mock API wrapper（thin wrapper over common code）|
| `evidence/im_hk_v14_diff/` | S2-C3 deterministic HKv13→HKv14 governed artifact diff evidence |
| `tests/test_review_session_browser.py` | S2-D1 browser-level review UI E2E（本机 Chrome/Edge，可 skip）|

---

## 八、多人协作架构约束（v3.0 新增）

基于本次 master 分支合并分析建立以下约束：

### 分支合并前的必检项

1. **文件集差异分析** — 先用 `comm` 或 `diff -rq` 确认哪些文件是新增/修改/删除
2. **核心模块优先级** — `src/lme_testing/bdd_export.py`、`schemas/`、`src/lme_testing/oracles/`、`src/lme_testing/signals/` 是主分支的核心资产，合并时不得删除
3. **broken import 检查** — 合并前检查所有 import 是否有对应模块文件
4. **编码问题检查** — 检查文件是否有 `???` 乱码（Windows 编码问题）

### 合并策略优先级

```
1. 新增文件（对方有，己方无）→ 直接评估是否纳入
2. Cherry-pick（对方某文件局部改进）→ 逐段分析，最小化改动
3. 整体覆盖（整个文件替换）→ 禁止，除非完全理解差异
4. 概念保留（对方引用但缺失实现）→ 记录为新任务，不合并破损代码
```

### provider.py 编码规范

开发者在 Windows 环境编写中文注释时，确保文件保存为 UTF-8（不带 BOM），避免 `???` 乱码。推荐在 `.editorconfig` 中强制：
```
charset = utf-8
```

---

## 九、已知架构限制（v3.0 更新）

| 限制 | 影响 | 接受原因 |
|------|------|---------|
| 单用户 Web UI | 不支持团队并发 | 工具定位 |
| Step library 基于模拟 API | step binding rate 无意义 | 待 Stage 3 |
| Checker 是 LLM，概率性 | 判断不保证一致性 | 通过 stability 测量缓解 |
| audit_trail/case_compare 已集成但为本地 HTML 输出 | 只覆盖 review-session 本地审计视图 | 符合单用户工具定位 |
| Mock API 不是真实 LME API | 只能验证脚本到 HTTP API 的闭环，不代表真实执行能力 | Stage 3 仍需 VM/API 权限 |
| Initial Margin HKv13 mock API 不是真实 VaR Platform | 只能验证 IM BDD/script 到 HTTP API 的闭环，不代表真实保证金计算能力 | Stage 3 仍需真实执行环境 |
| Initial Margin HKv14 bridge is POC/mock/stub only | 只验证 HKv14 intake、diff evidence and wrapper reuse，不代表 production downstream automation readiness | HKv13 remains preservation baseline; Stage 3 still requires real execution access |
| Windows PowerShell 工具链 | 跨平台受限 | 单人开发现状 |

---

## 十、架构评审检查清单（v3.0 更新）

在每次重大变更或分支合并前：

- [ ] 所有新增 import 都有对应的模块文件？
- [ ] 合并是否保留了 artifact 契约（7 套 schema）？
- [ ] BDD 层（`bdd_export.py`、`normalized_bdd.schema.json`）是否完整？
- [ ] Oracle 模块（8个）是否完整？
- [ ] Governance signals 数据来源是否标注（real_api/stub/no_data）？
- [ ] `atomic_write_json()` 是否保留？
- [ ] CI smoke test 是否通过？
- [ ] 是否与当前 roadmap 阶段一致？
