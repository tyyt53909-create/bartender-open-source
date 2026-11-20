# 调酒师开源版｜项目任务书 v0.2

日期：2026-11-20  
任务总数：34；状态分布：{"planned": 34}。
本文件由 coordination/tasks.json 与角色注册表生成。当前为未接入的规划快照，未创建真实远端 PR 或工程运行。

## 使用与交付规则

TaskSpec 是 task_spec_fields 的不可变投影。每次派工创建 RunManifest，记录真实仓库、版本、模型、主机、资源阶段和预算；结果为 WorkerResult，审查为 ReviewVerdict，实际集成为 IntegrationReceipt，门槛为 GateDecision。运行状态不改变任务摘要，模板不构成已执行证据。

depends_on 在可信账本确认依赖 accepted 时满足；execution_gates 单独判定。phase 是工作包，wave 是推荐波次，同波不等于同时就绪。门槛 unknown 与 false 都阻止放行。完整负面研究可以 accepted，能力 verified 和产品 gate passed 另行判断。

实现与验收资源分段申请。validation_resource_expression 的 all_of 表示检查都要完成，any_of 表示工具链条件成立时任选；不表示编码期一直持有 GUI。动作前置在系统操作前检查，允许先观察并记录 precondition_failed；缺机器、权限或实际观察仍为 blocked/not_run。

代码和版本化协议通过独立审查、当前基线候选验证、实际合并确认后接受。纯研究／裁决可归档不可变证据后接受，不伪造 merge SHA。作者子 Agent 不充当唯一独立 reviewer；角色默认范围不扩大任务 scope_paths。

## 波次与启动

| 启动波次 | 任务（仍须逐项满足依赖） | 工作目标 |
|---|---|---|
| W0 | OPS-01, OPS-02, OPS-03, OPS-04, OPS-08, APP-01 | 章程、工作区、共享构建布局与协调底座；波次内仍遵守依赖。 |
| W1 | OPS-05, APP-02, APP-03, APP-04, APP-05, APP-06, APP-07, APP-08, APP-09, APP-11 | 基线、身份和候选路线；首个执行器与可独立开发的纯模块。 |
| W2 | OPS-06, OPS-07, APP-10, APP-12, APP-13, APP-14, APP-15, APP-16, APP-17 | 垂直流程；第二执行器可选推进，调度服务在已有执行器上验收。 |
| W3 | APP-18, APP-19, APP-20, APP-21, APP-26 | 可靠性验收与 APP-26 汇总裁决。 |
| W4 | APP-22, APP-23, APP-25 | APP-25 界面补齐 → APP-22 独立验收 → APP-23 候选产物。 |
| W5 | APP-24 | 真实试用后决定正式版或继续预览。 |

人工 bootstrap 使用同一契约、排他资源登记和已授权 CLI，不等待未完成的调度器。OPS-05 或 OPS-06 一条真实可用即可验收 OPS-07；自动派工另需 automation_runtime_ready。OpenCode 仍是首条 Codex 路线的可选扩展。

## 首版需求映射

| 能力 | 相关任务 |
|---|---|
| F01 | APP-01, APP-07, APP-12, APP-14, APP-16, APP-17 |
| F02 | APP-02, APP-13, APP-17, APP-22, APP-25 |
| F03 | APP-02, APP-03, APP-05, APP-06, APP-07, APP-08, APP-12, APP-15, APP-16, APP-17, APP-19, APP-26 |
| F04 | APP-01, APP-02, APP-03, APP-04, APP-05, APP-07, APP-08, APP-09, APP-14, APP-15, APP-17, APP-22, APP-25 |
| F05 | APP-02, APP-03, APP-05, APP-06, APP-07, APP-08, APP-15, APP-17, APP-19, APP-26 |
| F06 | APP-01, APP-03, APP-05, APP-06, APP-07, APP-08, APP-10, APP-16, APP-17, APP-19, APP-26 |
| F07 | APP-01, APP-05, APP-06, APP-07, APP-08, APP-10, APP-11, APP-12, APP-17, APP-19, APP-21, APP-23, APP-26 |
| F08 | APP-01, APP-02, APP-03, APP-04, APP-05, APP-07, APP-08, APP-09, APP-14, APP-15, APP-17, APP-18, APP-22 |
| F09 | APP-01, APP-03, APP-04, APP-09, APP-13, APP-15, APP-18, APP-22, APP-25, APP-26 |
| F10 | APP-02, APP-03, APP-05, APP-06, APP-07, APP-08, APP-16, APP-20, APP-26 |
| F11 | APP-11, APP-13, APP-18, APP-21, APP-23, APP-26 |
| F12 | APP-13, APP-14, APP-22, APP-23, APP-25 |

APP-24 综合 F01—F12。需求覆盖不证明功能已实现。

## 任务总览

