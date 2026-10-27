Host handoff current (2026-10-27 SGT): owner requests complete GitHub delivery before moving to another host. Read START_HERE.md and docs/handoff/AGENT_HOST_HANDOFF_2026-10-27.md first. PR34 report-only; actual R014 execution remains clean exact9599. GPU1 same-scope owner permission persists. Owner reports node restored; this host read-only SSH exited255 remote-closed, so fresh resources/inventory106 remain UNVERIFIED. No native/model/TEST run. E2 full120 PR30 and course final v3 PR22 preserved; R3/protocol/TEST gates unchanged. Prior dated records below are historical.

Issue33/R014 current (2026-10-27SGT): R014 approved scoped scene code at exact9599f2e1b8d8ad4a51cb79cd7274f3daff493d42, machine grant eac3d8edeb3de7a33727d462ea652d7719e03629. Owner freshly granted GPU1 for9/36 scene-only, zero model/TEST. Three SSH timeouts255 prevent fresh106XML/resource checks; owner then requested CPU preservation. Scene NOT_EXECUTED,0constructors/0initloads/0E3TEST. No further SSH retry this turn, no inherited R013 or invented GPU UUID. Report-only branch cannot execute using its newer Head. See reports/E3/R014/TAKEOVER_HANDOFF.md and R014_STATUS.json; E2/course fallback preserved, protocol/TEST not frozen/authorized.

Issue31 E3 CPU priority (2026-10-26SGT): full charter docs/work_packages/E3-EXPANSION-MASTER-PLAN-2026-10-26.md supersedes old-stage entry below for this separate worktree. Planning/source inspection/CPU implementation only; E3 real model/GPU/MuJoCo/TEST NOT AUTHORIZED. E2 all120 retained117eligible+3censored, PR30@3484f3d R3 pending. Preserve course PR22@73ddec9 E2-only fallback and11/06 deadline. See reports/E3/E3_AUTONOMOUS_STATUS.json and REVIEW_REQUEST.md for live CPU state/scene blocker/consolidated gates. Do not self-sign, merge or change E2 original source/data/grants.

GPU1并行入口CPU候选完成：CPU源码d9e445cc693c4fc7284cfa54a83924e340f04360；启动器/原生server统一9GiB空闲下限，原55%/2GiB预算公式保留。普通/-O本机/Corelab各134/134实际0，原84完整审计与908输出完全一致。实际运行版本仍908、84已消耗/36未启动、0085 absent；候选无新TEST grant，不得启动模型/仿真/TEST。交付READY_FOR_INDEPENDENT_GPU1_RESOURCE_DELTA_REVIEW，需独立审核完整新Head、封存R012至84、签新grant后才可GPU1启动，0085/0086后强制检查点。不自签不merge。见 reports/E2/GPU1_ENTRY_DELTA/RESOURCE_DELTA_HANDOFF.md。

GPU1 latest owner instruction（2026-10-25）：用户明确“你使用GPU1”。已绑定新的私有GPU1资源记录；GPU1空闲10121MiB/总16376MiB，exact908冻结入口要求空闲>=16384MiB，当前及全空闲均无法通过。实际CPU隔离原始guard退出1，未启动server/模型/仿真，无新TEST，仍84已消耗/36未启动，0085 absent。不能自动改回GPU0、降低冻结检查或停止其他任务。GPU1资源入口限制需独立工程审核；更改执行代码须新完整Head/newgrant。见 reports/E2/R012/gpu1_request/GPU1_RESOURCE_ENTRY_REQUEST.md。

# Latest execution state — Issue25/R012,2026-10-25

