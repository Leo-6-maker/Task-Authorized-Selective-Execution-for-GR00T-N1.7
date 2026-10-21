# 执行、资源与可复现性手册

本文面向 Codex。当前尚未有本地运行收据；以下是实施步骤，不是已验证的一键安装承诺。先读 `AGENTS.md` 和当前执行issue。

## 1. 开始前

确认当前仓库/分支、授权工作包、资源许可及剩余时间。不得从公开仓库猜测内部SSH路径。仅使用用户已提供且获授权的连接；无连接时先完成CPU侧工作并报告阻塞，不编造部署结果。

只读检查：OS、Python、uv、驱动、GPU实际可用量/负载、EGL vendor、RAM、工作目录所在磁盘和空闲空间。记录脱敏资源类型与统计，不公开机器名、IP、账户、其他用户进程命令或环境变量。

资源初始规划：单GPU模型推理、CPU物理、EGL双相机、单主环境＋单shadow。不因为有剩余显存就占用他人运行时段。磁盘可按60–100GB规划上限核查，但这不是实测最低要求；实际选择性下载和记录量需测量。

## 2. 运行身份

候选上游源码：`NVIDIA/Isaac-GR00T@dac54b313160c201c450f97df0fd74ebd379c892`。本次规划已读取该commit的LIBERO wrapper、rollout入口和setup脚本。

历史审查给出的候选模型revision：`nvidia/GR00T-N1.7-LIBERO@2ea293aa20ba7cf5bbf3ba17a5fbcb1a01cbfe21`，子目录 `libero_object`。此revision来自先前审查，不代表本轮下载或组合兼容性已验证。M0必须查询、核对文件并固定；若不可用或不兼容，提交替代身份与原因，不静默退回浮动main。

实际锁定清单包括：本仓库SHA、上游SHA与submodule、模型revision与文件hash、processor/statistics、控制器配置、Python/依赖lock、CUDA/驱动、GPU类型、MuJoCo、renderer、随机种子和所有patch。

不要在正式测试中 `pip install -U` 或追随上游main。

## 3. 隔离安装

推荐目录结构（占位路径，不是既有内部目录）：

```text
$WORKSPACE/
  course-repo/
  upstream/Isaac-GR00T/
  runtime/                 # 本项目独立环境/受控配置
  checkpoints/             # 只下载Object推理必需文件
  cache/
  runs/                    # 大型原始运行数据，不进Git
```

固定源码后先检查官方setup全文。候选版本会重建自己的 `libero_uv` 并删除用户 `.libero` 配置；不得直接在日常HOME与共享科研目录执行。采用隔离HOME/容器或经过审计的配置路径patch；必须确认所有写入/删除路径只属于本项目。保留patch diff和sha，不能边安装边无记录修改依赖。

官方setup在该候选版本使用Python3.12、MuJoCo3.3.1等固定依赖。以实际固定脚本为准，不把旧LIBERO安装说明与GR00T主环境直接混装。保存模型server环境和sim-client环境各自的依赖记录。

模型按官方方式选择性获取：config、embodiment、权重shards/index、processor、statistics及实际加载需要的小型元数据；不下载训练optimizer或整个仓库。记录官方许可证，不重新分发模型。

先检查EGL渲染，再加载大模型。`CUDA_VISIBLE_DEVICES` 不自动证明EGL使用了同一设备；记录两者实际绑定。

## 4. 原生baseline最短路径

### M0-A：静态检查

核对Object权重目录、模型类型、embodiment、全部依赖、所需task注册与本项目输入输出记录接口。运行官方入口的 `--help` 并保存实际CLI，不编造未存在参数。

### M0-B：环境检查

单任务reset，输出两路原生图像，保存经过审核的小型截图。确认图像方向、尺寸、色彩、对象存在和观测state形状。记录控制频率、controller与action contract。

### M1-A：真实模型推理

候选上游启动形式（需Codex在固定版本验证，不是本仓库现成脚本）：

```bash
uv run python gr00t/eval/run_gr00t_server.py \
  --model-path "$CHECKPOINT_DIR/libero_object" \
  --embodiment-tag LIBERO_PANDA \
  --use-sim-policy-wrapper
```

