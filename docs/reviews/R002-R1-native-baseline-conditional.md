# R002 — R1 原生 baseline 续验审核与有条件 M2 放行

Reviewer role: **GPT**。日期：**2026-10-21 / Asia/Singapore**。协议：**TASE-001 v1.0**。

审核对象：PR #3，完整 head **`5e64f2408e4e798d229c0e42761207576abe7e46`**。本记录不覆盖将来的新提交，也不修改历史 R001。

## 1. 决议与授权边界

- **运行资格判断：**提交的代码、公开账本和身份记录支持原生 GR00T–LIBERO baseline 已从“无法加载”推进到“有真实执行与重复任务成功的交付证据”；旧 Cosmos 访问 blocker 不再是当前主要阻塞。
- **下一工作包：`CONDITIONAL_APPROVAL`，仅批准下述 M2 有界开发。**先补证据校验缺口，再开展完整快照、shadow 一致性和独立事件 oracle。执行前置条件见 [M2 工作包](../work_packages/M2-shadow-oracle.md)。CPU 修复和实现可立即进行，满足工作包前置测试后可继续有界仿真；这不是要求每个函数等待一次人工审批。
- **PR 合并判断：`CHANGES_REQUIRED`。**当前 head 的证据校验器有已复现的假 PASS 路径，私有 raw 内容尚未独立核验；本次不合并 PR #3、不关闭 Issue #2、不签署无保留的全量 raw-data 验收。
- **不授权 M3 运行时 Gate 干预/正式校准、M4 TEST、训练、换模型、WBC、实机或任务恢复。**M2 完成交接后再决定 M3；R2 正式实验关口仍有效。
- 已用 **12/24** DEV attempts 不变。M2 本工作包最多新增 **6** 次完整/部分采集 episode 或环境 probe，失败也计入；其余 **6** 次仍保留，不自动消耗。另设最多 **80** 次短前缀 shadow 验证尝试，单独记账，不能伪称新独立 episode 或免预算的完整 rollout。

## 2. 本轮真正做了什么

### 独立执行

通过 GitHub connector 读取固定 head 的源码，在 reviewer CPU sandbox 中按原始 UTF-8 内容建立选择性源码副本；先计算 Git blob SHA-1 与 GitHub 返回值逐文件匹配，再执行测试。直接 git clone 因 sandbox DNS 不可用失败；没有据此声称已克隆或核验整个仓库。

- `python -m unittest discover -s tests -v`：**8/8 PASS，exit 0**；reviewer Python **3.13.5**，不是 Corelab 的 Python 3.12.14。
- 对同一版 `scripts/summarize_baseline.py` 执行 **1 个有效对照＋4 个合成损坏证据用例**：有效对照通过，四个本应拒绝的用例也被错误接受，详见下文。
- 根据公开 CSV 的六行完整 episode 数值重新求和及计算中位数。该操作是公开摘要复算，不是对私有模型输出或物理结果的重新验证。

[Reviewer 检查收据](../../reports/reviewer/R002/checks.json)记录源码 blob 身份、测试范围和数值；[可复现合成探针](../../reports/reviewer/R002/reproduce_audit_gap.py)明确标为 synthetic，不是模型/机器人证据。

### 源码与记录审阅

读取 PR 元数据和文件清单、Issue #2、continuation report、runtime contract、DEV CSV、resume summary、manifest 头部、runtime lock 关键身份、`tase/baseline.py`、`tase/server.py`、`tase/evidence.py`、`scripts/summarize_baseline.py`、`scripts/verify_delivery.py`、`scripts/record_process.py`、安装约束相关源码及八项测试，并对照固定上游 `MultiStepWrapper`。

另外用 GitHub blob 身份确认：成功运行提交 `46b3461…` 的 `tase/baseline.py` 与审核 head 相同（`3700bf72719d00ec323222b4a34ab6ebd37d530f`）；server 运行提交 `5c8d813…` 的 `tase/server.py` 与审核 head 相同（`bcf7354065326f36244314eef30c1c1f91186c1c`）。这支持被审源码与运行记录之间的对应关系。

