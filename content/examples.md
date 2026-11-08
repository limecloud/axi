# 合同示例与采用清单

本页以通用的“文档审批”任务说明合同如何协作。名称与标识仅用于独立示例，不对应任何已上线服务；示例不是必须照抄的传输协议。

## 1. 从目标找到准确入口

能力索引描述用途和所需上下文，不能提前声明用户已获权：

```json
{
  "spec_version": "0.1.0",
  "contract_version": "1",
  "capabilities": [{
    "name": "documents.review",
    "purpose": "检查指定文档并记录审批决定",
    "required_context": ["workspace_id", "document_id"],
    "read": "documents.get",
    "write": "documents.decide",
    "method": "review-method",
    "access": "not_checked"
  }]
}
```

用户已经给出明确文档时，直接读取原文档。未给出时，在当前获权范围按名称查询；有多个匹配就返回各自足以区分的业务信息。缺少上下文时返回 `missing_context` 及缺项，不生成指向默认工作区的链接。

## 2. 精确的动作 Schema

以下 Schema 描述记录审批决定的输入。可执行动作还需在能力元数据中声明写入副作用与恢复方法。

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "additionalProperties": false,
  "required": ["document_id", "expected_revision", "decision", "operation_key"],
  "properties": {
    "document_id": {"type": "string", "minLength": 1},
    "expected_revision": {"type": "integer", "minimum": 1},
    "decision": {"type": "string", "enum": ["approve", "request_changes"]},
    "comment": {"type": "string", "maxLength": 2000},
    "operation_key": {"type": "string", "minLength": 16, "maxLength": 128}
  },
  "allOf": [{
    "if": {"properties": {"decision": {"const": "request_changes"}}},
    "then": {"required": ["comment"], "properties": {"comment": {"minLength": 1}}}
  }]
}
```

服务端从当前会话核对工作区和审批权限，检查预期修订，验证原操作键与固定输入是否一致，再记录决定。`operation_key` 的格式校验不能代替幂等存储；同键不同输入必须拒绝。只读预检通过不能豁免写入时的重新校验。

## 3. 能指导恢复的结果

明确完成时返回当前状态与原操作引用：

```json
{
  "status": "completed",
  "operation_id": "op_review_001",
  "document": {"id": "doc_contract_001", "revision": 8, "review_state": "approved"},
  "verification": {"decision_recorded": true, "content_quality": "not_evaluated"}
}
```

修订冲突没有执行本次写入，调用者应先读差异，不能自动接受新版本后重提旧决定：

```json
{
  "status": "blocked",
  "error": {
    "code": "revision_conflict",
    "message": "文档已更新，需要核对变更后再决定",
    "retryable": false,
    "next": {"capability": "documents.get", "document_id": "doc_contract_001"}
  }
}
```

客户端未收到提交应答时，只能报告认知状态未知。使用原操作键查询结果；查询成功后沿同一操作继续。若恢复读取也失败，保留原键并说明阻塞，不新建另一审批操作。下一步字段只提供数据，不构成继续写入的授权。

## 4. 与页面定位保持一致

同一文档列表中出现多个“批准”按钮时，页面应通过命名区域区分，例如“文档：采购合同”和“文档：保密协议”。定位结果至少包含区域名称、对象引用、可访问名称、禁用状态及匹配数。

页面工具读到“允许批准”只是界面状态；服务端仍执行正式权限与修订校验。对话框打开后只定位当前对话框内的控件，不能点击背景里同名按钮。上下文变更或页面更新后重新确认目标，不能将一次控件引用永久复用。

## 5. 产品采用清单模板

采用方在自身文档中维护一份清单，不向本标准回填产品实现细节：

| 项目 | 必须填写的内容 |
| --- | --- |
| 声明范围 | 产品版本、目标宿主、采用的规范版本与核心任务 |
| 发现入口 | 用途索引、方法入口、Schema 及其版本关系 |
| 事实归属 | 当前对象、权限、修订、操作和费用的权威来源 |
| 定位合同 | 唯一对象标识、命名区域、歧义处理、深链与上下文隔离 |
| 动作合同 | 输入校验、副作用、前置、最终授权与幂等策略 |
| 观察与恢复 | 真实状态、等待期限、取消、部分失败与原操作恢复 |
| 可选能力 | 浏览器与站点工具支持范围、失败降级和人工接管 |
| 验证记录 | 精确制品、任务样本、测试结果、性能指标和未验证项 |
| 发布核验 | 远端制品、实际发现能力、目标环境与产物回读 |

每项要求应当关联到测试或明确的不适用理由。没有证据的项目不能标为通过；范围之外的能力不能被包含在整体完成声明中。
