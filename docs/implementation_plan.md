# LME Testing — Implementation Plan v3.1

**修订日期：** 2026-04-23  
**范围：** Stage M（合并）+ Stage 1（真实数据接入）+ Stage 2 已执行任务  
**说明：** Stage 2 已基于真实数据展开：S2-T01 prompt 校准完成，S2-B1/B2 集成完成，S2-C1 mock API execution bridge 完成，S2-D1 browser-level review UI E2E 完成。

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
└── S2-D1: Browser-level review UI E2E
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
- `lme_testing/storage.py`（Main 当前版本）

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

`docs/run_directory_structure.md` 补充：
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
- `lme_testing/workflow_session.py`（Main 当前版本）
- `lme_testing/pipelines.py`（Main 当前版本）

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
- `lme_testing/config.py`（Main 当前版本）

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
- `docs/MERGE_STRATEGY.md`（本次分析报告，含 cherry-pick 清单）✅
- `vendor/master-branch/README.md` 更新 cherry-pick 完成状态 ✅（vendor/ 已删除）

**验收：**
- [x] `docs/MERGE_STRATEGY.md` 存在
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
- `docs/run_directory_structure.md` 存在并更新
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
- `docs/s2t01_coverage_analysis.md`
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
- `lme_testing/audit_trail.py`
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
- `lme_testing/case_compare.py`
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
- `docs/mock_api_validation_plan.md`
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

### S2-D1 — Browser-Level Review UI E2E

**状态：✅ DONE（2026-04-23）**

**目标：** 在 manager/API-backend 测试之外，用真实浏览器验证 review-session UI 的 BDD 和 Scripts 主路径。

**为什么现在做：**
- BDD/Scripts tab 的保存逻辑已经开始刷新 governed artifacts，必须验证浏览器层不会丢失 textarea edits 或展示 stale match metrics。
- 该任务属于 UI assurance，不改变 artifact schema、prompt、model default 或新增 LLM stage。

**输入契约：**
- `lme_testing/review_session.py`
- `tests/test_review_session.py` 中可复用的 deterministic fixture builder
- 本机可用 Chrome 或 Edge；无浏览器时测试应 skip

**输出契约：**
- `tests/test_review_session_browser.py`
- `docs/ui_test_plan.md` 标记 browser E2E 层已实现
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
