# 调酒师开源版｜初版产品与技术方案 v0.1

设计日期：2026-11-20  
项目原则：官方发行版免费；自有代码采用 MIT；先完成菜单栏的日常使用闭环。  
文档状态：产品范围与架构决策稿，可用于启动开发；不代表产品已经实现或通过 Mac 验收。

## 0. 本轮决定与证据边界

本轮由产品与 UX、macOS 架构、算法与可靠性三个 AI 角色独立研究，再交叉质询，由主审收敛。没有组织外部真人专家会议，没有进行新的用户访谈，也没有取得新的 Mac 实测成绩。

第二轮确立的目标是完整访问、布局可预测与输入保护。第三轮验证包已经有 35 项 Python 测试和 16 个几何样本的实际结果，但 Mac 编译与原生行为仍为 0。本方案保留这一边界。[R2][R3]

**首版的产品承诺：用户把低频项目收起来后，仍能找到正确项目、读取当前状态、完成原本操作；正在使用的菜单和用户后来作出的修改，不会被管理器打断或覆盖。**

冻结的决定：

1. 首版采用常驻／收纳两区；点击与全局快捷入口；已识别项目的基本过滤和用户别名；真实原菜单访问；交互保护；本地配置与恢复。
2. 默认手动收起。有可靠结束证据的交互才允许自动恢复；第三轮的固定 10 秒定时器不进入产品默认行为。
3. 自有列表与原菜单的操作分开。可以先定位，再由用户原位点击；“打开主应用”不算“打开菜单栏项目”。
4. Swift 6 语言模式、AppKit 系统外壳、SwiftUI 设置与列表；单进程模块化；本地版本化 JSON；Swift Testing 与 XCTest；站外签名公证分发。
5. 核心拆成 InventoryProvider、VisibilityBackend、AccessBackend 三个端口，统一由 OperationCoordinator 调度。外观、搜索、后续规则不直接改系统布局。
6. macOS 26 / Apple Silicon 作为首个实测基线；27 的原生 overflow 为并行候选。两条路径各过同样的核心门槛。验证顺序不代表 26 更可行，也不提前承诺 27、Intel 或历史系统支持。
7. 私有显隐断言不作为首版正式发行依赖。临时合成移动只进入独立研究构建，验证通过后再决定是否允许对应能力。
8. 像素镜像、第三分区、预设与规则属于后续增强；Top Shelf 对应工具集属于独立扩展域。

**仍不能冻结为“已可交付”的决定是：最终哪条系统后端能够通过刘海与容量不足时的完整可达性门槛。** 第一批开发必须回答这个问题。若 26 的原位／临时槽位和 27 的原生 overflow 都不能完成任务，产物仍是技术预览，不能靠一个静态第二栏改称正式 v1。

## 1. 产品定位与优先级依据

### 1.1 目标人群与首版任务

先服务有多个菜单栏工具、使用 MacBook 刘海内屏或接外屏、希望免费整理入口的用户。重度自动化和顶部工具集用户仍是未来人群，但不决定第一版的复杂度。

优先级依据是任务频率假设、缺失后的损害、是否有可接受的手动替代，以及该功能是否是其他能力的前置条件。没有真实转化率和访谈样本，因此以下是产品决策，不是已证实的购买动机排行榜。

首版完成五步：整理 → 查找 → 辨认 → 原生操作 → 恢复访问。频繁需要手工修理、点错项目或中断菜单，会直接破坏这个闭环。主题、预设等增强有价值，但无法补偿这些失败。

### 1.2 Bartender 的参考边界

Bartender 6 已有第二栏、搜索、分组、预设与触发器；这些不应被误列成 7 或 Pro 才提供的功能。7 强调可不录屏、Command Bar 和输入体验；其不录屏模式会用 App 图标代替菜单栏项目画面。7.1 的更新记录已加入 Tahoe 支持，7.2 又改进按刘海／溢出条件显示第二栏。以具体更新记录处理官网旧文案的冲突。[S01][S02][S03]

Pro / Top Shelf 增加媒体、日历、天气、剪贴板、文件暂存与 Agent 等任务。这些是扩展范围，不是菜单栏核心全部功能的付费归属。[S04]

本项目采用独立名称、图标、文案与实现。MIT 允许第三方商业使用；“官方版本免费”是发行承诺，不是禁止他人收费的许可证条款。[L01]

## 2. 首版功能范围

### 2.1 P0：缺失会破坏日常使用，或无法成为可信的常驻工具

| ID | 首版功能与业务规则 | 为什么必须做 | 验收边界 |
|---|---|---|---|
| F01 | 常驻／普通收纳两区。只展示后端能兑现的 Item、App 或连续区间粒度；用户先手动组织少量项目 | 整理是入口价值；显示一个单项开关却连带影响整组会破坏信任 | 实际结果与预览范围一致；分区不成立则不提交 |
| F02 | 一个常驻控制入口，点击展开／明确收起，一个可配置全局快捷键；窗口中有撤销限制入口 | 收纳项目必须随时找得回，控制器不能把自己也藏死 | 鼠标和键盘入口可达；冲突或注册失败有反馈 |
| F03 | 刘海、长应用菜单和容量不足时仍能访问真实目标 | 这是小屏用户最主要的价值；只挤出画面没有完成任务 | 目标在声明支持的配置中有真实可用入口；拒绝收起仅算保护，不算完成访问 |
| F04 | 已识别 Item 的目录、名称／别名过滤、待确认项提示 | 同一 App 的多个项目不能用同一个名字或列表首项代替 | 测试靶三个项目逐一正确；重排和重启后歧义不触发精确动作 |
| F05 | 保留原菜单、左／右键、Option 与子菜单；允许“定位后原位操作” | 菜单栏工具的价值在原本的交互，不能被简化成 App 启动器 | 真实菜单可打开并继续选择；无重复触发、错误目标或指针回跳 |
| F06 | 菜单会话保护和串行操作协调 | 自动收起、搜索、拓扑事件不能互相抢布局 | 菜单未结束时没有冲突变更；超时进入未知并保持访问 |
| F07 | 保存分区、别名、逻辑顺序与用户意图；用户新修改优先 | 重启、唤醒后不应不断重做设置，也不能被旧恢复覆盖 | 配置不丢失；已验证组合在常规重启／唤醒后仍保持可用分区与访问；需要反复手动重整的组合不能算完整通过 |
| F08 | 动态信息诚实呈现。关键持续状态可常驻；其余可通过真实原项读取 | 旧图像或通用 App 图标不能冒充当前电量、计数或连接状态 | 来源和新鲜度明确；无可靠数据时显示未知或引导查看原项 |
| F09 | 权限分层、拒绝和撤回后的明确行为 | 不愿录屏的用户仍能使用不依赖画面的功能 | 基础收放、精确识别与像素功能分别降级；不反复索权、不假成功 |
| F10 | 保护时钟、通知中心、控制入口与摄像头／麦克风指示和来源提示 | 系统状态完整是常驻工具的底线 | 收纳、打开通知中心、新采集开始、持续采集与退出后均观察完整 |
| F11 | 本地原子配置、版本迁移、修改前备份、用户选择登录启动、可查看兼容原因 | 更新或配置损坏不能让已配置环境失控 | 写入失败不部分覆盖；损坏有上一个有效版本；启动选项可撤销 |
| F12 | 本工具的键盘与 VoiceOver 支持、系统深浅模式、减弱动态效果，以及常驻资源检查 | 第一版要能长期使用，不能只在展示时正常 | 入口、目录、过滤、设置和恢复流程完整可达；第三方交互保留基线能力；无持续无效扫描，有真实资源记录 |

