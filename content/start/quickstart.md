# 快速上手

用一个本地文档审批例子验证 AXI 的最短闭环：读当前对象，以固定输入提交，模拟应答丢失，再查回原操作。本例不访问外部服务，不需要浏览器或真实账号。

## 前置条件

需要 Python 3.11 或更高版本和 `uv`。以下命令在仓库根目录执行，依赖装入隔离环境。数据库路径由你指定；`init` 只在文档表为空时添加示例文档，不重置现有数据。

```bash
uv run --no-project --with-requirements requirements-test.txt python scripts/validate-contracts.py
uv run --no-project --with-requirements requirements-test.txt python -m unittest discover -s tests -v
```

第一条检查 Schema、所有 JSON 示例与合同引用，第二条检查审批执行、修订冲突、撤权、同键重放和未知结果恢复。

## 1. 创建并读取示例对象

```bash
uv run --no-project --with-requirements requirements-test.txt python examples/review/provider.py --db .dev/review.sqlite init
uv run --no-project --with-requirements requirements-test.txt python examples/review/provider.py --db .dev/review.sqlite get
```

初始文档为 `scope_demo` 中的 `doc_contract_001`，修订为 `7`。读取结果显示当前审批状态及修订。示例身份由程序固定，不从输入中的范围标识推导权限。

## 2. 提交并模拟丢失应答

```bash
uv run --no-project --with-requirements requirements-test.txt python examples/review/provider.py --db .dev/review.sqlite decide --input content/examples/0.2.1/review-input.json --drop-response
```

程序先持久化审批，再输出 `unknown` 并以退出码 `3` 结束，模拟客户端未收到提交应答。数据库中可能已发生副作用，不能通过换键重试判断结果。

## 3. 恢复原操作

```bash
uv run --no-project --with-requirements requirements-test.txt python examples/review/provider.py --db .dev/review.sqlite recover --key review_contract_001
uv run --no-project --with-requirements requirements-test.txt python examples/review/provider.py --db .dev/review.sqlite get
```

恢复返回原操作的 `succeeded` 回执，文档修订为 `8`。用同一文件再次 `decide` 会返回同一回执；同键改变决定或修订则返回 `idempotency_conflict`。这里的 `succeeded` 仅表示决定已记录，内容质量仍为 `not_evaluated`。

## 示例边界

本例用 SQLite 事务保存领域写入与操作记录，便于观察原子性。它没有真实会话、网络传输、计费、异步工作器或持久恢复 SLA。测试中的失权由模拟身份注入，只证明调用顺序和拒绝行为。生产实现见[提供方指南](../develop/provider.md)。

下一步：阅读[数据模型](../specification/0.2.1/model.md)，或运行[文档站验收](../verification.md)。
