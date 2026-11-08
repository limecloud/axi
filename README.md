# AXI 设计规范

> 面向 AI Agent 的操作界面设计标准，覆盖发现、定位、执行、观察、恢复与交付。

[在线阅读](https://limecloud.github.io/axi/)

## 简介

将 Agent 作为产品的一类正式使用者，为它提供与人类界面共享业务语义、权限和状态的操作界面。本规范使用 AXI 表示 Agent eXperience Interface；这是本规范的约定，不声明为行业统一标准或既有 AXI 项目的官方版本。

文档独立于特定业务、宿主和部署域名。外部资料集中在参考文献，正文完整说明采纳的规则，不以外链代替规范。

## 角色分流

- 产品与交互设计 → [规范首页](content/index.md)、[原则与架构](content/architecture.md)
- 开发工具、插件与网站 → [操作合同](content/contracts.md)、[发现与交付](content/discovery.md)、[浏览器界面](content/browser.md)
- 验收与维护 → [验证标准](content/verification.md)、[参考与取舍](content/references.md)
- 实际接入 → [合同示例与采用清单](content/examples.md)

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

构建后执行浏览器验收。第一次需要安装测试浏览器；已有 Chrome 时可通过 `AXI_BROWSER_PATH` 指定其可执行文件路径。

```bash
uv run --no-project --with-requirements requirements-test.txt playwright install chromium
uv run --no-project --with-requirements requirements-test.txt python scripts/verify-site.py
```

测试覆盖项目子路径、所有页面与站内链接、图表解析与渲染、桌面/手机布局、导航、搜索和无外部运行时请求。证据写入 `.dev/site-validation.json`。

## 配置 / 参数

| 名称 | 用途 | 是否必填 |
| --- | --- | --- |
| `AXI_SITE_URL` | 构建时的站点规范地址；Actions 自动提供 | 否 |
| `AXI_BROWSER_PATH` | 测试时使用的浏览器可执行文件绝对路径 | 否 |

## 部署说明

GitHub Pages 使用 [发布工作流](.github/workflows/pages.yml) 构建并上传 `site/`。推送 `main` 或手动触发工作流后，先完成严格构建和浏览器验收，再部署静态站点。Pages 的发布来源设置为 GitHub Actions。站点使用相对资源地址，图表脚本、字体和样式不依赖外站。

标准版本见 [规范首页](content/index.md)。正文、图表和示例作为一个版本审阅；第三方图表库的许可证、固定版本及摘要见 [资源清单](content/assets/third-party.json)。

## 边界

本规范不定义新的模型、Agent Runtime 或传输协议，不替代业务权限和服务端事务。符合规范需要行为与任务证据；文档完整或支持某个协议不能单独构成符合性声明。