这些是产品应达到的要求，不是现有验证包已经完成的能力。第三轮的 Controller 还没有产品级会话锁、精确全局库存或完整恢复。

**两处范围必须说清：**

- 配置持久化与实际布局稳定分别验收。v1 保存逻辑意图，但不能以 JSON 仍在代替重启后的可用分区与访问；反复要求用户手动重整的组合记为部分支持。原位手动整理先由系统保持；本工具造成的临时改动必须可审计。精确重排能力不足时保留访问并说明限制，不因此改写第三方 App 的偏好文件。
- “未知项目不主动隐藏”指不为它产生新的隐藏意图。连续区间后端仍可能把新注册在该区间里的项目一起挤出；发现未知或库存不完整后应保守展开，并验证发现延迟。不能宣称未知项目绝对不会短暂被隐藏。

### 2.2 P1：提高效率与舒适度，可以在核心闭环之后加入

| 功能 | 建议顺序与原因 | 技术前置 |
|---|---|---|
| 始终隐藏第三分区 | 两区稳定后加入；减少普通展开时的低频噪声 | 普通展开、专用唤出、搜索和撤销限制的语义独立；后端能保持对应区间 |
| 高级搜索、缩写／拼音、最近使用、单项快捷键 | 基本过滤后迭代；重度键盘用户收益明显 | 可靠 Item 身份、冲突检测与可解释结果 |
| 手动预设 | 先于自动规则；工作、移动办公和演示之间一键切换 | 计划差异、可取消提交、手动修改优先 |
| 显示器关联预设 | 手动预设成熟后做 | 稳定拓扑标识、插拔收敛和独立基线 |
| 电源／时间／前台 App 的少量规则 | 首批自动化范围限定，暂不做复杂条件编辑器 | 三值条件、防抖、优先级、会话保护 |
| 动态项目图像与变化提醒 | 作为可选增强，不让录屏成为基础使用前提 | 来源可捕捉、缓存失效、时间戳、更新与能耗预算 |
| Hover、滚动、滑动和指针附近唤出 | 默认关闭；减少操作距离但也容易误开 | 输入冲突、延迟、焦点和多屏测试 |
| 分组、标签、分隔符 | 改善大量项目的辨认 | 视觉分组与实际显隐域分开建模 |
| 自有面板主题与细节 | 原生深浅模式之后做 | 对比度、可点击区域、减弱透明度／动态 |
| 配置导入导出 | 本地备份与迁移之后做 | 格式校验、重绑定、冲突预览，不携带敏感缓存 |
| 系统菜单栏间距与全局样式 | 单独作为兼容性成本较高的项目 | 不能用修改所有 App 偏好或强制结束其他进程换取整齐 |

“始终隐藏”曾被归为完整菜单栏工具的广义基础，本轮后置是首版两区范围的决定，并未否认其价值。它不是加一个布尔字段就能可靠实现的第三状态。

### 2.3 P2：独立扩展域

剪贴板历史、文件暂存与 AirDrop、跨播放器媒体控制、天气、日历、Agent 状态、AirPods、脚本 Widgets、云同步全部后置。将来选择需求最明确的一个模块独立交付，而不是同时铺满。

这些模块各有数据源、权限、缓存和故障模式。架构只保留将来可接入的边界，不在 v1 预先建通用插件市场、脚本运行器或云账户系统。

## 3. 首版交互设计

### 3.1 初次使用

启动后先观察系统版本与当前能力，不立即收起所有项目。界面只有“开始整理”和当前可用范围。用户进入项目目录时，再解释辅助功能对读取第三方项目的用途；若只使用基础几何入口，不强迫同时授权其他功能。

v1 没有像素镜像时，不显示一个尚不可用的录屏开关。以后引入真实项目画面时，单独说明它与 App 图标的差别，允许继续使用无画面模式。权限判定来自当前进程的实际观察，打开系统设置不等于授权完成。

第一次整理显示“保持常驻”和“收纳”。每次提交前说明实际影响范围。如果底层只能一起控制一个 App 的三个项目，UI 必须一起选中或明确阻止拆分；不能先显示三个独立开关，执行后才解释连带效果。

### 3.2 日常入口与项目行

点击图标展开；快捷键打开同一个入口并聚焦过滤框。默认不启用 Hover、滚动或自动收起。

每行只显示用户需要决定的信息：名称／别名、所属 App、可取得的状态及其有效性、当前可执行动作。三种操作必须分开：

- 打开原菜单：只有该 Item 的这项动作已验证时显示。
- 显示并定位：真实原项被确认可见后，提示用户在原位操作。
- 打开应用：独立的辅助动作，不冒充前两种。

方向键导航、Enter 执行当前明确动作、Esc 关闭本工具面板。Esc 不自动等于第三方菜单已经结束，也不自动解除它的交互保护。

本工具的入口、目录、过滤、设置和恢复流程提供键盘与 VoiceOver 支持；第三方原交互的可访问性不低于无管理器基线。纯键盘完成的端到端访问路径另行声明与验收，不宣称修复第三方控件原本缺失的键盘或读屏支持。

状态缺失使用“暂时无法读取状态”“项目需要重新确认”等具体文案。诊断页可以显示后端与证据；普通操作页不显示 API 名、内部 epoch 或异常栈。

### 3.3 布局与视觉方向

使用系统字体、SF Symbols、原生选中与焦点、系统深浅模式。设置分为“整理”“快捷键”“权限与兼容”“关于”。面板默认靠近当前触发屏幕的控制入口，不跨屏猜测位置；搜索字段清晰，动态数据与普通名称的层级分开。

可在 AppKit 的 NSPanel 容器内放置 SwiftUI 列表；系统窗口激活、原菜单和焦点交接仍由 AppKit 控制。非激活面板与键盘搜索需要专门验证，不能只加一个 styleMask 就假定焦点行为正确。

这一版不复制 Bartender 的玻璃主题、品牌和顶部灵动岛。设计质量首先体现为目标清楚、点击稳定、状态可信和操作过程中不跳动。

### 3.4 收起与恢复

默认用户明确收起。只有正向确认菜单结束，且临时布局仍属于当前操作时，才允许自动恢复。结束无法确认时，保持展开，给出“暂时保持展开；关闭菜单后可手动收起”。

“撤销本工具的收纳限制”是恢复入口：撤回本工具自己的限制与仍可确认归属的临时变更。它不会重新开启用户在系统设置里原先关闭的项目，也不能保证所有图标同时塞进第一行。

## 4. 多角色讨论的关键裁决

