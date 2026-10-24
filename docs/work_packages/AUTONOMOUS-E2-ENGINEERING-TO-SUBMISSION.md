# AUTONOMOUS-E2-ENGINEERING-TO-SUBMISSION — Codex 长程自主执行总任务

**授权来源：**用户于 2026-10-24 要求“制定 project 长程自主推进任务，工程问题自主修复”；GPT 独立事故审查 [R010](../reviews/R010-repeated-cleanup-and-autonomous-engineering.md)。  
**项目：**ME6401 Part 2 / TASE-002-v1.0 / frozen GR00T N1.7 LIBERO-Object + Runtime Task-Authorized Safety Gate。**本任务不涉及 GR00T+WBC、实机、再训练或新模型。**  
**目标：**从当前重复的 shadow cleanup 程序错误出发，由 Codex 自主解决工程阻塞、维护证据、在新独立许可下继续预先冻结的 TEST，从原始数据生成独立 R3 审核包，再准备最终课程交付。**不必为每个 CPU 错误询问用户或 GPT；但没有签署新 executable SHA 的独立 TEST grant，不能让已改源码运行正式实验。**

## 0. 单一真实状态源——此刻实际在哪里

| 维度 | 固定/确认 |
|---|---|
| 最近报告 PR | [PR #19](https://github.com/Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7/pull/19)，报告 HEAD `29f50b36af25a8b76583308cf0e5fbbe22365f27`；report-only，未合并 |
| 实际前14运行 HEAD | `a1c6424bd348b36c55a20d38750a269e9551a698`，科学冻结 |
| 原先活跃 grant | R008 commit `f084723cb1d00cb7675fa7394dc1b03c0ce3dcac`；已因第二次 cleanup 事故于 current main **暂停**，历史字节/提交保留 |
| R009 | 单次 `0010` incident clearance 现因 `0014` 复发而失效；历史审查记录保留 |
| 120 TEST 固定计划 | `e2-test-0001`…`e2-test-0120`，顺序且不得修改 |
| 已占名额 | **14 个：12 SUCCESS；0010/0014 两个 CLEANUP_ERROR/退出1，不能重跑、删去或标记SUCCESS** |
| 未占名额 | **106 个：`e2-test-0015`…`e2-test-0120`** |
| 已完成行为 | 保存主控制步1882、真实policy请求240；只覆盖 alphabet_soup 的 init6–9 部分 |
| 故障源 | 两次均为 `tase/shadow.py::Shadow.close`：join10后仍 alive → terminate/join5并 raise；worker 最终 exit0，但详细退出时序未知 |
| 原件来源 | 两处全量原件备份；上次14条raw归档254951092 bytes、1611成员、SHA256 `cfe5f8357d2b48b473e95015f46dad933b1a17afbe830f6d83e1a2a30e85a76f` |
| SCIENCE 固定 | `k=3`、可信TaskSpec、wrong-lift oracle、C0/C2、冻结模型/processor/控制器、30 TEST init/120 cells、16 raw/8 executed/720 max controls、2000 paired-cluster bootstrap/seed640500 |
| 截止 | 2026-11-06 23:59 SGT；优先完成真实数据和可辩护的结果，不牺牲证据规则 |

禁止把 GitHub 的 `READY_FOR_REVIEW`、本地 CPU PASS 或原件有双备份等同于“GPU试验已独立认可”。Codex、用户、GPT 的审批角色和任务产物应清晰分离。

## 1. 授权等级：最大化工程自主性，同时锁住科学实验

### A：Codex 可以自主完成、自己重复迭代、不需每次请示

- 读取所有已授权公开文件、当前私有原件/日记/manifest，安全备份、搜索定位、修复环境访问、验证拥有的节点/缓存、普通 SSH 恢复（不绕过安全认证）。
- **CPU-only** 故障复现、模拟器/worker 的合成替身、Linux multiprocessing close 测试、patch、单元与集成测试、普通/`-O`回归、静态对照、证据索引和 CPU 审计；测试失败后主动分析修复再测，不设置形式化“每次错先问GPT”关口。
- 与已确认重复 cleanup 事故有关的生命周期收尾、进程资源释放、实测收据与安全的历史多版本审计兼容修复；保留严格错误语义，必要时实现 read-only 假设验证与 instrument。
- Git 新分支、保留 parent PR 的 stacked draft PR、提交/更新 implementation/evidence、在每个里程碑更新 GitHub issue 与 owner-facing STATUS；公开材料只保留脱敏路径，不提交 token、权重、private pickle、内部账号。
- 普通授权范围内的两地存储哈希、失败/中断收据、代码版本注册表和停止点证明；旧目录和账本只读，新的衍生产物另存。
- 在已签署当前 CODE SHA 的机器 `TEST_AUTHORIZED` **并且实时 preflight 完全通过**之后，可以按原预登记顺序连续执行普通 TEST cells/每4格自动审计、自动备份，不必每格回来问用户/GPT。模型使用仍受实际GPU资源许可、单GPU共享条件和防干扰约束。
- 在工程修复和审核之间并行起草最终 slides、README、代码复现说明与文献引用，仍须将未经R3审核的性能措辞标为 preliminary。

### B：Codex 可自主修代码，但新代码**不能**自行启动真实模型／TEST

- 修改 `tase/shadow.py` 的工作进程关闭协议与收据，和为此确实必需的 `tase/e2_context.py` cleanup wrapper、`scripts/e2_audit_test.py`、`scripts/audit_epoch.py`、纯历史 grant verification helper 及 tests。
- 由于 `configs/e2_test.json` 的 `frozen_sha256` 固定 `tase/shadow.py`，只允许更新**变更工程文件相应的 SHA256 引用**；不允许修改配置中的任何科学参数、选参、动作限制、数据集或评价规则。
- 对需要改代码的工作，允许先在一个分支里反复编译、测试、修复、提交，直到完整的“可检查新 Head＋CPU／旧数据回归＋差异说明”就绪，**再申请一次独立机器 grant 审核**。不要每个中间提交都要求评审，但也不能假设新 Head 已有 TEST 权限。
- 新版本中的 admission 逻辑仍必须严格“current HEAD == reviewer authorized Head”；历史报告文件只在 **read-only auditing** 时使用旧的、曾经合法授权的 grant/commit/config 原件。被暂停的旧 grant 不能再授权未来运行。

### C：必须停止真实执行、需要独立 reviewer/owner 决定

- 没有合法GPU权限、授权主体发生变化、SSH/host-key 不可信、设备或cache被其他人占用、无法证实原件身份。
- 改变模型权重/processor、LIBERO源/controller、Gate预测或打分、TaskSpec/oracle阈值、k3、C0/C2、任务/seed/init、样本数量/顺序、统计估计量和样本排除标准。
- 运行前或运行时发现实际物理/主状态或policy RNG非干扰失败、已检查前缀与实际执行不等、未经授权动作执行、缺失/矛盾原始收据、worker残留不明身份或无法恢复完整账本。
- 在已签署 HEAD 之外调用真实server/GPU/model/MuJoCo；在未预留或已用的编号做额外真实试跑；重置、删除或“补做” `0010/0014`。
- R3 最终结论、科学条件修改、使用额外数据/额外计算预算、merge已有stacked PR、最终提交承诺。

**默认策略：**工程故障可在 CPU 分支上自主修复；只要可能影响真实模型/测试，真实 TEST 停止到下一项精确 grant。禁止通过修改 Python guard、JSON签名字段、Git ref 或自动生成伪“GPT approval”来规避此规则。

## 2. 长程阶段与验收：一次接手，滚动推进

### P0 — 保全和独立基线

- Fork/branch from PR19 fixed Head `29f50b36af25a8b76583308cf0e5fbbe22365f27`，例如 `codex/20-lifecycle-autonomous`，stacked PR base `codex/18-test-resume-r009`。先保存任何dirty/unpushed work，不修改旧运行checkout。当前失败的真实runtime HEAD仍 `a1c6424...`。
- 固定0010、0014异常原件/exit/worker收据，两个老授权历史 commit/hash，14条 reservation/result 原件身份、原件双备份与总账；当前 R008 grant 已在 main 暂停，R009 也已 superseded。
- 建立 `reports/E2/ENGINEERING_BASELINE.md`（公开脱敏）和私有 `code_epoch_ledger.json` 记录每个回合的源码HEAD、原始测试ID、grant commit、配置SHA、执行状态。旧结果不修改。
- **完成：**CPU纯只读清单重算120 planned/14 consumed/106 unopened、两次失效真实存在、旧原件哈希、没有隐藏的active job；无法获远端时明确 `REMOTE_NOT_VERIFIED`，CPU开发继续但不实际运行。

### P1 — 自主诊断和彻底修好 Shadow 生命周期

- 对现有 `tase/shadow.py`、`E2Context.close`、`retention.cleanup_resources`、Python `multiprocessing.Process` 关闭路径做可观察的时序分析：父发送close→worker读取消息→`native.close()`结束→pipe/worker退出→父join/exitcode。源里不存在的时序不得猜成已测事实。
- 先设计 CPU真实子进程 proxy fixture（无CUDA、GR00T、MuJoCo/模型）重现：正常、接收关闭后慢finalizer、退出0恰与is_alive()竞争、非0退出、SIGTERM忽略、child hung、Pipe EOF、重复close、worker未创建、partial receipt、资源只被本任务关闭。输入固定，重复执行以检测抖动。
- 修复原则是 **cooperative, bounded and observable shutdown**。只在工作进程真正有证据干净退出且最终exit0时标记clean；需要TERM/KILL或没有完整可靠证据时仍报错，不得简单 `except:pass`、仅把join延长到极大时长或忽略exitcode。区分正常但稍慢退出、需要强制终止、timeout、finalizer异常、未知partial；保证幂等，parent Pipe在全部分支安全关闭，不污染policy/robot状态。
- 原真实 run0010/0014 **仍记 CLEANUP_ERROR/exit1**；修复只影响将来。旧帧不得重新消费oracle或补造成功。新增清理日志单独追加到未来新的run，不能回填旧run。
- 独立静态证明变更位于关闭阶段，`worker.predict`、snapshot、frame/event sampling、PolicyClient、动作执行、Gate decision path未变化。如果改到了执行语义就升级到C。
- **完成：**正常/-O CPU专项子进程压力测试覆盖所有故障类、没有孤儿进程或泄漏、失败退出码与收据可信，整套现有CPU至少89测试加新增测试均通过，真正的慢/异常最终可解释，测试日志哈希完整。

### P2 — 同时解决跨版本 TEST 审计兼容（关键，不可略过）

目前两处单版本假设：
1. `scripts/e2_audit_test.py` 逐个旧 reservation 调 `authorize(repo, old_review_commit, old_review_path)`，而 `authorize` 要求**当前HEAD == old授权HEAD**及 old grant== current main；
2. `scripts/audit_epoch.py` 要求所有历史run的 `config_hash == sha256(当前e2_test.json)`。

修复了 `shadow.py` 后，若直接在新的 clean HEAD 审计老14个run，将因 head/hash不一致而误报失败。这不是数据造假，而是审计实现未支持多运行时代。

**Codex 自主实现独立的双模式：**

- **Admission mode（未来新单元）：**继续使用现有严格 `authorize()`；只允许新GPT grant与exact new HEAD，校验新engineered hash+所有科学锁+合法GPU环境。保留120唯一顺序ID与旧14不能重复的规则。
- **Historical audit mode（原有旧单元）：**不从“当前代码已获新许可”推断旧数据；逐run读取自身 reservation/result 记录的 `authorized_head`、grant review_commit/path/blob、原始config/model/split/catalog/nonce hash，并从仓库历史不可变commit和source archive独立核对其**在运行当时**的签署许可。即使旧grant后来暂停，**它已产生的旧证据仍可审核，但绝不能据此再启动新TEST**。禁止用新配置hash覆盖老记录。
- 只将每run原有SHA、status、task、condition、seed、控制轨迹/事件/收据映射到冻结的120-ID输出，不改变原始control/physics/annotation；任何身份冲突须fail-closed而非“跳过”或强行重新签名。
- 旧版本特定证明与新版本自己的原始证据相互隔离；旧14与未来0015+可并存于一份 read-only R3 audit，报告每个运行的code_epoch/config/grant版本。
- **保护统计不变**：`METRICS`、`bounds`、`statistics`、95% paired stratified bootstrap2000/seed640500和 `UAR=N/A` 语义保持逐字节或逐结果等价。两次 CLEANUP_ERROR 在冻住的主分析仍为 outcome_known=false，另外如实报告 operational-failure count=2，不把 `system_error` 的lower0称为无系统错误。
- 使用原始14条raw安全数据+冻结公开subset的CPU回归，验证旧/新审计在合法旧14的行、完整任务结局、状态统计和错误包保留方面一致；旧 grant不能在活跃admission中通过；改过历史文件、重复run-id、伪造grant、新配置冒充旧配置、未备份/缺视频必须失败。真实 original SHA不可使用 synthetic数据顶替。
- **完成：**一个可运行的 `audit_versioned_test.py` 或等价内聚修复+普通/-O测试，能以新HEAD只读审计旧14，无需改旧原件，也不让被吊销的旧R008重新授权新TEST。

### P3 — 一次完整工程 Delta 包交独立签署

Codex 合并 P1/P2 的**工程**代码于独立待审 stacked Head；生成：
- 新完整 `HEAD_SHA`、父commit、changed-files manifest；逐文件hash；说明哪些是 `shutdown`/old-version-audit/hash-only config 变更。
- 完整 normal/-O CPU suite 测试数量/exit/日志；慢/异常子进程收据；旧14原件只读两处SHA；两种 audit一致性与负例；自动检查 `policy/Gate/oracle/TaskSpec/controller/seed/dataset/stats` diff为空。
- 如果 `tase/shadow.py` byte改变而 `e2_test.json.frozen_sha256`未更新，此包**不具备新grant条件**；更新时仅能重算工程变化文件的hash、记录新config SHA，原语义字段与原冻结科学hash必须保持。
- 将执行分支标记 `READY_FOR_INDEPENDENT_RUNTIME_DELTA_REVIEW`。GPT独立核新Head+接口/测试/14条证据和冻结契约；若通过独立签署下一次 `TEST_AUTHORIZED` for exact Head，包含120原始ID并明确已消耗14/首个开放0015的恢复许可。**Codex不可自签、不可修改签署JSON使自己通过。**
- 普通 CPU 开发期间**无需**每个补丁请求 reviewer；只在这个已完成的控制点请求一次。如果 reviewer退修则按具体差异自主CPU修改后再交，不需要用户重新写计划。

### P4 — 新 grant 下长程自主跑完 TEST

先做合法Corelab实时只读资源/原件/dual-env/17模型文件/原来的两处备份、停止进程、TEST已用14/剩余106、grant/currentHEAD确认。若无SSH/资源，Codex可以在允许的范围内自主排查并同时写报告，**不可**使用违规替代账号或私钥或降低主机校验。

取得新grant后，启动一个全新有实际模型ready和loopback监听的server-session，原有server/失败worker不复用。默认只做冻结的下一单元：
`0015=alphabet_soup/init9/C2/B0` → `0016=alphabet_soup/init9/C2/G`，各仅一次；完成0016马上进行第4个init-cluster的源原件/worker清理/状态+RNG+动作/退出/两处备份/逐run版本审计。通过后不等待用户再次发指令，按 **0017…0120** 的原定顺序执行，每4格做自动完整性审计与双备份，不查看效果进行选择/停止。

Valid `SUCCESS`, `TIME_LIMIT`, `SEMANTIC_ABORT` 正常保留，绝不因没有理想风险阳性就换场景。原本14个ID和两次工程失败保留，不重跑、更改状态或把观察的task-success当complete。任何新的RUN一旦reserve、就占其原始ID；失败/中断/无result不能重复消费。无授权不得增加总量120。

工程异常处理采用分类状态机：
- `TRANSIENT_PRE_ADMISSION`（SSH暂断、非侵入目录校验失败等）：原件安全且不触发真实run时可有限重试，记录次数和收据，恢复时重核验身份，不得偷偷占用新ID。
- `POST_RESERVATION_PROGRAM_ERROR`、`SHADOW_LIFECYCLE_ERROR`、`MONITOR_ERROR`、`NATIVE_STATE_MISMATCH`、`AUTH_OR_RESOURCE_VIOLATION`、`UNKNOWN_OUTPUT`：**立即停止真实运行、保留该原ID和失败，转CPU自主修复分支**。更换代码后重新通过 P3 的独立 grant，一次性修全类问题；不要求用户重新下任务。
- `SCIENCE_PROTOCOL_CHANGE_REQUIRED`、`EVIDENCE_LOSS`、`UNAUTHORIZED_ACCESS`：必须请独立owner/reviewer决定，不能自批准。
- `COMPLETED`：所有120原始run ID已有reservation且结果/中断归档清楚，不同于全部成功。生成最终R3资料。

**注意：**一旦新grant签署，之后的正常RUN不需每四格向GPT求一次许可；结构性CPU检查由Codex自动执行。若错误导致可执行代码又改变，新HEAD必须重新签署；这个关口不能被“工程自主修复”豁免。

### P5 — 自主形成R3终局证据与课程交付

- 用固定120计划分母、per-task/C0-C2/B0-G报告 WrongObjectLift、TSR、合规成功、SEMANTIC_ABORT、异常、已执行controls/coverage、模型/monitor耗时、配对初态cluster95%区间，2000 bootstrap seed640500；出现零阳性时UAR=N/A，不写0；unknown/censored给上下界，重复帧不能当独立样本。
- 报告**two code epochs**（旧14 vs post-maintenance）的工程差异和局限；不把维护后版本全称为同一可执行 SHA。科学不变是设计和静态/数据契约，不是宣称两个版本完全同一二进制。区分实际算法Gate vs运行时cleanup、CALIB vsTEST、C2受控指令错配 vs自然OOD风险。
- 执行结束归档全部真实开始/结束、主/Shadow日志、保真安全NPZ/JSON/two-view媒体和两个授权地点完整hash备份；源媒体只在核准的私有目录，公开只有小型审核样本+hash。
- 提交一次 `R3_READY_FOR_INDEPENDENT_REVIEW`（数据完成不足也如实说明缺失），GPT检查独立TEST证据与统计后再决定课程最终结果措辞。
- 在独立report worktree并行起草课程slides（cover+<=15内容页及参考文献）、README/代码zip和最小复现说明；不因制作最终文件而改动冻结运行源码或实验账本。最终提交截止2026-11-06 23:59 SGT。

## 3. 统一状态、交付和沟通机制

仅靠散乱对话不再足够。Codex每个真实阶段更新一个 GitHub issue / PR，并提交**脱敏**状态文件：
`reports/E2/automation/AUTONOMOUS_STATUS.json`：
```json
{
  "phase": "P1_CPU_REPAIR",
  "execution_authorized": false,
  "current_code_head": null,
  "independent_review_grant": null,
  "total_planned": 120,
  "reserved_count": 14,
  "normal_full_outcomes": 12,
  "cleanup_errors": ["e2-test-0010","e2-test-0014"],
  "next_unopened_id": "e2-test-0015",
  "current_incident": "ISSUE18-INCIDENT-003",
  "cpu_test_regular": null,
  "cpu_test_optimized": null,
  "live_corelab_last_verified": null,
  "raw_two_copy_verification": null,
  "missing_evidence": [],
  "next_action": "Bounded self-directed CPU shadow lifecycle repair and mixed-head audit",
  "stop_reason": "R008 grant suspended after repeated cleanup"
}
```
首次文件由实现者生成、后续仅更新新状态并引用旧收据版本；缺信息写 `null`/`UNKNOWN`，不得填 PASS。多种“remaining”口径以**ledger中未预留ID**为准，旧operator `remaining_planned=107`包含已失败0014，不能解释成107次机会。

周期性公开只报**阶段完成和阻塞原因**，不逐日志刷评论：开始、修复与CPU回归达标、申请新grant、成功激活、每个数据信息完整的init组、异常停止、R3 ready、课程交付。每一真实运行都在私有log保留时间/哈希，不可通过普通PR评论取代实际original。

交付层：
- `docs/reviews`：独立reviewer做判断，Codex不能伪造。
- `docs/work_packages`、Issues：任务规划和权限范围。
- `tase/`、`scripts/`、`tests/`：实现和可重复CPU验证。
- `reports/E2`：执行者证据，**不是审核通过的同义词**。
- `private`：完整原始隐私目录/环境/权重和备份，永不公开。

## 4. 接手指令（给长程 Codex Agent）

> 你是该项目的长程执行工程师。不要每次遇到CPU异常就停下询问；在 R010/AUTONOMOUS-E2-ENGINEERING-TO-SUBMISSION 的授权边界内继续调查、修复、回归、备份、提交证据，直到得到可审的新HEAD并申请一次独立授权。此后按签署的精确版本无需逐格批准完成剩余106个冻结TEST，自动checkpoint、备份并形成R3与课程最终提交。旧14永久原状，两次CLEANUP_ERROR不能改/重跑。发现其他工程fault可自主修CPU，但更换真实执行源码就必须停在新grant前，不能自签。所有科学、模型、任务、样本及统计合同不得更改；不突破GPU资源许可。即使任务遇到障碍，也继续推动其他无关阻塞的工作流；用一份公开状态与可审证据明确真实完成/未完成，避免要求用户反复转述历史。

**本文件授予的是长期工作范围和自主CPU工程权限，不会自动创建一个持续运行的后台进程；必须由用户在有执行权限的Codex/Work环境中启动或继续 agent。**

