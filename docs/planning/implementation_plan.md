# LME Testing — Implementation Plan v3.1

**修订日期：** 2026-04-26  
**范围：** Stage M（合并）+ Stage 1（真实数据接入）+ Stage 2 已执行任务  
**说明：** Stage 2 已基于真实数据展开：S2-T01 prompt 校准完成，S2-B1/B2 集成完成，S2-C1 mock API execution bridge 完成，S2-C2 IM HKv13 mock bridge 完成，S2-C3 IM HKv14 POC document workflow and modular mock bridge 完成，S2-C4 IM HKv14 promoted downstream slice 完成，S2-D1 browser-level review UI E2E 完成。S2-F1 role-friendly HKv14 impact decision review package generator 已实现。S2-F2 MVP document readiness registry 已实现为 deterministic readiness package。

---
## 如何使用本文档

每个任务遵循统一结构：

- **任务 ID** — 全局唯一，格式 `S1-Txx`
- **目标** — 一句话说清楚做什么
- **为什么现在做** — 说明优先级依据
- **前置依赖** — 必须先完成的任务
- **输入契约** — 任务开始时必须存在的输入
- **输出契约** — 任务完成时必须产出的输出
- **实现要点** — 关键技术决策和约束
- **验收标准** — 可量化的完成判断
- **自评格式** — PASS / PARTIAL / FAIL
- **不在范围内** — 明确的边界

**治理规则：** 任务未达到 PASS 不得标记完成。PARTIAL 必须记录缺失项和补做计划。

---
## 任务总览与依赖图

```
Stage M（并行，1-3天）
├── SM-T01: vendor/ 存档         ─→ SM-T05: 文档归档
├── SM-T02: UTC 时间戳            ─→ SM-T05
├── SM-T03: Workflow 中断处理     ─→ SM-T05
└── SM-T04: 重试配置（可选）      ─→ SM-T05

Stage 1（Stage M 完成后）
├── S1-T01: Schema signal 修复    ─┐
├── S1-T02: Run 路径对齐          ─┼─→ S1-T04: 全量基准运行 ─→ S1-T05: 状态重写
├── S1-T03: Session 原子写入       ─┘
└── S1-T03b: Checker 真实稳定性   ─→ S1-T04

Stage 2 规划（Stage 1 完成后展开）
├── S2-B1: audit_trail.py 实现
└── S2-B2: case_compare.py 实现
└── S2-C1: Mock API execution bridge
└── S2-C2: Initial Margin HKv13 mock API execution bridge
└── S2-C3: Initial Margin HKv14 POC document workflow and modular mock API bridge
└── S2-C4: Initial Margin HKv14 promoted downstream slice
└── S2-C5: Mock API deliverables location policy
└── S2-D1: Browser-level review UI E2E
└── S2-F1: HKv14 role-friendly impact decision review
└── S2-F2: MVP document readiness registry
```

---

## Stage M — Master 分支合并

### SM-T01 — Vendor 存档

**目标：** 将 master 代码放入 `vendor/` 目录，保留可读性但不影响主路径

**输入契约：**
- master zip 文件

**输出契约：**
- `vendor/master-branch/`（完整 master 代码）✅
- `vendor/master-branch/README.md` ✅
- `.gitignore` 确认 `vendor/` 不被排除 ✅

**后续：** `vendor/` 目录已删除 — master 分支通过单独 remote 访问

**验收：**
- [x] `vendor/master-branch/lme_testing/review_session.py` 存在（已删除 — see above）
- [x] `python -c "from lme_testing.storage import timestamp_slug"` 正常
- [x] `vendor/master-branch/README.md` 有 cherry-pick 状态列表（已删除 — master 通过 separate remote）

**不在范围：** 将 vendor/ 加入任何 sys.path 或 import 路径

---

### SM-T02 — UTC 时间戳 Cherry-pick

**目标：** 将 `storage.py` 的 timestamp_slug 改为 UTC，增强跨时区协作可靠性

**输入契约：**
- `src/lme_testing/storage.py`（Main 当前版本）

**输出契约：**

`storage.py` 变更：
```python
# 变更前（Main 当前）
from datetime import datetime
def timestamp_slug() -> str:
    return datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")

# 变更后（cherry-pick from Master）
from datetime import UTC, datetime
def timestamp_slug() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
```

`docs/architecture/run_directory_structure.md` 补充：
> 时间戳格式：`YYYYMMDDTHHMMSSz`，UTC 时区，末尾固定 `Z`。示例：`20260419T120000Z`

