Issue31 E3 CPU priority (2026-10-26SGT): full charter docs/work_packages/E3-EXPANSION-MASTER-PLAN-2026-10-26.md supersedes old-stage entry below for this separate worktree. Planning/source inspection/CPU implementation only; E3 real model/GPU/MuJoCo/TEST NOT AUTHORIZED. E2 all120 retained117eligible+3censored, PR30@3484f3d R3 pending. Preserve course PR22@73ddec9 E2-only fallback and11/06 deadline. See reports/E3/E3_AUTONOMOUS_STATUS.json and REVIEW_REQUEST.md for live CPU state/scene blocker/consolidated gates. Do not self-sign, merge or change E2 original source/data/grants.

GPU1并行入口CPU候选完成：CPU源码d9e445cc693c4fc7284cfa54a83924e340f04360；启动器/原生server统一9GiB空闲下限，原55%/2GiB预算公式保留。普通/-O本机/Corelab各134/134实际0，原84完整审计与908输出完全一致。实际运行版本仍908、84已消耗/36未启动、0085 absent；候选无新TEST grant，不得启动模型/仿真/TEST。交付READY_FOR_INDEPENDENT_GPU1_RESOURCE_DELTA_REVIEW，需独立审核完整新Head、封存R012至84、签新grant后才可GPU1启动，0085/0086后强制检查点。不自签不merge。见 reports/E2/GPU1_ENTRY_DELTA/RESOURCE_DELTA_HANDOFF.md。

GPU1 latest owner instruction（2026-10-25）：用户明确“你使用GPU1”。已绑定新的私有GPU1资源记录；GPU1空闲10121MiB/总16376MiB，exact908冻结入口要求空闲>=16384MiB，当前及全空闲均无法通过。实际CPU隔离原始guard退出1，未启动server/模型/仿真，无新TEST，仍84已消耗/36未启动，0085 absent。不能自动改回GPU0、降低冻结检查或停止其他任务。GPU1资源入口限制需独立工程审核；更改执行代码须新完整Head/newgrant。见 reports/E2/R012/gpu1_request/GPU1_RESOURCE_ENTRY_REQUEST.md。

Issue25/R012 最新停止点（2026-10-25）：84已消耗=61 SUCCESS+10 TIME_LIMIT+10 SEMANTIC_ABORT+0010/0014/0016三次历史 CLEANUP_ERROR，36未启动。0084结构审计/双备份通过后，0085预留前发现另一项目GPU进程，显存低于冻结入口下限；operator实际exit1，native server实际exit0，所有本任务worker/server退出，无新增TEST错误。禁止重启旧operator或重跑任何旧ID。CPU保全/审核继续；只有资源充足并通过新的完整84前缀实时预检，才能使用仍有效的exact908/R012从0085继续；改执行代码需新独立grant。详见 reports/E2/R012/RESOURCE_STOP_HANDOFF.md。

Issue25/R012：exact908bef373eedf8d008ad8d9a91478e3f719eecfb 已获377fe3b85989e6d1fd105002c3c0c09827598886授权。用户后续明确允许显存充足时GPU0并行，GPU1可考虑；已留证资源覆盖条件，未停止原任务。实时完整预检exit0，0017/0018均SUCCESS/exit0，0018真实MuJoCo关闭握手/实际worker0/句柄释放、配对状态动作/RNG、原16未改及两地备份全通过，开始自主0019–0120，每四格结构核验/备份。任何新异常立即停止并保留原ID；科学冻结/执行代码不改，不自签R3，不merge。详见 reports/E2/R012/PROGRESS.md 和 automation/AUTONOMOUS_STATUS.json。

Issue23/R011：0015 SUCCESS/exit0，0016 CLEANUP_ERROR/exit1，真实执行按规则已停止；16已消耗=13SUCCESS+3CLEANUP_ERROR（0010/0014/0016），104未启动，0017 absent。原14原件全量未改，全16两地1900成员验哈希。真实CPU复现sentinel-ready/exitcodeNone误分类，已修复有界waitpid确认及未来撤销grant的只读历史registry；普通/-O本机及Corelab各123/123 exit0，原16审计完全一致。新CPU代码无TEST许可，READY_FOR_INDEPENDENT_RUNTIME_DELTA_REVIEW_AFTER_R011_0016。下一步独立GPT签新完整Head；不重跑、不merge。详见 reports/E2/R011/RUNTIME_DELTA_HANDOFF.md。

