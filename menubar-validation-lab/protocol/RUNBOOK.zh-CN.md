# 菜单栏候选后端对照验证：执行手册

这是一套实验协议与证据判定工具。当前交付环境是 Linux；本包在 Mac 上的编译、启动、菜单行为、权限行为和性能均为 **not_run**。Python 评估器测试通过，只说明判定程序的这些测试分支工作，不代表任何 macOS 能力通过。

## 本轮实际范围

- 无管理器基线：确认 Fixture 和系统原有菜单行为，作为同条件比较对象。
- legacy geometry：在目标旧系统（例如本项目拟测的 26）上验证。
- guarded native overflow：在 27 上验证带容量／阈值保护的多 spacer 候选。它与未修改的 MenubarHide 上游提交是不同实验对象。
- private read-only probe：本轮只探测框架、类或符号是否可见，**不激活 assertion**。探测成功不满足任何显隐、交互或恢复案例。私有行为实验必须另行准备受控 Mac、恢复验证与系统状态测试后开展。

每个后端必须记录 strategy_id、固定源码 revision、配置 SHA-256；不要混用原版上游、修改版与只读 probe 的证据。需要比较其他上游实现时，单独建立结果，不覆盖已有记录。

### 当前 Controller 的实际能力

Controller 是几何实验原型：它改变自己创建的占位项宽度，没有实现完整菜单栏管理器。窗口中的「收起 10 秒」会立即请求收起；「5 秒后收起」安排一次延迟触发，便于操作者提前打开菜单。收起被接受后，另一个 10 秒计时器请求展开。它们都运行在应用内，不是独立看门狗；主线程卡死时不保证执行，日志中的请求也不证明屏幕已经恢复。

| 目标 | 当前可做的实验 | 填表边界 |
|---|---|---|
| 几何收起与展开 | 手动放置占位项，发起请求，观察真实布局及原生访问路径 | 容量／阈值保护拒绝时记录拒绝原因；隐藏前置条件未建立，不计隐藏成功 |
| 同应用三项、动态数值、左右键及 Option | 用户直接操作实际可达的原项或系统原生溢出入口，并对照 Fixture 日志 | 只报告实际路径；没有单项搜索、镜像第二栏或跨应用点击转发 |
| 菜单仍打开时布局变化 | 点击「5 秒后收起」，在触发前打开 Fixture 菜单，观察收起和到期展开是否中断操作 | 属于几何触发的干扰实验，可支持 MB-06 的观察；不证明 MB-10 的规则仲裁 |
| 三分区与真实规则 | 本轮没有对应实现 | MB-08、MB-10 标 unsupported；按钮或定时器不能替代 |
| 菜单结束后的自动恢复 | 没有菜单会话锁或菜单结束回调；可手动展开或退出 Controller | MB-09 的 menu_end 不能因 10 秒到期展开而通过；disable_backend 可以单独实测 |
| 用户排序、应用重启后的布局恢复 | 没有持久排序、项目重匹配或其他 App 布局回放 | MB-11、MB-12 的完整目标 unsupported；可以另记本工具旧计时器是否被用户新操作取消 |
| 代理超时与重复激活 | 没有点击代理，Fixture 也不制造受控 AX 超时 | MB-22 的完整目标 unsupported；不能通过普通点击推断 |

未实现某项不是已观察到缺陷。它会限制正式支持范围；其中必测恢复条件未完成时，原型整体仍不能获得发布通过。若试验已经造成错误目标、菜单中断或状态误遮蔽，则应保留 failed，不能再以「尚未支持」抹去结果。

## 先建立可比较的条件

同一 comparison_group_id 内，应使用相同的匿名 machine_id、OS build、体系结构、Fixture 源码版本、应用清单、屏幕拓扑、菜单栏自动隐藏设置、独立 Spaces 设置及权限条件。外屏、缩放或系统版本不相同，就另建实验组和相应基线。

