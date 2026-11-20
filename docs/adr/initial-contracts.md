# OPS-01 项目章程与变更契约

用户委任 Codex 担任项目协调者。首版沿用 F01–F12 和 M0–M5，官方发行免费，自有代码采用 MIT。Codex 根据依赖和证据安排任务、指派负责人及独立验收者，并在已授权范围内推进日常开发。产品范围变更、新增预算或付费配额、外部账号与主机的使用授权、签名凭据和正式发布决定由用户保留。[工作章程](../../AGENTS.md) · [项目计划](../project-plan.md) · [产品基线](../baselines/product-design-v0.1.md)

## 派工与变更

每项任务指定一位负责人，每次实现使用独立 checkout 和分支。协调者将本次允许写入的路径列在任务简报中，范围必须落在任务卡的 `scope_paths` 内。需要改动范围外的共享接口或工程文件时，负责人说明目标路径、理由及影响，交由对应所有者处理，或由协调者修订任务契约后重新派工。角色职责和共享路径以仓库记录为准。[角色矩阵](../../coordination/roles.json) · [角色说明](../../roles/) · [路径归属](../../coordination/path-ownership.json)

开发模型的推理强度默认设为 `medium`。协调者按任务卡的候选顺序选择模型，在运行主机核实可用路由，分别记录请求配置及可核实的实际配置。没有调用证据的路由保持待核实。[模型目录](../../coordination/models.json) · [运行契约](../../contracts/README.md)

实现者、验收者和集成者均从指定的 `contract_sha` 读取章程、角色与任务规范，核对同一 `task_id`、`task_spec_sha256` 及本次源码基线 `base_sha`。计算任务摘要时，从卡片提取 `task_spec_fields` 中实际存在的字段，按键排序，以保留 Unicode 的紧凑 JSON 编码为 UTF-8，再计算 SHA-256。任一方发现摘要不符即暂停该任务，待协调者明确版本后继续。契约或实现提交变化时重新绑定并审查。OPS-01 启动基线为 `ae05e83c062468e001f415266a681c00a4ca0672`，其任务摘要为 `7271422dfc7d083e6abcc180fdd8e49d92d9c2b30af77b4431404e275aa9243d`。[任务账本](../../coordination/tasks.json) · [任务书](../task-book.md)

## 验收与放行

作者提交 WorkerResult，附提交、范围和原始检查输出。协调者另行指派作者及其子代理之外的独立审查 run，按验收标准核对原始证据，出具绑定 base、head 与契约的 ReviewVerdict。集成者在最新基线上验证候选，读回实际合并提交、树与父提交并记录 IntegrationReceipt。协调 Agent 汇集证据，由具有状态写权限的协调服务核对收据，在验收条件满足后将任务状态更新为 `accepted`；每项产品门槛另由授权主体签发 GateDecision。[协调策略](../../coordination/policies.json) · [机读记录](../../contracts/README.md)

M1 先要求 APP-04 与至少一项 APP-05/06/07 路线研究获验收，并提供匹配的基线，才进入 APP-08 独立裁决。只有 APP-08 获验收、至少一条声明范围内的路线在真实 Mac 上验证完整刘海核心任务，且该路线没有未解决的系统完整性阻断，才能打开 `M1_PRODUCT_GATE_PASSED`，供 APP-15/16 使用。负面研究结论可以验收；门槛为 false 或 unknown 时继续阻塞依赖该门槛的任务。正式发布另需用户授权。[门槛表达式](../project-plan.md) · [判定规则](../gate-evaluation.md)
