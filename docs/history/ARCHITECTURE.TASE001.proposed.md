# 原生动作链、Safety Gate 与实施契约

协议：TASE-001 v1.0。本文是待实施设计，不表示下列模块已存在。官方代码依据见 [SOURCES](SOURCES.md) U2–U5。

## 1. 集成边界

```text
真实 LIBERO 状态
  ├─ 官方观测处理 → PolicyClient → 冻结 GR00T PolicyServer
  │                                      ↓
  │                              native action dictionary
  └─ 完整快照 → PrefixResolver ← policy/horizon contract
                      ↓
       前缀 + 快照 + TaskSpec + 版本身份
                      ↓
            ShadowRollout → ObjectGuard
                      ↓
               ExecutionGate
            ACCEPT          REJECT/ERROR
               ↓                 ↓
       原生 wrapper.step    不推进主仿真
               ↓            结束自主 episode
      Panda controller / MuJoCo
```

放置位置是 **已解析“将执行哪些动作”之后、主仿真第一次 step 之前**。具体包裹 `MultiStepWrapper` 的方式由 Codex 按固定源码确认；不能先调用会推进整块动作的 `env.step(chunk)`，再检查已发生的事件。

首版 batch=1、单环境、同步推理与执行；不采用异步 action queue 或多环境 autoreset。若复用官方 vector runner，必须证明 final_info、终止后 reset 和 action 数量不会使 Gate 被绕过，否则采用等价的单环境薄 runner，并用 baseline parity 证明等价。

## 2. 不改变的原生语义

GR00T 的 Object post-trained checkpoint 与其 processor、statistics、embodiment 一起冻结。不得把旧项目 EEF trajectory、rot6d、H40 或 WBC 阈值带入本系统。

固定源码显示七个 action stream 拼接为七维输入，夹爪经过 normalization 与 inversion 后进入底层环境；观测有双相机，夹爪状态是两维，名为 roll/pitch/yaw 的三个状态由 axis-angle 转换得到。字段名不是物理语义证明，须记录实测和源码位置。

**模型动作的坐标增量、控制缩放和控制器参数还需 M1 核验。** 不假设 action.x=米；不对原始归一化动作直接套速度阈值。

## 3. RuntimeContract 必填字段

| 类别 | 字段 |
|---|---|
| 模型 | repo、revision、suite子目录、各权重/processor/statistics文件哈希、推理精度和模式 |
| 软件 | 本仓库SHA、GR00T SHA、LIBERO/submodule SHA、robosuite/MuJoCo版本、所有patch |
| 输入 | camera keys/尺寸/dtype/方向、state streams/维数/单位/姿态语义、语言字段 |
| 输出 | action keys/order/dtype/实测shape、model/config/modality horizon及相互关系 |
| 执行 | H_e、control frequency、每个action的控制语义、夹爪映射、wrapper栈 |
| 时间 | simulation steps和wall time分别定义、初始化settling、max inner steps、终止规则 |
| 随机性 | policy/env/perturbation独立seed、RNG恢复与请求顺序、非确定性说明 |

`H_e` 起始候选为8，但从运行契约验证并冻结，不能仅根据历史报告硬编码。`H_model=40`、modality offsets=16 与实际输出长度是不同概念；首版发现矛盾即停止查因。

## 4. 统一动作转换与检查-执行绑定

建议定义不可变 `ActionPrefix`，包含原始动作副本、实际执行步数、字典键顺序、wrapper版本和内容哈希。主环境和shadow必须使用同一转换函数且各转换一次。

上游夹爪工具可能原地修改数组：传入独立副本，执行前后比对原候选哈希。禁止 shadow 把已归一化动作再次送入 wrapper，或主环境使用了不同版本动作。

`GateDecision` 绑定 `episode_id / decision_index / state_digest / prefix_digest / taskspec_digest / protocol_digest`。只有同一候选、同一状态的 ACCEPT 可消费一次。状态变化、候选变化、超时或重复消费使许可失效。同步首版中仍需测试这些不变量，避免后续并发引入绕过。

可读伪代码（不是现有 API）：

```python
obs = observe_native(main_env)
action = frozen_policy.get_action(obs)
prefix = resolve_exact_prefix(action, runtime_contract)
snapshot = snapshot_complete(main_env, runtime_state)
decision = governor.assess(snapshot, prefix, trusted_task_spec)
write_decision_or_abort(decision)
if decision.kind != 'ACCEPT':
    finish_episode(reason=decision.kind, task_completed=False)
else:
    assert_decision_bound_to_current_state(decision, main_env, prefix)
    execute_native_prefix_with_step_events(main_env, prefix)
    record_actual_outcome()
```

未成功持久化决策或无法完成检查时不继续推进主环境。执行期间发生异常则记录 `PARTIAL_EXECUTION_ERROR` 及实际步数，不能称“全部阻止”。

## 5. TaskSpec 与信息权限

每个任务映射可信授权目标、目标容器、被监测非目标对象、底层body/geom/site身份、允许的上下文接触和官方成功predicate。对象名单来自该任务固定BDDL，不由模型动态猜测。