app_inventory 指同一套受测应用与系统组件，条目中记录相关版本；候选管理器单列在 backend，不因为基线没有运行 Controller 就改变受测清单。Fixture 和前台应用应相同，左侧应用菜单的展开状态及占用条件也应相同。打开 Controller 窗口会激活 Controller；「隐藏窗口」只隐藏窗口，不自动切回原先前台应用。准备触发后，操作者须切回基线选定的前台应用，再打开待测菜单，并记录该条件。评估器不读取前台应用，也不测量左侧菜单占用。

Controller 自己的 LAB 图标、占位项及其间距，是候选条件相对无管理器基线的实验差异，应在观察记录与截图中保留。不要声称两者桌面布局完全相同。可另存 Controller 已启动、保持展开时的快照，用来识别这些新增占用；它不能取代无管理器基线。

variant.context 是对 run.environment 的局部覆盖。例如权限变化后的 permission_profile 可以写在其中；未写的屏幕等字段继承 run.environment，不能靠省略解除条件。显式把 screen_topology 置空会被拒绝。评估器检查有效条件，并要求候选通过的每个基线适用变体，都有相同条件下通过的对应基线变体。不同真实屏幕布局仍应另建 comparison_group，不在一个组内混记。

fixture_run_id 可以在重置或重启后变化；它用于追踪本次日志，不充当稳定 Item 身份。固定 Item 的 AX ID 为：

- org.menuvalidation.fixture.alpha
- org.menuvalidation.fixture.beta
- org.menuvalidation.fixture.gamma

Fixture bundle 为 org.menuvalidation.Fixture，三项可见标题分别为 FA、B 000（动态计数）和 FC。动态标题不能作唯一身份。完整事件定义见 Fixture/README.md。

建议每次操作前重置场景，记录新的 fixtureRunID，再导出该次 JSONL；导出是快照，后续发生的事件需要再次导出。若看到 loggingStopped、日志缺失或 Fixture 未正确运行，应停止判定成功。

## 执行顺序

### 1. 无管理器基线

先正常停用其他菜单栏管理器，确认其限制已撤销。不要为了测试强制结束无关应用或覆盖系统配置。按根目录 README 在 Mac 构建 Fixture，先确认构建与启动本身成立；Linux 上的语法检查不能代替这一步。

把 results-template.json 复制到独立的 runs/baseline/results.json。填写环境，将 run_role 改为 baseline、backend.id 改为 none；只有真正进行 Mac 实验时才写 run_kind=mac_runtime。记录带时区的 started_at_utc、finished_at_utc。

逐项执行 test-cases.json 中适用于 baseline 的案例。候选专属的显隐／恢复案例可标 not_applicable，其他缺设备、缺样本或无法复现的项目标 blocked，不用 not_applicable 消除覆盖缺口。基线可限制声明的 capability 范围，但候选所声称支持、又适用于基线的能力必须有匹配基线；始终必测的系统完整性项目不能被范围声明绕过。

共同案例中提到收起、规则或其他候选动作时，基线不制造一个替代管理器；它执行相同的用户点击、等待、系统状态变化及结束操作，记录原始行为。候选带来的布局动作在候选运行中加入。基线只能证明无管理器时的对应观察成立，不能为候选恢复或仲裁逻辑背书。

先确认右键、Option 和滚轮在原始环境的实际行为。Fixture 把无法确定输入归因的 activation 标为 unknown；这不能充当 right 或 option 成功证据。滚轮派发取决于原生事件路径，基线未建立就不得把候选动作判为通过。

### 2. 每个候选独立运行

每次只运行一个管理器候选，保留普通可见窗口中的恢复入口。先记录展开时的顺序和可达性，再收起，执行相同任务。实验自动展开计时器属于实验行为：如果它打断正在使用的菜单，应记录该结果，不能在判定时忽略。

对当前 Controller，操作顺序如下：

1. 点击「显示定位标记」，手动用 Command 拖动，使 0–6 连续位于待测图标右侧、LAB 左侧。确认布局并记录；程序没有自动核验拖放位置。
2. 保存展开状态。准备观察原菜单时，点击「5 秒后收起」，隐藏实验窗口，切回基线选定的前台应用，在触发前打开 Fixture 的目标菜单。比较触发前、触发时及 10 秒到期请求展开后的行为。
3. 查看 Controller 是否记录 collapse_refused。被拒绝时保留具体原因，不把点击按钮、分配长度或计时器到期直接填成成功。再次试验应重新设置条件和日志区间，不覆盖前次结果。
4. 完成目标操作后再导出 Fixture 日志和 Controller 的展开快照。「展开后导出快照」本身会请求展开，不能在待测菜单仍打开时把它当成无干扰观察动作。