| ID | 工作 | phase / wave | 角色／模型候选 | 直接依赖 | 额外门槛 |
|---|---|---|---|---|---|
| OPS-01 | 建立项目章程、职责和变更契约 | W0 / W0 | 项目协调 / gpt6.2astra | — | — |
| OPS-02 | 登记执行器、模型路由和运行主机 | W0 / W0 | 架构与接口 / gpt6.2astra | OPS-01 | — |
| OPS-03 | 准备独立工作区与可复现构建环境 | W0 / W0 | 工具链、集成与发行 / gpt6.2sol → gpt6luna | OPS-01 | — |
| OPS-04 | 建立任务数据与最小协调板 | W0 / W0 | 核心逻辑 / gpt6.2sol | OPS-01 | — |
| OPS-05 | 接入 Codex 的薄执行适配器 | W0 / W1 | 工具链、集成与发行 / gpt6.2sol | OPS-02, OPS-03, OPS-04 | — |
| OPS-06 | 接入 OpenCode 的薄执行适配器 | W0 / W2 | 工具链、集成与发行 / gpt6.2sol | OPS-02, OPS-03, OPS-04 | — |
| OPS-07 | 实现有限调度、资源租约和预算 | W0 / W2 | 核心逻辑 / gpt6.2sol | OPS-03, OPS-04 | at_least_one_runner_ready |
| OPS-08 | 建立独立审查、CI 与单一合并通道 | W0 / W0 | 工具链、集成与发行 / gpt6.2sol | OPS-01, OPS-03, OPS-04 | — |
| APP-01 | 固定产品端口、数据模型与模块契约 | M0 / W0 | 架构与接口 / gpt6.2astra | OPS-01 | — |
| APP-02 | 真实 Mac 构建与无管理器基线 | M0 / W1 | 实验与验收 / gpt6.1terra | OPS-02, OPS-03 | — |
| APP-03 | 扩展验证夹具与条件化协议 v0.2 | M0 / W1 | 实验与验收 / gpt6.1terra | APP-01, APP-02 | M0_BASELINE_VERIFIED |
| APP-04 | 项目发现与唯一身份的 Mac 探测 | M1 / W1 | macOS 平台 / gpt6.2sol | APP-01, APP-03 | — |
| APP-05 | E26-A 不可见项目的精确 AX 访问 | M1 / W1 | macOS 平台 / gpt6.2sol | APP-04 | host_macos_26 |
| APP-06 | E26-B 临时可见槽位研究 | M1 / W1 | macOS 平台 / gpt6.2sol | APP-04 | host_macos_26 |
| APP-07 | E27-A 原生 overflow 研究 | M1 / W1 | macOS 平台 / gpt6.2sol | APP-04 | host_macos_27 |
| APP-08 | 审查 M1 证据并选定首条产品路线 | M1 / W1 | 独立审查 / grok4.7 → gpt6.2astra | APP-04 | M1_ROUTE_EVIDENCE_READY |
| APP-09 | 实现身份解析、能力表与观察模型 | M2 / W1 | 核心逻辑 / gpt6.2sol | APP-01 | — |
| APP-10 | 实现串行协调器与交互租约 | M2 / W2 | 核心逻辑 / gpt6.2sol | APP-01, APP-09 | — |
| APP-11 | 实现本地配置、迁移与恢复记录 | M2 / W1 | 核心逻辑 / gpt6.2sol | APP-01 | — |
| APP-12 | 实现拓扑、坐标与受限几何规划 | M2 / W2 | macOS 平台 / gpt6.2sol | APP-01, APP-02 | M0_BASELINE_VERIFIED |
| APP-13 | 实现 AppKit 外壳与稳定控制入口 | M2 / W2 | 原生界面 / gpt6.2sol | APP-01, APP-02 | M0_BASELINE_VERIFIED |
| APP-14 | 实现基本目录、别名和过滤交互 | M2 / W2 | 原生界面 / gpt6.2sol | APP-09, APP-13 | — |
| APP-15 | 接入选定路线的 Inventory 与 Access 适配器 | M2 / W2 | macOS 平台 / gpt6.2sol | APP-04, APP-08, APP-09 | M1_PRODUCT_GATE_PASSED |
| APP-16 | 接入显隐后端与两区业务计划 | M2 / W2 | macOS 平台 / gpt6.2sol | APP-08, APP-10, APP-12 | M1_PRODUCT_GATE_PASSED |
| APP-17 | 合成第一条完整产品流程 | M2 / W2 | 工具链、集成与发行 / gpt6.2sol | OPS-08, APP-10, APP-11, APP-13, APP-14, APP-15, APP-16 | — |
| APP-18 | 处理权限撤回与诚实降级 | M3 / W3 | macOS 平台 / gpt6.2sol | APP-17 | — |
| APP-19 | 验证多屏、会话与最小恢复 | M3 / W3 | 实验与验收 / gpt6.1terra | APP-17, APP-18 | — |
| APP-20 | 验证系统时钟与隐私状态完整性 | M3 / W3 | 实验与验收 / gpt6.1terra | APP-17, APP-18 | — |
| APP-21 | 验证重启、睡眠、异常退出与配置稳定 | M3 / W3 | 实验与验收 / gpt6.1terra | APP-11, APP-17, APP-18 | — |
| APP-22 | 可访问性、语言与常驻资源验收 | M4 / W4 | 实验与验收 / gpt6.1terra | APP-13, APP-14, APP-17, APP-18, APP-25 | — |
| APP-23 | 制作可安装候选与更新链路 | M4 / W4 | 工具链、集成与发行 / gpt6.2sol | OPS-08, APP-19, APP-20, APP-21, APP-22, APP-26 | M3_PRODUCT_GATE_PASSED |
| APP-24 | 小范围试用与首版发布裁决 | M5 / W5 | 项目协调 / gpt6.2astra | APP-23 | pilot_participation_authorized |
| APP-25 | 实现可访问性交互与本地化覆盖 | M4 / W4 | 原生界面 / gpt6.2sol | APP-13, APP-14, APP-18 | — |
| APP-26 | 独立汇总裁决 M3 产品门槛 | M3 / W3 | 独立审查 / grok4.7 → gpt6.2astra | APP-18, APP-19, APP-20, APP-21 | — |

## 完整任务卡

### OPS-01｜建立项目章程、职责和变更契约

归属工作包 phase：W0；推荐波次 wave：W0；角色：项目协调；模型候选顺序：gpt6.2astra；交付类型：workflow；状态：planned。

实现资源：linux_cpu。验收资源表达式：`{"all_of": [{"resource_class": "linux_cpu"}]}`。

直接依赖：无。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- AGENTS.md
- README.md
- LICENSE
- coordination/roles.json
- roles/
- contracts/
- templates/
- coordination/document-templates/
- docs/adr/initial-contracts.md
- docs/baselines/

**验收标准**

- 继承产品 F01-F12 和 M0-M5，不擅自扩大首版范围
- 定义单任务负责人、写入范围、验收者、M1 总门槛和发布授权边界
- 所有代理读取相同版本的任务契约

**需要的证据**

- 版本化章程
- 角色矩阵
- 契约 hash

接入前置：目标远端仓库尚未指定；本轮仅生成设计包

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`7271422dfc7d083e6abcc180fdd8e49d92d9c2b30af77b4431404e275aa9243d`

### OPS-02｜登记执行器、模型路由和运行主机

归属工作包 phase：W0；推荐波次 wave：W0；角色：架构与接口；模型候选顺序：gpt6.2astra；交付类型：workflow；状态：planned。

实现资源：linux_cpu。验收资源表达式：`{"all_of": [{"resource_class": "linux_cpu"}]}`。

直接依赖：OPS-01。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- coordination/models.json
- coordination/hosts.json
- tools/agent-control/probes/

**验收标准**

- 模型别名与 provider/实际 model ID 分开，未核验不得标为可调度
- 记录 Codex/OpenCode 实际版本、授权方式、输入输出能力及主机标签
- ocra 保留为未确认入口，不硬编码推测 API
- 路由失败明确阻塞或按预先批准的替代策略重排，不静默换模型

**需要的证据**

- 脱敏能力探测结果
- model-route manifest
- host capability manifest

接入前置：远端地址、真实模型 ID 与授权方式待环境接入时核验

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`df688c05b7c0e83e9d60499466f13b92a6b707f5e0f927934e94e7e73aee21a9`

### OPS-03｜准备独立工作区与可复现构建环境

归属工作包 phase：W0；推荐波次 wave：W0；角色：工具链、集成与发行；模型候选顺序：gpt6.2sol → gpt6luna；交付类型：workflow；状态：planned。

实现资源：linux_cpu。验收资源表达式：`{"all_of": [{"resource_class": "linux_cpu"}]}`。

直接依赖：OPS-01。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- tools/agent-control/workspaces/
- coordination/environments/
- docs/adr/build-layout.md
- Package.swift
- Package.resolved
- Apps/MenuBarApp/project.yml
- Config/
- tools/build/

**验收标准**

- 每个实现任务使用独立 branch 和 checkout/worktree，禁止共享可写目录
- 同机 worktree 与跨机器 clone 分开定义；工作树不被当作安全隔离
- 共享构建缓存与 DerivedData 不造成并发写入；保留 source SHA
- 采用根 Package.swift 映射当前 Packages/... 与 Tests/...；不引用越出嵌套包根的测试目录。
- 确立 XcodeGen 精确版本固定规则、project.yml 生成入口与隔离策略；本卡检查规则/脚本，实际 Mac 生成和构建由 APP-13 验收。生成工程不手改、不作为源文件权威。
- 新增文件在已定义 target 下自动发现；新增 target、依赖或构建选项仍经共享 manifest 所有者串行集成。

**需要的证据**

- 工作区创建/清理演练
- 修改隔离检查
- 环境与路径清单

环境说明：本卡验收工作区隔离与构建生成规则，不声称 XcodeGen/Xcode 已在 Mac 实跑；真实工程生成、固定版本和编译验收归 APP-13，Linux CLI 接入不因该 Mac 检查等待。

接入前置：实际仓库与远端执行主机待登记

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`23895db905ecfbb372c9545f884e2d38fef33d74b5bdf8cf458e562ba0b31025`

### OPS-04｜建立任务数据与最小协调板

