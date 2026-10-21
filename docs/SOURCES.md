# 来源、已核验事实与本版设计变更

日期：2026-10-21。来源分为用户提供材料、公开官方材料、本项目新设计；三者不混写。公开仓库不转载内部资料。

## A. 用户材料（负责人持有，不公开附件）

| ID | 材料 | 使用范围 |
|---|---|---|
| C1 | ME6401 Part 2 Project Information Sheet(2).pdf，8页 | 课程要求、交付、评分、截止 |
| P1 | deep-research-report-6401.md | 原GR00T+LIBERO治理研究方案与候选方向 |
| P2 | feasibility_review_20261021.md | 对接口、shadow、标签、统计和资源假设的纠偏 |
| D1 | 2026-10-21用户最新决定 | WBC不纳入；Gate嵌入原生LIBERO action执行；GPT审核、Codex执行、GitHub记录 |

C1定位：p1截止/目标；p2允许现成模型且聚焦一个问题；p3–5机制及实验证据；p7 slides和源码；p8评分。项目个人作业，占50%；2026-11-06 23:59 SGT提交CANVAS；封面另计、最多15页内容、参考文献另计、无口头报告、源码ZIP带README。

P1/P2中的内部资源检查属于历史瞬时状态，不构成本轮资源授权或本地运行验证。不在公开文档披露其中主机、账号、路径或SSH信息。原文件未作为本仓库公开数据集上传。

## B. 官方公开来源

| ID | 来源 | 本项目使用的依据 |
|---|---|---|
| U1 | [NVIDIA GR00T-N1.7-LIBERO model card](https://huggingface.co/nvidia/GR00T-N1.7-LIBERO) | LIBERO post-trained模型存在；模型许可及输出为连续动作 |
| U2 | [NVIDIA LIBERO example, pinned](https://github.com/NVIDIA/Isaac-GR00T/blob/dac54b313160c201c450f97df0fd74ebd379c892/examples/LIBERO/README.md) | 官方模型server/client评价与LIBERO任务路线 |
| U3 | [LIBERO native wrapper, pinned](https://github.com/NVIDIA/Isaac-GR00T/blob/dac54b313160c201c450f97df0fd74ebd379c892/gr00t/eval/sim/LIBERO/libero_env.py) | 原生相机/state/action、axis-angle、夹爪映射、step边界 |
| U4 | [Rollout entry, pinned](https://github.com/NVIDIA/Isaac-GR00T/blob/dac54b313160c201c450f97df0fd74ebd379c892/gr00t/eval/rollout_policy.py) | Horizon contract、wrapper、episode控制；必须继续追踪实际执行栈 |
| U5 | [LIBERO setup, pinned](https://github.com/NVIDIA/Isaac-GR00T/blob/dac54b313160c201c450f97df0fd74ebd379c892/gr00t/eval/sim/LIBERO/setup_libero.sh) | 独立sim环境、依赖pin以及删除路径风险 |
| U6 | [LIBERO官方仓库](https://github.com/Lifelong-Robot-Learning/LIBERO) | 任务/BDDL/初始化与仿真实现；实际版本由submodule锁定 |
| G1 | [NIST AI RMF官方入口](https://www.nist.gov/itl/ai-risk-management-framework) | 自愿性风险管理与trustworthiness设计/使用/评价逻辑 |

本轮实际读取U1、U3、U5及U4入口相关部分，查询上游main解析到 `dac54b313160c201c450f97df0fd74ebd379c892`；U2官方网页同时核查。没有下载权重、追踪全部调用图或运行代码。因此source verification不是runtime validation。

P2提供的HF候选revision `2ea293aa20ba7cf5bbf3ba17a5fbcb1a01cbfe21` 未在本轮下载验证，正式身份由M0核对；不得写成已验证兼容组合。

官方模型卡存在跨模型描述，涉及确切输入维数/方向/动作转换时以绑定版本wrapper、processor和运行契约为准，不从概述推断实现。

## C. 治理依据的使用方式

本项目以NIST AI RMF 1.0风险管理逻辑作背景，不宣称标准合规或认证；官方入口在查询时注明1.0正在修订。课程最终参考文献必须注明采用版本和访问日期，不写未经核验的“最新版2.0”。

框架到本项目的设计映射：GOVERN对应角色和变更权限；MAP对应场景和错误物体风险；MEASURE对应事件、覆盖/误拒、任务与成本；MANAGE对应执行限制和中止。此表是本项目映射，不是NIST对本项目的认可。

## D. 相对原P1的明确修订

| 原候选内容 | 本版决定 | 理由 |
|---|---|---|
| 广义goal progress＋release＋distractor风险 | 聚焦wrong-object grasp/lift，几何授权特征 | 正常操作不保证距离单调；收缩范围 |
| ACCEPT/REPLAN/SAFE HOLD | ACCEPT/REJECT/ERROR，中止自主episode | 不将未知hold/replan当作恢复保证 |
| 多suite/五任务/多baseline | Object三任务、B0/G为主 | 降低deadline关键路径 |
| 所有挑战统称模型失误 | C0/C1/C2分开，C2明确人工意图错配 | 保证事件来源可解释 |
| 80/100场景视为硬门槛 | 初始预算＋事件数/成本驱动的R2冻结 | 非课程规定，也非统计充分性保证 |
| chunk统计与闭环混合 | 固定候选选择性评价＋episode结果 | 干预后不能强配chunk |
| temporal monitor作为自动救场 | 必须change request后重新定义问题 | 一致地抓错也可能通过时序检查 |
| 治理后成功率应更高 | 首版拒绝终止，报告任务损失 | 不偷偷把拒绝包装成恢复 |

## E. 尚待验证的事实

本地GPU资源、EGL、显存峰值、完整模型动作合同、三个task的对象名单、shadow状态完整性、事件可靠性、自然违规数量、合适margin和效果大小均未由本次文档提交验证。

本文与各计划中的样本数、容差、日期分工、主指标、模块名和审核关口属于本项目设计建议，不应被引用成官方要求或实测结果。
