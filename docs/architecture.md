# LME Testing — Architecture v3.0

**修订日期：** 2026-04-19  
**变更说明：** 整合 master 分支合并分析。新增多人协作架构约束、vendor/ 目录职责、待实现模块规划（audit_trail、case_compare）。

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

---

## 四、模块目录（Main 完整版）

### 主要模块

| 模块 | 职责 | 来源 | 状态 |
|------|------|------|------|
| `lme_testing/pipelines.py` | maker/checker/planner/BDD 流水线 | Main | ✅ 910行 |
| `lme_testing/providers.py` | LLM API 调用，StubProvider | Main | ✅ 442行 |
| `lme_testing/prompts.py` | 所有系统 prompt 和版本号 | Main | ✅ 310行，带版本控制 |
| `lme_testing/review_session.py` | Web UI 服务，所有 API 路由 | Main | ✅ 1251行，含 BDD tabs |
| `lme_testing/workflow_session.py` | 全流程编排 | Main+Cherry-pick | 🔄 SM-T03 加中断处理 |
| `lme_testing/storage.py` | 文件 I/O 工具 | Main+Cherry-pick | 🔄 SM-T02 改 UTC 时间戳 |
| `lme_testing/bdd_export.py` | BDD 产物导出（.feature, step defs）| Main | ✅ |
| `lme_testing/step_registry.py` | Step 可见性注册与匹配 | Main | ✅（step lib 基于模拟）|
| `lme_testing/step_library.py` | Step 定义库（模拟 LME API）| Main | ⚠️ 模拟实现 |
| `lme_testing/human_review.py` | Human review HTML 渲染 | Main | ✅ |
| `lme_testing/schemas.py` | Schema 验证工具 | Main | ✅ |
| `lme_testing/config.py` | 配置加载与类型定义 | Main+Cherry-pick | 🔄 SM-T04 加重试配置 |
| `lme_testing/signals/__init__.py` | Governance signals 计算 | Main | ⚠️ 2/4 信号数据为空 |
| `lme_testing/oracles/` | 8 个确定性验证模块 | Main | ✅（未在真实场景验证）|
| `lme_testing/audit_trail.py` | 审计跟踪 HTML 生成 | **待实现（S2-B1）**| ❌ |
| `lme_testing/case_compare.py` | Case 对比视图 | **待实现（S2-B2）**| ❌ |

### Master 分支额外实现（已分析，部分 cherry-pick）

| Master 模块/特性 | 处理方式 | 原因 |
|----------------|---------|------|
| UTC 时间戳 | ✅ Cherry-pick（SM-T02）| 更规范 |
| KeyboardInterrupt 处理 | ✅ Cherry-pick（SM-T03）| 改善 UX |
| max_retries 配置 | 🧊 可选 Cherry-pick（SM-T04）| 待验证是否需要 |
| audit_trail 调用点 | 📋 概念保留，模块待实现（S2-B1）| 模块缺失无法直接合并 |
| case_compare 调用点 | 📋 概念保留，模块待实现（S2-B2）| 模块缺失无法直接合并 |
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
| `/api/audit_trail` | 无（S2-B1 后添加）| Master 有但模块缺失 |
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

## 七、目录结构（含 vendor/）

| 目录 | 职责 |
|------|------|
| `lme_testing/` | 核心 Python 包（主路径）|
| `scripts/` | 提取脚本、治理检查脚本 |
| `schemas/` | 7 套 artifact schemas + fixtures |
| `config/` | provider 配置、governance 配置 |
| `artifacts/` | 规则 artifacts（183条）|
| `docs/` | 架构、roadmap、治理、验收文档 |
| `tests/` | 15 个测试文件（78 个测试）|
| `samples/ruby_cucumber/` | Ruby Cucumber 原型（存档）|
| `logs-from-backup-run/` | POC 运行日志（存档）|
| `runs/` | pipeline 运行输出（gitignored）|
| `reports/` | HTML 报告输出 |
| `screenshot/` | 界面截图 |
| `vendor/master-branch/` | **新增（SM-T01）**：同事 master 分支快照，存档用 |

**`vendor/master-branch/` 约束：**
- 不参与任何 `import` 路径
- 不包含在 pytest 测试扫描范围内（`pyproject.toml` 或 `pytest.ini` 中 exclude）
- cherry-pick 完成后可删除，也可保留作历史参考

---

## 八、多人协作架构约束（v3.0 新增）

基于本次 master 分支合并分析建立以下约束：

### 分支合并前的必检项

1. **文件集差异分析** — 先用 `comm` 或 `diff -rq` 确认哪些文件是新增/修改/删除
2. **核心模块优先级** — `lme_testing/bdd_export.py`、`schemas/`、`lme_testing/oracles/`、`lme_testing/signals/` 是主分支的核心资产，合并时不得删除
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
| audit_trail/case_compare 待实现 | 缺少审计视图 | Stage 2 任务 |
| Windows PowerShell 工具链 | 跨平台受限 | 单人开发现状 |
| vendor/ 目录引入 | 增加 repo 体积 | cherry-pick 完成后可清理 |

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
- [ ] vendor/ 目录是否被 pytest exclude？
- [ ] 是否与当前 roadmap 阶段一致？