| 争议 | 产品侧要求 | 工程侧证据与异议 | 本轮决定 |
|---|---|---|---|
| 首版是否必须复制第二栏 | 小屏上所有常用项目可访问 | 自绘面板、图像和原菜单访问是三件不同工作 | 必须有真实可达路径；自有目录是 P0，实时镜像第二栏 P1 |
| 是否必须一键代理全部交互 | 快速且不点错 | AXPress 不等于右键、Option 或滚轮 | 已验证动作才代理，其余允许真实原位操作；不可达则不合格 |
| 始终隐藏是不是必需 | 展开时减少低频噪声 | 增加第三状态与后端粒度冲突 | 首版两区；第三分区 P1 |
| 自动收起是否默认开启 | 用完恢复整洁 | 第三方菜单结束并非普遍可观测 | 默认关闭；正向结束证据才恢复，超时不强制收起 |
| 是否直接采用私有 allow-list | 希望 27 尽快可用 | App 粒度、系统状态、生命周期和维护风险未消除 | 不进入 v1 正式依赖；原生 overflow 先做同任务验证 |
| 是否冻结 26 为正式后端 | 有 26 的潜在实测设备 | 展开仍受刘海限制，临时让位尚未证明 | 26 只排在首轮验证，不预判一定先发 |
| 是否用全局最优匹配解决身份 | 多项和重启后能找回 | 最优算法也可能只是“最好的错误配对” | v1 确定性唯一匹配＋用户确认；模糊匹配只作后续建议 |
| 是否给每个模块独立进程 | 扩展故障不拖垮主工具 | v1 拆进程增加 IPC、权限与状态恢复复杂度 | 先单进程明确模块边界；必要时单独隔离高风险提供者 |
| 是否为了排序写其他 App 偏好 | 希望重启后完全复原 | 其他 App 的状态项偏好、创建时机与用户新修改不受本工具事务控制 | v1 不走该修复路径；保留逻辑意图与可观察的最小变更 |

结论保留了主要分歧的原因。所有“支持”的最终判定仍由 Mac 原始证据决定；角色共识不能替代平台事实。

## 5. 技术栈与发行决策

| 层 | 采用方案 | 选择理由与边界 |
|---|---|---|
| 语言 | Swift 6 模式，严格并发检查 | 主平台 API 直接接入；小范围 C／Objective-C 桥只用于确有必要的边界 |
| 系统外壳 | AppKit：NSApplication、NSStatusItem、NSPanel、NSWindow、NSMenu | 控制状态项、窗口生命周期、焦点与原生事件；不把第三方 NSView 搬入自己面板 |
| 设置和目录 | SwiftUI 嵌入 AppKit；本地化 String Catalog | 适合声明式设置与列表；避免把全部系统交互塞进视图 |
| 第三方观察 | ApplicationServices / Accessibility、AXObserver；必要时 Quartz 窗口元数据作为辅证 | 数据可能缺失或由宿主提供；每个 Item 动作单独验证 |
| 画面捕捉 | ScreenCaptureKit，P1 可选适配器 | 捕捉范围与授权模式独立设计；不承诺隐藏 Item 天然可单独抓取 |
| 并发 | MainActor UI＋AX 专用线程／RunLoop＋单消费者命令队列 | Swift actor 隔离不等于跨 await 的事务；不让同步 AX IPC 阻塞 UI |
| 配置 | Codable 的版本化 JSON、原子替换与上一个有效备份；UserDefaults 仅放小偏好 | v1 数据量小、结构清楚，无须业务服务器或复杂数据库 |
| 全局快捷键 | KeyboardShortcuts，经 HotkeyAdapter 包装并锁定经验证版本 | 有原生录入器与部分冲突反馈；实际系统注册和其他工具冲突仍需测试 |
| 登录启动 | SMAppService.mainApp | 用户选择启用，读取真实状态，不手写后台守护进程 |
| 更新 | Sparkle 2，正式发布集成；手动检查为基础，自动检查由用户选择 | 系统兼容修复需要稳定更新通道；保留全部第三方 notices |
| 日志与性能 | OSLog、少量 signpost、本地有界诊断导出 | 不默认上报、截屏或保存第三方菜单正文；诊断可按用户操作生成 |
| 测试 | Swift Testing 测纯模型／状态机；XCTest／XCUITest 测本工具界面；真实 Mac 任务验收 | UI 自动化能力不等于全系统交互可自动验证 |
| 构建 | Xcode 项目＋内部 Swift Package；固定工具链、SDK 和依赖锁 | 不使用浮动分支发版本；具体 Xcode 小版本在首台 Mac 构建后固定 |
| 分发 | Developer ID 签名＋Hardened Runtime＋公证，站外发布 | 首版完整工具不以 Mac App Store 为主发行路线；不要求用户关闭系统保护 |

原生技术栈的选择是维护与系统集成判断，不是本轮测得 Swift 比其他框架快多少。Electron、跨平台壳或额外 Rust 核心不会解决跨进程 Item 发现、可达性和菜单生命周期，因此不在 v1 增加这些边界。

Apple 文档中的 NSStatusItem 围绕由应用创建并持有的状态项；没有因此获得任意第三方 Item 的全局管理权限。isVisible 也可能在项目因空间不足临时不可见时继续为 true，不能用它单独证明可达性。[A01][A02]

Swift 文档说明 await 是可挂起点，其他工作可以在此期间运行；单个 actor 不能取代操作队列、版本校验和会话保护。[A06] Apple 将辅助应用使用的 Accessibility API 列为 App Sandbox 不兼容活动，而 App Store 分发要求 Sandbox，因此本方案选择站外发行。[A07]

SMAppService 负责登记登录项并暴露状态；登记请求仍受用户批准控制。[A08] KeyboardShortcuts 提供可配置全局快捷键与系统／应用菜单冲突提示，不代表能预知所有第三方软件冲突。[D01] Sparkle 支持更新签名；本项目采用 HTTPS、Apple 签名公证及更新包签名，具体集成版本在首个发行构建固定。[D02]

首版最低构建目标拟定为 macOS 26，Apple Silicon 优先；这是一项产品支持范围选择。第三轮验证包能以 macOS 14 作为编译最低版本，不等于正式产品已经兼容 14。27 后端为独立能力轨道；Intel 与历史系统需要新增实机资源和矩阵后再决定。

## 6. 架构、端口与数据模型

### 6.1 业务状态的四层

UserIntent 保存用户希望怎样组织；ObservedState 保存系统当前实际暴露什么；EffectivePlan 是在现有能力下准备执行的最小计划；OperationReceipt 记录实际尝试、观察结果和仍可归属于本操作的变更。

持久化意图不等于系统当前状态，计划也不等于执行结果。每次界面更新应由观察和结果驱动，不能在调用 API 后立即把整组项目涂成“已经收纳”。

~~~mermaid
flowchart TD
    UI["状态项、目录、设置"] --> Q["统一操作协调器"]
    Rules["后续规则"] --> Q
    Inv["库存与状态观察"] --> Q
    Q --> P["纯计划器与能力检查"]
    P -->|计划| Q
    Q --> V["VisibilityBackend"]
    Q --> A["AccessBackend"]
    V -->|观察结果| Q
    A -->|观察结果| Q
    V --> OS["macOS 与第三方项目"]
    A --> OS
    OS --> Inv
    Q --> Store["用户意图与变更记录"]
    Q --> UI
