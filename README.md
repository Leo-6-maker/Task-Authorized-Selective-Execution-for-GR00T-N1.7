# Task-Authorized Selective Execution for GR00T N1.7

**ME6401 Part 2 — AI Governance for AI-Enabled Systems**

在原生 **GR00T N1.7 LIBERO-adapted policy → LIBERO/Panda execution** 链路中插入运行时 Safety Gate，研究错误物体抓持／抬升的选择性阻止及其任务完成、误拦截和计算成本。

> **范围决定（2026-10-21）：本项目不包含 WBC、Go2、ARX5 或自定义 EEF 轨迹转换。** 复用官方 LIBERO post-trained checkpoint、processor、embodiment 与原生动作执行接口；治理层不替代任务策略或低层控制器。

```text
LIBERO observation + task instruction
                ↓
        Frozen GR00T N1.7
                ↓
      Native LIBERO action chunk
                ↓
   Safety Gate (client/execution boundary)
      ├─ ACCEPT → checked prefix → native wrapper/controller → simulation
      └─ REJECT / ERROR → withhold prefix → end autonomous episode + record
```

## 当前状态（E2，2026-10-24）

Issue #8 的新环境、原生baseline、真实Gate及48次条件CALIB已完成，**READY_FOR_R2_REVIEW；无GPT结果批准、无自动merge、TEST未启动**。当前依据为[R004](docs/reviews/R004-fresh-epoch-progress-decision.md)，取代旧目录恢复门槛。不要重跑已完成ID或把下面历史M2额度当当前余额。

- [接手状态](reports/E2/TAKEOVER_STATUS.md) · [集中R2包](reports/E2/R2_REVIEW_PACKET.md) · [CALIB结果](reports/E2/calibration_report.md) · [67项完整账本](reports/E2/attempt_identity_ledger.csv)
- DEV19/24、独立短检查32/96、CALIB48/48、TEST0。1920次实际模型请求已对账，全部失败保留。Object7/7、Cosmos10/10重新核验完整，[无需重复下载](reports/E2/model_file_recheck.json)。
- [真实DEV Gate](reports/E2/gate_dev_report.md)及24组CALIB配对均核对同一主状态/RNG/动作前缀。C0成功11/12对11/12；C2实际wrong lift4/12对0/12，G以4次拒绝终止换取拦截，成功均8/12。CALIB同数据选k3和评价，不能当独立TEST或自然错误率。
- [可实际获取的最小数值/媒体材料](reports/E2/review/README.md)、[新CALIB事件图](reports/E2/calibration-first-event-contact-sheet.png)、[双地点归档核验](reports/E2/backup_chain_verification.json)。模型/仿真均已退出。下一步仅为GPT一次R2审核；[120格TEST只是未授权提案](configs/e2_protocol_lock.json)。

## 历史M2交付（以下是当时状态，当前入口以E2为准）

**M2 READY_FOR_REVIEW：24快照、74次shadow比较及原始重算已交付。PR #3/#5保持未合并，M3尚未授权。**

[M2实际报告](reports/M2/runtime_report.md) · [逐case数值](reports/M2/snapshot_validation.csv) · [独立事件定义/记录](reports/M2/oracle_definition.md) · [无副作用验证](reports/M2/noninterference_report.md) · [预算](reports/M2/budget_ledger.json) · [manifest](reports/M2/artifact_manifest.json)

M2使用6次预定采集（3 C0、3明确标记的C2指令错配），共249次真实推理、1,985控制步。74次短预测中主状态与policy RNG保持一致；1段受控错误物体抬升用于oracle可观测性，不能解释成自然风险率或治理改善。累计DEV 18/24，其余6次保留。私有原件独立审核仍待实际访问。

M1历史交付：真实 Object 模型完成181次forward、6个预定DEV episode，5次官方成功，ketchup初态1在720步上限失败。Alphabet soup和cream cheese均在初态0、1成功。当时累计12/24次DEV，包含环境检查和两次基础设施错误；M2之后的当前累计为18/24。

