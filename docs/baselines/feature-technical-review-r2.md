# Bartender 6、7 与 Pro：功能价值、实现讨论与复核
## 第二轮研究结果

研究日期：2026-11-20。目标：为拟开发的 macOS 菜单栏工具明确体验目标、候选技术路线和目前不能承诺的能力；本项目官方发行版本免费，自有代码采用 MIT。

本轮按产品与交互、macOS 工程与架构、扩展集成与权限三个方向并行研究，再相互质询，由主审汇总。这里是 AI 多角色技术评审记录；没有邀请外部专家，也没有在 Mac 上安装、运行或测量这些软件。证据来自厂商文档、Apple 等平台官方资料、固定提交的开源代码和少量第一手问题报告。

全文区分四种结论：**文档事实**说明厂商或平台写了什么；**源码事实**说明某个公开实现具体做了什么；**设计判断**是本项目的建议；**待验证**必须由实机、设备矩阵或用户研究回答。Bartender 是闭源产品，本轮不把候选方案冒充它的内部实现。

## 一、功能与价值：先明确我们要替代的体验

### 1. 6、7 与 Pro 的关系

Bartender 6、7 是主版本，Pro 是包含扩展工具的权益方案。6.5.1 已引入 Pro 与 Top Shelf；6.5.2 又加入 AirPods 连接及低电量提醒。因此，不能把 Pro 当成只在 7 才有的第三个独立版本。[S02]

| 范围 | 已核实的主要能力 | 归属和时效说明 |
|---|---|---|
| Bartender 6 菜单栏工具 | 隐藏与展开、快速唤出、刘海及空间不足时的访问、第二栏、分组、预设、触发器、搜索、样式和间距、自定义 Widgets | 搜索、分组、预设和第二栏都不是 7 或 Pro 才出现的能力；6 产品页仍将 Widgets 标为 Beta。[S01] |
| Bartender 7 的重点改进 | 录屏权限可选、厂商宣称管理操作不干扰鼠标、Command Bar、可独立设置外观的第二栏、在指针附近唤出、显示器关联预设、扩展自动化入口 | 拒绝录屏时使用 App 图标，不能据此认为动态信息完全相同；Command Bar 中的剪贴板历史属于 Pro 权益。[S03][S04] |
| 7 的后续更新 | 7.1 增加 Tahoe 支持、6 的设置迁移、配置导入导出和修改前备份；7.2 增加仅在刘海屏或溢出时显示第二栏等设置 | 查核时稳定版日志顶部为 7.2.0。官网部分兼容文案滞后，应依据具体版本记录；iCloud 同步仍在未来计划中。[S05] |
| Pro / Top Shelf | 顶部交互面板，媒体与音量、天气、日历、剪贴板历史、文件暂存与 AirDrop、Codex / Claude Code 状态，以及更新日志中的 AirPods 提醒 | 有无刘海都可用；它扩展了产品任务范围，并不只是菜单栏外观。[S06][S02] |

标准买断包含该主版本的更新；Pro 为订阅权益并包含有效期内后续大版本；Mega 是终身权益方案。这里不沿用未经本轮核实的日元结算价格。[S03][S06]

### 2. 基础能力、核心体验与购买理由

“基础”指一个菜单栏管理器进入用户比较范围所需的能力，不表示实现容易。常驻、普通隐藏与始终隐藏的区分、手动调整顺序、点击或快捷键展开、设置自动收起、启动及配置入口，构成功能基础。始终隐藏应有明确的专用唤出方式；快捷展开、搜索和自动规则是否涉及它，需要产品规则分别定义，不能把两种隐藏语义混成一类。6 的更新日志也记录了相关 Option 点击行为。[S02]

对付费价值的判断应看用户完成了什么任务。本轮没有付费访谈、转化率、续费或流失数据，以下是根据任务频率、失败代价与替代方案缺口提出的假设，不能写成已证明的购买动机排名。

| 体验核心 | 对应功能 | 用户可能愿意付费的原因 | 替代品必须通过的任务 |
|---|---|---|---|
| 整理后仍能完整使用 | 溢出访问、第二栏、空间让位、具体 Item 的识别与操作 | 小屏或刘海屏上的入口不再难找；整理不会让工具变得不可达 | 找到正确项目、辨认关键状态、打开原来的交互 |
| 布局可预测 | 保存顺序、恢复、显示器配置、应用重启后的重新匹配 | 用户不用不断修理已经整理好的环境 | 重启、插拔外屏、睡眠唤醒后，布局仍符合保存意图 |
| 操作不打断当前任务 | 稳定的菜单生命周期、输入与焦点保护、按需恢复 | 常驻工具可以长期留在系统里，不成为额外干扰 | 不误点、不抢拖拽、不提前关菜单、不恢复到过期布局 |
| 访问更快 | 搜索、快捷键、指针附近唤出、键盘导航 | 工具多或偏好键盘的人减少寻找成本 | 定位具体菜单项，而非随意打开所属应用 |
| 场景切换省事 | 分组、预设、触发器、显示器关联、Shortcuts / AppleScript | 工作、居家、演示、移动办公之间少做重复调整 | 条件变化得到正确动作，多个规则不会来回争夺布局 |
| 外观和信息组织符合偏好 | 样式、间距、分隔符、标签、自定义控件 | 对重视桌面整合与视觉秩序的用户，外观本身有价值 | 不牺牲点击命中、可读性、系统状态或资源开销 |

其中前三项贯穿全部功能。一个能折叠图标、却经常找错目标或打断菜单的工具，还没有兑现核心价值。

第二栏是一种实现方式。若系统原生溢出菜单能够可靠完成同样的任务，产品未必需要复制相同的外形。但如果它无法保留目标用户需要的状态、动作或布局，就应明确记录缺口，不能把缺少的能力改称“用户不需要”。

### 3. Pro 的价值依赖目标人群

资料搬运频繁的人可能最重视剪贴板和文件暂存；AI 开发者可能重视 Agent 的运行、等待和完成状态；经常听音乐、关注日程的人可能把媒体和日历作为最常用入口。Top Shelf 将这些任务集中在屏幕顶部，形成另一组效率价值。[S06]

