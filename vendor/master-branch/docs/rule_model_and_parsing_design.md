# LME 文本拆分、`atomic_rule` 与 `semantic_rule` 设计说明

## 1. 目的

本文档面向接手本项目的开发人员，说明以下内容：

- 为什么需要先做文本拆分，再做规则解析
- `atomic_rule` 和 `semantic_rule` 的职责边界
- 文本拆分脚本的设计原则
- `semantic_rule` 的正式字段清单与字段含义
- 每一种 `rule_type` 的独有字段说明
- 每一种 `rule_type` 的示例

这份文档是当前仓库中关于规则建模的主说明文档。

## 2. 总体处理链路

针对 LME 官方文档，建议固定采用如下流水线：

`PDF -> pages -> clauses -> atomic_rule -> semantic_rule -> Gherkin/DSL -> review -> coverage`

为什么不能让大模型直接从 PDF 生成测试案例：

- 覆盖率分母不稳定
- 追溯关系会丢
- 文档与测试案例之间没有中间事实层
- 双模型审核时难以判断到底是拆分错了还是语义理解错了

## 3. 两层规则模型

### 3.1 `atomic_rule`

`atomic_rule` 是文档事实层的最小规则单元。

主要职责：

- 作为覆盖率分母候选
- 作为文档追溯锚点
- 作为人工抽检对象
- 作为后续 `semantic_rule` 的输入

设计原则：

- 尽量由脚本稳定生成
- 尽量少解释业务语义
- 允许保守、允许偏粗，但必须可回溯

### 3.2 `semantic_rule`

`semantic_rule` 是语义层和半执行层。

主要职责：

- 生成 Gherkin/BDD 场景
- 生成结构化测试 DSL/YAML/JSON
- 作为模型审核输入
- 承载证据、推断、歧义、测试提示

设计原则：

- 每条 `semantic_rule` 必须来源于一个或多个 `atomic_rule`
- 允许规范化，但必须标明 `source_type`
- 每条规则必须带 `evidence`
- 对未来可执行测试保持足够接近，但不直接等于测试脚本

## 4. 文本拆分设计

### 4.1 拆分层级

固定为 4 层：

1. `document`
2. `section`
3. `clause`
4. `atomic_rule`

说明：

- `document` 是整本文档元数据
- `section` 是章节标题，例如 `Give-Ups`
- `clause` 是显式条款，例如 `46.`
- `atomic_rule` 是覆盖率与测试映射的最小规则单元

### 4.2 `clause` 的切分规则

主条款按显式编号切分，例如：

- `1.`
- `14.`
- `46.`

拆分过程应由脚本完成，而不是交给大模型。

原因：

- 切分结果必须稳定
- 同一文档每次执行应得到相同的条款边界
- 后续换模型时覆盖率口径不能漂移

### 4.3 `atomic_rule` 的切分规则

一条 `atomic_rule` 应只表达一个可判断的规范命题。

必须拆分的典型情况：

- 同一条款中出现多个独立 `must / must not / may / shall / will`
- 同时出现义务和禁止
- 同时出现多个时间要求
- 子条款 `(a)(b)(c)` 语义独立
- 罗马编号 `(i)(ii)(iii)` 语义独立
- 同一条款里定义多个枚举值

不建议拆分的情况：

- 只是背景或解释
- 只是补充短语，不能独立判定
- 只是示例

## 5. `atomic_rule` 字段说明

当前脚本产出的 `atomic_rule` 采用以下关键字段：

### `rule_id`

稳定规则 ID。

示例：

- `MR-046-01`
- `MR-052-A-1`

### `clause_id`

所属主条款 ID。

示例：

- `MR-046`

### `clause_number`

文档原始条款编号。

### `section`

所属章节。

示例：

- `Give-Ups`

### `start_page` / `end_page`

原文起止页码。

### `rule_type`

脚本层的初始分类猜测。

注意：

- 只是初判
- 不是最终语义结论

### `testability`

脚本层的初始可测性判断。

### `split_basis`

说明该规则是如何拆出来的。

示例：

- `sentence`
- `subclause:A`
- `subclause:B`

### `raw_text`

该规则对应的原始文本片段。

这是后续 `semantic_rule.evidence` 的重要基础。

## 6. `semantic_rule` 顶层通用字段

顶层通用字段只解释一次，各 `rule_type` 示例默认都复用这些定义。

### `semantic_rule_id`

语义规则层主键。

推荐格式：

- `SR-MR-046-03`
- `SR-MR-052-AB`

### `version`

`semantic_rule` schema 版本。

当前建议固定为：

- `1.0`

### `source`

来源追溯信息。

字段：

- `doc_id`
- `doc_title`
- `doc_version`
- `section`
- `clause_refs`
- `atomic_rule_ids`
- `pages`

作用：

- 文档追溯
- 覆盖率统计
- 人工抽检

### `classification`

规则分类与覆盖率元数据。

字段：

- `rule_type`
- `rule_tags`
- `testability`
- `priority`
- `coverage_eligible`

### `statement`

语义主体。

字段：

- `actor`
- `action`
- `object`
- `conditions`
- `constraints`
- `outcome`
- `exceptions`

