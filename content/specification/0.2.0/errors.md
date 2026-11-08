# 错误

错误应让客户端知道已发生什么，以及哪种下一步是合理的。人可读消息用于解释，稳定错误代码用于分支。

## 错误结构

`error` 必须有 `code`、`message` 和 `resolution`；可选 `details` 只包含获权且非敏感的诊断数据。`resolution.kind` 为 `none`、`correct_input`、`read`、`recover`、`reauthenticate` 或 `request_decision`；后四种按需要包含动作名，结构要求以 Schema 为准。

**AXI-ERR-001**：错误必须区分输入、身份、权限、修订、幂等冲突、服务故障与结果未知；不得仅返回“失败，请重试”或根据自由文本决定是否重发写入。

| 标准代码 | 典型状态 | 客户端动作 |
| --- | --- | --- |
| `invalid_input` | blocked | 修正参数；不自动执行另一写入 |
| `missing_context` | blocked | 补充获权上下文，必要时请求决定 |
| `unauthenticated` | blocked | 在原任务中恢复身份 |
| `forbidden` | blocked | 停止越权路径，不通过换入口绕过 |
| `not_found` | blocked | 按提供方披露策略处理；不探测其他范围 |
| `revision_conflict` | blocked | 读取差异，重新判断原授权是否适用 |
| `idempotency_conflict` | blocked | 保留原键与输入，核对调用错误 |
| `operation_expired` | blocked | 原保留期已失效；不得假设无副作用 |
| `cursor_invalid` | blocked | 明确重建查询；不得静默遗漏旧页 |
| `unsupported_version` | blocked | 选择明确支持的合同，不猜测降级 |
| `rate_limited` | blocked / failed | 按绑定提示延后；写入先核对是否接收 |
| `unavailable` | blocked / failed | 只在确定未接收时重试；否则恢复原操作 |
| `deadline_exceeded` | pending / failed | 区分停止等待与业务失败 |
| `result_unknown` | unknown | 查询原操作，禁止换键重复提交 |

`pending` 的期限提示可放在 `data`；Schema 不要求它同时携带错误。扩展错误使用命名空间代码，例如 `review.policy_denied`，不能冒用标准代码。

## 传输与业务错误

JSON 无法解析、RPC 方法不存在或无法完成身份验证时，绑定可能在生成 AXI 回执前失败。客户端必须保留传输层错误语义，不伪造一个已经完成的业务操作。一次超时不说明请求从未抵达服务端。

**AXI-ERR-002**：恢复提示和 `next` 信息必须作为数据处理，不能提供新的授权；错误不得泄露凭据、无权对象存在性或未脱敏用户内容。

审批示例的冲突回执见[错误样例](../../examples/0.2.0/blocked.json)，超时演练见[恢复实践](../../practices/recovery.md)。