归属工作包 phase：W0；推荐波次 wave：W0；角色：核心逻辑；模型候选顺序：gpt6.2sol；交付类型：workflow；状态：planned。

实现资源：linux_cpu。验收资源表达式：`{"all_of": [{"resource_class": "linux_cpu"}]}`。

直接依赖：OPS-01。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- coordination/tasks.json
- coordination/path-ownership.json
- coordination/README.md
- coordination/events/
- coordination/board/
- tools/render_docs.py
- tools/render_board.py
- tools/render_task_book.py
- tools/validate_plan.py
- tools/gate_eval.py
- tools/requirements.txt
- tests/
- docs/project-plan.md
- docs/task-book.md
- docs/agent-team-architecture.md
- docs/coordination-board.md
- docs/dependency-map.md
- docs/package-checks.md
- docs/audit-v0.2.md
- docs/check-results.json
- docs/validation/

**验收标准**

- 先用版本化任务 JSON、追加事件和生成的 Markdown/HTML 看板；不建通用平台
- 单协调者提交状态变更，worker 只能上报结果
- 看板显示依赖、阻塞、执行器/模型/主机、SHA、证据和下一步
- 任务 accepted 与产品 gate 通过分开显示
- 任务书、协调板、波次/需求/门槛视图由同一任务目录生成；--check 能拒绝人工改生成文档造成的漂移。

**需要的证据**

- 任务 schema
- 示例任务状态迁移
- 从任务数据重建的看板

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`5d28a024597b7d0160bace503df44ae97ba4af725cb6fbdc0dc6aad4a20217f7`

### OPS-05｜接入 Codex 的薄执行适配器

归属工作包 phase：W0；推荐波次 wave：W1；角色：工具链、集成与发行；模型候选顺序：gpt6.2sol；交付类型：workflow；状态：planned。

实现资源：linux_cpu。验收资源表达式：`{"all_of": [{"resource_class": "linux_cpu"}]}`。

直接依赖：OPS-02, OPS-03, OPS-04。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- tools/agent-control/adapters/codex/
- docs/adapter-contract.md

**验收标准**

- 按固定 CLI 版本启动任务并记录结构化输出、退出码和会话标识
- 从 TaskSpec 生成输入，不把旧聊天摘要当成唯一任务来源
- 支持取消请求、结果未知和进程确认退出；不把命令返回当验收通过

**需要的证据**

- 无外部副作用的 smoke run
- 脱敏运行 manifest
- 取消与异常退出记录

接入前置：需具备可调用 Codex 环境与已验证路由

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`9e78c9a5381e6588a4bae7e04847b5dcbd220e7abdc620b156cd81d5e9bc6ba9`

### OPS-06｜接入 OpenCode 的薄执行适配器

归属工作包 phase：W0；推荐波次 wave：W2；角色：工具链、集成与发行；模型候选顺序：gpt6.2sol；交付类型：workflow；状态：planned。

实现资源：linux_cpu。验收资源表达式：`{"all_of": [{"resource_class": "linux_cpu"}]}`。

直接依赖：OPS-02, OPS-03, OPS-04。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- tools/agent-control/adapters/opencode/

共享文件变更请求（owner 串行处理）：docs/adapter-contract.md。

**验收标准**

- 按实际版本验证 CLI/server/agent 配置，不混用不同版本字段
- 与 Codex 输出同一 WorkerResult 契约
- 模型列表与提供商实际能力核验通过；不可用时不阻塞已可用 Codex 首条开发线

**需要的证据**

- 实际版本与模型探测
- smoke run
- 停止/恢复语义记录

接入前置：当前未确认 OpenCode 安装、版本与模型可用性

不阻塞已可用的首条执行器路线。

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`110d5d17bb87c532293aecd7d50f2d1f7fbb5573a39c8a5d890384063e6bf048`

### OPS-07｜实现有限调度、资源租约和预算

归属工作包 phase：W0；推荐波次 wave：W2；角色：核心逻辑；模型候选顺序：gpt6.2sol；交付类型：workflow；状态：planned。

实现资源：linux_cpu。验收资源表达式：`{"all_of": [{"resource_class": "linux_cpu"}]}`。

直接依赖：OPS-03, OPS-04。额外门槛：at_least_one_runner_ready。

**可修改范围**

- tools/agent-control/coordination/
- coordination/policies.json
- docs/gate-evaluation.md

**验收标准**

- 第一阶段单协调者与有限脚本即可，手工分配也必须记录同一契约
- 依赖仅在 accepted 后释放；写范围冲突和 Mac GUI 主机锁会阻止派单
- 运行代次/租约 fencing 拒绝迟到提交；取消后确认实际进程退出才释放 GUI 主机
- 子代理计入父任务与全局并发/预算，不自动获得新写范围或合并权限
- 实现 true/false/unknown 门槛语义并与离线 gate_eval 合同样例一致；只有通过 automation_runtime_ready 后才启用自动派工。

**需要的证据**

- 一次并行任务演练
- 过期 lease/迟到结果演练
- 预算与取消状态记录

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`a0aaffd4eb51aed62213a178bfe670db255aef2a8cf6d892890ec03630e2dff8`

### OPS-08｜建立独立审查、CI 与单一合并通道

归属工作包 phase：W0；推荐波次 wave：W0；角色：工具链、集成与发行；模型候选顺序：gpt6.2sol；交付类型：workflow；状态：planned。

实现资源：linux_cpu。验收资源表达式：`{"all_of": [{"resource_class": "linux_cpu"}]}`。

直接依赖：OPS-01, OPS-03, OPS-04。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- .github/workflows/
- .github/CODEOWNERS
- tools/agent-control/integration/
- docs/merge-policy.md
- tools/package_starter.py
- MANIFEST.json
- .gitignore

**验收标准**

- 作者与审查者不同 run；review 绑定 base/head/contract SHA
- 最新基线上的候选通过所需 CI 后才合并，改动或 rebase 使旧批准失效
- worker 无 main 写权限，合并执行器执行已授权门槛
- 本地演练不冒充实际远端保护规则已配置
- 使用结构化 ReviewVerdict / RunManifest / IntegrationReceipt，校验来源和当前版本；不解析 Markdown 自由文本来推进状态。

**需要的证据**

- 候选合并演练
- CI/审查证据绑定
- 失败阻止合并记录

接入前置：实际远端仓库与保护规则尚未配置

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`f2525c4de998af809c9bf433a94ea519af05946392da27faf2a8806d30c0a846`

### APP-01｜固定产品端口、数据模型与模块契约

归属工作包 phase：M0；推荐波次 wave：W0；角色：架构与接口；模型候选顺序：gpt6.2astra；交付类型：code；状态：planned。

实现资源：linux_cpu。验收资源表达式：`{"any_of": [{"resource_class": "linux_cpu", "requires": "verified_swift_toolchain_and_portable_module"}, {"resource_class": "macos_build", "requires": "verified_xcode_toolchain"}], "platform_dependent_checks_require": "macos_build"}`。

直接依赖：OPS-01。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- Packages/MenuBarCore/Contracts/
- docs/adr/product-contracts.md

共享文件变更请求（owner 串行处理）：Package.swift, Package.resolved, Apps/MenuBarApp/project.yml, Config/。

**验收标准**

- 定义 InventoryProvider/VisibilityBackend/AccessBackend，计划器无系统副作用
- 定义四层状态、身份、观察来源、能力粒度、ticket 和 epoch 语义
- 明确各模块所有权与兼容演进规则
- 共享工程文件由集成者串行落地；其他任务只提交所需变更说明，不直接竞争编辑

**需要的证据**

- 端口契约
- 数据模型
- 针对歧义/版本失效的必要样例

