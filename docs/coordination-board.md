# 调酒师开源版｜Agent 协调板 v0.2

快照日期：2026-11-20  
连接状态：false；任务状态来源：planning_snapshot_not_connected。

34 张任务；0 个活动工程运行；0 个登记 PR；0 张 accepted。模型候选不是已验证实际路由。

## 任务视图

| ID | 工作 | phase / wave | 角色／模型候选 | 直接依赖 | 额外门槛 | 状态 |
|---|---|---|---|---|---|---|
| OPS-01 | 建立项目章程、职责和变更契约 | W0 / W0 | 项目协调 / gpt6.2astra | — | — | planned |
| OPS-02 | 登记执行器、模型路由和运行主机 | W0 / W0 | 架构与接口 / gpt6.2astra | OPS-01 | — | planned |
| OPS-03 | 准备独立工作区与可复现构建环境 | W0 / W0 | 工具链、集成与发行 / gpt6.2sol | OPS-01 | — | planned |
| OPS-04 | 建立任务数据与最小协调板 | W0 / W0 | 核心逻辑 / gpt6.2sol | OPS-01 | — | planned |
| OPS-05 | 接入 Codex 的薄执行适配器 | W0 / W1 | 工具链、集成与发行 / gpt6.2sol | OPS-02, OPS-03, OPS-04 | — | planned |
| OPS-06 | 接入 OpenCode 的薄执行适配器 | W0 / W2 | 工具链、集成与发行 / gpt6.2sol | OPS-02, OPS-03, OPS-04 | — | planned |
| OPS-07 | 实现有限调度、资源租约和预算 | W0 / W2 | 核心逻辑 / gpt6.2sol | OPS-03, OPS-04 | at_least_one_runner_ready | planned |
| OPS-08 | 建立独立审查、CI 与单一合并通道 | W0 / W0 | 工具链、集成与发行 / gpt6.2sol | OPS-01, OPS-03, OPS-04 | — | planned |
| APP-01 | 固定产品端口、数据模型与模块契约 | M0 / W0 | 架构与接口 / gpt6.2astra | OPS-01 | — | planned |
| APP-02 | 真实 Mac 构建与无管理器基线 | M0 / W1 | 实验与验收 / gpt6.1terra | OPS-02, OPS-03 | — | planned |
| APP-03 | 扩展验证夹具与条件化协议 v0.2 | M0 / W1 | 实验与验收 / gpt6.1terra | APP-01, APP-02 | M0_BASELINE_VERIFIED | planned |
| APP-04 | 项目发现与唯一身份的 Mac 探测 | M1 / W1 | macOS 平台 / gpt6.2sol | APP-01, APP-03 | — | planned |
| APP-05 | E26-A 不可见项目的精确 AX 访问 | M1 / W1 | macOS 平台 / gpt6.2sol | APP-04 | host_macos_26 | planned |
| APP-06 | E26-B 临时可见槽位研究 | M1 / W1 | macOS 平台 / gpt6.2sol | APP-04 | host_macos_26 | planned |
| APP-07 | E27-A 原生 overflow 研究 | M1 / W1 | macOS 平台 / gpt6.2sol | APP-04 | host_macos_27 | planned |
| APP-08 | 审查 M1 证据并选定首条产品路线 | M1 / W1 | 独立审查 / grok4.7 → gpt6.2astra | APP-04 | M1_ROUTE_EVIDENCE_READY | planned |
| APP-09 | 实现身份解析、能力表与观察模型 | M2 / W1 | 核心逻辑 / gpt6.2sol | APP-01 | — | planned |
| APP-10 | 实现串行协调器与交互租约 | M2 / W2 | 核心逻辑 / gpt6.2sol | APP-01, APP-09 | — | planned |
| APP-11 | 实现本地配置、迁移与恢复记录 | M2 / W1 | 核心逻辑 / gpt6.2sol | APP-01 | — | planned |
| APP-12 | 实现拓扑、坐标与受限几何规划 | M2 / W2 | macOS 平台 / gpt6.2sol | APP-01, APP-02 | M0_BASELINE_VERIFIED | planned |
| APP-13 | 实现 AppKit 外壳与稳定控制入口 | M2 / W2 | 原生界面 / gpt6.2sol | APP-01, APP-02 | M0_BASELINE_VERIFIED | planned |
| APP-14 | 实现基本目录、别名和过滤交互 | M2 / W2 | 原生界面 / gpt6.2sol | APP-09, APP-13 | — | planned |
| APP-15 | 接入选定路线的 Inventory 与 Access 适配器 | M2 / W2 | macOS 平台 / gpt6.2sol | APP-04, APP-08, APP-09 | M1_PRODUCT_GATE_PASSED | planned |
| APP-16 | 接入显隐后端与两区业务计划 | M2 / W2 | macOS 平台 / gpt6.2sol | APP-08, APP-10, APP-12 | M1_PRODUCT_GATE_PASSED | planned |
| APP-17 | 合成第一条完整产品流程 | M2 / W2 | 工具链、集成与发行 / gpt6.2sol | OPS-08, APP-10, APP-11, APP-13, APP-14, APP-15, APP-16 | — | planned |
| APP-18 | 处理权限撤回与诚实降级 | M3 / W3 | macOS 平台 / gpt6.2sol | APP-17 | — | planned |
| APP-19 | 验证多屏、会话与最小恢复 | M3 / W3 | 实验与验收 / gpt6.1terra | APP-17, APP-18 | — | planned |
| APP-20 | 验证系统时钟与隐私状态完整性 | M3 / W3 | 实验与验收 / gpt6.1terra | APP-17, APP-18 | — | planned |
| APP-21 | 验证重启、睡眠、异常退出与配置稳定 | M3 / W3 | 实验与验收 / gpt6.1terra | APP-11, APP-17, APP-18 | — | planned |
| APP-22 | 可访问性、语言与常驻资源验收 | M4 / W4 | 实验与验收 / gpt6.1terra | APP-13, APP-14, APP-17, APP-18, APP-25 | — | planned |
| APP-23 | 制作可安装候选与更新链路 | M4 / W4 | 工具链、集成与发行 / gpt6.2sol | OPS-08, APP-19, APP-20, APP-21, APP-22, APP-26 | M3_PRODUCT_GATE_PASSED | planned |
| APP-24 | 小范围试用与首版发布裁决 | M5 / W5 | 项目协调 / gpt6.2astra | APP-23 | pilot_participation_authorized | planned |
| APP-25 | 实现可访问性交互与本地化覆盖 | M4 / W4 | 原生界面 / gpt6.2sol | APP-13, APP-14, APP-18 | — | planned |
| APP-26 | 独立汇总裁决 M3 产品门槛 | M3 / W3 | 独立审查 / grok4.7 → gpt6.2astra | APP-18, APP-19, APP-20, APP-21 | — | planned |