~~~

### 6.2 模块职责

| 模块 | 输入与输出 | 禁止承担的职责 |
|---|---|---|
| InventoryProvider | 输出带来源、新鲜度和完整性的库存快照 | 不根据宿主 PID 猜生产者，不私自点击或排序 |
| IdentityResolver | 将当前观察与逻辑 Item 作唯一绑定或返回歧义 | 不按列表第一项、动态标题或旧坐标自动配对 |
| CapabilityRegistry | 按 OS build、后端版本、Item-action、权限和拓扑登记证据 | 不将一个系统版本的成功推广到所有版本 |
| LayoutPlanner | 生成受影响域、前置条件、动作与预期观察 | 不直接碰系统对象，不把经验宽度当平台保证 |
| VisibilityBackend | 执行受许可的几何或显隐计划 | 不偷偷扩大到未预览的 App／区间 |
| AccessBackend | 返回真实访问路径、执行已验证动作 | 不自行收放或重排；临时布局需求回到协调器 |
| OperationCoordinator | 串行消费命令，管理租约、代次、取消和观察 | 不在动作未知时自动重试，也不把取消当已回滚 |
| PresentationStore | 给 UI 提供值快照与具体操作状态 | 不持有可跨线程随意使用的 AX 引用 |
| ConfigStore / RecoveryJournal | 用户配置、迁移、备份和未结束操作的最小记录 | 不持久化活 AX handle、旧 PID 或完整第三方布局 |
| Diagnostics | 本地有限日志、版本与测试条件 | 不默认存第三方菜单正文、屏幕图像或远端上报 |

三个系统端口是正式设计：发现、显隐和访问可以分别拥有不同能力。比如几何显隐只支持连续区间，但某些项目可以精确 AX 访问；二者不能共用一个笼统的 supported=true。

VisibilityDomain 必须表达 individualItem、application、contiguousRange 或 ownItems，并说明是否跨屏共同生效。共享状态项的 length 不能伪装成“每台显示器独立隐藏同一 Item”。

AccessResult 至少区分：

~~~text
located(item, presentation, observationRevision)
actionSubmitted(operation)
observedMenuOpen(item, evidence)
ambiguous(candidates)
blocked(reason)
unsupported(reason)
outcomeUnknown(operation, reason)
~~~

内部动作提交成功不能直接转换成“用户任务完成”。完整业务成功还包含正确目标、原菜单可继续操作和没有副作用。

### 6.3 持久对象与瞬时对象

| 对象 | 主要字段 | 说明 |
|---|---|---|
| ProducerIdentity | bundle、可验证的路径／签名线索、确认记录 | 可缺失；宿主进程与生产者分开 |
| LogicalItem | 本地 UUID、生产者、稳定属性证据、别名、期望分区 | UUID 是本产品身份，不是系统保证的 Item ID |
| RuntimeBinding | 进程生命周期、AX 引用所属执行域、绑定版本、inventoryEpoch | PID／窗口号不能跨重启当永久主键 |
| Presentation | display ID、frame、坐标系、单位、scale、topologyEpoch、observedAt | 同一 Item 可有多个呈现；未证实的副本不强制合并 |
| StateObservation | value、source、observedAt、freshness、completeness | unknown 不等于 false、0 或没有变化 |
| DesiredLayout | userRevision、逻辑分区、顺序与邻居锚点 | 临时展开不写成永久布局 |
| OperationTicket | ID、generation、配置／库存／权限／拓扑版本 | 外部动作前后重验 |
| MutationRecord | before、applied、受影响域、邻居、owner、状态 | 只记录本工具确实作出并观察到的变更 |

可见性至少分为 configuredVisible、observedInBar、observedInOverflow、offscreen、unknown。不能用一个 Boolean 混合用户意图、系统声明和实际可见。

版本递增规则必须分开：inventoryEpoch 只用于身份集合或运行期绑定的结构变化；动态数值与普通展示刷新只更新 observationRevision。本操作预期内、已验证的布局变化更新 applied 与预期中间态，不使自己的 ticket 自动失效；外部或无法归因的变化仍触发重新检查。userRevision 记录用户意图修改，topologyEpoch 和 permissionEpoch 分别记录相关环境能力变化。

### 6.4 并发边界

MainActor 持有自有 AppKit 对象和 UI。同步 AX IPC 与 AXObserver 留在专用线程／RunLoop，跨边界传 Sendable 值快照。AXObserver 的 RunLoop 注册、重建与失效都由适配器持有。[A09]

Coordinator 可以用 actor 隔离状态，但只有一个执行循环消费会产生系统副作用的命令。观察事件允许更新 epoch；执行循环在每个 await 恢复后重新检查 ticket。取消让后续工作失效，不自动撤回已发送给其他进程的动作。

队列有上限。同一域反复出现的布局意图合并成最新计划；明确用户动作不能静默丢失，也不能过几分钟才突然重放。结果未知时释放普通计算资源，但保留必要的交互保护和可解释状态。

初版目录、设置与后端使用一个仓库、一个应用 target 和若干内部模块即可。暂不引入微服务、通用消息总线或多仓库同步。

## 7. 业务流程与关键算法

以下是设计伪代码与不变量，不是已经编译的产品代码。

### 7.1 项目发现与身份匹配

第一版使用确定性、可解释的唯一匹配：

1. 同一次进程生命周期内，保留仍可重新验证的 live binding。
2. 有稳定标识时，必须在已确认的生产者候选集合中唯一，且角色等约束相容。
3. 没有唯一标识时，只接受当前仍唯一成立的用户确认映射。
4. 重复标识、同名项目、动态标题、宿主切换或重启后的不确定都进入待确认。
5. 未匹配旧 Item 保留用户配置，不把它套到新出现的第一项。

~~~text
resolve(savedItem, inventory):
    if inventory is stale or incomplete for the required scope:
        return unknown

    if saved live binding is uniquely revalidated in the same process lifetime:
        return bound(currentHandle)

    candidates = verifiedProducerCandidates(savedItem)
    matches = candidates matching present stable identifier and compatible role
    if exactly one and identifier is collision-free:
        return bound(matches[0])
    if more than one:
        return ambiguous(matches)

    matches = candidates matching a still-valid user-confirmed discriminator
    if exactly one:
        return bound(matches[0])
    return unresolved(candidates)
~~~

动作执行前重新解析当前目标，不能永久相信列表打开时的 frame。动态数字不能一律删除来制造稳定标题：不同项目可能恰好靠数字区分。没有标注样本时不输出“95% 置信度”这类看似统计化的概率。

P1 可用带未匹配节点的最大权匹配／Hungarian 算法协助提出候选，避免多对一匹配；它不自动授权点击。位置、图像和标题相似度仅为建议线索，硬约束与用户确认继续优先。

### 7.2 基本搜索

v1 对已绑定 Item 的显示名、用户别名和已确认 App 名进行本地过滤。使用一致的 Unicode／大小写处理，保留用户原始文本；不要把不同语言字符粗暴转写成同一个身份。

