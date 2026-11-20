# 独立审查报告

这是 `ReviewVerdict` 的人类可读视图；裁决源为通过 `contracts/review-verdict.schema.json` 验证的 JSON。此 Markdown 模板不代表已经执行审查。

review_id：  
reviewer_run_id：  
reviewer_principal_id：  
author_attempt_id：  
author_run_id：  
task_id：  
task_spec_sha256：  
reviewed_base_sha：  
reviewed_head_sha：  
contract_sha：  
effective_model_id：  
review_verdict JSON 路径与 SHA-256：  

## 结论

approved / changes_requested / blocked / unknown

## 发现

逐项说明影响、复现或证据位置，以及需要改变什么。没有发现也要说明本次覆盖与未检查范围。

## 证据检查

源码版本、改动路径、测试来源和真实环境是否对应；WorkerResult 的自述不能代替原始结果。

## 有效性

此结论只绑定上述对象。作者追加提交、相关基线或契约变化后，需要重新评估。

审查者身份与独立性由受信协调者核对；作者自身或作者子 Agent 的 run 不能作为唯一独立验收者。报告中的自述身份不构成授权证明。

审查者可建议批准，无权自行将项目任务设为 accepted 或绕过集成规则。
