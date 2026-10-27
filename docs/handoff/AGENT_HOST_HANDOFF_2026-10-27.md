# 新主机完整接续交接

2026-10-27 SGT，Codex executor。负责人要求“先把完整内容提交 GitHub”，本轮交付为代码、公开证据、课程材料和私有证据索引的集中交接。没有执行场景或实验；没有给自己签发科学审核。较早的网络故障记录保持原样，最新情况以本文件与 HOST_HANDOFF_STATUS.json 为准。

## 必须分别获取的四条分支

仓库：https://github.com/Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7

| 内容 | 分支 / PR | 本轮读取的完整身份 |
|---|---|---|
| R014 报告、新主机入口、CPU 保全 | codex/33-r014-scene-inspection / #34 | 本文件所在最终提交；交接前 Head dfd0141b9ff85ff23cd21681a76ec8543b8106c7，base 9599f2e1b8d8ad4a51cb79cd7274f3daff493d42 |
| 获准 E3 执行源码 | codex/31-e3-cpu / #32 | 9599f2e1b8d8ad4a51cb79cd7274f3daff493d42，base 79510d9a302eeb7820f7ed35463c29bc649e1431 |
| E2 完整 120 格、R3 审核材料 | codex/28-r013-test / #30 | 3484f3de388df63ea1a758dfd6ff4cfa545b2333，base 79510d9a302eeb7820f7ed35463c29bc649e1431 |
| 最终课程备用稿及源码 | codex/20-course-draft / #22 | 73ddec9790c8540ad2b1faec6c989c7172cc5078，base 29f50b36af25a8b76583308cf0e5fbbe22365f27 |

以上 PR 在交接读取时均为 draft / open / unmerged。main 主要保存独立审核与计划，不包含全部实现/成果。不要根据旧 PR 正文猜 Head，也不要合并这些分支以制造一个未经批准的执行版本。新主机先实时读 PR head/base；变化时区分报告变化和执行源码变化。

在合法可写的新目录克隆后，可用以下方式拆分只读材料和实际执行身份（已有同名目录则先检查，不能覆盖）：

```bash
git clone https://github.com/Leo-6-maker/Task-Authorized-Selective-Execution-for-GR00T-N1.7.git tase-handoff
cd tase-handoff
git fetch origin
git switch --track origin/codex/33-r014-scene-inspection
git worktree add --detach ../tase-r014-exact 9599f2e1b8d8ad4a51cb79cd7274f3daff493d42
git worktree add --detach ../tase-e2-final 3484f3de388df63ea1a758dfd6ff4cfa545b2333
git worktree add --detach ../tase-course-final 73ddec9790c8540ad2b1faec6c989c7172cc5078
```

这些操作不安装环境、不启动模型或仿真。正式计算仍复用计算节点已经建立的双环境和权重。若 GitHub 认证方式不同，使用新主机已有合法方式，不转移旧主机凭据。

## 已完成与未完成

E3 P0 成果保全、P1 静态核验、P2 CPU 工程经 R014 有条件通过。9 个任务、36 个官方初始化内容身份、106 个资产 XML 的旧静态核验在 Issue31 已完成；不等于本轮现场重验。160 个拟议 TEST（A112/B48）均未预留；场景探针仍 0 构造 / 0 初始化；模型、server、Shadow、policy 请求及显式主动作均为 0。协议仍 PROPOSED，Gate P 科学冻结与 Gate C TEST 授权均待独立 GPT。

CPU：既有本机/Corelab 普通及 -O 均 187/187、实际 0；R014 阶段又在干净 exact9599 本机执行普通及 -O，各 187/187、实际 0。原始日志/退出收据哈希见 reports/E3/R014/CPU_REGRESSION.json。交接仅改文档/保全索引，无执行源码、配置或测试漂移；不为文档修改重复模型/回归。

网络：上一轮三个连接超时均实际 255，负责人要求先保全 CPU。本轮负责人报告计算节点已恢复；旧主机一次只读连接实际 255，远端在密钥交换阶段关闭连接，无远端输出。这个事实不等于新主机无权限，也不等于 GPU 仍不可用。没有继续搜索旧目录、修改 SSH/主机密钥、启动服务或停止其他项目进程。

## 新主机的唯一下一项运行工作

执行 Issue33 的 R014 有界场景身份核验，先完成全部实时前置条件：