### 未执行、未访问

没有登录 Corelab、启动 GPU、加载模型、重跑任何真实 episode；没有取得私有 NPZ、视频、原始 server 日志、状态/XML 或完整私有归档；没有逐字节核验全部 118 个公共及 766 个私有 artifact。原始内容仍为 **NOT_VERIFIED_BY_REVIEWER**，执行者的 hash/PASS 不能替代本轮未做的工作。

## 3. 账本复算与可以接受的有限结论

| 任务/初始化 | 结果 | 调用数 | 控制步 | wall seconds |
|---|---|---:|---:|---:|
| alphabet soup / 0 | SUCCESS | 18 | 141 | 10.4533049688 |
| alphabet soup / 1 | SUCCESS | 18 | 144 | 9.2192860609 |
| cream cheese / 0 | SUCCESS | 16 | 127 | 8.4195352639 |
| cream cheese / 1 | SUCCESS | 21 | 162 | 9.7049214221 |
| ketchup / 0 | SUCCESS | 18 | 144 | 9.0474088429 |
| ketchup / 1 | TIME_LIMIT | 90 | 720 | 21.9534146558 |

复算得到 **181** 次成功 policy calls、**1,438** 控制步、完整 episode wall median **9.4621037415 s**、mean **11.4663118691 s**。公开各行与报告汇总一致。12 次 DEV attempts 为 4 环境 probe PASS、2 infrastructure errors、5 policy SUCCESS、1 TIME_LIMIT。

- 5/6 是完整 episode 的描述性成功比例；包含 dtype 错误的 policy attempts 为 5/7；不能把环境 probe 算进成功分子，也不能把 181 个 chunk 当成 181 个独立任务。
- 两个预定任务在两个预定初始化成功，满足计划中的小规模运行资格模式。ketchup/init1 的超时失败保留，不要求为了“全绿”继续刷分；**超时本身不是 wrong-object 事件标签**。
- 代码保留官方 observation/action 路径、实际 16-step 输出与最多 8-step 执行、原生夹爪变换和 720-step 上限。固定上游 wrapper 确实可将时限表示为 done=true，而不是 truncated=true；本地失败仍按 TIME_LIMIT 单列，未因此假报 SUCCESS。
- 发布的 reserved 峰值 6,482,296,832 bytes = **6.037109375 GiB**，准确名称是 **PyTorch peak reserved memory**，不是已测得的整进程/渲染/CUDA 总显存峰值。
- 六个 DEV 样本不证明 TEST 泛化、错误物体风险率或治理效果；20 Hz 是仿真控制频率，不是已证明的实时期限。

