# 调酒师开源版｜Agent 开发小组架构 v0.2

设计日期：2026-11-20  
状态：经过分角色研究与复核的初版架构；尚未部署远端服务或启动工程任务。  
配套：项目计划书、项目任务书、协调板与 Agent 协作启动包。

## 1. 基本决定

开发以任务契约、Git 产物和验收证据组织。对话承担派发、讨论和解释，运行状态可在会话结束、断连或换模型后恢复。

固定八个逻辑角色：项目协调、架构、Core、Platform、UI、Validation、Reviewer、Integrator。角色、模型、执行器和主机分别建模；角色可以换模型，执行器可以换主机，验收规则保持不变。

首版先用一个协调者、独立工作区、现成 CLI 和串行集成通道启动。再把重复操作逐步自动化，避免产品开发被通用编排平台建设拖住。

## 2. 四个层次

| 层次 | 本项目职责 | 代表对象 |
|---|---|---|
| 工作规则 | 任务边界、接口、依赖、验收与授权 | AGENTS、TaskSpec、ADR、Gate |
| 协调与记录 | 领取、租约、预算、状态变更、恢复与看板 | Coordinator、Event、Receipt |
| 执行 | 启动模型与工具循环，保存结果和原生会话关联 | CodexExecAdapter、OpenCodeAdapter、可选 OrcaAdapter |
| 资源与产物 | 文件、Git、工具链、GUI、原始证据与发行 | clone/worktree、Mac/Linux、CI、Artifact |

~~~mermaid
flowchart TD
    Owner["项目负责人"] --> Lead["协调 Agent"]
    Lead --> C["协调服务与任务账本"]
    C --> B["协调板投影"]
    C --> R["执行器适配层"]
    R --> L["Linux 工作区"]
    R --> M["Mac 构建与 GUI 资源"]
    L --> PR["任务分支与 PR"]
    M --> PR
    PR --> V["独立审查与验收"]
    V --> I["单一集成通道"]
    I --> Main["受保护主干"]
    V --> C
    I --> C
~~~

协调 Agent 可以建议下一步，但不直接把自己或实现者的文字总结改成 accepted。状态迁移由协调服务依据已登记的证据与权限执行。初期人工协调也遵守同一规则并留下收据。

产品内部的 OperationCoordinator 负责菜单栏操作；本文件的 Coordinator 负责开发任务。二者是不同软件边界，不能把开发调度器和产品运行时混在同一模块。

## 3. Codex、OpenCode 与 ocra 的接入决定

### 3.1 名称与已核查状态

用户写的 ocra 与多 Agent／Codex／OpenCode／远端工作树语境最吻合的候选是 Orca ADE，但尚未得到准确 URL 确认。配置记录原始名称、候选 URL 和未确认状态，不混用其他同名项目的命令。

v0.1 编制时已读取该研究环境的 Codex CLI 0.169.0 的版本与 exec help，确认存在 JSONL 输出、结果 schema、指定目录、resume/fork 和 worktree 参数。没有启动模型推理任务，因此不据此宣称指定模型在远端已可调用。[C2]

v0.1 编制环境未安装 OpenCode。官方当前文档为 V2，Agent 与权限使用 agents、permissions、shell、subagent 等字段；实际接入需固定执行主机的版本与协议摘要。[P1][P2]

Orca 官方将编排标为 experimental，并说明当前编排面板／开关暂不可用，旧 run/run-stop 等入口已退役。Run 是持久命名空间与 inbox，Task 和 Dispatch 才承载任务及执行尝试；Run 不自动调度。Orca 接入必须先做实际 host 能力检查。[O1]

### 3.2 推荐接入顺序

CodexExecAdapter 先实现：协调器分配工作区，固定 CLI 版本，任务文件输入，记录 JSONL、退出码、结果与 session ID。输出 schema 检查结构，不能证明测试已经运行。

OpenCodeAdapter 第二实现：先根据实际 help 验证单次执行、指定 agent/model、JSON 输出和恢复指定 session。当前文档提供 standalone 私有服务方式；优先避免把各 worker 接到不清楚归属的共享后台服务。[P3]

OrcaAdapter 可作为操作入口和远程会话承载。项目协调器与 Orca 只能有一个派工权威；如果项目协调器调度，Orca 的原生 Dispatch 作为 run 的映射，不再另起一个会独立派相同任务的调度循环。

需要长会话、细粒度中断与审批回传时，再评估 Codex app-server。首版不要求 CLI、SDK、app-server 同时实现。

