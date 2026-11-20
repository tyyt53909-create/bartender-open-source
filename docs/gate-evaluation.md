# 门槛求值与可信输入边界

`tools/gate_eval.py` 是离线参考求值器，检查给定快照与产物的一致性。它不启动 Agent、不创建租约、不读远端 Git，也不证明调用者给它的注册表已获认证。未来 TypeScript 服务需接入可信账本，并通过同一语义用例。

## 三种结果

| 表达式 | true | false | unknown |
|---|---|---|---|
| all_of | 所有分支 true | 至少一项明确 false | 无 false，至少一项 unknown |
| any_of | 至少一项 true | 所有分支 false | 无 true，至少一项 unknown |

只有 true 可满足前置。任务通过该前置检查仍需资源、租约、预算、写范围和实际授权，不能直接转成 ready 或开始执行。`--task` 的结果只表示依赖／gate 前置，不表示派工许可。

支持 task_accepted、gate_ref、host_attribute、evidence_condition、authority_condition。表达式未知、字段缺失、来源失配、过期或撤销都不能产生正面放行。负面研究 accepted 与能力 verified 分别记录；研究证据完整性的门槛可以通过，同时产品能力门槛仍失败。

## 调用输入

调用者传入当前、已认证的协调账本快照：now、task_states、active decisions、current_bindings、authority_registry，以及引用产物的可读字节。文件系统方式使用 `--artifact-root` 限定读取根；工具校验摘要与目录逃逸，未提供原始字节不会因为拥有一个 hash 而通过。

GateDecision 的 source、scope、context 与当前绑定精确一致。scope manifest 至少含 scope_id；context manifest 至少含 context_id 和非空 environment_ids，证据环境必须在该上下文内。环境与支持范围改变需生成新绑定，不从其他 OS 搬用成绩。

签发主体、角色、门槛权限、有效期和撤销状态来自 authority registry；runs 登记 principal 与完整 parent_run_id 链。作者子树不能充当唯一独立审核或签发来源。工具还读取 ReviewVerdict 并检查 task/spec/contract/base/head/作者绑定及阻断项；原始测试日志是否真正支持业务结论，仍由独立验收负责。

M3 的 context manifest 还须包含 required_subject_tasks 指定的全部 subject_bindings，每项有 task_id、task_spec_sha256、head_sha 和非空 author_run_ids；它们必须和可信 runtime.subject_bindings 精确对应。汇总任务作者、审查者和门槛签发者都须独立于这些原始作者子树。缺失来源、旧 spec 或缺父链时仍为 unknown。可信账本负责记录真实且完整的作者集合，任意本地 JSON 不能自行建立信任根。

## 签发与消费

M0 对应 APP-02 的独立验收；M1 产品裁决对应 APP-08；M3 汇总裁决对应 APP-26。source.author_run_id 指该来源任务交付作者；ReviewVerdict 由另一独立 run 审查这份交付，GateDecision 可由该有权限的审查者或独立 lead 签发。对汇总裁决还要检查原始 subject 作者集合；不需要无穷递归地再创建“审核的审核”。

at_least_one_runner_ready 的两个分支分别要求 OPS-05 + codex_runner_verified、OPS-06 + opencode_runner_verified。condition_source_tasks 防止把另一适配器的收据贴给本分支。OPS-07 的完成、至少一条真实 runner 及租约隔离证据共同构成 automation_runtime_ready，由 deployment.activation_gate 消费。人工 bootstrap 不依赖这个门槛。

## 可复查命令

```bash
python3 tools/gate_eval.py --gate M0_BASELINE_VERIFIED
python3 tools/gate_eval.py --task APP-12
python3 tools/gate_eval.py --graph
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

无运行快照时，M0 和 APP-12 前置应为 unknown。退出码：0=true；2=false；3=unknown；1=输入或用法错误。不要把 unknown 的退出码改成成功来让流水线绿灯。测试数据是 synthetic；它们不代表任何产品功能或真实 runner 可用。

`--graph` 保留 all_of/any_of 和 gate_ref，同时提供保守的引用边检查。引用边用于发现与环检查，不能被误当全部强制依赖；未选择路线和资源时不承诺唯一关键路径时长。

## 发行候选变化

APP-25 或后续修复改变相关发行候选时，生成新的 APP-26 attempt：重跑受影响 M3 验证，或附独立签署的未受影响证据复用依据，再签发当前 candidate/scope/context 绑定；W3 历史裁决不直接放行 W4 产物。

后续实现时，单任务 accepted 保留历史交付事实；新 candidate 的验证与门槛通过新的 attempt 和收据记录，不改写旧结果。
