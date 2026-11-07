"use strict";
function healthAlerts(name, alerts) {
  if (!alerts.length) return [];
  const items = alerts.map((a) => el("li", null, {class: "alert"}, [
    box("who", [link(a.id, taskHref(name, a.id), "mono strong"), el("span", a.title, {class: "strong"}),
      el("span", null, {class: "chip warn"}, [el("span", "⚠", {"aria-hidden": "true"}), el("span", " " + a.chip)])]),
    link("Xem task →", taskHref(name, a.id), "go small"),
    el("p", a.reason, {class: "why"}),
    el("p", null, {class: "do"}, [el("b", "Việc nên làm:"), el("span", " " + a.action)])]));
  return [section(`Cảnh báo sức khỏe (${num(alerts.length)})`, [el("ul", null, {}, items)], "Việc có dấu hiệu bị kẹt", "health", "health-h")];
}
// Weekly report: a pure Markdown builder (d = project view, cost = /cost view, now = Date).
function weeklyReport(name, d, cost, now) {
  const day = (ms) => new Date(ms).toISOString().slice(0, 10);
  const since = day(now.getTime() - 7 * 86400000);
  const tasks = Object.values(d.kanban).flat().filter((t) => !(t.children || []).length);
  const line = (t) => `- ${t.id}: ${String(t.frontmatter.title || "").replace(/\s+/g, " ")}`;
  const list = (items, mapper) => items.length ? items.map(mapper) : ["- Không có."];
  const byStatus = (s) => tasks.filter((t) => statusOf(t) === s);
  const recent = new Set(d.activity.filter((a) => a.time && a.time.slice(0, 10) >= since).map((a) => a.id));
  const done = byStatus("done");
  const doneIds = new Set(done.map((t) => t.id));
  const next = byStatus("planned").filter((t) => String(t.frontmatter.depends || "").split(/[,\s]+/).filter(Boolean).every((x) => doneIds.has(x)));
  const decisions = d.decisions.map((x) => x.replace(/^- /, "")).filter((x) => /^\d{4}-\d\d-\d\d/.test(x) && x.slice(0, 10) >= since);
  const t = cost.totals;
  return [`# Báo cáo tuần: ${name}`, `Từ ${since} đến ${day(now.getTime())}`,
    "## Việc đã xong", ...list(done.filter((x) => recent.has(x.id)), line),
    "## Đang làm", ...list(byStatus("in-progress").concat(byStatus("review")), line),
    "## Bị chặn", ...list(byStatus("blocked"), line),
    "## Quyết định", ...list(decisions, (x) => `- ${x}`),
    "## Token và chi phí (toàn dự án)", `- Token vào: ${num(t.input)}; ra: ${num(t.output)}; cache: ${num(t.cache)}; lượt chạy: ${num(t.runs)}`,
    `- Chi phí: ${cost.has_prices ? usd(t.cost) : "Chưa có giá"}`,
    "## Việc kế tiếp", ...list(next, line)].join("\n\n").replace(/\n\n(?=- )/g, "\n") + "\n";
}
async function downloadReport(name, d, button) {
  button.disabled = true;
  try {
    const response = await fetch(`/api/projects/${enc(name)}/cost`, {cache: "no-store"});
    if (!response.ok) throw new Error(String(response.status));
    const now = new Date();
    const href = URL.createObjectURL(new Blob([weeklyReport(name, d, await response.json(), now)], {type: "text/markdown;charset=utf-8"}));
    const a = el("a", null, {href, download: `bao-cao-tuan-${name}-${now.toISOString().slice(0, 10)}.md`});
    document.body.append(a);
    a.click();
    setTimeout(() => { a.remove(); URL.revokeObjectURL(href); }, 1000);
  } catch (e) { showError(e); } finally { button.disabled = false; }
}
function dashboard(name, d) {
  const tasks = Object.values(d.kanban).flat();
  const report = el("button", "Tải báo cáo tuần", {type: "button", class: "btn"});
  report.addEventListener("click", () => downloadReport(name, d, report));
  const waiting = d.po_waiting.map((w) => {
    const t = tasks.find((t) => t.id === w.id);
    return box("poi", [link(w.id, taskHref(name, w.id), "mono strong"), el("span", t?.frontmatter.title || "", {class: "strong"}),
      chip(`${REASON[w.reason] || w.reason}${w.text ? " · " + w.text : ""}`, "warn"), link("Xem task →", taskHref(name, w.id), "push small")]);
  });
  const count = leafCounts(d);
  const stats = [[d.po_waiting_count, "Chờ PO"], [count["in-progress"], "Đang làm · task lá"], [count.blocked, "Bị chặn · task lá"], [count.done, "Task lá đã xong"]];
  const activity = d.activity.slice(0, 30).map((a) => box("fi", [el("span", a.time ? a.time.slice(11, 16) : "—", {class: "muted small"}),
    el("span", null, {}, [link(a.id, taskHref(name, a.id), "mono"), el("span", ` ${a.text}`)])]));
  const decisions = d.decisions.slice(0, 20).map((x) => {
    const text = x.replace(/^- /, "");
    const date = text.match(/^\d{4}-\d{2}-\d{2}/);
    return box("fi", [el("span", date ? `${date[0].slice(8, 10)}/${date[0].slice(5, 7)}` : "—", {class: "muted small"}),
      el("span", date ? text.slice(10).replace(/^[: ]+/, "") : text)]);
  });
  const u = d.usage;
  return [box("heading", [box("stack", [heading(name),
    el("span", "origin/main", {class: "muted small mono"})]),
    box("chips", [report, link("Chi phí và quota →", `${projectHref(name)}/cost`, "small"), link("Đồ thị phụ thuộc →", `${projectHref(name)}/graph`, "small"), chip(d.source.sha.slice(0, 7), "mono")])]),
    ...healthAlerts(name, d.alerts || []),
    section(`Chờ PO (${num(d.po_waiting_count)})`, waiting.length ? waiting : [empty("Không có việc chờ PO.")], "Những việc cần anh/chị quyết", "po"),
    box("stats", stats.map(([n, label], i) => box("stat", [el("div", num(n), {class: "n"}, i === 3 ? [el("span", ` / ${num(Object.values(count).reduce((a, b) => a + b, 0))}`, {class: "denom"})] : []), el("div", label, {class: "l"})]))),
    section("Kế hoạch", [box("", d.plans.length ? d.plans.map(planRow) : [empty("Chưa có kế hoạch.")])], `${num(d.plans.length)} kế hoạch · ${num(d.plans.filter((p) => p.status === "active").length)} đang chạy`),
    ...filterWorkspace(name, tasks),
    box("grid2", [section("Hoạt động", [box("feed", activity.length ? activity : [empty("Chưa có hoạt động.")])]),
      section("Quyết định", d.decisions_text ? [pre(d.decisions_text)] : [box("feed", decisions.length ? decisions : [empty("Chưa có quyết định.")])])]),
    section("Sử dụng", [el("p", `${num(u.totals.runs)} lượt · ${num(u.totals.output)} output`, {class: "usage-summary muted small"}),
      table(["Model", "Lượt", "Input", "Output", "Cache"],
      [...Object.entries(u.models), ["Tổng", u.totals]].map(([m, r]) => [m, num(r.runs), num(r.input), num(r.output), num(r.cache)]),
      "Bảng sử dụng token")], `Vòng review: ${num(u.totals.review_rounds)}`, "panel usage")];
}
const usd = (n) => n === null || n === undefined ? "Thiếu giá" : `≈ US$${Number(n).toLocaleString("vi-VN", {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
function costBar(tokens, max, hatch) {
  const pct = max ? Math.round(tokens / max * 100) : 0;
  const fill = el("div", null, {class: `bar-f${hatch ? " hatch" : ""}`});
  fill.style.width = `${pct}%`; // CSSOM, not a style attribute: the CSP forbids inline styles
  return box("cell", [el("div", null, {class: "bar-t", role: "img", "aria-label": `${num(tokens)} token, ${pct}% mức lớn nhất`}, [fill]),
    el("strong", num(tokens))]);
}
function costTable(label, rows, caption, hasPrices, project) {
  const max = Math.max(0, ...rows.map((r) => r.tokens));
  const head = [label, "Tổng token", "Vào", "Ra", "Cache", "Lượt chạy", ...(project ? ["Vòng review"] : []), ...(hasPrices ? ["Ước tính"] : [])];
  const body = rows.map((r) => {
    const badges = [];
    if (r.top) badges.push(el("span", `↑ Top ${r.top}`, {class: "badge b-top"}));
    if (r.fails >= 2) badges.push(el("span", `✕ ${r.fails} lần FAIL`, {class: "badge b-fail"}));
    const name = project ? [link(r.id, taskHref(project, r.id)), el("span", ` ${r.title}`), el("br"),
      el("span", `${r.plan} · ${r.tool}${r.model ? " / " + r.model : ""}`, {class: "muted small"})] : [el("span", r.key)];
    const cells = [["", name], ["", [costBar(r.tokens, max, !!r.top), ...(badges.length ? [box("badges", badges)] : [])]],
      ["Vào", num(r.input)], ["Ra", num(r.output)], ["Cache", num(r.cache)], ["Lượt chạy", num(r.runs)],
      ...(project ? [["Vòng review", num(r.review_rounds)]] : []), ...(hasPrices ? [["Ước tính", usd(r.cost)]] : [])];
    return el("tr", null, {}, cells.map(([l, c], i) => el("td", Array.isArray(c) ? null : c,
      {class: i === 0 ? "name" : i === 1 ? "barc" : "num", ...(l ? {"data-l": l} : {})}, Array.isArray(c) ? c : [])));
  });
  return el("div", null, {class: "scroll"}, [el("table", null, {}, [el("caption", caption),
    el("thead", null, {}, [el("tr", null, {}, head.map((h, i) => el("th", h, {scope: "col", class: i > 1 ? "num" : ""})))]),
    el("tbody", null, {}, body)])]);
}
function costPage(name, d) {
  const t = d.totals;
  const total = d.has_prices ? (t.cost === null ? "chưa đủ giá" : usd(t.cost)) : "Chưa có";
  const stats = [[num(t.input), "Token vào"], [num(t.output), "Token ra"], [num(t.cache), "Token cache"], [num(t.runs), "Lượt chạy"],
    [total, d.has_prices ? "Ước tính USD, theo prices trong config" : "Ước tính USD: thiếu prices"]];
  const keyed = (rows, key) => rows.map((r) => ({...r, key: r[key]}));
  const groups = [["Task đắt nhất và vòng review", d.tasks, "Task", true], ["Theo plan", keyed(d.plans, "plan"), "Plan"],
    ["Theo tool", keyed(d.tools, "tool"), "Tool"], ["Theo model", keyed(d.models, "model"), "Model"]];
  const note = d.has_prices ? [] : [el("div", null, {class: "note", role: "note"}, [
    el("div", null, {}, [el("strong", "Chỉ hiển thị token, chưa có chi phí USD."),
      el("br"), el("span", "Thêm bản đồ prices theo từng model vào .omi/config.json để xem ước tính.")])])];
  const legend = el("ul", null, {class: "legend", "aria-label": "Chú giải"}, [
    el("li", null, {}, [el("i", null, {class: "hatch"}), el("span", "Top 5 đắt nhất (vạch chéo + nhãn “Top n”)")]),
    el("li", null, {}, [el("span", "✕ n lần FAIL", {class: "badge b-fail"}), el("span", " task có từ 2 vòng review FAIL")]),
    el("li", null, {}, [el("i", null, {class: "plain"}), el("span", "Các task còn lại")])]);
  const jump = el("nav", null, {class: "jump", "aria-label": "Nhóm số liệu"}, groups.map(([text], i) => {
    const b = el("button", text.startsWith("Task") ? "Theo task" : text, {type: "button", class: "btn"});
    b.addEventListener("click", () => document.getElementById(`cost-${i}`)?.scrollIntoView({behavior: "smooth", block: "start"}));
    return b;
  }));
  const panels = groups.map(([text, rows, label, byTask], i) => {
    const panel = section(text, [
      ...(byTask ? [legend] : []),
      rows.length ? costTable(label, rows, `${text}. Thanh so với mức lớn nhất; giá trị luôn ghi bằng chữ.`, d.has_prices, byTask ? name : null) : empty("Chưa có dữ liệu sử dụng.")],
      byTask ? `${num(rows.length)} task · số vòng review = số hàng reviewer trong Usage` : `${num(rows.length)} mục`);
    panel.setAttribute("id", `cost-${i}`);
    return panel;
  });
  return [box("stack", [link(`← Về dự án ${name}`, projectHref(name), "small"), el("p", `Dự án ${name} · chỉ đọc`, {class: "muted small"}), heading("Chi phí và quota")]), jump,
    box("stats cost-stats", stats.map(([n, l]) => box("stat", [el("div", n, {class: "n"}), el("div", l, {class: "l"})]))), ...note,
    ...panels];
}

function catalogPage(name, d) {
  const labels = {skills: "Kỹ năng", rules: "Rules", references: "References", patterns: "Patterns", workflows: "Quy trình"};
  const selected = new URLSearchParams(viewHash().split("?")[1] || "").get("item");
  return [heading(`Catalog · ${name}`), ...Object.entries(labels).map(([kind, title]) => section(title,
    (d.catalogs?.[kind] || []).length ? d.catalogs[kind].map(item => el("article", null, {class: "catalog-entry", ...(selected === item.id ? {"aria-label": "Mục đã chọn"} : {})}, [
      el("h3", item.id), el("p", item.text), el("p", "Task sử dụng", {class: "small muted"}),
      item.tasks.length ? itemList(name, "depends", item.tasks) : empty("Chưa có task sử dụng.")])) : [empty("Catalog trống.")]))];
}
