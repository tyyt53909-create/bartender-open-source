# APP-01 菜单栏产品契约

本决定适用于首版两区整理、库存、原项访问和恢复。三个系统端口分别报告发现、显隐和访问结果。跨模块只传递 Swift 6 的 Sendable 值，系统对象留在创建它的执行域。[产品基线 §6–7](../baselines/product-design-v0.1.md) · [构建布局](build-layout.md)

## 四层状态及写入责任

| 层 | 谁写入 | 读者可以依据什么行动 |
|---|---|---|
| UserIntent | 配置模块保存本地逻辑项目、别名、常驻和收纳两组有序 ID，用户编辑时递增 userRevision | 规划器读取期望分区与顺序。临时展开只进入操作记录，未匹配项目继续保留配置。 |
| ObservedState | InventoryProvider 从指定观察范围返回库存和呈现快照 | 身份解析器和界面均检查来源、观察时间、新鲜度与完整性。过期、部分和未知库存不能证明目标唯一。 |
| EffectivePlan | LayoutPlanner 从请求、意图、观察、能力和 ticket 同步产生值 | 协调器读取预览域、能力前提、动作及预期观察。前提不足时规划器返回 held。实现只使用参数，不读系统、时钟或存储，不调后端。 |
| OperationReceipt | 协调器为实际尝试的每一步记录结果与已确认变更 | 界面区分已定位、已提交、观察到原菜单、歧义、受阻、不支持及结果未知。恢复只使用本工具已执行且观察确认的变更。 |

**模块所有权。** 架构负责人维护本目录的值类型与端口。APP-09 拥有匹配规则与条件能力表，平台适配器拥有 AX 线程、RunLoop、AppKit 对象及各端口实现。APP-12 拥有几何规划策略。APP-10 的协调器是副作用命令的唯一消费者，在每次 await 返回时和下次派发前复验；AccessBackend 的临时布局请求只回到协调器重新规划。APP-11 拥有配置迁移与恢复日志。UI 展示快照并提交意图。诊断只保留必要证据。

## 观察和身份

LogicalItem.id 是本地 UUID。ProducerIdentity 记录经过验证的生产者线索；宿主生命周期属于 RuntimeBinding。适配器在原执行域按临时 handle 查找活对象，绑定替换即发新 handle，增加 inventoryEpoch。持久化只保存逻辑身份、确认映射和意图。重启、宿主变化、重复标识或候选不唯一时须重新解析。别名、动态标题、PID、列表顺序与旧坐标均不足以建立绑定。

解析器在完整的新鲜范围内重验本生命周期的绑定、生产者内唯一的稳定标识或仍唯一的用户确认映射，输出 unique、ambiguous、unmatched 或 unknown。unique 同时携带被解析的逻辑 ID 和运行期绑定。ExactTarget 核对请求 ID 与解析 ID 相同，并检查该绑定在本轮库存中只出现一次。调用方在执行时须再次匹配当前 ticket、绑定与项目。一个项目可有多个 Presentation，各自携带屏幕、frame、单位、坐标空间、scale、时间与拓扑代次；副本关系未知时保留独立观察。

动态值、可见状态及库存各自有来源、时间、新鲜度和完整性。缺值保持未知。configuredVisible 仅表示系统声明；栏内、溢出区和屏外分别观察。过期值可标注后展示，不能驱动精确操作。

## 能力与预览

按 OS build、硬件、后端及其 revision、权限模式、拓扑、Item 和动作逐条登记。发现、显隐和访问独立取证；基础几何、依赖辅助功能的精确访问和可选像素读取分别处理权限。首版默认路径只消费适用条件完全匹配且具证据的 verified 条目。experimental 只供研究，unsupported 记录已知限制，unknown 保留缺证结论。未知系统版本或撤权后重新评估。

显隐域列出单项、整个应用及其成员、有序连续区间或本工具自有项，并明确单屏或跨屏联动。预览与交互租约覆盖全部受影响成员和屏幕。执行前若成员、邻居、跨屏范围或权限变化，暂停旧计划。适配器不能擅自扩大作用域。位置观察、动作提交与菜单打开分别留证；超时后可能已送达，结果未知时保留访问并停止自动重发。