环境说明：纯 Swift 检查仅在匹配工具链与依赖可用时在 Linux 执行；需要平台依赖则安排 macos_build。

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`7b4e1344c10e705517739b476f3aa8e4aaa600a5923b3ee4919ee557a3ab1d8f`

### APP-02｜真实 Mac 构建与无管理器基线

归属工作包 phase：M0；推荐波次 wave：W1；角色：实验与验收；模型候选顺序：gpt6.1terra；交付类型：research；状态：planned。

实现资源：macos_gui_exclusive。验收资源表达式：`{"all_of": [{"resource_class": "macos_gui_exclusive"}]}`。

直接依赖：OPS-02, OPS-03。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- menubar-validation-lab/environment/
- menubar-validation-lab/results/baseline/
- menubar-validation-lab/build-fixes/

若编译修复必须触及现有 Lab 源文件，先精确增补当前 attempt scope 并取得排他写入，不把 build-fixes 目录当作唯一可修代码路径。

**验收标准**

- 在真实 Mac 编译已有 Lab 并记录实际工具链、OS build、硬件与 source hash
- 先验证同 App 三项目、右键、Option、子菜单和动态计数无管理器基线
- 故障恢复入口与实验退出步骤先成立
- M0 门槛由本卡验收的独立 reviewer/lead 签发 GateDecision；作者不能用 accepted 或自己的报告打开门槛。

**需要的证据**

- 完整构建日志
- 匹配环境的基线结果
- 原始事件与观察记录

通用研究规则：在已具备实际主机与相符基线的观察中，动作前置不成立时提交 precondition_failed/skipped_with_reason 与实测依据，未发生动作的日志不适用；完整负面研究可以 accepted，但能力不能 verified。缺主机、权限或没有实际观察仍为 blocked/not_run。

本卡补充：本卡真实构建或无管理器基线失败可用完整日志提交研究验收；M0_BASELINE_VERIFIED 继续关闭。缺 Mac 或没有执行记录仍为 blocked/not_run。

环境说明：同一主机的 GUI 与干扰性构建排他；旧运行停止并恢复基线后才交接。

接入前置：真实 Mac、交互桌面会话与观察条件未登记

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`fe6dfa3139f6d30a541d4cfe6f8f188573e43036c13cb6712aa04f8a451be182`

### APP-03｜扩展验证夹具与条件化协议 v0.2

归属工作包 phase：M0；推荐波次 wave：W1；角色：实验与验收；模型候选顺序：gpt6.1terra；交付类型：code；状态：planned。

实现资源：macos_build。验收资源表达式：`{"all_of": [{"resource_class": "macos_build"}, {"resource_class": "macos_gui_exclusive"}]}`。

直接依赖：APP-01, APP-02。额外门槛：M0_BASELINE_VERIFIED。

**可修改范围**

- menubar-validation-lab/Fixture/
- menubar-validation-lab/protocol/v0.2/
- menubar-validation-lab/tools/evaluator-v0.2/

共享文件变更请求（owner 串行处理）：Package.swift, Package.resolved, Apps/MenuBarApp/project.yml, Config/。

**验收标准**

- 保留 v0.1 历史结果，增加超宽、重复身份、动态标题与晚到动作场景
- 普遍完整性与声明能力条件分别表达；缺硬件保持 blocked/not_run
- 评估器验证记录，不伪装为重新执行 UI

**需要的证据**

- 新协议/hash
- 夹具构建与行为记录
- 条件适用评估用例

环境说明：实现／编译不包含 GUI 通过；涉及界面、输入或真实屏幕证据时单独申请整机 GUI 租约。

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`6888442428a37bff3551e44fb3a4f83a61d071ced4921dc8ea0282371d351782`

### APP-04｜项目发现与唯一身份的 Mac 探测

归属工作包 phase：M1；推荐波次 wave：W1；角色：macOS 平台；模型候选顺序：gpt6.2sol；交付类型：research；状态：planned。

实现资源：macos_gui_exclusive。验收资源表达式：`{"all_of": [{"resource_class": "macos_gui_exclusive"}]}`。

直接依赖：APP-01, APP-03。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- menubar-validation-lab/experiments/identity/

**验收标准**

- 分开记录生产者、宿主、运行期引用与呈现
- 同 App 三项目、重排、重启与重复标识情况下不选第一项
- 当前可达性与动态字段来源真实记录

**需要的证据**

- AX/对象观察快照
- 身份变化复现
- 不确定性清单

通用研究规则：在已具备实际主机与相符基线的观察中，动作前置不成立时提交 precondition_failed/skipped_with_reason 与实测依据，未发生动作的日志不适用；完整负面研究可以 accepted，但能力不能 verified。缺主机、权限或没有实际观察仍为 blocked/not_run。

环境说明：同一主机的 GUI 与干扰性构建排他；旧运行停止并恢复基线后才交接。

接入前置：需要实际 Mac GUI 独占时段

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`3575d81c4987738edee438b393e305c9a4a23b1c474794432432172b5050b943`

### APP-05｜E26-A 不可见项目的精确 AX 访问

归属工作包 phase：M1；推荐波次 wave：W1；角色：macOS 平台；模型候选顺序：gpt6.2sol；交付类型：research；状态：planned。

实现资源：macos_gui_exclusive。验收资源表达式：`{"all_of": [{"resource_class": "macos_gui_exclusive"}]}`。

直接依赖：APP-04。额外门槛：host_macos_26。

**可修改范围**

- menubar-validation-lab/experiments/e26-ax/

**验收标准**

- 在真实目标不可见条件下，对唯一且声明 action 的对象只发一次动作
- 独立观察正确原菜单、可用位置、子菜单与结束结果
- 超时不盲目重发，逐 Item-action 声明结果
- 同一候选完成适用的系统状态、输入与恢复完整性观察；失败保留，不从另一 OS 借成绩

**需要的证据**

- macOS 26 匹配基线
- 原始 action 与 UI 观察
- 逐动作能力表
- 同条件下系统状态、输入与恢复的共同门槛记录

通用研究规则：在已具备实际主机与相符基线的观察中，动作前置不成立时提交 precondition_failed/skipped_with_reason 与实测依据，未发生动作的日志不适用；完整负面研究可以 accepted，但能力不能 verified。缺主机、权限或没有实际观察仍为 blocked/not_run。

环境说明：同一主机的 GUI 与干扰性构建排他；旧运行停止并恢复基线后才交接。

接入前置：仅适用实际 macOS 26；未具备条件时保持 blocked

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`1322ac76e7a8d8697e8f32f4356f78ac6b6031d207df5842c3e67fddb5ae93fc`

### APP-06｜E26-B 临时可见槽位研究

归属工作包 phase：M1；推荐波次 wave：W1；角色：macOS 平台；模型候选顺序：gpt6.2sol；交付类型：research；状态：planned。

实现资源：macos_gui_exclusive。验收资源表达式：`{"all_of": [{"resource_class": "macos_gui_exclusive"}]}`。

直接依赖：APP-04。额外门槛：host_macos_26。

**可修改范围**

- menubar-validation-lab/experiments/e26-slot/

**验收标准**

- 源真实可命中、目标槽足够、输入空闲和身份可观察才尝试
- 独立研究构建默认关闭，不用负坐标猜测完全离屏目标
- 用户中途修改时放弃旧恢复，并记录输入与菜单副作用
- 同一候选完成适用的系统状态、输入与恢复完整性观察；失败保留，不从另一 OS 借成绩
- 可接受前置不成立的完整负面研究；实际移动步骤必须在全部前置通过后执行。

