# R003 — M2 shadow / oracle 审核及定向补验

Reviewer role：**GPT**。日期：**2026-10-22 / Asia/Singapore**。协议：TASE-001 v1.0。

- PR #5 审核 head：`d64cb1002980738f170e3206d004b4a882166543`。
- PR #3 修复父版本：`3e214c0b761d0639bf73948356a92a03bf2ddedc`。
- 报告中的物理运行版本：`16f0249299a11805666f68eb06c09c8f3974efef`；后处理版本：`7b3ccdec283bb565864ffba726d479b13d01de90`。
- 本记录不覆盖未来新 head，不覆写 R001/R002，不合并任一 PR。

## 1. 决议

**M2 的主要工程路径具有实质进展，但本次不签署无保留的 M2 完成或 M3 运行批准。**

| 对象 | 本次处置 |
|---|---|
| PR #3 / R002 修复 | 所审源码修复和针对性 CPU 回归可接受；原始记录独立审核仍未完成，不自动合并 |
| PR #5 / M2 | `CHANGES_REQUIRED`：风险阳性预测覆盖缺口、oracle 输入契约缺口需要定向闭合 |
| 原件交付 | `BLOCKED_EVIDENCE_ACCESS`：两份 ZIP 目前仅是用户 Windows 路径，当前会话没有取得文件字节 |
| 下一执行 | 仅允许本文规定的 CPU 修复及原有预算内 M2 定向补验；不是重跑整个 baseline |
| M3 / CALIB / TEST | 不放行真实 Gate 干预、正式校准或 TEST；设计讨论可继续，不等于运行许可 |

DEV 保持 **18/24**，剩余六次仍保留。本补验 **不新增 policy acquisition、模型请求或完整自主 episode**。允许使用原 M2 **74/80** 中剩余最多六个短 shadow 比较名额，失败也计入；若条件不具备，报告阻塞，不自行扩量。既有资源许可仍需有效，这不是新的 GPU 独占授权。

## 2. 实际审核范围

通过 GitHub connector 固定两个 PR head，阅读父版本的 audit contract、manifest 校验、异常留证及 baseline 接线；阅读 M2 snapshot、shadow worker、主环境集成、TaskSpec、event oracle、审计器、server RNG endpoint、配置、报告和公开 CSV。

在 reviewer CPU 环境中，从 connector 返回文本建立选择性源码副本，并验证七个 Python 文件及一份公开 CSV 的 Git blob SHA-1 与 GitHub 返回身份一致。Git clone 因 DNS 不可用失败，未因此声称克隆/验证了整个仓库。

**真正执行：**10 个父修复针对性合成用例、12 个 oracle / snapshot-helper 合成用例，分别用普通 Python 和 `python -O` 运行，输出一致；复算公开比较表与源 episode 数值。环境为 Python 3.13.5 / NumPy 2.3.5，不是 Corelab 的冻结物理环境。复现和收据：

- [contract_probes.py](../../reports/reviewer/R003/contract_probes.py)
- [checks.json](../../reports/reviewer/R003/checks.json)

**未执行：**完整的 21-method unittest suite、GPU 推理、MuJoCo 物理或 shadow 重跑。**未读取：**私有 NPZ、视频、原始 JSONL、snapshot pickle 或两份 ZIP。不能把执行者的私有重审结论改写成 reviewer 已独立核验原件。

## 3. 已确认的积极结果

### 3.1 R002 的重要修复不是仅改报告

在已核对字节的当前代码上，缺腕部图、空 observation、错误 dtype、空 manifest、重复 manifest 和覆盖缺项均被拒绝；两个有效对照通过。合成的中途 step 异常保留此前成功一步的 trace 和失败记录；cleanup 异常仍执行后续清理并产生 `CLEANUP_ERROR / exit 1`。普通 / -O 结果一致。

父版本 `summarize_baseline.py` 也已显式检查完整 reset-parity key 集合、布尔值和 horizon/history，一并修复了空集合 `all()` 的旧缺口。这个具体分支本轮是源码审阅，不能冒称已独立重跑全部父版本 raw。

### 3.2 Shadow 架构职责清楚

`mjSTATE_INTEGRATION`、controller 缓存、gripper memory、observable/task state、wrapper/history、oracle 持续状态和 RNG 均有明确捕获/恢复路径。独立 spawn worker 只接收 snapshot / action，没有模型对象；主路径始终放行原动作，不用 shadow 修改任务策略。主状态和 server CPU/CUDA RNG 指纹比较实现了相应非干扰检查。