VisibilityStep 将动作与规划时的新鲜完整基线、逐屏预期布局一起送入 VisibilityBackend。每份布局指纹覆盖批准域内全部成员的顺序和各自实际可见状态，同时记录前后邻居。完整观察中的空邻居表示已确认的边界；读不到邻居时标记观察不完整。执行者在派发前重验基线，适配器在动作后重新采样，返回带实际观察域、来源、时间、完整性及观察代次的 LayoutSample。观察代次在同一操作的采样上下文中单调递增。

MutationRecord 的认领入口核对当前 ticket、观察域、采样代次和观察质量，再将各屏实际布局与整步预期逐项比较。全部吻合且确有变化才可保存观察所得的 applied。成员仍在栏内而近邻已被替换时，该步停止，不认领也不继续恢复。

## 操作代次与恢复

| 事件 | 对当前操作的处理 |
|---|---|
| 数值或普通呈现刷新 | 仅更新 observationRevision。执行前仍检查该动作所需的新鲜度。 |
| 本操作的预期中间态已观察确认 | 更新 applied 和邻居指纹，保留 ticket。 |
| 身份集合、绑定替换或目标退出 | 更新 inventoryEpoch，丢弃旧目标。 |
| 编辑意图、相关权限或拓扑改变 | 分别更新 userRevision、permissionEpoch、topologyEpoch；废弃旧动作和旧恢复权。 |
| 外部或无法归因的布局改变 | 协调器提升 generation 并重新观察，保护用户新布局。 |
| 取代、取消、迟到回调 | 切换操作 ID 或 generation，取消时可清空 active ticket；旧完成回调不能推进当前操作。已发出的动作仍要观察结果。 |

协调器在 await 返回后，从当前隔离状态读取 active ticket；复验、写收据与排入后续步骤之间保持同一隔离段。迟到结果可供诊断，不能追加到新操作的收据。契约样例以可控挂起点覆盖等待期间切换 ticket、保持 ticket 但更换邻居、按预期更新中间态三种时序。APP-10 负责生产执行循环。

MutationRecord 绑定 owner ticket、实际影响域、before 和已验证的 applied（含邻居）。恢复时取得第三份新鲜 current，核对 ticket、相邻项目、成员、显示范围、用户修改和交互租约。菜单打开或结束未知时保持访问；计时器只触发复查。只有 current 与最近确认的 applied 一致时才可执行最小逆步骤。每步重验并观察，变化或结果未知即停止并保留未解决记录。重新配置屏幕后发起新的恢复意图。恢复日志的持久投影由 APP-11 定义，不保存 AX 对象或整份第三方布局。

## 演进与集成请求

公共签名、枚举分支、域的含义和版本递增规则由架构负责人协调变更。增加枚举分支须更新所有穷举消费者和独立样例；更改粒度、权限或身份语义须重验受影响能力证据。持久格式单独版本化，迁移保留未匹配意图，旧数据缺失的新字段按未知处理。

请 integrator 在根 Package.swift 串行登记以下两个互不重叠的 target，Swift 语言模式为 6。

| target | 类型、路径与依赖 |
|---|---|
| MenuBarContracts | library target，path 为 Packages/MenuBarCore/Contracts/Sources，无包依赖；同名 library product 供应用和其他模块导入。 |
| MenuBarContractExamples | executable target，path 为 Packages/MenuBarCore/Contracts/Examples，只依赖 MenuBarContracts；同名 executable product 仅用于显式验证。 |

两者在 macOS 和有 Swift 6 Foundation 的 Linux 上均应纳入目标图。AppKit、AX、XcodeGen 与 App 壳仅在 macOS 构建路径纳入；正式产品最低系统依既有规划由 APP-13 验证。生产 target 排除样例目录，App 无样例依赖。无需外部包、资源、锁文件或配置变更。接入根清单后分别运行 `swift build --target MenuBarContracts` 与 `swift run MenuBarContractExamples`；Linux 的实际构建结果需在对应主机另行记录。当前样例以独立客户端导入生产模块，用 swiftc 单独编译后运行。