### 3.3 适配器共同契约

| 方法 | 契约 |
|---|---|
| probe | 记录版本、协议、平台、模型目录、授权状态和工具能力 |
| start | 接收持久 attempt 与幂等键，返回实际 session／dispatch／进程收据 |
| observe | 获取增量输出与当前状态，不把事件流当持久事实全集 |
| interrupt | 请求停止当前工作，返回请求是否送达；不代表进程已退出 |
| reconcile | 断连后核对原生 session、进程、Git 与产物 |
| collect | 归档提交、diff、退出状态、原始检查输出和摘要 |
| close | 确认停止并保留产物后释放资源 |

每个工作区只有一个创建者：项目工作区管理器已经创建 worktree 时，不再叠加 Codex 的 managed worktree。恢复必须指定原生 session ID，不能使用“最近一次会话”跨任务续接。

Orca 远端的项目、执行工具与认证留在服务器；客户端登录不会自动传过去。远端断连不等于 worker 停止。[O2]

OpenCode 当前事件 API 的契约允许断连漏事件、慢消费者溢出。因此协调板必须重查 session 与持久产物，不从缺失的事件序列猜测任务结束。[P4]

## 4. 模型与岗位路由

| 项目别名 | 用户指定模型 | 初始用途 | 调用前检查 |
|---|---|---|---|
| gpt6.2astra | GPT-6.2 Astra | 架构、复杂协调、关键状态机审查、跨模块冲突 | 执行器实际 model ID、reasoning 选项、权限与额度 |
| gpt6.2sol | GPT-6.2 Sol | 模块实现、测试修复、适配脚本、日常集成 | 同上 |
| gpt6.1terra | GPT-6.1 Terra | 界面观察、交互复现、可访问性与视觉记录 | 图像与 GUI 工具是否由实际 host 暴露 |
| grok4.7 | Grok 4.7 | 独立反例审查、替代方案与实现复核 | OpenCode/provider 路由、工具调用和结构化结果 |

官方文档已列出上述 OpenAI 模型，Grok 官方也公开 grok-4.7 标识；这只确立公开名称，不证明目标账户可用。[C1][X1]

注册表分开保存 requested label、documented candidate ID 与 effective provider/model ID。effective 在真实执行前保持 null；每次 run 保留最终生效配置。不能把 OpenAI 在 Codex 可选，推导为相同 ID 一定能通过 OpenCode 的某条 API 路由调用。

模型调用状态建议为 unresolved、catalog_seen、invocation_verified、blocked。目录可见仍需在已授权环境做最小调用才能验证该次访问。该证明记录时间、执行器版本、认证类型与能力，不当作永久可用保证。

初始分工是候选方案，运行同类代表任务后再调整。跨模型审查可以提供不同角度，但不自动消除共同盲区；独立证据与可重现行为继续优先。

不设置静默换模型。路由不可用时，按事先配置的替代规则重排并更新 effective model，或者保留阻塞。模型名称本身不会提供 Computer Use 工具、Mac 桌面或辅助功能授权。

## 5. 任务、执行尝试和产品门槛

TaskSpec 是要完成的工作；RunAttempt 是一次执行；Gate 是跨任务的产品判断。一项任务可有多次尝试，一个完整失败实验仍可能交出有效研究结论。

### 5.1 TaskSpec

任务目录卡片使用 id、phase、wave、role、model_alias/model_candidates、runner_candidates、compute_class、depends_on、execution_gates、scope_paths、acceptance_criteria、evidence_required 等字段。TaskSpec 的不可变内容以 task_spec_fields 的投影为准，task_spec_sha256 使用 UTF-8、键排序、紧凑 JSON 的 SHA-256。卡片中的状态与实际执行字段是投影，不能混进规范摘要。

scope_paths 是本包的写范围字段；write_scope 只作为中文说明中的概念，不再另立第二个同义结构。任务卡 id 在运行收据中作为 task_id。预算、真实工作区、主机、租约、实际模型和授权登记在 RunManifest；当前规划卡没有凭空填写这些运行事实。

phase 是归属工作包，wave 是推荐波次。运行调度看当前依赖、门槛、授权与资源，不把波次当作可派工状态。

模型消息只引用任务版本，不在执行中偷偷修改验收条件。范围变更先产生新版本，失效受影响的旧检查。

### 5.2 RunAttempt