1. 先读 AGENTS、docs/STATUS、docs/CODEX_HANDOFF、docs/REVIEW_WORKFLOW、Issue33 全文、E3 Master Plan、R014 报告和签署 JSON。当前报告引用的 R014 是独立 GPT 签署文件；执行者不得改写。
2. 复用任务自有 workspace、server/sim Python、官方权重和固定 GR00T/LIBERO。核对真实节点、HOME、UID/GID、mount、项目 ownership/storage alias、checkout status、活动进程和现有 stage。保留任何失败/部分 stage，不能删除锁、覆写输出或修改其他研究 checkout。
3. 机器许可必须从独立签署提交读取：`--review-commit eac3d8edeb3de7a33727d462ea652d7719e03629 --review-path docs/reviews/R014-E3-SCENE-INSPECTION-AUTHORIZED.json`。授权执行 Head **9599f2e1b8d8ad4a51cb79cd7274f3daff493d42**；grant 文件 SHA256 **adddb3e67480c7f03c29b6313782fd46e3e084a5bd27e1a490eedc69be71b7f7**。重新获取当前 main，确认尚未暂停/替代，不把报告分支 Head 当执行 Head。
4. **在任何 MuJoCo 构造前**运行 CPU-only `e3.scene.verify_inventory()`，重验现场全部 106 XML、BDDL、初始化文件/36 内容身份，以及 pin。保存路径/字节/hash 的私有清单、真实开始和退出收据，必须实际 exit0。源码清单 configs/e3_sources.proposed.json SHA256 **c10d2640e1176a3f19e19ee806e3703c6f55213f0d623dba872d65b8c0b58b37**。探针本身不会自动代替这项全 XML 检查。
5. 负责人已对本轮 R014 明确回复 **“授权本轮使用 GPU1”**：9 环境/36 初始化、零模型/零 TEST，并行但不得干扰其他任务。原许可持续有效，无需为同范围重复询问。它不是继承 R013，也不替代实际 UUID/EGL/空闲至少 9 GiB/任务隔离核验。尚未取得本轮真实 UUID，allocation JSON 未完成，禁止填猜测值。
6. 完成双备份可访问性和资源/授权/身份核验后，只执行一次有界 `e3.scene_probe`，使用原 scripts/record_process.py 与独占的新收据输出；至多 9 环境构造、36 初始化加载。任何异常保留原 ID/目录/退出，不自行换 ID 重跑。零模型、零 TEST、零 server、零 Shadow、零显式主动作。不沿用 E2 TEST grant。
7. 保存编译后 TaskSpec/物体几何身份、全部开始/关闭/退出、资源释放与两处逐文件 hash 证明。探针只做环境构造与 set_init_state，**不是**正式 native reset/seed+10 settling+完整动作流程验证，不能声称物理/Shadow/模型一致性已通过。
8. 提交集中审核包与新完整报告 Head，申请独立 Gate P/C。没有新的精确版本正式 TEST_AUTHORIZED 不得执行 E3 160 次。

## 私有运行定位与备份

完整主机、账号、GPU UUID、路径、原始日志和 runtime map 不公开到 GitHub。新主机通过负责人既有 SSH 配置进入已授权节点；不要复制私钥或改主机验证。

计算节点项目的 HOME 相对入口是 `Projects/me6401-e2`。优先只读既有 operator receipts 定位，不做无界全盘搜索：

- `operator/issue31-e3-cpu-01/CPU-code-location.private.json`：E3 CPU 源码实际位置；旧 CPU 快照是 f8f4348dfc77eb0b40f85080b664d45ee368e86a，不能替代场景授权 exact9599。
- `operator/environment-copy-05/launch.json` 的 derived_environments：既有 server/sim 双环境。不要重装、重下 Object/Cosmos 或借用其他研究 checkout。
- `operator/e2-storage-alias.json`：runs 实际挂载/缓存身份；`operator/issue28-frozen-code` 为旧 E2 exact795，不是 E3 执行 checkout。
- 固定上游 `upstream/Isaac-GR00T` dac54b313160c201c450f97df0fd74ebd379c892；其 LIBERO 8f1084e3132a39270c3a13ebe37270a43ece2a01。
- `operator/issue33-r014-01` 与缓存 `issue33-r014-code-01` 是先前拟议 staging 名称，**未确认创建**。先检查是否存在/部分写入，不假定成功，不覆盖。
- `evidence_exports/` 下存私有归档。既有 E3 CPU 两地 proof stage 为 issue31-e3-corelab-CPU-proof-01、issue31-e3-local-CPU-handoff-01，详见公开 proof JSON。