默认排序：完全匹配 → 前缀 → 包含 → 稳定的用户顺序。最近使用和模糊相关性后置，避免结果在用户准备按 Enter 时重新排序。键盘选中绑定 item key 与 observation revision，库存变化时重新确认。

歧义条目可作为“待确认的三个项目”展示；允许展开原位供用户判断，但禁用假精确动作。选择结果之后能返回 located、menu-open 或 unknown 等不同结果，UI 不统一显示一个绿色成功提示。

### 7.3 显隐计划与两区组织

对于连续区间后端，首版编辑方式应是引导用户在原生菜单栏手动调整项目或边界，系统观察后再形成分区。目录可显示两区，但在没有经过验证的移动后端前，不提供看似能任意移动第三方项目的列表拖拽。

~~~text
planVisibility(intent, observed, capabilities):
    require current topology and inventory needed by the operation
    domain = resolveActualControllableDomain(intent)
    if domain would include an unapproved/protected target:
        return blocked with affected-scope preview
    if current interaction conflicts with domain:
        return deferred
    if backend geometry preconditions fail:
        return rejected
    return minimal plan + expected observation + owned mutation fields
~~~

新项目、拓扑改变或授权撤回使原计划失效。未知项目不能被自动加入隐藏意图；区间后端发现未知时请求展开并重新观察。发现能力不足本身要进入兼容门槛。

系统保护意图不能只是一份图标名字黑名单：名称会本地化、宿主会变化。已知系统项目需要适配证据，未知系统状态要保守处理；实际像素或交互被遮蔽时，不得以“我们没有主动选中它”作为通过理由。

### 7.4 刘海、空间不足与后端选择

目前保留三个具体实验，而非一个空泛的 makeRoom()：

| 实验 | 前置与动作 | 能决定什么 | 不能推出什么 |
|---|---|---|---|
| E26-A：不可见目标的精确 AX 动作 | 对唯一、当前且声明对应 action 的 Item 发送一次动作；观察菜单位置与后续选择 | 该 Item-action 是否能直接到达真实菜单 | 左键成功不代表右键、Option、滚轮或其他 Item 成功 |
| E26-B：临时可见槽位 | 源 frame 真正可命中、目标槽足够、输入空闲、身份和邻居可观察时，研究一次受限 Command-drag；移动后重新验证 | 该条件下是否可安全让位并保留原交互、最小恢复 | 完全离屏或宿主不暴露的目标不满足前置；负坐标不是可靠路由 |
| E27-A：原生 overflow | 多占位计划合格后，逐个进入系统 overflow 使用三个同 App 项目 | 原生收纳能否保留身份、动作和状态 | 出现 overflow 图标不等于全部交互完整 |

E26-B 是独立研究构建，正式版默认关闭。Quartz 能发送事件并不保证其可可靠重排任意第三方状态项。必要的未文档化宿主／窗口路由需要独立评审，不能藏进普通点击实现。

自有列表分页不会让原项变得可点击，因而不是第四条已证明的方案。激活一个左侧菜单较短的 App 也不能保证给任意数量项目腾出空间，且会改变焦点。

26 的几何与 27 的多占位都需要运行时证据。第三轮已知样本中，1512／663.5 pt 内屏加 3440 pt 逻辑宽外屏时，433 × 7 = 3031 pt，模型目标少 409 pt，应拒绝新收起；这不是实测漏出 409 pt。[R3][G01]

几何保护固定检查非空、有限正值、实际刘海右侧区域、经验阈值余量和总容量。六个 spacer 与 64 pt 余量是候选模型的参数，不是 macOS 硬约束。改变数量或公式要成为新候选重新验收，不能无限增加占位项试错。

### 7.5 多屏坐标与拓扑收敛

所有 frame 必须带坐标空间、单位与 topologyEpoch。内部布局使用逻辑点；AX／AppKit／Quartz／捕捉像素各走显式转换适配器，不把整个桌面统一乘一个 scale。

屏幕归属使用二维矩形和 display 映射，覆盖负坐标、上下排列与混合缩放，不能只按 x 判断，也不能永远用当前主窗口屏幕代替目标屏幕。刘海几何使用实际 safe area 与 auxiliaryTopRightArea；它提供输入，不提供隐藏效果保证。[A10]

屏幕变化时先使旧 ticket、旧坐标和旧恢复权失效，不等于立即改写长度或回放旧布局。由新的 RecoveryIntent 重新观察，决定哪些自有限制仍可撤销；菜单未结束或状态未知时，普通恢复继续尊重交互租约。确需救援才能恢复访问时，应记录实际布局变更及菜单是否被中断，不能把救援中的中断计为正常流程无打断通过。重新取稳定拓扑与库存后再规划；稳定性通过有限连续观测判定，不能睡固定一秒就假定系统完成注册。连续变化有总预算，超出后暂停新收纳，保留可确认安全的恢复入口并说明暂缓整理。

屏幕设备标识可以辅助同一机器的配置，但克隆 EDID、重复显示器和重连都可能产生歧义。首版不承诺跨机器全自动匹配显示器预设。

### 7.6 菜单会话与操作仲裁

InteractionLease 覆盖整个受影响显隐域。一个占位项能影响多个项目，因此不能只锁住用户点的那一行。

~~~mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Resolving: 用户请求
    Resolving --> Revealing: 目标唯一
    Resolving --> Held: 歧义或能力不足
    Revealing --> InUse: 原生访问成立
    Revealing --> Held: 结果未知
    InUse --> Held: 结束无法确认
    InUse --> RestoreCheck: 正向结束证据
    Held --> RestoreCheck: 用户明确结束或新证据
    RestoreCheck --> Idle: 所有权仍有效并完成最小恢复
    RestoreCheck --> Held: 用户修改或观察不足
    Held --> Idle: 用户接管并撤销本工具限制
~~~

Held 表示保持访问、禁止后台冲突变更，不表示系统菜单一定仍打开。自绘弹层、helper 进程和多个子菜单都可能使结束观测不完整。

AXObserver 通知并非所有目标都支持；27 的 expandedInterfaceDelegate 管理应用自己的状态项，不能监听所有第三方菜单，且绑定 NSMenu 的项目也不走该展开回调。[A04][A05]

原子操作规则：

- MenuOpen 或 EndUnknown 时，自动规则、自动收起和预设重排不得改变该域。
- 计时器可触发重新观察或提示，不能把“经过几秒”解释成“用户用完”。
- 新搜索不抢走当前原菜单；排队或让用户先结束本次操作。
- 明确的用户收起属于新意图，要取消旧恢复并重新检查；不能称作自动确认菜单结束。
- 目标退出、权限撤回、拓扑改变或用户新修改都会使旧绑定失效。
- AX 超时或 CannotComplete 后不自动再发一次。Apple 明确该错误可能来自目标的模态处理，动作可能已经发生。[A03]

### 7.7 恢复：三快照与所有权

保存 before（操作前）、applied（本工具变更后实际观察）和 current（当前新观察）。恢复只做本操作仍拥有的最小逆操作。