server只对获授权的本地/受控网络开放；确认绑定配置，不把无认证推理接口暴露到公网。先batch=1。保存一次真实请求的输入schema、输出schema/horizon、状态与夹爪语义、耗时、峰值显存和模型身份。

### M1-B：完整原生episode

使用官方rollout路径或语义等价的薄runner，先单环境。记录从reset到成功、时间上限或错误的完整过程。`get_action()` 返回数组、视频看起来在动、人工接管成功均不等于完整baseline验证。

若为固定benchmark初始化扩展runner，单独记录该差异，并证明观测、action conversion、wrapper、controller、history和success语义未变。

### M1-C：小规模开发矩阵

在三预定任务、C0及开发挑战中逐步安排不超过24次episode runs（含完整smoke episode）。首要证明正常重复完成；不能为凑违规而先做大批故障。保留所有run和尝试，注明尚未成熟的oracle只作人工核查，不输出正式准确率。

预算耗尽、模型连续因同一未明原因失败或无可用GPU时，提交R1阻塞报告，不无限尝试。

## 5. Shadow和Gate开发顺序（R1放行后）

先实现snapshot round-trip，再同动作主/影子比较，再独立oracle，最后加入风险判据和执行门控。没有shadow验证，不用其输出为正式标签背书。

做CPU级接口/错误处理测试后，运行真实snapshot tests。给Gate喂NaN、缺对象、过期state、被修改前缀、重复许可和模拟超时，验证全部不会绕过拒绝。

`shadow-on / always-accept` 完成baseline parity后，才运行会真正阻止动作的G。

## 6. 正式实验运行纪律

实验代码先提交并固定SHA。工作树不干净时仅能标开发探索；要么clean commit，要么保留patch/hash并申请新运行身份。

每次run先校验protocol lock、输入文件hash和配置hash。一个正式run只属于一个protocol_id。先写planned-cell manifest，再运行，不用最终生成的成功目录反推分母。

分阶段记录：开始、模型载入、reset、决策、执行、终止、清理。异常保留原artifact，不覆盖同名文件。重跑新建attempt_id并链接原run。

## 7. Artifact与日志

GitHub提交：源代码、配置、schema、sanitized报告、小型CSV/JSON汇总、图表、少量获许可fixture和artifact manifest。

获授权外部存储保留：完整snapshot、原始action、逐步物理状态、视频、未脱敏日志。GitHub manifest使用相对artifact ID、大小、SHA-256、格式、生成run/commit、公开性和复核状态；不放绝对内部路径。

最少元数据：

```text
protocol_id, run_id, attempt_id, pair_id, task_id, init_id, init_hash
split, condition_id, perturbation_config_hash, policy_seed, env_seed
repo_sha, upstream_sha, checkpoint_revision, processor_hash, runtime_lock_hash
observation_hash, action_hash, execution_prefix_hash, state_digest
step, inner_steps, control_hz, H_e, decision, reason, margin, trigger_object
oracle_label, first_event_step, official_success, termination_reason
inference_ms, shadow_ms, governor_ms, total_wall_ms
artifact_ids, exit_code, started_at_sgt, completed_at_sgt
```

隐藏条件的权限应在代码API上落实：Gate不能读取oracle_label或fault flag。记录字段齐全不等于所有组件都可读取全部字段。

## 8. 成本测量

先测baseline episode wall time `t_B` 和governed `t_G`；正式初始预算为 `90*t_B + 90*t_G`，还需校准、初始化、失败重跑和打包空间。不要把模型单次推理延迟当作episode总耗时。

分别报告推理、shadow、risk计算、通信、主仿真和端到端。计时涉及GPU时明确同步方法；渲染/首轮模型warmup分开。仿真等待不会自动证明满足真实20Hz控制截止时间。

## 9. 可复现交付

最终CLI至少覆盖preflight、baseline、shadow validation、calibration、governed、analysis和package。具体命令必须在实现后写入README并实测；初始化文档不预先声称这些脚本已存在。

干净目录验证：安装/配置、CPU测试、小型真实smoke、从已保存结果重建主表/图、源码ZIP清单。模型和完整数据由官方获取，README描述准确身份和许可证。不得为降低包体删除关键实验脚本或负结果。
