# 当前状态索引

更新时间：2026-10-21（Asia/Singapore）。最新适用审核：[R002](reviews/R002-R1-native-baseline-conditional.md)。

## 范围与版本

TASE-001 v1.0：**GR00T N1.7 LIBERO-adapted policy → 任务授权 Safety Gate → 原生 LIBERO/Panda**。无WBC、训练、实机。架构见[ADR-0001](decisions/ADR-0001-native-libero-only.md)。R000/R001保留历史，不被覆盖。

本main主要保存计划/审核；实现仍在[PR #3](https://github.com/Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7/pull/3)，本轮审阅head=`5e64f2408e4e798d229c0e42761207576abe7e46`，**未合并**。

## 当前证据

| 项目 | 状态 | 解释 |
|---|---|---|
| 原生部署/HF访问 | EXECUTOR_RUNTIME_EVIDENCE_DELIVERED | 新报告已记录模型加载和完整policy运行，旧401不再是主阻塞 |
| 六个预定DEV任务格 | 5 SUCCESS / 1 TIME_LIMIT | 公开账本复算一致；两任务各两初态成功；不是TEST或治理结果 |
| 推理/控制 | 181 calls / 1438 steps | 公开汇总与代码路径审阅；私有NPZ尚未由reviewer读取 |
| CPU证据/安装测试 | REVIEWER_REPRODUCED 8/8 PASS | 精确Git blob校验后，在reviewer CPU sandbox重跑 |
| 证据auditor完整性 | EXECUTOR_FIX_AND_REAUDIT_DELIVERED | R002四类假PASS及其余负例已补；普通/-O 13项测试；[A项报告](../reports/M1/audit_hardening_report.md)，待独立复核 |
| 私有原件 | NOT_VERIFIED_BY_REVIEWER | 必须提供可访问原件/脱敏包；hash声明不等于独立核验 |
| Shadow/oracle | M2 CONDITIONALLY_AUTHORIZED | 见下述工作包；尚未实现/通过 |
| Gate/CALIB/TEST | NOT_AUTHORIZED | 未进入M3/正式实验 |
| 治理有效性 | NO_EVIDENCE_YET | baseline成功不是治理效果 |

## 当前授权与入口

**PR处置：CHANGES_REQUIRED，不合并。执行处置：CONDITIONAL_APPROVAL，允许[M2工作包](work_packages/M2-shadow-oracle.md)。**

先修复证据校验和异常留证，重审既有raw；条件满足后进行有界shadow/oracle开发。旧DEV账本12/24，本工作包最多新增6次，失败也计入；剩余6次保留。另有最多80个有记录的短shadow验证case，不计为独立任务，不得扩成无界完整rollout。

私有原件独立核验尚未关闭；Codex不得自签GPT认可。下一关为M2交接审核，不自动进入M3/CALIB/TEST。GPU使用仍须现有资源许可有效。没有后台任务或自动Codex启动。