**需要的证据**

- 前置条件证明
- 移动/恢复原始记录
- 用户修改保留结果
- 同条件下系统状态、输入与恢复的共同门槛记录

通用研究规则：在已具备实际主机与相符基线的观察中，动作前置不成立时提交 precondition_failed/skipped_with_reason 与实测依据，未发生动作的日志不适用；完整负面研究可以 accepted，但能力不能 verified。缺主机、权限或没有实际观察仍为 blocked/not_run。

实际动作前置：source_is_really_hittable, destination_capacity_confirmed, input_idle, identity_and_neighbors_revalidated。

环境说明：同一主机的 GUI 与干扰性构建排他；旧运行停止并恢复基线后才交接。

接入前置：仅适用实际 macOS 26 且源可命中；不满足不能算失败后自动绕过

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`64c08392531ce616fd7abf632931fa5a4e967eafcee0f8352f88e625b7894b88`

### APP-07｜E27-A 原生 overflow 研究

归属工作包 phase：M1；推荐波次 wave：W1；角色：macOS 平台；模型候选顺序：gpt6.2sol；交付类型：research；状态：planned。

实现资源：macos_gui_exclusive。验收资源表达式：`{"all_of": [{"resource_class": "macos_gui_exclusive"}]}`。

直接依赖：APP-04。额外门槛：host_macos_27。

**可修改范围**

- menubar-validation-lab/experiments/e27-overflow/

**验收标准**

- 真实 macOS 27 的几何前置与容量成立后再进入候选
- 同 App 三项目逐一验证原菜单、右键、Option、子菜单和动态状态
- 观察时钟、通知中心、摄像头/麦克风及来源提示
- 同一候选完成适用的系统状态、输入与恢复完整性观察；失败保留，不从另一 OS 借成绩。

**需要的证据**

- macOS 27 匹配基线
- 候选参数与原始结果
- 系统状态观察
- 同条件下系统状态、输入与恢复的共同门槛记录

通用研究规则：在已具备实际主机与相符基线的观察中，动作前置不成立时提交 precondition_failed/skipped_with_reason 与实测依据，未发生动作的日志不适用；完整负面研究可以 accepted，但能力不能 verified。缺主机、权限或没有实际观察仍为 blocked/not_run。

环境说明：同一主机的 GUI 与干扰性构建排他；旧运行停止并恢复基线后才交接。

接入前置：未登记 macOS 27 主机；不升级既有机器以填满矩阵

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`cf65bd34f9dc5289decb0667bfff95617bcd303c1670f241fa673fbaaa65733e`

### APP-08｜审查 M1 证据并选定首条产品路线

归属工作包 phase：M1；推荐波次 wave：W1；角色：独立审查；模型候选顺序：grok4.7 → gpt6.2astra；交付类型：decision；状态：planned。

实现资源：linux_cpu。验收资源表达式：`{"all_of": [{"resource_class": "linux_cpu"}]}`。

直接依赖：APP-04。额外门槛：M1_ROUTE_EVIDENCE_READY。

**可修改范围**

- docs/decisions/m1-route/
- menubar-validation-lab/capabilities/

**验收标准**

- 逐路线独立裁决；至少一条完整任务通过才打开产品 M1 gate，全部失败也可交付 accepted 的 No-Go 研究决定。
- 其他路线未测保持其真实状态，不为获得 gate 改成 passed
- 无合格路线时维持技术预览，给出下一项能消除不确定性的实验
- 输出结构化 ReviewVerdict 与 GateDecision，绑定 source/scope/context；首选 Grok 4.7，已配置回退为独立 Astra run，实际路由必须记录。

**需要的证据**

- 不可变证据引用与 hash
- 独立审查结论
- 声明支持的条件与动作集合

审查规则：independent_from_all_subject_authors; trusted_authority_validation_required; no_recursive_review_of_review。

任务规范 SHA-256：`40c0e2dd2b928ba31104b6ea39d4993a9060cb991adbd73f2fc56e3cf4cf2178`

### APP-09｜实现身份解析、能力表与观察模型

归属工作包 phase：M2；推荐波次 wave：W1；角色：核心逻辑；模型候选顺序：gpt6.2sol；交付类型：code；状态：planned。

实现资源：linux_cpu。验收资源表达式：`{"any_of": [{"resource_class": "linux_cpu", "requires": "verified_swift_toolchain_and_portable_module"}, {"resource_class": "macos_build", "requires": "verified_xcode_toolchain"}], "platform_dependent_checks_require": "macos_build"}`。

直接依赖：APP-01。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- Packages/MenuBarCore/Identity/
- Packages/MenuBarCore/Capabilities/
- Tests/Core/IdentityTests/

共享文件变更请求（owner 串行处理）：Package.swift, Package.resolved, Apps/MenuBarApp/project.yml, Config/。

**验收标准**

- 唯一绑定、歧义、未知和未匹配配置保留都有明确输出
- 禁止以动态标题/PID/坐标作为跨重启身份
- 普通数值刷新不递增结构 epoch

**需要的证据**

- 纯模型必要测试
- 接口使用样例
- 错误配对反例

环境说明：纯 Swift 检查仅在匹配工具链与依赖可用时在 Linux 执行；需要平台依赖则安排 macos_build。

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`b278fb33771bc517370bc3eeae6c1eec3fb716651d037c93516f8d1fde510000`

### APP-10｜实现串行协调器与交互租约

归属工作包 phase：M2；推荐波次 wave：W2；角色：核心逻辑；模型候选顺序：gpt6.2sol；交付类型：code；状态：planned。

实现资源：linux_cpu。验收资源表达式：`{"any_of": [{"resource_class": "linux_cpu", "requires": "verified_swift_toolchain_and_portable_module"}, {"resource_class": "macos_build", "requires": "verified_xcode_toolchain"}], "platform_dependent_checks_require": "macos_build"}`。

直接依赖：APP-01, APP-09。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- Packages/MenuBarCore/Coordination/
- Tests/Core/CoordinationTests/

共享文件变更请求（owner 串行处理）：Package.swift, Package.resolved, Apps/MenuBarApp/project.yml, Config/。

**验收标准**

- 单消费者执行副作用命令，await 后重验 ticket
- 租约覆盖实际显隐域，unknown 时不自动收起
- 取消/迟到回调/本操作预期变更不产生竞争或自我失效

**需要的证据**

- 并发状态机测试
- 事件序列与不变量
- 模拟超时后的结果

环境说明：纯 Swift 检查仅在匹配工具链与依赖可用时在 Linux 执行；需要平台依赖则安排 macos_build。

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`d06fa1e2e89a217aa31d00ddfa56f790e8f60bd2d98b86666edd23221a0bb87c`

### APP-11｜实现本地配置、迁移与恢复记录

归属工作包 phase：M2；推荐波次 wave：W1；角色：核心逻辑；模型候选顺序：gpt6.2sol；交付类型：code；状态：planned。

实现资源：linux_cpu。验收资源表达式：`{"any_of": [{"resource_class": "linux_cpu", "requires": "verified_swift_toolchain_and_portable_module"}, {"resource_class": "macos_build", "requires": "verified_xcode_toolchain"}], "platform_dependent_checks_require": "macos_build"}`。

直接依赖：APP-01。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- Packages/MenuBarPersistence/
- Tests/Core/PersistenceTests/

共享文件变更请求（owner 串行处理）：Package.swift, Package.resolved, Apps/MenuBarApp/project.yml, Config/。

**验收标准**

