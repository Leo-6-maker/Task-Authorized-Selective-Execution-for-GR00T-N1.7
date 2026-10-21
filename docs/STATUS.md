# 当前状态索引

更新时间：2026-10-21（Asia/Singapore）

## 权威范围

协议：TASE-001 v1.0。架构决定：[ADR-0001](decisions/ADR-0001-native-libero-only.md)。初始审核：[R000](reviews/R000-planning-review.md)。

**GR00T N1.7 LIBERO-adapted policy → Safety Gate → native LIBERO/Panda execution。无WBC、无实机、无额外训练。**

## 当前阶段

| 项目 | 状态 | 证据/说明 |
|---|---|---|
| 计划、范围与工作流 | DOCUMENTED | 本仓库文档及R000 |
| 官方checkpoint与native接口的外部依据 | SOURCE_VERIFIED | SOURCES中的官方材料与固定源码 |
| 本地隔离部署 | ENVIRONMENT_VALIDATED / BACKBONE_ACCESS_BLOCKED | [M0报告](../reports/M0/preflight.md)；双环境、Object文件哈希和依赖检查通过；不代表模型加载成功 |
| GPU资源 | SHARED_USE_AUTHORIZED | 用户本轮允许显存充足时共用；没有独占预留，未停止现有任务 |
| 原生环境检查 | 4 PASS / 1 ERROR RETAINED | 三个预定任务双相机/EGL/20Hz；[全部开发记录](../reports/M1/dev_runs.csv) |
| 真实模型推理与native episode | BLOCKED / ZERO_MODEL_FORWARDS | Cosmos受限backbone返回HTTP401；[M1报告](../reports/M1/baseline_report.md) |
| Shadow一致性 | NOT_IMPLEMENTED | 待M2 |
| Gate与oracle | NOT_IMPLEMENTED | 本仓库没有运行时实现 |
| CALIB/TEST冻结 | NOT_FROZEN | 阈值与规模仍为计划候选 |
| 治理有效性 | NO_EVIDENCE_YET | 不填写示意结果 |

## 当前授权

R000的原始范围仍为 `APPROVED_FOR_BOUNDED_BOOTSTRAP`：M0–M1，总预算最多24个开发attempt。当前已用5/24（包含失败和环境smoke），剩余19；完整policy episode为0，成功率N/A。

本轮用户已明确允许显存充足时共用GPU，随后要求“先提交包含此阻塞的R1审核包”。Codex停止新增GPU尝试，以 **READY_FOR_REVIEW / INCOMPLETE** 交接。R1 reviewer决定为 **PENDING**；没有新的GPT批准记录，不能进入M2–M3。

交付身份：[runtime lock](../configs/runtime_lock.json)，SHA-256 `9783e72f673626aba84c2ac63bf40db4247e6cad98ec73e1a21215c0dd80fcb2`；[artifact manifest](../reports/M1/artifact_manifest.json)。具体run绑定其实际执行SHA，PR head为交付审核对象。

未授权：训练、正式TEST、修改最终事件/阈值后继续沿用旧结果、WBC/其他仿真器、实机、无限重试、破坏共享环境。

## 当前入口

- [Codex工作指令](CODEX_HANDOFF.md)
- [完整工作包](PROJECT_PLAN.md)
- [审核规范](REVIEW_WORKFLOW.md)

阶段完成后Codex可以更新客观进度与报告链接，但reviewer批准状态必须引用新审核记录，不能自签。GitHub issue和PR承载正在执行的具体任务；建立issue并不代表执行已经启动。
