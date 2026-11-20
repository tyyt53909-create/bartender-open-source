# 结构化依赖与门槛视图

由 coordination/tasks.json 生成。ALL 表示全部，ANY 表示任一分支满足；表达式保留替代路径。保守环检查遍历所有可能边，不代表所有备选都成为运行前置。路线、资源和时长未确定时，不生成虚构的数值关键路径。

## 任务直接依赖

| 任务 | 直接依赖 | 额外 gate |
|---|---|---|
| OPS-01 | — | — |
| OPS-02 | OPS-01 | — |
| OPS-03 | OPS-01 | — |
| OPS-04 | OPS-01 | — |
| OPS-05 | OPS-02, OPS-03, OPS-04 | — |
| OPS-06 | OPS-02, OPS-03, OPS-04 | — |
| OPS-07 | OPS-03, OPS-04 | at_least_one_runner_ready |
| OPS-08 | OPS-01, OPS-03, OPS-04 | — |
| APP-01 | OPS-01 | — |
| APP-02 | OPS-02, OPS-03 | — |
| APP-03 | APP-01, APP-02 | M0_BASELINE_VERIFIED |
| APP-04 | APP-01, APP-03 | — |
| APP-05 | APP-04 | host_macos_26 |
| APP-06 | APP-04 | host_macos_26 |
| APP-07 | APP-04 | host_macos_27 |
| APP-08 | APP-04 | M1_ROUTE_EVIDENCE_READY |
| APP-09 | APP-01 | — |
| APP-10 | APP-01, APP-09 | — |
| APP-11 | APP-01 | — |
| APP-12 | APP-01, APP-02 | M0_BASELINE_VERIFIED |
| APP-13 | APP-01, APP-02 | M0_BASELINE_VERIFIED |
| APP-14 | APP-09, APP-13 | — |
| APP-15 | APP-04, APP-08, APP-09 | M1_PRODUCT_GATE_PASSED |
| APP-16 | APP-08, APP-10, APP-12 | M1_PRODUCT_GATE_PASSED |
| APP-17 | OPS-08, APP-10, APP-11, APP-13, APP-14, APP-15, APP-16 | — |
| APP-18 | APP-17 | — |
| APP-19 | APP-17, APP-18 | — |
| APP-20 | APP-17, APP-18 | — |
| APP-21 | APP-11, APP-17, APP-18 | — |
| APP-22 | APP-13, APP-14, APP-17, APP-18, APP-25 | — |
| APP-23 | OPS-08, APP-19, APP-20, APP-21, APP-22, APP-26 | M3_PRODUCT_GATE_PASSED |
| APP-24 | APP-23 | pilot_participation_authorized |
| APP-25 | APP-13, APP-14, APP-18 | — |
| APP-26 | APP-18, APP-19, APP-20, APP-21 | — |

## 门槛表达式

### at_least_one_runner_ready

至少一条已验收且当前能力证据有效的 CLI 适配器；不能只看任务 accepted。

消费方：OPS-07, gate:automation_runtime_ready。

```json
{
  "expression": {
    "any_of": [
      {
        "all_of": [
          {
            "kind": "task_accepted",
            "task_id": "OPS-05"
          },
          {
            "kind": "evidence_condition",
            "name": "codex_runner_verified",
            "requires_bound_artifacts": true
          }
        ]
      },
      {
        "all_of": [
          {
            "kind": "task_accepted",
            "task_id": "OPS-06"
          },
          {
            "kind": "evidence_condition",
            "name": "opencode_runner_verified",
            "requires_bound_artifacts": true
          }
        ]
      }
    ]
  },
  "policy": {
    "decision_required": true,
    "permitted_source_tasks": [
      "OPS-05",
      "OPS-06"
    ],
    "issuer_roles": [
      "reviewer",
      "lead"
    ],
    "require_independent_run": true,
    "required_bindings": [
      "source",
      "scope",
      "context"
    ],
    "decision_owner_tasks": [
      "OPS-05",
      "OPS-06"
    ],
    "condition_source_tasks": {
      "codex_runner_verified": [
        "OPS-05"
      ],
      "opencode_runner_verified": [
        "OPS-06"
      ]
    }
  }
}
```

### M0_BASELINE_VERIFIED



消费方：APP-03, APP-12, APP-13。

```json
{
  "expression": {
    "all_of": [
      {
        "kind": "task_accepted",
        "task_id": "APP-02"
      },
      {
        "kind": "evidence_condition",
        "name": "selected_mac_baseline_verified",
        "requires_bound_artifacts": true
      }
    ]
  },
  "policy": {
    "decision_required": true,
    "permitted_source_tasks": [
      "APP-02"
    ],
    "issuer_roles": [
      "reviewer",
      "lead"
    ],
    "require_independent_run": true,
    "required_bindings": [
      "source",
      "scope",
      "context"
    ],
    "decision_owner_tasks": [
      "APP-02"
    ]
  }
}
```

### M1_ROUTE_EVIDENCE_READY

{"all_of": ["APP-04 accepted", "at least one candidate has a matching baseline and complete raw evidence, including failures"], "any_of": ["APP-05 accepted with complete experimental report", "APP-06 accepted with complete experimental report", "APP-07 accepted with complete experimental report"], "rules": ["此 gate 只允许独立审查开始，不表示访问路线已合格；完整失败报告也可满足", "单个实验任务 accepted 可以表示研究完整但结果失败；只有 capability verdict verified 才满足路线条件", "同一 OS 可组合互补访问能力，组合路线必须独立跑完整任务而不能仅拼接各动作分数", "未选择或无硬件路线保持 blocked/not_run/excluded，不增加通过数"]}

消费方：APP-08。

