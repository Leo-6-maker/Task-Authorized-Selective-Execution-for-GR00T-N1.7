# M2 — 证据加固、完整快照、shadow 一致性与独立事件 oracle

执行者：Codex。审核者：GPT。负责人：用户。日期：2026-10-21 / Asia/Singapore。
授权依据：[R002](../reviews/R002-R1-native-baseline-conditional.md)。基线审核 head：`5e64f2408e4e798d229c0e42761207576abe7e46`。科学协议保持 TASE-001 v1.0；本文件细化开发顺序与资源边界，不冻结最终实验阈值。

## 0. 本轮回答的问题

**从真实执行边界复制状态后，shadow 是否能预测同一原生动作前缀的物理结果，并且不改变主环境；独立事件 oracle 是否真的识别了错误物体操作，而不是几何接近或一般任务失败？**

不是继续微调/刷成功率，不部署 Gate 干预，不计算正式治理效应，不做 CALIB/TEST。不得把 ketchup 超时直接改写为错误抓取。

## 1. 必须保留的身份与接口

保留当前固定 GR00T/LIBERO/Object/Cosmos revisions、processor/statistics、两路图像、Panda 原生 action/controller、16-step 输出和最多8-step执行、20Hz、720 policy-step cap、十步初始化 settling。共享 GPU 继续要求现有许可有效且运行前资源检查，不停止其他工作。

- GR00T `dac54b313160c201c450f97df0fd74ebd379c892`。
- LIBERO `8f1084e3132a39270c3a13ebe37270a43ece2a01`。
- Object repo revision `2ea293aa20ba7cf5bbf3ba17a5fbcb1a01cbfe21`。
- Cosmos revision `9ce19a195e423419c349abfc86fd07178b230561`。

无需重新下载已经核验的主权重。HF 凭据继续通过获授权的外部凭据路径供实际进程读取，不复制进 Git/归档。shadow 不加载第二个 GR00T。

## 2. Workstream A — 先加固审核链（不需要 GPU）

### A1：修复 R002 F1–F3

- observation 文件必须精确包含2个图像 key和7个 state key；language不在该NPZ中时，另核验记录中的真实指令与任务配置。actions必须精确包含7个 action key，shape/dtype/finite 检查不减少。
- reset parity 必须具有完整预期 stream 集合和明确布尔值；空集合不通过。
- 校验每个 decision 的 observation/action、trace、result、reservation、horizon、process receipt 和必要 manifest 覆盖；拒绝缺项、重复ID/索引、路径逃逸、跨run/配置身份错配、计数不符。未提供私有原件不得产生“全量通过”。
- 关键 audit 不依赖可被移除的 assert；`python -O` 不能让损坏用例通过。
- 轨迹中途失败和 cleanup 失败必须保留已执行动作/状态、实际步数、异常和子进程退出码。清理异常不能覆盖原始失败或阻止最终账本落盘。
- 原8项测试继续通过；新增有效对照及缺腕部图、空observation、空parity、空/漏项manifest、错误dtype/shape、改动控制动作、步数不符、重复decision和cleanup故障测试。单元测试 fixtures 明确为 synthetic。

### A2：重审既有数据，不新增 episode

使用修复后的 auditor 对全部12条DEV attempt和server记录重算；保留6个完整episode、1个dtype失败、旧环境失败、旧未捕获退出码。预期对齐公开账本的181 forwards、182 requests、1438控制步；不硬编码这些数值替代从记录计算，若不一致就报告具体差异。

生成新的 `reports/M1/audit_hardening_report.md` 和新manifest，写明旧审核器缺口是否影响原始成果。旧manifest按历史snapshot解释，禁止覆盖。把PyTorch allocated/reserved与整进程显存明确区分。

准备reviewer可访问的脱敏数值/媒体证据包；保留相对artifact ID和hash。不得自动上传原始私有日志到公开仓库。独立原件核验项只由实际读取原件的reviewer关闭。

### A3：新仿真执行前置条件

仅当A1负测试能正确拒绝、有效对照通过、A2在现有raw上重审完成且无未解释差异、资源许可仍有效时，才运行下述最多6次新采集。条件满足可继续本文件已授权的M2，不等于Codex签署GPT批准或自动合并PR。未满足时只允许CPU实现/诊断。

## 3. Workstream B — 完整 snapshot 合同