- 版本化 Codable JSON 原子替换并保留上一个有效版本
- 持久化用户意图，不保存活 AX 引用和旧坐标作为恢复指令
- 损坏/迁移失败/中断写入可恢复且保留用户数据

**需要的证据**

- 配置版本样例
- 写入故障与迁移测试
- 最小 journal 格式

环境说明：纯 Swift 检查仅在匹配工具链与依赖可用时在 Linux 执行；需要平台依赖则安排 macos_build。

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`be253f12d54e746fc152d385e861ec9d6ae77ec5e0384a009df3af85ada12720`

### APP-12｜实现拓扑、坐标与受限几何规划

归属工作包 phase：M2；推荐波次 wave：W2；角色：macOS 平台；模型候选顺序：gpt6.2sol；交付类型：code；状态：planned。

实现资源：macos_build。验收资源表达式：`{"all_of": [{"resource_class": "macos_build"}, {"resource_class": "macos_gui_exclusive"}]}`。

直接依赖：APP-01, APP-02。额外门槛：M0_BASELINE_VERIFIED。

**可修改范围**

- Packages/MenuBarPlatform/Topology/
- Packages/MenuBarPlatform/Geometry/
- Tests/TopologyTests/

共享文件变更请求（owner 串行处理）：Package.swift, Package.resolved, Apps/MenuBarApp/project.yml, Config/。

**验收标准**

- 显式坐标空间、逻辑点/像素、display 与 topologyEpoch
- 负坐标、上下排列、混合缩放与容量反例不误判
- 纯计划器只返回计划，拒绝无效几何与不明确影响范围

**需要的证据**

- 转换与几何测试
- 真实屏幕输入样本
- 编译日志

环境说明：实现／编译不包含 GUI 通过；涉及界面、输入或真实屏幕证据时单独申请整机 GUI 租约。

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`e41ae0a6ff2eefb0de30c3e0ea2f8f79fcb009c48878cb5cb7334dade67b6923`

### APP-13｜实现 AppKit 外壳与稳定控制入口

归属工作包 phase：M2；推荐波次 wave：W2；角色：原生界面；模型候选顺序：gpt6.2sol；交付类型：code；状态：planned。

实现资源：macos_build。验收资源表达式：`{"all_of": [{"resource_class": "macos_build"}, {"resource_class": "macos_gui_exclusive"}]}`。

直接依赖：APP-01, APP-02。额外门槛：M0_BASELINE_VERIFIED。

**可修改范围**

- Apps/MenuBarApp/AppShell/
- Packages/MenuBarPlatform/Hotkeys/
- Packages/MenuBarPlatform/LoginItem/

共享文件变更请求（owner 串行处理）：Package.swift, Package.resolved, Apps/MenuBarApp/project.yml, Config/。

**验收标准**

- 常驻控制入口、窗口恢复入口和可配置快捷键可用
- 焦点、Esc、本工具面板生命周期有明确语义
- 用户选择登录启动，权限不足或快捷键冲突有反馈
- 未经 M1 放行不启用未知后端收纳
- 在实际 Mac 固定并记录 XcodeGen/Xcode/Swift/SDK 版本，从干净工作区生成 project.yml 对应工程并验证目标图、资源和构建；共享清单改动交 owner 串行处理。

**需要的证据**

- 本工具 UI 行为记录
- 快捷键/登录项实际状态
- Mac 编译日志
- 精确生成器与工具链版本
- 干净工作区工程生成及 Mac 构建日志

环境说明：实现／编译不包含 GUI 通过；涉及界面、输入或真实屏幕证据时单独申请整机 GUI 租约。

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`d1b4f022ac2db93d5562638cd90e485fd69b067cf36ffccc73d2bebbee69a052`

### APP-14｜实现基本目录、别名和过滤交互

归属工作包 phase：M2；推荐波次 wave：W2；角色：原生界面；模型候选顺序：gpt6.2sol；交付类型：code；状态：planned。

实现资源：macos_build。验收资源表达式：`{"all_of": [{"resource_class": "macos_build"}, {"resource_class": "macos_gui_exclusive"}]}`。

直接依赖：APP-09, APP-13。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- Apps/MenuBarApp/UI/Directory/
- Apps/MenuBarApp/UI/Settings/Organization/
- Tests/DirectoryTests/

共享文件变更请求（owner 串行处理）：Package.swift, Package.resolved, Apps/MenuBarApp/project.yml, Config/。

**验收标准**

- 名称/别名/App 名基本过滤，结果和选中身份稳定
- 打开原菜单、显示并定位、打开应用三种动作区分
- 歧义不可精确代理，状态未知不伪装实时
- 整理设置页表达常驻／普通收纳意图与真实控制粒度，手动整理后的当前布局、失败与未知状态均有明确反馈。

**需要的证据**

- 过滤与选择状态测试
- 目录交互记录
- 来源与新鲜度展示

环境说明：实现／编译不包含 GUI 通过；涉及界面、输入或真实屏幕证据时单独申请整机 GUI 租约。

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`ecbe5fcf651a35b01a2224e5a8cdfaef70f1f7d5d3ec6d6d8de01195808bb4b4`

### APP-15｜接入选定路线的 Inventory 与 Access 适配器

归属工作包 phase：M2；推荐波次 wave：W2；角色：macOS 平台；模型候选顺序：gpt6.2sol；交付类型：code；状态：planned。

实现资源：macos_build。验收资源表达式：`{"all_of": [{"resource_class": "macos_build"}, {"resource_class": "macos_gui_exclusive"}]}`。

直接依赖：APP-04, APP-08, APP-09。额外门槛：M1_PRODUCT_GATE_PASSED。

**可修改范围**

- Packages/MenuBarPlatform/Inventory/
- Packages/MenuBarPlatform/Access/

共享文件变更请求（owner 串行处理）：Package.swift, Package.resolved, Apps/MenuBarApp/project.yml, Config/。

**验收标准**

- 只接入 M1 已有证据的 Item-action，保留条件与版本边界
- AX 有界读取、专用执行域与值快照，不阻塞主线程
- Located/actionSubmitted/menuOpen/unknown 分开返回

**需要的证据**

- 适配契约测试
- 所选路线回归记录
- 超时/缺失对象处理

环境说明：实现／编译不包含 GUI 通过；涉及界面、输入或真实屏幕证据时单独申请整机 GUI 租约。

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`cbe332ec059707b59c3d7cc27164c0e1885ee1432f376d7996c7e9972114cbb4`

### APP-16｜接入显隐后端与两区业务计划

归属工作包 phase：M2；推荐波次 wave：W2；角色：macOS 平台；模型候选顺序：gpt6.2sol；交付类型：code；状态：planned。

实现资源：macos_build。验收资源表达式：`{"all_of": [{"resource_class": "macos_build"}, {"resource_class": "macos_gui_exclusive"}]}`。

直接依赖：APP-08, APP-10, APP-12。额外门槛：M1_PRODUCT_GATE_PASSED。

**可修改范围**

- Packages/MenuBarPlatform/Visibility/
- Packages/MenuBarCore/Layout/

共享文件变更请求（owner 串行处理）：Package.swift, Package.resolved, Apps/MenuBarApp/project.yml, Config/。

**验收标准**

- 声明真实 Item/App/区间控制粒度与跨屏影响
- 提交前检查租约、几何和受保护目标，结果由新观察确认
- 新未知项目不产生隐藏意图且库存缺口有明确恢复路径

**需要的证据**

- 计划差异与范围预览
- 候选后端回归
- 新项目发现延迟记录

环境说明：实现／编译不包含 GUI 通过；涉及界面、输入或真实屏幕证据时单独申请整机 GUI 租约。

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`6fc10cb93df5ecf5d829e095ef82eeb138bbd63859c86b2102210641fc10ce3f`