建议将“菜单栏管理”和“顶部工具集”视为两个可独立交付、共享面板调度的产品域。可以分阶段建设，但不应因为某项集成难做，就在需求分析中否认它的价值。相反，也不能因为 Pro 功能多，就默认全部目标用户都愿意为全部模块承担权限与常驻开销。

对现有需求用户，下一轮应请他们复现最近一次真实障碍：哪个 Item 找不到、哪次接屏打乱布局、哪些操作必须用右键或 Option、是否已经使用其他剪贴板或文件工具。用任务证据检验优先级，单纯询问“这些功能想不想要”容易得到全部都要的答案。

## 二、多角色技术讨论：争议、证据与决定

### 议题 A：菜单栏管理器到底能控制什么？

**macOS 工程侧的判断。** 公开 NSStatusBar / NSStatusItem 可以创建、配置和移除本应用持有的状态栏对象。文档没有提供一个跨进程枚举所有第三方 NSStatusItem 并任意修改它们的通用管理器。另一个容易误读的细节是：NSStatusItem.isVisible 即使在项目因空间不足暂时不可见时，也可能返回 true。[A01][A02]

这决定了“找得到对象”“知道它在哪”“能改变它的显隐”“能执行它的动作”必须分别证明。不能从一个 API 名字推导出整套能力。

**架构侧的决定。** 模型至少区分以下对象：

| 对象 | 需要保存的内容 | 不能混为一谈的东西 |
|---|---|---|
| App | 生产者身份、bundle、应用路径等线索 | 一个 App 可能产生多个 Item |
| Item | 稳定标识（若提供）、语义特征、用户别名、期望分区与顺序 | 当前 PID、窗口 ID 和列表序号不是跨重启的可靠身份 |
| Presentation | 当前屏幕、frame、缩放、可见性、可用动作与数据时间 | 同一 Item 的多屏副本不是多个逻辑 Item |
| VisibilityDomain | 后端实际控制的是 Item、App 还是连续位置区间 | 配置界面按 Item 分类，不表示底层能逐 Item 显隐 |
| InteractionSession | 本次操作目标、布局版本、是否已打开、是否仍由我们控制临时修改 | 不应在旧操作结束时覆盖用户刚做的新修改 |

持续身份匹配应优先使用实际存在的稳定 AXIdentifier；没有时结合生产者、可用语义和用户确认。动态 title 不能当唯一主键。匹配存在歧义时应显示待确认，不能默默选择同 App 的第一个图标。

布局保存逻辑顺序与邻居锚点，具体坐标根据屏幕拓扑重算。需要覆盖上下排列的显示器、负坐标、独立缩放、刘海和自动隐藏菜单栏；不能只按横坐标选择屏幕。屏幕配置变化有官方通知可订阅，但“收到通知”不等于已经恢复成功。[A06][A07]

### 议题 B：隐藏与展开要选哪条路线？

本轮保留三个候选后端用于比较，不预先承诺全部进入正式版。

| 路线 | 已发现的实现依据 | 主要边界 | 本轮决定 |
|---|---|---|---|
| 较旧系统的几何分区 | 扩大自有分隔状态项，使一侧项目被挤出可见范围；Hidden Bar 的 legacy 引擎有对应实现 | 控制连续区间；依赖系统布局行为；没有由此获得任意第三方显隐和排序能力 | 作为 26 等目标系统的候选，逐版本验证 |
| 27 的多 spacer 与原生 overflow | MenubarHide 将多个受限宽度状态项组合，利用系统溢出区域收纳左侧项目 | 启发式阈值；宽窄混合屏可能越界；它在 27 禁用自建面板和布局保存/恢复 | 必须加入原型比较；足以否定“27 必须走私有接口”的过早收敛 |
| 27 的私有 bundle allow-list | Hidden Bar 动态加载 MenuBarClientCore，配置允许显示的 bundle 与系统项 | 私有接口；第三方应用的 bundle 允许列表是 App 粒度，系统项另以未文档化列表处理；有系统状态及通知中心副作用 | 只有补出明确用户价值，并通过系统交互门槛，才考虑启用 |

依据分别见固定版本源码 [G01][G02][G09][G10]。几何方案虽然调用公开 length 属性，其效果仍依赖未文档化的系统布局，不应宣传成“只用公开 API，因此不会受系统升级影响”。

MenubarHide 的固定实现注册六个 spacer，并根据各屏宽度、刘海右侧区域和经验余量计算长度。六个和阈值都是该项目的工程选择，不是 Apple 的平台保证。它提供了值得验证的路线，尚不能证明在所有屏幕组合上成熟可用。[G09]

**产品侧的质询。** “能收起来”只验证一小部分任务；隐藏后的辨认、操作、排序恢复也必须成立。

**最终决定。** 在同一组 Item、相同系统 build、相同屏幕和授权条件下比较两条 27 路线。优先采用能完成核心任务且维护负担较小的方案；若达不到任务，不用技术偏好掩盖缺项。私有 allow-list 通过 bundle 列表不能分别隐藏同一 bundle 的不同 Item，这是接口结构的限制，增加测试不会让它自然获得该能力；其他几何或 AX 路线的 Item 能力另行判断。

固定 NativeVisibilityEngine 源码记录了收起时摄像头／麦克风使用者名称提示被隐藏、屏幕角点仍保留的行为；默认补救仅在一次新的采集开始时展开，用户随后仍可再次隐藏。本轮将其列为需要实机消除，或据此限制支持范围的发布门槛，不把一次展开视作彻底修复。这是源码记录的行为，不是本轮已经复现的实验结果。[G04]

Bartender 7.0.4 自身也解释了 27 中按 App 一起显隐的行为，但这不能推导为 27 上所有查找、排序、AX 动作或几何溢出都只可能按 App 操作。[S05]

### 议题 C：第二栏与搜索怎样保留真正的使用体验？

**实现拆分。** 自己画面板、展示项目的信息、触发原项目，这三件事需要分别实现。

