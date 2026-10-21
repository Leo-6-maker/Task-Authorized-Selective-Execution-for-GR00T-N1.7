# 当前状态索引

更新时间：2026-10-21（Asia/Singapore）

协议 TASE-001 v1.0；[ADR-0001](decisions/ADR-0001-native-libero-only.md)；初始范围审核 [R000](reviews/R000-planning-review.md)。

**GR00T N1.7 LIBERO-adapted policy → Safety Gate（后续阶段）→ native LIBERO/Panda。当前仅实现 M0–M1 原生 baseline。**

| 项目 | 状态 | 实际证据与限制 |
|---|---|---|
| 资源与隔离部署 | RUNTIME_VALIDATED | 已获显存充足时共享 GPU 许可；双环境与依赖核验；[M0](../reports/M0/preflight.md) |
| HF / auxiliary 访问 | RESOLVED_AND_PINNED | 外部 HF_TOKEN_PATH；Cosmos 固定 revision 与 LFS/文件哈希；无凭据入库 |
| 真实 Object 模型 | RUNTIME_VALIDATED | 原生 policy 加载、181 次 forward；[续验锁](../configs/runtime_lock_resume.json) |
| 原生 DEV episode | 5 SUCCESS / 1 TIME_LIMIT | 三任务 × 两固定初态；alphabet soup、cream cheese 各 2/2；ketchup 1/2 |
| 全部 DEV 预算 | 12/24 USED | 4 次环境 PASS、2 次基础设施错误、5 次成功、1 次时间上限；[全部记录](../reports/M1/dev_runs_resume.csv) |
| 动作与 reset 契约 | EXECUTOR_RUNTIME_AUDITED | horizon 16 / prefix 8；1,438 控制输入逐项复算；[契约](../reports/M1/runtime_contract_resume.md) |
| 当前交付 | READY_FOR_REVIEW | [续验报告](../reports/M1/continuation_report.md)、[manifest](../reports/M1/artifact_manifest_resume.json)；新 head 的独立 R1 PENDING |
| 当前 GPU 进程 | STOPPED_CLEANLY | 本项目 server 官方关闭，真实子进程 exit 0 |
| Shadow / oracle / Gate | NOT_IMPLEMENTED | 待相应 R1 放行 |
| CALIB / TEST / 训练 / WBC | NOT_RUN | 当前未授权 |
| 治理或安全效果 | NO_EVIDENCE_YET | baseline 成功不代表治理有效 |

最新独立决定仍为 [R001](reviews/R001-M0-M1-access-blocked.md)：它绑定旧 head `24ad57fd0dad73327f00851529c32ba762e42569`，结论 BLOCKED_RESOURCE，维持原 M0–M1 的有界补验权限。负责人之后要求按计划继续；本轮解除访问阻塞并补交真实运行证据，没有修改 R001 或自行签发新阶段批准。

当前 runtime lock SHA-256：`5666660bfb7ba215912b774bf546fbddc1c7b34d1c07f52689f5ab8c5d9ce29d`。每个 run 绑定实际执行 SHA；PR head 是新的审核对象。原始视频/state/log 的独立 reviewer 验证仍为 NOT_VERIFIED，直至访问私有原件。

剩余 12 个 DEV slots 不自动授权 M2–M3。下一步交由 GPT 审阅新 head、失败分母、契约、成本及私有证据可访问性，并决定后续范围/预算；Codex 不自动 merge。