**实现要点：**
- `atomic_write_json()` 保持不变（是 Main 独有的，Master 没有）
- 新时间戳格式（末尾有 `Z`）可通过字符串后缀区分旧格式
- 历史 `runs/` 目录名不受影响（已有目录不会重命名）

**验收：**
- [ ] `timestamp_slug()` 输出 `20260419T120000Z` 格式
- [ ] `atomic_write_json` 仍存在于 `storage.py`
- [ ] CI unit test 通过（test_storage.py）
- [ ] smoke test 通过

**风险：** 低。纯格式变更，不影响功能逻辑。

---

### SM-T03 — Workflow 中断处理 Cherry-pick

**目标：** 在 maker/checker 长时间 API 调用期间支持 Ctrl+C 中断

**输入契约：**
- `src/lme_testing/workflow_session.py`（Main 当前版本）
- `src/lme_testing/pipelines.py`（Main 当前版本）

**输出契约：**

`workflow_session.py` 变更：
- `run_workflow()` 返回类型改为 `tuple[...] | None`（None 表示被中断）
- maker 和 checker 步骤各加入 `try/except KeyboardInterrupt`，中断时调用 `p.shutdown()`
- 加入 `[workflow] Step N/4:` 进度输出（4步：Extract → Normalize → Maker → Checker）
- 函数签名加入 `provider_out: list = []`（用于中断时 shutdown）

`pipelines.py` 变更：
- `run_maker_pipeline()` 加入 `provider_out: list | None = None` 参数（默认 None，向后兼容）
- `run_checker_pipeline()` 同上
- 若 `provider_out is not None`，将 provider 实例追加到列表中

**实现要点：**
- `provider_out` 参数默认为 `None` 而非 `[]`（避免 Python mutable default 陷阱）
- `workflow_session.py` 调用方在 `except KeyboardInterrupt` 中 `return None`
- 调用 `run_workflow()` 的上层（`cli.py`）需要处理 `None` 返回值（打印"已中断"并正常退出）

**验收：**
- [ ] 在 workflow 运行中按 Ctrl+C：有 `[workflow] Maker step interrupted` 输出
- [ ] 中断后不留残留 HTTP 连接（provider.shutdown() 被调用）
- [ ] `cli.py` 对 `None` 返回值有处理（不 crash）
- [ ] smoke test 通过（StubProvider 的 shutdown 是 no-op）

**风险：** 中。需要修改 pipelines.py 函数签名，有 regression 风险。在分支上先验证，smoke test 后合并。

---

### SM-T04 — 重试配置 Cherry-pick（可选）

**目标：** 在 `RoleDefaults` 中恢复 `max_retries` 和 `retry_backoff_seconds`

**判断：** 如果 Stage 1 的全量运行中发现 API timeout/transient error 频繁，再做此项；否则跳过。

**输入契约：**
- `src/lme_testing/config.py`（Main 当前版本）

**输出契约：**
```python
@dataclass
class RoleDefaults:
    timeout_seconds: float = 120.0
    batch_size: int = 4
    max_retries: int = 3          # 新增（cherry-pick from master）
    retry_backoff_seconds: float = 2.0  # 新增
```

- `providers.py` 的 MiniMax provider 使用 `max_retries` 和 `retry_backoff_seconds` 做指数退避重试
- StubProvider 忽略这两个字段

**验收：**
- [ ] `config.maker_defaults.max_retries == 3`
- [ ] MiniMax API 调用在 503 时有重试行为（手动测试或 mock）

**风险：** 低（只增加字段，不改变现有行为，默认值等同于之前的隐式行为）

---

### SM-T05 — 合并文档归档 ✅

**目标：** 将合并分析存档到 docs/ ✅

**输出：**
- `docs/archives/20260419_master_merge_strategy.md`（本次分析报告，含 cherry-pick 清单）✅
- `vendor/master-branch/README.md` 更新 cherry-pick 完成状态 ✅（vendor/ 已删除）

**验收：**
- [x] `docs/archives/20260419_master_merge_strategy.md` 存在
- [x] 所有已完成 cherry-pick 打勾

---

## Stage 1 — 真实数据接入

*（延续 Implementation Plan v2.0 的 S1-T01~T05，此处仅列关键更新）*

### S1-T01 — Schema Signal 数据源修复

**状态：✅ DONE（2026-04-19）**
- `validate_schemas.py --output-json` 正常工作
- `runs/schema_validation_latest.json` 存在（370 fixtures，0 failures）
- `compute_governance_signals()` → `schema_signal_source: "real_validation"`
- `test_schema_failure_rate_detects_invalid_fixtures` 测试通过

