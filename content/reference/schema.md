# Schema 参考

本版使用 JSON Schema Draft 2020-12。[下载完整 Schema](../schemas/0.2.1/axi.schema.json)，可在离线验证器中使用。`$id` 是草案的标识，不是下载地址；内部 `$ref` 不依赖网络。

下面的表由同一 Schema 在构建时生成，只列无条件必填项。条件必填由 Schema 的 `allOf` / `oneOf` 和相应规范章节共同解释，不手工维护另一份字段定义。

## Catalog

<!-- axi-schema:catalog -->

目录条目的引用与动作合同需要进一步交叉检查，见[能力发现](../specification/0.2.1/discovery.md)。

## Action

<!-- axi-schema:action -->

写动作的 `idempotency.mode` 必须是 `required`，包括键字段、恢复动作和正整数保留秒数。必要上下文与键必须确实出现在必填输入中。嵌入的业务 Schema 要再做元 Schema 检查，见[执行](../specification/0.2.1/execution.md)。

## Result

<!-- axi-schema:result -->

`blocked`、`failed`、`unknown` 需要错误；`succeeded`、`pending`、`partial`、`cancelled` 需要业务数据；`pending`、`unknown` 需要原操作引用。`unknown` 固定使用 `result_unknown` 和恢复方向。写入其他非 blocked 状态也需要原操作引用，该条件依赖动作合同，由跨文档检查验证。

## Context

<!-- axi-schema:context -->

范围引用由服务端检查，不能从该字段推导权限。[上下文规范](../specification/0.2.1/context.md)定义切换、消歧与陈旧响应处理。

## Operation

<!-- axi-schema:operation -->

`input_digest` 固定为 `sha256:` 加 64 位小写十六进制。具体输入规范化由动作提供方公布，示例向量见[示例](../examples.md)。

## Page

<!-- axi-schema:page -->

非空游标的空页仍可继续；`consistent` 快照另需快照修订。见[分页](../specification/0.2.1/pagination.md)。

## Batch

<!-- axi-schema:batch -->

唯一项标识、整体与逐项状态的一致性、只读白名单和获权范围需要行为及交叉验证，见[批量读取](../specification/0.2.1/batch.md)。

## 验证器能力

```bash
uv run --no-project --with-requirements requirements-test.txt python scripts/validate-contracts.py
```

该命令固定校验本仓库的 Schema 与审批示例包，不是通用认证服务。它拒绝包外合同引用和联网解析；不会执行工具或访问生产资源。负例与事务测试见[验证指南](../verification.md)。
