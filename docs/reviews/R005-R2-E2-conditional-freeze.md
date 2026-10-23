# R005 — E2 R2 审核：条件科学冻结，TEST 暂不放行

**Review date:** 2026-10-24（Asia/Singapore）  
**Reviewer:** GPT，源代码/公开证据部分独立复核；未登录 Corelab，也未接收约2 GB私有完整原件。  
**Reviewed PR:** [#9](https://github.com/Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7/pull/9)  
**Fixed Head:** `fc38e816ff3e75e87c29da3aa18009dcc0542f02`；**reported CALIB-G runtime SHA:** `03653db11bfb0f570b5e3e6ab78b1a37ef2c9b57`。  
**Protocol:** `TASE-002-v1.0 / E2`  
**Reviewer receipt:** [reports/reviewer/R005/independent_checks.json](../../reports/reviewer/R005/independent_checks.json)

## 1. 审核决定

| 对象 | 本次结论 |
|---|---|
| E2 模型、环境、原生 Gate 机制 | **`SUPPORTED_WITH_SCOPED_EVIDENCE`**：源码审阅、核心 CPU 复验、样本真实数值及报告账本一致 |
| CALIB 结果与预先定义的 `k=3` 选择 | **`CONDITIONALLY_ACCEPTED_FOR_PROTOCOL_FREEZE`**：不修改已提交阈值、标签、任务、split或主要指标；仍是同数据选择/描述结果 |
| M1/M2 历史原件 | `LEGACY_NOT_INDEPENDENTLY_VERIFIED`，不并入E2指标 |
| E2 全部私有原件/488个候选/24个CALIB raw pairs | `PARTIAL_INDEPENDENT_VERIFICATION_ONLY`：公开可核数值已抽审，完整原件尚未由GPT逐条验证 |
| 正式120次TEST | **`NOT_AUTHORIZED`**。目前不存在已经核验的冻结TEST runner；必须先落实本文F1/F2并完成一次小范围 delta-review。 |
| PR #9 | 保持DRAFT/open，不自动合并；本文件不签署全量原件PASS或最终治理普适有效 |

科学配置已具备可冻结的核心：原生GR00T/LIBERO/processor、动作16步/执行前缀最多8步、GR00T策略冻结、任务授权TaskSpec、contact-only Gate、独立wrong-object-lift oracle、`k=3`、C0/C2、30个TEST初始化身份、120个已规划cell、配对cluster bootstrap和零分母N/A。**执行门未放行并不意味着需要新训练、新CALIB或重新下载模型。**

## 2. 独立实际审核——范围具体到什么

### 2.1 GitHub与提交对应

读取[#9](https://github.com/Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7/pull/9)、R2 packet、现行protocol lock、CALIB plan/selection、split/test cell manifest、67身份行、24配对行、DEV实际预测/接触/拒绝记录、四个CALIB first-onset真实数值片段，以及关键执行源码。

对比实际CALIB G源码 `03653db1…` 到交付head `fc38e816…` 的4个commit：变更为报告、CPU导出/总结脚本、TEST提案/协议文件与公开日志脱敏，**无 `tase/` 原生Gate和policy执行代码变更**。这支持报告所说的“交付代码树未在校准后偷偷更换执行算法”；不代替对完整私有运行目录的审计。

### 2.2 运行总账的独立汇总复算

从公开67行身份CSV独立统计，得到67个不同ID：DEV19 + CALIB48；SUCCESS52、TIME_LIMIT9、SEMANTIC_ABORT5、STARTED_OR_INTERRUPTED1；共15,126个已观察主控制步、1,920个模型请求。唯一没有完整`result.json`的`e2-dev-0006`是已记录的537控制步/SIGTERM143；不可因后续诊断完成而删除或视为成功。执行者报告的两个模型7/7、10/10全哈希通过属于**执行者文件字节核验收据**，GPT没有下载超过10GB权重自行重算哈希。

### 2.3 CALIB 配对表的独立复算

24个B0/G配对：
- C0：两臂均11/12官方成功，wrong-lift均0/12；一例TIME_LIMIT/臂，C0成功率差0个百分点；
- C2受控上游指令错配：B0 4/12 wrong-lift，G 0/12；四个配对G在第56主控制步后拒绝，B0对应首次违规在62/148/61/61，四个G均标为SEMANTIC_ABORT而非任务成功；C2官方任务成功两臂均8/12。
- **四个阳性全属于cream_cheese任务的C2**，因此不能称跨任务普适风险防护或自然OOD结论。CALIB也是挑选`k`的数据，不是独立泛化TEST。
- `k=1,2,3` 在已记录CALIB候选集上均给出4/4主事件窗拦截、0/286个C0局部无事件候选拒绝，依事先写入的并列规则选择更大的`k=3`；不声称参数之间存在实证性能差异。

### 2.4 独立读取真实派生片段，而非仅查看汇总

从PR公开文件直接读取DEV配对`e2-dev-0009`（B0）与`e2-dev-0017`（G）的实际物理帧、`prediction-007.json`、接触输入、Gate决策及主状态/RNG守卫。逐步比较57–64控制步的预测与B0实测：EEF位姿、手指位置、物体位姿、左右接触、成功标志和oracle标签 **8/8窗口各字段一致**。G已完成56步，其决策7为REJECT、`completed_controls_before=completed_controls_after=56`，B0首次wrong-lift为60。该例G的开发阈值是`k=2`，**不能把它冒充校准后`k=3`的真实运行**；后者的结果依据CALIB交付而非这个DEV原件。

四个CALIB正例的公开数值点，独立计算在首次事件处非目标对象相对基准抬高约 0.0297–0.0356m，均双指接触；先前一帧均高于0.02m，物体相对EEF移动约0.000023–0.000171m，符合提交的局部高度/携带一致性定义。**只有稀疏帧可独立检查**，并非全时间序列重标注，也非独立视频专家判定。

### 2.5 真正运行的CPU复验

把GitHub固定head的 `tase/gate_features.py` 和 `tase/execution_gate.py` 按源码恢复到reviewer CPU环境，并通过 `git hash-object` 验证与GitHub blob SHA一致（分别`45304283c1e2fb23cb5509f3e78c9ae3d27641e6`和`0a12f72697d3585f226545445eb4620ea1c3f2f2`）。在Python3.13.5普通/-O模式各运行4项定向检查，均PASS：`k=3`跨前缀历史、单步接触放行、非法接触类型拒绝、错误/拒绝零执行与ACCEPT原动作不变。

**未重新执行**执行者46项完整CPU测试、MuJoCo/GPU推理、真实物理接触或全量两个私有归档。不要把上述4项检查宣称为完整46/46独立重跑。

## 3. 需要正确解释的科学结论

**已支持的限定表述：**在E2开发及校准的受控指令错配条件下，执行者数据和公开原始派生证据支持Gate通过预测非目标双指接触前兆拒绝候选，且在已试C0校准初态上未观察到任务成功损失。

**尚不可声称：**真实世界安全保证、自然模型幻觉防护、所有三任务都有违规正例、实机实时约束满足、Gate促进任务恢复成功、跨训练未见分布泛化，或独立TEST效果。特别是一个CALIB违规到第148步才发生，但G在第56步已中止；这体现**更早的未授权接触前兆**，不意味着Gate曾在第56步直接预测第148步的物理抬升。

Gate带来提前终止/减少执行曝光，因此正式效果必须同时报告错误抬升、官方成功、合规成功、semantic abort、错误/超时、执行覆盖及耗时。CALIB的4个独立违规episode不能用其持续接触帧数膨胀样本。

监测耗时报告：中位约107.39ms，P95约1021.99ms（包含worker启动/快照/证据及守卫但不含全部最外层日志成本）；不能声称20Hz硬实时。历史CPU失败日志有非凭据本地路径，当前文件有脱敏派生，但Git历史没有被重写；无已报告凭据泄漏，这属于独立公开信息管理风险，不应悄悄破坏审计提交身份。

## 4. TEST放行的两个必要补件

### F1（必需）：冻结TEST执行/审计代码，并提交无真实TEST运行的负测试

当前`tase/epoch_runner.py`明确只允许`split in ['DEV','CALIB']`，且`configs/e2_protocol_lock.json`为`PROPOSED_FOR_R2_NOT_APPROVED`，拟议120个TEST cell不会自动变成可执行、已验收的entry point。

- 用**单独的小型代码差异**实现`TEST`专属运行入口/ledger及audit：强制读取exact 120-cell manifest、锁定(k=3)、两条件两系统、init内容hash、每场景policy/env seed、16/8/720动作及任务授权；保留原DEV/CALIB结论与配置，不重训、不改变source controller。
- 独立TEST总预算120，**每个失败/中断reservation计数**，重启不能重置或按成功数补齐。TEST不许改k、oracle规则、任务条件、统计或split；C2必须独立保留真实授权与实际policy文字。
- **先做CPU/synthetic**：正确/错误run-ID、错误init hash、重复/缺项/超预算、不完整manifest、监控错误、拒绝零控制步、stop后不再执行、`python -O`、TEST授权标志缺失均有fail-closed检查；不消耗任何TEST cell。
- 产出固定CODE SHA、manifest哈希和可执行audit；**执行前提交delta-review**，新代码不能继承旧head的运行授权。

### F2（必需）：补一份可独立核验的CALIB原件派生包

目前GitHub有119个DEV原件派生文件及四个CALIB阳性事件稀疏数值，**没有由reviewer独立读取的488行候选输入/输出、24组CALIB真实raw pair数组及全程原始日志**。Codex全量机器自审不能等于独立原件审阅。

无需重新跑CALIB或上传2GB私有包；只做CPU导出、哈希绑定并接受小范围独立抽验：
- 488行候选明细：candidate_id、source snapshot/actual-event identity、onset label、三候选决策、时间步、source artifact SHA与分组；重新计算4/4、0/286和选择规则，不只传已经聚合的selection.json。
- 预先固定选样方法导出至少四组阳性配对与若干C0阴性配对的实际动作、转换控制、物理状态/真实接触、Gate预测/拒绝与run/exit receipt，`allow_pickle=False`安全NPZ/JSON；归档写明源文件hash及真实丢失/排除项。
- 若不能上传GitHub，提交授权私有附件；**本机路径不视为可访问原件**。
- 不重写旧CPU失败历史，不为了让审核“全绿”改变原始物理帧、标签或备份。

## 5. 达到F1/F2后如何继续（不要求重做CALIB）

审核新head的TEST执行diff、CPU负测试和补交的有源哈希CALIB小包，确认与冻结协议相同后，GPT发布**单独的TEST运行放行结论**，才执行预登记的120格。验收过程不读取TEST结果选参。

TEST阶段按task和condition给出B0/G事件率与95%区间；按init身份分层配对bootstrap、预设seed/2000重复。全部运行及失败有同样的进程/模型/控制/视频与备份账本；中断等不能默认为没有违规，报缺失及上下界。每个场景拒绝后直接终止、不能从TSR分母删除；零阳性UAR=N/A。

**R005已经条件接受研究配置：只需补齐执行入口与独立原件证明，不允许借此重新挑k=2、更换三个任务、改人工故障定义或重跑CALIB以改善表格。** 若真实证据发现必须修订科学协议，提交新的明确版本及影响分析，再决定是否重跑。

### 本轮未做的事

没有运行TEST、没有编辑模型或Gate代码、没有合并PR #9、没有主动修改Corelab环境或权重/凭据；没有声称我亲自核验了Object7/7和Cosmos10/10的原始多GB文件。