这是针对固定版本、固定 Object 场景的 adapter，不是任意 robosuite 环境的完整状态保证。静态引用排除仍依赖本场景假设；实际原件和覆盖之外状态没有在本轮独立验证。

### 3.3 公开账本的数值可复算

从与 Git blob 一致的 `snapshot_validation.csv` 复算：**24 个不同 snapshot、74 次 comparison、589 个预测控制步**；三次比较各提前结束在第七步，故 `74*8-3=589`。六个源 episode 的公开数值合计 **249 次模型调用、1,985 个控制步、152.757616071 秒**，与报告汇总相符。

24 个快照分层为 13 个无接触接近、1 个 CONTACT、9 个 LIFT_OR_TRANSPORT、1 个时限边界。重复三次不是三个独立任务。报告中的 74/74、最大误差零和 RNG 一致仍属于执行者对私有物理记录的重审结果；本轮验证的是公开摘要及实现逻辑，不是这些物理原件。

## 4. F1 — 关键覆盖缺口：唯一 wrong-lift 没有进入 shadow 比较窗

**优先级：进入 M3 前必须补齐的验证缺口；不表示原 74 次比较错误，也不指控违反原采样协议。**

公开 `event_cases.csv` 的唯一错误物体抬升是 `dev-m2-017`，alphabet soup 相对 cream-cheese 授权，**第 94–170 步**；第 91–93 步为错误抓持迹象。

但同一源 episode 的 snapshot 表只包含：

| 决策索引 | 此前完成控制步 | 实际检查前缀 | 与 94–170 相交 |
|---|---:|---|---|
| d006 | 48 | 49–56 | 否 |
| d009 | 72 | 73–80 | 否 |
| d089 | 712 | 713–720 | 否 |

因此，现有 74 次比较中 **0 个检查窗包含已报告的 WRONG_OBJECT_LIFT**。其他 episode 没有该标签。现在可以说通用短前缀复制取得了开发证据，不能说已经验证“wrong-object 发生前的预测及事件 onset 一致”。第一事件时间被复制到晚期 snapshot 也不是重新预测了当时事件。

这来自预先固定的 C2 `[6,9,89]` 采样和全局 24 快照上限，不是需要反复换模型或制造更多成功数据的问题。正确补法是验证已有失败附近的状态，不是事后把开发快照伪装成盲测。

## 5. F2 — 已独立复现的 oracle 输入契约缺口

**优先级：M3 接线前修复；当前实际物理记录是否受影响不能由合成用例推断。**

`oracle_definition.md` 说非有限观测应为 AMBIGUOUS，缺失/未知证据不能继承持续计数。但 `EventOracle.consume()` 仅对各物体位置做有限值检查；末端位置、姿态、手指状态、接触布尔类型等未完整验证。使用与 head 及物理运行 commit 完全相同 blob 的 oracle，得到：

| 合成输入 | 实际输出 |
|---|---|
| 物体位置 NaN（有效异常对照） | AMBIGUOUS |
| EEF 位置 NaN | 普通 CONTACT / GRASP_EVIDENCE，没有标记未知 |
| EEF quaternion、物体 quaternion 或 finger position 含 NaN | 仍可产生 WRONG_OBJECT_LIFT |
| 接触字段为字符串 `"False"` | 被 Python truthiness 当作接触，仍可产生 WRONG_OBJECT_LIFT |

正常正确/错误目标、禁止 gate 字段、缺失对象、跨 chunk 的第九步 onset、独立数组拷贝等正/负对照表现符合当前定义。

**修复要求：**在改变 oracle 历史之前完整验证输入 schema、shape、有限值、接触类型、合法 step；baseline/参数也需显式验证。非法观测可选择明确失败，由上层记录为 monitor error；或按文档传播 AMBIGUOUS 并清除受影响的持续证据。不得偷偷将非法值转换成正常 `False` 或 NO_EVENT，亦不得抹去历史上已发生的 sticky violation。

修复仅处理数据契约，不借机改变 2 cm / 两步 / 1 cm 参数以增加阳性。对已有全部有效帧生成新派生审计结果，说明标签是否保持一致；旧 raw、标签、manifest 不覆盖。

**影响边界：**`audit_m2.frame_arrays()` 已对正常归档数值作有限/shape 检查，并要求接触为 bool；原生 sampler 也生成 bool。因此本发现不是现有六次采集含 NaN/字符串或唯一事件为假阳性的证据。它是 live oracle 与声明契约不一致，不能仅靠事后 auditor 报错代替执行前验证。

## 6. F3 — 私有原件尚未取得，不能关闭独立核验

