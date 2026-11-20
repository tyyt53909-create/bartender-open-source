# Menu Bar Validation Lab · v0.1

这是“调酒师开源免费版”项目的第一份后端验证包，用同一组任务检查候选方案的菜单可达性、交互语义、系统状态和恢复行为。它目前是研究用源码与记录工具，还不是可正式使用的菜单栏管理器。

**当前真实状态：Linux 中完成便携检查；Mac 编译与运行均未执行。24 个任务、50 个覆盖变体全部保留 not_run。** 完整实际结果见 results/ 下的报告，不能把 Python 测试通过当作 macOS 功能通过。

## 包内有什么

| 组件 | 本版做什么 | 本版没有证明什么 |
|---|---|---|
| Fixture | 同一 App 产生三个可区分的状态项；Beta 每秒更新数字；记录原生菜单、右键、Option、子菜单和自身状态 | 尚未在 Mac 编译；系统托管层是否保留 AX 身份和输入归因，需要基线 |
| Controller | 手动几何收起、5 秒后触发、10 秒后请求展开；常规窗口提供恢复入口 | 没有 Item 搜索、自动排序、三分区、转发点击、规则引擎或菜单会话锁 |
| Observer | 只读观察屏幕几何和本 Fixture 的 AX 属性、声明动作、frame | 不读取所有 App；AX 空结果不证明图标不存在；没有完成系统宿主进程发现 |
| PrivateProbe | 动态加载目标私有框架并检查指定类与 selector 是否存在 | 不创建或激活显隐 assertion；存在性不证明行为、签名或稳定性 |
| protocol / evaluator | 24 个任务、50 个变体；将原始观察、人工确认和提交证据校验区分开 | 不会自动操作 Mac UI，也不会重新执行外部 verifier |
| backend-analysis | 固定上游源码、MIT notices、16 个几何样本和算术结果 | 模型条件满足或失败，均不等于 Mac 实测结论 |

Controller 的策略名是 guarded_candidate。27 上的多占位方案来自固定的 MenubarHide 几何计算，加入了缺数据、容量不足、阈值与 64 pt 余量检查；不能把本版结果署名为“未经修改的 MenubarHide”。源提交和原文 hash 见 backend-analysis/source-manifest.json。

## 在 Mac 开始：先基线，再候选

需要 macOS 14+ 与 Apple 开发工具；**几何收起实验仅开放 macOS 26 / 27**。其他版本可以尝试构建并做只读观察，不能据此声称收起兼容。不要为了运行实验升级或降级系统。

在解压目录中执行：

~~~bash
python3 tools/preflight.py --output runs/local-preflight.json
bash scripts/build-macos.sh
open build/Fixture.app
~~~

preflight 只读软件环境；它成功也不代表编译成功。构建脚本只生成本机架构产物，不自动运行、不签名公证、不安装登录项。build 目录里应得到 Fixture.app、Controller.app、observer 和 private-probe。原始构建输出必须保留；如果编译失败，先记为 build failure，修复后固定新源码版本再继续。

**此时先不要开启 Controller。** 正常停用已有菜单栏管理器，在 Fixture 上确认 FA、B 000、FC 各自菜单可达，分别做左键、右键、Option 和子菜单操作，再检查计数变化。菜单打开期间的计数是否更新，也要由基线实际证明。Fixture 的 New run / reset 可重开日志，Export JSONL 导出当时快照。

将 protocol/results-template.json 复制到新的 runs/baseline/results.json，按 protocol/RUNBOOK.zh-CN.md 填写真实环境和证据。每个新实验组使用新的目录，不覆盖本包记录的当前 Linux 结果。

基线建立后再启动候选：

~~~bash
open build/Controller.app
~~~

1. 点击“显示定位标记”。用 Command 拖动，把 0–6 连续放在待测图标右侧、LAB 左侧；先记录最终排列。创建顺序不能保证菜单栏的显示顺序。
2. 点击“收起 10 秒”。26 使用一个 10000 pt 占位项；27 使用带拒绝保护的多项模型。界面给出“已赋予宽度”只代表命令执行到了该步，不证明屏幕上的项目已成功收起。
3. 对模型允许的实验，逐项观察能否到达正确菜单、继续操作、保留右键与 Option 的语义。模型拒绝必须记录为拒绝／受限，不能计为隐藏功能通过。
4. 如需观察菜单使用中遇到新动作，点击“5 秒后收起”，隐藏 Controller 窗口，再打开 Fixture 菜单。它只注入一次定时触发，没有实现规则仲裁。到期展开若关闭了正在使用的菜单，按失败事实记录。
5. 使用窗口“立即展开”撤回本程序的占位宽度。重新执行 open build/Controller.app 可找回窗口；Controller 前台时 Command+Shift+R 是本地恢复快捷键，不是全局救援热键。

Controller 打开窗口会变成前台 App；隐藏窗口不会自动恢复之前的前台应用。对照时应手动保持相同的前台 App 与左侧菜单占用，并记录 Controller 自有占位项及 LAB 图标带来的额外布局条件。