通过进程级外部 HF_TOKEN_PATH 解决凭据发现问题，并固定 Cosmos revision。实测 PyTorch peak reserved 约 6.04 GiB（不是整进程及渲染总显存），episode 中位 9.46 秒。[R002](docs/reviews/R002-R1-native-baseline-conditional.md) 有条件允许 M2；先完成[审计加固](reports/M1/audit_hardening_report.md)，再按 Issue #4 有界验证 snapshot/shadow/oracle。M3 尚未授权。

- [M0安装、资源与失败报告](reports/M0/preflight.md)
- [M1续验报告与全部开发记录](reports/M1/continuation_report.md)
- [原生运行契约与实测限制](reports/M1/runtime_contract_resume.md)
- [运行身份](configs/runtime_lock_resume.json) / [artifact manifest](reports/M1/artifact_manifest_resume.json)
- [首次阻塞交付的历史报告](reports/M1/baseline_report.md)

## 阅读顺序

| 文档 | 用途 |
|---|---|
| [项目主计划](docs/PROJECT_PLAN.md) | 研究问题、范围、里程碑、验收、风险和课程交付 |
| [架构与动作契约](docs/ARCHITECTURE.md) | Gate 精确插入位置、shadow、一致性与拒绝行为 |
| [实验协议](docs/EXPERIMENT_PROTOCOL.md) | 独立标签、B0/G、挑战条件、split、指标与统计 |
| [执行与资源手册](docs/EXECUTION_RUNBOOK.md) | 版本、隔离安装、运行证据和资源保护 |
| [审核与协作](docs/REVIEW_WORKFLOW.md) | 用户决策、GPT 审核、Codex 实施、GitHub 记录 |
| [Codex 首轮交接](docs/CODEX_HANDOFF.md) | 可直接执行的 M0–M1 工作范围与停止条件 |
| [当前状态](docs/STATUS.md) | 已核验事实、待验证项、当前授权包 |
| [来源与变更说明](docs/SOURCES.md) | 课程依据、官方源码、历史报告与本版设计的区别 |
| [AGENTS.md](AGENTS.md) | 所有执行 agent 必须先读的仓库约束 |

## 分工

**用户**是项目负责人、资源授权人和课程提交者。**GPT**负责方案与实验审核，基于提交到 GitHub 的代码、配置和证据给出明确结论。**Codex**负责实现、测试、运行、整理证据和交付 PR。**GitHub**保存代码、协议、issue、PR、审核决议和可公开结果；不承担模型推理或 GPU 调度。

审核是按提交触发的，不表示 GPT 正在后台持续监控。创建 issue 也不等于已经启动 Codex。具体交接、复核和阶段放行以 [审核流程](docs/REVIEW_WORKFLOW.md) 为准。

## 科学边界

- Safety Gate 在这里主要指 **任务授权 guardrail**，不是完整物理安全认证。
- Gate 可使用可信任务对象映射与仿真状态；不把对象真值新增到 VLA 输入中。
- 第一版只执行“接受或中止”，不自动修轨迹、不恢复任务、不重训模型。
- 目标是减少定义明确的违规，同时报告任务损失；不预设成功率提升。
- 公开 checkpoint 的存在不等于本地系统已经运行成功。

## 课程交付

截止：**2026-11-06 23:59 Asia/Singapore（UTC+08:00）**。提交封面、最多 15 页内容 slides（参考文献另计）及含 README 的源码 ZIP。课程原始说明由项目负责人持有，不在公开仓库转载。

## 公开仓库与大文件

不得提交凭据、SSH 配置、内部主机/IP/账户、完整机器日志、模型权重、完整数据集或未经许可的第三方资产。大型运行记录留在获授权存储中，GitHub 保存脱敏摘要、相对 artifact ID、尺寸和 SHA-256 清单。原始课程附件与内部可行性审查不自动公开。

## 启动方式

CPU侧检查不加载模型：