### S1-T02 — 全量运行数据路径对齐

**状态：✅ DONE（2026-04-19）**
- `docs/architecture/run_directory_structure.md` 存在并更新
- `runs_analyzed = 21 > 0`，`total_rules = 180 ≥ 180`
- `coverage_signals.latest_coverage_percent = 72.78%`

### S1-T03 — Session Snapshot 原子写入

**状态：✅ DONE（2026-04-19）**
所有 `review_session.py` 写入路径均已使用 `atomic_write_json`：
- reviews save: `atomic_write_json` (lines 151-152)
- BDD save: `atomic_write_json` (lines 231-232)
- scripts save: `atomic_write_json` (lines 354-355)
- finalize manifest: `atomic_write_json` (line 409, fixed)
- `_save_manifest`: `atomic_write_json` (line 639, fixed)
- 移除未使用的 `write_json` import

### S1-T03b — Checker 真实稳定性

**状态：❌ BLOCKED — API 可靠性不足**
MiniMax API 连接随机断开，全量 322-case 测量无法完成。参见 S2-T02 findings（v4 retry 改善但未解决）。

### S1-T04 — 全量规则质量基准

**状态：✅ DONE（2026-04-19）**
- 全量 183 条规则 maker + checker 运行完成
- `docs/releases/BASELINE-183-RULES.md` 存在（含12条人工抽查）
- Coverage 数字：72.78%（131/180 fully covered）
- 证据：`evidence/20260419_baseline_full/`（maker/checker summaries + coverage_report + HTML）

### S1-T05 — 状态声明重写

**状态：✅ DONE（2026-04-19）**
- README.md Verification Status 表格已更新（S1.1 ✅, S1.2 ✅）
- README.md 无 "All Phases Complete" 表述
- acceptance.md S1.1/S1.2/S1.5 均标记 COMPLETE

---

## Stage 2 — 基于真实数据的质量提升与执行桥接

### S2-T01 — Maker/Checker Coverage Calibration

**状态：✅ DONE（2026-04-21）**

**目标：** 基于全量 180 条可测试规则的真实 maker/checker 输出，提升覆盖率并确认 prompt 校准边界。

**输入契约：**
- Stage 1 全量 baseline：72.22%/72.78% coverage 区间的真实运行证据
- `artifacts/lme_rules_v2_2/semantic_rules.json`
- maker/checker run artifacts

**输出契约：**
- `docs/planning/s2t01_coverage_analysis.md`
- maker/checker prompt version notes
- v1.5 run artifacts：`runs/maker/20260421T074319Z/`、`runs/checker/20260421T083003Z/`

**验收：**
- [x] 全量 180-rule run 完成
- [x] 覆盖率从 v1.0 72.22% 提升至 v1.5 78.89%
- [x] 剩余 gap 分为 evidence-constrained 与 LLM non-determinism
- [x] 不再把 80% 作为 prompt-only 可保证目标

**自评：** PASS。当前证据基础下 prompt 校准已达到实际天花板；剩余问题需要 richer evidence、stabilization strategy 或真实执行环境。

---

### S2-B1 — audit_trail.py 实现

**状态：✅ DONE（2026-04-21）**

**目标：** 生成 maker → checker → human decision chain 的审计 HTML。

**输出契约：**
- `src/lme_testing/audit_trail.py`
- `review_session.py` finalize path 集成
- `final/audit_trail.html` 输出

**验收：**
- [x] `build_audit_trail(session_dir, output_path) -> dict` 实现
- [x] finalize 时自动生成 audit trail
- [x] 生成失败不阻塞 session finalize

**自评：** PASS。

---

### S2-B2 — case_compare.py 实现

**状态：✅ DONE（2026-04-21）**

**目标：** 在 rewrite 后生成相邻 iteration 的 case 对比 HTML。

**输出契约：**
- `src/lme_testing/case_compare.py`
- `review_session.py` rewrite job 集成
- `iter<N>/rewrite/case_compare.html` 输出

**验收：**
- [x] `build_case_compare(...) -> dict` 实现
- [x] rewrite 后自动生成对比视图
- [x] 生成失败不阻塞 rewrite job

**自评：** PASS。

---

### S2-C1 — Mock API Execution Bridge

**状态：✅ DONE（2026-04-23）**

**目标：** 在真实 LME API/VM 不可用时，提供一个基于 `docs/materials/LME_Matching_Rules_Aug_2022.md` 的 mock API 服务，验证 BDD/script 可以真实调用 API under test。

