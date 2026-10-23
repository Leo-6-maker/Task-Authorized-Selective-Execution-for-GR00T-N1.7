# TAKEOVER-RECOVERY-001 — 新执行 Agent 接手与运行上下文恢复

日期：2026-10-23。计划制定：GPT reviewer；执行：新的 Codex/实现 agent；项目负责人：用户。

本文件是接手工作包，不是新的 M2/M3 结果审核，不覆盖 R003，不自动启动任何远端工作。新 agent 的目标是接续已有实现和原始证据，不是重建一个同名项目再从零跑。

## 0. 当前判断与事实来源

用户本轮报告：经已配置的跳板与 GPU 节点完成只读检查；可读进程中未发现本项目任务；发现两个旧 GR00T checkout，均为 `51d4c89f…`；本项目运行 checkout、R003 收据及共享账本未定位；部分候选存储无读取权限。该报告全文位于用户新电脑，GPT 本轮只取得用户摘要，没有读取其本地文件，也没有登录远端。

本轮 GitHub 读取确认：

| 对象 | 查询时身份 | 解释 |
|---|---|---|
| PR #3 | `codex/2-native-baseline`，`3e214c0b761d0639bf73948356a92a03bf2ddedc` | 父实现分支，未合并；运行原件独立审核不自动完成 |
| PR #5 | `codex/4-m2-shadow-oracle`，`7e73108fd87a711b4cdc339d93749cc4add3628f` | 最新实现与 R003 补验代码，未合并；PR 正文仍引用旧 head |
| R003 | 审核 `d64cb1002980738f170e3206d004b4a882166543` | 允许有界 CPU 修复及特定旧动作补验，不授权 M3/CALIB/TEST |
| 历史预算 | DEV 18/24；shadow 74/80 | 历史节点，不等于当前剩余量；补验是否已消耗待恢复真实账本 |
| 本轮运行状态 | `ORIGIN_WORKSPACE_UNRESOLVED / CURRENT_LEDGER_UNKNOWN` | 未找到不等于不存在；无权限不等于目录为空 |

`51d4c89f…` 不匹配本项目固定的 GR00T 源码。不能直接在这些 checkout 上安装、切版本或执行课程实验；也不能仅凭 SHA 就断言它们一定属于哪一个其他项目。