| 表示方式 | 能提供什么 | 需要承认的缺口 |
|---|---|---|
| App 图标与名字 | 基本辨认所属应用；可以不采集菜单栏像素 | 不一定区分同 App 多项；可能丢失数字、徽章、同步进度 |
| AX 语义表示 | 读取原应用实际暴露的 title、description、value 等 | 数据可能缺失、陈旧或不稳定；不能凭空补齐未提供的状态 |
| 真实图标快照 | 拍到时的外观与动态内容 | 有捕捉权限、更新频率、离屏、遮挡、失效和功耗问题；图片仍不是原控件 |

Ice 的公开实现使用自有面板与图像缓存，并在操作时临时显示原 Item、触发原交互。它没有把其他进程的 NSView 真正搬进自己的面板。其实现还调用了 CGS 私有接口，因此不能将整套能力归为仅用公开 CGWindowList API。[G05][G06][G07]

ScreenCaptureKit 的官方能力覆盖屏幕、应用和窗口捕捉；这不证明任意被隐藏、离屏或已被系统合成的菜单项都能单独抓到。[A05] 在 27 上研究合成菜单栏或展开 overflow 后的画面裁剪，是一个候选实验，当前不能写成已解决方案。

**搜索的关键问题。** Hidden Bar 核验版本的 PaletteItemPresser 接受 bundle 参数，并遍历到第一个可见、支持 AXPress 的对象就执行。它可作为按 App 默认入口的参考，不能证明精确的多 Item 搜索已经实现。[G03]

我们的建议索引应指向逻辑 Item，记录实际可用动作、别名及状态来源。搜索结果要区分“打开这个菜单项”“显示并定位这个菜单项”和“打开应用主窗口”。无法分辨具体 Item 时，不应返回看似精确的成功结果。

对于用户必须使用的动态状态，像素不是唯一表达方式；可靠的 AX 文本也可能满足任务。但“显示一个通用 App 图标”无法自动等价于“所有信息都保留”。

### 议题 D：如何做到不抢输入，又不提前关菜单？

**交互侧提出的目标。** 用户点开 VPN、音量或同步工具后，应能继续选择菜单、子菜单、右键或修饰键动作。自动收起和触发器不得在这时重排目标。

**工程侧提出的限制。** AXPress、AXShowMenu 等动作是否存在，由目标应用暴露的能力决定。AXPress 不是右键、Option-click、滚轮或拖拽的通用替代。Apple 还明确说明，AX 操作的 CannotComplete 可能来自目标进入模态处理导致超时，并不一定代表动作没有发生；盲目重试可能把刚打开的菜单再次关闭。[A03]

对不提供所需 AX 动作的 Item，可研究临时揭示后重新定位，再派发对应鼠标与修饰键事件。Ice 有合成事件路径可供研究，但这会带来授权、输入干扰与系统事件路由变化的问题，需逐动作验收。失败时保留系统原位访问，不把相邻对象当作替代目标。[G06]

建议用一次完整的交互会话协调所有动作：

1. 解析具体 Item，建立本次操作代次。
2. 如果需要，暂时展示原位置；在展示完成后重新验证身份和 frame。
3. 执行已证实支持的动作，观察真实结果。
4. 原菜单、弹层或用户交互持续期间，暂停自动收起和冲突重排。
5. 操作结束后，确认临时布局仍由这次会话拥有，再恢复。
6. 目标退出、用户手动重排、切屏、撤销授权或更换预设后，废弃旧回调。

菜单打开/关闭的观测可以结合应用支持的 AX 通知与实际窗口变化。按 PID 和窗口层级判断只是启发式，自绘弹层及 helper 进程可能破坏这一假设。无法可靠观测结束时，保持可见并提供明确的收起操作，比固定数秒后强制恢复更可控。[A04][G03]

27 新增 expandedInterfaceDelegate / expandedInterfaceSession，适用于自己持有的状态项展开界面；不是监控所有第三方菜单的全局代理。Apple 还说明，使用 NSMenu 的状态项不接收这些展开回调，应按其自有菜单机制处理。[A12]

“零鼠标”需要拆成三个独立指标：是否改变指针位置、是否注入合成鼠标事件、是否打断用户正在进行的输入。恢复旧指针坐标也可能造成干扰——如果用户已经移动鼠标，就不能强行把它送回过去的位置。厂商的 mouse-free 声明不够支持对底层事件机制的推断。

### 议题 E：分组、预设、触发器怎样避免互相争夺控制？

**架构判断。** 所有修改菜单栏的请求必须进入同一个操作协调器。不能让搜索、触发器、自动排序和第二栏各自修改系统，然后彼此修复对方制造的变化。

建议将状态拆为“用户期望”与“当前观察”。规则只产出期望变化，计划器评估目标后端能执行多少，再提交、观察和记录结果。输出至少包括：已观察成功、部分完成、不支持、超时且结果未知。一次 API 返回值不能代替用户任务成功。

规则数据包含条件、目标 Item/预设、优先级、持续时间、退出条件与最近原因。建议用户主动操作和正在进行的交互优先；显式选择预设可以短时覆盖自动规则；随后才合并上下文条件与默认配置。具体优先级是本项目的设计建议，需要在交互中展示清楚。

| 条件或动作 | 候选实现 | 需要防止的错误推断 |
|---|---|---|
| 电源、电池 | IOKit 电源快照与变化通知 | 不必高频扫描整个菜单栏来发现电源变化。[A09] |
| 时间、日期 | 定时调度并处理时区、睡眠唤醒、时间跳变 | 不能只靠启动时计算一次延迟 |
| 应用与屏幕变化 | NSWorkspace、NSApplication 对应通知 | 变化事件并不保证所有 Item 已完成重新注册。[A07][A08] |
| 网络路径、Wi-Fi 条件 | NWPathMonitor 与 CoreWLAN 分工 | 有网络或使用 Wi-Fi 不等于知道 SSID，更不等于知道是公共网络或 VPN 已连接。[A10][A11] |
| 图标或内容变化 | 能读取时优先语义值；否则研究局部图像差异 | 图像闪动、主题变化、动画不应触发无限往返；捕捉失效不能视为“没有变化” |
| 会议状态 | 用户显式预设、已验证的应用事件，或明确的日历时间条件 | 日历时间、麦克风活动、摄像头活动、屏幕共享是不同信号 |
| Shortcuts / AppleScript / 自定义入口 | 通过 App Intents actions 向 Mac Shortcuts 暴露有限动作，再转发到同一协调器 | 不泛化成其他平台的全部 App Shortcuts 展示能力；外部入口也不能绕过交互锁和错误反馈。[A13] |