至少保存 task_id、attempt_id、parent_attempt_id、fencing_token、任务摘要、host、执行器版本、requested/effective model、base_sha、工作区、原生 session、开始与结束状态、预算和收据。

默认一次独立实现任务对应一个分支，例如 task/app-09/a01。失败重试使用新的 attempt ID，不能覆盖旧日志。继续已有会话保留原 attempt 关系，实际新执行是否需要新代次由协调器记录。

### 5.3 状态

代码与版本化文档任务的主路径：

~~~mermaid
stateDiagram-v2
    [*] --> Planned
    Planned --> Ready: 前置满足
    Ready --> Running: 已确认启动
    Running --> Submitted: 提交产物
    Submitted --> Validating: 独立检查
    Validating --> ChangesRequested: 需要修改
    ChangesRequested --> Ready: 新尝试就绪
    Validating --> MergeQueued: 检查通过
    MergeQueued --> Integrated: 已确认合并
    Integrated --> Accepted: 产物与验收完成
    Ready --> Blocked: 资源或条件不足
    Running --> Blocked: 启动或运行结果未知
    Blocked --> Ready: 已对账并解除
~~~

cancel_requested、launch_unknown、running_unknown 等属于 RunAttempt／资源状态，不挤进一列任务状态中掩盖细节。cancelled 表示该任务被取消，failed 表示某次尝试的结果，不自动抹掉任务。

纯实验／审查任务可以在不可变证据归档并独立验收后进入 accepted；如果同时产生代码或版本化协议变更，相关改动仍走 Git 集成。不能伪造一个合并 SHA 来填空。

M1_ROUTE_EVIDENCE_READY 只要求至少一条完整研究可供裁决，允许负面结论。M1_PRODUCT_GATE_PASSED 另要求已声明范围内有真实 verified 路线且完整性阻断清零。前者不能代替后者。

## 6. Git 工作方式

### 6.1 工作区所有权

每个写入任务一个唯一写入负责人、一个分支、一个 checkout。受信同机环境可以使用 worktree；远端优先独立 clone。Git worktree 共享仓库元数据和 refs，不是权限沙盒。[G1]

clone 也只隔离代码与 Git 元数据；同一 OS 用户下的进程仍可能访问其他路径。真正的执行隔离由独立用户、隔离环境和受控凭据提供。路径协议与 diff 检查不能冒充操作系统访问限制。

根 Package.swift、Package.resolved、XcodeGen project.yml、xcconfig、CI 工作流和顶层产品契约归相应所有者串行处理。已定义 target 内的普通源文件通过目录发现，生成 pbxproj 不手改；具体方案见 [构建布局 ADR](adr/build-layout.md)。其他任务遇到需要改共享文件时，提交变更需求；协调器可以转交所有者或重新分配排他范围。

首版不维护长期 integration 分支。任务分支小批量、持续合入受保护 main；集成候选为临时 ref。这样“最后合并”发生在每个可验收任务结束，不积累到项目尾声一次解决全部冲突。

全新仓库的根提交由已授权的初始协调会话建立并记录人工审查收据；它是一次明确的 bootstrap 事件。保护规则建立后立即关闭该例外，不让后续实现任务以初始化为由跳过审查。

初始化采用 BOOTSTRAP_BASELINE 收据，保存已审查材料、初始 commit、仓库配置和检查结果，不伪造一个尚不存在的 PR 或 merge SHA。

### 6.2 必须分开的四类版本

| 对象 | 记录 |
|---|---|
| 实现提交 | base_sha、head_sha、task_spec_sha256、contract_sha |
| 独立审查 | reviewed_base_sha、reviewed_head_sha、reviewer_run_id、审查结果摘要 |
| 集成验证 | candidate_sha、candidate_tree_oid、target_base_sha、环境与测试收据 |
| 真实合并 | merge_commit_sha、merge_tree_oid、parents、远端确认时间 |

contract_sha 指约定的接口契约版本引用；task_spec_sha256 是任务规范内容摘要，两者不要混用。Git 对象 ID 不预设全部只有一种长度，由实际仓库对象格式确定。

审查只对已绑定对象有效。新提交、rebase、冲突解决、接口版本变化或影响相关行为的基线变化，都触发重新检查。轻微改动可以按风险复用未受影响证据，但必须记录理由，不能直接搬用旧的总体通过结论。

### 6.3 合并顺序

