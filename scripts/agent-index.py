"""从同一正文生成供 Agent 读取的入口，不维护第二份规范。"""

from pathlib import Path


def on_post_build(config, **kwargs):
    docs = Path(config["docs_dir"])
    site = Path(config["site_dir"])
    base = config.get("site_url", "").rstrip("/")
    summary = [
        "# AXI 设计规范",
        "",
        "> 面向 Agent 的操作界面：发现、定位、执行、观察、恢复与验证。",
        "",
        "独立设计草案；不是行业统一标准，也不隶属于同名项目。",
        "规范版本与用语以首页为准。文档不授予业务权限。",
        "",
        "## 规范正文",
        "",
    ]
    full = ["# AXI 设计规范全文", ""]
    for item in config["nav"]:
        title, name = next(iter(item.items()))
        route = "" if name == "index.md" else name.removesuffix(".md") + "/"
        summary.append(f"- [{title}]({base}/{route})")
        full.extend([f"<!-- {name} -->", "", (docs / name).read_text(), ""])
    summary.extend(["", f"- [完整 Markdown 正文]({base}/llms-full.txt)", ""])
    (site / "llms.txt").write_text("\n".join(summary))
    (site / "llms-full.txt").write_text("\n".join(full))