### APP-17｜合成第一条完整产品流程

归属工作包 phase：M2；推荐波次 wave：W2；角色：工具链、集成与发行；模型候选顺序：gpt6.2sol；交付类型：code；状态：planned。

实现资源：macos_build。验收资源表达式：`{"all_of": [{"resource_class": "macos_build"}, {"resource_class": "macos_gui_exclusive"}]}`。

直接依赖：OPS-08, APP-10, APP-11, APP-13, APP-14, APP-15, APP-16。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- Apps/MenuBarApp/Composition/
- Tests/Integration/
- menubar-validation-lab/results/vertical-flow/

共享文件变更请求（owner 串行处理）：Package.swift, Package.resolved, Apps/MenuBarApp/project.yml, Config/。

**验收标准**

- 真实完成整理→查找→正确原菜单→保持→手动收起
- 原生动作不被重复发送，目录结果与真实目标一致
- 记录整合 candidate SHA，局部 mock 测试不代替本任务

**需要的证据**

- 整合构建
- 端到端操作与日志
- 独立验收记录

环境说明：构建与 GUI 检查分段申请资源；编码和普通编译不占 GUI 租约。GUI 敏感测量期间，同机干扰性构建暂停；all_of 不表示整个任务全程同时持有两类租约。

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`1b5f78a4b9609bb1304edec825ed18cccf048d01203df6e1c90062dc2cd358e0`

### APP-18｜处理权限撤回与诚实降级

归属工作包 phase：M3；推荐波次 wave：W3；角色：macOS 平台；模型候选顺序：gpt6.2sol；交付类型：code；状态：planned。

实现资源：macos_build。验收资源表达式：`{"all_of": [{"resource_class": "macos_build"}, {"resource_class": "macos_gui_exclusive"}]}`。

直接依赖：APP-17。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- Packages/MenuBarPlatform/Permissions/
- Apps/MenuBarApp/UI/Settings/Permissions/
- menubar-validation-lab/results/permissions/

共享文件变更请求（owner 串行处理）：Package.swift, Package.resolved, Apps/MenuBarApp/project.yml, Config/。

**验收标准**

- 拒绝/撤回 AX 后不误点、不假成功，恢复入口仍可用
- 不含像素模块时不索取不存在功能的录屏权限
- 权限和对象变化使缓存/旧 ticket 失效，动态状态清楚标记未知

**需要的证据**

- 实际权限状态矩阵
- 撤回与恢复过程
- UI/日志结果一致性

环境说明：构建与 GUI 检查分段申请资源；编码和普通编译不占 GUI 租约。GUI 敏感测量期间，同机干扰性构建暂停；all_of 不表示整个任务全程同时持有两类租约。

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`a9551e5e9bfced3d9c2e1a18a1e6b6d0c7035909a272603915bd8494518b5b1a`

### APP-19｜验证多屏、会话与最小恢复

归属工作包 phase：M3；推荐波次 wave：W3；角色：实验与验收；模型候选顺序：gpt6.1terra；交付类型：validation；状态：planned。

实现资源：macos_gui_exclusive。验收资源表达式：`{"all_of": [{"resource_class": "macos_gui_exclusive"}]}`。

直接依赖：APP-17, APP-18。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- menubar-validation-lab/results/topology-session/
- Tests/RecoveryRegression/

**验收标准**

- 菜单未关时触发变化不执行普通冲突操作
- 屏幕变化废弃旧坐标，由新恢复意图决策；救援中断如实记录
- before/applied/current 保留用户新布局，逆操作一步未知就停

**需要的证据**

- 插拔/混合缩放/上下排列记录
- 菜单保持与用户重排证据
- 故障复现及回归

环境说明：同一主机的 GUI 与干扰性构建排他；旧运行停止并恢复基线后才交接。

接入前置：所声明显示器与刘海条件必须真实具备

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`884e3ccb8e496806f3cef5c583e734ce149f4a3511c321b306a993298c84d7fa`

### APP-20｜验证系统时钟与隐私状态完整性

归属工作包 phase：M3；推荐波次 wave：W3；角色：实验与验收；模型候选顺序：gpt6.1terra；交付类型：validation；状态：planned。

实现资源：macos_gui_exclusive。验收资源表达式：`{"all_of": [{"resource_class": "macos_gui_exclusive"}]}`。

直接依赖：APP-17, APP-18。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- menubar-validation-lab/results/system-integrity/

**验收标准**

- 时钟、通知中心、控制入口、采集指示与来源提示在各阶段完整
- 覆盖采集新开始/持续/结束、展开/收起与异常退出
- 缺设备或观察条件保持 blocked，不能写默认通过

**需要的证据**

- 匹配无管理器基线
- 系统状态观察
- 候选差异与问题记录

环境说明：同一主机的 GUI 与干扰性构建排他；旧运行停止并恢复基线后才交接。

接入前置：系统状态的实际观察条件与操作者会话需具备

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`c80007c4da13ad342e38540fbdc20fc10cfd510c53785ce39ecd5db89ef618cd`

### APP-21｜验证重启、睡眠、异常退出与配置稳定

归属工作包 phase：M3；推荐波次 wave：W3；角色：实验与验收；模型候选顺序：gpt6.1terra；交付类型：validation；状态：planned。

实现资源：macos_gui_exclusive。验收资源表达式：`{"all_of": [{"resource_class": "macos_gui_exclusive"}]}`。

直接依赖：APP-11, APP-17, APP-18。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- menubar-validation-lab/results/lifecycle/
- Tests/PersistenceRegression/

**验收标准**

- 配置持久与真实分区/访问稳定分别通过
- 正常退出、强制终止、卡死与重新启动分开记录
- 未完成 journal 不按旧 PID/frame 回放，用户新设置保留

**需要的证据**

- 生命周期与故障记录
- 配置版本前后比较
- 恢复路径与适用条件

环境说明：同一主机的 GUI 与干扰性构建排他；旧运行停止并恢复基线后才交接。

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`2ca0e7782e3e6872eff48bd0edb329475bddc3da4c33499e6f22624c1e232339`

### APP-22｜可访问性、语言与常驻资源验收

归属工作包 phase：M4；推荐波次 wave：W4；角色：实验与验收；模型候选顺序：gpt6.1terra；交付类型：validation；状态：planned。

实现资源：macos_gui_exclusive。验收资源表达式：`{"all_of": [{"resource_class": "macos_gui_exclusive"}]}`。

直接依赖：APP-13, APP-14, APP-17, APP-18, APP-25。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- menubar-validation-lab/results/usability-performance/
- Tests/UsabilityAcceptance/
- docs/findings/usability/

**验收标准**

- 本工具入口/目录/过滤/设置/恢复可用键盘与 VoiceOver
- 第三方交互不低于原基线，纯键盘端到端路径单独声明
- 资源测量记录条件，不用未测数字证明低占用；无持续无效扫描
- 覆盖 APP-18 权限设置页的键盘、VoiceOver 与声明语言；记录页面/场景覆盖矩阵。
- 本卡只修改验收用例、原始记录与缺陷说明；产品修复交 APP-25 或新建具备精确范围的 UI 修复卡。

**需要的证据**

- 键盘与 VoiceOver 任务记录
- 真实延迟/CPU/内存/唤醒样本
- 语言与系统显示模式检查

环境说明：同一主机的 GUI 与干扰性构建排他；旧运行停止并恢复基线后才交接。

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`bb7b9a95eb41f4bc37597bd4930a6e15271ae4cd051e3e08a1c6e3aac5acb605`