10 秒是主线程定时器的计划时间，**不是卡死或崩溃后的恢复保证**。屏幕变化、休眠或会话退出会请求展开；这些通知能否及时到达、系统是否完成布局、菜单是否被打断都仍待测试。程序不自动重排其他应用，也不把旧顺序覆盖回去；这不等于已经验证了“恢复时尊重用户修改”的产品能力。

## 观察与证据

可用命令行观察器生成一个只读快照：

~~~bash
mkdir -p runs/observations
build/observer > runs/observations/observer.json
build/private-probe > runs/observations/private-probe.json
~~~

Observer 不主动弹出辅助功能授权请求。权限不足会记录 permission_missing；是否授权，由操作者在系统设置中正常处理。Controller 和命令行 Observer 是不同进程，不能假定两者授权相同。这里没有读取或修改 TCC 数据库，也没有请求录屏权限。

AX 观察限制在 Fixture bundle，并限制节点数量、逐对象消息超时和总查询预算；该预算仍是尽力而为，不能当作硬性实时保证。它不会执行 AXPress，也不会验证菜单栏中未知第三方项目的身份。

Controller 的“展开后导出快照”会先请求展开，保存的是该状态的观察，不是收起状态截图。若要留收起期间观察，应在实验记录中标明使用独立 Observer 的时间与 Controller run ID，并记录终端操作可能带来的焦点影响。

Fixture 和 Controller 的 JSONL 默认保存在各自的 Application Support/MenuBarValidationLab 子目录，均有约 8 MiB/run 上限。Fixture 控制窗口可导出或定位文件；Controller 提供“查看日志”。应用没有联网、桌面录屏、摄像头或麦克风采集。

时钟、通知中心、摄像头和麦克风必须按协议观察真实系统功能，不能用 Fixture 的普通图标代替。操作者手动启用自己选择的音视频应用，仅记录系统指示与交互结果，不需要保存音视频内容。

完整填写方式、证据 hash、匿名机器标识与同条件基线见 protocol/RUNBOOK.zh-CN.md。每个 passed 都要有具体任务观察，不能仅引用 activation 或 menuOpened。

~~~bash
python3 tools/evaluate_results.py runs/candidate/results.json \
  --baseline runs/baseline/results.json \
  --output runs/candidate/evaluation.json
~~~

评估器只校验提交记录的结构、归属、时间和文件 hash；输出的 passed 是被提交证据支持的声明范围结论，不是独立的 UI 重跑认证。unsupported 不算完整覆盖。错误目标、交互被打断、系统状态误遮蔽和覆盖用户改动必须保留为阻断失败。

## Linux 或 Mac 上可以重跑的便携检查

~~~bash
bash scripts/run-portable-checks.sh
python3 backend-analysis/geometry_verify.py --output results/recomputed-geometry.json
python3 tools/evaluate_results.py protocol/results-template.json \
  --output results/template-evaluation.json
~~~

最后一条对未执行模板预期退出 2，表示环境／覆盖不足。不要为了让 shell “变绿”而把模板改成通过。Linux 调用 build-macos.sh 预期退出 78，不会尝试编译 AppKit。

16 个样本使用逻辑点 pt。以 1512 pt 屏宽、663.5 pt 刘海右侧区域加 3440 pt 逻辑宽外屏为例，模型每项 433 pt，7 项最多 3031 pt，低于自身覆盖目标 409 pt。本版因此拒绝实验；这不是实际 Mac 已出现图标泄漏的报告，也不能把外屏硬件像素数直接填成逻辑点。

## 当前能力边界

这份包把比较任务、合成观测靶、几何实验入口和记录判定连起来了，尚未完成候选后端的全面 A/B。特别是：

- 私有路线只交付只读探针，显隐行为没有启用。
- 真机编译、AX 暴露、原菜单交互、系统隐私状态、多屏切换、故障恢复与性能均待执行。
- 没有 Item 搜索、规则仲裁、三分区和代理点击，因此这些能力不能从该原型放行。
- 只读源码复核已纠正编译桥接与控制次序问题；没有 Apple SDK，仍不能保证第一次 Mac 构建成功。

把整个目录交给本机 Codex 时，可使用 LOCAL_CODEX_TASK.md 作为具体任务书。优先产出一份可复现的无管理器基线和当前系统的单候选记录，再决定下一步是否值得实现完整后端。

## 许可证与原始依据

本包新增代码使用 MIT，见 LICENSE；第三方源码与衍生几何逻辑保留原版权通知，见 THIRD_PARTY_NOTICES.md。本包没有包含 Bartender 专有二进制或代码，也没有将 GPL 项目代码重新标为 MIT。

Apple 接口依据：

- [NSStatusItem.length](https://developer.apple.com/documentation/appkit/nsstatusitem/length)：设置本状态项占用宽度；不保证管理其他 App 的隐藏效果。
- [NSScreen.auxiliaryTopRightArea](https://developer.apple.com/documentation/AppKit/NSScreen/auxiliaryTopRightArea-gr2n)：刘海右侧区域观察。
- [AXUIElementSetMessagingTimeout](https://developer.apple.com/documentation/applicationservices/1459345-axuielementsetmessagingtimeout)：超时设置只针对该 AX 对象，不能从应用元素自动推定所有子元素同样受限。

