# 执行器契约与接入检查

这是本项目的协议设计，当前包没有可运行的派工服务。

## 共同操作

probe、start、observe、interrupt、reconcile、collect、close。start 接收已持久 attempt 与幂等键；超时进入 unknown 后查询，不直接重发。close 需要实际停止与产物收集证据。

输入采用模板 task-brief 与 run-manifest；worker 结果使用 worker-result.schema.json；可信的运行器另生成执行收据。模型自行生成的结果不充当可信执行证明。

## Codex 首条路线

本轮只读核查本机版本 0.169.0 与 exec help。未来在目标 host 固定版本，使用指定工作区、JSONL、结果 schema 和显式 session 恢复。协调器创建工作区后不再叠加 managed worktree。

命令参数由适配器按数组传给进程，任务正文从文件或 stdin 输入。不要将任务文本、仓库名或路径拼成可执行 shell 字符串。使用已有受控权限配置，不增加跳过沙盒或批准的参数。

## OpenCode 第二条路线

本轮未安装或调用。按实际版本 help 和官方 V2 文档验证 run、JSON、独立 server、指定 session 与 agent/model 路由。当前文档字段与旧版本不同，不直接部署一个未经核对的配置文件。

原生事件不是持久全集；断连后查询 session、Git 和产物。子 Agent 权限独立核查，不依赖隐含的父权限上限。

## ocra

待确认具体产品。Orca ADE 是候选，尚未安装或连接。若采用，映射项目 attempt 与 native Task/Dispatch，并保持一个派工权威；不可同时让两个系统自行为同一 task 启动 worker。

## 首次演练

两个不相交写入任务、一次独立审查、一次候选合并、一次断连/取消、一次过期 lease 和一次负面研究裁决。演练完成后记录实际兼容表；不要把文档结构检查写成演练通过。