需要防抖、冷却期、进入/退出不同阈值，以及有期限的临时显示。条件读取失败或权限不足应为 unknown，不直接当 false。日志记录触发原因和动作结果，避免为了调试保存日历内容、剪贴板或整张桌面截图。

分组本身可以用我们自己的状态项和面板实现；但“面板里把项目放进一个组”不等于“已能在系统里独立控制组内每项”。同理，在自有列表里拖动排序不等于原生菜单栏排序成功。

原生即时重排可研究带 Command 的合成鼠标事件；Ice 采用了这一类方法，需核对目标、当前输入状态与动作后的真实位置。[G06] 另一候选是恢复各应用未文档化的 NSStatusItem Preferred Position 偏好；MenubarHide 将其用在应用下次注册状态项前的恢复。这不等于即时排序，也不应为生效强制结束应用；该项目在 27 关闭此路径，不能直接照搬到 27。[G11]

恢复计划应只移动必要的已识别项目，每次移动后重新观察。用户正在拖动或主动改布局时暂停，未知或尚未启动的项目保留逻辑位置，不盲目补齐。显示器组合关联整体预设，与每块屏幕拥有完全独立的原生顺序和显隐是不同目标；后者必须由后端明确证明支持，不能由多屏模型自动推得。

### 议题 F：样式、间距与 Widgets 的难度为什么不同？

自有面板的配色、圆角、材质和排列可以由 AppKit / SwiftUI 管理。系统整条菜单栏的样式则是另一类问题：覆盖层可能需要处理窗口层级、点击穿透、全屏、Spaces、壁纸、透明度、对比度和辅助功能；不能因为画出了好看的面板，就认为原生菜单栏主题也已完成。

间距尤其需要单独审查。Ice 的固定实现写入未文档化的 NSStatusItemSpacing / NSStatusItemSelectionPadding 全局偏好，随后尝试重启菜单栏应用；未退出时，代码还有延迟后 forceTerminate 的分支。[G08] 这是可核验的 Ice 行为，不是对 Bartender 实现的断言。

本项目不应把间距做成静默重启其他应用的开关。若研究此方案，需要保存原值与本次修改范围，尽量在自然重启或重新登录后生效；“立即应用”应让用户看到涉及的应用并选择是否重启。

Widgets 的产品范围包括无需代码配置、内置数据源、自定义脚本和点击动作，并非仅是脚本输出容器，也不等于 Apple WidgetKit。替代实现需要分别设计数据选择、展示格式、点击动作、配置保存和错误提示；官方展示的系统指标示例不应被当成完整的数据源支持清单。[S03]

建立自己的 NSStatusItem 相对直接，复杂度来自采样和执行控制。脚本应由明确 executable 与 arguments 启动，限制时间、输出与并发；超时要处理子进程，导入配置不能自动运行未确认脚本。分进程能隔离部分崩溃，但单独一个 XPC 服务不会自动把任意脚本变安全。若选择 NSUserScriptTask，还必须注意 Apple 将它定义为在应用沙盒外执行用户脚本，不能把它宣传成安全运行任意代码的沙盒。[X16]

## 三、Pro / Top Shelf 的逐项实现研究

以下均为可用于开源替代的候选设计，不代表已发现 Bartender 的内部代码。独立开关、按需授权和停用后停止采集，是本项目建议。

### 1. 顶部面板与事件仲裁

可以用自己的 NSPanel 承载界面，根据各屏 safeAreaInsets 和屏幕几何定位；没有刘海时也用普通顶部区域承载。这里是在 Mac 上实现相似交互，不是调用一个已证实存在、可任意扩展的 iPhone Dynamic Island 系统接口。[A06]

面板模型至少区分静止概览、临时提示、用户主动展开和拖放接收。用户正在拖文件、选剪贴板、粘贴或操作原菜单时，当前内容、命中区域和焦点应锁定。媒体、Agent、日历与设备事件按类合并排队，交互结束只展示仍有效的内容；过期提醒不补播。减弱动态效果、键盘操作和 VoiceOver 应与外观一并设计。

锁屏及用户主动启用的演示隐私模式下，抑制剪贴板、日程标题、文件名和 Agent 内容等敏感预览，恢复后不自动补播旧卡片。这是明确的产品状态规则，不依赖“准确检测全部屏幕共享软件”的未经验证假设。

### 2. 媒体与音量

媒体必须拆为元数据、播放控制、目标播放器选择、输出设备与音量。MPNowPlayingInfoCenter 的公开用途是为自己应用播放的媒体提供信息，并不证明可以读取及控制其他所有应用。[X01]

候选路线是给实际支持的播放器建立适配器：应用提供的脚本接口、明确的集成协议，或需要另行验证的私有媒体接口。AppleScript 控制其他应用需要处理 Automation 授权。[X17] 已读到的 MediaRemoteAdapter 明确使用私有 MediaRemote.framework，可作为第二条实验路线，但不能证明它能控制任意播放器。[X15] 浏览器内多标签页、多播放器同时播放、内容切换和应用退出都需要定义当前目标；不能用“最后活跃进程”猜测唯一正确播放器。

音量控制与媒体状态应分开。对 Core Audio 输出设备应检查相关属性是否存在且可写，不可假定每个外接数字设备都支持系统音量。逐 App 音量混音也不是“读到当前歌曲”就自然具备的功能。[X02]

### 3. 剪贴板历史

候选实现是观察 general pasteboard 的 changeCount，按实际可读类型读取并去重，以文本、图像和文件引用等类型建索引。对大图像、文件内容、富文本与短时间连续复制分别限额；不要默认把复制文件等同于把所有文件内容再复制一遍。