用户提供的是两份本机 Windows 路径，不是本会话中已上传的 ZIP。检查当前挂载目录并进行针对性的 Files/Library 搜索后未取得两份原件；没有读取路径另一端电脑的文件，也没有验证归档 SHA。

待核验包：

- `R002-private-sanitized-originals.zip`：声明 SHA-256 `d0d317ee83226ce3dd34a654468636b43deb8cae5a959b4fe628fda5ba3eba98`。
- `M2-private-sanitized-originals.zip`：声明 SHA-256 `859b177e097fab1c88449d30afcf3c2d2175256ecdb795793cc9a517de9737a2`。

实际提供文件后，优先核对归档身份、manifest 和安全 NPZ/JSON 导出，再独立比较指定接触/阳性/边界案例和媒体。不能把附件 pickle 当作可信可执行格式直接加载；不要求把内部原始日志或凭据发布到公开 GitHub。

## 7. 不阻塞 CPU 开发、但必须保留的解释边界

1. **一个事件不是 77 个独立风险样本。** 94–170 共 77 个阳性控制帧，是同一段携带事件；既不证明自然错误率，也不足以估计检测 recall/precision。
2. Oracle 和 shadow 两边使用同一套事件规则。一致证明实现重放一致，不独立证明该规则真的代表物理携带。需对正/负/模糊视频与状态联合核查；当前基于双指接触与相对位移的规则仍是开发代理。
3. `BOUNCE_OR_UNSUPPORTED_LIFT` 不是已确认碰撞弹起；正常释放也可能落入该类。报告已经披露，应继续保持。
4. C2 的逐请求文本未分别落盘。现有源码有明确 override，不能据此宣称 C2 未施加；未来正式实验需保存实际发送指令与可信 TaskSpec 的独立绑定/摘要，禁止事后补造旧日志。
5. 一次 M1/M2 141 步完全一致不等于已建立 B0/G 随机配对。后续需冻结每场景随机流与执行语义，并单独测 governor latency；当前 episode wall time 不能当 Gate 开销。
6. 此时没有真正 Gate 拒绝，不报告治理收益、UAR 或安全保证。WBC、额外训练、实机仍在范围外。

## 8. 定向补验工作（替代无边界重跑）

### A. CPU 先行

Codex 修复 F2 并加入上述负样本及有效对照；普通/-O 均验证。对既有 M1/M2 有效原件重审，保留版本身份和差异；将缺原件问题与代码检查失败分开记录。准备真实附件，不上传内部资料到公开仓库。

### B. 使用旧动作补正例预测，仅消耗剩余最多六个 shadow case

在所需原件及有效资源许可具备、输入契约修复通过后，允许专门做以下 M2 开发诊断：

- 从 source 017 已保存的 **d009 完整 snapshot（72 步后）** 恢复到独立模拟器。
- 只回放已保存的原生 action，推进到 **d011 前（88 步后）** 和 **d012 前（96 步后）**。不重新请求 GR00T。
- 对两个边界各做最多三次、每次最多八步的预测比较：覆盖 **89–96 的首次错误抓持/抬升**与 **97–104 的持续携带**；实际 event onset 应与原件记录核对，不预先伪造通过。
- 确定性历史回放必须先与原始 control/state/physical-frame/oracle 证据对齐，完整记录 worker setup、历史 replay 控制步与预测步。不能从旧 flattened state 直接声称恢复了缺失的 controller 历史。
- 新的两个边界标为 **RECONSTRUCTED_FROM_FULL_SNAPSHOT_AND_SAVED_ACTIONS / DEV_DIAGNOSTIC**，不是旧采集时保存的原始 snapshot，也不是独立 TEST。用单独 supplemental config/report，保留原 24/74 表不变。
- 含失败总比较数不得超过原 80；不新增自主 episode，DEV 保持 18/24。若确定性回放无法对齐、原件缺失、六次用尽或需要新增推理，停止并报告，不从保留六次 DEV 中自行取用。

该补验只弥补已知事件的覆盖，不用于估计泛化或事后选择正式阈值。条件通过、原件独立审核完成后提交新的完整 head，再决定 M3。

## 9. 总结

**不推翻现有基线或 74 次通用一致性结果，也不要求为得到更漂亮的成功率重新训练。** 所审父修复已实质改善证据链；M2 给出了可用的状态复制/隔离预测结构。现在差的是一个关键阳性窗口验证、一个明确的输入契约修复，以及真正可访问的原件。先闭合这些，才能把“能做预测”推进为“可以开始验证任务授权 Gate”。