**为什么现在做：**
- Stage 3 真实 LME API 接入仍阻塞于外部 VM 权限。
- 现有 step library 多为 stub/模拟对象，无法证明脚本通过 HTTP 调用外部测试对象。
- Mock API 可作为受控的 execution bridge，验证从需求文档到 BDD/script 的闭环形态。

**输入契约：**
- `docs/materials/LME_Matching_Rules_Aug_2022.md`
- 已有 maker/checker/BDD/step integration 文档
- 代表性可执行规则：MR-001、MR-002、MR-003、MR-004、MR-007、MR-008、MR-046、MR-064、MR-071、MR-075

**输出契约：**
- `deliverables/lme_mock_api/` 可运行源码
- `deliverables/lme_mock_api.zip` 可下载压缩包
- `docs/planning/mock_api_validation_plan.md`
- BDD feature + Python step definitions + lightweight runner + unittest

**验收：**
- [x] mock API 可本地启动：`python -m mock_lme_api.server --port 8766`
- [x] BDD step definitions 使用 HTTP client 调用 mock API
- [x] `python run_bdd.py` 通过：33 passed, 0 failed
- [x] `python -m unittest tests.test_mock_api` 通过：2 tests OK
- [x] README 和源码包含在 zip 中
- [x] 文档明确 mock bridge 不代表真实 LME API readiness

**不在范围：**
- 不替代 Stage 3 真实 LME API 接入
- 不模拟完整 matching engine、clearing、settlement 或真实 LME connectivity
- 不改变主流水线 artifact schema、prompt、model default

**自评：** PASS。

---

### S2-C2 — Initial Margin HKv13 Mock API Execution Bridge

**状态：✅ DONE（2026-04-26）**

**目标：** 在真实执行环境不可用时，提供一个基于 `Initial Margin Calculation Guide HKv13` 的 mock API 服务，验证 IM HKv13 领域从 governed rules 到 BDD/script 再到 HTTP API under test 的闭环形态。

**为什么现在做：**
- `artifacts/im_hk_v13/` 已存在并通过 schema validation，共 164 条 semantic rules。
- S2-C1 已证明 matching rules 领域的 mock execution bridge 形态可行。
- IM HKv13 是计算指南领域，适合用确定性接口验证脚本可执行性，而不改变主流水线 contract。

**输入契约：**
- `docs/materials/Initial Margin Calculation Guide HKv13.pdf`
- `artifacts/im_hk_v13/semantic_rules.json`
- `artifacts/im_hk_v13/source_from_pdf.md`
- `artifacts/im_hk_v13/validation_report.json`

**输出契约：**
- `deliverables/im_hk_v13_mock_api/` 可运行源码
- `deliverables/im_hk_v13_mock_api.zip` 可下载压缩包
- `docs/planning/im_hk_v13_mock_api_validation_plan.md`
- BDD feature + Python step definitions + lightweight runner + unittest

**实现要点：**
- 独立包 `mock_im_api`，不加入主包 import path。
- 使用确定性小公式覆盖 RPF validation、position normalization、market risk components、MTM split、rounding/aggregation、corporate actions、cross-day netting、cross-currency netting、intraday MTM treatment。
- 不改变 schemas、prompts、provider defaults 或主 pipeline contracts。

**验收：**
- [x] mock API 源码和 README 存在
- [x] BDD step definitions 使用 HTTP client 调用 mock API
- [x] positive/negative scenarios 覆盖代表性 API responses
- [x] `python -m compileall deliverables/im_hk_v13_mock_api` 通过
- [x] `python -m unittest discover -s deliverables\im_hk_v13_mock_api\tests -t deliverables\im_hk_v13_mock_api -v` 通过：4 tests OK；BDD summary 37 passed, 0 failed
- [x] Section 3.2.4.2 Flat Rate Margin POC 覆盖 guide example：`(1,300,000 x 30% + 60,000,000 x 12%) x 2 = 15,180,000`
- [x] 文档明确 mock bridge 不代表真实 Initial Margin execution readiness

**不在范围：**
- 不实现完整 VaR Platform 或生产 Initial Margin engine
- 不替代 Stage 3 真实执行环境接入
- 不把 164 条 semantic rules 全量转换为 executable BDD
- 不改变 artifact schema、prompt、model default

**自评：** PASS。Mock bridge 已独立交付并通过静态编译、HTTP-backed BDD runner 和 unittest discovery；不改变主流水线 schemas、prompts、models 或 artifact contracts。

---

### S2-C3 — Initial Margin HKv14 POC Document Workflow And Modular Mock API Bridge

**状态：✅ DONE（2026-04-26）**