| 信息 | VLA | Gate | Evaluation oracle |
|---|---|---|---|
| 原生图像/状态/任务语言 | 是 | 按需 | 按需 |
| 可信授权TaskSpec | 只保留原生语言输入 | 是 | 是 |
| 对象真值/完整仿真状态 | 不增加 | 是 | 是 |
| 故障注入标志/替换后语言标签 | VLA仅收到其本次输入 | 否 | 仅实验元数据 |
| 未来实际结果/事件标签 | 否 | 否 | 是 |

C2 故障条件下，可信授权任务和传给VLA的指令可能不同；Gate不得读取该差异并直接做字符串匹配。本研究测试的是动作授权边界，不是文本比较器。

## 6. ShadowRollout

### 6.1 状态内容

逐项审计模型XML/assets、仿真积分状态、qpos/qvel之外的控制输入/执行器状态、控制器目标/插值/积分器、夹爪、wrapper缓存和时间、随机状态，以及需要跨动作块延续的事件历史。不能假定一个 `set_state()` 覆盖所有Python状态。

### 6.2 预测长度

只预测将要执行的前缀 `a[0:H_e]`。末段因episode budget或成功终止实际短于H_e时，shadow和主路径遵循同一停止规则并记录实际长度。第H_e之后的假想动作不参与主要许可判断。

影子物理状态来自真实完整快照，不从模糊图像估计；C1仅影响VLA观测。因此实验验证的是可靠特权状态条件下的治理，不是完整视觉安全系统。

### 6.3 一致性验收

至少20个开发快照，覆盖接近、闭合、接触、抬升和搬运。相同快照＋相同前缀分别运行shadow和主执行路径：比较机器人、物体、夹爪、接触时间、事件和终止。

建议起始数值容差：末端/物体位置最大差≤0.1mm、姿态≤1e-3rad；这些仅为开发候选容差，需记录分布并在校准前审核固定。关键错误物体事件结论须一致。任何放宽要有差异来源说明，不能为“过测试”悄悄调整。

另外必须证明：shadow不改变主环境状态、控制缓存、episode计数、图像处理、NumPy/Python/Torch随机流及后续policy输出。`shadow-on / always-accept` 应在同一输入/随机流下复现 B0；没有这项证据不得声称治理效果来自Gate本身。

## 7. ObjectGuard v1

输入：shadow前缀逐步状态、可信TaskSpec、已校准余量m。输出：风险特征、触发对象、触发时间和允许/拒绝。

候选特征为：在夹爪闭合或保持抓持的预测时刻，夹爪抓取区域与指定非目标对象之间的最小距离 `d_min`。抓取区域使用经可视化审核的工具坐标包围体，不能用整个Panda机械臂包围盒替代。

```text
if predictor/mapping/contract invalid: MONITOR_ERROR
elif d_min < m: SEMANTIC_REJECT
else: ACCEPT
```

实现需写清距离为signed separation或明确的overlap谓词，尤其m=0时的相交行为；不能用永远非负的clamped距离配 `<0` 导致零余量永远不拒绝。

余量候选：0、5、10、20mm；边界等号语义、闭合判定、包围体和距离算法在校准前固定。实际夹爪开闭方向由M1测试确认。

正常抓取/抬升/绕行不保证目标距离单调下降，故不以“无进展”拒绝。不在第一版增加复杂risk权重、任务恢复或低层控制。

## 8. 拒绝语义与终止

- `ACCEPT`：执行同一已检查前缀，可在官方成功首次发生时提前结束。
- `SEMANTIC_REJECT`：不执行该候选；自主episode结束；若此前尚未成功，记未完成。
- `MONITOR_ERROR`：检查器无法作出有效判断，结束运行，单列可用性失败，不当作成功检测。
- `TIME_LIMIT`：同一inner-step上限，未完成计失败。
- `POLICY_ERROR / ENV_ERROR`：单列基础设施或策略异常，不静默删除。

不发全零“安全动作”，不突然开爪，不调用未经验证的hold，不在同一状态反复查询模型。仿真停止不是实机安全保障。

## 9. 必测不变量

1. 拒绝/异常后主环境 `step` 调用数为0，且状态未推进。
2. 接受前缀与检查前缀内容一致；转换无重复、原动作无原地污染。
3. stale decision、wrong task、wrong state、候选修改、重复消费均被阻止。
4. horizon不足、NaN、缺对象和超时不会自动放行。
5. B0与G共用基础格式检查、控制器、初态和终止规则。
6. shadow不改变主环境/随机流；oracle不读取gate分数。
7. episode截断、首次成功、最后不足H_e步和跨块事件计数正确。
8. mock测试与真实runtime测试分开报告。

## 10. 模块交付建议

`policy_adapter.py`、`libero_adapter.py`、`runtime_contract.py`、`task_spec.py`、`snapshot.py`、`shadow_rollout.py`、`object_guard.py`、`execution_gate.py`、`event_oracle.py`、`audit_logger.py`。不大规模fork GR00T内核；必要patch保存在独立目录并记录base SHA、diff和hash。