```json
{
  "expression": {
    "all_of": [
      {
        "kind": "task_accepted",
        "task_id": "APP-04"
      },
      {
        "any_of": [
          {
            "kind": "task_accepted",
            "task_id": "APP-05"
          },
          {
            "kind": "task_accepted",
            "task_id": "APP-06"
          },
          {
            "kind": "task_accepted",
            "task_id": "APP-07"
          }
        ]
      },
      {
        "kind": "evidence_condition",
        "name": "complete_selected_route_research_with_matching_baseline",
        "requires_bound_artifacts": true
      }
    ],
    "negative_research_is_eligible": true
  },
  "policy": {
    "decision_required": true,
    "permitted_source_tasks": [
      "APP-05",
      "APP-06",
      "APP-07"
    ],
    "issuer_roles": [
      "reviewer",
      "lead"
    ],
    "require_independent_run": true,
    "required_bindings": [
      "source",
      "scope",
      "context"
    ],
    "decision_owner_tasks": [
      "APP-05",
      "APP-06",
      "APP-07"
    ]
  }
}
```

### M1_PRODUCT_GATE_PASSED

{"all_of": ["APP-08 accepted", "at least one declared target route verified for core notch/capacity task", "no unresolved wrong-target/input/system-state/user-modification integrity failure in declared route"]}

消费方：APP-15, APP-16。

```json
{
  "expression": {
    "all_of": [
      {
        "kind": "task_accepted",
        "task_id": "APP-08"
      },
      {
        "kind": "evidence_condition",
        "name": "at_least_one_declared_route_verified_for_core_notch_task",
        "requires_bound_artifacts": true
      },
      {
        "kind": "evidence_condition",
        "name": "no_unresolved_integrity_blocker_in_declared_route",
        "requires_bound_artifacts": true
      }
    ]
  },
  "policy": {
    "decision_required": true,
    "permitted_source_tasks": [
      "APP-08"
    ],
    "issuer_roles": [
      "reviewer",
      "lead"
    ],
    "require_independent_run": true,
    "required_bindings": [
      "source",
      "scope",
      "context"
    ],
    "decision_owner_tasks": [
      "APP-08"
    ]
  }
}
```

### M3_PRODUCT_GATE_PASSED

APP-26 汇总同一候选/支持范围/环境上的 M3 证据，独立签发正面裁决；所有必测项通过且无 P0。

消费方：APP-23。

```json
{
  "expression": {
    "all_of": [
      {
        "kind": "task_accepted",
        "task_id": "APP-26"
      },
      {
        "kind": "task_accepted",
        "task_id": "APP-18"
      },
      {
        "kind": "task_accepted",
        "task_id": "APP-19"
      },
      {
        "kind": "task_accepted",
        "task_id": "APP-20"
      },
      {
        "kind": "task_accepted",
        "task_id": "APP-21"
      },
      {
        "kind": "evidence_condition",
        "name": "all_mandatory_scope_outcomes_passed",
        "requires_bound_artifacts": true
      },
      {
        "kind": "evidence_condition",
        "name": "no_open_p0_blocker",
        "requires_bound_artifacts": true
      }
    ]
  },
  "policy": {
    "decision_required": true,
    "permitted_source_tasks": [
      "APP-26"
    ],
    "issuer_roles": [
      "reviewer",
      "lead"
    ],
    "require_independent_run": true,
    "required_bindings": [
      "source",
      "scope",
      "context"
    ],
    "decision_owner_tasks": [
      "APP-26"
    ],
    "required_subject_tasks": [
      "APP-18",
      "APP-19",
      "APP-20",
      "APP-21"
    ]
  }
}
```

### host_macos_26



消费方：APP-05, APP-06。

```json
{
  "expression": {
    "kind": "host_attribute",
    "attribute": "os_major",
    "equals": 26
  },
  "policy": {
    "decision_required": false,
    "permitted_source_tasks": [],
    "issuer_roles": [],
    "require_independent_run": false,
    "required_bindings": [],
    "decision_owner_tasks": []
  }
}
```

### host_macos_27



消费方：APP-07。

```json
{
  "expression": {
    "kind": "host_attribute",
    "attribute": "os_major",
    "equals": 27
  },
  "policy": {
    "decision_required": false,
    "permitted_source_tasks": [],
    "issuer_roles": [],
    "require_independent_run": false,
    "required_bindings": [],
    "decision_owner_tasks": []
  }
}
```

### pilot_participation_authorized



消费方：APP-24。

```json
{
  "expression": {
    "kind": "authority_condition",
    "name": "pilot_participation_authorized"
  },
  "policy": {
    "decision_required": false,
    "permitted_source_tasks": [],
    "issuer_roles": [],
    "require_independent_run": false,
    "required_bindings": [],
    "decision_owner_tasks": []
  }
}
```

### automation_runtime_ready

仅决定是否启用自动调度；OPS-07 与至少一条实际执行器及租约/取消证据齐全。人工 bootstrap 不依赖它。

消费方：policy:deployment.activation_gate。

```json
{
  "expression": {
    "all_of": [
      {
        "kind": "task_accepted",
        "task_id": "OPS-07"
      },
      {
        "kind": "gate_ref",
        "gate_id": "at_least_one_runner_ready"
      },
      {
        "kind": "evidence_condition",
        "name": "scheduler_fencing_verified",
        "requires_bound_artifacts": true
      }
    ]
  },
  "policy": {
    "decision_required": true,
    "permitted_source_tasks": [
      "OPS-07"
    ],
    "issuer_roles": [
      "reviewer",
      "lead"
    ],
    "require_independent_run": true,
    "required_bindings": [
      "source",
      "scope",
      "context"
    ],
    "decision_owner_tasks": [
      "OPS-07"
    ]
  }
}
```
