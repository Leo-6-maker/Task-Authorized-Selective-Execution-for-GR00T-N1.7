# E2 START HERE — 新agent的当前入口

2026-10-23，GPT规划补充。当前任务是 [Issue #8](https://github.com/Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7/issues/8)。执行依据：[R004](../reviews/R004-fresh-epoch-progress-decision.md)；详细步骤：[E2工作包](E2-FRESH-EXECUTION-AND-GATE.md)。

## 更新到已提交的接手PR #7

本轮进一步读取了 [PR #7](https://github.com/Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7/pull/7) 的实时元数据、12个变更文件清单及完整TAKEOVER_STATUS。其head为 `bb9b4346037441b220d03c26737002748856dc23`，分支 `codex/6-takeover-recovery`，父版本为PR #5的 `7e73108fd87a711b4cdc339d93749cc4add3628f`。

PR #7只提交状态、交接材料和CPU收据，文件清单没有运行代码/测试/配置改动。报告说明普通及 `-O` 模式均24/24通过，Python3.12.14/NumPy1.26.4，已保全14个本地修改/未跟踪文件；两轮定位已结束，旧原件与账本仍未知。**这些是本轮读到的执行者记录，不是GPT重新运行测试或核验私有原件。**

为保留新agent已经完成的交接工作，优先从 **PR #7当前head** 建 `codex/8-e2-gate`，而不是退回或覆盖现有worktree。若head有新变化，先记录完整身份并核对改动。其运行代码基础仍为PR #5，所以详细E2工作包的技术分析、版本和授权不变。

已完成的同版CPU测试无需为了“接手”反复重跑；新的代码修改后仍须回归，在新的物理环境还需完成其真实合同检查。旧本地保全文件不要删除，也不要未经甄别全部带入E2。

## 下一动作已经改变

PR #7/Issue #6中“唯一下一步是获得旧目录上下文和完整账本”的文字是旧恢复工作包下的结论。用户本轮明确旧电脑送修并要求不精确恢复，因此由R004替代：

**停止主动搜索旧目录 → 新授权目录建E2双环境 → 六格新baseline → 新事件/关键shadow → 真正的Gate → CALIB → 一次R2冻结。**

允许按工作包新预算运行；旧原件未知不再阻塞。没有声称旧M2或PR #7结果被无保留批准，也没有自动合并任何PR。

## 直接执行概要

1. 保全本地worktree，从PR #7的已核对head创建E2分支，正常整合main的R004和E2文档，不force push。
2. 在当前账号已有合法权限的新根目录创建独立workspace，不修改找到的旧科研checkout。复用已提交安全安装和故障修复；需要的固定官方权重可重新下载。
3. 建 `E2 / TASE-002-v1.0` 新ledger和runtime lock。旧消费保留未知，新DEV最多24、短一致性验证96；满足条件后CALIB48。正式TEST120是后续计划，待R2。
4. 真正接入Gate：预测非目标双指接触前兆；独立实际wrong-lift评价；ACCEPT执行同一最多8步前缀，REJECT/ERROR零主执行并终止。不要再只做always-accept记录。
5. 新数据按scenario重置随机状态，记录实际指令与可信任务的分离；保存全部失败；原件至少两份备份并准备实际可交付的安全审核包。

下一项交付应是新环境与新baseline，然后是新Gate演示/DEV与校准证据。无需等待旧电脑修好，不需要再次提交只有“访问阻塞”的定位报告。
