# AXI 设计规范

> 面向 Agent 的操作界面草案，协同 CLI、MCP、Skills、插件和交互视图，覆盖安装到退役的生命周期。

[在线阅读](https://limecloud.github.io/axi/)

## 简介

将 Agent 作为产品的一类正式使用者，为它提供与人类界面共享业务语义、权限和状态的操作界面。当前为 AXI（Agent eXperience Interface）0.2.1 草案，不声明为行业统一标准或既有 AXI 项目的官方版本。

文档独立于特定业务、宿主和部署域名。外部资料集中在参考文献，正文完整说明采纳的规则，不以外链代替规范。

## 角色分流

- 理解与试跑 → [首页](content/index.md)、[本地快速上手](content/start/quickstart.md)
- 产品接入 → [生态分层](content/ecosystem/index.md)、[生命周期](content/lifecycle/index.md)、[提供方指南](content/develop/provider.md)
- 宿主适配 → [Codex 开放接口](content/ecosystem/codex/index.md)、[Claude Code](content/ecosystem/claude-code/index.md)、[WorkBuddy](content/ecosystem/workbuddy/index.md)、[DSH](content/ecosystem/dsh/index.md)
- 合同实现 → [版本化规范](content/specification/0.2.1/index.md)、[Schema](content/schemas/0.2.1/axi.schema.json)
- 维护与验收 → [验证](content/verification.md)、[采用清单](content/reference/adoption.md)、[贡献](content/community/contributing.md)

## 快速上手

### 前置条件

- Python >= 3.11。
- `uv`，或能创建独立虚拟环境的 Python 包管理器。

### 安装与运行

在本目录执行，依赖仅安装到工具管理的隔离环境：

```bash
uv run --no-project --with-requirements requirements.txt mkdocs serve --dev-addr 127.0.0.1:8000
uv run --no-project --with-requirements requirements.txt mkdocs build --strict
```

### 测试

先验证合同与参考行为，再构建和验收文档站。第一次需要安装测试浏览器；已有 Chrome 时可通过 `AXI_BROWSER_PATH` 指定其可执行文件路径。

```bash
uv run --no-project --with-requirements requirements-test.txt python scripts/validate-contracts.py
uv run --no-project --with-requirements requirements-test.txt python -m unittest discover -s tests -v
uv run --no-project --with-requirements requirements.txt mkdocs build --strict
uv run --no-project --with-requirements requirements-test.txt playwright install chromium
uv run --no-project --with-requirements requirements-test.txt python scripts/verify-site.py
```

合同检查验证目录、Schema、示例和方法引用；行为测试验证同键重放、并发、应答丢失恢复、撤权、CAS、保留期和事务回滚。文档站检查覆盖项目子路径、全部页面与链接、要求索引、原文下载、方法包、图表、桌面/手机布局、导航和搜索。证据写入 `.dev/`。

## 配置 / 参数

| 名称 | 用途 | 是否必填 |
| --- | --- | --- |
| `AXI_SITE_URL` | 构建时的站点规范地址；Actions 自动提供 | 否 |
| `AXI_BROWSER_PATH` | 测试时使用的浏览器可执行文件绝对路径 | 否 |

## 部署说明

GitHub Pages 使用 [发布工作流](.github/workflows/pages.yml) 构建并上传 `site/`。推送 `main` 或手动触发工作流后，先完成合同、行为、严格构建和浏览器验收，再部署静态站点。Pages 的发布来源设置为 GitHub Actions。站点使用相对资源地址，图表脚本、字体和样式不依赖外站。

标准版本见 [规范首页](content/index.md)。正文、图表和示例作为一个版本审阅；第三方图表库的许可证、固定版本及摘要见 [资源清单](content/assets/third-party.json)。

## 边界

本规范不定义新的模型、Agent Runtime、包格式、授权或传输协议，不替代业务权限和服务端事务。参考代码只实现本地审批，MCP、MCP Apps、插件和 DSH 目前提供集成指南；各载体的实现与验证边界见[兼容性矩阵](content/ecosystem/compatibility.md)。符合性需要精确制品与任务证据。
