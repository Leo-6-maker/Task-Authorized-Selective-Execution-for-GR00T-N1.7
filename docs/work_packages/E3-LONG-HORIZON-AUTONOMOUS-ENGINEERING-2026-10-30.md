# E3 / ME6401 长程自治推进章程（2026-10-30 SGT）

> **定位：长期执行工作包，不是 TEST 授权、GPU 资源许可证、科学协议修订或自动后台任务。**
> 用户已明确要求：**普通工程问题由执行者自行修复、验证、提交和归档，不逐项申请 GPT 审核**。保留一项已经在代码中强制执行的边界：**科学协议、精确运行版本及新的真实 GPU/TEST 准入必须分别满足现有独立授权**。不要把本章程解读成 R019 NO_TEST 的撤销。

## 0. 当前固定事实与不可混淆的身份

| 含义 | 当前依据 |
|---|---|
| 独立 ME6401 课程仓库 | `Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7`；不是 GR00T+WBC |
| PR42 计划/报告 Head | `8298bd3fc820289e0343dd84dcd5faccd7d3a5fd`；**不是**原生运行 Head |
| 唯一候选原生运行 Head | `126491066226a0d52968d8bcf363d295781c2684`（PR41）；PR42 对 e3/tase/scripts/tests/configs 代码差异为零 |
| 源码锁 SHA256 | `14abb2ace96424b68a5b0bd25fcc3b897d152fa0eb8efb28ae153de38732b3bc`；141 项 |
| 当前 independent CPU 审查 | R019 `266ce04507a6a430fade03f1dac4ce0f568aca22`：CPU refreeze 与原 0001 同 ID 只读核对通过，**NO_TEST** |
| 原0001 获取历史 | `859e40b5f460365a8853bf3486969e9f8e28951c` / R017 `ca979be10c00389ed57b77967c232d7a84132406`，raw SUCCESS，runner/supervisor exit0；历史冻结审计 exit1/1 永久保留 |
| 最新版本化统计资格 | 0001 新 R018 分析 eligible SUCCESS；全160原定分母内已消费1、未启动159（E3A 余111、E3B 48） |
| 首批 A4 | 0001 历史原件**只读复用**＋只运行0002、0003、0004；首个 checkpoint 目前**未完成** |
| 计划器 | PR42 `reports/E3/R019_EXECUTION_PREP/resume_plan.py` 只读159 ID、28个 A4＋8个 B6 计划；不能申请/执行/占用任何 TEST |
| 现有 GPU1 用户同意 | 已由 operator 私有收据保存，**不等于**新精确 Head 的独立执行 grant；无需对已给出的相同许可反复询问 |
| 当前观察（2026-10-30 22:36 SGT） | GPU1 空闲10,121MiB、总16,376MiB；当前只读 sample，不是资源 reservation |
| 硬约束 | 物理GPU1、UUID路由、EGL1、preload与postload各≥9GiB空闲、最多55% allocator、预留2GiB；无GPU0回退、不碰其他用户进程 |
| E2 正式版 | PR38 `9efba1994235ee0cb844653a45c6f1b0812442a7` 保持独立；E2全120/117 eligible+3 censored，18,070份原件不变；E2 R3仍独立待审 |
| 课程截止 | 2026-11-06 23:59 SGT；**11/06不启动任何实验**；≤15页内容slides（封面/参考除外）、PPTX/PDF、source ZIP README |

以上都是截至本工作包制定时的事实；以后必须在每次交接中标注实际观测时间，不得把过时GPU样本、旧 Head 或旧 grant 当成当前事实。

## 1. 总目标、优先级和自治执行权

**P0（必须交付）**：稳定且真实的 E2 正式课程源代码、slides、引用/AI辅助披露、完整验收与最终提交清单，保持 E2 已冻结实验不受 E3 影响。课程优先，不以 E3 成功为前置。

**P1（条件允许才做）**：在新的、有效的精确 Head `E3_TEST_AUTHORIZED` 和实际资源/时间窗同时成立之后，对原定 FULL160 执行一次且仅一次。首个 A4 是老0001与新0002–0004，剩余各批按4/6格自动通过真实检查点后继续，不在普通成功或普通负结果之间等待人工/GPT。