证据入口：[固定报告](https://github.com/Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7/blob/5e64f2408e4e798d229c0e42761207576abe7e46/reports/M1/continuation_report.md)、[固定账本](https://github.com/Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7/blob/5e64f2408e4e798d229c0e42761207576abe7e46/reports/M1/dev_runs_resume.csv)、[运行契约](https://github.com/Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7/blob/5e64f2408e4e798d229c0e42761207576abe7e46/reports/M1/runtime_contract_resume.md)。

## 4. 必须修复/约束的发现

### F1 / P1 — 证据校验器对不完整输入存在假 PASS（独立复现）

`scripts/summarize_baseline.py` 只遍历 observation NPZ 中已经存在的 key，没有验证完整 expected key set；reset parity 使用 `all(values())` 而不验证 key 集合；per-run manifest 只验证所列项目，不要求覆盖必需 artifact。

对完整的合成阳性对照分别只施加一种损坏，观察结果：

| 合成变更 | 应有行为 | 当前实际行为 |
|---|---|---|
| 删除 `video.wrist_image` | 拒绝不完整 request 证据 | `request_dtypes_shapes=PASS` |
| observation NPZ 为空 | 拒绝 | `request_dtypes_shapes=PASS` |
| reset parity 映射为空 | 拒绝 | `native_reset_history_parity=PASS` |
| per-run manifest 为空 | 拒绝“已完整验 hash”的主张 | `artifact_hashes=PASS` |

这证明的是 **审计程序不充分**，不证明六条真实记录缺数据或执行造假。原生 policy 的输入校验与离线证据校验不是同一个环节。

修复要求：完整 key 集合、每个决定对应的 observation/action/trace/receipt 与 manifest 覆盖、重复/缺失记录和跨文件身份一致性必须显式验证；增加四项负测试和有效对照，重跑全部现存 raw evidence。不得通过删除坏行、重算旧 hash 覆盖历史或重新跑一条成功替换原失败来“修证据”。

### F2 / P2 — 关键审计依赖 Python `assert`

关键 stage-validation 使用 assert，优化模式可移除这些检查。改为明确异常/检查，或显式拒绝优化运行；提供正常和 `python -O` 下的负测试。`verify_delivery.py` 默认允许私有文件未提供、打印 NOT_VERIFIED 后正常退出属于已声明行为；stage gate 必须有严格模式或额外检查，不能只把 exit 0 当作全量私有证据通过。

### F3 / P2 — 故障时 trace 最后部分可能未持久化

baseline 的 `control_trace.npz` 在每个完整 macro-step 之后才保存；`client.close()` 在最终结果落盘之前，且没有独立异常保护。执行中途或 cleanup 异常可能遗失最新动作/状态或阻止结果写出。当前六条成功完成的执行没有由此被否决；但进入 M2 故障注入前应补 finally/增量 trace 持久化与 cleanup 错误隔离。用合成异常测试，不冒充 GPU/物理试验。

### F4 / M2 设计约束 — snapshot 与 RNG 还没有通过

现存 `get_sim_state()`、settled-state hash、最新观测相等不构成完整 controller/wrapper/RNG snapshot。不得直接将这些字段称为 shadow-ready。

server 只在启动时设置 Torch seed；客户端 reset 不重置采样 RNG。当前 DEV 描述可成立，但后续 B0/G 不可仅凭相同初态或相同环境 seed 声称配对随机流一致。M2 shadow 不得调用 policy、消耗或修改主 policy RNG；未来配对 RNG 方案须在 R2 前单独冻结。

### F5 / 独立证据边界

优先交付已有完整私有 runtime archive 或其必要脱敏子集给 reviewer 可访问的私有附件/授权渠道。至少覆盖全部六个成功/超时 episode 的数值 trace 与 terminal decisions、182 条 server request 记录、退出码、失败 006，以及成功和失败的图像/视频样本。无需重跑、不得将 credentials/内部路径或整包原始日志直接公开到 GitHub。只再提供 executor 的新 PASS 摘要不能关闭独立原件核验项。

## 5. 下一步与合并规则

1. 先在 PR #3 补 F1–F3、CPU 回归测试、新的 append-only 审计报告/manifest；保留旧成果与全部失败。
2. M2 的纯 CPU 实现可并行。满足 M2 工作包的可检查前置条件后，允许其有界仿真开发，不必等待每个 helper 的人工审核；独立 raw-content 核验仍未完成，不能自签关闭。
3. PR #3 未合并时，M2 使用以修复后 PR #3 head 为起点的独立 stacked branch/PR；不要把 shadow/Gate 源码塞进 M1 PR。引用本 main 上的 R002，不覆写 R001。
4. 本次只推进到 M2。M3/CALIB/TEST 未授权；新的阶段放行、PR 合并和最终 R1 无保留确认均须新证据/明确决定。

**结论：这是有价值且足以继续工程开发的真实 baseline 交付，但不是可以跳过证据完整性与 shadow 验证的理由。**