84/120 original IDs consumed:61 SUCCESS,10 TIME_LIMIT,10 SEMANTIC_ABORT,and original0010/0014/0016 CLEANUP_ERROR;36 NOT_STARTED,next0085. Mandatory0018 and all four-cell structural/two-copy checkpoints through0084 passed. A new unrelated GPU process triggered the pre-admission resource guard before0085;actual operator exit1,native server exit0,all owned episode/worker/server processes absent. No new TEST error or0085 reservation. Both inspected devices currently fail unchanged free-VRAM requirements. Exact908/R012 and all science stay fixed. CPU audit/export/preservation continues;fresh complete84-prefix preflight and sufficient owner-authorized resources are required before a new uniquely named same908/R012 server. Any executable change requires a fresh independent grant. No retries,self-signing or merge. See [resource-stop handoff](../reports/E2/R012/RESOURCE_STOP_HANDOFF.md) and [current status](../reports/E2/automation/AUTONOMOUS_STATUS.json). Final36/R3/course submission remain incomplete.

---

Issue25/R012：exact908bef373eedf8d008ad8d9a91478e3f719eecfb 已获377fe3b85989e6d1fd105002c3c0c09827598886授权。用户后续明确允许显存充足时GPU0并行，GPU1可考虑；已留证资源覆盖条件，未停止原任务。实时完整预检exit0，0017/0018均SUCCESS/exit0，0018真实MuJoCo关闭握手/实际worker0/句柄释放、配对状态动作/RNG、原16未改及两地备份全通过，开始自主0019–0120，每四格结构核验/备份。任何新异常立即停止并保留原ID；科学冻结/执行代码不改，不自签R3，不merge。详见 reports/E2/R012/PROGRESS.md 和 automation/AUTONOMOUS_STATUS.json。

Issue23/R011：0015 SUCCESS/exit0，0016 CLEANUP_ERROR/exit1，真实执行按规则已停止；16已消耗=13SUCCESS+3CLEANUP_ERROR（0010/0014/0016），104未启动，0017 absent。原14原件全量未改，全16两地1900成员验哈希。真实CPU复现sentinel-ready/exitcodeNone误分类，已修复有界waitpid确认及未来撤销grant的只读历史registry；普通/-O本机及Corelab各123/123 exit0，原16审计完全一致。新CPU代码无TEST许可，READY_FOR_INDEPENDENT_RUNTIME_DELTA_REVIEW_AFTER_R011_0016。下一步独立GPT签新完整Head；不重跑、不merge。详见 reports/E2/R011/RUNTIME_DELTA_HANDOFF.md。

当前 Issue #20 / R010：Shadow合作清理、必要server信号清理wrapper和跨版本只读TEST审计已完成；本机与Corelab普通/-O各118/118实际exit0，原14原件审计统计完全一致，原件与新CPU证明均两处验哈希。状态READY_FOR_INDEPENDENT_RUNTIME_DELTA_REVIEW，execution_authorized=false。旧R008暂停/R009失效；需GPT绑定最终完整新Head签新grant后，才可从0015继续，0016强制检查点。真实账本仍14已消耗（12SUCCESS，0010/0014 CLEANUP_ERROR）/106未执行。课程15页草稿与源码ZIP已准备，R3与最终提交未完成。不逐CPU错误请求批准，不自签、不重跑、不merge。见 reports/E2/engineering/RUNTIME_DELTA_HANDOFF.md 与 reports/E2/automation/AUTONOMOUS_STATUS.json。

当前 Issue #18 / R009：0011/0012及强制检查点通过后，0014再次CLEANUP_ERROR/exit1，已强制停止并关闭服务器。120计划=14已消耗（12SUCCESS+0010/0014两次清理故障）+106未启动；0015未预留。代码仍exact a1c6424bd348b36c55a20d38750a269e9551a698，无修复/重跑/merge。普通/-O停止审计与公开数值CPU核验均实际exit0，原件两处验哈希保全。当前STOPPED_FOR_REPEATED_CLEANUP_INCIDENT_REVIEW，下一步仅GPT事故审核及有界CPU生命周期修复授权，新代码须新grant后才能继续。详见 reports/E2/R009/R3_HANDOFF.md。

