# TAKEOVER-RECOVERY-001 审核入口

- [TAKEOVER_STATUS](TAKEOVER_STATUS.md)：Issue #6 执行结果、边界及唯一下一步。
- [source_map.json](source_map.json)：实时 PR head/base、最新 main、R003 审阅身份与测试源码。
- [ledger_summary.json](ledger_summary.json)：历史公开声明与当前权威消费未知的区分；不是原始账本。
- [普通模式收据](issue6-cpu/normal.json) / [日志](issue6-cpu/normal.txt)：24/24、exit 0。
- [优化模式收据](issue6-cpu/optimized.json) / [日志](issue6-cpu/optimized.txt)：24/24、exit 0。
- [CLI 收据](issue6-cpu/cli-help.json)：仅参数帮助入口，无实际回放或原件审计。
- `artifact_manifest.json`：本次公开材料的字节数、SHA-256 和范围，不包含自身。

以上为 Codex executor 交付；不构成 GPT 审核批准。私有 runtime map、节点/路径身份、发现记录、逐预期 ID 对账索引和精确导出请求保存在 repo 外。原件未恢复，故真实原件逐条对账、静态帧重审及 R003 物理执行状态仍未核实。