1. 从任务提交收集不可变 head 与差异，检查写入范围。
2. 独立 reviewer 读取该版本及契约；独立验证环境重跑必要检查。
3. 在最新目标基线上生成候选，记录 candidate 与 tree。
4. 候选通过后进入单一集成队列。
5. 合并前核对 head、基线、规则与已授权范围；基线变化则重建候选。
6. 读取实际 merged 状态、merge commit、tree 与 parents。
7. 检查实际产物与已测候选的对应关系；若不相符，不进入 accepted。
8. 归档证据后更新协调板，再释放下游依赖。

没有文本冲突不等于没有语义冲突。接口改变、默认值改变和状态机次序尤其需要在组合候选上验证。

GitHub 原生 merge queue 受仓库和套餐条件限制。实际不可用时，使用单一人工或服务队列，保留受保护分支与基线检查；不以强推 main 模拟原子合并。原生 queue 的 CI 要响应 merge_group。[G2]

GitHub 合并 API 的 sha 约束 PR head，不锁 base。异步请求的 202 表示已接受，enqueued 表示已入队，均不等于已经合并；后续必须读回真实结果。[G3]

单一集成租约持有到异步结果明确结束，平台同时启用所需的最新基线检查并禁止集成身份绕过规则。合并前读取一次 base 不能防止提交期间的基线推进；发现推进时失效候选并重新排队。若其他写入者绕过保护造成未预期产物，不自动改写主干历史，保留事件、暂停 accepted 并生成具体修复或回退任务。

## 7. 协调服务：小而明确

### 7.1 实现选择

薄自动化服务拟采用 TypeScript、接入时固定的受支持 Node.js LTS 和本机 SQLite。包内 Python 工具只执行离线规范检查、文档生成、门槛参考求值与封装，不写 live 账本，也不启动执行器。未来服务需通过同一契约与语义样例，不能让两种语言各维护一份独立的任务真相。CLI 以结构化参数启动，不把任务文本拼进 shell 命令。Web 界面不是首批必要条件，先输出 JSON 与 Markdown 看板。

SQLite 放在协调主机的本地磁盘，单写服务持有连接，运行态不作为 Git 冲突文件共享。若使用 WAL，遵守其同主机要求、耐久写入与一致性备份，并核对实际链接的 SQLite 版本；官方当前修复说明包含 WAL-reset 相关版本要求。[D1]

计划与代码进入 Git；运行状态与事件进入账本；大型证据进入独立产物目录或受控存储，Git 记录 manifest 和摘要。看板是投影，不再另建一个可独立改状态的权威数据库。

### 7.2 调度算法

可派单任务必须同时满足：

- depends_on 的任务已 accepted；
- 所需 gate 的证据满足，unknown 不当作 true；
- 模型、执行器、host 和授权 profile 已匹配；
- 写入范围与共享文件租约无冲突；
- GUI／构建资源可用；
- 全局和父任务预算、会话数与深度仍有空间。

同优先级中优先处理关键路径、已完成实现的评审和长期等待的任务。先把候选集合筛正确，再排序；不使用复杂优化模型弥补错误依赖。

4 个活动会话包含协调、评审与子 Agent，3 个 writer 只是上限。先预留审查容量再派实现；创建子 Agent 前必须取得可用槽位。容量不足时在当前任务内完成辅助工作，或在执行器确认可恢复暂停后释放父会话槽位；不能让所有父任务占满槽位进入 waiting_children。工作区所有权、GUI 租约与会话槽位分别处理，暂停不自动证明资源可交接。

预算按父任务累计子 Agent 与重试；预留后才启动。实际花费不足时释放余额，unknown 用量保留不确定并禁止无限派单。金额、订阅额度和 token 分别记录；首次参数由项目预算配置决定。

### 7.3 启动、租约与过期结果

一次启动采用本地事务：领取任务、增加 fencing token、预留预算、记录 launch intent 和 outbox；事务提交以后才调用执行器。

执行器适配器持久记录幂等键与原生收据，至少支持按 attempt 查询。数据库、进程和远端 API 之间没有天然的 exactly-once 事务，所以启动超时记 launch_unknown，先对账，再决定继续、取消或人工处理。

fencing token 是该次运行的有效代次。心跳、提交和完成事件必须带 task_id、attempt_id、token；旧 token 的结果进入历史，不修改新运行。

租约到期只撤销旧运行的提交权，不证明它的 shell 或 GUI 动作已经停止。工作区、主机和进程状态分开管理；确认旧进程退出、收集产物并恢复必要基线后才释放资源。

## 8. 远端部署与 Mac 资源