**目标：** 在不覆盖 HKv13 preservation baseline 的前提下，将 `Initial Margin Calculation Guide HKv14` 纳入 governed intake，生成 HKv13→HKv14 deterministic diff evidence，并用 shared common package + thin HKv14 wrapper 验证 mock/stub execution bridge reuse。

**为什么现在做：**
- HKv13 mock API bridge 已完成，可作为 preservation baseline。
- HKv14 PDF input is available under `docs/materials/Initial Margin Calculation Guide HKv14.pdf`.
- The POC needed deterministic diff evidence and a bounded downstream decision note before any wrapper work.

**输入契约：**
- `docs/materials/Initial Margin Calculation Guide HKv14.pdf`
- `artifacts/im_hk_v13/`
- Existing HKv13 mock API behavior as preservation baseline

**输出契约：**
- `artifacts/im_hk_v14/`
- `evidence/im_hk_v14_diff/im_hk_v13_to_v14_diff.json`
- `docs/planning/im_hk_v14_diff_report.md`
- `docs/planning/im_hk_v14_downstream_decision.md`
- `docs/planning/im_hk_v14_mock_api_validation_plan.md`
- `deliverables/im_hk_mock_api_common/`
- `deliverables/im_hk_v14_mock_api/`
- `deliverables/im_hk_v14_mock_api.zip`
- `scripts/compare_initial_margin_versions.py`

**实现要点：**
- `scripts/extract_matching_rules.py` uses `pypdf` as the primary PDF extractor for PDF inputs and writes full extracted `source_from_pdf.md`.
- `scripts/compare_initial_margin_versions.py` compares governed artifact directories generically despite the Initial Margin filename.
- HKv14 wrapper reuses shared code in `deliverables/im_hk_mock_api_common/` instead of rebuilding a separate implementation.
- HKv13 deliverable remains the preservation baseline and must not be overwritten by HKv14 work.

**验收：**
- [x] HKv14 governed artifacts generated: 38 pages, 10 clauses, 164 atomic rules, 164 semantic rules
- [x] Deterministic HKv13→HKv14 diff generated and summarized: 10 changed candidates, 0 added, 0 removed, 1 ID drift candidate, 0 source-anchor warnings
- [x] POC downstream decision note records accepted deterministic candidates
- [x] HKv14 mock API health/rules labels are HKv14-specific while implementation is shared
- [x] HKv14 BDD runner passes included feature steps: 37 passed, 0 failed
- [x] Full unittest discovery passed after package refresh: 193 tests, 1 browser E2E skip when Chrome DevTools unavailable
- [x] Docs and artifact governance checks passed

**不在范围：**
- 不声明 HKv14 downstream automation production-ready
- 不改变 schemas、prompts、default models or roadmap phase boundaries
- 不实现 future role-friendly decision UI
- 不替代 Stage 3 real execution environment

**自评：** PASS。HKv14 POC artifacts, deterministic diff evidence, decision note, shared mock implementation, thin wrapper, tests, and governance checks are present. The work remains explicitly bounded to POC/mock/stub bridge validation.

---

### S2-C4 — Initial Margin HKv14 Promoted Downstream Slice

**状态：✅ DONE（2026-04-26）**

**目标：** Promote HKv14 from POC-only continuation into a governed Stage 2 downstream candidate while preserving HKv13 as the stable baseline.

**为什么现在做：**
- Human project owner explicitly approved promotion.
- S2-C3 produced governed HKv14 artifacts, deterministic diff evidence, decision note, and a thin HKv14 mock wrapper.
- Promotion requires a scoped contract before further implementation.

**输入契约：**
- `docs/planning/im_hk_v14_promotion_scope.md`
- `evidence/im_hk_v14_diff/im_hk_v13_to_v14_diff.json`
- `docs/planning/im_hk_v14_downstream_decision.md`
- `artifacts/im_hk_v14/`
- `deliverables/im_hk_mock_api_common/`
- `deliverables/im_hk_v14_mock_api/`
- `deliverables/im_hk_v13_mock_api/`

**输出契约：**
- `docs/planning/im_hk_v14_downstream_treatment_mapping.md`
- updated `docs/planning/im_hk_v14_mock_api_validation_plan.md`
- updated HKv14 flat-rate validation data/test/BDD label
- refreshed `deliverables/im_hk_v14_mock_api.zip`

**实现要点：**
- First implementation action must be deterministic diff candidate mapping.
- Do not change mock behavior before each accepted diff candidate has a treatment category.
- Keep HKv13 and HKv14 validation runnable side by side.
- Keep schema, prompt, and model impact at none unless a separate governed task is opened.