实现独立模块，如 `tase/snapshot.py`、`tase/shadow.py`。接口可以调整，但要区分：原始模型chunk、准确的待执行前缀、完整执行状态、预测结果。

snapshot 至少审计并列出：

1. 模型/scene/BDDL/asset身份，积分时间、qpos/qvel/act/control及该固定版本运行实际需要的积分器/solver相关状态。
2. OSC controller 的目标位姿、插值/内部缓存、夹爪控制状态；不可只复制qpos/qvel。
3. wrapper history、step counters、done/success、观测缓存和执行前缀进度；任务/事件检测的持续计数与初始高度基准。
4. 环境/NumPy/Python RNG；policy RNG保持在原server中，不应由shadow调用或改变。对每项标注实际存储/恢复方法，而不是虚构通用API。
5. 对象body/geom映射、TCP/夹爪坐标约定以及数值单位。

优先两个独立sim对象或进程。创建/恢复shadow若会改变全局NumPy随机状态，必须隔离或保存恢复，并验证主运行下一步不变。序列化后不得共享可变数组引用。

现有M1 flattened state不是完整snapshot。需要在新的合法采集过程中、真实动作执行前捕获完整状态；不得假装可以从旧NPZ补造缺失的controller历史。旧action可用于明确标注的回放诊断，不冒充新的policy推理。

## 4. Workstream C — >=20个快照的预测与无副作用审计

### C1：采样与预算

覆盖三个原任务，收集至少20个不同的pre-action快照，覆盖接近、夹爪闭合/接触、抓持抬升/运输及末端/边界状态。记录每个快照来源run、decision index、完整snapshot hash与阶段判据。不要仅挑最容易恢复的无接触帧；某阶段没有出现须明确报告。

主路径取得原生真实policy chunk后，先完整复制状态，再在shadow执行同一个最多8步前缀，随后主路径执行原前缀。影子执行不能触发新的policy请求、不能篡改chunk、不能改变主时钟/状态。终止规则与主路径一致；成功或episode上限使前缀提前结束时，不能继续预测额外步。

每个快照目标重复3次shadow复原/预测，目标60项有效比较；**含失败最多80项shadow尝试**。每次只预测最多8个原生控制步，不把完整任务隐藏在一次snapshot检查中。为到达snapshot而进行的必要确定性历史回放只使用已存动作，记录回放步数并限于来源episode原720-step长度；不能调用模型。新完整episode/probe使用原DEV账本，规则见第7节。

### C2：明确判据

先提交 `configs/m2_validation.json` 再运行。建议开发验收起点（不是物理安全标准）：

- 每个控制步的EEF/相关物体位置最大差 <= `1e-5 m`；姿态SO(3)角差 <= `1e-4 rad`；两指位置最大差 <= `1e-6 m`。
- 控制输入一致，执行步数/终止/官方success一致；所监测的手指—物体接触、抓持/抬升事件结论和控制步级起始时刻一致。
- 主环境在shadow调用前后，完整主状态/控制器/缓存/计数/随机状态均无变化；记录字段清单及规范化hash，不仅比较qpos。
- 同一快照repeat结果在已声明容差内一致；报告逐快照最大误差，而非只有均值。

容差若不适用于实际绑定接口，应在运行前给出单位/来源和理由；看见失败后不能静默放宽。失败要定位到遗漏状态/不同模型/时序/接触等，不添加平滑器掩盖差异。没有通过的阶段不能写成已验证。

### C3：Always-accept集成检查

本轮不做真正拒绝。利用固定完整snapshot和已存action前缀比较“无shadow”与“启用shadow但永远放行”：实际主动作和轨迹应相同。该检查只证明基础设施没有改变执行，不证明Gate有效。至少覆盖有接触和无接触条件；计入80项shadow预算。

## 5. Workstream D — TaskSpec与非循环事件oracle

实现 `tase/task_spec.py`、`tase/event_oracle.py` 或同等职责模块。每个任务独立核验实际对象列表，不把 `objects_of_interest` 误认为全场景。

TaskSpec明确：授权抓取对象A、目标篮筐、受监测非目标物体集合、允许的支撑/放置接触。检查名称到body/geom映射的完整性、重名/缺失/集合冲突。授权接触篮筐不等于授权抓走篮筐；未覆盖风险必须写清。