最小部署可以由一台已有 Mac 同时承担协调与构建；有远端 Linux 时，将文档、纯逻辑、审查和非 Mac 脚本分出去。未具备远端主机不妨碍按同一协议在本机起步。

连接优先复用已授权 SSH 或受控私网。不为了看板开放一个无认证公网执行接口。主机 registry 仅登记别名、能力、连接引用和认证类型；密钥留在执行主机的已有安全机制中，不写入任务或仓库。

macos_build 要固定 Xcode／SDK 与独立构建目录。macos_gui_exclusive 还要求真实可用的 console 会话、权限状态和任务所需显示器条件；SSH 可连接不证明这些条件成立。

GUI 任务开始前确认无冲突管理器与恢复入口，结束后记录实际状态。断连或取消后若不能确认输入停止，主机进入 quarantine，不让新 Agent 接手继续点击。quarantine 是资源状态，可以由已登记操作者或恢复流程解除。

Mac 验收日志由可信的验证入口采集，并与实际源码和环境绑定。实现 Agent 自己写的一段 passed JSON 或一个 SHA，只能成为待核查材料；内容摘要证明文件一致，不能独自证明测试真实执行。

## 9. 子 Agent 的规则

子 Agent 分两种：

**只读辅助**：查源码、找调用点、分析日志、提出反例。使用父任务的参考快照，产物返回父任务，计入全局预算与会话数。

**独立写入子任务**：在协调板登记 child task，分配独立 scope、工作区、分支、验收和预算。父任务进入 waiting_children；所有子任务满足合并要求后，父任务整合自己的部分。

waiting_children 是 run 的等待原因，不直接增加一个未经定义的任务状态；父任务的状态、槽位占用和工作区所有权继续按现有状态机记录。

默认最大深度 1、每任务最多 2 个子 Agent。子任务的权限、网络与预算不得因递归而扩大；父任务取消后，跟踪并确认全部子进程停止，保留已产出的提交。

工具原生 subagent 不等于上述约束自动成立。Codex 提供子 Agent 工作流；OpenCode 的 Agent 权限按其配置处理，不能假定父角色的限制必然成为子角色的上限。[C3][P1][P2] 每次加载原生角色配置时，都需校验项目政策并记录实际生效权限。

父任务作者的子 Agent 不充当该任务唯一独立 reviewer。审查 run 从已提交版本和验收契约开始，避免把作者自述当成结论。

## 10. 协调板

协调板至少提供三个视图：

| 视图 | 回答的问题 |
|---|---|
| 任务 | 哪项任务处于哪个阶段、依赖谁、下一步是什么 |
| 运行与资源 | 谁正在执行、用什么模型/执行器/机器、租约与预算是否有效 |
| 证据与集成 | 哪个提交被谁审查、哪些检查在哪台机器完成、是否真实合并 |

每张任务卡显示目标、角色、候选与实际模型、执行器版本、host、依赖、write scope、当前 attempt、base/head/candidate/merge、检查摘要、阻塞原因与下一步。

不把推理全文当看板主要内容。正常状态展示产物和下一步，异常才展开相应事件与日志。未知模型、缺失证据和未连接主机明确显示未核验。

本轮交付的是由 tasks.json 生成的规划快照；全部工程任务 planned，run／PR／SHA 均为空。它不是已连接远端的实时控制台。实际运行中状态由单写协调者更新，worker 不同时修改看板文件。

## 11. 授权与自主运行边界

任务接入时建立项目授权 profile：仓库、分支前缀、可用工具、预算、可以自动进行的提交／PR／合并范围，以及仍需负责人裁决的范围变更与公开发行。

一旦已有授权覆盖，协调器持续推进，不为每次测试、修复或普通提交重复询问。新的破坏性动作、超预算或超范围改变返回具体待决事项；先完成已经授权且可审查的准备工作。

worker 不持有 main 直接写权限或发行密钥。即使同一个模型可担任 integrator，真正合并凭据也只由受控集成入口使用，不放进模型可任意执行的 shell。

当前轮次只设计与生成文件，没有批准一个尚未指定的仓库、服务器或账单自动执行。启动包以 deployment.enabled=false、空主机与空远端交付。

## 12. 小型协作演练与验收

接入后的首轮演练用低影响任务验证：

