# 外部交叉审查复核与 v0.2 修订记录

日期：2026-11-20。对象：4 份 v0.1 Markdown、原始启动包及其展开后的 JSON/Python、历史基线和 Lab 源文件。外部意见来自用户转交的 Gemini4Neon 交叉验证，其说明只读过 ZIP 清单与大小。本轮展开了实际源码，不以那份审查的假设代替文件证据。

## 结论

审查指出的大部分不一致成立，其中 M0 门槛遗漏、QA 写范围、实际路径与任务声明脱节，都会影响后续派工正确性。v0.2 已在任务源数据、契约、生成器和回归检查中修正。工作分解由 32 张扩为 34 张：新增 APP-25 承接生产无障碍／本地化实现，新增 APP-26 承接 M3 汇总裁决。

有一项需要收窄：原包的 Gate 并非只有字符串。v0.1 tasks.json 已有 all_of / any_of，validate_plan.py 也会把其中 task_accepted 引用纳入保守环检查。实际缺口是文档未充分呈现条件关系、没有求值器，以及 OPS-07 缺明确的自动调度启用消费关系。不能把“没有直接下游 depends_on”一概认定为“完全未入图”。

本轮关闭的是规划材料和离线工具的缺陷。任务仍全部 planned；真实 Mac、CLI/provider 接入、远端分支保护与合并、签名发行尚未执行。

## 原包的可核实依据

原始 ZIP SHA-256：`a86c37c6db0e0e4e801dfc25be5c5e5afea59e8af5cc7152b073a71db1937023`。ZIP 含 35 个文件，其 MANIFEST 中列出的文件字节数和摘要均与原文件一致。本轮没有修改这份旧 ZIP。

核对范围包括全部任务卡、6 类拟议／已有契约关系、角色注册表、scope、模板、生成脚本、波次、需求映射、Gate 表达式及原始 Lab 清单。复核时还比较了新的任务书、计划和协调板是否由相同输入生成。

## 逐项裁定及修订

| 编号 | 外部发现 | 裁定与已采取的修订 |
|---|---|---|
| A01 | APP-12/13 缺 M0 | 成立。两卡增加 M0_BASELINE_VERIFIED；APP-02 完整失败研究 accepted 仍不能放行。离线用例专门检查此情形。 |
| A02 | 六张卡在 depends_on 图中悬空，Gate 未结构化 | 部分成立。原 JSON 结构与环检测已覆盖候选分支；新版保留条件树、增加三值求值与依赖视图。OPS-07 的输出由 automation_runtime_ready 消费；未给 bootstrap 人为增加循环依赖。 |
| A03 | APP-04..07 带 APP-02 专属说明 | 成立。通用 research_evidence_policy 与单卡 research_task_note 分开，M0 构建失败说明仅留在 APP-02。 |
| A04 | APP-22 同时验收和改生产 UI，漏权限页 | 成立。APP-22 只写验收代码、结果和缺陷；新增 APP-25 UI 实现，依赖 APP-13/14/18。APP-22 显式依赖 APP-18/25，覆盖权限设置页。 |
| A05 | OPS-03/05/06 误归 macOS Platform | 成立。改归 integrator，角色文件与注册表同步加入工作区、CLI 适配器和工具链职责。 |
| A06 | OPS-01/02/04/07 路径错位 | 成立，且原包更广泛地缺持续维护归属。保留平铺 JSON，按真实文件重写 scope，增加 path-ownership.json 区分源文件、生成物和历史资料。既有源文件必须存在且被任务范围覆盖。 |
| A07 | phase/wave 混用，OPS-06/07 未排入表 | 成立。卡片分开 phase 与 wave；波次表从任务目录生成。OPS-06/07 明确列入 W2，前者仍可选，后者在实际首执行器验证后验收。 |
| A08 | B1/B2 私有链接不可移植 | 成立。归档两份基线及其 R2/R3/Lab 引用，改为仓库相对路径。provenance 同时保留原 SHA 和迁移后 SHA；本轮只改导航，不改历史结论。 |
| A09 | APP-17/18 编码占 GUI 独占资源 | 成立。实现资源改 macos_build；Mac 构建与 GUI 验收按阶段申请。all_of 表示都需验证，不表示全程同时持有资源。 |
| A10 | 共享 pbxproj/Package.swift 易成瓶颈 | 接受。路线固定为根 SwiftPM 清单 + XcodeGen，普通已定义 target 内的文件由目录发现；新增 target、依赖和构建选项仍串行处理。生成 pbxproj 不手改。 |
| A11 | 缺结构化审查和裁决契约 | 成立。增加 ReviewVerdict、RunManifest、IntegrationReceipt、GateDecision，连同 TaskSpec/WorkerResult 共六类严格 Schema。Markdown 是人读视图，不用于解析状态迁移。 |
| A12 | M0/M3 签发归属不清 | 成立。M0 归 APP-02 的独立验收，M1 产品门槛归 APP-08，M3 新增 APP-26 汇总。issuer 角色、来源任务和当前绑定写入 gate_policies；自报 reviewer 不构成权威。 |
| A13 | APP-14 未映射 F01 | 成立。增加 F01，并补手动整理与实际反馈的验收标准，非只改表格。 |
| A14 | APP-07 的 M1 验收不对称 | 成立。补输入和恢复完整性、同条件证据、跨 OS 不借成绩，并补 F06/F07 映射。 |
| A15 | Reviewer 的 Grok / Astra 展示不一致 | 成立。APP-08/26 首选 grok4.7，回退 gpt6.2astra；角色、计划、任务和看板同源展示，实际 route 仍 unresolved。 |
| A16 | TaskSpec/TaskContract、WorkerResult/RunnerResult 混用 | 成立。统一六类名称，修掉实际任务验收文本中的旧名；scope_paths 是唯一任务写范围字段。 |
| A17 | 任务书声称生成却没有随包生成器 | 成立。v0.1 的 task-book 生成脚本存在于研究工作区，未进入 ZIP。新版打包 render_docs.py 与兼容入口，五份视图统一生成，--check 拒绝漂移。 |
| A18 | Python 与未来 TypeScript 边界不清 | 接受。Python 编译和验证离线规划；TypeScript/Node.js/SQLite 才是拟实现的在线协调服务。两者共用契约与语义用例，Python 不持有 live 状态写入权。 |