当前 Issue #20 / R010：Shadow合作清理、必要server信号清理wrapper和跨版本只读TEST审计已完成；本机与Corelab普通/-O各118/118实际exit0，原14原件审计统计完全一致，原件与新CPU证明均两处验哈希。状态READY_FOR_INDEPENDENT_RUNTIME_DELTA_REVIEW，execution_authorized=false。旧R008暂停/R009失效；需GPT绑定最终完整新Head签新grant后，才可从0015继续，0016强制检查点。真实账本仍14已消耗（12SUCCESS，0010/0014 CLEANUP_ERROR）/106未执行。课程15页草稿与源码ZIP已准备，R3与最终提交未完成。不逐CPU错误请求批准，不自签、不重跑、不merge。见 reports/E2/engineering/RUNTIME_DELTA_HANDOFF.md 与 reports/E2/automation/AUTONOMOUS_STATUS.json。

当前 Issue #18 / R009：0011/0012及强制检查点通过后，0014再次CLEANUP_ERROR/exit1，已强制停止并关闭服务器。120计划=14已消耗（12SUCCESS+0010/0014两次清理故障）+106未启动；0015未预留。代码仍exact a1c6424bd348b36c55a20d38750a269e9551a698，无修复/重跑/merge。普通/-O停止审计与公开数值CPU核验均实际exit0，原件两处验哈希保全。当前STOPPED_FOR_REPEATED_CLEANUP_INCIDENT_REVIEW，下一步仅GPT事故审核及有界CPU生命周期修复授权，新代码须新grant后才能继续。详见 reports/E2/R009/R3_HANDOFF.md。

# Agent execution contract

本文件约束在本仓库工作的 Codex 或其他实现 agent。先阅读 `docs/STATUS.md`、`docs/CODEX_HANDOFF.md`、当前执行 issue 和 `docs/REVIEW_WORKFLOW.md`。更高优先级的用户及安全指令始终优先。

## 当前 Issue #16 / R008（优先于历史入口）

R008已授权exact `a1c6424bd348b36c55a20d38750a269e9551a698`，真实激活前置条件已核验。实际TEST在已消耗0010的CLEANUP_ERROR/exit1时按停止规则终止：10已预留（9正常+1清理错误）、110未启动。保全代码/科学冻结和全部原件，不重跑、不换ID、不自行继续下一格或修复执行代码；先提交GPT事故评估。详见 `reports/E2/R008/R3_HANDOFF.md`。Codex不自签R3、不自动merge。

## 当前 Issue #14 / R007（优先于历史入口）

R007=`SCOPED_CPU_REPAIR_AUTHORIZED / TEST_EXECUTION_SUSPENDED`。仅修改 TEST server launcher 的目录/授权收据交接及 CPU 集成测试；native server 独占 mkdir、全部科学与120格冻结保持不变。当前 main 的 R006 已暂停，不使用历史 grant 重启。交付 `READY_FOR_R007_FIX_REVIEW`，新完整 Head 必须由 GPT 审核并另签 R008 后才可启动 GPU/模型/仿真/TEST。保留原失败目录/收据，不 merge、不自签批准。详见 `reports/E2/R007/R007_FIX_HANDOFF.md`。

## 当前 Issue #10（优先于下方历史入口）

main/R005 条件科学冻结，TEST 未授权。Issue #10 从 PR #9 实时 head 建独立 stacked 分支，只实现固定120格 TEST 软件路径、CPU负测试及既有 CALIB 原件的 CPU 导出。不得重跑模型/CALIB或下载权重，不改冻结 k3/TaskSpec/oracle/C0/C2/split/seed/16-8-720。交付 `READY_FOR_R2_DELTA_REVIEW`，等待独立 GPT exact-head TEST 放行；许可协议见 `docs/work_packages/E2-TEST-ENTRY.md`。不伪造审核、不自动merge。

## 当前入口（E2）

