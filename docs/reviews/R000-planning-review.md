# R000 — 初始方案与有界启动审核

Reviewer role：GPT。日期：2026-10-21。协议：TASE-001 v1.0。类型：规划审核，不是运行验收。

## 审核依据

用户提供的课程说明、研究报告、可行性审查以及最新“原生LIBERO、不含WBC”的明确决定；目标GitHub仓库初始为空且公开；官方checkpoint材料与GR00T固定源码 `dac54b313160c201c450f97df0fd74ebd379c892` 的native wrapper、setup和rollout入口。

本文与同一bootstrap Git commit中的计划文件构成同一审核对象；实际commit身份以Git历史为准，不伪造未来SHA。

## 结论

`APPROVED_FOR_BOUNDED_BOOTSTRAP`。

批准Codex在已授权资源执行M0–M1及CPU侧接口/日志测试，总计最多24次开发episode runs。通过真实基线证据后提交R1；不自动进入正式TEST。

## 已确认

范围排除WBC；官方存在LIBERO post-trained路线；原生wrapper能够承接其action并进行夹爪转换；公开仓库应排除内部机器信息和大文件。详细来源记录见SOURCES。

## 未验证

本地部署、GPU预留、模型加载、EGL、task成功、shadow、Gate、事件标签和任何治理效果。本次没有登录GPU节点、启动训练或执行模型。项目不存在运行成功结论。

## R1必须审查

完整版本身份；原生obs/action契约；双相机与实际horizon；完整episode和重复正常任务成功；固定初始化；全量失败记录；资源成本；公开artifact卫生。

## 保留约束

不训练、不引入WBC、不访问正式TEST、不擅自修/平滑动作、不执行未经验证的hold、不删除共享配置、不停止其他任务。资源权限缺失时先报告。

## 发布状态说明

该review是本次用户请求下的GPT文档审核记录，不是假装有独立GitHub人类批准者。Codex不得修改本文为“运行通过”；后续审核新建R001等文件。