~~~text
restoreOwnedMutation(record):
    if ticket, userRevision, topologyEpoch or permissionEpoch changed:
        abandon old inverse; keep access available
        return

    current = observe affected domain freshly
    if incomplete, ambiguous or related interaction unresolved:
        abandon old inverse; explain uncertainty
        return

    if fingerprint(current) differs from fingerprint(record.applied):
        preserve current; treat new arrangement as user/system update
        return

    for step in minimalInverse(record.confirmedMutations):
        recheck ticket and neighbors against latest verified intermediate state
        if changed: stop
        perform one step
        observed = observe outcome
        if observed is unknown or differs from this step's expected result:
            stop remaining inverse; preserve journal as unresolved
            return
        update expected intermediate state from the verified result
~~~

指纹包含逻辑身份、相对顺序、邻居锚点、分区边界、相关拓扑和本工具改变的字段；容差由回归样本校准。没有收到拖拽通知，不证明用户没有动过。

每步恢复都以最近一次已验证的中间态为基准，不能因为自己的上一步逆操作改变了邻居，就误判为外部修改。任一步结果未知或不符合预期，立即停止剩余逆操作；记录保留为未解决，不在下一次启动盲目重试。

这是应用层的乐观并发检查，不是 WindowServer 提供的原子 CAS。检查与系统动作之间仍有竞争窗口，因此 v1 默认不自动重排其他 App 项目；临时移动若必要，必须以独立适配能力通过验证。

例如 before=A-B-X-C，applied=A-X-B-C，而 current=B-A-X-C。当前顺序已不是本操作留下的结果，应保留新排列，不把整份 before 写回。搜索临时展开也不应被保存为永久分区。

正常退出、强制结束、主线程卡死与下次启动恢复分别验收。启动发现未完成 journal 时，不按旧 PID、frame 或整份旧排序回放；先观察，只清理可确认属于本工具的资源。进程内定时器不能作为进程卡死后的救援保证。

### 7.8 初版仲裁与后续规则算法

v1 虽不提供规则编辑器，仍要有统一优先级：

系统状态与输入保护 → 当前交互租约 → 明确用户意图 → 仍拥有的临时恢复 → 后台默认整理。

系统事件的高优先级首先意味着失效旧操作和重新观察，不自动授予破坏当前菜单的权限。恢复入口“撤销本工具限制”可以按新的恢复意图接管自己的资源，但普通后台任务不绕过会话保护；必要救援造成的中断如实记录。重复请求合并，用户修改增加 userRevision，使旧计划失效。

P1 的规则只产出 ProposedIntent，不直接调用后端。规则至少包含条件、目标、优先级、进入／退出稳定条件、冷却、失效时间和解释原因。数据源采用 true／false／unknown：

- unknown 不等于 false。权限被撤回或状态源失联时，不因此推出新的自动隐藏。
- 防抖合并短时间重复事件；滞回让进入和退出条件不同；冷却限制来回切换。
- 同一域计算一个最终意图，并记录胜出的原因；操作带因果 ID，避免自己的变更反过来触发逆规则。
- 第一批只支持电源、时间和已确认前台应用／显示拓扑。网络路径不能自动等于某个 SSID，也不能据此断言公共 Wi-Fi 或 VPN 状态。
- 若做低电量显示，可在原型用“≤20%进入、≥25%退出”演示滞回；这是待校准的产品参数，不是已优化结果。时间、时区和唤醒后要重新计算，不能只保留启动时定时器。

### 7.9 动态状态与像素

每个列表字段带 source、observedAt、freshness。App 图标只帮助识别应用；AX value 只呈现实际暴露的信息；截图是过去某一时刻的画面。缺数据不造值，旧帧不无限期标实时。

v1 优先让用户看到真实原项。持续需要监视的数值可保留常驻；基本目录不承诺完全镜像隐藏状态。P1 引入 ScreenCaptureKit 时，源必须是实际可共享内容，捕捉范围和生命周期可控；其 API 不保证任意隐藏、离屏或系统合成状态项可单独抓到。[A11]

不能为了后台刷新图像反复展开真实菜单栏。无法取得隐藏图像时显示状态不可用，让用户选择查看原项。权限、目标、显示拓扑改变后缓存失效，默认仅内存缓存；是否落盘必须由之后的功能决定和说明。

系统内容选择器的用户选源会话与一般屏幕捕捉权限是不同路径。使用 picker 也不等于应用获得无需用户选择的持续全屏访问；具体选择在像素原型中验证。[A12]

### 7.10 常驻资源预算

先约束结构，再用真实数据定标：

- 空闲时不持续捕捉画面、不逐帧扫描所有项目。
- 事件驱动加有界重新扫描；无响应目标单独退避，不拖累全局。
- AX 每个对象设置消息超时，并限制节点数与总查询预算。只在根对象设置超时不会自动覆盖其他对象。[A13]
- 本地缓存检索与后台库存扫描分离，打开列表不等待全部 AX 查询完成；过期状态清楚标记。
- 界面关闭时停止仅用于该界面的高频更新。
- 日志、诊断和恢复记录有容量与保留策略，写入失败要能解释。

首轮可暂定热缓存面板打开 p95≤150 ms、≤200 条本地过滤 p95≤50 ms，作为待校准目标。CPU、RSS、能耗和唤醒预算必须在真实基线下确认；当前不填虚构的达标数值。测量须记录硬件、OS、项目数、显示器、模式、前后台和采样窗口。

## 8. 后端支持策略与发布范围

| 对象 | 当前状态 | 初版决定 |
|---|---|---|
| 26／Apple Silicon 的基础两区几何 | 有实验源码，未 Mac 编译／运行 | 首轮开发与验收；通过才能进入正式能力表 |
| 26／刘海与超宽库存 | 完整访问仍是阻塞实验 | E26-A/B 不能完成主任务时，不宣称该人群完整可用 |
| 27／多 spacer 与原生 overflow | 有源码依据、模型检查和容量反例，没有运行证据 | 并行实验，用同一组 P0 任务验收 |
| 私有 bundle allow-list | 第三轮只有存在性探针 | v1 正式构建关闭，不作静默兜底 |
| AX 精确动作 | 逐 Item-action 验证 | 只为已证路径开启；其他动作原位访问或明确不支持 |
| 像素镜像 | 可选路线未完成验证 | P1，基础版不需要持续捕捉 |
| Intel、14／15、未知大版本 | 未进入正式测试范围 | 不自动继承支持；新增矩阵后再决定 |

每个支持条目绑定 OS build、硬件类别、后端 revision、权限模式、拓扑范围与动作集合。升级到未知大版本时，不复用旧版 verified 标签；保留诊断和撤销本工具限制的入口。

能力四态采用 verified、experimental、unsupported、unknown。能力受限可返回具体限制；若部分子动作通过，应拆成多个 capability，而不是让一个模糊 partial 掩盖哪些任务不能做。

核心完整性门槛普遍适用：错误目标、自动中断、误遮蔽系统隐私状态、覆盖用户新修改、无结果却报告成功，均阻断相应后端正式支持。不是只要给它贴 experimental 就可以在正式默认路径中执行。