**验收：**
- [x] 10 changed candidates and 1 ID drift candidate mapped to downstream treatment categories
- [x] Required HKv14-specific BDD/data/test updates identified and applied
- [x] HKv13 deliverable remains preserved
- [x] HKv13 and HKv14 validation commands pass after implementation change
- [x] Docs and artifact governance checks pass

**不在范围：**
- 不声明 HKv14 production downstream automation readiness
- 不替代 Stage 3 real execution environment
- 不改变 schemas、prompts、default models
- 不实现 future role-friendly decision UI

**自评：** PASS. Promotion contract, deterministic treatment mapping, HKv14 validation data refresh, side-by-side HKv13/HKv14 validation, and governance checks are complete. The slice remains bounded to mock/stub downstream baseline candidacy.

---

### S2-C5 — Mock API Deliverables Location Policy

**状态：✅ DONE（2026-04-26）**

**目标：** Decide whether current long-lived mock API samples remain under `deliverables/` or move under a future `samples/` or `tools/` path.

**Decision:** Keep current mock API source folders and packaged zips under `deliverables/` for Stage 2.

**Output contract:**
- `docs/planning/mock_api_deliverables_policy.md`

**Implementation notes:**
- No directories are moved.
- Existing validation commands and zip paths remain stable.
- Revisit before adding a new mock API bridge or promoting mock APIs into maintained internal tooling.

**验收：**
- [x] Human decision captured
- [x] No file move authorized
- [x] Revisit trigger documented
- [x] Schema/prompt/model/artifact-contract impact documented as none

**自评：** PASS.

---

### S2-D1 — Browser-Level Review UI E2E

**状态：✅ DONE（2026-04-23）**

**目标：** 在 manager/API-backend 测试之外，用真实浏览器验证 review-session UI 的 BDD 和 Scripts 主路径。

**为什么现在做：**
- BDD/Scripts tab 的保存逻辑已经开始刷新 governed artifacts，必须验证浏览器层不会丢失 textarea edits 或展示 stale match metrics。
- 该任务属于 UI assurance，不改变 artifact schema、prompt、model default 或新增 LLM stage。

**输入契约：**
- `src/lme_testing/review_session.py`
- `tests/test_review_session.py` 中可复用的 deterministic fixture builder
- 本机可用 Chrome 或 Edge；无浏览器时测试应 skip

**输出契约：**
- `tests/test_review_session_browser.py`
- `docs/planning/ui_test_plan.md` 标记 browser E2E 层已实现
- `requirements.txt` 声明 full test discovery 需要的 `jsonschema>=4.0.0`

**实现要点：**
- 启动真实 local review-session HTTP server。
- 使用纯 stdlib Chrome DevTools Protocol harness 驱动 installed Chrome/Edge；不引入 Playwright/Selenium 依赖。
- 测试使用 deterministic fixture artifacts，不调用 live LLM provider。
- BDD tab dirty-state 保护：未保存 textarea edits 在 tab navigation 后不能被自动 reload 覆盖。

**验收：**
- [x] 浏览器打开 review UI 并完成 Review -> BDD -> Scripts 导航
- [x] BDD textarea 未保存内容在 tab navigation 后保留
- [x] Save BDD Edits 后 Scripts tab 显示 refreshed exact/unmatched metrics
- [x] Save Scripts Edits 后 visible match metrics 更新
- [x] Full unittest discovery 通过：181 tests OK
- [x] Governance baseline checks 通过

**不在范围：**
- 不覆盖 submit/finalize browser flow
- 不引入 hosted/multi-user UI 自动化
- 不改变 review-session artifact contracts

**自评：** PASS。

---

### S2-F1 — HKv14 Role-Friendly Impact Decision Review

**状态：✅ DONE（2026-04-27）**

**目标：** 将 `docs/architecture/Executable_Engineering_Knowledge_Contract.md` 中 "MVP Scope and Delivery Plan" 的 human-control slice 提升为当前 repo 的小范围 governed implementation path。

Approved slice:

```text
Initial Margin HKv13 -> HKv14 -> Deterministic Diff -> Role Review -> Structured Decision Record
```

**为什么现在做：**
- HKv14 deterministic diff、downstream treatment mapping, and mock/stub bridge decision evidence already exist.
- Current HKv14 decision handling is Markdown-based; the proposal requires role-friendly review and structured decisions.
- This slice can improve human review traceability without adding a generic document platform or new LLM stage.

