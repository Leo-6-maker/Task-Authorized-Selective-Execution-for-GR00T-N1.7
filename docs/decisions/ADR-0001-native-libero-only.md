# ADR-0001 — Native LIBERO only; no WBC

日期：2026-10-21。状态：ACCEPTED SCOPE DECISION。依据：项目负责人明确要求。

## 决定

使用LIBERO-adapted GR00T N1.7经匹配官方processor/wrapper输出并执行原生LIBERO action。Safety Gate位于policy输出与原生动作执行之间。WBC不作为模块、依赖、实验baseline或课程贡献。

第一版以官方Object checkpoint建立基线；不把“还需完成自研GR00T+WBC微调”当作课程前置条件，也不因此授权新训练。

## 保留

保留LIBERO/Panda自带低层控制器及仿真执行。它不是用户科研项目中的WBC。Gate只许可/拒绝，不接管任务规划或生成替代动作。

## 拒绝语义

REJECT阻止候选前缀并结束当前自主episode。没有真实硬件safe-hold承诺；重试/恢复属于未来独立扩展。

## 原因

原生模型与环境匹配让主要实验变量成为治理机制，而不是新本体/动作接口适配。与课程强调治理工程而非基础模型训练一致。

## 影响

不复用旧项目EEF10、rot6d、H40或速度阈值；只复用严谨的版本、日志和审核习惯。源代码/权重是否在本地可用仍需M0/M1验证。

## 变更条件

引入WBC、其他本体、重新训练或换action契约需负责人明确决定和新的ADR/协议版本，不属于Codex常规工程自主修改。
