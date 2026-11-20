# Agent 开发小组工作约定

本文件是待采用的项目规则模板。导入正式仓库后，结合实际任务契约执行；本启动包尚未接入远端。

## 工作依据

先读任务卡、项目计划书、产品契约与相关 ADR，再进入指定工作区。以 task_id、任务版本、base SHA 和 write scope 为边界。对话用于讨论，Git、任务账本和验收记录承载持久事实。

在已授权范围内自主推进实现、修复、检查和提交，不为普通可逆步骤反复请求确认。遇到明确超范围变化，先完成范围内可审查工作，再说明具体待决事项。

## 独立实现

每个实现 attempt 使用唯一分支与独立 checkout。只能修改分配范围；需要共享接口、工程文件、依赖锁或 CI 变化时，提交精确变更需求，由所有者串行处理或取得新的范围版本。

不要直接写 main，不强推主干，不删除别人的工作树。worktree 与 clone 都不是系统权限沙盒；不要修改全局工具配置来绕过本任务边界。

## 子 Agent

只读探索和日志分析可按已配置额度派发。所有子 Agent 计入父预算与全局活动会话上限。创建前取得空闲槽位，不能占满父会话后一起等待子任务。

需要写代码的子 Agent 升级为协调板可见子任务，使用独立 scope、分支和工作区。独立 reviewer 由协调者创建，不能只用作者自己的子 Agent 完成审查。

## 交付与检查

输出 WorkerResult，附实际提交、改动路径、执行环境、原始检查输出和仍未解决的问题。未执行标 not_run，结果无法确定标 unknown，不用退出码或文字宣称代替行为证据。

你只能声明 submitted / blocked / failed / cancelled。accepted 由独立验收和协调流程决定。研究允许交付负面结论；生产路线是否可用另看 capability verdict。

Mac 原生行为必须在登记的真实 Mac 条件下验收。按主机取得 GUI 排他租约；不同分支不能同时驱动同一菜单栏。

## 合并

审查绑定 base/head/contract；候选绑定最新基线与 candidate SHA。任何新提交或影响相关行为的基线改变，都重新判断旧证据是否有效。集成者改过代码后仍需独立审查。

合并请求接受或入队不等于合并成功。由受控集成入口读回实际 merge commit、tree、parents，再更新任务。

## 停止和恢复

断连、超时、取消请求、租约过期都不等于进程已停止。只管理本任务拥有的 session／进程组，保留阶段产物。无法确认 GUI 停止时将主机隔离等待恢复，不能让下一位 Agent 接手点击。

## 产品边界

保持免费官方发行与自有代码 MIT。首版按 F01—F12 与 M0—M5 执行。私有显隐、像素镜像、规则和 Pro 工具集不偷偷进入默认路径。目标不明确、状态未知、用户修改或系统完整性风险出现时，遵守产品契约的保守行为。

文档使用自然、清楚的中文；报告先写结果、证据和实际限制，避免重复进度口号。

## 文件与机读依据

任务卡使用 TaskSpec 投影和 scope_paths；RunManifest/WorkerResult/ReviewVerdict/IntegrationReceipt/GateDecision 使用 contracts 中的同名 Schema。模板不构成已执行收据。任务状态 accepted 与产品门槛分别记录；unknown 门槛不得放行。

修改源 JSON 或 coordination/document-templates 后运行 python3 tools/render_docs.py，再以 --check 验证。生成文档不单独人工维护。范围所有权见 coordination/path-ownership.json；所有权提示不会自动扩大本次 run 的 scope_paths。根 Package.swift 与 XcodeGen project.yml 由集成者串行修改，生成 pbxproj 不手改。