根据实际准备验证的范围填写 claimed_capabilities；正式 Mac 验收记录不能为空。填写是待核验的声明，仍需对应案例及必测条件通过。Linux preflight 模板可以保持空声明和 not_run。当前缺少的三分区、搜索、规则、菜单锁和排序恢复按上表处理，不用挑选少数按钮成功来填写整项能力通过。

优先完成原菜单访问与系统完整性，再做规则、恢复和环境变化。发现错误目标激活、输入被抢占、系统隐私状态误遮蔽或用户修改被覆盖，应立即停止继续扰动，使用实验窗口撤销限制，保存失败证据。

### 3. 状态与敏感资源案例

时钟案例必须验证通知中心是否保持打开、是否能关闭、快捷键是否工作，以及指针是否被移动。只有菜单窗口或进程存在，不能证明任务成功。

摄像头和麦克风由操作者在明确选择的应用中手动启用，本包不会自动录制。只需要观察系统指示、名称提示和访问面板，不保存音视频。先比较无管理器状态，再测试候选收起、新采集开始以及采集持续期间再次收起；“开始时展开一次”不足以证明后续状态不被误遮蔽。

多屏场景需要对应设备。没有刘海加外屏、混合缩放或上下排列的实际配置，就保留 blocked。不同权限 profile 的建议标签包括：

- ax_on_capture_off
- ax_on_capture_on
- ax_off_capture_off
- ax_revoked_capture_off
- ax_on_capture_revoked

这些标签描述本次实验条件，不代表评估器自行读取了系统授权状态。

当前几何原型没有 AX 点击代理或屏幕镜像流程。可以观察无授权时其已声明的几何能力，但不能用「没有报错」推断代理降级、旧快照失效或授权撤回处理成功。没有可撤回的授权前态时，撤回变体标 blocked 并写明条件；明确没有对应能力时标 unsupported。不要为完成表格而臆造授权变化。

### 4. 结束并恢复

正常退出或停用候选，确认所有本工具限制已撤销，保留用户原先在系统设置中关闭的项目。崩溃恢复仅针对本实验管理器单独测试，不强制结束其他应用。保存实际需要的手动恢复步骤，它们也是结果的一部分。

## 如何填结果与证据

test-cases.json 含 24 个任务、50 个覆盖变体。results-template.json 已包含全部条目，初始都为 not_run。每个变体填写 status、reason、observations、context 和 evidence。

- passed：当前 Mac 条件下，实际任务满足预期并有证据。
- failed：尝试后不满足预期。没有完整证据的失败报告仍不能放行；之后补证据，不将它删成通过。
- blocked：缺设备、权限、样本、恢复保障或其他前置条件。
- unsupported：后端明确不提供此能力；不必称为 bug，但不能计入该能力正式支持。
- unknown：动作可能发生、状态不确定等情况，不能当成功。
- not_run：没有执行。
- not_applicable：仅用于协议明确排除的 run_role。

已经观察到的失败必须保留为 failed，即使最后决定不提供该功能。评估器会阻断任何状态中提交的 machine_verified 负断言（matched=false 或 expected 与 observed 不同），防止把失败证据保留着却将状态改成 unsupported。它不会读懂自然语言是否描述了失败，也不解析任意附件里的失败语义；操作者必须正确标记结果。删除记录、改写历史或遗漏观察，不在文件结构检查可以保证的范围内。

每个 evidence 必须绑定 run_id、case_id、variant_id，提供唯一 id、本次运行区间内的 observed_at_utc、相对当前结果目录的 artifact 路径和 SHA-256。证据文件不能指向目录外，也不能重复使用同一个 evidence id。

evidence.kind 的意义必须保持清楚：