Issue #8 / `docs/work_packages/E2-START-HERE.md`、R004 与 E2 工作包是当前执行依据。
R004 已替代 Issue #6 的旧 workspace/ledger 恢复前置条件。允许在合法可写新目录隔离安装双环境、下载必要官方权重并运行 E2 / TASE-002-v1.0。
新 DEV 最多24 attempts、独立短一致性验证最多96次；DEV前置条件通过后 CALIB最多48次；正式 TEST仍须R2。不搜索旧目录，不修改其他checkout，不把旧预算重置或混入新效果分母。下方初始授权文字仅为历史启动约束，不否定R004。

## Project boundary

- 这是 ME6401 运行时治理项目，不是 GR00T+WBC 科研仓库。
- 仅使用原生 GR00T N1.7 LIBERO-adapted checkpoint / LIBERO_PANDA / LIBERO 执行链。
- 不加入 WBC、Go2、ARX5、自定义 EEF10/rot6d 解码、其他研究模型继承链或新一轮训练。
- 第一版 Gate：`ACCEPT` 执行核验过的前缀；`REJECT` 阻止执行并终止该自主 episode；不自动 HOLD、REPLAN 或修改动作。

## Ownership and authority

- 用户负责资源授权、范围决定和最终课程提交；GPT 负责科学与工程审核；Codex 负责实现和证据交付。
- Codex 可以提交建议与 self-check，不得伪造 GPT 审核、篡改已签署审核文件或给自己签发阶段批准。
- `docs/STATUS.md` 中的 reviewer 决定必须指向独立审核记录。没有审核记录时只能写 `READY_FOR_REVIEW`，不能写 `APPROVED`。
- 当前初始授权仅覆盖 M0–M1 与不依赖 GPU 的接口/测试设计。M2 及后续正式运行需相应审核放行。
- 不需要为授权范围内的普通实现细节逐项请求确认；遇到科学协议、共享资源或范围变更才停在边界提交 change request。

## Scientific integrity

- 明确区分 `PLANNED`、`IMPLEMENTED`、`TESTED_LOCALLY`、`RUNTIME_VALIDATED`、`REVIEWED`。
- 模型权重、processor、statistics、embodiment、wrapper、控制器和 horizon 共同构成运行身份；不能只记录 checkpoint 名称。
- 不根据最终测试结果修改阈值、事件定义、场景、随机种子或排除规则。开发、校准、测试按初始化身份隔离。
- 不把没有事件标为安全证明；分母为零时给出 N/A；不得捏造示例结果作为实测。
- Gate 的风险特征与实际事件 oracle 分离。拒绝和基础设施错误必须分开统计。
- 保存失败、超时和中止；不以丢弃失败运行提高成功率。
- 一次正式比较只改变治理机制，保持原生 policy 和执行契约相同。

## Execution safety and public repository hygiene

- 仅在用户已授权的资源运行。先只读核查，不能停止其他任务、改变驱动、关闭 SSH 主机验证或删除共享目录。
- 审查上游安装脚本；已知 LIBERO setup 涉及环境目录和用户配置删除，必须隔离，不能盲跑。
- 不提交权重、数据集、资产、访问凭据、SSH 文件、内部主机/IP/用户名、完整环境变量或未脱敏日志。
- 不把原始课程 PDF、内部可行性报告或其他科研项目文件自动复制到公开仓库。
- 不上传外部遥测；如依赖默认启用 tracking，先禁用或取得授权。
- `git push --force`、重写既有证据、删除历史结果、修改仓库可见性/权限不属于本次授权。

## Delivery

- 从 `main` 建 `codex/<issue>-<scope>` 分支；一个有界工作包一个 PR。
- 每份运行报告绑定完整 commit SHA、配置哈希、artifact 清单和实际命令/退出码；不能只给截图或“已通过”。
- 单元测试使用 mock 必须标明；mock 不能替代真实 GR00T 或真实仿真验收。
- 实验代码提交后再运行正式实验；工作树若不干净，保存 patch/hash 并标为探索运行，不混入正式结果。
- 审核前更新 issue、PR、阶段报告和公开 artifact manifest。使用仓库模板。
- 不自动 merge 自己的 PR；获得当前 head 的审核结论后由用户或明确授权的 reviewer 合并。
- 按任务包预算停止，不无限重装、不无界续训、不在失败后悄悄换项目。