主要来源：[AGENTS](../../AGENTS.md)、[R003](../reviews/R003-M2-shadow-oracle-review.md)、[Issue #4](https://github.com/Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7/issues/4)、[PR #5](https://github.com/Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7/pull/5)、PR #5 分支的 `reports/M2/R003_supplement_plan.md` 与 `scripts/supplement_m2_r003.py`。

## 1. 本次允许与禁止

立即允许：安全地保存新电脑现有修改；GitHub 读取/fetch；建立新的本地接手分支/工作目录；在授权目录做有界只读定位；整理私有路径映射；CPU 合成单元测试；核验已取得证据的字节/hash与静态数据；编写、测试 R003 范围内尚未完成的修复；提交脱敏交接材料。

暂不允许：启动模型/推理 server、创建真实仿真或 shadow 实例、产生新 episode/probe、重新下载大模型、重装服务器环境、修改旧 checkout/账本、进入 M3/CALIB/TEST。后续只在第 7 节的恢复条件满足时沿用 R003 已有补验权限，不增加实验预算。

禁止：`git reset --hard`、`git clean -fd`、force push、删除旧结果/锁、停止他人任务、绕过 SSH 主机验证、猜测或读取他人凭据、用 sudo/chmod/chown 越过权限、向公开仓库上传内部路径/主机/账号/完整环境或未经脱敏的接手报告。

**余额未知时，运行许可暂挂起；不把实际已用量擅自改成 0 或 80。**

## 2. 工作流与输出

两条线并行推进：A 线恢复原执行位置、访问权和证据账本；B 线完成本地代码接手、CPU 回归和交付整理。A 线阻塞不等于 B 线无事可做。

| 步骤 | 工作 | 完成证据 |
|---|---|---|
| T0 | 保存本地工作，固定 Git 身份与任务归属 | source map、完整 SHA、未提交/未推送工作记录 |
| T1 | 确认节点/账号/挂载身份，进行有界定位 | 私有位置表、候选状态与查找覆盖 |
| T2 | 权限或路径不足时获取最小交接 | 精确路径/有限目录访问或原件导出；不要求整个 NAS 权限 |
| T3 | 对账旧运行和 R003 消耗 | 逐 run/case 的 reconciliation、未知项、实际可用权限 |
| T4 | 并行 CPU 修复与证据打包 | 普通/-O 测试、有效/负例、已有帧标签重算 |
| T5 | 根据实际状态决定补验或仅审计 | 不重复已完成工作，不突破失败即停/原预算 |
| T6 | 交付新的可审核接手包 | 完整 head、公开摘要、私有清单和 READY_FOR_REVIEW |

不要求每条命令人工审批；只在缺权限、缺原件、运行余额不明、需要新增资源或改变协议时停在相应边界。

## 3. T0 — 先保存并固定代码状态

1. 在新电脑现有 repo 记录 `git status --short --branch`、`git rev-parse HEAD`、最近五个提交。现有 TAKEOVER_REPORT 先保留原件；检查是否含内部路径，未经脱敏不得提交。
2. 保存必要 patch、未跟踪文件及未推送提交于私有交接目录。不要用清理命令消除脏工作树。
3. Fetch 后重新读取 PR #3/#5 的 live head/base；读取 `origin/main` 上最新审核。若 head 已前进，记录新 SHA；不要强制回退到本文查询值。
4. 代码以 PR #5 的最新远端分支为接手基础；主分支当前不是完整执行环境的替代。初次接手用新本地分支 `codex/<本issue号>-takeover-recovery`，注明父 SHA。
5. 不对 PR #3/#5 做自动 rebase、合并或关闭。接手修复若需独立 PR，可将 PR #5 分支作为 stacked base；报告/doc-only 修改根据实际 diff 单独处理，保留明确依赖。
6. 确保只有一个 agent 写本项目工作树。核对原 agent 是否停止写入及用户可读的活动记录；无法确认时先不修改共享树，不 kill 进程。

建议只读命令（适用于当前 repo；输出先存私有目录）：

```bash
git status --short --branch
git rev-parse HEAD
git log -5 --oneline
git fetch origin --prune
git show origin/main:docs/reviews/R003-M2-shadow-oracle-review.md
git show origin/codex/4-m2-shadow-oracle:reports/M2/R003_supplement_plan.md
```

阅读顺序：AGENTS → 最新审核 → Issue #4/PR #3/#5 讨论 → R003 supplement plan → 当前实现/配置 → runtime lock → 运行报告/manifest。STATUS/PR 正文可能滞后；代码 head、实际运行收据和 reviewer 决议分别确认，不能用一个替代全部。

## 4. T1 — 找回原工作区，而不是无界全盘搜索

### 4.1 先确认是不是同一个节点、账号和存储视图

在本地及实际 GPU 会话分别记录受限、只读身份信息。SSH alias 的名字相似、GPU 容量相似，都不足以证明落到了同一个宿主和目录视图。

核查 hostname、UID/GID、HOME、当前真实路径、GPU UUID（私有）、候选目录所有者及挂载 source/type；必要时与旧 operator receipt 的同类字段比较。旧 HOME 与新 HOME、节点本地盘与 NAS、登录宿主与容器/会话的存储视图可能不同，均为待检验假设，不先认定某一个原因。

```bash
hostname
id
printf 'HOME=%s\n' "$HOME"
pwd -P
getent passwd "$(id -u)"
findmnt -T "$HOME"
# 对已获准的具体候选路径；失败与权限不足也要记录
stat -c '%u:%g %a %n' "$CANDIDATE_ROOT"
findmnt -T "$CANDIDATE_ROOT"
```

不得把上述内部输出原样公开。不要读取其他用户进程的完整命令行/环境；“在可读范围未发现任务”不是整个节点无任务的证明。

### 4.2 先从已有交接材料反向找路径

优先查看新电脑的交接报告与私有 runtime-map、旧电脑的项目 operator notes/记录、已取得的项目专用 receipt 和归档目录清单。仅取路径、工作目录、解释器、run ID、退出码与 hash；不要全文打印 shell history、环境变量或 token。

请旧 agent/负责人一次性导出：实际工作区、课程 checkout、两个 Python、固定上游源码与模型目录、M1/M2 raw 根、原共享账本、R003 输出及最后运行。这比反复遍历 NAS 更有价值。

### 4.3 有界目录定位

使用负责人已授权的 HOME、节点用户级缓存、项目 scratch 和可读 NAS 子目录作为候选根。历史路径线索只能作为候选，不在公开计划中编造或公开内部根目录。

先查名称和元数据，命中后才读少量内容；建议上限为每轮最多 6 个候选根、每根深度 7、每根 90 秒。最多两轮；第二轮必须有新的路径/账号/挂载线索。超时、权限拒绝、深度限制或输出截断均表示覆盖不完整，不能解释为文件不存在。目录特别大时立即缩小，不扫 `/`，不扫描全部模型权重。

优先名称锚点：

```text
Task-Authorized-Selective-Execution-for-GR00T-N1.7
course-repo
runtime_lock_m2.json
m2-runtime-budget.json
dev-m2-017
m2-r003-01
r003-dev-m2-017-d011-r0
snapshot-009.pkl
R002-private-sanitized-originals.zip
M2-private-sanitized-originals.zip
```

候选结果分为 `FOUND_MATCH`、`FOUND_OTHER_REVISION`、`PERMISSION_DENIED`、`MOUNT_UNAVAILABLE`、`SEARCH_INCOMPLETE`、`NO_MATCH_WITHIN_SCOPE`；保留检查范围与错误，不写笼统的“服务器没有项目”。旧 SHA 的 checkout 只作排除/路径线索，不原地改造。

## 5. T2 — 权限阻塞的最小交接请求

完成一轮针对性定位仍无结果，或已遇到关键目录权限问题时，即可发出具体请求，不必等遍历完所有地方。

给负责人/原执行者/有权限管理员的请求（内部发送，不自动对外联系）：

> 请提供此课程项目最后一次运行的实际宿主/账号映射、TASE_WORKSPACE、课程 repo、GR00T upstream、server/simulator Python、原始 runs/episodes 与 runs/m2_shadow 的精确位置，以及 R003 是否已经运行及其最后收据。若新账号无法访问，请由所有者提供仅该项目子目录的必要读取/遍历权限，或导出完整账本与所需原件至新账号已授权目录。需要写入恢复实验时再单独授予最小写权限；不需要整个 NAS、其他项目或任何明文凭据。

若只能导出脱敏 reviewer 包，明确它是审核材料，不默认等于可执行 workspace。物理回放需要可信原始完整 snapshot、同版 assets/控制器和真实账本；安全 NPZ/JSON 摘要未必能恢复这些内容。

等待权限期间继续 T4。先整理源码与测试，不启动新环境“绕开”访问问题。

## 6. T3 — 恢复账本及原件身份

### 6.1 不把公开历史摘要当当前账本

恢复原 `runs/episodes`、`runs/m2_shadow`，以及 R003 的 operator/start/exit/result 收据。对所有 reservation（成功、失败、STARTED/中断均包含）按相对 run ID、ordinal、来源 snapshot、实际代码/config SHA、结果与文件 hash 对账。

不只数成功 result；不因为某目录没有 result 就释放名额；不删除 stale lock；不同磁盘/备份的同一 run ID 不可重复计数。ID 相同且内容不同时记为冲突，禁止择优保留。

制作新的 `ledger_reconciliation.json`，记录历史声明、当前实际证据、来源副本、重叠/冲突、未知范围、执行许可。它是派生对账报告，不伪装原始执行账本，不写回旧 reservation。缺失原件要写 `UNKNOWN`/`NOT_VERIFIED`，不能补造 PASS。

### 6.2 必须核对的原件

- M1 原包声明 SHA-256：`d0d317ee83226ce3dd34a654468636b43deb8cae5a959b4fe628fda5ba3eba98`。
- M2 原包声明 SHA-256：`859b177e097fab1c88449d30afcf3c2d2175256ecdb795793cc9a517de9737a2`。
- R003 如有新的原件包，使用其自身新收据/hash，不套用旧包身份。
- ZIP 先核对 hash、目录遍历/重复名称/异常解压大小，再解到新私有目录；不直接执行附件代码或反序列化来历未核实的 pickle。
- 优先安全 NPZ（`allow_pickle=False`）/JSON 数值和媒体独立核验；已确认来源与 hash 的物理 snapshot 留给固定环境下的授权回放路径。

### 6.3 预算分流表

| 恢复的实际状态 | 允许动作 |
|---|---|
| 完整可信账本确认 DEV=18、shadow=74；不存在补验 reservation/启动痕迹 | T5 条件全部成立后，可按既有 R003 一次性有界补验 |
| shadow=80，且六条补验结果完整 | 不重跑；只进行 CPU 重审、整理并提交审核 |
| shadow=75–79，或任一补验失败/中断/存在无 result reservation | 先做静态诊断并提交精确恢复方案；原脚本不是可随意重入的 resume 程序，不能换 run ID 重新执行 |
| 仍不可访问/副本不全/冲突/可能存在未发现运行 | 当前余额 UNKNOWN，真实运行继续禁止；不将名义上限减去旧历史摘要当剩余量 |
| 出现超过约定的消费 | 如实保留并报告，不删除、不重编号；申请明确处理 |

依据 `scripts/supplement_m2_r003.py`，入口检查原 shadow 数正好为配置的 74、DEV 为 18，并采用 append-only 输出；不能修改这两个 guard 只是为了让程序继续跑。

## 7. T4/T5 — 恢复期间如何继续做有效工作

### 7.1 可立即并行的 CPU 工作

1. 审阅当前 `tase/event_oracle.py`、`tests/test_oracle_inputs.py`、补验和重审脚本，先确认 R003 修复是否已存在；不重复覆写已经完成的实现。
2. 在可用的独立本地 CPU 环境运行纯合成测试，普通与优化模式分别保留命令、依赖和退出码。没有测试环境时只建立最小本地 CPU 环境，不修改服务器两个已冻结环境。不得把 mock 或本地不同 Python 版本的结果称为远端物理验证。
3. 核对有效输入正例、NaN/shape/布尔类型/step/baseline/参数负例、原子历史更新、sticky violation 保留、跨 chunk 连续计数。保持原 2 cm / 两步 / 1 cm 开发定义，不为增加阳性调标签。
4. 有可信可读原始数据时先 CPU 重审；使用新输出目录，不改旧标签或 manifest。若仅有安全导出，明确重审覆盖，不能无声替代原 pickle 读路径并声称全量同等验证。
5. 整理公开 PR 正文、STATUS 与真实 head 的差异，提交脱敏更正；reviewer 批准状态不由执行者更改。

建议 CPU 入口（确认相关测试无真实 simulator/model 调用后）：

```bash
python -m unittest discover -s tests -v
python -O -m unittest discover -s tests -v
```

### 7.2 恢复运行身份，不盲目重装

已找回原 workspace 时只核对固定源码/依赖/解释器与模型 hash，不重复下载安装：

- GR00T：`dac54b313160c201c450f97df0fd74ebd379c892`。
- LIBERO：`8f1084e3132a39270c3a13ebe37270a43ece2a01`。
- Object revision：`2ea293aa20ba7cf5bbf3ba17a5fbcb1a01cbfe21`。
- Cosmos revision：`9ce19a195e423419c349abfc86fd07178b230561`。

账号/节点映射、两套 Python、资产位置、原生接口、EGL 绑定、共享资源许可分别确认。旧记录的可用显存和授权不等于现在有可用资源。R003 补验不启动 policy server，因此不应为这项任务重新下载模型或请求新 token。

若确需恢复环境，仅提交 `RESTORE_ENVIRONMENT_CHANGE_REQUEST.md`：缺失项、备份来源、只读源/新目标、版本锁、资源与预算影响。新环境必须使用独立目录，历史原件只读保留；没有批准前不重建 GPU runtime。

### 7.3 何时可以沿用既有 R003 补验许可

全部条件同时满足：正确原件与完整账本已找回；确认补验从未启动/消耗；CPU 修复与有效帧重审通过；原 simulator 环境及固定身份匹配；当前资源许可有效；无其他 agent 同时写；代码已提交且工作树干净。

此时才按原补验配置，以固定模拟器 Python 执行既有脚本一次。它恢复 source017 d009（72 步后），只用保存动作重建 d011/d012，比较 89–96 和 97–104；最多六个短比较，失败即停。没有新增模型调用/自主 episode，不动六个保留 DEV 名额，不进入 M3。

这不是要求此时立即执行该命令；它是前置条件通过后的原有入口：

```bash
"$SIM_PY" scripts/supplement_m2_r003.py --workspace "$TASE_WORKSPACE"
```

若补验已完成，改走 `scripts/audit_m2_r003.py` 的 CPU 审计入口，参数按实际原件根目录和 `--help`/源码确认。不要因为最终报告尚未写完，就重新跑物理。

## 8. 确认原工作区不可恢复时的有限后备方案

两轮有界定位后仍无新线索，停止重复扫描，明确问题是权限、路径未知还是数据不可恢复（后者需所有者/管理员或备份证据支持）。

- 代码可从 GitHub 恢复：保留正确分支，不丢已有实现。
- 原始运行与预算不能从源码恢复：保留独立限制，先从旧电脑/NAS/获授权归档恢复。
- 只有摘要无原件：可以继续 CPU 实现和文档，不声称历史运行已独立复验。
- 原件和账本确实遗失：提交 evidence-loss / environment-restore change request。若未来需重新采集，必须作为明确的新运行批次、显式追加预算、旧失败与证据缺口仍保留；不能重建空账本伪装历史从未运行。

接手成功不是“找了一天还在找”，而是明确落到：可按原工作继续、等待一项精确权限/交接、或已形成可决策的恢复申请。

## 9. 交付文件与隐私

私有目录放在 repo 外，或已确认忽略且不会被打包的路径。以下文件是本次待创建输出，不宣称已经存在：

```text
private_takeover/
  runtime-map.local.yaml
  identity-and-access.json
  workspace-discovery.csv
  denied-paths.md
  ledger_reconciliation.json
  command_receipts/
  recovered_originals/       # 只读源副本；安全检查后另处解压
  cpu_test_outputs/
  operator_handoff.md
```

`runtime-map.local.yaml` 至少包含：local_repo、remote_checkout、task_workspace、upstream_root、server_python、sim_python、assets/checkpoint/cache roots、episode_ledger、shadow_ledger、R003 output/receipts、raw archive locations、credential FILE LOCATION ONLY、GPU/EGL 与许可说明、每字段证据来源。未知填 null，不猜，不填 token。

公开仅提交脱敏的 `reports/takeover/TAKEOVER_STATUS.md`、公开测试收据及必要代码。不得直接上传用户现有本地报告；它可能包含内部目录和账户。

最终接手报告分别回答：

1. 本地/远端完整 SHA 与当前 reviewer 决议。
2. 工作区与权限是否恢复；未恢复时精确缺哪项。
3. 实际 DEV/shadow 消耗与证据来源，是否存在中断/冲突。
4. R003 修复、CPU 重审、物理补验各自的状态。
5. 本轮实际做了什么、明确没做什么；是否产生任何新运行。
6. 需提交给 GPT 的原件位置/附件与 hash；独立核验项仍由 reviewer 实际读取后关闭。
7. 下一步是否仅为审核，或需单项恢复授权。

最终状态使用 `TAKEOVER_READY_FOR_REVIEW`、`BLOCKED_EXACT_ACCESS_REQUEST` 或 `RESTORE_CHANGE_REQUEST_READY`，不使用自签 `M3_APPROVED`。模型、治理性能、原件核验的既有结论均不因接手而自动改变。

## 10. 给新 Agent 的简明执行指令

你接续这个项目而非从零复现。先保全本地工作与最新 PR #5 代码，阅读 R003。立即并行：A线只读核实节点/账号/挂载，优先从项目 operator receipts 与旧交接定位原工作区，最多两轮有界搜索，权限不足提出精确最小交接；B线运行纯 CPU 回归并核对最新 R003 修复，整理公开/私有输出。未找回完整账本前不要启动模型或仿真。补验若已经执行则只审计，不重跑；部分执行/失败则保留名额并报告，不改 guard。仅在原件、账本、身份和资源全部满足原 R003 前置条件且确认从未启动补验时，执行一次原有有界旧动作诊断。不要占用其他科研 checkout，不扩预算、不进入 M3、不合并。以实际证据交付接手报告和原件审核包。
