"""从导航、规范正文和 Schema 生成 Agent 入口与字段参考。"""

import hashlib
import json
from io import BytesIO
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from mkdocs.exceptions import PluginError
from mkdocs.structure.files import File


def navigation(items, parents=()):
    for item in items:
        if isinstance(item, str):
            yield parents, item
            continue
        for title, target in item.items():
            if isinstance(target, list):
                yield from navigation(target, (*parents, title))
            else:
                yield (*parents, title), target


def route(name):
    if name == "index.md":
        return ""
    if name.endswith("/index.md"):
        return name.removesuffix("index.md")
    return name.removesuffix(".md") + "/"


def requirements(config):
    output = []
    seen = set()
    docs = Path(config["docs_dir"])
    for path in sorted((docs / "specification").rglob("*.md")):
        for match in re.finditer(r"^\*\*(AXI-[A-Z]+-\d{3})\*\*[：:]\s*(.+)$", path.read_text(), re.M):
            identifier, text = match.groups()
            if identifier in seen:
                raise PluginError(f"重复要求编号：{identifier}")
            seen.add(identifier)
            name = path.relative_to(docs).as_posix()
            output.append({"id": identifier, "requirement": text, "source": name,
                           "url": route(name) + "#" + identifier.lower()})
    if not output:
        raise PluginError("没有找到规范要求")
    return {"spec_version": "0.2.1", "requirements": output}


def on_files(files, config, **kwargs):
    files.append(File.generated(config, "requirements.json", content=json.dumps(requirements(config), ensure_ascii=False, indent=2) + "\n"))
    skill = Path(__file__).resolve().parents[1] / "examples/review/skills/document-review/SKILL.md"
    bundle = BytesIO()
    with ZipFile(bundle, "w") as archive:
        entry = ZipInfo("document-review/SKILL.md", date_time=(1980, 1, 1, 0, 0, 0))
        entry.compress_type = ZIP_DEFLATED
        entry.external_attr = 0o100644 << 16
        archive.writestr(entry, skill.read_bytes())
    files.append(File.generated(config, "downloads/document-review-skill.zip", content=bundle.getvalue()))
    return files


def schema_type(value):
    if "$ref" in value:
        return value["$ref"].rsplit("/", 1)[-1]
    if "const" in value:
        return json.dumps(value["const"], ensure_ascii=False)
    if "enum" in value:
        return ", ".join(value["enum"])
    if "oneOf" in value or "anyOf" in value:
        return "组合类型"
    result = value.get("type", "任意 JSON")
    return " / ".join(result) if isinstance(result, list) else result


def on_page_markdown(markdown, page, config, **kwargs):
    schema = json.loads((Path(config["docs_dir"]) / "schemas/0.2.1/axi.schema.json").read_text())

    def table(match):
        definition = schema["$defs"][match.group(1)]
        rows = ["| 字段 | 类型 / 值 | 无条件必填 | 说明 |", "| --- | --- | --- | --- |"]
        for name, value in definition["properties"].items():
            required = "是" if name in definition.get("required", []) else "否"
            rows.append(f"| `{name}` | `{schema_type(value)}` | {required} | {value.get('description', '见对应规范章节')} |")
        return "\n".join(rows)

    markdown = re.sub(r"<!-- axi-schema:([a-z]+) -->", table, markdown)
    return re.sub(r"^(\*\*(AXI-[A-Z]+-\d{3})\*\*[：:])", lambda m: f'<a id="{m.group(2).lower()}"></a>\n\n{m.group(1)}', markdown, flags=re.M)


def on_post_build(config, **kwargs):
    docs = Path(config["docs_dir"])
    site = Path(config["site_dir"])
    base = config.get("site_url", "").rstrip("/")
    def address(path):
        return f"{base}/{path}" if base else path or "./"
    summary = [
        "# AXI",
        "",
        "> 面向 Agent 的操作界面：发现、定位、执行、观察、恢复与验证。",
        "",
        "独立设计草案；不是行业统一标准，也不隶属于同名项目。",
        "当前规范为 0.2.1 草案，未发布稳定版。文档不授予业务权限。",
        "",
    ]
    full = ["# AXI 设计规范全文", ""]
    index = []
    section = None
    for titles, name in navigation(config["nav"]):
        if titles[0] != section:
            section = titles[0]
            summary.extend(["", f"## {section}", ""])
        content = on_page_markdown((docs / name).read_text(), None, config)
        url = address(route(name))
        raw = address(name)
        summary.append(f"- [{' / '.join(titles[1:])}]({raw})")
        # 每页均有稳定 Markdown 地址；链接解析相对文档源路径。
        output = site / name
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content)
        full.extend([f"<!-- {name} -->", "", content, ""])
        index.append({"title": titles[-1], "section": titles[0], "url": url,
                      "markdown": raw, "source": name,
                      "sha256": hashlib.sha256(content.encode()).hexdigest()})
    summary.extend(["", "## 机器入口", "", f"- [要求索引]({address('requirements.json')})",
                    f"- [文档索引]({address('docs.json')})", f"- [Schema]({address('schemas/0.2.1/axi.schema.json')})",
                    f"- [完整 Markdown 正文]({address('llms-full.txt')})", ""])
    (site / "llms.txt").write_text("\n".join(summary))
    (site / "llms-full.txt").write_text("\n".join(full))
    root = docs.parent
    sources = {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not any(part in (".git", ".dev", "site", ".venv", "__pycache__") for part in path.relative_to(root).parts)
    }
    (site / "docs.json").write_text(json.dumps({"spec_version": "0.2.1", "pages": index, "build_source_sha256": sources}, ensure_ascii=False, indent=2) + "\n")
