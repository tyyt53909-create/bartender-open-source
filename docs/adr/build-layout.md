# ADR：根 SwiftPM 清单与 XcodeGen 工程生成

状态：本轮确定的工程路线；OPS-03 定义隔离与生成规则，APP-01 定义模块契约；精确工具链版本、实际工程生成与 Mac 编译由 APP-13 验证。

## 决策及理由

根 `Package.swift` 描述 Swift target 图，用显式 target.path 映射现有 `Packages/...` 和顶层 `Tests/...`。不同时维护 `Packages/MenuBarCore/Package.swift` 作为第二个包根。SwiftPM 的 target 路径必须留在包根内；根包可以包含这些目录，嵌套包不能用 `../../Tests` 绕出去。[S1]

App 壳由 `Apps/MenuBarApp/project.yml` 定义，固定版本的 XcodeGen 根据目录、target、资源、scheme 和配置生成工程，并引用本地根 Swift 包。生成的 `project.pbxproj` 不手工维护；每个工作区独立生成，不作为并行修改的源文件权威。[S2][S3]

已定义 target 下增加普通源文件，使用目录发现；它减少逐文件登记产生的冲突。新增 target、依赖、资源规则、编译条件或测试入口仍会改变构建图，因此 `Package.swift`、`Package.resolved`、`project.yml` 和 `Config/` 由 integrator 按准确变更请求串行处理。XcodeGen 并不消除这些真正的语义冲突。

## 布局与资源约定

| 路径 | 用途 | 写入归属 |
|---|---|---|
| 根 Package.swift | 平台／纯逻辑模块及测试 target 的唯一清单 | OPS-03 引入，integrator 串行维护 |
| Packages/MenuBarCore/ 等 | 已定义 target 的源文件 | 对应模块任务 |
| Tests/ | 根包显式映射的测试 target | 对应实现或验收任务 |
| Apps/MenuBarApp/project.yml | App 壳、资源、配置和本地包引用 | integrator |
| Config/ | xcconfig 等共享构建设置 | integrator |
| 生成的 xcodeproj、DerivedData、可写缓存 | 每个 attempt 的构建中间产物 | 单一工作区，不共享并发写入 |

这些产品工程目录仍是规划位置；本包没有伪造可编译的 App 清单。APP-13 必须记录精确 XcodeGen 版本及获取校验、Xcode build、Swift、SDK、主机系统和目标最低系统。`minimumXcodeGenVersion` 只声明下限，不能替代版本锁。[S3]

Linux 只运行经过实际验证的 portable target/test 图。根包存在平台模块时，不能因为用了 SwiftPM 就假设任意 `swift test` 均能在 Linux 成功；APP-01 必须确定可执行命令及平台条件。AppKit 与真实交互继续在 Mac 上验证。

构建和 GUI 是两个资源阶段；普通编码和编译不持有 GUI 租约。GUI 时序或资源测量期间暂停同机干扰性构建。所有动作都绑定实际 source SHA、环境和构建输出，目录生成成功不是产品行为通过。

## 验收与后续变化

新 checkout 由固定入口生成工程，并验证目标图、资源与构建。普通文件增删不应引入手写 pbxproj 补丁；新增模块则通过一次明确的共享清单更新完成。若实际目标 Xcode 需要文件系统同步文件夹，在同一生成器配置中评估，不另立手工工程权威。

本 ADR 选定路线，不填写未经验证的工具版本，不记录不存在的 Mac 构建成绩。

[S1]: https://docs.swift.org/package-manager/PackageDescription/PackageDescription.html
[S2]: https://github.com/yonaskolb/XcodeGen
[S3]: https://github.com/yonaskolb/XcodeGen/blob/master/Docs/ProjectSpec.md
