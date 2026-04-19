# LME Testing — Implementation Plan v3.0

**修订日期：** 2026-04-19  
**范围：** Stage M（合并）+ Stage 1（真实数据接入）  
**说明：** Stage 2 任务在 Stage 1 完成后、基于真实数据另行制定。

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
```

---

## Stage M — Master 分支合并

### SM-T01 — Vendor 存档

**目标：** 将 master 代码放入 `vendor/` 目录，保留可读性但不影响主路径

**输入契约：**
- master zip 文件

**输出契约：**
- `vendor/master-branch/`（完整 master 代码）
- `vendor/master-branch/README.md`：
  ```markdown
  # Master Branch Snapshot

  同事（CodeFreddy/LME-Testing master branch）的代码快照，存档用途。
  日期：2026-04-19
  
  ## 已 cherry-pick 的改进
  - [ ] SM-T02: UTC 时间戳（storage.py）
  - [ ] SM-T03: Workflow 中断处理（workflow_session.py）
  - [ ] SM-T04: 重试配置（config.py）
  
  ## 识别为 Stage 2 任务的功能
  - audit_trail.py（模块缺失，已记录为 S2-B1）
  - case_compare.py（模块缺失，已记录为 S2-B2）
  
  ## 不合并的内容
  - providers.py（编码损坏，缺 StubProvider）
  - review_session.py（整体，会破坏 BDD tabs）
  - pipelines.py（整体，缺 planner/BDD pipeline）
  
  此目录在所有 cherry-pick 完成后可删除，或保留作历史参考。
  ```
- `.gitignore` 确认 `vendor/` 不被排除（应加入 repo）

**验收：**
- [ ] `vendor/master-branch/lme_testing/review_session.py` 存在
- [ ] `python -c "from lme_testing.storage import timestamp_slug"` 正常（不受 vendor 影响）
- [ ] `vendor/master-branch/README.md` 有 cherry-pick 状态列表

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

### SM-T05 — 合并文档归档

**目标：** 将合并分析存档到 docs/

**输出：**
- `docs/MERGE_STRATEGY.md`（本次分析报告，含 cherry-pick 清单）
- `vendor/master-branch/README.md` 更新 cherry-pick 完成状态

**验收：**
- [ ] `docs/MERGE_STRATEGY.md` 存在
- [ ] vendor README 中所有已完成 cherry-pick 打勾

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

**状态：🔄 IN PROGRESS**
Main 已有 `atomic_write_json()`（SM-T02 保留）。需要确认 `review_session.py` 中所有 snapshot 写入路径（reviews、bdd、scripts）都已使用 `atomic_write_json`。

检查点：
```
diff: review_session.py line 138-139
< write_json(snapshot_path, normalized)
< write_json(latest_path, normalized)
---
> atomic_write_json(snapshot_path, normalized)
> atomic_write_json(latest_path, normalized)
```

### S1-T03b — Checker 真实稳定性

**状态：❌ BLOCKED — API 可靠性不足**
MiniMax API 连接随机断开，全量 322-case 测量无法完成。参见 S2-T02 findings（v4 retry 改善但未解决）。

### S1-T04 — 全量规则质量基准

**状态：❌ BLOCKED — 依赖 S1-T03b 完成**
需要 API 稳定性支持全量 183-rule 运行。

### S1-T05 — 状态声明重写

**状态：✅ DONE（2026-04-19）**
- README.md Verification Status 表格已更新（S1.1 ✅, S1.2 ✅）
- README.md 无 "All Phases Complete" 表述
- acceptance.md S1.1/S1.2/S1.5 均标记 COMPLETE

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