| 类型 | 可以证明什么 | 不能直接推出什么 |
|---|---|---|
| machine_observation | Fixture 原始事件、环境快照等数据确已被提交 | 事件发出不代表正确原菜单已被用户操作 |
| machine_verified | 提交的固定版本验证器对一个明确断言给出的核验记录 | 本评估器不会重跑该验证器，也不会重新执行 Mac UI |
| operator_attested | 操作者明确记录自己看到的菜单、状态、操作结果及副作用 | 不是机器自动测试，也不是加密认证的观察者身份 |

本协议的完整 UI 成功都要求 operator_attested。保留日志作为补充，同时记录“打开了哪一个菜单、能否继续选择、是否被提前关掉、焦点和指针如何变化”。仅有 menuOpened、menuClosed 或 activation 不足以通过：它们并不包含关闭原因及全部用户可见结果。

machine_verified 还需提供 assertion_id、verifier、verifier_revision、expected、observed 与 matched=true。assertion_id 必须属于该案例列出的 machine_assertions。本评估器只检查这些字段的结构、绑定、时间、文件 hash 和提交的值是否一致；输出明确标注 structure_and_artifact_hash_only、replayed_verifiers=0。不要把这一步描述成重新跑过原始实验。

人工证据记录应有观察者标识与 statement。若观察者是本机 AI 智能体，应如实写明，不冒充人类。可保存一份普通文本观察记录，必要时附局部截图；避免上传无关桌面、文件名、日历或账户内容。

## 结果文件与评估命令

从包根目录运行：

    python3 tools/evaluate_results.py protocol/results-template.json --output protocol/current-evaluation.json

初始模板预期退出码为 2，release_verdict=blocked_by_environment、accepted_pass_variants=0。这是当前 Linux 环境的正确结果，不是脚本执行失败。

收集真实基线及候选证据后运行：

    python3 tools/evaluate_results.py runs/candidate/results.json --baseline runs/baseline/results.json --output runs/candidate/evaluation.json

此处的目录是建议目录；证据文件路径以每个 results.json 所在目录为根。不能把生成的 evaluation.json 改名当原始 results.json 再喂给评估器。

配置和源码 hash 应针对实际构建输入生成；fixture_revision 与 backend.revision 接受完整 git_commit 或 source_sha256。测试目标变更后必须重新固定协议：protocol_sha256 是整个协议 JSON 的规范化 SHA-256（UTF-8，键排序，ensure_ascii=False，separators=(',', ':')），不是任意文件 hash。

### 输出的两层含义

release_verdict 判断**已声明范围及必测完整性条件**能否放行；suite_verdict 判断整个对照套件是否完成。范围外的 unsupported 可以进入 scope_exclusions，但 suite_verdict 仍为 incomplete，不会冒充完整 Bartender 等价。

候选放行必须同时具备实际 Mac 条件、有效证据、通过范围内任务，以及匹配且已通过的无管理器基线。系统 build、设备、屏幕、权限 profile、应用清单或 Fixture 来源不匹配会阻止比较。

退出码：

- 0：提交证据支持的声明范围通过且基线匹配。仍须阅读 suite_verdict 和人工证据标记。
- 2：尚未具备环境、覆盖未完成或缺少合格基线。
- 1：输入／证据无效，或出现阻断失败。

这不是系统正确性的形式证明；评估器不能判断观察者是否说实话，也不能只凭文件 hash 证明界面行为。它的作用是让缺证据、错环境、部分覆盖和未执行项无法在记录中被轻易算成通过。

## 当前已执行与未执行

本轮可以在 Linux 执行：JSON 结构与引用检查、评估器单元测试、源码模型的独立测试。后端模型算术满足某个条件，也只属于该模型的结论，不能填入本协议的 Mac 行为 passed。

本轮不能在当前环境执行：Mac 编译、AppKit 行为、授权对话框、真实菜单事件、摄像头／麦克风指示、多显示器恢复和性能测量。私有只读 probe 本身也需要 Mac 才能实际运行，不能从静态源码推测探测成功。

下一位本机执行者应从基线开始，逐步积累原始证据；测试包完整只代表准备工作完整，不代表这些实验已经发生。