## 9. 验收协议：沿用已有证据，修正范围判定

### 9.1 保留第三轮，不重写历史

既有 v0.1 协议有 24 个任务、50 个变体及真实 Linux 结果。此次没有补造 Mac 成绩，也不修改旧日志来配合新功能范围。[R3]

建议开发时建立协议 v0.2：沿用原始任务，新增声明能力与适用条件，给协议重新计算 hash。不能让没有像素功能的构建被要求伪造“曾获录屏权限再撤回”的前态；也不能把“没有捕捉器”填成“捕捉故障恢复通过”。

分三类判定：

1. 普遍必测：错误目标、输入保护、系统状态、用户修改优先、退出恢复、数据真实性。
2. 声明能力必测：例如精确代理、像素缓存、第三分区、预设。声明了或实际执行该功能，就必须满足对应任务。
3. 范围外未实现：明确列出排除，不增加通过数。缺硬件、缺权限或测试尚未做，仍是 blocked / not_run，不能改写成不适用。

已观察到的失败必须保留，无论后来是否取消该功能。完整测试套件覆盖与声明范围的放行结果继续分开输出。评估器只校验证据结构、绑定、时间、hash 和提交断言，不冒充独立 UI 重跑。

### 9.2 最小核心场景

| 场景 | 发布要求 |
|---|---|
| 同 App 三项＋重复标识＋动态标题 | 唯一时精确操作；歧义时绝不选第一项 |
| 重排、重启、PID 重用、宿主变化 | 旧绑定失效，不能继续执行旧坐标动作 |
| 真实刘海与长菜单造成目标不可见 | 从不可达到真实可操作的路径成立，静态列表不算 |
| 右键、Option、子菜单、动态数值 | 在声明路径保留原任务；代理与原位分开记录 |
| AX action 超时但菜单随后打开 | 不补发导致菜单反转或关闭 |
| 菜单保持期间有新展开／收起意图 | 旧会话不被后台任务中断 |
| 用户在临时布局中手动重排 | 当前用户排列保留，旧恢复放弃 |
| 外屏插拔、上下排列、混合缩放 | 不串屏、不用旧 frame；恢复及访问可解释 |
| AX 拒绝／撤回、库存不完整 | 不误点、不锁死恢复入口 |
| 时钟、通知中心、摄像头／麦克风状态 | 点击、快捷键、持续状态和来源提示无损害 |
| 正常退出、强制结束、卡死、重启 | 分别记录恢复结果，不能相互代替 |
| 配置部分写入、损坏和版本迁移 | 保留上一个有效配置，不整份静默重置 |
| 键盘、VoiceOver、减弱动态 | 本工具主流程完整可达；第三方交互保持基线能力；声明支持的纯键盘端到端路径无需鼠标 |
| 空闲、连续展开、睡眠唤醒后的资源 | 记录真实数据，识别持续扫描、内存增长和过量唤醒 |

Fixture 的三个项目是控制变量，还需要真实第三方 App 的标准菜单、自绘弹层、helper 进程、多 Item 与动态状态样本。每个样本先跑无管理器基线；基线不成立，不归咎于候选。

显示器与系统条件必须一致。Controller 打开窗口会改变前台 App 和左侧菜单占用；不能将基线的 Finder 与候选的其他长菜单应用混在一张结果表。新显示拓扑另建比较组。

### 9.3 Go / No-Go

进入正式 v1 至少要求：

- 声明目标系统的真实 Mac 构建、安装与核心任务通过；
- 主要目标刘海场景存在已验证的原项访问路径；
- 没有未处理的错误目标、系统状态损害、自动中断或覆盖用户修改；
- 降级有真实可用入口，未实现项不在默认 UI 暗示支持；
- 配置迁移、退出恢复、签名公证及更新链路在实际产物上验证；
- 性能记录与适用范围清楚，不以 Python 单元测试或 CI 编译代替。

少数目标动作不支持可以形成明确的兼容范围；但不能把主要目标人群的核心任务全部排除后，以“通过剩余小范围”宣称本项目的首版目标完成。

## 10. 开发顺序与可审查交付物

不按 UI 页面逐个铺功能。按风险与依赖推进：

| 阶段 | 工作 | 可审查交付物 | 进入下一步的条件 |
|---|---|---|---|
| M0：冻结范围与工程基线 | 使用本方案、确认首台 Mac 实际版本、固定工具链；编译已有验证包 | 构建日志、环境快照、固定依赖；无管理器基线 | 真实 Fixture 行为与日志成立 |
| M1：核心可达性验证 | 扩展 Fixture 制造真实超宽；做身份、E26-A/B、E27-A 和恢复入口 | 每条候选独立结果、录像或人工观察＋日志、能力表 | 至少一条目标路径完成主要 P0 访问；否则保持技术预览 |
| M2：最小垂直功能 | Core 模型、三个端口、协调器、两区入口、基本目录和原生访问 | 一条整理→查找→原菜单→保持→手动收起的真实流程 | 流程不靠固定时间假定结束，不点错目标 |
| M3：稳定与恢复 | 持久化、权限、拓扑、代次、用户修改优先、系统状态 | v0.2 协议结果、故障复现、配置迁移测试 | 核心阻断项清零，范围与实现一致 |
| M4：可用性与发行 | 键盘、VoiceOver、语言、资源定标、签名公证、更新、支持说明 | 可安装候选包、完整来源及 notices、回归记录 | 实际下载产物和升级保留配置 |
| M5：小范围试用 | 从现有需求者选择代表任务，记录一次完整使用和失败恢复 | 任务记录、反复手动修理次数、已知问题与优先级修订 | 决定是否发布 v1，或回到具体失败阶段 |

不在当前阶段给出确定周数：关键访问路径还未在 Mac 证明，后端差异足以改变工作量。每阶段以证据和可操作结果退出，比承诺一个缺乏依据的日期更有用。

M1 可以并行研究两种系统路径，但同一台测试机器一次只运行一个管理器。M2 的纯模型、配置与 UI 外壳可适度并行，不能在后端尚未证明时把大量界面连到假数据并算产品完成。

后续 P1 推荐顺序为：基本稳定 → 高级搜索／标签 → 手动预设 → 显示器关联 → 少量规则 → 可选像素 → 第三分区和更深外观。具体顺序应根据首批真实任务修订，不能仅凭展示效果决定。

## 11. 开源、维护与发行

自有源代码 MIT；引入 MIT 代码片段保留原版权与完整许可。Hidden 与 MenubarHide 可以作为对应固定版本的 MIT 参考；Ice 检查版本为 GPL-3.0-or-later，不直接复制实现再改标为 MIT。[G01][G02][G03][G04]

依赖通过锁文件固定。KeyboardShortcuts 的许可证保留；Sparkle 除主体 MIT 外还要保留其包含的外部组件 notices。建立 THIRD_PARTY_NOTICES 与依赖清单，发布包和源码保持一致。[D01][D03]

核心离线运行，不建立登录、订阅、云配置或远程图标识别服务。更新检查单独开关；不远程下发脚本或未审查的私有后端切换。发布签名密钥不进入 App 或源码。