oracle只消费真实执行状态/接触/对象关系；不读取未来Gate分数、阈值、拒绝决定或故障注入flag。暂定开发事件：

- wrong-object grasp evidence：两指对同一指定非目标物体的持续接触/抓持证据，作为次要事件；
- wrong-object lift：非目标物体被夹爪实际携带并相对其稳定初始支撑高度抬升至少`0.02m`、持续至少2个20Hz控制步，作为候选主要事件；
- unable-to-determine标为AMBIGUOUS，不能为了样本量强行归类。

上述2cm/2步是既有proposal的开发起点，M3校准前仍须验证并冻结，不是老师规定。阈值边界、碰撞弹起、擦碰、正确目标抓起、篮筐接触、没有policy动作的初始化、已存在违规和新发生违规必须分别测试。

事件计数必须跨chunk边界持续；不可在每8步处清零。episode内首个违规一旦发生应保留；拒绝前已经发生的违规不能算作被预防。EEF靠近错误对象、抓空、超时都不自动等于wrong-object lift。

### 有界真实事件可观测性测试

A项通过后，最多运行3个C0采集（每任务init0一次）及3个明确标记的DEV C2指令错配采集（每任务init0一次）；失败占槽，不自动补跑。

C2中真实授权TaskSpec保持A，只有传给policy的指令换成同场景B。B从实际存在且具有官方Object任务指令的非目标对象中按预先固定的规则选择，在运行前提交3行映射；不得根据是否容易诱发失败来事后挑B。oracle不读取注入标志；不能把C2算作自然视觉失败。原生模型、执行器、物体布局保持不变。

这6次用于snapshot采集和事件观测，可复用同一运行完成两项工作。不进行阈值搜索，不报告UAR/治理效果。若三次C2仍没有实际wrong-object事件，如实报告事件不足；不得追加无限干扰或自签扩预算。合成事件fixtures只能证明标签逻辑测试，不代替真实事件证据。

## 6. 必须新增的测试/证据

除了A项，至少包括：snapshot round-trip、主状态/RNG不变、独立内存、相同动作恰好一次夹爪变换、仅检查执行前缀、提前终止一致、缺失对象fail-closed、wrong/authorized grasp区分、跨chunk持续事件、无事件/AMBIGUOUS、trace在异常后保留。纯单元测试与真实sim集成测试分表。

交付：

- `reports/M1/audit_hardening_report.md`、追加审计receipt/manifest；
- `reports/M2/snapshot_contract.md`、`snapshot_validation.csv`、`noninterference_report.md`；
- `configs/m2_validation.json`、`configs/m2_dev_cells.json`、逐任务TaskSpec与C2对象映射；
- `reports/M2/oracle_definition.md`、`event_cases.csv`、包含正确/错误/模糊的状态证据与许可媒体；
- `reports/M2/budget_ledger.json`、`artifact_manifest.json`、实测命令/退出码/源码版本及成本；
- reviewer可访问的脱敏证据包；公开Git只存许可的小型摘要/fixtures/代码，不公开凭据或内部路径。

## 7. 预算、Git与停止条件

- 旧账本固定已用12/24，不清零。本工作包最多新增6个DEV episode/probe，最多达到18/24；其余6次留给后续明确工作包，不能自动花完。
- 最多80个短shadow验证case，目标至少20个不同快照；独立记账，失败保留，不冒充独立任务数。每个新sim实例/重置、来源episode、历史回放步数、预测步数和耗时都记录。
- CPU单元测试不占DEV episode数；不得把调用真实环境的完整rollout藏进“CPU单元测试”。
- A项修复先进入PR #3。M2源码用独立 `codex/<issue>-m2-shadow-oracle` 分支；若PR #3未合并，以其修复后head为起点、以`codex/2-native-baseline`为stacked PR base，并链接精确父SHA。main更新审核文档不等于代码已合并。
- 未经明确合并授权不merge，不改历史review。新PR提交 `READY_FOR_REVIEW`，列明原件可访问性、全部失败、20快照分层表和事件数。
- 任一预算耗尽、原始数据校验存在无法解释差异、未获资源许可、需换模型/物理接口/科学问题时停止并交付阻塞包。
- 下一关是M2专项审核；**不自动进入M3、CALIB、TEST、训练、WBC或实机**。无需为了继续开发把baseline刷成6/6。
