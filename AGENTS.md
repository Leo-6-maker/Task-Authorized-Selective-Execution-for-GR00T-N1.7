# Agent execution contract

本文件约束在本仓库工作的 Codex 或其他实现 agent。先阅读 `docs/STATUS.md`、`docs/CODEX_HANDOFF.md`、当前执行 issue 和 `docs/REVIEW_WORKFLOW.md`。更高优先级的用户及安全指令始终优先。

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
