# R001 — M0/M1 原生 GR00T–LIBERO 基线交付审核（Cosmos 访问阻塞）

- **Reviewer role:** GPT（基于可访问 GitHub 提交、源码与公开运行摘要进行审查；未登录 Corelab，未运行代码）。
- **Date:** 2026-10-21 Asia/Singapore。
- **Protocol:** TASE-001 v1.0；**PR:** #3；**Issue:** #2。
- **Reviewed head:** `24ad57fd0dad73327f00851529c32ba762e42569`。
- **Primary decision:** **`BLOCKED_RESOURCE` — M0/M1 资格尚未通过；只允许在负责人完成访问授权后继续原 M0–M1 的有界补验。**
- **Stage authorization:** 不放行 M2–M3、CALIB、TEST、shadow、Gate、训练或 WBC；不合并 PR #3；保留原 DEV 预算 **5/24 已用、19 剩余**。

## 实际审阅范围和证据等级

读取 PR #3 元数据及变更文件清单、Issue #2、`reports/M0/preflight.md`、`reports/M1/baseline_report.md`、`reports/M1/runtime_contract.md`、`reports/M1/evidence/checks.json`、模型下载摘要、`configs/runtime_lock.json`、`tase/baseline.py`、`tase/server.py`、`tase/evidence.py`、`scripts/runtime_env.sh`、`scripts/prepare_runtime.py`、`scripts/download_model.py`、DEV 配置、CPU 测试和已有审核协议。按公开证据区分 implementation/source review 与实际 runtime verification。

**未独立读取：**私有 raw server traceback、原始视频/PNG/Sim state、安装原始日志及实际 GPU 上的模型文件；公开哈希与执行者报告不能替代访问原件。**未独立执行：**CPU 测试、GPU 推理或完整 episode。CPU `8 passed` 是已提交的执行记录而非 reviewer 重跑结果。

## 已达到的有限结果

1. 代码范围遵循原生 `LIBERO_PANDA`，没有 WBC、额外训练、实机、正式 CALIB/TEST 或 Gate 实现。
2. `runtime_env.sh` 有意重设 `HOME`、`HF_HOME` 和 cache 路径；独立环境是设计目标，也使已有常规用户目录的 Hugging Face login 无法自动被新进程看见。进程级 `HF_TOKEN` 或 `HF_TOKEN_PATH` 是否设置需要在**同一隔离进程**验证。
3. 公开报告记录了官方 Object 七个文件的大小及哈希（含两片 LFS 权重）、GR00T/LIBERO/checkpoint revisions、独立环境和后续 dependency check。
4. DEV 共五次原生环境探测：4 PASS、1 初始化失败且保留；三任务双相机/EGL/20 Hz 的结果属于**环境级**证据，不是模型 forward 或成功 episode。
5. 执行者未把后台 launcher exit 0 伪报为模型加载成功，也明确披露子进程实际退出码未捕获；这种失败报告边界是正确的。

## 阻塞（必须补证）

**B1 — HF gated-backbone access。** `nvidia/GR00T-N1.7-LIBERO` Object 主权重下载成功，但 `Gr00tPolicy` 初始化需读取独立 gated `nvidia/Cosmos-Reason2-2B`；当前返回 HTTP 401。该模型要求用户在 Hugging Face 网页同意访问条款并使用具有对应读取权限的账号。已授权账号的 token 还必须对被重设 `HF_HOME` 的实际 server 进程可见。不能假定过去 Corelab/Hopper 的 HF 凭据已经进入新环境，也不能因 401 推断模型算法失败。

**B2 — R1 原生基线尚未成立。** `0` 个 GR00T forward、`0` 个完整 policy episode，官方 TSR=N/A；实际 action horizon / 8-step 前缀、client/server 合约、完整 gripper 转换、thin adapter 与官方 reset/history parity、模型 VRAM/耗时、两任务跨初态重复正常成功均尚未通过。

**B3 — 运行可追踪性。** 首次后台模型 launcher 没有记录子进程真实退出码；后续模型启动必须 foreground 或等待子进程并记录真实 code。初次 simulator dependency check 的退出码也被 wrapper 吞掉，尽管后续复检记录 PASS。

**B4 — 原始证据未由 reviewer 实际验证。** 在能审查私有原件前，原始 traceback/PNG/state/log 的内容均标记 NOT_VERIFIED；不将公开 manifest 的 hash 自动当作审阅原件的证明。

## 允许的下一步（限定 M0–M1）

1. **项目负责人自行在浏览器中确认授权**：登录其 HF 账号，打开 `https://huggingface.co/nvidia/Cosmos-Reason2-2B`，审阅并在同意时接受模型访问条款/共享信息。若审批未通过则停止；不可规避 gated 模型访问控制。
2. **在实际 server 一模一样的隔离环境**中，确认 `HF_HOME`、`HF_TOKEN_PATH`、`HF_TOKEN` 的存在/优先级及 `hf auth whoami` 身份（不要输出 token）；如果历史普通 HOME 已登录而隔离环境未登录，由负责人在隔离 `HF_HOME` 下交互 `hf auth login`，或使用批准的安全凭据注入。不得把 token 值传给 Codex、提交 Git、放进 CLI 参数或日志。
3. **CPU/网络级最小访问探针**：用实际 server Python 和环境读取 `nvidia/Cosmos-Reason2-2B/config.json` 并报告 `ACCESS_OK` 或脱敏后的错误分类，不要打印 Authorization header、token、URL 查询密钥。模型分支需核实后续 auxiliary revision 身份。
4. 只有 owner 确认解除 blocker 且 GPU 使用授权仍有效时，Codex 才继续**原有 19 个 DEV slots**：前台启动模型并捕获真实退出码与模型身份/峰值，执行一条真实 `get_action`、记录实际输出 contract，然后做原生完整 episode 与两任务跨多初态重复测试。提交 M1 修复/续验报告、全量成功失败、运行 SHA/identity、PR 更新，重新申请 R1。
5. 不更换 backbone、不绕过 license、不换模型、不重置预算、不提前实现 M2/M3。若需要放宽范围，先在 Issue #2 请求新的明确决议。

## Reviewer conclusion

目前的**隔离部署与失败留证是可用的阶段成果**，但严格的 R1 资格不通过。**本决议仅维持已存在的 M0–M1 有界补验权限，不构成新 GPU 授权、不授权更高阶段。** PR #3 保持 open/unmerged，Issue #2 保持 open，模型真实成功/治理效果不得由环境 probe 推断。

下一次审核对象必须是新的完整 PR head SHA 和可复核的真实运行证据。