**输入契约：**
- `evidence/im_hk_v14_diff/im_hk_v13_to_v14_diff.json`
- `docs/planning/im_hk_v14_downstream_treatment_mapping.md`
- `artifacts/im_hk_v13/`
- `artifacts/im_hk_v14/`
- `docs/planning/im_hk_v14_role_review_plan.md`

**输出契约：**
- `runs/im_hk_v14/review_decisions/<timestamp>/decision_record.json`
- `runs/im_hk_v14/review_decisions/<timestamp>/decision_summary.md`
- `runs/im_hk_v14/review_decisions/<timestamp>/review.html`
- focused tests for load, save, validation failure, and Markdown export

**实现要点：**
- Keep the decision record JSON canonical; Markdown is derived export only.
- Capture reviewer role, reviewer name, decision, rationale, comments, and timestamp.
- Allowed roles and decisions must be validated deterministically.
- Prefer existing local review-session patterns where practical.
- Use atomic writes for structured decision records.
- Keep deterministic evidence visible.

**验收：**
- [x] Existing HKv13 baseline artifacts and deliverables are untouched
- [x] HKv14 remains POC/mock/stub downstream baseline candidate work
- [x] Every candidate decision links back to deterministic diff evidence or downstream treatment mapping
- [x] Structured decision record validates deterministically
- [x] Markdown summary is derived from structured JSON
- [x] Focused tests cover load, save, validation failure, and export
- [x] Docs and artifact governance checks pass

**不在范围：**
- Generic document upload or document library
- Full workflow engine or role-based permission system
- New LLM-driven stage
- Prompt, schema, or default model changes
- Automatic test case updates or code generation
- Stage 3 real execution readiness claims

**验证：**
- `.venv\Scripts\python.exe -m unittest tests.test_im_hk_v14_role_review -v`: passed, 5 tests OK.
- `.venv\Scripts\python.exe main.py im-hk-v14-role-review --output-dir .tmp_test\s2f1_review --reviewer-name Test --rationale "Planning validation"`: passed, generated 11 candidates.
- `.venv\Scripts\python.exe -m compileall src\lme_testing tests`: passed.

**自评：** PASS. S2-F1 is implemented as a deterministic local review package generator with canonical JSON, derived Markdown, and local HTML review surface. It remains bounded to HKv14 POC/mock/stub decision review.

---

### S2-F2 — MVP Document Readiness Registry

**状态：✅ IMPLEMENTED（2026-04-29）；deterministic package generated**

**目标：** 将 `docs/architecture/Executable_Engineering_Knowledge_Contract.md` 中 "MVP Scope and Delivery Plan" 的 document registration/readiness slice 提升为当前 repo 的小范围 governed implementation path。

Approved slice:

```text
Register MVP documents -> validate metadata/readiness -> produce document_readiness.json
```

**为什么现在做：**
- Full MVP scope starts with registering Function Spec old/new, Test Plan, and Regression Pack Index before any LLM-assisted mapping.
- S2-F1 produced reviewed impact decisions; S2-F2 should make the upstream document set explicit and deterministic.
- A readiness registry gives later MVP work a stable input contract without adding a generic document platform.

**输入契约：**
- `docs/materials/Initial Margin Calculation Guide HKv13.pdf`
- `docs/materials/Initial Margin Calculation Guide HKv14.pdf`
- placeholder entries for Test Plan and Regression Pack Index
- `docs/planning/mvp_document_readiness_plan.md`

**输出契约：**
- `evidence/mvp_document_readiness/<timestamp>/document_readiness.json`
- `evidence/mvp_document_readiness/<timestamp>/document_readiness_summary.md`
- focused tests for valid registry generation, missing source handling, placeholder handling, and validation failure

**实现证据：**
- generator: `src/lme_testing/mvp_document_readiness.py`
- CLI: `python main.py mvp-document-readiness`
- evidence: `evidence/mvp_document_readiness/20260429T075702Z/`
- tests: `tests/test_mvp_document_readiness.py`

**实现要点：**
- Treat Initial Margin HKv13/HKv14 guides as the repo-specific stand-in for the broader proposal's Function Spec old/new pair.
- Record deterministic file existence and content hash for available source files.
- Mark unavailable Test Plan and Regression Pack Index as explicit placeholders or blockers.
- Represent HKv14 superseding HKv13.
- Keep missing inputs visible in `blockers`; do not silently ignore them.

