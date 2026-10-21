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
| 本地部署和GPU预留 | NOT_VERIFIED | 本次规划未登录/安装/预留资源 |
| 真实模型推理与native episode | NOT_RUN | 待Codex M0/M1 |
| Shadow一致性 | NOT_IMPLEMENTED | 待M2 |
| Gate与oracle | NOT_IMPLEMENTED | 本仓库没有运行时实现 |
| CALIB/TEST冻结 | NOT_FROZEN | 阈值与规模仍为计划候选 |
| 治理有效性 | NO_EVIDENCE_YET | 不填写示意结果 |

## 当前授权

`APPROVED_FOR_BOUNDED_BOOTSTRAP`：Codex执行M0–M1，最多24个开发episode runs；允许授权内的CPU测试和文档实现；实际GPU使用需资源许可。下一关为R1。

未授权：训练、正式TEST、修改最终事件/阈值后继续沿用旧结果、WBC/其他仿真器、实机、无限重试、破坏共享环境。

## 当前入口

- [Codex工作指令](CODEX_HANDOFF.md)
- [完整工作包](PROJECT_PLAN.md)
- [审核规范](REVIEW_WORKFLOW.md)

阶段完成后Codex可以更新客观进度与报告链接，但reviewer批准状态必须引用新审核记录，不能自签。GitHub issue和PR承载正在执行的具体任务；建立issue并不代表执行已经启动。
