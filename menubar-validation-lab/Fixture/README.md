# Menu Bar Fixture

这是菜单栏管理器对照实验的**观测靶应用**，不是候选管理后端。它只创建自己的三个状态项，记录自己收到的事件和自己的布局。源码采用本验证包的 MIT 许可证。

当前交付状态：已做 Linux 环境下的 shell 语法、Info.plist 和边界静态检查；**没有 Apple SDK，因此尚未编译、运行或验证 macOS 行为**。外部 AX 是否看得到标识、事件是否穿过 macOS 27 的托管层、菜单展开期间定时器是否持续触发，都要先在 Mac 基线验证，不能据源码直接判定成功。

## 在 Mac 构建和运行

要求 macOS 14 或更高，以及 Xcode / Apple Command Line Tools。以下命令从验证包根目录执行：

~~~bash
bash Fixture/build.sh
open build/Fixture.app
~~~

构建只产生本机架构的应用，默认产物是 build/Fixture.app。可以通过 FIXTURE_BUILD_DIR 指定另一个输出目录。构建脚本不签名、不公证、不自动启动、不配置登录项。非 macOS 主机会退出 78，并明确表示没有尝试编译。

应用的 bundle ID 固定为 org.menuvalidation.Fixture。退出按钮只退出本应用，退出时移除自己的状态项。若状态项被测试管理器收起，可以重新执行 open build/Fixture.app 打开控制窗口，再暂停或退出。

## 三个可区分的 Item

| 逻辑 Item | 可见标题 | 设置的 AX identifier | 稳定 label |
|---|---|---|---|
| alpha | FA | org.menuvalidation.fixture.alpha | Fixture Alpha |
| beta | B 000，数字每秒变化 | org.menuvalidation.fixture.beta | Fixture Beta |
| gamma | FC | org.menuvalidation.fixture.gamma | Fixture Gamma |

三个 Item 来自同一个 App，用于揭露“按 bundle 找到首个图标，就误以为找到了指定 Item”的问题。各 Item 使用固定 autosave name，Beta 用固定宽度和等宽数字，避免数字变化本身无意改变布局。

这些是**应用设置的身份**，不是对外部 AX 库存的承诺。先由 Controller 的观察器确认目标系统是否实际暴露它们；如果没有，要记作识别能力缺口。

每个 Item 均可打开自己的原生 NSMenu。直接左键、右键、Option+左键和 Option+右键各生成可辨认的菜单标题及 variant。菜单包含 primary action 与一个 submenu action。菜单中没有自动关闭计时器；让它保持打开至少五秒，用于观察管理器是否提前恢复布局。

应用使用近期、属于自己按钮窗口的 NSEvent 归因。如果 AXPress 或系统托管路径没有提供可归因的指针事件，variant 记为 unknown，并显示默认菜单。不能把 unknown 转成“右键或 Option 已通过”。

## 控制窗口

- **Pause / Resume counter**：只暂停或恢复 Beta 动态数值，不改变菜单或任何其他应用。
- **New run / reset**：结束旧 run，新建 UUID 和日志文件，把计数重置为零；不删除旧日志，不修改菜单栏顺序。
- **Snapshot layout**：记录自己的按钮 frame、窗口编号、可见属性以及屏幕几何。
- **Export JSONL**：导出点击时刻的日志快照；保存面板选择位置后写入，后续发生的事件不包含在这份快照内。
- **Reveal log**：在 Finder 中显示当前日志。
- **Hide controls**：交互实验开始前隐藏控制窗口，避免它占用焦点。
- **Quit fixture**：正常终止本应用。

控制窗口只在手动启动、重新打开或选择菜单中的控制入口时激活。计时器不会自动弹出窗口。状态项和控制窗口都会改变当前屏幕的测试条件，应在无管理器基线和候选条件中保持一致。

## 计时器和菜单保持

Counter Timer 显式加入 common 和 eventTracking run-loop modes，设计上希望在 NSMenu tracking 时继续更新。但这不是已测结果。

实际证据应同时满足：

1. menuOpened / menuClosed 的 session 对应正确 Item；
2. 这个时间区间内有 Beta 的 stateChanged；
3. stateChanged.details.activeMenuSessions 包含正在打开的 session；
4. 用户观察到状态、点击目标和菜单保持符合任务要求。

