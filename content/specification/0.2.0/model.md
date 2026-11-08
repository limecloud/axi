# 数据模型

AXI JSON 表示由五种文档组成。它们可以是静态制品，也可以是现有协议中的结构化内容；`kind` 是数据类型标识，不是 RPC 方法名。

## 通用字段

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `spec_version` | 固定字符串 `0.2.0` | 本文档使用的 AXI 表示版本 |
| `kind` | 字符串枚举 | `catalog`、`action`、`result`、`page` 或 `batch` |
| `extensions` | 可选对象 | 显式命名空间下的可选扩展数据 |

**AXI-DATA-001**：采用 JSON 表示的实现必须验证当前文档类型，拒绝未知核心字段及不支持的版本；不得通过忽略拼写错误或默认成另一动作继续写入。

## 五种文档

| 类型 | 必要内容 | 用途 |
| --- | --- | --- |
| catalog | 提供方、目录修订、能力摘要 | 小型用途发现，可分页交换 |
| action | 名称、合同修订、副作用、输入/输出 Schema、上下文、恢复、绑定 | 精确执行合同 |
| result | 动作、合同修订、状态、上下文 | 单次读取或操作的当前回执 |
| page | 范围、查询修订、结果项、下一游标、快照模式 | 有界集合读取 |
| batch | 范围、逐项标识与回执、快照模式 | 独立只读操作集合 |

完整字段和可下载样例见[Schema 参考](../../reference/schema.md)。嵌入的业务 Schema 使用 JSON Schema Draft 2020-12；业务数据可有领域字段，AXI 包装层保持封闭。

## 动作的副作用

| `effect` | 含义 | 例子 |
| --- | --- | --- |
| `read` | 不修改业务状态 | 读取文档、查询原操作 |
| `view` | 仅改变当前本地视图 | 缩放、定位、选中 |
| `draft` | 写入可编辑草稿 | 保存未提交修改 |
| `submit` | 提交产生外部可见效果 | 记录审批、提交生成 |
| `irreversible` | 不能可靠撤回的业务变更 | 业务明确界定的永久操作 |

分类说明影响，不授予权限。`draft` 也属于写入，不能借“草稿”绕过身份和修订检查。

## 最小读取回执

```json
{
  "spec_version": "0.2.0",
  "kind": "result",
  "action": "documents.get",
  "contract_revision": "1",
  "status": "succeeded",
  "context": {"scope_id": "scope_demo", "resource_id": "doc_contract_001", "revision": 7},
  "data": {"review_state": "pending"}
}
```

`scope_id` 是示例工作区引用；当前身份由绑定提供。`revision` 可以是整数或字符串，客户端不应根据大小推断所有业务的版本先后。