**P2（科学质量）**：固定 task/init/condition/arm/seed、k3/native16-8-720/settling10、2000次task-stratified bootstrap seed641500，原定160单元永久保留分母，包含所有缺失/失败/未启动；不为获正结果修改实验设计。

**P3（长期科研复用）**：在课程完成后可自主继续 CPU 静态分析、可复现报告、代码可维护性与后续协议草案；不自行开展新的 GPU 研究、训练/WBC/硬件或新任务 TEST。

**核心自治授权（工程，不是 TEST）**：
执行者可以在独立工程分支上自主 triage→最小修复→负向测试→正常/-O完整CPU回归→清单核验→私有收据/双备份→报告PR。路径/权限/环境/依赖/远端运输/日志/序列化/清理/测试夹具/只读仪表板/文档/CI 等非科学工作**不需要逐步回问 GPT**。出错时继续有界 CPU 修复，不要把 `WAIT_GPT` 当默认状态。

**精确运行边界**：
- 运行代码（e3/tase/scripts/configs/tests）发生任何受锁变动，新 commit 不是旧 grant 允许的 Head。可自主完成全部 CPU 工程修复，但不能以旧 grant 重新执行；把全部修复合成一个干净的新 release 后**仅在需要恢复真实 TEST 时**进行一次新版本执行准入。
- 更改科学问题/样本/原始标签/臂/阈值/门/种子/预算/误差定义/统计抽样/资源最低门槛或操作范围，属于 protocol/resource 决策，不得假称工程修复。
- 未有有效 `E3_TEST_AUTHORIZED`、真实 GPU1 资源绑定和合法时间窗：**CPU_ONLY**。不得生成伪造授权文件、修改 `authorize()`、通过环境变量绕过锁或对旧R017进行“修补启动”。
- 原始0001与 E2 原件只读保存，不重跑、不覆盖、不替换 ID；G/A0/Shadow 证据为0时不得宣布 Gate 效果。

## 2. 自治状态机（所有状态必须可从原始收据重新构造）

```text
CPU_READY
  ├─无当前独立TEST grant → CPU_DIAGNOSTICS + E2_SUBMISSION
  ├─grant有效、许可/窗口有效、资源预检不足 → CAPACITY_WAIT_CPU_WORK
  └─准入全部通过 → SERVER_ADMISSION → E3A_0002_TO_0004
       ├─批次审计+配对物理/RNG+完整双备份通过 → A4_CHECKPOINT_RELEASE
       │    └─下个原定A4 ... A112 → E3B_B6 ... B48
       └─异常 → NATIVE_STOP_PRESERVE → CPU_DIAGNOSE → NEW_RELEASE_CANDIDATE
完成全部 → FROZEN_E3_RESULTS → INDEPENDENT_CLAIM_REVIEW → REPORT
课程轨：E2_FINAL_SOURCE → SLIDES_QA → COURSE_FREEZE → CANVAS_OWNER_SUBMIT
```

**不得从异常/超时/未知结果自动回到 RUNNING。** CPU 修好不等于故障 ID 变成未消费；修复版本也不自动继承旧授权。网络断连先定位原远端PID与原账本，禁止盲目重启。

## 3. 可持续的工程自修复循环（不申请 GPT）

**工程工单处理**：

