# 当前状态索引

更新时间：2026-10-23（Asia/Singapore）。当前执行：Issue #8 / E2；最新适用范围决定为 [R004](reviews/R004-fresh-epoch-progress-decision.md)，它不是新结果验收。历史 R003 仍仅绑定其所审提交。

## 当前 E2 入口（优先于历史索引）

- 按 [E2 START HERE](work_packages/E2-START-HERE.md) 从 PR #7 实时 head `bb9b4346037441b220d03c26737002748856dc23` 建立 `codex/8-e2-gate`，正常整合 main；保留 PR #5 的运行实现与旧交接成果。原本地14个修改/未跟踪文件继续保全，未覆盖。
- `E2 / TASE-002-v1.0`：新 DEV 上限24、独立短一致性96；满足工作包前置条件后 CALIB48。TEST 待 R2，未授权；不训练、不接WBC、不上实机、不自动合并。
- 已建立新的合法可写 workspace；隔离双环境安装继续进行，失败/超时留存。Object 固定版本7/7文件独立复算大小及SHA256全部一致。先前项目缓存中的固定 Cosmos 版本10/10文件已校验并复制到独立E2副本，真实退出码0；无需再下载或提供token，不要求恢复旧账本。
- 新代码已实现 scenario reset/seed、实际语言与TaskSpec分离、接触前兆Gate、唯一执行边界、完整快照采集、安全数值审计和有界验证/备份入口。**IMPLEMENTED，不等于 RUNTIME_VALIDATED 或 REVIEWED。**
- [E2 CPU收据](../reports/E2/cpu/normal.json)及[-O收据](../reports/E2/cpu/optimized.json)：31项纯合成测试 exit0，绑定各自 source commit；不替代真实模型/仿真验收。
- 当前六格 baseline 尚未完成；真实运行、账本和审核状态将在 [E2 setup](../reports/E2/setup.md) 持续记录。下一项关键交付仍是新环境真实 baseline，随后关键 shadow 与可运行 Gate。
- 旧原件保持 `TEMPORARILY_UNAVAILABLE / NOT_INDEPENDENTLY_VERIFIED`；旧预算后续消费 UNKNOWN。下面 Issue #6 的恢复阻塞已由 R004 取代，不能用来停止 E2。

## 历史 Issue #6 接手状态（其恢复前置条件已由 R004 取代）

- 工作包：`TAKEOVER-RECOVERY-001`，发布于 `origin/main` 的 `9a7c9bd6ade46cbe92704270b068b9126c733953`。
- 实时 PR #5 head：`7e73108fd87a711b4cdc339d93749cc4add3628f`；base：`codex/2-native-baseline` / `3e214c0b761d0639bf73948356a92a03bf2ddedc`。两 PR 保持未合并；旧 PR 正文不是当前 head 来源。
- R003 审阅 PR #5 的 `d64cb1002980738f170e3206d004b4a882166543`。当前已有 oracle 输入修复、旧动作补验和 CPU 审计脚本；新 head 尚待 GPT 审核，执行者不自签批准。
- 新建本地接手 worktree，原修改和 14 个文件保存在 repo 外且原工作树不动。未修改执行代码、历史审核或原账本。
- **本轮 CPU：24/24 normal 与 24/24 `-O`，均 exit 0**；独立本地 Python 3.12.14 / NumPy 1.26.4，纯合成 fixtures。[命令与收据](../reports/takeover/issue6-cpu/normal.json)和[优化模式](../reports/takeover/issue6-cpu/optimized.json)另存。这不是远端物理验证或原件审核。
- 双跳节点、UID/GID、真实 HOME 和挂载已核对；同名 HOME 的真实路径不同。两轮有界定位后，原工作区、原件和共享账本仍未恢复，部分候选根权限拒绝。未找到不能解释为不存在。
- **`BLOCKED_EXACT_ACCESS_REQUEST` / `CURRENT_LEDGER_UNKNOWN`**：历史 DEV18/shadow74 不是当前余额。未取得 reservation/result/start/exit，不能判定补验未执行；不重跑、不换 ID。
- 唯一下一步为原执行者/项目目录所有者提供项目专属上下文与完整账本导出；私有精确请求已准备。真实运行继续暂挂；保留六次 DEV、M3/CALIB/TEST、训练/WBC/实机均不在本轮可执行范围。

## 历史 R002/M2 交付索引（以下保留旧记录，不代表当前运行余额或新授权）

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
| Shadow/snapshot | EXECUTOR_RUNTIME_VALIDATED / READY_FOR_REVIEW | [M2报告](../reports/M2/runtime_report.md)：24快照、74次比较、589预测控制步；全量原始重算通过，待独立审核 |
| DEV事件oracle | OBSERVABILITY_EVIDENCE_DELIVERED | 1段受控错误物体抬升，正常/接触/模糊记录保留；不是正式标注准确率或治理效果 |
| 当前预算 | DEV 18/24; SHADOW 74/80 | 本工作包6次新采集已结束，其余6次DEV保留；模型已正常退出 |
| Gate/CALIB/TEST | NOT_AUTHORIZED | 未进入M3/正式实验 |
| 治理有效性 | NO_EVIDENCE_YET | baseline成功不是治理效果 |

## 当前授权与入口

**PR处置：CHANGES_REQUIRED，不合并。执行处置：CONDITIONAL_APPROVAL，允许[M2工作包](work_packages/M2-shadow-oracle.md)。**

先修复证据校验和异常留证，重审既有raw；条件满足后进行有界shadow/oracle开发。旧DEV账本12/24，本工作包最多新增6次，失败也计入；剩余6次保留。另有最多80个有记录的短shadow验证case，不计为独立任务，不得扩成无界完整rollout。

A项在父PR #3 head `3e214c0b761d0639bf73948356a92a03bf2ddedc` 补交。M2已在独立stacked [PR #5](https://github.com/Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7/pull/5)交付，实际运行SHA `16f0249299a11805666f68eb06c09c8f3974efef`；[预算账本](../reports/M2/budget_ledger.json)与[manifest](../reports/M2/artifact_manifest.json)另存。本次执行者结果为READY_FOR_REVIEW，不改变R002的独立审核/合并决定。

私有原件独立核验尚未关闭；Codex不得自签GPT认可。下一关为M2交接审核，不自动进入M3/CALIB/TEST。GPU使用仍须现有资源许可有效。没有后台任务或自动Codex启动。
