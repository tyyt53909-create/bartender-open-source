# 离线检查与封装说明

v0.2 的验证结果记录于 [check-results.json](check-results.json)，完整回归输出见 [unit-tests.log](validation/unit-tests.log)。这些记录仅对应启动材料和离线逻辑，不是产品、远端或 Mac 通过成绩。

```bash
python3 tools/validate_plan.py
python3 tools/render_docs.py --check
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tools/gate_eval.py --gate M0_BASELINE_VERIFIED
python3 tools/package_starter.py --output /absolute/output/starter.zip
python3 tools/package_starter.py --verify /absolute/output/starter.zip
```

缺运行证据时，gate 命令返回 unknown、退出码 3 是预期关闭状态；其他检查通过不能把它转换成 passed。所有依赖已安装后，检查、生成和封装命令不请求网络。

本版严格核对 TaskSpec 和六类 Schema；回归用例覆盖失败研究 accepted 后的生产门槛、条件备选、签发者、M3 多作者、过期／错版本／错环境证据、QA 写范围、资源摘要、波次与生成文档。样例位于 contracts/fixtures/，其 valid 仅指形状有效。

历史 Lab 只验证原始 manifest 与实际字节一致，本轮未把旧测试数量重复计入新的回归统计，也没有运行 Mac。原有第三方通知与来源清单保持原样。

MANIFEST.json 记录全包除自身之外的文件大小和 SHA-256。封装器排除 Python 缓存和构建中间物，固定归档时间并保留文件模式。外层清单还覆盖 Lab 的原始清单本身。最终 ZIP 的摘要在随交付的本轮结果中给出，不把 ZIP 自身摘要递归写进 ZIP 内容。