**验收：**
- [x] `document_readiness.json` is generated deterministically
- [x] HKv13 and HKv14 source files are registered with existing-source checks and hashes
- [x] Placeholder Test Plan and Regression Pack Index records are explicit
- [x] Missing inputs are visible in `blockers`
- [x] HKv13 -> HKv14 supersedes relationship is represented
- [x] Deterministic validation rejects unsupported roles/states and ready records with missing sources
- [x] Focused tests cover valid registry generation, missing source handling, placeholder handling, and validation failure
- [x] Docs and artifact governance checks pass

**不在范围：**
- Generic document upload UI
- Document storage platform
- OCR or new parser work
- New LLM-driven stages, summaries, or maker/checker changes
- Requirement-to-test mapping, regression-pack mapping, or automation backlog generation
- JIRA, Zephyr, Git, CI, Confluence, or SharePoint integration
- Stage 3 real execution readiness claims

**自评：** PASS. S2-F2 is implemented as deterministic document readiness registry generation. Workflow readiness intentionally remains `blocked` until real Test Plan and Regression Pack Index inputs are provided.

---

## S2-T02 findings — Checker Instability Measurement（已执行）

**背景：** 在 Stage M 合并完成前进行的探索性测量，为 Stage 2 质量提升提供数据基础。

### 测量过程

| Run | 处理 cases | 失败原因 | Instability |
|-----|-----------|---------|-------------|
| v1 | 14/322 | 静默截断（pipeline 误报 complete） | 71%（14 cases）|
| v2 | 14/64 | 静默截断 + API 404 | — |
| v3 | 63/322 | SSL EOF（batch 64）| 60%（10 comparable）|
| v4 | 121/322（Run A），97/322（Run B）| Retry 改善，Run B 进程中断 | 未产出 stability_report（Run B 中断）|

### 关键发现

1. **Error surfacing fix**（`pipelines.py`）：`batches_processed`/`failed_batch_num` 追踪，异常时报告真实 remaining count
2. **Retry logic**（`providers.py`）：`max_retries=3`，指数退避重试 transient errors（SSL EOF、connection reset、HTTP 5xx）；Run A 从 63→121 batches（+92%）
3. **API 可靠性是根本瓶颈**：连接在 10~121 cases 后随机断开/超时，非代码问题，全量 322-case 测量需 API 稳定性支持
4. **Instability pattern**：delta 主要为 1（噪声），少数 case 有 delta≥2 的 meaningful divergence；无系统性方向偏移

### 对 Stage 2 的影响

- **S2-T01（Maker prompt 改进）**：blocked — checker instability 高（60%+）使 maker 改进价值无法稳定测量
- **S2-T02 本身**：需 API 可靠性解决后才能完成全量测量；当前数据 directionally concerning 但不可靠
- **Retry 作为缓解**：已实现，partial success

### 不在范围内（Stage 1 修复后）

- 全量 322-case instability measurement（依赖 API 稳定性）
- 确认 instability 阈值（10%）：当前 60% 已 >> threshold，但样本小非全量

---

## Stage 2 规划模块（占位，待 Stage 1 后展开）

### S2-B1 — audit_trail.py 实现

**背景：** Master 分支的 review_session.py 引用了 `from .audit_trail import build_audit_trail`，但模块不存在。Main 的 review_session.py 中没有此调用，但功能有价值。

**接口设计（参考 master 的调用方式）：**
```python
def build_audit_trail(session_dir: Path, output_path: Path) -> dict:
    """
    生成审计跟踪 HTML。
    
    输入：session_dir/iterations/<N>/ 下的所有 maker/checker/review 数据
    输出：audit_trail.html（决策链时间线），返回 {"path": str, "rules_count": N}
    """
```

**集成点：**
- `review_session.py` 的 `/api/audit_trail` GET 端点已存在（master 版本有，需确认 main 版本是否有）
- 在 `ReviewSessionManager.finalize()` 时自动调用

**UI 需求：** 每条 rule 一行，显示：maker 输出摘要 → checker 判断（pass/block/reason）→ human 决策（approve/rewrite/reject）→ 最终状态

### S2-B2 — case_compare.py 实现

**背景：** Master 分支引用 `from .case_compare import build_case_compare`，但模块不存在。

**接口设计：**
```python
def build_case_compare(
    session_dir: Path, 
    iteration_a: int, 
    iteration_b: int, 
    output_path: Path
) -> dict:
    """
    生成两个迭代之间的 case 对比 HTML。
    
    用途：rewrite 后查看 case 有何变化
    输出：case_compare.html（并排视图，高亮变化）
    """
```

**触发时机：** 在 `ReviewSessionManager._run_rewrite_job()` 完成后调用（iteration N vs N-1 对比）

**前置：** S2-B1 完成后（共用部分 session 数据读取逻辑）

