# 分页与输出

集合读取必须有界，并让客户端知道是否还有内容。没有返回某项，可能表示未装载，不代表该项不存在。

## 页面结构

`page` 包含 `context`、`query_revision`、`items`、`next_cursor` 与 `snapshot`。游标是服务端定义的不透明字符串，客户端不能解析或自行加一。

**AXI-PAGE-001**：分页必须以 `next_cursor: null` 明确结束；空 `items` 配合非空游标仍表示可以继续。游标必须绑定原查询与适用范围，失效时明确返回 `cursor_invalid`，不得静默从第一页开始。

**AXI-PAGE-002**：提供方必须声明快照模式。`consistent` 表示各页属于同一已标识快照，必须包含 `snapshot.revision`；`best_effort` 表示列表可能在读取间变化，客户端不得据此声称全局一致。

```json
{
  "spec_version": "0.2.1",
  "kind": "page",
  "context": {"scope_id": "scope_demo"},
  "query_revision": "documents-name-contract-v1",
  "items": [],
  "next_cursor": "opaque_page_2",
  "snapshot": {"mode": "best_effort"}
}
```

不强制公开精确总量；总量未知时不能填 `0`。客户端可以在已找到唯一明确对象后停止翻页，但不能把未读取的分页包含在完整性声明中。

## 投影与截断

**AXI-OUT-001**：默认输出必须保留当前决定所需的身份范围、对象、修订、恢复、失败和费用单位；任何内容截断必须显式表达，并提供精确继续读取路径。

业务数据可以使用 `fields`、范围读取或资源链接；其具体输入由动作 Schema 定义。精简摘要与完整读取应该共享同一修订，避免摘要属于旧版而展开内容属于新版。不能只为了减少 Token 删除恢复操作键。

客户端读取上限应根据任务明确设置。超过上限时报告已读范围和继续游标，避免无限翻页。
