# LME Testing — Master 分支合并策略

**分析日期：** 2026-04-19  
**分析对象：** `LME-Testing-main`（你的版本）vs `LME-Testing-master`（同事版本）  
**GitHub：** https://github.com/CodeFreddy/LME-Testing

---

## 一、结构对比结论

**Master 是 Main 的完整子集。** Master 没有任何 Main 不具备的文件。

| 维度 | Main | Master |
|------|------|--------|
| 总文件数 | ~130 | ~60 |
| `lme_testing/` 模块数 | 18 | 9 |
| `schemas/` | 7 套 schema + fixtures | 0 |
| `tests/` | 15 个测试文件 | 4 个测试文件 |
| `scripts/` | 14 个治理脚本 | 2 个提取脚本 |
| `docs/` | 20+ 文档 | 4 个文档 |
| CI/CD | 完整 `.github/workflows/` | 无 |
| Oracle 模块 | 8 个 | 0 |
| Governance signals | 完整 | 无 |
| BDD 层 | 完整（`bdd_export.py`、normalized_bdd schema）| 无 |

---

## 二、Master 独有代码价值分析

虽然 Master 是子集，但其共有文件中有若干改进值得 cherry-pick：

### ✅ 有价值，应合并进 Main

**1. `storage.py` — UTC 时间戳（更规范）**

Master 使用 `datetime.now(UTC)` 产出 `20260413T120000Z` 格式，Main 使用本地时间。UTC 时间戳在跨时区协作时更可靠。

```python
# Master 版（更好）
from datetime import UTC, datetime
def timestamp_slug() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
```

合并方式：**直接替换 Main 的 timestamp_slug，保留 Main 的 atomic_write_json**

---

**2. `workflow_session.py` — KeyboardInterrupt 中断处理 + 进度输出**

Master 在 maker/checker 步骤上增加了 `try/except KeyboardInterrupt` + `provider.shutdown()` 和 `[workflow] Step N/4:` 进度打印，Main 没有这些。这对长时间 API 调用的用户体验影响显著。

```python
# Master 版（Main 缺失）
try:
    maker_summary = run_maker_pipeline(...)
except KeyboardInterrupt:
    print("[workflow] Maker step interrupted — aborting.", flush=True)
    for p in provider_out: p.shutdown()
    return None
```

合并方式：**将 master 的 workflow_session.py 中 KeyboardInterrupt 部分 cherry-pick 进 main**

---

**3. `config.py` — `max_retries` 和 `retry_backoff_seconds` 字段**

Master 的 `RoleDefaults` 有重试配置，Main 移除了这两个字段。对 API 调用稳定性有帮助。

```python
# Master 版（Main 缺失）
max_retries: int = 3
retry_backoff_seconds: float = 2.0
```

合并方式：**在 Main 的 RoleDefaults 中重新加入这两个字段**

---

**4. `review_session.py` — Audit Trail 概念（但模块缺失，是 broken state）**

Master 引用了 `from .audit_trail import build_audit_trail` 和 `from .case_compare import build_case_compare`，但这两个模块**在 master 中根本不存在**。Master 的 review_session.py 在当前状态下**无法运行**。

这两个模块是好想法（审计跟踪、case 对比视图），但需要从头实现。

合并方式：**不直接合并 master 的 review_session.py（会破坏 main 的 BDD 功能）**  
**将 audit_trail 和 case_compare 列为 Stage 2 新增模块任务**

---

### ⚠️ 有差异，需要评估

**5. `semantic_rules.json` — Main 有 `paragraph_ids`，Master 没有**

两者都有 183 条规则，但 Main 的 source 字段中有 `paragraph_ids`（traceability anchor），Master 没有。**Main 的版本更完整，应以 Main 为准。**

**6. `providers.py` — Master 有编码损坏（??? 乱码）**

Master 的 providers.py 中文注释显示为 `?????`，是 Windows 编码问题导致的 UTF-8 损坏。代码也只有 135 行，缺少 StubProvider。**以 Main 为准，不合并。**

---

### ❌ 不合并

| Master 内容 | 原因 |
|------------|------|
| `providers.py`（135行旧版） | 编码损坏，缺少 StubProvider |
| `pipelines.py`（639行旧版） | 缺少 planner/BDD pipeline |
| `review_session.py` 的 BDD 路由移除 | Main 的 BDD tab 是主要新功能 |
| `prompts.py`（无版本号） | Main 有完整版本控制 |

---

## 三、合并执行方案

### 步骤 1：将 Master 放入 Main 的 `vendor/` 目录

```
LME-Testing-main/
└── vendor/
    └── master-branch/      ← 完整解压 master zip 到此目录
        ├── lme_testing/
        ├── scripts/
        └── ...
```

作用：保留 master 代码可读性，便于后续 cherry-pick，不污染主代码路径。

**`vendor/master-branch/README.md`** 内容：
```
此目录为同事（CodeFreddy/LME-Testing master 分支）的代码快照，存档用途。
不参与任何 import 路径。
Cherry-pick 完成后可删除，或保留作为历史参考。
```

---

### 步骤 2：Cherry-pick 4 项改进

按优先级：

**P1（立即做，低风险）**

```bash
# storage.py: 替换 timestamp_slug 为 UTC 版本
# 保留 Main 的 atomic_write_json
```

**P2（本周内，中风险）**

```bash
# workflow_session.py: 添加 KeyboardInterrupt 处理和进度输出
# 需要同时更新 run_maker_pipeline/run_checker_pipeline 的函数签名加 provider_out 参数
```

**P3（可选）**

```bash
# config.py: 在 RoleDefaults 中重新加入 max_retries 和 retry_backoff_seconds
```

---

### 步骤 3：实现 Master 中 broken 的两个缺失模块（新增任务）

- `lme_testing/audit_trail.py` — 生成审计跟踪 HTML（记录 maker → checker → human review 的完整决策链）
- `lme_testing/case_compare.py` — 生成 case 对比视图（同一 rule 的多次迭代对比）

这两个模块是好功能，应纳入 Stage 2 任务。

---

### 步骤 4：同步 `docs/` 文档体系

Master 的 `docs/` 只有 4 个文档，Main 有 20+。不存在合并冲突，Main 文档体系完整保留。

---

## 四、风险评估

| 风险 | 等级 | 缓解 |
|------|------|------|
| timestamp_slug 改为 UTC 导致历史 run 目录排序混乱 | 低 | 新格式有 `Z` 后缀可区分；历史目录不受影响 |
| workflow_session.py cherry-pick 破坏现有 BDD 路径 | 中 | 先在分支上测试，smoke test 验证 |
| audit_trail/case_compare 实现中引入 review_session.py 回归 | 中 | 作为独立模块实现，不修改 review_session.py 主逻辑 |

---

## 五、合并完成检查清单

- [x] `vendor/master-branch/` 目录创建并解压
- [x] `vendor/master-branch/README.md` 存在
- [x] `storage.py` timestamp_slug 改为 UTC
- [x] `storage.py` atomic_write_json 保留
- [x] `workflow_session.py` 加入 KeyboardInterrupt + 进度输出
- [x] `config.py` 加入 max_retries 和 retry_backoff_seconds
- [x] CI smoke test 在合并后通过
- [x] `MERGE_STRATEGY.md` 存档到 `docs/archives/` 目录
- [x] `docs/stage2_planned_modules.md` 创建（audit_trail + case_compare 需求文档化）