### APP-23｜制作可安装候选与更新链路

归属工作包 phase：M4；推荐波次 wave：W4；角色：工具链、集成与发行；模型候选顺序：gpt6.2sol；交付类型：release；状态：planned。

实现资源：macos_build。验收资源表达式：`{"all_of": [{"resource_class": "macos_build"}, {"resource_class": "macos_gui_exclusive"}]}`。

直接依赖：OPS-08, APP-19, APP-20, APP-21, APP-22, APP-26。额外门槛：M3_PRODUCT_GATE_PASSED。

**可修改范围**

- Release/
- THIRD_PARTY_NOTICES.md
- docs/support/
- tools/agent-control/release/

**验收标准**

- 真实产物完成签名、公证和下载后验证，更新包校验及配置保留成立
- MIT/依赖通知、支持范围与已知限制随源码和包一致
- 发布凭据只用于受控发行作业，不进入实现代理；未授权公开发布不执行
- APP-25 或后续修复改变相关发行候选时，生成新的 APP-26 attempt：重跑受影响 M3 验证，或附独立签署的未受影响证据复用依据，再签发当前 candidate/scope/context 绑定；W3 历史裁决不直接放行 W4 产物。

**需要的证据**

- 产物 hash 与签名/公证记录
- 升级回归
- 依赖许可证与支持矩阵

实际动作前置：signing_and_notarization_authorized_for_exact_candidate, public_release_requires_existing_scope_or_final_concrete_authorization。

环境说明：先完成可审查的本地打包、许可、更新与支持说明；签名／公证／公开发布各自核对已有授权，不用待批准阻断准备工作。

接入前置：发行签名身份与托管目标尚未配置

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`503539e91e3db2e7e8d24cc834871cad8c4cabac984cd3eaad5a464d54be2045`

### APP-24｜小范围试用与首版发布裁决

归属工作包 phase：M5；推荐波次 wave：W5；角色：项目协调；模型候选顺序：gpt6.2astra；交付类型：decision；状态：planned。

实现资源：macos_gui_exclusive。验收资源表达式：`{"all_of": [{"resource_class": "macos_gui_exclusive"}]}`。

直接依赖：APP-23。额外门槛：pilot_participation_authorized。

**可修改范围**

- docs/pilot/
- docs/decisions/v1-release/

**验收标准**

- 以代表任务记录成功、阻塞、手动修理次数与恢复成本
- 独立汇总 F01-F12 的实际支持范围，不按任务卡完成率推导产品通过
- 明确发布/继续技术预览/回退到具体修复阶段的理由

**需要的证据**

- 经同意的试用任务记录
- 版本化验收矩阵
- 发布或延期决定

环境说明：同一主机的 GUI 与干扰性构建排他；旧运行停止并恢复基线后才交接。

接入前置：试用者、真实环境和公开发布动作需在进入该阶段时落实

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`b9ef8d1447ceb695cd5cb05baba7cffe36a8e3a078db350be95ce3f2e2e463cb`

### APP-25｜实现可访问性交互与本地化覆盖

归属工作包 phase：M4；推荐波次 wave：W4；角色：原生界面；模型候选顺序：gpt6.2sol；交付类型：code；状态：planned。

实现资源：macos_build。验收资源表达式：`{"all_of": [{"resource_class": "macos_build"}, {"resource_class": "macos_gui_exclusive"}]}`。

直接依赖：APP-13, APP-14, APP-18。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- Apps/MenuBarApp/UI/Accessibility/
- Apps/MenuBarApp/Resources/Localizations/
- Apps/MenuBarApp/AppShell/
- Apps/MenuBarApp/UI/Directory/
- Apps/MenuBarApp/UI/Settings/Organization/
- Apps/MenuBarApp/UI/Settings/Permissions/
- Tests/AccessibilityTests/

共享文件变更请求（owner 串行处理）：Package.swift, Package.resolved, Apps/MenuBarApp/project.yml, Config/。

**验收标准**

- 实现本工具入口、目录、过滤、整理与权限设置、恢复流程的键盘路径、焦点顺序和 VoiceOver 语义。
- 统一可见文案与无障碍标签的本地化资源，覆盖长文本、缺译回退和系统显示模式；声明已实现语言范围。
- 仅在 APP-13/14/18 已 accepted 的界面上串行修改；不借此改后端与第三方菜单行为。
- 提交编译与必要界面自检证据，独立最终验收由 APP-22 完成。
- APP-25 或后续修复改变相关发行候选时，生成新的 APP-26 attempt：重跑受影响 M3 验证，或附独立签署的未受影响证据复用依据，再签发当前 candidate/scope/context 绑定；W3 历史裁决不直接放行 W4 产物。

**需要的证据**

- 界面与字符串变更清单
- 键盘/VoiceOver 自检记录
- 对应 Mac 构建结果

环境说明：实现／编译不包含 GUI 通过；涉及界面、输入或真实屏幕证据时单独申请整机 GUI 租约。

审查规则：independent_run_required; author_child_is_not_sole_reviewer。

任务规范 SHA-256：`ccec175fd61aeceae4ab96622ab801c50d487ed4658963070a78a415beaa10bf`

### APP-26｜独立汇总裁决 M3 产品门槛

归属工作包 phase：M3；推荐波次 wave：W3；角色：独立审查；模型候选顺序：grok4.7 → gpt6.2astra；交付类型：decision；状态：planned。

实现资源：linux_cpu。验收资源表达式：`{"all_of": [{"resource_class": "linux_cpu"}]}`。

直接依赖：APP-18, APP-19, APP-20, APP-21。额外门槛：无额外 gate；仍须派工通用前置。

**可修改范围**

- docs/decisions/m3-product/

**验收标准**

- 核对 APP-18/19/20/21 的实际产物、支持范围、环境上下文与原始证据，不能拼接不兼容候选或跨 OS 成绩。
- 在同一声明范围与当前候选上逐项核对必测结果和 P0 阻断；签发符合 GateDecision 契约的通过、拒绝或未知裁决。
- No-Go 也可作为完整的独立裁决 accepted；M3_PRODUCT_GATE_PASSED 仅在正面证据与权威校验全满足时打开。
- APP-25 或后续修复改变相关发行候选时，生成新的 APP-26 attempt：重跑受影响 M3 验证，或附独立签署的未受影响证据复用依据，再签发当前 candidate/scope/context 绑定；W3 历史裁决不直接放行 W4 产物。

**需要的证据**

- APP-18/19/20/21 证据索引及内容摘要
- 独立 ReviewVerdict
- 绑定候选、范围和上下文的 GateDecision

审查规则：independent_from_all_subject_authors; trusted_authority_validation_required; no_recursive_review_of_review。

任务规范 SHA-256：`870bdf959e960dbfc016b7e39cdef566d8776ba99cb4f2106a8101a7a0a8db63`

## 门槛定义与签发

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

结构见 [依赖视图](dependency-map.md)。M0 由 APP-02 的独立验收签发，M1 产品裁决归 APP-08，M3 汇总裁决归 APP-26。签发主体必须在可信 registry 登记，报告里自称 reviewer 不产生权限。

## 修复与变更

发现问题转具体修复卡或回实现者；APP-22 不直接修改生产 UI。新提交或相关基线／契约变化使旧结论重新评估。Grok 不可用时按已列候选顺序选择独立 Astra run，记录 requested/effective 路由。

新增任务通过同一 Schema、引用、路径和生成检查，不把初始任务总数硬编码为永久规则。发行准备与签名、试用、公开发布的授权按具体动作分别核对。