建议理解方式：

- `conditions` 是“规则在什么前提下生效”
- `constraints` 是“字段或值必须满足什么限制”
- `outcome` 是“期望结果是什么”

### `execution_mapping`

连接到未来可执行测试层的桥接字段。

字段：

- `business_inputs`
- `observable_outputs`
- `system_events`
- `preconditions_for_execution`
- `postconditions_for_execution`
- `dsl_assertions`

这部分服务两个目标：

- 生成 Gherkin
- 生成结构化测试 DSL

### `evidence`

证据列表。

每条证据至少包含：

- `target`
- `quote`
- `page`
- `atomic_rule_id`

### `review`

审核元数据。

字段：

- `confidence`
- `inference_flags`
- `ambiguities`

### `test_design_hints`

测试设计辅助信息。

字段：

- `gherkin_intent`
- `positive_scenarios`
- `negative_scenarios`
- `boundary_scenarios`
- `data_requirements`
- `oracle_notes`

## 7. 关键枚举值

### `rule_type`

正式枚举：

- `obligation`
- `prohibition`
- `permission`
- `deadline`
- `state_transition`
- `data_constraint`
- `enum_definition`
- `workflow`
- `calculation`
- `reference_only`

### `testability`

- `testable`
- `partially_testable`
- `ambiguous`
- `non_testable`

### `priority`

- `critical`
- `high`
- `medium`
- `low`

### `source_type`

- `explicit`
- `normalized`
- `inferred`

## 8. 各 `rule_type` 的独有字段与示例

### 8.1 `obligation`

含义：

- 文档要求主体必须执行某个动作

独有字段：

- `type_payload.obligation.mode`
- `type_payload.obligation.fulfillment`

示例：

```json
{
  "classification": {
    "rule_type": "obligation"
  },
  "statement": {
    "actor": {"value": "member", "source_type": "normalized"},
    "action": {"value": "retain_audit_trail", "source_type": "normalized"},
    "object": {"value": "orders_trades_post_trade_operations", "source_type": "normalized"}
  },
  "type_payload": {
    "obligation": {
      "mode": "must",
      "fulfillment": "required"
    }
  }
}
```

### 8.2 `prohibition`

含义：

- 文档明确禁止某种行为

独有字段：

- `type_payload.prohibition.mode`
- `type_payload.prohibition.scope`

示例：

```json
{
  "classification": {
    "rule_type": "prohibition"
  },
  "statement": {
    "actor": {"value": "member", "source_type": "normalized"},
    "action": {"value": "submit_give_up_trade", "source_type": "normalized"},
    "object": {"value": "give_up_trade", "source_type": "normalized"}
  },
  "type_payload": {
    "prohibition": {
      "mode": "must_not",
      "scope": "submission"
    }
  }
}
```

### 8.3 `permission`

含义：

- 文档允许某种行为，但不是义务

独有字段：

- `type_payload.permission.mode`
- `type_payload.permission.optional`

示例：

```json
{
  "classification": {
    "rule_type": "permission"
  },
  "statement": {
    "actor": {"value": "executing_member", "source_type": "normalized"},
    "action": {"value": "register_executor_half_directly", "source_type": "normalized"},
    "object": {"value": "give_up_clearer", "source_type": "normalized"}
  },
  "type_payload": {
    "permission": {
      "mode": "may",
      "optional": true
    }
  }
}
```

### 8.4 `deadline`

含义：

- 文档规定了时间截止条件

独有字段：

- `type_payload.deadline.deadline_kind`
- `type_payload.deadline.reference_event`
- `type_payload.deadline.offset_iso8601`
- `type_payload.deadline.absolute_time_local`
- `type_payload.deadline.timezone`
- `type_payload.deadline.business_day_offset`
- `type_payload.deadline.breach_outcome`

示例：

```json
{
  "classification": {
    "rule_type": "deadline"
  },
  "statement": {
    "actor": {"value": "executing_member", "source_type": "normalized"},
    "action": {"value": "enter_trade_half", "source_type": "normalized"},
    "object": {"value": "give_up_executor_trade_half", "source_type": "normalized"}
  },
  "type_payload": {
    "deadline": {
      "deadline_kind": "relative",
      "reference_event": "client_order_execution",
      "offset_iso8601": "PT10M",
      "absolute_time_local": null,
      "timezone": "Europe/London",
      "business_day_offset": 0,
      "breach_outcome": "late_submission"
    }
  }
}
```

### 8.5 `state_transition`

含义：

- 文档要求或描述系统状态变化

独有字段：

- `type_payload.state_transition.trigger_event`
- `type_payload.state_transition.from_state`
- `type_payload.state_transition.to_state`
- `type_payload.state_transition.automatic`

示例：

```json
{
  "classification": {
    "rule_type": "state_transition"
  },
  "statement": {
    "actor": {"value": "matching_system", "source_type": "normalized"},
    "action": {"value": "generate_trade_half", "source_type": "normalized"},
    "object": {"value": "give_up_clearer_trade_half", "source_type": "normalized"}
  },
  "type_payload": {
    "state_transition": {
      "trigger_event": "give_up_executor_trade_half_submitted",
      "from_state": "submitted",
      "to_state": "clearer_half_generated",
      "automatic": true
    }
  }
}
```

