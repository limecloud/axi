# 操作合同导读

操作合同说明一项能力如何被发现、针对哪个对象执行，以及结果不明确时如何恢复。精确规则集中在版本化规范，本页提供阅读路径。

## 从目标到结果

| 实现问题 | 权威章节 | 关键检查 |
| --- | --- | --- |
| 在哪里做 | [能力发现](specification/0.2.1/discovery.md) | 用途、合同引用、版本和缓存失效 |
| 对谁操作 | [上下文与定位](specification/0.2.1/context.md) | 范围、唯一对象、修订和歧义 |
| 是否允许 | [执行与授权](specification/0.2.1/execution.md) | 用户意图、最终权限、输入和前置 |
| 做成什么 | [结果与状态](specification/0.2.1/results.md) | 接收、在途、完成、质量分别表达 |
| 怎样继续 | [错误](specification/0.2.1/errors.md)与[恢复](specification/0.2.1/recovery.md) | 稳定分类、原键、保留期和未知 |
| 怎样少等待 | [分页](specification/0.2.1/pagination.md)、[批量](specification/0.2.1/batch.md)、[等待](specification/0.2.1/wait.md) | 有界、逐项、取消和一致性 |

## 可执行合同

字段形状以[JSON Schema](schemas/0.2.1/axi.schema.json)为准；业务与顺序要求见规范正文。将同一合同映射到不同载体时，保留对象、权限、副作用和恢复语义，而不是强求相同命令名称。

从[审批示例](examples.md)开始实现，再按[采用清单](reference/adoption.md)明确任务、绑定和证据范围。
