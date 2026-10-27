R014 latest (2026-10-27 SGT): remote access restored; one exact9599 scene diagnostic attempted and failed during LIBERO config bootstrap with EOFError, actual child/operator exit1, BEFORE LiberoEnv import completed. Constructors0/init0/model0/TEST0; no retry. Fresh XML106/BDDL/init36 and pinned dual environments passed; E2 normal/-O audit equal and all18070 originals rehashed unchanged after failure. CPU-only config4 normal/-O and full187 normal/-O all actual0. Failed diagnostic60-member archive and prior CPU31-member archive both two-location whole/member verified. READY_FOR_INDEPENDENT_R014_REENTRY_REVIEW: external launcher omitted LIBERO_CONFIG_PATH/task HOME; correction CPU-validated. Need explicit independent permission for one additional scene-only attempt; current one-process limit not self-extended. Read reports/E3/R014/resume/RECOVERY_REVIEW_REQUEST.md and STATUS.json. E3 protocol/TEST remain unauthorized; report Head is not execution Head.

Host handoff current (2026-10-27 SGT): owner requests complete GitHub delivery before moving to another host. Read START_HERE.md and docs/handoff/AGENT_HOST_HANDOFF_2026-10-27.md first. PR34 report-only; actual R014 execution remains clean exact9599. GPU1 same-scope owner permission persists. Owner reports node restored; this host read-only SSH exited255 remote-closed, so fresh resources/inventory106 remain UNVERIFIED. No native/model/TEST run. E2 full120 PR30 and course final v3 PR22 preserved; R3/protocol/TEST gates unchanged. Prior dated records below are historical.

Issue33/R014 current (2026-10-27SGT): R014 approved scoped scene code at exact9599f2e1b8d8ad4a51cb79cd7274f3daff493d42, machine grant eac3d8edeb3de7a33727d462ea652d7719e03629. Owner freshly granted GPU1 for9/36 scene-only, zero model/TEST. Three SSH timeouts255 prevent fresh106XML/resource checks; owner then requested CPU preservation. Scene NOT_EXECUTED,0constructors/0initloads/0E3TEST. No further SSH retry this turn, no inherited R013 or invented GPU UUID. Report-only branch cannot execute using its newer Head. See reports/E3/R014/TAKEOVER_HANDOFF.md and R014_STATUS.json; E2/course fallback preserved, protocol/TEST not frozen/authorized.

Issue31 E3 CPU priority (2026-10-26SGT): full charter docs/work_packages/E3-EXPANSION-MASTER-PLAN-2026-10-26.md supersedes old-stage entry below for this separate worktree. Planning/source inspection/CPU implementation only; E3 real model/GPU/MuJoCo/TEST NOT AUTHORIZED. E2 all120 retained117eligible+3censored, PR30@3484f3d R3 pending. Preserve course PR22@73ddec9 E2-only fallback and11/06 deadline. See reports/E3/E3_AUTONOMOUS_STATUS.json and REVIEW_REQUEST.md for live CPU state/scene blocker/consolidated gates. Do not self-sign, merge or change E2 original source/data/grants.

GPU1并行入口CPU候选完成：CPU源码d9e445cc693c4fc7284cfa54a83924e340f04360；启动器/原生server统一9GiB空闲下限，原55%/2GiB预算公式保留。普通/-O本机/Corelab各134/134实际0，原84完整审计与908输出完全一致。实际运行版本仍908、84已消耗/36未启动、0085 absent；候选无新TEST grant，不得启动模型/仿真/TEST。交付READY_FOR_INDEPENDENT_GPU1_RESOURCE_DELTA_REVIEW，需独立审核完整新Head、封存R012至84、签新grant后才可GPU1启动，0085/0086后强制检查点。不自签不merge。见 reports/E2/GPU1_ENTRY_DELTA/RESOURCE_DELTA_HANDOFF.md。

GPU1 latest owner instruction（2026-10-25）：用户明确“你使用GPU1”。已绑定新的私有GPU1资源记录；GPU1空闲10121MiB/总16376MiB，exact908冻结入口要求空闲>=16384MiB，当前及全空闲均无法通过。实际CPU隔离原始guard退出1，未启动server/模型/仿真，无新TEST，仍84已消耗/36未启动，0085 absent。不能自动改回GPU0、降低冻结检查或停止其他任务。GPU1资源入口限制需独立工程审核；更改执行代码须新完整Head/newgrant。见 reports/E2/R012/gpu1_request/GPU1_RESOURCE_ENTRY_REQUEST.md。

# Latest execution state — Issue25/R012,2026-10-25

84/120 original IDs consumed:61 SUCCESS,10 TIME_LIMIT,10 SEMANTIC_ABORT,and original0010/0014/0016 CLEANUP_ERROR;36 NOT_STARTED,next0085. Mandatory0018 and all four-cell structural/two-copy checkpoints through0084 passed. A new unrelated GPU process triggered the pre-admission resource guard before0085;actual operator exit1,native server exit0,all owned episode/worker/server processes absent. No new TEST error or0085 reservation. Both inspected devices currently fail unchanged free-VRAM requirements. Exact908/R012 and all science stay fixed. CPU audit/export/preservation continues;fresh complete84-prefix preflight and sufficient owner-authorized resources are required before a new uniquely named same908/R012 server. Any executable change requires a fresh independent grant. No retries,self-signing or merge. See [resource-stop handoff](../reports/E2/R012/RESOURCE_STOP_HANDOFF.md) and [current status](../reports/E2/automation/AUTONOMOUS_STATUS.json). Final36/R3/course submission remain incomplete.