# 当前状态索引

当前 Issue #16：R008真实激活后，在原e2-test-0010的shadow清理阶段返回CLEANUP_ERROR/exit1，已按STOP规则关闭服务器。120计划保留：10已预留（9正常+1清理错误）、110未启动。运行代码仍exact a1c6424bd348b36c55a20d38750a269e9551a698，未改动。普通/-O live停止审计均exit0；原件两处核验完成。详见[事件交接](../reports/E2/R008/R3_HANDOFF.md)。下一步仅GPT事故评估；不重跑0010、不自动继续0011。下方Issue14状态保留为历史。

## Issue #14 — READY_FOR_R007_FIX_REVIEW / TEST_EXECUTION_SUSPENDED

R007 允许 TEST server launcher 目录与 admission 交接的 CPU 修复；旧 R006 已由 main 暂停。修改仅涉及 launcher 与新增 CPU 集成测试，native server/scientific configs 保持不变。最终固定代码 `a904e2678a3c511e36580a173e77b9c72521e093` 普通与 `-O` **89/89、真实suite子进程退出0**，包括原71项和18项新检查。未启动GPU、模型、仿真或真实TEST；上次已核验TEST0/120，本轮新增消耗0。

[修复交接](../reports/E2/R007/R007_FIX_HANDOFF.md)列出精确代码/收据、保全hash及限制：当前Corelab SSH超时，最新远端现场刷新和新CPU原件远端副本尚未完成；保留快照审计不是新远端核验。唯一下一步为GPT审核新Head并决定是否签发R008；任何将来真实运行之前必须恢复只读现场核对。下方R006/Issue12原授权文字均为历史，不覆盖暂停决定。


## Issue #12 — R006 authorized, execution stopped before model load

R006/grant commit `6c5d6c69e9abecf66999eab318b6d8c8a1b676a6` authorizes exact execution Head `3e2cb7ff0b98ac82564e0b7a60523a29cb4c8964`; PR #11 stays open/unmerged. Current grant admission/resource/source/model/official-init checks passed. The first frozen server launch hit a directory-ownership contract conflict and exited1 before torch/model load. R006's stop rule was applied: **TEST0/120 reserved, all120 unstarted, no model requests/simulation**. Runtime code and scientific freeze remain unchanged. No new name, retry, bypass or grant edit.

[Incident and proposed bounded repair](../reports/E2/TEST/INCIDENT-001.md) · [Issue12 handoff](../reports/E2/TEST/R3_HANDOFF.md). Only next step is GPT incident assessment / exact-head repair authorization. Below is retained Issue10/history; its pre-R006 authorization status is historical.


## Issue #10 — READY_FOR_R2_DELTA_REVIEW / TEST NOT_AUTHORIZED

