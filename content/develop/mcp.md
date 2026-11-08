# MCP 绑定

MCP 可以承载 AXI 能力。MCP 负责协议发现、调用、传输与其授权合同；AXI 补充产品任务的定位、状态、恢复与验收语义。本页是映射指南，本仓库没有实现 MCP Server。

## 映射

| AXI | MCP 接入方式 | 要保留的语义 |
| --- | --- | --- |
| 动作名称与用途 | tool 名称和 description | 命名空间、用途与选择条件 |
| input_schema | tool inputSchema | 必填、枚举、条件和未知字段拒绝 |
| 输出合同 | outputSchema 与 structuredContent | 当前状态、范围、修订、原操作与错误 |
| 目录/方法 | 明确的发现工具、资源或宿主索引 | 实际可用版本、按需读取与失效 |
| 副作用 | annotations 加正式业务校验 | annotations 是提示，不授予权限 |
| 原操作恢复 | 独立只读工具 | 查回同一操作，不重新执行写入 |

工具名可按 MCP 及宿主限制映射，但映射必须稳定、可发现，并保留 AXI 动作名与合同修订，不能因为字符替换发生名称碰撞。

## 结构化回执

示意结果如下；这是 MCP 内容包装，内层才是 AXI 回执：

```json
{
  "content": [{"type": "text", "text": "文档当前审批状态为 approved。"}],
  "structuredContent": {
    "spec_version": "0.2.0",
    "kind": "result",
    "action": "documents.get",
    "contract_revision": "1",
    "status": "succeeded",
    "context": {"scope_id": "scope_demo", "resource_id": "doc_contract_001", "revision": 8},
    "data": {"review_state": "approved"}
  },
  "isError": false
}
```

文字与结构必须一致；完整写入回执见[成功样例](../examples/0.2.0/succeeded.json)。MCP 协议错误和工具业务错误是不同层次，映射 `isError` 时遵守实际采用的 MCP 版本，不能把 JSON-RPC 接收成功当业务成功。

## 版本和渐进发现

采用方分别声明 MCP 协议版本与 AXI 规范/合同版本，使用所选 MCP 版本的能力发现和缓存失效规则。不能从 AXI `spec_version` 推断 MCP 初始化、每请求元数据或传输行为。

小工具集可以直接暴露；大集合按宿主支持采用渐进发现。未经兼容评审不应突然隐藏现有工具、改名或改成万能执行器。宿主缓存合同与模型只看当前候选可以同时实现。

## 安全和中断

保持 MCP 的来源信任、身份与调用审查。工具 annotations、资源文字和外部 Skill 不可提高授权。断线或取消 RPC 不等于领域操作已取消；写入结果不确定时按[恢复合同](../specification/0.2.0/recovery.md)查询原操作。

MCP 官方资料的采集版本和采用边界见[参考资料](../references.md)。协议升级必须独立验收，不能依据文档中的包装例子宣称互操作已通过。