新增系统读取隐私行为必须纳入设计。Apple 文档已提供 NSPasteboard.AccessBehavior 和 ask / allow / deny 等策略；公开属性的可用性与各系统版本默认启用的行为仍须实机验证。程序读取可能受到提示或拒绝，不能宣称剪贴板历史天然无需任何授权。[X03][X04]

建议默认不采集，用户明示开启；提供应用排除、保留时间、暂停与清空。密码管理器标记及敏感类型过滤只能减少风险，不能保证所有密码和 token 都被识别。需要落盘时，应将内容、缩略图、搜索索引、缓存、备份的保留策略一起设计；仅加密主数据库不代表所有派生数据都加密。

“选择历史项”与“自动粘到目标应用”应分开。自动粘贴的合成按键通常还需要辅助功能能力，与读取剪贴板的许可不同；未具备控制能力时保留复制按钮，供用户自行粘贴。自动粘贴前记录目标应用和输入上下文，在执行前重新确认；不确定时仅复制到剪贴板。若承诺恢复原剪贴板，必须确认期间没有新的复制，避免覆盖用户刚得到的内容。所谓一天保留应覆盖索引、缩略图和缓存清理；不承诺由普通删除即可保证底层存储物理不可恢复。

### 4. 文件暂存与 AirDrop

先决定暂存的是文件引用还是一份副本。引用节省空间，但原文件移动、被删除、权限失效或 iCloud 尚未下载时可能不可用；副本更独立，却需要空间配额、过期清理和导出语义。

拖放可能产生 file promises，不能只接受立即存在的文件 URL。若在沙盒与跨重启访问场景下持久保存引用，需要正确处理 security-scoped bookmarks 的授权、陈旧状态和访问生命周期。权限取决于构建方式和文件来源，不能把同一要求机械套到所有发行构建。[X05][X06]

AirDrop 可以研究 NSSharingService / 系统分享入口，让用户选择设备并发起发送。界面被打开只表示分享开始；完成、失败和取消应各自反馈，不能宣传为后台静默发送给附近所有设备。[X07]

### 5. 日历

EventKit 能查询事件，但 Apple 明确没有 read-only 的读取授权。要读事件，系统层面需要 full access；我们可以只实现展示并限制读取范围，却不能对用户说系统只给了只读权限。[X08]

建议独立启用，只查询用户选定日历和有限时间窗，按事件存储变化、时间点和唤醒刷新。处理全天事件、时区变化、重复事件、取消及多个重叠事件；会议链接仅由用户点击打开。日历中的“进行中”只代表时间区间，不能证明用户确实加入会议或正在共享屏幕。

### 6. 天气

WeatherKit 提供官方数据路径，但其包含的每月 50 万次调用属于开发者会员账户额度，不是每位终端用户各有 50 万次。官方数据还需按要求归属展示。[X09]

免费应用必须设计缓存、刷新节流、离线与超额行为。优先允许手动选城市，定位单独授权；不要把精确位置作为使用整个菜单栏工具的条件。使用其他服务时，逐个确认商用/开源分发、调用限制与数据许可。MIT 许可证不会取消上游天气服务费用，发布源代码也不等于可以公开服务端密钥。

### 7. Codex、Claude Code 等 Agent 状态

应建立事件适配器，接收真实的会话开始、运行、等待批准、本轮响应结束和失败事件，再映射为统一状态。状态还需要 session ID、时间戳、来源版本和失联过期处理。

不要扫描 CPU 使用率、猜测终端文字或读取完整对话来制造一个看似精确的进度百分比。没有分母与进度事件时，只显示已知状态；“运行中”“等待用户”“本轮响应结束”“来源未连接”比伪造的 73% 更可信。

本轮查到 Codex 和 Claude Code 的官方 lifecycle hooks，可让用户配置的 hook 向本地桥发送最小事件；若我们的应用本身连接并管理 Codex app-server，则还可消费相应协议通知。它们都不是旁观所有独立终端会话的万能接口。[X12][X13][X14]

Codex 的 turn/completed 还可能携带 interrupted 或 failed，必须检查状态；Claude Code 的 Stop 表示响应结束，不证明用户目标已达成。只有来源确实提供任务成功语义时才显示“任务完成”。Codex 文档明确 transcript 格式不是稳定 hook 接口；非受管 hook 需要用户审阅并信任具体定义，观察桥不能绕过这一步。[X12][X13][X14]

本地 IPC 建议限制来源、会话令牌、payload 大小和生命周期；默认不存提示词、源码及完整终端输出。观察器故障不能阻塞 Agent 正常工作，也不应改变其批准决定。不要假定 MCP 的存在自动带来全部任务生命周期与进度数据。

### 8. AirPods 连接与电量

6.5.2 发布记录使这项进入本轮范围。[S02] 连接提醒可研究 IOBluetoothDevice 的公开连接通知；但公开 hands-free 电量回调不能证明可读取所有 AirPods 的左耳、右耳、充电盒精确百分比。[X10][X11]

本轮检查到的开源 PairPods 通过运行时 selector / KVC 读取 batteryPercentLeft、Right、Case 等属性；这些不能当成已经确认有公开稳定文档的能力。[X18] 完整电量应归入未文档化适配实验，按设备、系统和连接状态探测能力。不可读取时显示未知或省略，不能把最后一次电量冒充当前，也不应为了显示数据强制重连设备。

## 四、收敛后的系统结构与研发范围

### 1. 建议架构

主应用采用原生 macOS 技术栈，以 AppKit 负责状态项、窗口和系统交互，SwiftUI 承载适合的设置与面板视图。具体实现语言选择并不解决跨进程控制难题，核心在于下列职责边界。

