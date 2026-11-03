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

## 当前状态

**DOCUMENTATION_BOOTSTRAP / NOT_RUNTIME_VALIDATED**。

本仓库初始化提交的是计划、实施约束、实验协议与审核流程，不是已完成的模型部署、治理代码或实验结果。未在本次规划中登录 GPU 节点、运行 GR00T 或验证治理效果。首个有界执行包为 **M0–M1：隔离部署、接口核验、原生 baseline**；见 [Codex 首轮交接](docs/CODEX_HANDOFF.md)。

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

当前没有已验证的安装脚本或可运行的治理入口。**不要把文档中的拟实现命令当作已存在的程序。** Codex 从 `docs/CODEX_HANDOFF.md` 开始，以 PR 和可核查证据完成首轮交付。