1. 自动分类：`CPU_SETUP`、`TEST_FIXTURE`、`PATH/IO`、`REMOTE_TRANSPORT`、`MANIFEST/HASH`、`RESOURCE_SAMPLE`、`NATIVE_EVIDENCE`、`SCIENCE_PROTOCOL`。前五类通常自主处理；最后两类可能要求停TEST，后者必须独立协议决策。
2. 记录失败的完整启动命令、实际退出码、时间、版本、stderr原件与证据 SHA256（涉及私有路径/UID/UUID的原件仅在私有双备份；GitHub只发布脱敏摘要）。
3. 在**独立可写工程 worktree**做最小变更，禁止直接修改精确运行 detached checkout、已封存原件/锁历史/既有结果。
4. 先做触发失败的 targeted test，并新增可重现的负向回归；随后普通和 `python -O` 全套 CPU，收集 **真实** exits，不仅统计测试条数。原始运行版的完整231项和 PR42 计划器17项可各在相应环境执行；修改任何一侧就相应重测。
5. 每次修复检查 `git diff`、source inventory、来源 commit、锁/配置/科学常数对比；没完成 re-freeze 就只称 `CPU_CANDIDATE`，不能发新的正式运行 Head。
6. 同类型 CPU 故障可有限次修复，失败原因和全部中间日志都留存；不覆盖旧结果、不假造成功。将多个良性工程问题合并为一个有清晰 diff 的 PR，**无需每次修复请求 GPT 审阅**。
7. 只有需要重新获得真实执行许可或科学结果对外主张时，才提交一次**完整、精确版本**的独立准入/结果审核；不按函数、批次或普通 PR 反复审批。

**自动修复止损**：同一故障经过3次有针对性的不同修复仍失败，或没有诊断信息再推进会破坏原件时，将其标记 `CPU_BLOCKED_WITH_EVIDENCE`，切换到其它 CPU 可执行工作及课程交付。不是让执行者一直空等 GPT；也不是授权盲目清理、降低校验或数据重采。

## 4. GPU1 容量调度：先算风险，再满足实际门槛

**当前容量判断**（依据 PR42 2026-10-30 22:36 SGT 的样本，不得当实时保证）：

- GPU1 free `10121 MiB`，total `16376 MiB`；
- preload floor `9 GiB=9216 MiB`，历史R017模型 peak reserved `6392119296 bytes =6096 MiB`；
- 假设历史 peak reserved 近似当前常驻占用，postload free 约 `10121-6096=4025 MiB`，比9216门槛少 `5191 MiB`；
- 推算仅满足历史相近 footprint 的**无安全余量** preload free 至少 `9216+6096=15312 MiB`。此公式只作**保守调度提示**，不能代替实时 postload 检验，更不能假定峰值 reserved 与实际物理显存占用完全相等。

**外层自主调度**：

1. 无新 grant 时，**只读 GPU 查询**、用户已许可的CPU工作、E2准备，绝不“试加载模型看能否通过”。
2. 有新 grant/有效时间窗后，可每15分钟做一次无CUDA查询。若真实空闲小于 `15312 MiB`，优先判为 `LIKELY_POSTLOAD_CAPACITY_BLOCKED`，不为碰碰运气反复加载；此建议阈值可根据实际历史合法收据评估，但**原始pre/post 9GiB硬规则不得更改**。
3. 满足只读风险条件且合法 allocation 记录绑定 Head/grant/Owner/GPU1 UUID/EGL，才调用原生 launcher；仍须从 launcher 与 native server 获取原本的真实preload/postload内存测量，任一未通过即停止。没有GPU0后备、没有对其他任务的抢占或kill。
4. 无法得到足够空闲资源时，不持续占据 GPU、端口或虚拟内存：标明 `CAPACITY_BLOCKED`，记录采样时间、其他作业只读摘要、建议可用时段并切换 E2/CPU。不得把周期性资源查询说成已预约资源。
5. 若多次实测在9GiB postload门槛下因模型占用无法承载，则形成**独立容量分析报告**：同机GPU1错峰/合法独占时段、经所有者明确分配的符合要求的另一台机器（仍只能GPU1、版本/环境重核验）等选项。放宽9GiB/55%/2GiB或切换GPU0必须单独获得允许；不属于执行者的日常修复权限。

## 5. 真正可运行的 E3 原始序列（仅在新 grant + 实时资源全通过后）