## 源码复核追加发现的接缝

实际路径检查发现，原 35 个文件只有 AGENTS.md 命中某张原任务卡的 scope_paths。这不表示所有文件都应立刻被修改，而是说明未给维护动作安排完整归属。新版没有把所有 OPS 扩成整个仓库写权限；对已有脚本、配置、文档源、生成物与历史输入分别登记。

Lab 原清单列出的 53 个文件全部匹配字节和 SHA-256，连同原清单自身共 54 个历史文件纳入新包，排除运行缓存。第三轮报告已在 Lab 中，不再重复复制。链接检查还纠正了 Lab 入口实际叫 README.zh-CN.md 的路径细节。

SwiftPM 工程布局另有约束：原任务目录使用顶层 Tests，却还列出嵌套 Packages/MenuBarCore/Package.swift。新版采用根 manifest 映射当前目录，取消嵌套包根假设，避免 target.path 试图越出包根。官方依据与工程判断见 [构建布局 ADR](adr/build-layout.md)。

OPS-03 继续在 Linux 验收工作区和生成规则，实际 XcodeGen 版本固定、干净工程生成、目标图、资源与 Mac 构建归 APP-13。这样未取得 Mac 时仍可实现 CLI 适配器；不能把规范检查写成 Mac 生成通过。

M3 汇总涉及多位作者。只比较 APP-26 最后一份报告的作者还不够。新版要求 context manifest 与可信账本提供 APP-18/19/20/21 的 subject_bindings，并逐项检查当前 spec/head/作者集合。汇总作者、审查者、签发者都要独立于原始作者子树；缺失、过期或来源不符不得通过。完整作者集合与信任根仍由真实协调服务提供，离线 JSON 不能自行建立身份可信性。

APP-25 在 W4 可能改动 W3 已验过的界面。APP-23/25/26 已明确：候选改变后，重新生成 APP-26 attempt，重跑受影响 M3 验证，或给出独立签署的未受影响证据复用理由，再签发最新 candidate/scope/context 的裁决。历史 gate 不能直接放行新发行候选。

## 本轮验证方式与证据

准确测试数量、执行状态与命令结果记录在 [离线检查结果](check-results.json)；完整 unittest 输出在 [检查日志](validation/unit-tests.log)。检查包含严格 Schema、缺证据关闭、错误／过期／跨环境绑定、独立性、候选变化、模板不可当收据、条件依赖、任务写范围和同源文档。

`render_docs.py --check` 检查实际交付文档是否与源数据一致；`validate_plan.py` 检查现有路径归属、角色、规范摘要、需求映射、条件图、历史文件摘要和本地链接；`package_starter.py --verify` 对 ZIP 成员集合和每个成员的摘要再次核验。最终归档还在新的临时目录展开并重新执行离线命令，避免依赖研究工作区之外的脚本。

所有测试样例明确为 synthetic，不计入项目 accepted 数。它们验证的是规则与拒绝逻辑。当前尚未执行真实 runner/provider 调用、在线调度／租约与断连演练、XcodeGen 或产品 Mac 构建、菜单栏 GUI 验收、远端合并保护、签名公证或正式发布。产品最关键的候选路线可行性仍必须由 M0/M1 实验回答。

## 文件维护入口

以后修改任务时编辑 coordination/tasks.json，规范摘要按 task_spec_fields 重新计算；计划和架构的叙述源在 coordination/document-templates/。运行 tools/render_docs.py 更新生成文档，执行离线检查，再由 tools/package_starter.py 封装。构建和真实执行仍按各自任务卡进入独立工作区，不能因文档修订完成而把工程卡改成 accepted。