公开可下载包与开发者本机构建区分。正式包采用 Developer ID、Hardened Runtime 和公证，并验证下载产物；公证不代表功能或权限使用已经获得 App Store 审核。[A14]

配置备份记录本工具意图，不扫描并整份回放所有其他 App 的偏好。上游 MenuBarArrangement 的相关实现说明了其他 App 自行持有状态项位置和创建时机这一复杂性，但本项目不将该写偏好路线纳入 v1。[G05]

免费发行仍有签名账户、构建、适配测试和问题响应等维护成本。第一版避免天气服务和云同步等持续服务依赖，可以把维护重点放在系统兼容与核心可靠性上。

## 12. 复盘：防止方案中的承诺越过证据

本轮已修正或明确的关键点：

- 7.1 已支持 Tahoe，不能继续照抄首页旧兼容文案。
- 第二栏不是跨进程 NSView 搬运；画出图标不等于打开原菜单。
- 标准 App 图标不等于动态状态，别名不等于稳定系统身份。
- public length 的布局效果仍依赖系统行为，不能称作稳定的全系统管理 API。
- 26 先测试不等于 26 已选定首发；临时槽位前置不成立时不能假定离屏投递有效。
- 原生 overflow 的存在不证明右键、Option 和状态完整。
- actor 不是跨 await 事务；Task.cancel 不是撤回外部动作。
- AX CannotComplete 不必然失败，不能自动重试。
- 没收到拖拽事件不证明用户没修改；应用层恢复检查不是系统原子 CAS。
- 不自动给未知项下隐藏意图，仍不能保证区间后端不会暂时挤走未知新项。
- 10 秒实验计时器不是产品菜单会话锁，正常退出清理不是崩溃恢复证据。
- 无像素构建不需要伪造录屏撤回场景；范围排除也不能抹掉实际失败。
- 私有断言不作为“几何不够就自动启用”的兜底。
- 当前方案、接口和伪代码均为设计；原有 35 项便携测试没有变成产品验收。

本轮没有留下需要用户先选择十几个技术选项才能继续的空白。可以直接按冻结的范围与技术栈启动 M0/M1；需要用实验决定的后端问题已经写成具体前置、步骤、失败条件和交付物。

## 13. 参考资料

引用于 2026-11-20 核查。产品页面会变化；源码结论绑定固定提交。设计规则、优先级、算法伪代码和预算目标属于本项目决定，不能反推为来源作者的承诺。

### 既有项目证据

- [R2] 第二轮功能、技术与复核报告。
- [R3] 第三轮验证包实际结果：35 项 Python 测试、16 个几何样本，Mac 编译／UI 未执行。

### 厂商、平台与依赖

- [S01] Bartender 6 产品页。
- [S02] Bartender 7 产品页。
- [S03] Bartender 7 更新记录，核对 7.1 / 7.2 与既往边界。
- [S04] Bartender Pro / Top Shelf。
- [A01] NSStatusItem。
- [A02] NSStatusItem.isVisible。
- [A03] AXUIElementPerformAction 的模态处理与超时说明。
- [A04] AXObserverAddNotification。
- [A05] NSStatusItem.expandedInterfaceDelegate。
- [A06] Swift 并发与挂起点。
- [A07] App Sandbox 限制。
- [A08] SMAppService。
- [A09] AXObserverGetRunLoopSource。
- [A10] NSScreen.safeAreaInsets / auxiliaryTopRightArea。
- [A11] ScreenCaptureKit。
- [A12] Apple WWDC：系统内容选择器的会话授权。
- [A13] AXUIElementSetMessagingTimeout。
- [A14] Notarizing macOS software before distribution。
- [D01] KeyboardShortcuts 官方仓库和许可证。
- [D02] Sparkle 官方集成说明。
- [D03] Sparkle 完整许可证与包含的组件 notices。
- [L01] MIT 许可证原文。

### 固定源码

- [G01] MenubarHide 几何模型：a4476bfe81a9a84ac94f8dfb273c4eaad8f9e960。
- [G02] Hidden 的 MIT 许可证：ee3af2475431540ddfa211b9e1e64b08a156f8f0。
- [G03] Hidden 原生显隐 shim，同一提交。
- [G04] Ice LICENSE：11edd39115f3f43a83ae114b5348df6a0e1741cf。
- [G05] MenubarHide MenuBarArrangement，同 G01 提交。

[R2]: feature-technical-review-r2.md
[R3]: ../../menubar-validation-lab/第三轮_验证启动与实际结果.md
[S01]: https://www.macbartender.com/Bartender6/
[S02]: https://www.macbartender.com/bartender7/
[S03]: https://www.macbartender.com/Bartender7/release_notes/
[S04]: https://www.macbartender.com/pro/
[A01]: https://developer.apple.com/documentation/appkit/nsstatusitem.md
[A02]: https://developer.apple.com/documentation/appkit/nsstatusitem/isvisible.md
[A03]: https://developer.apple.com/documentation/applicationservices/1462091-axuielementperformaction
[A04]: https://developer.apple.com/documentation/applicationservices/1462089-axobserveraddnotification
[A05]: https://developer.apple.com/documentation/appkit/nsstatusitem/expandedinterfacedelegate.md
[A06]: https://docs.swift.org/latest/documentation/the-swift-programming-language/concurrency/
[A07]: https://developer.apple.com/documentation/security/protecting-user-data-with-app-sandbox.md
[A08]: https://developer.apple.com/documentation/servicemanagement/smappservice.md
[A09]: https://developer.apple.com/documentation/applicationservices/1459139-axobservergetrunloopsource
[A10]: https://developer.apple.com/documentation/AppKit/NSScreen/auxiliaryTopRightArea-gr2n
[A11]: https://developer.apple.com/documentation/ScreenCaptureKit
[A12]: https://developer.apple.com/videos/play/wwdc2023/10053/
[A13]: https://developer.apple.com/documentation/applicationservices/1459345-axuielementsetmessagingtimeout
[A14]: https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution
[D01]: https://github.com/sindresorhus/KeyboardShortcuts
[D02]: https://sparkle-project.org/documentation/
[D03]: https://github.com/sparkle-project/Sparkle/blob/2.x/LICENSE
[L01]: https://opensource.org/license/mit
[G01]: https://github.com/junior-rj/menubar-hide/blob/a4476bfe81a9a84ac94f8dfb273c4eaad8f9e960/MenubarHide/CollapsedGeometry.swift
[G02]: https://github.com/consolelabs/hidden/blob/ee3af2475431540ddfa211b9e1e64b08a156f8f0/LICENSE
[G03]: https://github.com/consolelabs/hidden/blob/ee3af2475431540ddfa211b9e1e64b08a156f8f0/hidden/Features/StatusBar/Engine/Native/HBNativeVisibilityShim.m
[G04]: https://github.com/jordanbaird/Ice/blob/11edd39115f3f43a83ae114b5348df6a0e1741cf/LICENSE
[G05]: https://github.com/junior-rj/menubar-hide/blob/a4476bfe81a9a84ac94f8dfb273c4eaad8f9e960/MenubarHide/MenuBarArrangement.swift