- 使用干净的 `126491066226a0d52968d8bcf363d295781c2684` 作为原生运行候选；**绝不**以 PR42 计划报告 Head 启动。计划器输入/输出与原生运行树分离。
- 先重新读原始账本、私有0001同ID核对和新授权，确认当前只有0001已消费、0002未存在、无并行operator、无旧启动PID。若状态与计划不同，CPU重新生成保守只读计划，不自造“可重试”ID。
- 原R017外部控制器假设从0开始且使用过期07:30截止，**不得直接复用**。执行者可自行开发、静态验证并CPU测试新的**外层 operator 编排器**，它只调用已授权的 `e3.server_launcher`、`e3.supervisor` 与真实 `e3.checkpoint.build`，不得实现新的action/seed/场景逻辑，不得跳过任何原生校验。
- 由新的精确版本授权明确给出当前可用时间窗、新ID范围及历史0001重入语义。计划执行 `E3A: 0002→0003→0004`，以旧0001为B0原件构造真实首个A4配对checkpoint，先执行所有审计和两地点每成员及整包hash，再允许0005。若缺视频、进程收据、真实动作/RNG一致性、Shadow关闭或备份证明，**停止新ID**。
- 然后按28个A4完整簇顺序处理E3A至112；A112全部真实闭合后，进入E3B的8个B6簇（每簇C0/C2×B0/A0/G），同样每簇查验与双备份，不能由“程序显示success”自动替代。
- 正常科学结果 `SUCCESS/TIME_LIMIT/SEMANTIC_ABORT` 且真实exit0/完整审计通过 → 继续。低成功率/无baseline阳性/0个拒绝不构成自动调参理由。真实模型、物理、monitor、cleanup、OOM、身份证据、备份等异常 → 消费ID保留、停止新单元、全部诊断CPU；禁止重试、补seed、替换单元。
- 原定 FULL160 分母、task/init cluster、采样2000/seed641500保持。不从E3仅一个B0正常成功推断G/A0、泛化或“100%安全”。

## 6. 双轨时间表与停止预算（绝不让E3绑架课程）

| 截止节点（SGT） | 自主交付 | 准入/停止条件 |
|---|---|---|
| **10/30夜–10/31** | PR42只读计划封存；CPU外层controller负向测试、资源只读采样、E2正式材料QA；整合唯一执行授权请求（如容量有现实可行性） | 无新 grant：0新增 GPU/TEST；无需逐步 GPT 工程审核 |
| **11/01–11/02** | 容量及授权允许时，从0002继续E3A，首个完整A4验证后逐簇推进；每日汇总运行与备份 | 9GiB postload/UUID/完整检查点失败→停新ID |
| **11/03–11/04** | 若A112已闭合并获同一合法范围覆盖，再做E3B48；同时并行统计及E2 R3、slide/ZIP自检 | 任何非工程可恢复的原生错误→停止、留下失败和缺失界 |
| **11/05** | **课程最终冻结日**：E2独立课程slides/PDF、源码 ZIP、原始120审计、引用、AI披露、页数、预览与hash核验；E3只保留审定的单独附件 | 不为E3完成率牺牲已可交E2 |
| **11/06** | **零实验**；检查提交文件与说明，最后由课程所有者向Canvas提交，保存提交回执；截止23:59SGT | 不在课业提交日追加GPU试验 |
| **11/07以后（单独科研轨）** | 可自主CPU维护、source-linked可复现分析、负结果记录、技术报告和下一版科学协议草案 | 新GPU/训练/新模型/新任务/物理硬件均需新协议与资源范围；不自动沿用课程许可 |

这些日期是项目管理优先级，不是抢占机器或超出已获授权时间窗的许可。新执行授权中的真实窗口优先级高于表内建议日期；窗口结束前至少保留足够单元完成/核验/清理时间，不能为了凑满一簇提前占用未来ID。

**若11/02仍没有可满足postload9GiB的GPU1窗口或新grant，项目立即把提交资源优先配置给E2；E3保持诚实的部分结果与资源阻塞报告。**若在截止前只有一部分E3数据，也不删掉其余未启动行，不向E2主结果掺入探索性结果。

## 7. 持续交付、审计与失败处置

每次 Codex 会话/阶段结束，必须先完成以下可机读交接，而不是只说“准备继续”：

