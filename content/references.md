# 参考与设计取舍

资料核对日期：2026-11-08。以下是独立来源与适用范围，正文要求已经完整写入规范，不依赖读者跳转外站才能实施。外部页面更新不会自动修改本规范；变更采纳须重新评估与验证。

## 文档结构与生态依据

本轮按官方站点索引定位并读取正文，借鉴 MCP 的“概念—规范—开发—实践—参考”分层。规范页先说明范围，再给字段、约束、示例、状态/错误与安全边界；教程与权威合同分开。外部项目的品牌、组织结构和兼容声明不属于 AXI。

| 资料 | 本轮读取范围 | 独立采纳 |
| --- | --- | --- |
| [MCP 2026-07-28 规范](https://modelcontextprotocol.io/specification/2026-07-28/index.md) | 总览、工具、Schema、分页、取消、版本及贡献流程 | 明确规范状态、要求用语、机器合同、可选能力、版本与提案；不另造 MCP 传输 |
| [MCP 客户端实践](https://modelcontextprotocol.io/docs/2026-07-28/develop/clients/client-best-practices.md) | 渐进发现、宿主缓存与模型上下文 | 目录与精确合同分层，按任务证据决定是否增加检索 |
| [MCP Apps 概览](https://modelcontextprotocol.io/extensions/apps/overview#mcp-apps)与[构建指南](https://modelcontextprotocol.io/extensions/apps/build.md) | UI 资源、宿主桥接、沙箱、CSP、权限与支持条件 | 与结构化工具共享对象/授权，保留无 App 路径；不宣称所有宿主均支持 |
| [OpenAI Skills 概念](https://developers.openai.com/plugins/concepts/skills)与[构建](https://developers.openai.com/plugins/build/skills) | 元数据激活、方法资源及 MCP 协作 | Skill 是方法层，不替代实时数据、鉴权和受控动作 |
| [OpenAI 插件架构](https://developers.openai.com/plugins/concepts/plugins.md)与[打包](https://developers.openai.com/plugins/build/plugins) | 原生包、可移植格式、兼容入口、分发与组件 | 复用原生制品，区分包、服务与 UI 的版本 |
| [OpenAI 鉴权](https://developers.openai.com/plugins/build/auth.md) | 资源元数据、OAuth、PKCE、客户端识别和恢复 | 按宿主与协议支持交集接入，不复制固定回调或任意共享凭据 |
| [OpenAI 测试](https://developers.openai.com/plugins/deploy/connect-chatgpt.md)与[发布](https://developers.openai.com/plugins/deploy/submission.md) | 单项能力、安装后组合任务、新会话、更新与审核 | 逐层验证，发布后回读实际能力；不把平台审核定义成 AXI 自有认证 |
| [dsh-browser 固定源码](https://github.com/omdsh-dev/dsh-browser/tree/f7bafd3191e96745cb94a1074d189e23a30b3d3b) | README 中的桥接/扩展组成、文本快照、标签绑定和权限 | 原生适配与浏览器桥接分开，借鉴局部读取；不复用其基准为通用性能结论 |
| [POSIX Utility Conventions](https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap12.html) | 参数、选项、操作数和语法约定 | 与现代 CLI 设计配合，不声称长选项或 JSON 由 POSIX 强制规定 |
| [Command Line Interface Guidelines 源文](https://github.com/cli-guidelines/cli-guidelines/blob/main/content/_index.md) | 帮助、stdout/stderr、JSON、TTY、交互、信号及分发 | 明确机器模式与退出语义，叠加 AXI 范围、授权及恢复；这是社区设计指南 |

采集时 MCP 规范的 `latest` 指向 2026-07-28；OpenAI 鉴权页仍引用其明确支持的 MCP 授权版本。两者不是可自动互换的兼容承诺，采用方需要冻结实际交集。

CLI 指南站点在本次采集返回 403，使用其公开源码正文核对，未据此声称在线页面已成功访问。

## 术语与协议的区别

| 名称 | 主要讨论对象 | 本规范的关系 |
| --- | --- | --- |
| Agent Experience / AX | Agent 完成目标的整体体验 | 本规范关注其操作界面的可用性、效率和可靠性 |
| Agent-facing interface | 面向 Agent 的操作接口面 | 最直接的描述，不限定 CLI 或协议 |
| AXI / Agent eXperience Interface | 已有项目对 Agent 友好工具的一组设计原则 | 重要参考；本规范是独立采用和扩展，不冒称其官方规范 |
| Agentic UI / Generative UI / A2UI | 人通过 Agent 工作，或 Agent 生成供人操作的界面 | 与面向 Agent 的操作界面有关，但不能互相等同 |
| AG-UI | Agent 后端与用户前端之间的事件、状态和交互协议 | 解决另一层连接，不是替代工具发现和业务合同 |
| MCP | Agent 应用与工具/资源服务的协议 | 可承载 AXI 能力，协议兼容不等于交互质量合格 |
| WebMCP / Site tools | 网站向当前页面中的 Agent 暴露能力 | 浏览器增强，与独立服务工具互补 |
| Agent Skills | 可发现、按需读取的方法与支持资源 | 方法载体，不代替实时索引、Schema和状态 |

AX、AUI、AXI 的缩写尚未构成唯一统一的行业用语。交流时应写清全称与讨论层次，不仅凭缩写判断设计是否相同。

## 官方插件样本与本地工作区依据

2026-11-08读取OpenAI官方市场目录、manifest和下列README/方法，冻结提交`d420d13051bffe4543ed39e30fa46b87148e47dd`。官方收录不等于速度排名；本轮未安装或运行这些插件，不将静态方法文字声称为实际宿主性能。

| 来源 | 已读机制 | 采用与边界 |
| --- | --- | --- |
| [官方市场目录](https://github.com/openai/plugins/tree/d420d13051bffe4543ed39e30fa46b87148e47dd) | 原生插件/方法/工具按实际组件交付 | 载体与业务能力分开，按实际宿主冻结支持范围 |
| [Creative Production MCP说明](https://github.com/openai/plugins/blob/d420d13051bffe4543ed39e30fa46b87148e47dd/plugins/creative-production/mcp/README.md)及produce方法 | 本地修订看板、原始文件/有限预览/trace，open创建视图、后续小回执增量更新 | 同任务同视图，完整文件与轻回执分开；公开tree未取得核心store脚本，证据限于README和方法 |
| [Figma use方法](https://github.com/openai/plugins/blob/d420d13051bffe4543ed39e30fa46b87148e47dd/plugins/figma/skills/figma-use/SKILL.md) | 一次发现所需Schema、精确ID、类型按需读取 | 精确定位与有界上下文，不把其原子编辑声明推导为任意实现已支持 |
| [Canva编辑方法](https://github.com/openai/plugins/blob/d420d13051bffe4543ed39e30fa46b87148e47dd/plugins/canva/skills/canva-edit-design/SKILL.md) | transaction、operations、preview、commit/cancel | 相关编辑组合，保留事务或部分完成语义；不改变AXI核心只读批量范围 |
| [Adobe批量方法](https://github.com/openai/plugins/blob/d420d13051bffe4543ed39e30fa46b87148e47dd/plugins/adobe/skills/adobe-batch-edit-photos/SKILL.md) | preset按需发现、先样张、widget及非widget路径 | 渐进呈现与批次验证；非widget仍上传，不据此称纯本地 |
| [Remotion Studio方法](https://github.com/openai/plugins/blob/d420d13051bffe4543ed39e30fa46b87148e47dd/plugins/remotion/skills/remotion-studio/SKILL.md) | 本机工程、已有Studio复用、CLI渲染与真实URL | CLI与可选本地网页组合，不能从目录存在推导执行成功 |
| [HyperFrames CLI方法](https://github.com/openai/plugins/blob/d420d13051bffe4543ed39e30fa46b87148e47dd/plugins/hyperframes/skills/hyperframes-cli/SKILL.md) | HTML源、headless JSON检查、preview/render与质量档 | 源资料和交付分开、机器入口不依赖GUI |
| [Vercel插件说明](https://github.com/openai/plugins/blob/d420d13051bffe4543ed39e30fa46b87148e47dd/plugins/vercel/README.md)及CLI/verification方法 | 意图/实体/路径元数据、按任务reference、浏览器/API/真实数据核验 | 定位和方法分层，少工具不自动证明快或完整 |
| [Supabase方法](https://github.com/openai/plugins/blob/d420d13051bffe4543ed39e30fa46b87148e47dd/plugins/supabase/skills/supabase/SKILL.md) | 实际help、依赖/Schema检查、有界失败处理 | 先真实发现，保留阻塞，避免无限重试 |
| [Cloudflare官方MCP](https://developers.cloudflare.com/agents/model-context-protocol/cloudflare/servers-for-cloudflare/)及官方插件配置 | search/execute按需API发现与Code Mode | 确定编排放代码，不从Token宣传数推导其他任务倍数，不开放任意执行旁路 |
| [OpenAI Plugin Eval](https://github.com/openai/plugins/blob/d420d13051bffe4543ed39e30fa46b87148e47dd/plugins/plugin-eval/README.md)及benchmark-harness | 真实codex exec、成功清单、原始日志和用量；静态估计与实测分开 | 任务级性能/正确性证据，保留失败与样本条件 |
| [ChatCut固定源码](https://github.com/ChatCut-Inc/agent-plugin/tree/5b93f3afca456dc1dd1da01661ea3825846f83a8) | Desktop/local MCP、实际活动项目验证、旧Web项目与loopback媒体导入 | 页面/文件/执行位置分别声明；部分路线会上传，不能照搬为无隐式传输保证 |
| [OpenAI元数据优化](https://developers.openai.com/plugins/guides/optimize-metadata.md)、[工具规划](https://developers.openai.com/plugins/plan/tools.md) | 直接/间接/负例激活、明确输入与有限结果 | 正确首调先于减少点击，按任务评测选择准确性 |
| [MCP elicitation](https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation.md) | 客户端能力声明、form/URL、枚举和拒绝/取消 | 优先宿主原生选择；协议定义不证明特定宿主均支持，不收敏感输入或假定统一弹窗API |

| 文件与系统来源 | 已读机制 | 采用与边界 |
| --- | --- | --- |
| [Obsidian存储说明](https://github.com/obsidianmd/obsidian-help/blob/master/en/Files%20and%20folders/How%20Obsidian%20stores%20data.md)、[VS Code工作区](https://code.visualstudio.com/docs/editing/workspaces/workspaces) | 普通文件夹、Markdown/外部编辑、工作区配置及可重建cache | 目录作为用户内容边界，原操作事务不当cache清空 |
| [Quarto项目](https://quarto.org/docs/projects/quarto-projects.html)及[文本源](https://quarto.org/docs/get-started/hello/text-editor.html) | 文本/配置源、多格式生成、output-dir与预览 | 源和派生交付分开，避免多份可写权威源 |
| [Remotion资源](https://www.remotion.dev/docs/assets.md)、[渲染CLI](https://www.remotion.dev/docs/cli/render.md) | 相对媒体引用与本地输出 | 文件夹可容纳多种交付，逐格式验证不泛称任意媒体支持 |
| [Comfy CLI](https://docs.comfy.org/agent-tools/cli.md)、[MCP](https://docs.comfy.org/agent-tools/mcp.md)及[首次生成](https://docs.comfy.org/get_started/first_generation.md) | 本机执行、能力/工作流/结果取得、CLI下载磁盘 | CLI/MCP互补及按实际能力运行；不宣称采用方已集成这些模型 |
| [Blender依赖打包](https://docs.blender.org/manual/en/latest/files/blend/packed_data.html) | 可打包与不可打包依赖各有边界 | 交接清单记录缺依赖和质量范围 |
| [Local-first论文](https://www.inkandswitch.com/essay/local-first/) | 本地内容为主、可选云端 | 不是浏览器cache，不要求所有远程领域本地化，不强制构建CRDT平台 |
| [SQLite场景](https://www.sqlite.org/whentouse.html)、[应用文件格式](https://www.sqlite.org/appfileformat.html)、[WAL](https://www.sqlite.org/wal.html)、[备份](https://www.sqlite.org/backup.html) | 嵌入式事务、本机并发边界和一致快照 | 普通文件与内部事务分工，WAL不作网络多机协议，数据库快照不保证外部媒体一致 |
| [Apple目录](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/FileSystemOverview/FileSystemOverview.html)、[Windows Known Folder](https://learn.microsoft.com/en-us/windows/win32/shell/knownfolderid)、[XDG Base Directory](https://specifications.freedesktop.org/basedir/latest/) | 文档/应用数据/缓存/临时目录分工、重定向及有效绝对路径 | 产品公布OS默认根和解析，不硬编码用户名或把项目藏cache；混合平台文档按对应OS解释 |

freedesktop的xdg-user-dirs入口在本次访问受限，未将其挑战页当正文；不据此规定未经核验的目录API。具体默认目录、渐进引导和是否使用远程能力由产品目标决定，来源不构成统一拓扑或通用性能承诺。

## 其他一手资料与设计取舍

| 来源 | 可核对的依据 | 采用与证据边界 |
| --- | --- | --- |
| [AXI 项目](https://github.com/kunchenguid/axi) | 十项原则、CLI实例及作者发布的浏览器/GitHub评测 | 采用有界输出、明确错误、上下文和下一步；作者的模型、任务及实现对比不能推导成任何宿主都更快 |
| [Anthropic：Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) | 面向任务的工具、命名空间、有效上下文和评测 | 选择高价值操作，避免逐端点机械包装；以任务与负例验证 |
| [Anthropic：Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) | 按需发现、代码组合、减少中间上下文 | 确定逻辑放在代码；不据此向普通业务暴露任意执行权限 |
| [Vercel：AGENTS.md 与 Skills 评测](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals) | 特定 Next.js 任务中被动短索引与主动方法检索的差异 | 采用简短路标加按需方法；不泛化为 Skills 无用或必须修改全局文件 |
| [Vercel：减少 Agent 工具](https://vercel.com/blog/we-removed-80-percent-of-our-agents-tools) | 文档良好的语义数据层与文件系统 Agent 的特定案例 | 减少多余封装，先改善上下文；不把文件系统/SQL访问当所有产品默认入口 |
| [Agent Skills 规范](https://agentskills.io/specification) | 元数据、方法、支持文件与渐进披露 | 方法按需读取、包内引用可迁移；索引和实际版本一致 |
| [MCP 架构](https://modelcontextprotocol.io/docs/learn/architecture) | 工具、资源、Prompt及协议发现的职责 | 复用协议，最终身份和业务规则留在服务端 |
| [OpenAI：Site tools](https://learn.chatgpt.com/docs/webmcp) | 当前页面工具、共享会话、支持条件和逐调用检查 | 功能检测、窄工具、只读提示、保留普通界面；不假设所有账号和宿主均可用 |
| [WebMCP 草案](https://webmachinelearning.github.io/webmcp/) | 页面注册、执行、取消、作用域与权限合同 | 属持续变化的提案；实现时核对当前API及宿主，不冻结为强制协议 |
| [Chrome：WebMCP early preview](https://developer.chrome.com/blog/webmcp-epp) | 声明式和命令式页面能力接口方向 | 可探索增强，不替代语义HTML、权限和结果核验 |
| [OpenAI：插件 UI 指南](https://developers.openai.com/plugins/concepts/ui-guidelines) | 工具可独立完成核心目标，视觉用于检查和选择 | 可视化按需，不能把完整后台搬进卡片或假定专有桥通用 |
| [OpenAI：插件构建](https://developers.openai.com/plugins/build/plugins) | 插件、方法、工具配置及安装后引导 | 同版本交付和能力引导；插件不自行开启宿主权限 |
| [AG-UI](https://docs.ag-ui.com/introduction) / [A2UI](https://a2ui.org/) | 用户界面交互协议与生成式界面表示的分工 | 区分“Agent操作业务”与“Agent生成给人的UI”，按实际需要组合 |
| [Playwright 最佳实践](https://playwright.dev/docs/best-practices) | 用户可见定位、原生语义、自动等待和隔离 | 语义定位与可观察状态优先，避免CSS/XPath脆弱定位和固定暂停 |
| [Cloudflare：Markdown for Agents](https://blog.cloudflare.com/markdown-for-agents/) | 面向Agent的内容协商和精简读取 | 适用于文档读取；不能替代操作合同、身份和实时状态 |

## 对 AXI 十项原则的独立取舍

| 原则方向 | 本规范要求 |
| --- | --- |
| Token高效输出 | 高信息密度、有界结果；不强制TOON或固定宣称节省比例 |
| 最小默认字段 | 按决策裁剪，保留修订、恢复、成本和失败所需字段 |
| 内容截断 | 明确截断并可精确读取完整内容，不能静默丢失 |
| 预计算聚合 | 对真实常见路径减少往返，不为潜在需求添加巨型聚合 |
| 明确空状态 | 零结果与未加载、无权、失败分开表达 |
| 结构化错误 | 稳定分类、幂等及恢复，拒绝未知输入 |
| 环境上下文 | 显式限定账号和资源；不自动安装会话Hook或修改全局配置 |
| Content first | 已知目标快速读实际数据；不强制无参数命令自动联网 |
| 上下文式下一步 | 返回必要缺口、恢复入口和下一步，建议不等于授权 |
| 一致帮助 | 窄索引加按需Schema，保持版本可核对 |

本规范不复制外部项目的基准结论作为自身性能承诺，不要求安装参考项目，也不把某一种输出格式或浏览器框架设为符合性的必要条件。
