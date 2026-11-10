# 示例

本组示例使用独立的“文档审批”领域说明 AXI 0.2.1。它不对应已上线业务，不依赖外部账号、图片或服务。

## 文件

| 文件 | 用途 | 验证方式 |
| --- | --- | --- |
| [catalog.json](examples/0.2.1/catalog.json) | 三项能力的轻量目录 | AXI Schema 与引用一致性 |
| [review-action.json](examples/0.2.1/review-action.json) | 审批输入、输出、授权与恢复合同 | Schema、业务 Schema 和恢复动作解析 |
| [get-action.json](examples/0.2.1/get-action.json) | 读取文档 | Schema 与目录一致性 |
| [recover-action.json](examples/0.2.1/recover-action.json) | 查回原操作 | Schema 与目录一致性 |
| [review-input.json](examples/0.2.1/review-input.json) | 固定审批输入 | 审批 input_schema |
| [succeeded.json](examples/0.2.1/succeeded.json) | 决定持久化后的回执 | AXI 与业务输出 Schema |
| [unknown.json](examples/0.2.1/unknown.json) | 应答未知与原操作引用 | 恢复字段、错误和输入摘要 |
| [blocked.json](examples/0.2.1/blocked.json) | 条件修订冲突 | 稳定错误与读取方向 |
| [page.json](examples/0.2.1/page.json) | 空页仍有下一游标 | 游标与快照模式 |
| [batch.json](examples/0.2.1/batch.json) | 只读批量的成功/拒绝混合 | 唯一 item_id、逐项状态与范围 |

## 跑通闭环

按[快速上手](start/quickstart.md)创建本地数据库、读修订、提交并模拟丢失应答、重启后恢复。参考代码位于仓库的 `examples/review/provider.py`，行为测试在 `tests/test_contracts.py`。

示例回执的 `op_review_001` 是固定夹具标识；参考程序实际生成唯一操作标识。输入摘要由同一规范化规则生成，测试校对固定向量。

## 规范化向量

示例只允许字符串与整数输入。移除 `operation_key` 后，按键排序，以无多余空格的 UTF-8 JSON 编码，`ensure_ascii=False` 且拒绝 NaN；该字节串的 SHA-256 加 `sha256:` 前缀作为摘要。

```json
{"decision":"approve","document_id":"doc_contract_001","expected_revision":7,"scope_id":"scope_demo"}
```

这不是对任意浮点数、Unicode 归一化或跨语言 JCS 的完整实现。生产合同应明确自己的规范化规则和跨语言测试向量。

## 覆盖边界

本例已覆盖本地原子写入与幂等顺序，不包含生产身份、MCP 传输、页面工具、下游收费或异步调度。夹具中的 page 和 batch 只验证数据合同，不表示参考 CLI 已实现分页与批量执行器。生产接入按[验证层次](verification.md)补充真实任务证据。