| 模块 | 责任 | 关键限制 |
|---|---|---|
| CapabilityRegistry | 按 OS build、后端、权限和 Item 记录支持程度 | 用 supported / partial / unsupported / unknown，不能把未测填成支持 |
| Inventory | 发现 App、Item 与屏幕副本，维护身份及数据新鲜度 | 报告未识别或过期状态，不猜测身份 |
| LayoutPlanner | 将用户意图与当前屏幕、能力、系统状态合成操作计划 | 不主动隐藏无法识别的项目；不承诺后端不具备的 Item 粒度 |
| OperationCoordinator | 串行协调显隐、排序、搜索调用与恢复 | 保护用户交互，取消旧代次，结果必须观测 |
| Presentation | 原生 overflow 协作、自有第二栏、搜索与状态语义 | 表示方式与操作能力分开 |
| RuleEngine | 将事件和规则变成期望状态 | 防抖、过期、冲突原因与手动覆盖 |
| ProviderHost | 媒体、日历、天气、剪贴板、文件、Agent、设备数据 | 按需启动，独立授权和故障隔离 |
| Store / Recovery | 配置版本、迁移、修改前快照和恢复记录 | 不覆盖后来发生的用户编辑，不顺带持久化敏感内容 |

开始时无需将每个模块拆成独立进程。先明确协议边界；对不可信脚本、易崩溃或高开销的提供者，再按实际隔离需求使用 helper / XPC。私有接口集中在可禁用的适配层，避免污染配置和 UI 逻辑。

“显示全部”应表示撤销本工具施加的限制、恢复用户访问，不能擅自重新开启用户原先在系统设置里关闭的项目。物理空间不足时，这也不能保证所有项目同时位于原生第一行，仍需保留可访问的溢出或面板路径。退出回滚、崩溃恢复与下次启动修复是三种情境，要分别验证；有清理回调不等于崩溃时一定会执行。

授权应跟能力走：创建自有状态项、读取第三方 AX、捕捉像素、向其他应用发送 Apple Events、日历读取和剪贴板读取各有不同边界，拒绝某项授权不应封锁无关模块。基础配套还包括快捷键冲突反馈、用户选择的登录启动、版本化配置及原子写入、导入前校验和备份；导出不默认带剪贴板、文件内容、凭据和未审阅脚本的自动执行状态。这些都是建议的实现要求。

### 2. 分阶段交付，但保持完整目标

| 阶段 | 可评估的交付物 | 不能借阶段名称掩盖的限制 |
|---|---|---|
| 技术证明 | 同样本对比 26 几何、27 原生 overflow、27 私有 allow-list；验证 Item 身份、操作、状态与恢复 | 仅凭折叠截图不能决定正式后端 |
| 基础可用版 | 已验证平台上的收放、手动组织、搜索、清楚的权限降级和恢复入口 | 如果只有 App 级入口或静态图标，要直说，不称完整 Bartender 等价 |
| 核心体验版 | 具体 Item 访问、目标人群所需动态状态和交互、可靠布局、预设与少量高价值规则 | 不支持的右键/多项身份/屏幕组合不能以未来承诺计入完成 |
| 扩展工具集 | 独立启用的 Pro 对应模块，逐一给出支持应用与数据源 | 不把某一个播放器或某一代 AirPods 的成功扩大为全平台支持 |

本轮建议优先验证“完整访问、布局稳定、输入保护”三个技术门槛。天气和日历已经有较清晰的数据路线，却不能替代菜单栏内核的可行性证明；媒体、AirPods 和系统级样式应单独评估兼容成本。

### 3. 免费 MIT 的工程边界

Hidden Bar 与 MenubarHide 为 MIT 参考基础；Ice 本轮检查的代码为 GPL-3.0-or-later。可研究其思想与机制，但不应直接复制其代码后把整体标成 MIT。实际采用每个依赖或代码片段前，应固定版本、核验许可证并保留要求的 notices。[G10][L01][L02]

官方版本可以承诺免费，MIT 本身仍允许第三方商业使用，不能将 MIT 解释成禁止别人收费。应用名称、图标、视觉素材和产品文案需要自有实现与授权。站外分发的签名、公证和持续系统适配应成为维护计划；如果使用私有 API，不能同时把完整能力进入 Mac App Store 当成已经确定的发行路线。[L03][L04]

## 五、复盘：已修正的地方、保留的未知与验收

### 1. 对上一轮和本轮推论的复核

上一轮已经明确写过“候选实现不等于 Bartender 内部实现”“首版不等于完整替代”和“需实机验证”。本轮保留这些正确边界；下面区分遗漏补充、推论收紧和需要继续防止的错误。

| 项目 | 本轮核查结果 | 对项目的影响 |
|---|---|---|
| 版本与权益 | 补明 Pro / Top Shelf 在 6.5.1 已存在；6.5.2 AirPods 提醒此前未展开 | 避免将核心工具误列为 Pro 独占，补全 Pro 范围 |
| 27 的技术路线 | 新发现多 spacer 配合系统 overflow 的公开源码候选 | 不能仅因单个巨大 spacer 失效，就认定只能使用私有 API |
| App 搜索与 Item 搜索 | 固定 Hidden Bar 代码仅按 bundle 找首个可操作元素 | 初版入口可用性与最终 Item 精确访问分开验收 |
| 第二栏的动态信息 | 静态 App 图标、AX 语义与原像素各有不同覆盖 | 不能把低权限模式宣传为无信息损失 |
| 显隐粒度 | 私有 bundle allow-list 的 App 粒度有源码依据 | 限制只归属于对应路径，不外推为整个 macOS 不可能 Item 级 |
| 鼠标承诺 | 指针位移、事件注入、输入干扰是不同指标 | 不用“肉眼看不到移动”证明“完全没有干扰” |
| AX 动作结果 | 超时可能发生在动作已经进入模态处理之后 | 不自动重试；先观察，避免第二次点击反转结果 |
| Apple 新展开接口 | 27 有自有状态项展开会话接口 | 补入候选架构，但不误当跨进程全局菜单监听 |
| Ice 的接口 | 除 CGWindow 等能力外，代码还调用 CGS 私有桥接 | 不把整套复现描述成纯公开 API |
| 间距 | 某开源方案修改全局偏好并可能强制结束其他应用 | 不将它当成普通面板 padding，也不把该做法归因给 Bartender |
| 媒体接口 | MPNowPlayingInfoCenter 面向本应用媒体信息 | 跨播放器读取和控制必须独立研究适配器 |
| 日历权限 | EventKit 读取需完整访问，没有系统只读授权 | 用户说明必须诚实区分用途与系统授权范围 |
| 剪贴板 | 现行文档有程序读取隐私策略 | 不能保留“剪贴板永远不用授权”的假设 |
| 天气成本 | WeatherKit 配额按开发者账户 | 免费分发需要服务预算、缓存与超额策略 |
| Agent 状态 | 必须有真实事件来源和版本适配 | 没有事件时不推测精确进度；不宣称 MCP 自然提供全部状态 |
| AirPods | 连接通知与精确左右耳/盒电量是不同问题 | 未文档化电量接口单列实验，不能泛化公共 API 覆盖 |
| 路线图与发布 | iCloud 同步、某些扩展在所查材料里仍是未来时态 | 不列入已交付功能；官网冲突以具体更新记录审慎判断 |
| 付费动机 | 缺少真实购买研究 | 本轮只能提出有依据的价值假设，不制造百分比与排名 |

