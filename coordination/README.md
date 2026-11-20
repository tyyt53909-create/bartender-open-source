# 协调数据

tasks.json 是规范与初始规划快照。TaskSpec 只取 task_spec_fields 投影；运行状态不进入 task_spec_sha256。roles/models/hosts/policies 分别登记职责、候选路由、资源与策略，实际未接入字段保持 null。

phase 是工作包，wave 是推荐波次。gate_definitions 保留 all_of/any_of/gate_ref；gate_policies 登记来源任务、签发角色与绑定要求。accepted、verified、passed 分开。gate_consumers 明确非任务消费方，避免自动调度自举循环。

path-ownership.json 登记现有源文件、生成物与历史资料；scope_paths 仍是每次任务的授权边界，角色默认范围不扩大权限。document-templates 是计划与架构的叙述源，动态表格与任务书／看板由 tools/render_docs.py 编译。--check 检测漂移。

Python 只做离线检查、参考门槛求值与生成。未来 TypeScript/Node.js/SQLite 协调服务是 live 状态单写者，使用同一 JSON 契约与语义回归。任意本地 runtime JSON 不能证明可信主机身份；离线检查不会启动执行器或调用模型。

自动派工需 deployment.activation_gate=automation_runtime_ready 通过；人工 bootstrap 可以先按同一契约和租约登记开展工作，不等待自身调度器完成。