新 R014 本机 CPU 原件包 stage **issue33-r014-local-CPU-preservation-01**：638492 字节、31 成员、SHA256 **5bc28bf84a0bd03401d8a4723ce3e00129027b97c9dbefdbf3df78ddeec751b7**。本机整包和每成员已验；**远端副本待同步**。不能用 Issue31 的旧双备份证明声称新包已两处。负责人可将本轮单独提供的私有 host-transfer 归档安全传给新主机，校验 transport receipt 后，再独占复制至远端并逐成员核验。不得上传该私有包至公开仓库。

## E2 与课程成果不会因 E3 换主机而丢失

PR30 的 reports/E2/R013/final120/R3_HANDOFF.md、R3_REVIEW_PACKET.md、ledger、冻结审计、original manifest、backup_verification、公开导出和 origin bindings 是完整 E2 入口。120/120 永久消耗：89 SUCCESS、18 TIME_LIMIT、10 SEMANTIC_ABORT、0010/0014/0016 三次 CLEANUP_ERROR；117 可纳入完整结果、3 删失。失败不得改写/重跑；独立 R3 尚待完成。

原 18070 文件 canonical manifest SHA256 **9e4ce4d233e1d2ff6fc3d2154a099cb1721d4f9140a01463ccb184851277d603**。两处完整覆盖通过既有 checkpoint 归档依赖与最终 closure 证明，不能表述为存在两份独立的 3.59GB standalone 归档。最终覆盖 stage issue28-final120-original-coverage-01，836321 字节/60 成员，SHA256 **1c75486418dffaae40977fcd3a7f65d6c89b2f5855e34b5ae2d1b980a00cacd3**；完整审阅证明 stage issue28-final120-review-proof-01，45472580 字节/2461 成员，SHA256 **616cc772e0a1e1c97af977779b7178a728cb058c08d1534758b2490c13dff9ec**。全部原件详细依赖以 PR30 backup_verification 为准。本轮只验证了本机 2725 公开证据及 4 课程文件未变，没有重新核验所有远端原件。

PR22 的最终备用材料：

- submission/R3-review-draft/ME6401-full120-review-v3.pptx：15 页可编辑；236896 字节；SHA256 **9ace8d2172635c1fde1272eb69c7e5b7e29fa35cd9a2a6b9bf04a2647f7a9b00**。
- submission/R3-review-draft/SOURCE_R013_FINAL.zip：108 源码文件；259224 字节；SHA256 **e3553716d8cd01dc13d9963b9329e73bf38c13cc4c9f7e35dae2e7dd9c66e3d3**；普通/-O 各134、实际0。
- 同目录 FULL120_VERIFICATION.json、FULL120_MANIFEST.json、README 说明来源、局限及最终版本。

课程 deadline 2026-11-06 23:59 SGT，11/06 不做实验；E2-only 备用优先。主人身份、课程政策、AI 披露、最终提交仍待负责人完成，不可标记已提交。不得将 E3 提案或合成示例混作真实实验结果。

## 旧松散修改已保全

本机旧 PR5 工作区有 README/STATUS 修改及早期 TAKEOVER_REPORT/CPU 失败日志，课程旧工作区还有 v2 PPTX 与 SOURCE_R013.zip。全部 15 个松散文件/patch 已原样私有归档，原工作区未 reset/更改。另在 reports/E3/R014/SUPERSEDED_LOOSE_SNAPSHOTS.zip 发布可公开的历史副本：正文旧本机路径已替换，原始身份及每成员 hash 见相邻 JSON。其旧状态、失败和 v2 不能覆盖本交接、R004 后的新批次或最终课程 v3。无需新 agent 再从送修旧电脑恢复 workspace。

新主机的第一个具体交付是 **实时 CPU 106 XML 前置检查收据和完整 R014 现场身份检查结果**；如果访问/资源仍阻塞，则只提交准确失败收据并推进无阻塞的 E2 R3/课程核验，不能虚报场景通过。
