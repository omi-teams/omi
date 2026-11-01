"use strict";
// State content is always plain text; no Markdown or HTML is evaluated.
const view = document.getElementById("view");
const nav = document.getElementById("nav");
const status = document.getElementById("status");
const err = document.getElementById("err");
const GLYPH = {planned: "○", "in-progress": "▶", review: "◐", blocked: "✖", done: "✓"};
const STATUS = {planned: "Chưa bắt đầu", "in-progress": "Đang làm", review: "Đang review", blocked: "Bị chặn", done: "Xong"};
const REASON = {blocked: "Bị chặn", next_task: "Việc kế tiếp", next: "Bước tiếp theo", po_gate: "Chờ PO duyệt bước"};
let timer = null;
let revision = null;
let loading = false;
let polling = false;
let failed = false;
let current = "";
let seen = null;
let openReports = null;
let disclosures = new Map();
let request = 0;

function el(tag, text, attrs, kids) {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = text;
  for (const [k, v] of Object.entries(attrs || {})) node.setAttribute(k, v);
  for (const kid of kids || []) node.append(kid);
  return node;
}
const box = (cls, kids) => el("div", null, {class: cls}, kids);
const num = (n) => Number(n || 0).toLocaleString("vi-VN");
const link = (text, href, cls) => el("a", text, {href, class: cls || ""});
const enc = encodeURIComponent;
const projectHref = (p) => `#/p/${enc(p)}`;
const taskHref = (p, id) => `${projectHref(p)}/t/${enc(id)}`;
const chip = (text, cls) => el("span", text, {class: `chip ${cls || ""}`});
const empty = (text) => el("p", text || "Trống", {class: "empty"});
const heading = (text) => el("h1", text, {id: "title", tabindex: "-1"});
const pre = (text) => el("pre", text || "—");
function section(text, kids, note, cls) {
  return el("section", null, {class: cls || "panel"}, [
    box("ph", [el("h2", text), ...(note ? [el("span", note, {class: "muted small"})] : [])]), ...kids]);
}
function progress(done, total) {
  return el("progress", null, {class: "track", max: String(total || 1), value: String(done || 0),
    "aria-label": `${done || 0}/${total || 0} mục đã xong`});
}
function planRow(p) {
  return box(`plan ${p.status === "done" ? "completed" : ""}`, [el("span", p.id, {class: "mono strong"}), el("span", p.title || "—"),
    progress(p.done, p.total), el("span", `${p.done}/${p.total} mục`, {class: "r small"})]);
}
function table(head, rows, caption) {
  return el("div", null, {class: "scroll", tabindex: "0", "aria-label": caption}, [
    el("table", null, {}, [el("caption", caption),
      el("thead", null, {}, [el("tr", null, {}, head.map((h, i) => el("th", h, {scope: "col", class: i ? "r" : ""})))]),
      el("tbody", null, {}, rows.map((r) => el("tr", null, {class: r[0] === "Tổng" ? "total" : ""},
        r.map((c, i) => el("td", c, {class: i ? "r" : "mono"})))))] )]);
}
function setNav(parts) {
  nav.replaceChildren();
  if (!parts.length) return;
  nav.append(link("Dự án", "#/"));
  for (const [text, href] of parts) nav.append(el("span", "/", {"aria-hidden": "true"}),
    href ? link(text, href) : el("span", text, {"aria-current": "page"}));
}
function home(items) {
  const cards = items.map((p) => {
    const card = link(null, projectHref(p.name), "pc");
    card.append(box("row", [box("stack", [el("span", p.name, {class: "pn"}),
      el("span", "origin/main", {class: "mono muted"})]),
      chip(p.po_waiting_count ? `${num(p.po_waiting_count)} chờ PO` : "Không chờ PO", p.po_waiting_count ? "warn" : "")]),
    ...(p.plans.length ? p.plans.map((plan) => box("stack", [
      box("row small", [el("span", `${plan.id} ${plan.title || ""}`), el("span", `${plan.done}/${plan.total} mục`, {class: "muted"})]),
      progress(plan.done, plan.total)])) : [empty("Chưa có kế hoạch")]),
    box("counts", Object.keys(STATUS).map((s) => box("", [el("b", num(p.task_counts[s])), el("span", STATUS[s])]))),
    box("chips", [branchChip(p.branch)]));
    return card;
  });
  return [box("heading", [heading("Dự án"), el("span", `${num(items.length)} dự án · ${num(items.reduce((n, p) => n + p.po_waiting_count, 0))} việc chờ PO`, {class: "muted small"})]),
    box("projects", cards.length ? cards : [empty("Chưa có dự án.")])];
}
function branchChip(branch) {
  return el("span", branch || "Nhánh: Chưa rõ", {class: "chip", title: "Nhánh kho trạng thái"});
}
const PHASES = {not_started: "Chưa bắt đầu", planning: "Lên kế hoạch", design: "Thiết kế", working: "Đang làm",
  review: "Đang review", qa: "Đang QA", po: "Chờ PO", blocked: "Bị chặn", done: "Xong"};
