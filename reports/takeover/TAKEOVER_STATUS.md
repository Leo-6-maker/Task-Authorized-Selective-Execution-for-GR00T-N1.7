# Issue #6 接续执行交付

日期：2026-10-23（Asia/Singapore）。执行者：Codex。工作包：[TAKEOVER-RECOVERY-001](https://github.com/Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7/blob/9a7c9bd6ade46cbe92704270b068b9126c733953/docs/work_packages/TAKEOVER-RECOVERY-001.md)。

**交付状态：`BLOCKED_EXACT_ACCESS_REQUEST`。** GitHub 代码接手、原修改保全、两轮有界定位及完整 CPU 回归已完成；权威原 workspace、完整运行账本与 R003 原始收据仍未恢复。当前实际 DEV/shadow 消耗和补验执行状态均为 `UNKNOWN`，真实运行许可继续暂挂。下一步仅为取得本项目的上下文与完整账本导出包。

## 1. 版本与已有工作保全

| 身份 | 完整 SHA / 处置 |
|---|---|
| 本轮 fetch 后的 `origin/main` | `9a7c9bd6ade46cbe92704270b068b9126c733953` |
| 实时 PR #5 head | `codex/4-m2-shadow-oracle` / `7e73108fd87a711b4cdc339d93749cc4add3628f` |
| 实时 PR #5 base | `codex/2-native-baseline` / `3e214c0b761d0639bf73948356a92a03bf2ddedc` |
| 最新 GPT R003 审阅对象 | `d64cb1002980738f170e3206d004b4a882166543`；不自动覆盖当前 head |
| 本次测试源码 | `7e73108fd87a711b4cdc339d93749cc4add3628f`，运行代码/测试/配置未改动 |
| 本次独立交付分支 | `codex/6-takeover-recovery`，从实时 PR #5 head 建立独立 worktree |
| 原远端运行 checkout | `UNKNOWN`，未用其他 checkout 替代 |

已在 repo 外私有目录保全原工作树的两个 tracked 修改及全部未跟踪材料，共 14 个文件，附二进制 patch、status、完整 HEAD、文件 hash 和归档。保全归档 SHA-256：`39b7d53cb4d91349fa73bee88283c37acfe77f6ff77a9711232a48691d2ee86a`。原工作树没有未推送提交，仍保留原分支与修改；没有 reset、clean、stash 移走或覆盖它们。

本次仅由当前执行者写新建的本地 worktree。原远端 workspace 尚未定位，无法确认原执行者的写入状态，因此没有写远端共享树、账本或运行输出。PR #3/#5 均未 rebase、合并或关闭。

## 2. A 线：身份、位置与访问恢复

节点和路径仅用代号：N0=新电脑，N1=登录节点，N2=负责人指定计算节点；C01–C12 的真实路径、owner、UID/GID 和 mount source/type 均只存 repo 外私有文件。

- 非交互 SSH 与主机密钥校验正常。N1/N2 的 hostname、machine-id 不同；当前 UID/GID 和 HOME 字面值相同，HOME 真实解析路径不同。已分别保存真实 HOME、pwd、候选目录 owner/mode、挂载和 GPU UUID；没有打印完整环境或凭据。
- 没有取得旧项目 operator 原件，故不能把本次身份与原运行身份认定为相同。GPU/alias 相似不能替代该核对。
- 先从公开 manifest 提取 operator/原件归档的确切名称与 hash，再按名称查找；没有全文读取 shell history、环境、其他用户凭据或其他用户完整进程参数。
- 本次当前 UID 的可读进程中未发现项目标志。这个观测不证明全节点无任务，也不证明 R003 从未执行。

| 有界定位 | 范围和线索 | 结果 |
|---|---|---|
| 第一轮 | 六个候选根；本机常用交接位置、两节点的项目交接/下载位置；精确 operator/原件名称 | 0 个名称锚点命中；四个根为范围内未命中，两个因跳过链接/深度等限制覆盖不完整 |
| 第二轮 | 六个候选根；新增线索为节点各自解析后的真实 HOME/存储视图，以及元数据确认的受限 NAS 根 | 0 个名称锚点命中；四个根覆盖不完整，C11/C12 权限拒绝 |

每根限制：目录深度 7、30 秒、最多 30,000 个 entry；不跟随目录符号链接，不遍历模型/权重/数据集和凭据目录。私有 CSV/JSON 逐根保存实际计数、耗时、跳过链接、深度边界及错误。**两轮已结束，不继续扩大搜索，也不把未搜索范围解释为不存在。** 本工作包没有运行 sudo/chmod/chown、删除锁、停止任务或改造其他 `51d4c89f…` checkout。

## 3. 账本与原件：已知和未知分开

| 对象 | 公开历史声明 | 本轮权威原件核对 |
|---|---|---|
| DEV | 18/24，另外六次保留 | 当前实际消费 `UNKNOWN`；六次保留名额不可用于本工作包 |
| 原 M2 shadow | 74/80、24 snapshots、589 predicted controls | 当前实际消费和余额 `UNKNOWN`；不按旧 74 计算余额 |
| R003 六个计划 case | d011/d012 各三次，计划 ordinal 75–80 | reservation/result/start/exit 全部未恢复；不能断言没启动或已完成 |
| R003 driver | 原入口 `m2-r003-01` | identity、start、preflight_error、result、cleanup、exit 均未取得 |
| 原件归档 | 两个 reviewer ZIP 和 operator archive 有公开声明 hash | 没有取得对应字节；未验证归档，未反序列化 pickle |

私有 `ledger_reconciliation.json` 已建立 **99 个预期 ID 的待核对索引**：18 个历史 DEV、74 个历史 shadow、6 个计划补验和 1 个 driver。它只引用公开声明；每行原始 reservation/result/start/exit、代码/config 身份、来源副本及 hash 均显式为 `null/UNKNOWN`。这不是 99 次实测运行，也不是已完成逐原件对账。没有仅数成功文件、释放无 result 槽位、把未知消费改为 0/80 或将备份当成额外运行。

私有原件索引保留 1,880 条公开 manifest 中的 private-artifact 声明及归档预期身份；取得字节标志全部为 false。实际原件去重、冲突检查和有效帧重审尚不能进行。公开派生摘要见 [ledger_summary.json](ledger_summary.json)。GPT 原件核验仍为 `NOT_VERIFIED_BY_REVIEWER`。

## 4. B 线：现有代码接手及 CPU 回归

- 输入契约修复已在 `307fd4f7416c48df5f922300791f58832775a1e3` 存在：修改历史前校验 schema、shape、有限值、布尔接触、step、baseline/参数，并保留 sticky violation；不重写已有实现。
- 同一提交已包含独立 supplement 配置/计划与旧动作诊断；`7e73108…` 已包含 CPU 审计脚本。脚本存在不等于补验运行或审计通过。
- 已核对 supplement 入口的 74/18 guard、原 ID、append-only 输出和失败即停；没有修改 guard、阈值、ID 或补验实现。driver 的目录/启动/preflight 痕迹也必须纳入恢复判断，不能仅因没有新 case 就重入。
- 审计器仅读取可信原件，但包含 pickle 路径；没有取得原件就不调用实际 audit。两个脚本的 `--help` 均 exit 0，验证的仅为 CLI 参数入口。

本轮在 **独立本地 Python 3.12.14 / NumPy 1.26.4** 环境完成全套已有合成测试。仅安装本地 CPU 所需解释器和 NumPy；没有安装或改动远端环境、下载模型或加载物理环境。版本号相同不代表完整远端 runtime 身份相同。

| 实际命令 | 结果 | 收据 |
|---|---|---|
| `<CPU_PYTHON> -m unittest discover -s tests -v` | **24/24，exit 0** | [normal.json](issue6-cpu/normal.json)、[日志](issue6-cpu/normal.txt) |
| `<CPU_PYTHON> -O -m unittest discover -s tests -v` | **24/24，exit 0** | [optimized.json](issue6-cpu/optimized.json)、[日志](issue6-cpu/optimized.txt) |
| supplement/auditor `--help` | 各 exit 0 | [CLI 收据](issue6-cpu/cli-help.json) |

覆盖有效 fixture 与 19 种单一损坏变体、oracle 非法输入/原子历史/sticky violation、跨 chunk、授权/错误对象区分及 CPU snapshot/helper。normal/-O 分别留存命令、SGT 时间、版本、源码/配置文件 hash 和日志 hash。测试中的临时 synthetic reservation 不属于共享账本，不消耗实际 DEV/shadow。此前原工作树 Python 3.10 环境失败证据保持原样，没有用本轮结果覆盖。

状态分别为：代码 `IMPLEMENTED`；已有合成逻辑 `TESTED_LOCALLY`；既有有效帧重审 `NOT_EXECUTED_NO_TRUSTED_ORIGINALS`；物理补验 `EXECUTION_STATUS_UNKNOWN`；当前 head 独立审核 `PENDING`。没有把 CPU PASS 当作 M2 完成或 GPT 批准。

## 5. 私有交付及唯一下一步

以下已创建于 repo 外受限目录，不提交到 Git：

`runtime-map.local.yaml`、`identity-and-access.json`、`workspace-discovery.csv`、两轮发现记录、`denied-paths.md`、`ledger_reconciliation.json`、`originals-index.json`、操作/CPU 收据、`operator_handoff.md`。runtime map 中未恢复的远端 checkout、两套 Python、资产/模型、账本、R003 输出等字段均为 null，并注明证据来源；本地 CPU 环境没有冒充原 server/sim 环境。凭据只保留 location 字段且当前为 null，无凭据内容。

**唯一下一步：由最后执行者或课程目录所有者提供 project-only 的 `TAKEOVER-RECOVERY-001-context-and-ledger.tar.gz`，或等价只读访问。** 私有 `operator_handoff.md` 已给出当前真实节点/UID/GID、两个受限候选根及 owner、精确文件清单和新电脑私有落点。请求仅包含：原 task root/checkout/解释器/挂载映射；完整 episodes/shadow 清单及每个 reservation/result/start/exit（含失败、无结果和锁）；所有 R003 driver/operator 收据；现有原件包位置和 hash；导出 manifest 与覆盖缺口。无需整个 NAS 权限、密码/token、其他项目或权重。请求已准备，未擅自向他人发送。

收到后先静态核对归档身份与完整性，再逐 reservation/result/start/exit 对账：完整六条已完成只审计；部分/失败/中断提交精确恢复方案并保留原 ID；仅完整证据确认从未启动且全部 R003 条件成立时，才可能沿用原许可执行一次旧动作诊断。当前没有满足这些前置条件。

本轮新增真实模型请求、episode、shadow、GPU/仿真工作负载均为 **0**；没有重装服务器、重置账本、改其他 checkout、删除历史/锁、进入 M3/CALIB/TEST、训练、WBC、合并 PR 或自签审核。
