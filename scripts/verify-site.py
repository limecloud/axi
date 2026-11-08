"""验证真实静态站点；以项目子路径模拟 GitHub Pages。"""

import hashlib
import json
import os
import re
import tempfile
import threading
from datetime import datetime, timezone
from functools import partial
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
from zipfile import ZipFile

import yaml
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
EVIDENCE = ROOT / ".dev"


class Document(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.links = []
        self.ids = set()
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        attribute = "href" if tag in ("a", "link") else "src"
        if tag in ("a", "link", "script", "img") and attribute in attrs:
            self.links.append(attrs[attribute])


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def source_hashes():
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(ROOT.rglob("*"))
        if path.is_file() and not any(part in (".git", ".dev", "site", ".venv", "__pycache__") for part in path.relative_to(ROOT).parts)
    }


def main():
    frozen_sources = source_hashes()
    assert (SITE / "index.html").is_file(), "请先运行 mkdocs build --strict"
    documents = {p: Document(p) for p in SITE.rglob("*.html")}
    checked_links = 0
    for page, document in documents.items():
        for href in document.links:
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc or href.startswith("//"):
                continue
            path = unquote(parsed.path)
            if path.startswith("/"):
                path = path.removeprefix("/axi/").lstrip("/")
                target = (SITE / path).resolve()
            else:
                target = (page.parent / path).resolve() if path else page
            if target.is_dir():
                target /= "index.html"
            assert target.is_relative_to(SITE), f"站外本地路径：{page.name}: {href}"
            assert target.is_file(), f"失效链接：{page.relative_to(SITE)}: {href}"
            if parsed.fragment and target in documents:
                assert unquote(parsed.fragment) in documents[target].ids, f"失效锚点：{href}"
            checked_links += 1

    manifest = json.loads((ROOT / "content/assets/third-party.json").read_text())
    vendor = ROOT / "content/assets/mermaid.min.js"
    assert hashlib.sha256(vendor.read_bytes()).hexdigest() == manifest["sha256"]
    source_pages = sorted((ROOT / "content").rglob("*.md"))
    for page in source_pages:
        assert not re.search(r"纸团|zhituan|/Users/|limecloud|file://", page.read_text(), re.I), f"业务耦合：{page.name}"
    diagrams = [match.group(1) for page in source_pages for match in re.finditer(r"```mermaid\n(.*?)```", page.read_text(), re.S)]
    assert diagrams, "未找到规范图表"
    assert (SITE / "llms.txt").is_file() and (SITE / "llms-full.txt").is_file()
    agent_index = json.loads((SITE / "docs.json").read_text())
    assert agent_index["build_source_sha256"] == frozen_sources, "构建产物与当前源码不一致，请重新构建"
    requirements = json.loads((SITE / "requirements.json").read_text())
    assert requirements["requirements"], "要求索引为空"
    for item in requirements["requirements"]:
        parsed = urlsplit(item["url"])
        target = SITE / parsed.path / "index.html"
        assert target in documents and parsed.fragment in documents[target].ids, item

    # SafeLoader 不识别 MkDocs 的配置标签，只需读取导航的纯 YAML 片段。
    config_text = (ROOT / "mkdocs.yml").read_text()
    nav_text = re.search(r"(?ms)^nav:\n(.*?)(?=^[^ \n]|\Z)", config_text).group(1)
    navigation = yaml.safe_load(nav_text)
    def pages(items):
        for item in items:
            for title, name in item.items():
                if isinstance(name, list):
                    yield from pages(name)
                else:
                    route = "" if name == "index.md" else name.removesuffix("index.md") if name.endswith("/index.md") else name.removesuffix(".md") + "/"
                    yield title, route
    routes = list(pages(navigation))
    assert len(routes) == len(source_pages) == len(agent_index["pages"]), "导航与正文不一致"
    for item in agent_index["pages"]:
        path = SITE / item["source"]
        assert path.is_file(), "Markdown 下载缺失"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
        assert "<!-- axi-schema:" not in path.read_text(), "Markdown 字段表未展开"
    with ZipFile(SITE / "downloads/document-review-skill.zip") as package:
        assert package.namelist() == ["document-review/SKILL.md"]
        assert package.read("document-review/SKILL.md") == (ROOT / "examples/review/skills/document-review/SKILL.md").read_bytes()
    exported = [href for href in re.findall(r"\]\(([^)]+)\)", (SITE / "llms.txt").read_text())]
    exported.extend(item[field] for item in agent_index["pages"] for field in ("url", "markdown"))
    for href in exported:
        path = unquote(urlsplit(href).path)
        target = (SITE / path.removeprefix("/axi/").lstrip("/")).resolve()
        if target.is_dir():
            target /= "index.html"
        assert target.is_relative_to(SITE) and target.is_file(), f"失效 Agent 入口：{href}"

    EVIDENCE.mkdir(exist_ok=True)
    errors, remote_requests, responses, cases = [], [], [], []
    with tempfile.TemporaryDirectory(prefix="axi-site-") as tmp:
        (Path(tmp) / "axi").symlink_to(SITE, target_is_directory=True)
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=tmp))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        origin = f"http://127.0.0.1:{server.server_port}"
        base = origin + "/axi/"
        try:
            with sync_playwright() as playwright:
                launch = {"headless": True}
                if os.environ.get("AXI_BROWSER_PATH"):
                    launch["executable_path"] = os.environ["AXI_BROWSER_PATH"]
                browser = playwright.chromium.launch(**launch)
                browser_version = browser.version
                for width, height in [(1440, 1000), (390, 844)]:
                    context = browser.new_context(viewport={"width": width, "height": height})
                    page = context.new_page()
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.on("request", lambda request: remote_requests.append(request.url) if not request.url.startswith(origin + "/") and request.url.startswith(("https:", "http:")) else None)
                    page.on("response", lambda response: responses.append({"url": response.url, "status": response.status}) if response.status >= 400 else None)
                    rendered = 0
                    for title, route in routes:
                        print(f"检查 {width}px {route or '/'}", flush=True)
                        response = page.goto(base + route, wait_until="networkidle")
                        assert response.status == 200, route
                        assert page.locator("article h1").count() == 1, title
                        if not route:
                            parsed = page.evaluate("""async sources => { for (const source of sources) await mermaid.parse(source); return sources.length; }""", diagrams)
                            assert parsed == len(diagrams)
                        count = page.locator(".axi-diagram").count()
                        if count:
                            page.wait_for_function("""() => [...document.querySelectorAll('.axi-diagram')].every(node => node.querySelector('svg') && !node.querySelector('.error-icon'))""")
                            rendered += count
                        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), f"页面横向溢出：{title} {width}"
                        cases.append({"page": route or "/", "viewport": width, "diagrams": count, "status": "passed"})
                        if route in ("", "architecture/"):
                            page.screenshot(path=str(EVIDENCE / f"{route.strip('/') or 'index'}-{width}.png"), full_page=True)
                    assert rendered == len(diagrams), "浏览器图表数量不匹配"
                    page.goto(base, wait_until="networkidle")
                    if width == 1440:
                        page.wait_for_function("""() => !document.querySelector('.md-search-result__meta').textContent.includes('正在初始化')""")
                        page.locator(".md-search__input").fill("Schema")
                        page.locator(".md-search-result__item").first.wait_for()
                        assert page.locator(".md-search-result__item").count() > 0
                        page.keyboard.press("Escape")
                    else:
                        page.locator('header label[for="__drawer"]').click()
                        page.locator('.md-nav--primary label').filter(has_text=re.compile(r"^\s*参考\s*$")).last.click()
                        page.locator(".md-nav--primary").get_by_role("link", name="合同导读", exact=True).click()
                        page.wait_for_url(base + "contracts/")
                        assert page.locator("article h1").inner_text().startswith("操作合同")
                    context.close()
                browser.close()
        finally:
            server.shutdown()
            thread.join()

    assert not errors, errors
    assert not responses, responses
    assert not remote_requests, remote_requests
    assert frozen_sources == source_hashes(), "验证期间源码变化，证据失效"
    result = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "scope": "项目子路径上的真实静态站点与 Chromium；不代表任何业务宿主或业务任务验收",
        "browser_version": browser_version,
        "pages": len(routes),
        "viewports": [1440, 390],
        "local_links_checked": checked_links,
        "diagrams_parsed": len(diagrams),
        "requirements_indexed": len(requirements["requirements"]),
        "markdown_pages": len(agent_index["pages"]),
        "search": "passed",
        "mobile_navigation": "passed",
        "external_runtime_requests": remote_requests,
        "page_errors": errors,
        "cases": cases,
        "source_sha256": frozen_sources,
    }
    (EVIDENCE / "site-validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("source_sha256", "cases")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
