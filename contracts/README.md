# 机读契约 v0.2

本目录固定六种记录名称：`TaskSpec`、`WorkerResult`、`ReviewVerdict`、`RunManifest`、`IntegrationReceipt`、`GateDecision`。协调器读取 JSON；Markdown 报告是供人阅读的解释，不能替代 JSON 裁决或用来解析状态。

## 记录的含义

| 契约 | 承载的事实 | 不能单独证明的事项 |
| --- | --- | --- |
| TaskSpec | 任务卡字段、依赖、写范围、验收要求与初始运行态投影 | 任务已经运行或通过验收 |
| WorkerResult | 某次 attempt 的交付声明、实际源码、检查与产物引用 | accepted、产品能力已可用 |
| ReviewVerdict | 对指定 base/head、任务摘要与契约提交的独立审查结论 | 审查身份真实、现有分支仍等于被审查分支 |
| RunManifest | 实际运行主机、执行器、模型解析结果、工作区与资源租约 | 请求的模型标签就是实际模型；attempt 终止就是进程停止 |
| IntegrationReceipt | 候选集成与真实合并结果的读回记录 | 合并请求入队就是已合并；已合并就是已验收 |
| GateDecision | 在指定 source、scope、context 下，由指定主体签发的门槛裁决 | JSON 自报 passed 或自报 reviewer 就具有开门权限 |

Schema 均为 JSON Schema Draft 2020-12，自包含且不需要在线获取引用。时间统一写为 UTC `YYYY-MM-DDTHH:MM:SS[.小数]Z`；Schema 的 pattern 检查词法，真实日期是否合法及先后关系还需实际解析。`FormatChecker` 只有在对应可选格式依赖已安装时才会校验 `date-time` / `uri`，不能只传入这个类就假设所有 format 已生效。未知属性会被拒绝；字段变更需要相应版本迁移。

`task.schema.json` 的标题已统一为 `TaskSpec`。v0.2 为兼容现有任务账本，仍校验包含初始 runtime projection 的完整卡片；真正参与 `task_spec_sha256` 计算的是账本 `task_spec_fields` 指定的不可变字段投影。`schema_version` 登记在任务目录根对象，不在每张卡重复。规划阶段的运行态 `null` 仅表示尚未发生，不能填入运行收据。

## 摘要与引用

`base_sha`、`head_sha`、`contract_sha`、各 candidate/merge/tree OID 接受仓库使用的 40 或 64 位小写十六进制 Git 对象 ID。`contract_sha` 固定指向本次运行所采用的契约版本 Git 提交，不能用模型标签、文件名或“最新”代替。`task_spec_sha256` 和所有 `sha256` 字段固定为 64 位内容摘要。

产物引用统一为 `{ "path": "相对路径", "sha256": "内容摘要" }`。path 相对于当前可信证据根目录；拒绝绝对路径与 `..` 路径穿越。实际验证器还必须解析真实路径并拒绝经符号链接逃出证据根目录的文件，读取字节后重算摘要。文件存在、摘要相同只证明内容被固定，不能证明作者、观察结果或执行环境可信。

`TaskSpec` 摘要使用既定规范：按 `task_spec_fields` 投影，JSON key 排序、UTF-8、保留 Unicode、紧凑分隔符，再计算 SHA-256。Git 工作区中的原始文件字节摘要与此投影摘要含义不同，不得混用。

## 协调器必须执行的语义检查

Schema 负责记录形状，协调器负责下列跨记录关系。这些条件不能由自由文本声明替代。

1. **独立性与权限。** 从外部可信 authority registry 核对 principal、角色、允许签发的 gate、run 和 authority 记录。审查 run 不能是作者 run，也不能位于作者的子 Agent 父链中；缺失父链、循环或无法确认的创建关系返回 unknown。记录自身的 `role`、`run_id` 只是待核实声明。身份认证、可信运行登记及签名验证属于真实协调器的接入责任；此包没有实现密码学签名体系。
2. **当前绑定。** 对比 task/attempt、fencing token、TaskSpec 摘要、契约提交、reviewed base/head、候选提交、scope/context 与当前可信账本。分支、目标基线、契约、范围或上下文发生变化后旧结果不能直接沿用。`contract_sha` 必须是被允许采用的实际提交。
3. **审查来源。** 按 `review_verdict_ref` 读取并校验 ReviewVerdict，将其 task/author/reviewed source/contract 与 GateDecision 或 IntegrationReceipt 的对应字段逐项核对；校验 reviewer manifest、WorkerResult 和原始证据。一个摘要正确、内容却属于其他任务的报告不能通过。
4. **门槛范围。** `scope.manifest_ref` 与 `context.manifest_ref` 固定本次适用的路线、OS build、显示器条件、权限、基线和所需能力集。调用方必须提供当前所需 scope/context，不能从待审决定反向生成“当前值”。OS、路由或机器条件之间不能借用实验成绩。范围内容的产品解释仍由对应 gate policy 与证据验收实现。
5. **门槛裁决。** 校验 `issued_at <= 当前时间 < expires_at`，拒绝过期、未来签发或撤销的决定；检查受信来源的新旧顺序与撤销事实，不能忽略撤销后重放较早的 passed。按照 gate policy 验证完整必需条件集，逐一核对 evidence 的环境与真实产物；`passed` 的 JSON 形状有效仍不足以开门。
6. **资源与停止。** RunManifest 的租约、主机和 fencing token 必须与当前资源账本相符；terminal attempt、取消请求和租约超时均不自动释放 GUI 占用。`confirmed_stopped` 要求停止证据，实际释放还需要校验进程/会话所属权与停止事实。
7. **合并读回。** `status=merged` 必须带真实 merge commit、tree、parents 及读回证据。比对实际树与已验证候选树，并核对集成策略与父链。Merge request 被接收或排队只允许 requested/queued；后续 accepted 仍由任务验收规则决定。

上述第 1、2、4、5 项的离线 gate 求值由 `tools/gate_eval.py` 按它公开的输入契约执行。其测试只能证明输入处理与拒绝逻辑，不能把示例 registry 变成生产身份系统。审查内容、实际 Mac 行为、远端合并和真实进程停止都需要运行环境提供可验证来源。

## 模板与合成样例

`templates/*.json` 的运行契约模板使用外层 `template_status: template_not_executed`，待填写字段在 `payload` 内。外层模板和未填写的 payload 均应无法通过运行时 Schema。实际记录需另建文件并填写观测值；不得把占位值、全零摘要或样例收据登记到真实证据账本。

`fixtures/` 的所有例子都带 `synthetic` 命名，仅用于 Schema 结构回归。它们使用虚构仓库、ID、时间和摘要；未附实际证据字节，也没有运行任何 Mac 测试、调用付费模型或合并代码。valid 表示“形状符合 Schema”，不表示“已获授权或事实成立”。invalid 样例覆盖错误自验收、缺少证据、未探测模型、未读回合并、门槛缺少绑定和路径穿越等风险。

在仓库根目录执行：

```sh
python3 -m unittest discover -s tests -p 'test_contracts.py' -v
```

任务账本使用同一 Schema 的整体验证由计划检查工具负责。测试依赖的 `jsonschema` 版本由包根依赖清单固定。