---

# Codex 首轮执行指令 — M0/M1 Native Baseline

**当前任务：在不引入WBC、不训练模型的条件下，跑通官方GR00T N1.7 LIBERO-Object原生执行链，并交付可审核的基线证据。**

本文件可作为Codex任务入口。先读 `AGENTS.md`、`docs/STATUS.md`、`docs/PROJECT_PLAN.md`、`docs/ARCHITECTURE.md` 和 `docs/EXECUTION_RUNBOOK.md`，并检查实时GitHub issue中是否有更新授权。

## 执行范围

M0：隔离资源/环境与固定身份。M1：双相机、真实policy推理、action contract、完整native episode和小规模开发试跑。可同时写CPU侧日志schema、manifest和mock接口测试，但不能把它们当作真实运行验收。

暂不实现最终复杂risk scorer，不进行校准/TEST，不启动新训练。首要问题是“模型本来能不能正常完成选定任务”，不是“先把Gate写得很复杂”。

## 具体顺序

1. 拉取main，创建 `codex/<issue>-native-baseline` 分支，记录起始SHA。
2. 在用户已授权资源只读预检；缺访问/配额就报告，不猜凭据、不碰其他进程。
3. 建隔离工作目录；审查固定上游setup中的删除路径。提交安装方案/必要patch与脱敏preflight。
4. 核验源码候选和Object模型revision，选择性下载推理文件；保存manifest与hash。
5. 验证LIBERO单环境EGL、两路图像、任务对象和原生观测。
6. 真实模型server/client smoke，记录输入输出shape、horizon、夹爪映射和控制器语义。失败时不以随机动作或旧研究模型代替。
7. 跑一个完整正常episode，然后逐步扩展到预定三个任务。总计最多24个开发episode runs；包含smoke、失败和挑战尝试。
8. 验证固定初始化的装载、settling和可重现；相同seed不能代替状态hash。
9. 记录每个run状态、官方success、终止原因、调用数、inner control steps、wall time与峰值显存。保留所有失败。
10. 汇总M0/M1报告，提出R1后的shadow/oracle实施建议，提交PR并停在审核关口。

## 必交付

| 路径建议 | 内容 |
|---|---|
| `reports/M0/preflight.md` | 获授权资源的脱敏验证、安装风险、可用性和阻塞 |
| `configs/runtime_lock.json` | 实际source/model/dependency/patch身份，不写未验证版本PASS |
| `reports/M1/runtime_contract.md` | cameras、state/action、horizon、夹爪、control rate、wrapper/初始化契约 |
| `reports/M1/baseline_report.md` | 所有开发run汇总、成功与失败、成本、已知问题、下一步 |
| `reports/M1/artifact_manifest.json` | artifact ID、大小、hash、公开性、来源run和验证方式 |
| `tests/`及运行入口 | 已实现的接口/manifest/日志测试；mock与runtime分开 |
| README更新 | 实测可运行命令；尚未完成的功能明确标注 |
| PR/执行issue | commit、实际测试、未完成项、申请R1审核 |

原始视频、snapshot和日志留在授权存储；公开GitHub只放脱敏证据及必要小样例。不要上传课程PDF或内部审查全文。

## 接受标准

- 真实Object适配权重被正确加载，非base+随意tag；版本可核验。
- 双相机和state/action契约清楚，不把7个state stream误写成7维连续state。
- 有完整episode证据；至少两个预定任务在不止一个开发初始化上重复成功。
- 未成功场景和基础设施错误完整保留，未为了通过而挑seed或改任务。
- 能区分模型动作与环境控制输入，夹爪只转换一次。
- 具有运行成本估计和明确剩余阻塞，足以决定下一阶段预算。

未达到全部标准也必须提交真实报告，状态写 `CHANGES_REQUIRED` 的建议或 `READY_FOR_REVIEW`，不能自签GPT结论。

## 停止条件

无获授权GPU；需要删除共享配置/停止他人任务/修改安全设置；模型接口不匹配且无法定位；24个episode预算用尽；需要更换模型/任务/训练路线；试图读取正式TEST。出现这些情况保留现场证据，在issue中说明最小阻塞和建议，不无界继续。

## 给GPT的交接格式

```text
M0/M1 READY_FOR_REVIEW
PR: <url>
Head: <full sha>
Runtime lock: <path + hash>
Actual tests/runs: <commands + exit status>
Baseline: <counts by task, including failures>
Artifacts: <manifest path>
Unverified/blocked: <explicit list>
Request: R1 approval for M2–M3, or targeted repair authorization.
```

不要写“模型已经安全”“治理已有效”。本轮只建立可用且可追溯的原生基线。