1. 两个任务修改不相交路径，分别提交并形成候选。
2. 一个任务尝试越界修改共享文件，被检查拦下并转交所有者。
3. worker 报完成但没有有效提交或证据，任务保持待验收。
4. 审阅后追加提交或基线推进，旧批准不自动适用。
5. 启动超时后对账，确认没有重复运行。
6. 子 Agent 消耗父预算并遵守全局并发，不绕开资源限制。
7. GUI lease 到期但旧进程仍在，主机不被重新分配。
8. 合并 API 返回 accepted/enqueued，协调板不提前改成 integrated。
9. 研究结果全部失败，仍能完成裁决，但产品 M1 gate 保持关闭。
10. 协调进程重启，能够从账本、Git 和原生 session 恢复状态。

这些是未来协作基础设施的验收场景，本轮只检查规划数据、引用、DAG 与模板结构，没有执行这些远端演练。

## 13. 复核后的修正

- 把 Orca 从唯一不可替代编排后端调整为候选适配器。
- 把任务 accepted 与产品路线 verified 分开，允许研究完整地失败。
- 将 Integrator 与 Reviewer 分开，集成者修改代码后仍需独立审查。
- 把构建资源与 GUI 验收资源分别登记。
- 将 lease 失效与进程停止分开，避免两名 Agent 接管同一桌面。
- 将实现、审查、候选和真实合并的 SHA 分开，防止验证错版本。
- 保留 bootstrap 手动路径，避免“先完成调度器，才能开发调度器”的循环前置。
- 确认当前交付是设计与初始看板，不包含运行中的远端服务或产品通过成绩。

## 参考资料

核查日期 2026-11-20。平台页面可能继续变化，执行时固定实际版本与能力记录。

[C1]: https://learn.chatgpt.com/docs/models.md
[C2]: https://learn.chatgpt.com/docs/non-interactive-mode.md
[C3]: https://learn.chatgpt.com/docs/agent-configuration/subagents.md
[C4]: https://learn.chatgpt.com/docs/environments/git-worktrees.md
[P1]: https://opencode.ai/docs/agents/
[P2]: https://opencode.ai/docs/permissions/
[P3]: https://opencode.ai/docs/cli/commands/
[P4]: https://opencode.ai/docs/api
[O1]: https://orca.dev/docs/cli/orchestration
[O2]: https://orca.dev/docs/remote-servers
[G1]: https://git-scm.com/docs/git-worktree
[G2]: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue
[G3]: https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request-asynchronously
[D1]: https://sqlite.org/wal.html
[X1]: https://docs.x.ai/developers/models/grok-4.7

## 本轮修订：明确的机读边界

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

M0 由 APP-02 的独立验收签发；M1 产品门槛由 APP-08 的独立裁决签发；M3 增设 APP-26 汇总 APP-18/19/20/21 的当前候选证据后签发。签发角色是登记过的 reviewer/lead，任务作者及其子树不能作为唯一独立签发者。权限来自可信 authority registry，不来自 JSON 自称的 role。

gate_definitions 原有 all_of / any_of 结构；v0.2 加入 gate_ref、gate_policies 和离线 gate_eval.py。结构图保留替代分支，不把 any_of 的所有候选误算为强制依赖；候选未选、资源未知时不输出虚构的单一关键路径时长。OPS-07 的产物由 deployment.activation_gate 消费，人工 bootstrap 不等待它，避免自举循环。

命名固定为 TaskSpec、RunManifest、WorkerResult、ReviewVerdict、IntegrationReceipt、GateDecision。六份对应 Schema 位于 contracts/；templates/ 中的 null 和 template_not_executed 是填写提示，不能通过正式收据校验。原始 Markdown 审查报告仅作人读说明；推进 MergeQueued 必须读取机读结论、核对当前版本、检查必要独立验证，随后验证实际集成候选。

GateDecision 绑定 task/spec/contract/base/head/candidate、author/reviewer run、scope 与 context manifest、证据摘要和有效期。独立签发登记、运行父链、原始字节与当前绑定仍需由可信调用方提供。离线工具可以验证给定输入的一致性，不能证明一份任意本地 JSON 来自真实可信主机，更不能替代远端权限和实际执行回执。候选、范围、环境或相关契约改变时，旧门槛不得沿用为总体通过。

所有生产 UI 无障碍与本地化修改移到 APP-25；APP-22 是独立验收。OPS-03/05/06 属于工具链、集成与发行角色；Platform 保持 AppKit/AX/几何职责。APP-17/18 编码、编译与 GUI 验收分段持有资源。基线、路径归属与文档生成规则分别见 baselines/provenance.json、coordination/path-ownership.json 和 tools/render_docs.py。