```json
{
  "project": "ME6401_TASE_E3",
  "timestamp_sgt": "<actual source-bound timestamp>",
  "runtime_head": "126491066226a0d52968d8bcf363d295781c2684",
  "report_head": "<actual report commit>",
  "source_lock_sha256": "14abb2ace96424b68a5b0bd25fcc3b897d152fa0eb8efb28ae153de38732b3bc",
  "execution_grant": null,
  "GPU1_owner_consent": "PRIVATE_RECORD_VERIFIED_NOT_RESOURCE_RESERVATION",
  "resource_sample_time": null,
  "E3_planned": 160,
  "E3_consumed": 1,
  "E3_versioned_eligible": 1,
  "E3_unstarted": 159,
  "next_original_id": "e3a-test-0002",
  "actual_A4_completed": 0,
  "actual_B6_completed": 0,
  "current_activity": "CPU_ONLY",
  "unresolved_incident": null,
  "private_original_backup": "EXECUTOR_ATTESTED_2_LOCATIONS",
  "independent_private_rehash": false,
  "E2_frozen_unchanged": true,
  "course_submitted": false
}
```

任何报告都应独立展示：**实际命令、原退出码、开始/结束时间、真实资源测量、锁定源码、结果ID、所有已消费/未知/未启动、证明的独立性范围、备份证据和下一步许可**。仅把源文件复制到GitHub不等于私有原件的独立验哈希；旧错误原件不得删除或修改。

保持独立分支：`runtime` 精确冻结且干净，`operator-engineering` 可自主修复，`course-E2` 只读保护，`reports` 新增脱敏报告。避免提交泄漏的HOME、服务器地址、个人UID、真实UUID、private logs、机器许可原文。

## 8. 执行者的长期自治指令（直接交给 Codex）

> 你负责ME6401 TASE课程仓库的长期工程推进。以本文件及最新正式独立review/原始账本为约束。**不要把小工程问题重新交给GPT或用户逐个批准**；自己核查错误、最小修复、加负向测试、运行普通和 `-O` CPU回归、检查source lock和原始不变性，形成新PR/真实退出收据/两地备份和明确交接。不要重复已知的GPU1用户同意问题。  
> 
> 持续在CPU可执行任务间推进，优先完成E2课程提交文件。R019当前是NO_TEST；在新的独立精确Head E3_TEST_AUTHORIZED、合法窗口及新的物理GPU1准入同时成立前，绝不运行模型、MuJoCo、Shadow或预留0002。不存在的独立grant不能自行伪造签发。  
>
> 一旦新的授权与资源都齐备，使用只读计划的159个未启动ID，先0002–0004并用旧0001建立真实A4，然后逐簇自动完成 E3A/B；正常科学负结果继续，真正原生错误永久保留ID并停止新增TEST、转入CPU诊断。所有工程修复均独立分支进行，不通过修改冻结Head绕过旧grant。  
>
> 单次会话能完成多少就完成多少，保存实际收据和下一动作。**不要声称此GitHub文件或聊天会自动在后台运行Codex/SSH**。若未持有持久远端执行会话，只把任务移交给现有有权 operator；不能凭计划制造运行成功记录。11/06零实验，课程提交优先。

## 9. 下一阶段完成定义（DoD）

- **工程自治完成**：普通CPU错误不用等待GPT，原始异常收据保全；每次代码变更有同源test和hash；计划器与运行树严格分离。
- **E3A完成**：原定112/112真实消费、28/28完整A4审计与两地证明，历史0001仅复用一次；异常消耗若存在仍保留在160分母并停止或经独立同ID核对。
- **E3B完成**：原定48/48真实消费、8/8完整B6；B0/A0/G同条件、同初态可配对，无擅自换样本、种子、阈值。
- **研究报告完成**：各任务、C0/C2、每臂结果、未知界、成本、abort、失败与不确定性，bootstrap严格按冻结方案。零baseline阳性时 conditional prevention写N/A；无20Hz实时时限/硬件安全泛化夸大。
- **课程完成**：E2正式版独立且符合slide/source规范，Owner在截止前自行提交并保存Canvas回执，E3研究结果不替代E2项目要求。

**最终原则**：无穷无尽的“GPT小审核”不是自治；伪造TEST授权、放宽安全门槛或重做已消费实验也不是自治。以严格隔离的CPU自修复循环＋版本化执行授权＋真实自动检查点＋期限内可交付成果，取得长期进度。