```bash
python -m unittest discover -s tests -v
python scripts/verify_delivery.py
```

本轮实际安装入口为 `scripts/prepare_runtime.py`，运行前必须固定上游源码并建立独立workspace、HOME与cache；详见[M0报告](reports/M0/preflight.md)。官方setup之后还须按 `configs/sim_constraints.txt` 修复实测发现的兼容冲突。安装成功不能代替模型/环境验收。

`scripts/runtime_env.sh` 接受运行者明确设置的 `TASE_WORKSPACE`、`TASE_GPU_UUID`、`TASE_EGL_DEVICE_ID`，只使用项目目录内的配置、缓存与环境。实际GPU使用必须得到资源许可。`--allocation-record` 是已有用户许可的记录，不会自动产生许可。

真实环境检查已用如下入口验证；每个新attempt必须使用新的run ID，失败也消耗总计24次的DEV预算：

```bash
"$SIM_PY" -m tase.baseline --workspace "$WORKSPACE" \
  --run-id dev-env-NEW --task alphabet_soup --init-index 0 \
  --allocation-record "$WORKSPACE/runs/gpu-authorization.json" --probe-only
```

`tase.server` 和去掉 `--probe-only` 的原生 runner 已通过本轮六个 DEV episode 验证，包含一个真实策略失败。访问许可由负责人确认；通过外部 `HF_TOKEN_PATH` 使用已有 active token，无需复制 token 到项目环境。不能将 token 写入代码、命令参数、PR 或日志。

固定 Cosmos revision `9ce19a195e423419c349abfc86fd07178b230561` 的推理文件并核验后，将 `$WORKSPACE/runtime/model-resolution/nvidia/Cosmos-Reason2-2B` 符号链接指向该 isolated HF cache snapshot。从 `runtime/model-resolution` 启动 native server，可让官方相对模型标识解析到固定本地文件，避开本次离线 tokenizer 元数据查询问题。具体文件清单与失败修复见续验报告。

已验证的 server/client 入口如下；先完成上述环境、缓存、资源许可检查，设置 `SERVER_PY`、`SIM_PY` 与 `REPO` 的绝对路径，再分别在两个终端执行。NEW 必须换成未使用的 attempt ID：

```bash
# Server terminal: source scripts/runtime_env.sh before changing directory.
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
cd "$WORKSPACE/runtime/model-resolution"
"$SERVER_PY" -u "$REPO/scripts/record_process.py" \
  --receipt "$WORKSPACE/runs/server-NEW.exit.json" -- \
  "$SERVER_PY" -u -m tase.server \
  --model "$WORKSPACE/checkpoints/libero_object" \
  --output "$WORKSPACE/runs/server-NEW" \
  --allocation-record "$WORKSPACE/runs/gpu-authorization.json"

# Client terminal: same runtime_env.sh; wait for MODEL_LOADED / loopback ready.
cd "$REPO"
"$SIM_PY" -u scripts/record_process.py \
  --receipt "$WORKSPACE/runs/dev-policy-NEW.exit.json" -- \
  "$SIM_PY" -u -m tase.baseline --workspace "$WORKSPACE" \
  --run-id dev-policy-NEW --task alphabet_soup --init-index 0 \
  --allocation-record "$WORKSPACE/runs/gpu-authorization.json"
```

CPU 复算私有 evidence（需要 numpy；不会调用 GPU）：

```bash
"$SIM_PY" scripts/summarize_baseline.py --private-runtime "$WORKSPACE" \
  --output "$WORKSPACE/runs/audit-NEW.json"
```

M2入口为同一 `tase.baseline` 加 `--m2`，只接受 `configs/m2_dev_cells.json` 的6个固定run ID；server需加 `--audit-rng`。本次6个ID已消耗，不能重用或再新增采集。CPU原件重算入口 `scripts/audit_m2.py --help`，只读取可信的本任务私有归档。Gate/校准/正式TEST仍没有获授权运行入口；此文档不授权继续花费保留预算。