const TYPES = {milestone: "Milestone", epic: "Epic", fr: "FR", nfr: "NFR", task: "Task"};
const typeChip = (t) => chip(TYPES[t.type] || t.type || "Task", t.type || "task");
const statusOf = (t) => t.status || t.frontmatter.status || "planned";
const statusChip = (t, derived = false) => chip(`${GLYPH[statusOf(t)] || "○"} ${STATUS[statusOf(t)] || statusOf(t)}${derived ? " · tổng hợp" : ""}`, statusOf(t) === "in-progress" ? "working" : statusOf(t));
const phaseOf = (t) => t.phase || {key: {planned: "not_started", "in-progress": "working"}[statusOf(t)] || statusOf(t), label: STATUS[statusOf(t)]};
const stepText = (t) => `bước ${t.step_index || "?"}/${t.step_count || "?"} · ${t.current_step || t.frontmatter.step || "—"}`;
function disclosure(key, title, kids, opened = false, cls = "") {
  const det = el("details", null, {class: cls, ...(disclosures.get(key) ?? opened ? {open: ""} : {})}, [title, ...kids]);
  det.addEventListener("toggle", () => disclosures.set(key, det.open));
  return det;
}
function taskTree(name, items) {
  const byId = new Map(items.map(t => [t.id, t]));
  function node(t, ancestors = new Set()) {
    const path = new Set([...ancestors, t.id]);
    const kids = (t.children || []).map(id => byId.get(id)).filter(k => k && !path.has(k.id));
    const badges = [typeChip(t), el("span", t.id, {class: "mono"}), statusChip(t, !!kids.length)];
    if (!kids.length) return box("leaf", [box("chips", badges), link(t.frontmatter.title || t.id, taskHref(name, t.id))]);
    const done = kids.filter(k => statusOf(k) === "done").length;
    const bar = progress(done, kids.length);
    bar.setAttribute("aria-label", `${t.id}: ${done}/${kids.length} con trực tiếp đã xong`);
    return disclosure(`tree:${t.id}`, el("summary", null, {}, [box("chips", badges), el("span", t.frontmatter.title || "—"),
      box("progress-row", [bar, el("span", `${done}/${kids.length}`, {class: "small"})])]),
      [box("children", kids.map(k => node(k, path)))],
      !["done", "blocked"].includes(statusOf(t)));
  }
  const roots = items.filter(t => !byId.has(t.parent)).sort((a, b) => a.id.localeCompare(b.id));
  return box("tree", roots.length ? roots.map(t => node(t)) : [empty("Chưa có task. Các task sẽ xuất hiện sau lần cập nhật dữ liệu kế tiếp.")]);
}
function leafCounts(d) {
  const count = Object.fromEntries(Object.keys(STATUS).map(s => [s, 0]));
  for (const t of Object.values(d.kanban).flat().filter(t => !t.children?.length)) count[statusOf(t)] = (count[statusOf(t)] || 0) + 1;
  return count;
}
function dashboard(name, d) {
  const tasks = Object.values(d.kanban).flat();
  const waiting = d.po_waiting.map((w) => {
    const t = tasks.find((t) => t.id === w.id);
    return box("poi", [link(w.id, taskHref(name, w.id), "mono strong"), el("span", t?.frontmatter.title || "", {class: "strong"}),
      chip(`${REASON[w.reason] || w.reason}${w.text ? " · " + w.text : ""}`, "warn"), link("Xem task →", taskHref(name, w.id), "push small")]);
  });
  const count = leafCounts(d);
  const stats = [[d.po_waiting_count, "Chờ PO"], [count["in-progress"], "Đang làm · task lá"], [count.blocked, "Bị chặn · task lá"], [count.done, "Task lá đã xong"]];
  const leaves = tasks.filter(t => !t.children?.length);
  const columns = [], vacant = [];
  for (const [key, label] of Object.entries(PHASES)) {
    const items = leaves.filter(t => phaseOf(t).key === key);
    const cards = items.map(t => {
      const ph = phaseOf(t);
      return el("article", null, {class: `card ${key}`}, [el("span", t.id, {class: "mono muted"}),
        link(t.frontmatter.title || "—", taskHref(name, t.id), "t"),
        box("chips", [typeChip(t), chip(ph.label, ph.key)]), el("span", stepText(t), {class: "small"}),
        el("span", `Vòng review: ${t.review_round ?? "—"}`, {class: "small"})]);
    });
    const column = box(`col col-${key}`, [box("colh", [chip(label, key), el("span", num(items.length), {class: "muted"})]),
      ...(cards.length ? cards : [empty("Chưa có task.")])]);
    (items.length ? columns : vacant).push(column);
  }
  const board = box("stack", [box("kanban", columns), ...(vacant.length ? [disclosure("empty-phases",
    el("summary", `${vacant.length} giai đoạn trống`), [box("kanban", vacant)], false, "empty-phases")] : [])]);
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
    box("chips", [link("Chi phí và quota →", `${projectHref(name)}/cost`, "small"), chip(d.source.sha.slice(0, 7), "mono")])]),
    section(`Chờ PO (${num(d.po_waiting_count)})`, waiting.length ? waiting : [empty("Không có việc chờ PO.")], "Những việc cần anh/chị quyết", "po"),
    box("stats", stats.map(([n, label], i) => box("stat", [el("div", num(n), {class: "n"}, i === 3 ? [el("span", ` / ${num(Object.values(count).reduce((a, b) => a + b, 0))}`, {class: "denom"})] : []), el("div", label, {class: "l"})]))),
    section("Kế hoạch", [box("", d.plans.length ? d.plans.map(planRow) : [empty("Chưa có kế hoạch.")])], `${num(d.plans.length)} kế hoạch · ${num(d.plans.filter((p) => p.status === "active").length)} đang chạy`),
    section("Cây công việc", [el("p", "Trạng thái cha tổng hợp từ con trực tiếp; mở một hàng để xem cấp dưới.", {class: "muted small"}), taskTree(name, tasks)]),
    section("Kanban", [el("p", "Chỉ task lá · thứ tự pha cố định · cột trống thu gọn", {class: "muted small"}), board]),
    box("grid2", [section("Hoạt động", [box("feed", activity.length ? activity : [empty("Chưa có hoạt động.")])]),
      section("Quyết định", [box("feed", decisions.length ? decisions : [empty("Chưa có quyết định.")])])]),
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
function workflow(d) {
  const f = d.frontmatter;
  const steps = d.workflow_steps || [];
  const currentStep = d.current_step || f.step;
  const at = steps.findIndex(s => (typeof s === "string" ? s : s.id) === currentStep);
  const finished = f.status === "done";
  const list = steps.length ? el("ol", null, {class: `steps${steps.length > 7 ? " vertical" : ""}`}, steps.map((s, i) => {
    const id = typeof s === "string" ? s : s.id;
    const current = !finished && i === at;
    const done = finished || (at >= 0 && i < at);
    return el("li", null, {class: done ? "complete" : current ? "current" : "", ...(current ? {"aria-current": "step"} : {})}, [
      el("span", done ? "✓" : String(i + 1), {class: `sn ${current ? "current" : done ? "done" : ""}`}),
      box("stack", [el("strong", id), el("small", `${done ? "✓ Xong" : current ? "Hiện tại" : "Chưa bắt đầu"}${s.gate === "po" ? " · PO duyệt" : ""}`)]),
      ...(i < steps.length - 1 ? [el("span", "→", {class: "arrow", "aria-hidden": "true"})] : [])]);
  })) : empty("Chưa có định nghĩa quy trình.");
  return section(`${d.children?.length ? "Quy trình riêng" : "Quy trình"}${f.workflow ? " · " + f.workflow : ""}`,
    [list, ...(!finished && at < 0 && steps.length ? [empty("Không xác định bước hiện tại.")] : [])], at >= 0 ? `Bước ${at + 1}/${steps.length}` : null);
}
function taskUsage(usage) {
  const list = el("dl", null, {class: "task-usage"}, usage.rows.length ? usage.rows.map(r => el("div", null, {}, [
    el("dt", r.role), el("dd", `Output: ${/^\d+$/.test(r.output) ? num(r.output) : r.output}`),
    el("dd", `Thời gian: ${r.duration}`)])) : [el("div", null, {}, [el("dt", "Sử dụng"), el("dd", "Chưa có dữ liệu sử dụng.")])]);
  if (usage.rows.length) list.append(el("div", null, {}, [el("dt", "Tổng"),
    el("dd", `${num(usage.runs)} lượt · Output: ${num(usage.output ?? usage.rows.reduce((n, r) => n + (/^\d+$/.test(r.output) ? Number(r.output) : 0), 0))}`)]));
  return list;
}
function taskPage(name, id, d) {
  const f = d.frontmatter;
  const criteria = el("ul", null, {class: "crit"}, d.criteria.map((c) => el("li", null, {}, [
    el("span", c.checked ? "✓" : "", {class: `ck ${c.checked ? "checked" : ""}`, role: "img", "aria-label": c.checked ? "Xong" : "Chưa"}), el("span", c.text)])));
  const reports = d.reports.split(/\n(?=\d{4}-\d\d-\d\d[^\n]*:)/).filter(Boolean).reverse().map((r, i) => {
    const [summary, ...body] = r.split("\n");
    const verdict = (summary + " " + (body[0] || "").replace(/^> ?/, "")).match(/\b(DONE|PASS|FAIL|BLOCKED|NEEDS SCOPE)\b/);
    const text = verdict && !summary.includes(verdict[0]) ? `${summary.replace(/:$/, "")} · ${verdict[0]}` : summary;
    openReports ??= new Set([text]);
    const det = el("details", null, openReports.has(text) ? {open: ""} : {}, [el("summary", text), pre(body.join("\n").replace(/^> ?/gm, ""))]);
    det.addEventListener("toggle", () => openReports[det.open ? "add" : "delete"](text));
    return det;
  });
  const meta = el("dl");
  const labels = {plan: "Kế hoạch", depends: "Phụ thuộc", role: "Role", tool: "Tool", model: "Model", effort: "Effort", scope: "Scope", skills: "Skills"};
  for (const [k, label] of Object.entries(labels)) {
    const dd = el("dd", null, {class: "mono"});
    if (k === "depends" && f[k]) {
      const ids = Array.isArray(f[k]) ? f[k] : String(f[k]).split(/[,\s]+/).filter(Boolean);
      for (const dep of ids) dd.append(link(dep, taskHref(name, dep)), el("span", " "));
    } else dd.textContent = Array.isArray(f[k]) ? f[k].join(", ") : String(f[k] || "—");
    meta.append(el("dt", label), dd);
  }
  return [box("stack", [link(`← Về dự án ${name}`, projectHref(name), "small"), box("row", [
    box("chips", [el("span", id, {class: "mono muted"}), heading(f.title || id), typeChip(d), statusChip(d, !!d.children?.length)])])]),
    workflow(d), box("layout", [box("main", [
      section("Mục tiêu", [el("p", d.goal || "—", {class: "goal"})]),
      section("Tiêu chí nghiệm thu", [criteria], `${d.criteria.filter((c) => c.checked).length}/${d.criteria.length} xong`),
      section("Checkpoint", [pre(d.checkpoint)]), section("Các bước", [pre(d.steps)]),
      section(`Báo cáo (${reports.length})`, reports.length ? reports : [empty("Chưa có báo cáo.")])]),
    el("aside", null, {class: "side"}, [section("Thông tin", [meta]), section("Sử dụng", [taskUsage(d.usage)],
      `${num(d.usage.runs)} lượt · ${num(d.usage.review_rounds)} vòng review`)])])];
}
const INBOX_REASON = {po_gate: "Chờ PO duyệt", needs_scope: "NEEDS SCOPE", quota: "QUOTA stop", review_fail: "Review FAIL ×2"};
let inboxItems = null;
const inboxSeen = new Set();
let notifyEnabled = false;
let notifyPending = false;
let notifyMessage = "";
let storageAvailable = true;
try { notifyEnabled = window.localStorage.getItem("omi-board-notifications") === "on"; }
catch (_) { storageAvailable = false; }
const notificationAPI = () => window.isSecureContext && window.Notification;
const inboxKey = (i) => JSON.stringify([i.project, i.id, i.reason, i.gate || "", i.since || "", i.request_marker || ""]);
function pageTitle() {
  const title = document.getElementById("title");
  document.title = `${inboxItems?.length ? `(${inboxItems.length}) ` : ""}${current === "#/inbox" ? "Hộp thư PO" : title?.textContent || "Dự án"} — omi board`;
}
function acceptInbox(items) {
  const baseline = inboxItems === null;
  const fresh = items.filter(i => !inboxSeen.has(inboxKey(i)));
  for (const item of items) inboxSeen.add(inboxKey(item));
  inboxItems = items;
  document.getElementById("inbox-count").textContent = String(items.length);
  pageTitle();
  if (!baseline && fresh.length && notifyEnabled && notificationAPI()?.permission === "granted") {
    try {
      const note = new window.Notification(`${fresh.length} việc mới chờ PO`, {
        body: fresh.map(i => `${i.project} · ${i.id}: ${INBOX_REASON[i.reason] || i.reason}`).join("\n")});
      note.onclick = () => { window.focus(); location.hash = "#/inbox"; note.close(); };
    } catch (_) {
      notifyMessage = "Không tạo được thông báo. Kiểm tra cài đặt trình duyệt.";
      renderNotificationSettings();
    }
  }
}
function renderNotificationSettings() {
  const target = document.getElementById("notification-settings");
  if (!target) return;
  const api = notificationAPI();
  const denied = api?.permission === "denied";
  const enabled = notifyEnabled && api?.permission === "granted";
  const button = el("button", notifyPending ? "Đang xin quyền…" : enabled ? "Tắt thông báo" : "Bật thông báo",
    {type: "button", class: `btn${!enabled ? " notify-enable" : ""}`, "data-control": "notifications"});
  button.disabled = notifyPending || !api || denied;
  button.addEventListener("click", async () => {
    if (notifyPending) return;
    if (enabled) notifyEnabled = false;
    else {
      notifyPending = true; renderNotificationSettings();
      try {
        const permission = await api.requestPermission();
        notifyEnabled = permission === "granted";
        notifyMessage = permission === "default" ? "Chưa cấp quyền. Bấm Bật thông báo để thử lại." : "";
      } catch (_) { notifyEnabled = false; notifyMessage = "Không xin được quyền thông báo. Thử lại khi trình duyệt sẵn sàng."; }
      finally { notifyPending = false; }
    }
    // Enabling establishes a baseline; no backlog notifications.
    for (const item of inboxItems || []) inboxSeen.add(inboxKey(item));
    try { window.localStorage.setItem("omi-board-notifications", notifyEnabled ? "on" : "off"); }
    catch (_) { storageAvailable = false; }
    renderNotificationSettings();
    document.getElementById("notification-settings")?.querySelectorAll("button")[0]?.focus({preventScroll: true});
  });
  target.replaceChildren(box("row", [box("stack", [el("h2", "Thông báo trình duyệt"),
    el("p", "Chỉ hoạt động khi board đang mở và tab đang hiển thị; tab ẩn dừng kiểm tra. Không có thông báo nền.", {class: "muted small"})]), button]),
    el("p", !api ? "Trình duyệt không hỗ trợ thông báo hoặc kết nối chưa an toàn." : denied ?
      "Quyền thông báo bị chặn. Mở cài đặt trình duyệt để thay đổi." : enabled ? "Đã bật thông báo cho việc mới." : "Thông báo đang tắt.", {class: "small"}),
    el("p", `${notifyMessage}${!storageAvailable ? " Tùy chọn chỉ áp dụng cho tab này." : ""}`, {role: "status", class: "small"}));
}
function inboxAge(stamp) {
  const minutes = Math.max(0, Math.floor((Date.now() - stamp) / 60000));
  return `Chờ ${minutes < 60 ? minutes + " phút" : Math.floor(minutes / 60) + " giờ"}`;
}
function refreshInboxAges() {
  if (current !== "#/inbox") return;
  for (const node of view.querySelectorAll("strong")) {
    const stamp = node.getAttribute("data-inbox-since");
    if (stamp !== null) node.textContent = inboxAge(Number(stamp));
  }
}
function inboxPage(items) {
  const tasks = new Set(items.map(i => JSON.stringify([i.project, i.id])));
  const rows = items.map(i => {
    const command = i.command;
    const feedback = el("p", "", {role: "status", class: "small"});
    const copy = el("button", "Sao chép lệnh", {type: "button", class: "btn", "data-control": inboxKey(i),
      "aria-label": `Sao chép ${command} · ${i.project}`});
    copy.addEventListener("click", async () => {
      const focused = document.activeElement === copy;
      copy.disabled = true;
      try { await window.navigator.clipboard.writeText(command); feedback.textContent = `Đã sao chép: ${command}`; }
      catch (_) { feedback.textContent = "Không sao chép được. Chọn và sao chép lệnh hiển thị bên trên."; }
      finally {
        copy.disabled = false;
        if (focused && copy.isConnected && (document.activeElement === document.body || document.activeElement === copy)) copy.focus({preventScroll: true});
      }
    });
    const date = i.since ? new Date(i.since.replace(" ", "T") + "Z") : null;
    const valid = date && Number.isFinite(date.getTime());
    const age = valid ? inboxAge(date.getTime()) : "Chờ: chưa rõ thời điểm";
    return el("li", null, {}, [box("stack", [chip(i.gate ? `PO · ${i.gate}` : INBOX_REASON[i.reason] || i.reason, i.reason === "po_gate" ? "po" : "blocked"),
      link(`${i.id} · ${i.title || "Chưa có tiêu đề"}`, taskHref(i.project, i.id), "strong"),
      el("p", i.text || "Cần PO quyết định; xem chi tiết task."), el("p", `Dự án: ${i.project}`, {class: "small muted"})]),
      box("inbox-age", [el("strong", age, valid ? {"data-inbox-since": date.getTime()} : {}), ...(valid ? [el("time", `${i.since} UTC`, {datetime: date.toISOString(), class: "small muted"})] : [])]),
      box("inbox-command", [el("code", command), copy, feedback])]);
  });
  const title = heading("Hộp thư PO ");
  title.append(chip(`${items.length} việc`, "po"));
  return [box("heading inbox-heading", [title]),
    el("p", "Mọi việc đang chờ anh/chị quyết định, từ tất cả dự án. Board chỉ đọc; sao chép lệnh rồi chạy trong terminal của dự án.", {class: "inbox-intro"}),
    el("section", null, {id: "notification-settings", class: "panel inbox-notice"}),
    section("Đang chờ quyết định", [el("p", "Việc chờ lâu nhất ở trên. Lệnh không tự chạy.", {class: "small muted"}),
      rows.length ? el("ul", null, {class: "inbox-items"}, rows) : empty("Không có việc chờ PO. Mọi quyết định đã được xử lý.")], `${items.length} việc · ${tasks.size} task`, "panel inbox-panel")];
}
function updated(source) {
  failed = false;
  if (err.contains?.(document.activeElement)) document.getElementById("refresh").focus();
  err.replaceChildren();
  document.getElementById("source").textContent = `${source.repo.replace(/^[a-z]+:\/\//i, "")} @ ${source.sha.slice(0, 7)}`;
  if (source.stale) err.append(el("span", `Dữ liệu cũ - không kết nối được GitHub (lúc ${source.fetched_at ? new Date(source.fetched_at).toLocaleTimeString("vi-VN", {hour12: false}) : "chưa rõ"})`));
  status.replaceChildren(el("span", "Cập nhật lần cuối ", {class: "update-label"}),
    el("span", new Date().toLocaleTimeString("vi-VN", {hour12: false})));
}
function showError(e) {
  if (failed) return;
  failed = true;
  const retry = el("button", "Thử lại", {type: "button", class: "btn"});
  retry.addEventListener("click", () => route(retry));
  err.replaceChildren(el("span", `Không tải được dữ liệu (${e.name === "AbortError" ? "quá thời gian chờ" : e.message}). `), retry);
}
async function route(button = null) {
  const hash = location.hash === "#main" ? current || "#/" : location.hash || "#/";
  const previous = current;
  const changed = hash !== current;
  current = hash;
  if (changed) {
    seen = null; openReports = null; revision = null;
    if (hash.split("/t/")[0] !== previous.split("/t/")[0]) disclosures = new Map();

  }
  loading = true;
  view.setAttribute("aria-busy", "true");
  const label = button ? [...button.childNodes || button.children] : [];
  if (button) { button.disabled = true; button.textContent = "Đang tải…"; }
  const ticket = ++request;
  const abort = new AbortController();
  const limit = setTimeout(() => abort.abort(), 10000);
  try {
    const m = hash.match(/^#\/p\/([^/]+)(?:\/t\/([^/]+)|\/(cost))?$/);
    const name = m ? decodeURIComponent(m[1]) : null;
    const id = m?.[2] ? decodeURIComponent(m[2]) : null;
    const costs = !!m?.[3];
    const isInbox = hash === "#/inbox";
    if (changed) view.replaceChildren(heading(isInbox ? "Hộp thư PO" : costs ? "Chi phí và quota" : id || name || "Dự án"),
      el("div", null, {class: "skeleton", "aria-hidden": "true"}), el("p", "Đang tải…"));
    const path = name ? `/api/projects/${enc(name)}${id ? "/tasks/" + enc(id) : costs ? "/cost" : ""}` : "/api/projects";
    const response = await fetch(path, {cache: "no-store", signal: abort.signal});
    if (!response.ok) throw new Error(String(response.status));
    const text = await response.text();
    if (ticket !== request) return;
    const data = JSON.parse(text);
    // /api/projects aggregates every project's inbox from one immutable snapshot.
    let board = data;
    let boardText = text;
    if (name) {
      const response = await fetch("/api/projects", {cache: "no-store", signal: abort.signal});
      if (!response.ok) throw new Error(String(response.status));
      boardText = await response.text(); board = JSON.parse(boardText);
      if (ticket !== request) return;
    }
    const items = board.inbox || [];
    let contentKey = JSON.stringify([text, boardText]);
    // The detail endpoint carries the task's own workflow; the project view
    // carries hierarchy and the status derived from its children.
    if (id) {
      const response = await fetch(`/api/projects/${enc(name)}`, {cache: "no-store", signal: abort.signal});
      if (!response.ok) throw new Error(String(response.status));
      const projectText = await response.text();
      const project = JSON.parse(projectText);
      contentKey = JSON.stringify([text, boardText, projectText]);
      const item = Object.values(project.kanban).flat().find(t => t.id === id);
      if (item) Object.assign(data, {status: item.status, children: item.children, parent: item.parent, type: item.type});
      if (ticket !== request) return;
    }
    if (!name && !isInbox) {
      const projectTexts = await Promise.all(data.projects.map(async p => {
        const response = await fetch(`/api/projects/${enc(p.name)}`, {cache: "no-store", signal: abort.signal});
        if (!response.ok) throw new Error(String(response.status));
        const projectText = await response.text();
        p.task_counts = leafCounts(JSON.parse(projectText));
        return projectText;
      }));
      contentKey = JSON.stringify([text, ...projectTexts]);
      if (ticket !== request) return;
    }
    if (contentKey === seen) { refreshInboxAges(); revision = board.source.sha; updated(data.source); return; }
    // Render off the page, and only cache a response after its view succeeds.
    const nodes = isInbox ? inboxPage(items) : name ? costs ? costPage(name, data) : id ? taskPage(name, id, data) : dashboard(name, data) : home(data.projects);
    const scrolled = window.scrollY;
    const focused = document.activeElement;
    const focusInView = !changed && view.contains(focused);
    view.replaceChildren(...nodes);
    if (isInbox) {
      renderNotificationSettings();
      const listTitle = view.querySelectorAll("h2")[1];
      listTitle.setAttribute("id", "inbox-title"); listTitle.setAttribute("tabindex", "-1");
      listTitle.setAttribute("aria-label", `Đang chờ quyết định: ${items.length} việc`);
      view.querySelectorAll("section")[1].querySelectorAll("span")[0]?.setAttribute("role", "status");
    }
    if (focusInView) {
      const control = focused.getAttribute("data-control");
      const replacement = [...view.querySelectorAll("a, summary, button")].find(n => control ? n.getAttribute("data-control") === control :
        n.tagName === focused.tagName && n.getAttribute("href") === focused.getAttribute("href") &&
        n.textContent === focused.textContent);
      (replacement || (isInbox ? document.getElementById("inbox-title") : view)).focus({preventScroll: true});
    } else if (!changed && focused !== document.body && focused.isConnected === false) {
      view.focus({preventScroll: true});
    } else if (!changed && focused.isConnected && document.activeElement !== focused) {
      focused.focus({preventScroll: true});
    }
    if (!changed) window.scrollTo(0, scrolled);
    if (changed) setNav(isInbox ? [["Hộp thư PO"]] : name ? id || costs ? [[name, projectHref(name)], [id || "Chi phí"]] : [[name]] : []);
    acceptInbox(items);
    seen = contentKey;
    revision = board.source.sha;
    updated(data.source);
    if (changed) document.getElementById("title").focus();
  } catch (e) {
    if (ticket !== request) return;
    if (seen === null) view.replaceChildren(document.getElementById("title"));
    showError(e);
  } finally {
    clearTimeout(limit);
    if (button) { button.disabled = false; button.replaceChildren(...label); }
    if (ticket === request) {
      loading = false;
      view.setAttribute("aria-busy", "false");
    }
  }
}
async function pollVersion() {
  if (document.hidden || loading || polling) return;
  polling = true;
  const hash = current;
  const ticket = request;
  const abort = new AbortController();
  const limit = setTimeout(() => abort.abort(), 10000);
  try {
    const path = "/api/version";
    const response = await fetch(path, {cache: "no-store", signal: abort.signal});
    if (!response.ok) throw new Error(String(response.status));
    const data = JSON.parse(await response.text());
    if (hash !== current || ticket !== request || document.hidden) return;
    if (data.sha !== revision || failed) await route();
    refreshInboxAges();
  } catch (e) {
    if (hash === current && ticket === request && !document.hidden) showError(e);
  } finally {
    clearTimeout(limit);
    polling = false;
  }
}
function schedule() {
  clearInterval(timer);
  timer = document.hidden ? null : setInterval(pollVersion, 3000);
}
const refresh = document.getElementById("refresh");
refresh.addEventListener("click", () => route(refresh));
document.addEventListener("visibilitychange", () => {
  schedule();
  if (!document.hidden) pollVersion();
});
window.addEventListener("hashchange", () => route());
schedule();
route(refresh);