另一个需要明确的细节：Bartender 7 的发布文章说，菜单项截图会缓存到本地磁盘；“数据不离开设备”与“从不落盘”不是同一句话。[S04] Bartender 6 的首发文章曾描述仅在内存保存图像，本轮没有验证其后续版本是否改变这一策略。[S08] 我们的隐私说明也必须覆盖实际版本的缓存和清理方式。

### 2. 第一手问题报告如何使用

Hidden Bar #547 报告了折叠时点击时钟导致指针位移、通知中心不保持打开的情境；报告针对 macOS 27.2.1 / 1.13.0，查核时已经关闭。#523 报告进入 Google Meet、出现麦克风或摄像头状态后无法正常收起，针对 macOS 27.0.1 / 1.13.0，查核时仍打开。[I01][I02]

它们证明这些失败情境值得覆盖，不证明当前最新版一定复现，也不能用于推算发生频率或付费意愿。对应的验收应转化为系统状态、菜单生命周期与并发事件测试。

### 3. 本轮尚未解决的问题

未取得 Bartender 的内部实现；未独立测量其性能、输入行为与所有权限降级；未在 Mac 上比较三条后端；未证明所有第三方 Item 都可稳定识别、截图或激活；未完成不同 AirPods、播放器、屏幕组合和系统 build 的矩阵；未验证目标用户的购买原因。以下是进入实现时必须回答的问题，不应在报告中填成成功。

| 原型 | 必须覆盖的情境 | 能决定什么 |
|---|---|---|
| 身份与动作 | 同 App 两项以上、动态 title、无 AX 标签、helper 进程、应用更新/重启 | 能否精确到 Item，哪些动作真正可用 |
| 27 后端对比 | 同一库存分别运行多 spacer 与 allow-list | 哪条路线提供所需显隐和可达性，副作用是否可接受 |
| 信息与第二栏 | 像素、AX、静态三种表示；徽章、数字、动画和失效缓存 | 目标任务是否丢失关键信息 |
| 菜单会话 | 子菜单、右键、Option、滚轮、拖动、菜单打开时触发规则 | 是否保持原交互并正确恢复 |
| 屏幕与布局 | 刘海/无刘海、宽窄混合、纵向、多缩放、Space、全屏、插拔、睡眠 | 保存意图能否跨环境稳定匹配 |
| 系统与故障 | 时钟/通知中心、摄像头与麦克风状态、权限撤销、进程退出、回调超时 | 不破坏系统状态，失败后可访问、可解释、可恢复 |
| Pro 代表流程 | 两播放器竞争、粘贴前焦点切换、文件 promise、日历拒权、天气超额、Agent 失联 | 扩展不会抢占核心操作，也不会展示虚假的新鲜数据 |

错误目标激活、数据丢失、系统隐私状态被误遮蔽、用户操作期间强行恢复布局，应视为发布阻断。支持范围内的任务需要有观测证据；范围外显示不支持或降级，不能用“稍后修复”计为本阶段已经覆盖。

衡量应围绕任务成功、误开次数、焦点丢失、人工修复次数、恢复结果，以及空闲/使用中 CPU、唤醒、内存和能耗。数值目标应在真实基线与样本上设定，本轮不提供虚构的测试成绩或确定工期。

## 六、本轮形成的决定

产品目标保留完整菜单项访问、可预测布局与输入保护；阶段范围可以缩小，目标本身不因实现困难而改写。

工程上先比较后端能力，再固定框架；让具体 Item、App 与屏幕呈现分开建模；所有布局修改经过一个能够观察结果、处理取消和尊重用户修改的协调器。界面始终展示实际支持程度。

Pro 分成独立的数据提供者和交互模块，与菜单栏内核共享状态和调度，避免某个扩展的失败拖垮整个工具。原生公开路径可验证的优先验证；未文档化或私有路径保留为明确的实验，而非默认可交付承诺。

## 参考资料与固定版本

下列资料在 2026-11-20 核查。链接到 main 的产品材料随时间可能变化；源码结论以本轮固定提交为准。文中设计建议不应误解成来源作者的实现承诺。

### 产品资料

- [S01：Bartender 6 产品页][S01]
- [S02：Bartender 6 更新记录][S02]
- [S03：Bartender 7 产品页][S03]
- [S04：Meet Bartender 7，2026-09-14][S04]
- [S05：Bartender 7 更新记录][S05]
- [S06：Bartender Pro][S06]
- [S07：Bartender 支持与鼠标问题说明][S07]

### 平台与源码

平台和扩展资料在文中按编号链接。关键源码版本：Hidden Bar ee3af2475431540ddfa211b9e1e64b08a156f8f0；Ice 11edd39115f3f43a83ae114b5348df6a0e1741cf（本轮读到的旧 main，不代表最新测试版）；MenubarHide a4476bfe81a9a84ac94f8dfb273c4eaad8f9e960。