NSMenu 回调只证明本应用观察到打开/关闭，不会说明是谁关闭菜单。用户按 Esc、点外部、选择动作和管理器错误恢复都可能造成关闭，因此仍需要操作记录。缺少日志、计时器停顿或错误写入，都不能算通过。

## JSONL 接口

每条事件含以下公共字段：

~~~json
{
  "schemaVersion": 1,
  "sequence": 1,
  "event": "activation",
  "timestamp": "2026-11-20T00:00:00.000Z",
  "monotonicSeconds": 1234.5,
  "fixtureRunID": "illustrative-run-id",
  "bundleID": "org.menuvalidation.Fixture",
  "itemID": "beta",
  "sessionID": "illustrative-session-id",
  "details": {
    "variant": "option",
    "eventAttribution": "recent_own_pointer_event"
  }
}
~~~

上面的 JSON 是格式示例，不是本轮实测数据。itemID 与 sessionID 仅在适用时出现。跨进程关联优先使用同一 Mac 的 monotonicSeconds，并同时记录 Fixture 和 Controller run ID；不同 Mac 或重启后的 monotonic clock 不可直接混用。

| event | 关键 details |
|---|---|
| fixtureStarted | OS、PID、已创建 Item ID、计数周期 |
| activation | variant：left / right / option / right+option / unknown；归因依据 |
| menuOpened / submenuOpened | variant、depth、counter |
| menuClosed / submenuClosed | variant、depth、counter、可计算时的 openDurationSeconds |
| actionSelected | commandID：primary / submenu；variant |
| menuTrackingReturned | itemSelected；不用于推断任何第三方动作是否成功 |
| stateChanged | Beta counter、visibleTitle、当时 activeMenuSessions |
| counterPausedChanged | paused、counter |
| scrollObserved | deltaX / deltaY、phase；仅属于自己状态按钮的本地事件 |
| layoutObserved | 自有按钮 frame、屏幕几何、原因 |
| fixtureActivated / fixtureDeactivated | 本应用活跃状态发生变化；不记录前台的其他应用身份 |
| fixtureWakeObserved | 本应用观察到唤醒 |
| loggingStopped | 日志大小上限；之后观测不可用 |
| fixtureRunEnded / fixtureStopping | 手动重置或退出 |

frameAppKit 使用 AppKit 全局坐标与 point 单位，不能直接当成 AX / CG 的左上原点坐标。statusItemIsVisible 和本地窗口 frame 均不证明用户真实看得见该项目。27 的系统托管可能不给本进程完整 presentation，这应记录为 no_local_button_window。

Scroll 使用**本地**事件监视器，不改变事件、不使用全局监听。系统是否把状态项滚轮事件交付给本应用，需要基线验证；没有收到事件不证明候选管理器丢弃了它。

## 日志范围与完整性

日志默认位于本用户 Application Support 下的：

MenuBarValidationLab/Fixture/fixture-<runID>.jsonl

每个 run 最大约 8 MiB，达到上限后追加 loggingStopped 并停止记录，控制窗口显示该 run 不完整。手动建立新 run 后才继续。旧 run 不自动删除；操作者可通过 Reveal log 自行清理。

本应用不录屏、不读剪贴板、不扫描其他应用、不请求麦克风或摄像头、不联网、不发送合成输入、不修改系统设置或其他 App 的偏好。它也不检查权限弹窗或以空缺数据充当成功。摄像头、麦克风、时钟和通知中心场景应按总测试协议由操作者操作真实系统功能，不能用本 fixture 冒充系统状态指示。

## 官方接口依据

- [NSStatusItem](https://developer.apple.com/documentation/appkit/nsstatusitem)
- [NSMenu.popUp(positioning:at:in:)](https://developer.apple.com/documentation/appkit/nsmenu/popup(positioning:at:in:))
- [NSAccessibilityProtocol](https://developer.apple.com/documentation/appkit/nsaccessibilityprotocol)
- [NSStatusItem.isVisible 的溢出边界](https://developer.apple.com/documentation/appkit/nsstatusitem/isvisible)

运行之前必须先通过实际 Mac 的构建和无管理器基线；本文件没有预填任何兼容性通过结果。