当前依据为 main [R005](https://github.com/Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7/blob/e00f40cea298ce67159007d619dbf5e2747cb178/docs/reviews/R005-R2-E2-conditional-freeze.md)：条件科学冻结，不是 TEST 放行。独立 stacked `codex/10-test-freeze` 接续 PR #9 `fc38e816ff3e75e87c29da3aa18009dcc0542f02`；保留原交付，不重写/rebase父PR。

新增固定120格许可门/ledger/CPU审计及统计；仅CPU导出既有488候选与8组CALIB完整数值配对。真实TEST仍0，DEV19/CALIB48、原始失败和备份均保留，无新模型/仿真/下载。详见 [R2_DELTA_HANDOFF](../reports/E2/R2_DELTA_HANDOFF.md) 和 [TEST入口合同](work_packages/E2-TEST-ENTRY.md)。本段优先于下方历史Issue8“尚无R005”状态；原运行事实不变。下一步仅独立GPT delta审核。


更新时间：2026-10-24（Asia/Singapore）。当前执行：Issue #8 / E2；最新适用范围决定为 [R004](reviews/R004-fresh-epoch-progress-decision.md)，它不是新结果验收。历史 R003 仍仅绑定其所审提交。

## 当前 E2 入口（优先于历史索引）

执行者已完成 Issue #8 的原生 baseline、DEV Gate 和条件 CALIB，当前为 **READY_FOR_R2_REVIEW / NOT_GPT_APPROVED**。范围决定仍为 [R004](reviews/R004-fresh-epoch-progress-decision.md)；没有新的独立结果审核，也没有合并 PR。

- 分支 `codex/8-e2-gate` 从 PR #7 `bb9b4346037441b220d03c26737002748856dc23` 接续 PR #5 `7e73108fd87a711b4cdc339d93749cc4add3628f`，正常整合 main。原工作树修改与旧交接保留，未修改其他研究 checkout。
- 固定原生 GR00T/LIBERO 双环境与 Object/Cosmos 权重：[runtime lock](../configs/runtime_lock_E2.json)、[最新17文件复核](../reports/E2/model_file_recheck.json)。Cosmos来自既有项目缓存，已建立独立E2副本；不需要重复下载或新token。
- [67个attempt完整对账](../reports/E2/ledger_reconciliation.json)：DEV19/24、独立短验证32/96、CALIB48/48、TEST0且未授权。包括原0006中断、537控制步/exit143/缺result和不可解码视频；不以诊断0019替换它。总1920次真实模型请求、15126主控制步。52 SUCCESS、9 TIME_LIMIT、5 SEMANTIC_ABORT、1原中断只是账本分类，不是混合效果分母。
- [新baseline](../reports/E2/baseline_report.md)覆盖六格，5成功/1满720步timeout；[新C2与shadow](../reports/E2/shadow_validation_report.md)有两次主要事件、16不同快照/32短比较PASS；[DEV Gate](../reports/E2/gate_dev_report.md)六格5成功/1拒绝，危险配对在56步后拒绝下一前缀，B0首次wrong lift60步，候选主执行0。
- [CALIB结果](../reports/E2/calibration_report.md)：24B0+24G全部完成，24组主状态/RNG、原动作及实际控制前缀一致，普通/-O原件审计一致退出0。C0成功11/12对11/12；C2成功8/12对8/12，主要wrong lift4/12对0/12、G4次拒绝终止。488个固定B0功能预测按预声明并列规则选k3，0/4首次事件候选漏放、0/286 C0局部拒绝。**同一CALIB数据选点与评价，不是独立TEST、自然错误率或安全认证。**
- [CPU46项普通](../reports/E2/cpu/03653db1/normal.json)与[-O](../reports/E2/cpu/03653db1/optimized.json)均通过，明确合成；真实短比较、DEV/CALIB数据审计和实际模型不能相互替代。模型/仿真已全部退出，当前没有本项目活动native任务。
- [可实际获取的最小数值/媒体包](../reports/E2/review/README.md)含119个原件派生文件；[CALIB四个新主要事件窗口](../reports/E2/calibration_first_event_windows.json)及[双视角图](../reports/E2/calibration-first-event-contact-sheet.png)补充全部新阳性。66个完整结果的视频覆盖全部主控制步；原中断视频仍保留。完整可信pickle/原件留私有备份，未声称GPT已读取。
- CPU失败回溯曾带本机路径，当前文件已脱敏并保留原始私有hash；历史提交未改写，未发现凭据。[实际说明](../reports/E2/public_log_redaction.json)。原件与失败结果未修改。
- 唯一下一步：GPT集中R2审核 [E2交接/审核包](../reports/E2/R2_REVIEW_PACKET.md) 和 [提议冻结](../configs/e2_protocol_lock.json)。120个TEST格仅为未授权提案；当前runner拒绝TEST，不自动开始新GPU任务、训练、WBC、实机或merge。旧原件仍未独立核验，旧后续预算UNKNOWN，不再主动恢复旧目录。

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