### 8.6 `data_constraint`

含义：

- 针对字段值、格式、允许范围的约束

独有字段：

- `type_payload.data_constraint.field`
- `type_payload.data_constraint.constraint_kind`
- `type_payload.data_constraint.format`
- `type_payload.data_constraint.allowed_values`
- `type_payload.data_constraint.applies_when`

示例：

```json
{
  "classification": {
    "rule_type": "data_constraint"
  },
  "statement": {
    "conditions": [
      {
        "id": "C1",
        "kind": "field",
        "field": "venue_code",
        "operator": "equals",
        "value": "Inter-office",
        "source_type": "explicit"
      }
    ],
    "constraints": [
      {
        "id": "K1",
        "field": "trade_time",
        "operator": "matches_format",
        "value": "HH:MM:SS",
        "source_type": "explicit"
      }
    ]
  },
  "type_payload": {
    "data_constraint": {
      "field": "trade_time",
      "constraint_kind": "format",
      "format": "HH:MM:SS",
      "allowed_values": [],
      "applies_when": ["venue_code=Inter-office"]
    }
  }
}
```

### 8.7 `enum_definition`

含义：

- 定义规则词典中的代码值、账户值、价格类型等

独有字段：

- `type_payload.enum_definition.field`
- `type_payload.enum_definition.value`
- `type_payload.enum_definition.meaning`
- `type_payload.enum_definition.applies_to`

示例：

```json
{
  "classification": {
    "rule_type": "enum_definition"
  },
  "statement": {
    "action": {"value": "define_enum_value", "source_type": "normalized"},
    "object": {"value": "venue_code", "source_type": "normalized"}
  },
  "type_payload": {
    "enum_definition": {
      "field": "venue_code",
      "value": "Inter-office",
      "meaning": "all other business agreed non-electronically",
      "applies_to": ["agreed_trade"]
    }
  }
}
```

### 8.8 `workflow`

含义：

- 文档定义了多分支、多步骤流程

独有字段：

- `type_payload.workflow.trigger`
- `type_payload.workflow.branches`
- `branch_id`
- `branch_condition`
- `steps`

示例：

```json
{
  "classification": {
    "rule_type": "workflow"
  },
  "type_payload": {
    "workflow": {
      "trigger": "clearer becomes known after UNA flow",
      "branches": [
        {
          "branch_id": "A",
          "branch_condition": "cancel_cleared_trade_path",
          "steps": [
            "cancel_system_generated_cleared_trade",
            "submit_executor_half_with_known_clearer"
          ]
        },
        {
          "branch_id": "B",
          "branch_condition": "reverse_original_executor_half_path",
          "steps": [
            "reverse_original_executor_half",
            "submit_executor_half_with_known_clearer"
          ]
        }
      ]
    }
  }
}
```

### 8.9 `calculation`

含义：

- 文档中存在公式、均值、替换、衍生值计算

独有字段：

- `type_payload.calculation.calculation_kind`
- `type_payload.calculation.inputs`
- `type_payload.calculation.formula_description`
- `type_payload.calculation.rounding_rule`

示例：

```json
{
  "classification": {
    "rule_type": "calculation"
  },
  "type_payload": {
    "calculation": {
      "calculation_kind": "substitution",
      "inputs": ["short_price_code", "published_absolute_value"],
      "formula_description": "substitute correct price and calculate absolute values for differential legs",
      "rounding_rule": null
    }
  }
}
```

### 8.10 `reference_only`

含义：

- 仅作为说明、背景或上下文保留，不直接生成测试

独有字段：

- `type_payload.reference_only.reason`

示例：

```json
{
  "classification": {
    "rule_type": "reference_only",
    "testability": "non_testable",
    "coverage_eligible": false
  },
  "type_payload": {
    "reference_only": {
      "reason": "contextual_explanation_only"
    }
  }
}
```

## 9. `semantic_rule` 与测试生成的关系

生成 Gherkin 时建议主要依赖：

- `statement`
- `execution_mapping`
- `test_design_hints`
- `evidence`

建议的映射方式：

- `Given` <- `conditions` 和 `preconditions_for_execution`
- `When` <- `actor + action + object`
- `Then` <- `outcome + observable_outputs + dsl_assertions`

生成结构化 DSL 时建议主要依赖：

- `business_inputs`
- `observable_outputs`
- `system_events`
- `dsl_assertions`

## 10. 开发建议

- 不要让大模型决定文本怎么切
- 不要省略 `evidence`
- 不要把 `source_type=inferred` 当成高置信事实
- 不要把 `reference_only` 纳入可测覆盖率分母
- 建议先稳定 `atomic_rule`，再做 `semantic_rule`

## 11. 相关文件

- 规则抽取脚本：[extract_matching_rules.py](/F:/Develop/python/LME-Testing/scripts/extract_matching_rules.py)
- 脚本说明文档：[rule_extraction_script_guide.md](/F:/Develop/python/LME-Testing/docs/rule_extraction_script_guide.md)
