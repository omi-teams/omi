"use strict";
const SVGNS = "http:" + "//www.w3.org/2000/svg"; // XML namespace id, never fetched
const NODE = {w: 176, h: 60, dx: 224, dy: 84};
const nodeClass = (s) => ({"in-progress": "working"}[s] || (STATUS[s] ? s : "planned"));
function svg(tag, attrs, text, kids) {
  const node = document.createElementNS(SVGNS, tag);
  if (text !== undefined && text !== null) node.textContent = text;
  for (const [k, v] of Object.entries(attrs || {})) node.setAttribute(k, v);
  for (const kid of kids || []) node.append(kid);
  return node;
}
function graphChart(name, g) {
  const rows = new Map(), at = new Map();
  for (const n of g.nodes) {
    const row = rows.get(n.layer) || 0;
    rows.set(n.layer, row + 1);
    at.set(n.id, {x: 24 + (n.layer - 1) * NODE.dx, y: 34 + row * NODE.dy});
  }
  const width = 48 + (g.summary.layers - 1) * NODE.dx + NODE.w, height = 54 + (Math.max(...rows.values()) - 1) * NODE.dy + NODE.h;
  const arrow = (id, cls) => svg("marker", {id, viewBox: "0 0 10 10", refX: "9", refY: "5", markerWidth: "7", markerHeight: "7", orient: "auto"},
    null, [svg("path", {d: "M0 0L10 5L0 10z", class: `g-arrow ${cls}`})]);
  const edges = [...g.edges].sort((a, b) => a.critical - b.critical).map((e) => {
    const [from, to] = [at.get(e.from), at.get(e.to)];
    const [x1, y1, x2, y2] = [from.x + NODE.w, from.y + NODE.h / 2, to.x - 2, to.y + NODE.h / 2];
    const mid = (x1 + x2) / 2;
    return svg("path", {d: `M${x1} ${y1} C${mid} ${y1} ${mid} ${y2} ${x2} ${y2}`, class: `g-edge${e.critical ? " crit" : ""}`,
      "marker-end": `url(#${e.critical ? "gc" : "ga"})`});
  });
  const heads = [...rows.keys()].map((layer) => svg("text", {class: "g-lh", x: 24 + (layer - 1) * NODE.dx, y: 16}, `Tầng ${layer}`));
  const nodes = g.nodes.map((n) => {
    const {x, y} = at.get(n.id);
    const status = `${GLYPH[n.status] || "○"} ${STATUS[n.status] || n.status}`;
    return svg("a", {href: taskHref(name, n.id), tabindex: "-1", class: `g-node ${nodeClass(n.status)}`}, null, [
      svg("title", {}, `${n.id} · ${n.title || "—"} · ${status}${n.critical ? " · trên đường găng" : ""}`),
      svg("rect", {x, y, width: NODE.w, height: NODE.h, rx: 8}),
      svg("text", {class: "g-id", x: x + 10, y: y + 18}, n.id),
      svg("text", {class: "g-ti", x: x + 10, y: y + 36}, n.title || "—"),
      svg("text", {class: "g-st", x: x + 10, y: y + 52}, status),
      ...(n.critical ? [svg("text", {class: "g-star", x: x + NODE.w - 20, y: y + 18, "aria-hidden": "true"}, "★")] : [])]);
  });
  return el("div", null, {class: "g-chart"}, [svg("svg", {width, height, viewBox: `0 0 ${width} ${height}`, "aria-hidden": "true", focusable: "false"}, null,
    [svg("defs", {}, null, [arrow("ga", ""), arrow("gc", "crit")]), ...heads, ...edges, ...nodes])]);
}
// No scope in the URL: the first active plan, else every task.
const graphScope = (d, scope) => d.scopes[scope] ? scope : d.plans.find((p) => p.status === "active")?.id || "all";
// Shorten node text to the box by measured width; hidden (phone) charts measure 0 and are refitted on resize.
function fitGraph() {
  for (const node of view.querySelectorAll(".g-ti, .g-st")) {
    const full = node.getAttribute("data-full") ?? node.textContent;
    node.setAttribute("data-full", full);
    node.textContent = full;
    let cut = full.length;
    while (cut > 1 && node.getComputedTextLength() > NODE.w - 20) node.textContent = full.slice(0, --cut).trimEnd() + "…";
  }
}
window.addEventListener("resize", () => { if (view.querySelector?.(".g-chart")) fitGraph(); });
const idList = (ids) => ids.length ? ids.join(", ") : "không có";
function graphItem(name, n) {
  const relations = [`Phụ thuộc: ${idList(n.depends)}`, `Chặn: ${idList(n.blocks)}`,
    ...(n.status === "blocked" ? [`Bị chặn bởi: ${n.blocked_by.length ? n.blocked_by.join(", ") : "chưa ghi rõ"}`] : n.waiting.length ? [`Đang chờ: ${n.waiting.join(", ")}`] : [])];
  return el("li", null, {class: `g-it${n.critical ? " crit" : ""}${n.status === "blocked" ? " blocked" : ""}`}, [
    box("g-who", [link(n.id, taskHref(name, n.id), "mono strong"), el("strong", n.title || "—"), statusChip(n),
      ...(n.critical ? [el("span", null, {class: "chip g-crit"}, [el("span", "★", {"aria-hidden": "true"}), el("span", " Đường găng")])] : [])]),
    link("Mở task →", taskHref(name, n.id), "go small"), el("p", relations.join(" · "), {class: "g-rel small muted"})]);
}
function graphPage(name, d, scope) {
  const g = d.scopes[scope];
  const plans = [...d.plans.map((p) => [p.id, p.id]), ["all", "Tất cả"]];
  const chips = el("nav", null, {class: "g-plans", "aria-label": "Chọn kế hoạch"}, plans.map(([id, text]) =>
    link(text, `${projectHref(name)}/graph/${enc(id)}`, `chip planned${id === scope ? " current" : ""}`)));
  chips.querySelectorAll("a")[plans.findIndex(([id]) => id === scope)].setAttribute("aria-current", "page");
  const s = g.summary;
  const head = box("stack", [heading("Đồ thị phụ thuộc"),
    el("span", `${name} · ${scope === "all" ? "tất cả kế hoạch" : scope} · phụ thuộc → task đứng sau`, {class: "muted small mono"})]);
  if (g.empty) return [head, chips, section("Sơ đồ", [box("g-blank", [el("p", "Chưa có task nào khai báo phụ thuộc.", {class: "strong"}),
    el("p", "Thêm dòng depends: TASK-124 vào phần đầu file task để thấy thứ tự và đường găng ở đây. Đồ thị chỉ để xem, không sửa được từ board."),
    link(`← Về dự án ${name}`, projectHref(name))])], null, "panel", "g-h")];
  const counts = [[s.tasks, "task"], [s.layers, "tầng"], [s.blocked, "bị chặn"],
    [s.critical, `task trên đường găng (còn ${s.critical_left} chưa xong)`]];
  const banner = g.cycles.length ? [el("div", null, {class: "g-warn", role: "alert"}, [
    el("h2", `Có vòng phụ thuộc, không thể xếp tầng cho ${s.cycle_tasks} task`),
    el("ul", null, {}, g.cycles.map((c) => el("li", c.join(" → "), {class: "mono"}))),
    el("p", "Cách sửa: bỏ một dòng depends trong vòng này. Các task còn lại vẫn hiển thị bên dưới.")])] : [];
  const legend = el("ul", null, {class: "g-legend", "aria-label": "Chú giải"}, [
    ...Object.keys(STATUS).map((st) => el("li", null, {}, [chip(`${GLYPH[st]} ${STATUS[st]}`, nodeClass(st))])),
    el("li", null, {}, [el("span", null, {class: "g-sw crit", "aria-hidden": "true"}), el("span", "Đường găng ★")]),
    el("li", null, {}, [el("span", null, {class: "g-sw", "aria-hidden": "true"}), el("span", "Phụ thuộc")]),
    el("li", null, {}, [el("span", null, {class: "g-sw box", "aria-hidden": "true"}), el("span", "Bị chặn (nét đứt)")])]);
  const diagram = s.tasks ? [legend, graphChart(name, g)] : [empty("Mọi task đều nằm trong vòng phụ thuộc.")];
  const layers = [...new Set(g.nodes.map((n) => n.layer))].map((layer) => el("li", null, {}, [
    el("h3", layer === 1 ? "Tầng 1 — không phụ thuộc task nào" : `Tầng ${layer}`),
    el("ul", null, {class: "g-items"}, g.nodes.filter((n) => n.layer === layer).map((n) => graphItem(name, n)))]));
  const diagramPanel = section(`Sơ đồ${g.cycles.length ? ` (không gồm ${s.cycle_tasks} task trong vòng)` : ""}`, diagram,
    "Bấm vào một ô để mở task · danh sách bên dưới có cùng nội dung", "panel g-wide", "g-h");
  diagramPanel.setAttribute("aria-hidden", "true");
  return [head, chips, el("ul", null, {class: "g-summary", "aria-label": "Tóm tắt"}, counts.map(([n, l]) =>
    el("li", null, {}, [el("b", num(n)), el("span", ` ${l}`, {class: "muted small"})]))), ...banner, diagramPanel,
    section("Danh sách phụ thuộc", [el("ol", null, {class: "g-layers"}, layers)], "Theo tầng, từ task gốc đến cuối kế hoạch", "panel", "g-l")];
}
