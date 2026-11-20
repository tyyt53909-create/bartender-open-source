# Menu Bar Agent Starter v0.2

“调酒师开源版”的项目计划与多 Agent 协作启动材料。本版经外部交叉审查后展开原始 JSON/Python 修订，包含 34 张任务卡、8 个逻辑角色、6 类机读契约、条件门槛参考求值、同源文档生成及可移植历史实验材料。

当前所有工程任务仍为 planned，未接入远端执行主机或实际模型路由，也没有真实 PR、Mac 构建和 GUI 验收成绩。本包的检查只证明离线结构、字节与规则一致。

## 阅读顺序

1. [审查修订记录](docs/audit-v0.2.md)：哪些发现成立、哪些需纠正，修订与验证证据。
2. [项目计划](docs/project-plan.md) 与 [小组架构](docs/agent-team-architecture.md)：产品范围、岗位与执行规则。
3. [任务书](docs/task-book.md)、[协调板](docs/coordination-board.md)、[条件依赖图](docs/dependency-map.md)。
4. [机读契约](contracts/README.md)、[门槛求值](docs/gate-evaluation.md)、[构建布局 ADR](docs/adr/build-layout.md)。
5. [历史基线](docs/baselines/README.md) 与 [实验源码入口](menubar-validation-lab/README.zh-CN.md)。

## 离线复查

需要 Python 3.10+ 与 tools/requirements.txt 固定的 jsonschema。首次配置可在独立环境安装依赖；以下检查本身不使用网络：

```bash
python3 -m pip install -r tools/requirements.txt
python3 tools/validate_plan.py
python3 tools/render_docs.py --check
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tools/gate_eval.py --gate M0_BASELINE_VERIFIED
```

最后一条在没有运行快照时应返回 unknown，退出码 3，表示不能放行。不能把这个预期关闭结果记为产品失败，也不能将其改成通过。

修改 tasks.json 或 document-templates 后运行 python3 tools/render_docs.py；计划与架构的动态表格、全部任务卡、协调板和依赖视图一起更新。--check 检测人工修改生成文档造成的漂移。

## 接入与维护

先登记真实仓库、主机、模型路由、预算和授权 profile。人工 bootstrap 可以按同一任务与收据格式推进，不等待未完成的调度器；自动派工需 automation_runtime_ready。部署模板默认关闭。

scope_paths 按精确文件或以 / 结尾的目录前缀匹配，角色默认范围不会扩大权限。path-ownership.json 区分源文件、生成物与历史资料；本包没有给任何 worker 发真实凭据。worktree 与 clone 也不构成 OS 沙盒。

Swift target 图采用根 Package.swift；App 用固定版本 XcodeGen 生成工程。OPS-03 定义规则，APP-13 才验证真实 Mac 工程生成与构建。不要把包内历史 Lab 的源码或 Linux 测试成绩当作产品实现已完成。

导入已有仓库时按已采用的任务范围合并，保留现有工程规则。AGENTS.md 与 roles/ 是本项目约定，并非已安装的 CLI 原生 agent 配置。

## 许可和历史完整性

自有启动材料使用随附 MIT LICENSE。历史 Lab 的源码、固定上游证据、完整第三方许可通知与原 PACKAGE-MANIFEST 均保留；上游资料不因被放入启动包而改变许可。基线副本只修改导航链接，迁移前后摘要分别登记。

发布包的 MANIFEST.json 记录每个文件的字节数和 SHA-256（清单自身除外）。可用 tools/package_starter.py 重建或验证归档。未来实验变更须产生新的 Git/证据版本，不回写历史结果。