[S01]: https://www.macbartender.com/Bartender6/
[S02]: https://www.macbartender.com/Bartender6/release_notes/
[S03]: https://www.macbartender.com/bartender7/
[S04]: https://www.macbartender.com/Bartender7/Blog/meet-bartender-7/
[S05]: https://www.macbartender.com/Bartender7/release_notes/
[S06]: https://www.macbartender.com/pro/
[S07]: https://www.macbartender.com/Bartender6/support/
[S08]: https://www.macbartender.com/B5blog/Meet-Bartender-6/
[A01]: https://developer.apple.com/documentation/appkit/nsstatusitem
[A02]: https://developer.apple.com/documentation/appkit/nsstatusitem/isvisible
[A03]: https://developer.apple.com/documentation/applicationservices/1462091-axuielementperformaction
[A04]: https://developer.apple.com/documentation/applicationservices/1462089-axobserveraddnotification
[A05]: https://developer.apple.com/documentation/screencapturekit/capturing-screen-content-in-macos
[A06]: https://developer.apple.com/documentation/appkit/nsscreen/safeareainsets
[A07]: https://developer.apple.com/documentation/appkit/nsapplication/didchangescreenparametersnotification
[A08]: https://developer.apple.com/documentation/appkit/nsworkspace/didactivateapplicationnotification
[A09]: https://developer.apple.com/documentation/iokit/1523868-iopsnotificationcreaterunloopsou
[A10]: https://developer.apple.com/documentation/network/nwpathmonitor
[A11]: https://developer.apple.com/documentation/corewlan
[A12]: https://developer.apple.com/documentation/appkit/nsstatusitem/expandedinterfacedelegate
[A13]: https://developer.apple.com/design/human-interface-guidelines/app-shortcuts
[G01]: https://github.com/consolelabs/hidden/blob/ee3af2475431540ddfa211b9e1e64b08a156f8f0/hidden/Features/StatusBar/Engine/LegacyLengthEngine.swift
[G02]: https://github.com/consolelabs/hidden/blob/ee3af2475431540ddfa211b9e1e64b08a156f8f0/hidden/Features/StatusBar/Engine/Native/HBNativeVisibilityShim.m
[G03]: https://github.com/consolelabs/hidden/blob/ee3af2475431540ddfa211b9e1e64b08a156f8f0/hidden/Features/Palette/PaletteItemPresser.swift
[G04]: https://github.com/consolelabs/hidden/blob/ee3af2475431540ddfa211b9e1e64b08a156f8f0/hidden/Features/StatusBar/Engine/NativeVisibilityEngine.swift
[G05]: https://github.com/jordanbaird/Ice/blob/11edd39115f3f43a83ae114b5348df6a0e1741cf/Ice/UI/IceBar/IceBar.swift
[G06]: https://github.com/jordanbaird/Ice/blob/11edd39115f3f43a83ae114b5348df6a0e1741cf/Ice/MenuBar/MenuBarItems/MenuBarItemManager.swift
[G07]: https://github.com/jordanbaird/Ice/blob/11edd39115f3f43a83ae114b5348df6a0e1741cf/Ice/Bridging/Bridging.swift
[G08]: https://github.com/jordanbaird/Ice/blob/11edd39115f3f43a83ae114b5348df6a0e1741cf/Ice/MenuBar/Spacing/MenuBarItemSpacingManager.swift
[G09]: https://github.com/junior-rj/menubar-hide/blob/a4476bfe81a9a84ac94f8dfb273c4eaad8f9e960/MenubarHide/CollapsedGeometry.swift
[G10]: https://github.com/junior-rj/menubar-hide/blob/a4476bfe81a9a84ac94f8dfb273c4eaad8f9e960/README.md
[G11]: https://github.com/junior-rj/menubar-hide/blob/a4476bfe81a9a84ac94f8dfb273c4eaad8f9e960/MenubarHide/MenuBarArrangement.swift
[X01]: https://developer.apple.com/documentation/mediaplayer/mpnowplayinginfocenter
[X02]: https://developer.apple.com/documentation/coreaudio/audioobjectispropertysettable(_:_:_:)
[X03]: https://developer.apple.com/documentation/appkit/nspasteboard/accessbehavior-swift.enum
[X04]: https://developer.apple.com/documentation/updates/appkit
[X05]: https://developer.apple.com/documentation/appkit/nsfilepromisereceiver
[X06]: https://developer.apple.com/documentation/foundation/nsurl/bookmarkcreationoptions/withsecurityscope
[X07]: https://developer.apple.com/documentation/appkit/nssharingservice
[X08]: https://developer.apple.com/documentation/eventkit/accessing-the-event-store
[X09]: https://developer.apple.com/weatherkit/
[X10]: https://developer.apple.com/documentation/iobluetooth/iobluetoothdevice/register(forconnectnotifications:selector:)
[X11]: https://developer.apple.com/documentation/iobluetooth/iobluetoothhandsfreedevicedelegate/handsfree(_:batterycharge:)
[X12]: https://learn.chatgpt.com/docs/hooks
[X13]: https://learn.chatgpt.com/docs/app-server
[X14]: https://code.claude.com/docs/en/hooks
[X15]: https://github.com/ejbills/mediaremote-adapter/blob/7d5b6cc99b933ae2a2378d11ee9798acf6b69009/README.md
[X16]: https://developer.apple.com/documentation/foundation/nsuserscripttask
[X17]: https://developer.apple.com/documentation/bundleresources/information-property-list/nsappleeventsusagedescription
[X18]: https://github.com/wozniakpawel/PairPods/blob/fee839a9bd21c1db8e394253f47619714ca28b86/PairPods/AudioDevice.swift
[L01]: https://github.com/consolelabs/hidden/blob/ee3af2475431540ddfa211b9e1e64b08a156f8f0/LICENSE
[L02]: https://github.com/jordanbaird/Ice/blob/11edd39115f3f43a83ae114b5348df6a0e1741cf/LICENSE
[L03]: https://opensource.org/license/mit
[L04]: https://developer.apple.com/app-store/review/guidelines/
[I01]: https://github.com/consolelabs/hidden/issues/547
[I02]: https://github.com/consolelabs/hidden/issues/523