## 推荐启动波次

| 启动波次 | 任务（仍须逐项满足依赖） | 工作目标 |
|---|---|---|
| W0 | OPS-01, OPS-02, OPS-03, OPS-04, OPS-08, APP-01 | 章程、工作区、共享构建布局与协调底座；波次内仍遵守依赖。 |
| W1 | OPS-05, APP-02, APP-03, APP-04, APP-05, APP-06, APP-07, APP-08, APP-09, APP-11 | 基线、身份和候选路线；首个执行器与可独立开发的纯模块。 |
| W2 | OPS-06, OPS-07, APP-10, APP-12, APP-13, APP-14, APP-15, APP-16, APP-17 | 垂直流程；第二执行器可选推进，调度服务在已有执行器上验收。 |
| W3 | APP-18, APP-19, APP-20, APP-21, APP-26 | 可靠性验收与 APP-26 汇总裁决。 |
| W4 | APP-22, APP-23, APP-25 | APP-25 界面补齐 → APP-22 独立验收 → APP-23 候选产物。 |
| W5 | APP-24 | 真实试用后决定正式版或继续预览。 |

资源与具体 scope 见任务书。建议全局上限 4 个模型会话、3 个实现写入任务，每台 Mac GUI 1 个任务；协调、审查与子 Agent 都计入。人工调度同样保留资源和运行记录。

## 门槛及其消费关系

| 门槛 | 结构表达式 | 裁决来源任务 | 消费方 |
|---|---|---|---|
| at_least_one_runner_ready | ANY(ALL(OPS-05 accepted; evidence:codex_runner_verified); ALL(OPS-06 accepted; evidence:opencode_runner_verified)) | OPS-05, OPS-06 | OPS-07, gate:automation_runtime_ready |
| M0_BASELINE_VERIFIED | ALL(APP-02 accepted; evidence:selected_mac_baseline_verified) | APP-02 | APP-03, APP-12, APP-13 |
| M1_ROUTE_EVIDENCE_READY | ALL(APP-04 accepted; ANY(APP-05 accepted; APP-06 accepted; APP-07 accepted); evidence:complete_selected_route_research_with_matching_baseline) | APP-05, APP-06, APP-07 | APP-08 |
| M1_PRODUCT_GATE_PASSED | ALL(APP-08 accepted; evidence:at_least_one_declared_route_verified_for_core_notch_task; evidence:no_unresolved_integrity_blocker_in_declared_route) | APP-08 | APP-15, APP-16 |
| M3_PRODUCT_GATE_PASSED | ALL(APP-26 accepted; APP-18 accepted; APP-19 accepted; APP-20 accepted; APP-21 accepted; evidence:all_mandatory_scope_outcomes_passed; evidence:no_open_p0_blocker) | APP-26 | APP-23 |
| host_macos_26 | host.os_major=26 | 可信主机／授权登记 | APP-05, APP-06 |
| host_macos_27 | host.os_major=27 | 可信主机／授权登记 | APP-07 |
| pilot_participation_authorized | authorization:pilot_participation_authorized | 可信主机／授权登记 | APP-24 |
| automation_runtime_ready | ALL(OPS-07 accepted; gate:at_least_one_runner_ready; evidence:scheduler_fencing_verified) | OPS-07 | policy:deployment.activation_gate |

没有真实 RuntimeSnapshot 与证据时，不宣称任何产品 gate passed。失败研究可以 accepted；这不打开 M0/M1/M3。

## 模型登记

| 别名 | 实际 provider | 实际 model ID | 可用状态 |
|---|---|---|---|
| gpt6.2astra | 未解析 | 未解析 | unresolved |
| gpt6.2sol | 未解析 | 未解析 | unresolved |
| gpt6.1terra | 未解析 | 未解析 | unresolved |
| grok4.7 | 未解析 | 未解析 | unresolved |

实际登记主机数：0。ocra 候选确认状态：false。

## 更新入口

协调者提交版本化任务变化；运行事实未来由单写账本导出。python3 tools/render_docs.py 生成全部视图，--check 检查漂移。生成器不派工、不改状态、不连接远端。
