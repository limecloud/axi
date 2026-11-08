/* 图形为本文档的一部分，使用本地资源，不依赖外站脚本。 */
mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: "neutral", flowchart: { htmlLabels: false }, fontFamily: "system-ui, sans-serif" });
const diagrams = [...document.querySelectorAll(".axi-diagram")];
const sources = diagrams.map(node => node.textContent);
// Mermaid 接收纯文本，Markdown 生成的 code 容器不能进入图表解析器。
diagrams.forEach((node, index) => {
  node.textContent = sources[index];
  node.tabIndex = 0;
  node.setAttribute("role", "region");
  node.setAttribute("aria-label", "图表，可使用方向键横向滚动");
});
mermaid.run({ nodes: diagrams }).then(() => {
  diagrams.forEach(node => {
    const svg = node.querySelector("svg");
    // 长流程保留文字尺寸，在图表区域滚动，避免整图缩成不可读的小字。
    if (svg?.viewBox.baseVal.width) svg.style.minWidth = `${Math.ceil(svg.viewBox.baseVal.width)}px`;
  });
}).catch(() => {
  diagrams.forEach((node, index) => {
    if (node.querySelector("svg:not([aria-roledescription='error'])")) return;
    node.textContent = sources[index];
    node.setAttribute("aria-label", "图表渲染失败，以下为图表源文本");
  });
});
