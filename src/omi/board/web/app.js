"use strict";
// State content is always plain text; no Markdown or HTML is evaluated.
const view = document.getElementById("view");
const nav = document.getElementById("nav");
const auto = document.getElementById("auto");
const countdown = document.getElementById("countdown");
const status = document.getElementById("status");
const err = document.getElementById("err");
const KEY = "omi-board-auto";
const GLYPH = {planned: "○", "in-progress": "▶", review: "◐", blocked: "✖", done: "✓"};
const STATUS = {planned: "Kế hoạch", "in-progress": "Đang làm", review: "Review", blocked: "Bị chặn", done: "Xong"};
const REASON = {blocked: "Bị chặn", next_task: "Việc kế tiếp", next: "Bước tiếp theo", po_gate: "Chờ PO duyệt bước"};
let timer = null;
let nextRefresh = 0;
let current = "";
let seen = null;
let openReports = null;
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
    "aria-label": `${done || 0}/${total || 0} task đã xong`});
}
function planRow(p) {
  return box(`plan ${p.status === "done" ? "completed" : ""}`, [el("span", p.id, {class: "mono strong"}), el("span", p.title || "—"),
    progress(p.done, p.total), el("span", `${p.done}/${p.total}`, {class: "r small"})]);
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
      box("row small", [el("span", `${plan.id} ${plan.title || ""}`), el("span", `${plan.done}/${plan.total}`, {class: "muted"})]),
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
function dashboard(name, d) {
  const tasks = Object.values(d.kanban).flat();
  const waiting = d.po_waiting.map((w) => {
    const t = tasks.find((t) => t.id === w.id);
    return box("poi", [link(w.id, taskHref(name, w.id), "mono strong"), el("span", t?.frontmatter.title || "", {class: "strong"}),
      chip(`${REASON[w.reason] || w.reason}${w.text ? " · " + w.text : ""}`, "warn"), link("Xem task →", taskHref(name, w.id), "push small")]);
  });
  const count = d.task_counts;
  const stats = [[d.po_waiting_count, "Chờ PO"], [count["in-progress"], "Đang làm"], [count.planned, "Kế hoạch"], [count.done, "Task đã xong"]];
  const label = (s) => el("span", null, {}, [el("span", "", {class: `dot ${s}`, "aria-hidden": "true"}),
    el("span", ` ${GLYPH[s] || "○"} ${STATUS[s] || s}`)]);
  const mergeEmpty = !d.kanban.review?.length && !d.kanban.blocked?.length;
  const columns = Object.entries(d.kanban).map(([s, items]) => {
    const cards = items.map((t) => {
      const f = t.frontmatter;
      const card = link(null, taskHref(name, t.id), `card ${s}`);
      card.append(el("span", t.id, {class: "mono muted"}), el("span", f.title || "—", {class: "t"}));
      const chips = [f.step, [f.model, f.effort].filter(Boolean).join(" · ")].filter(Boolean);
      if (chips.length) card.append(box("chips", chips.map((c) => chip(c))));
      return card;
    });
    const more = cards.length > 2 ? el("details", null, {class: "more"}, [
      el("summary", `+ ${num(cards.length - 2)} task khác`, {class: "small", "aria-label": `Hiện thêm ${num(cards.length - 2)} task · ${STATUS[s] || s}`}),
      ...cards.slice(2)]) : null;
    return box(`col col-${s}${mergeEmpty && (s === "review" || s === "blocked") ? " empty-pair" : ""}`, [
      box("colh", [label(s), el("span", num(items.length), {class: "muted"})]),
      ...(cards.length ? cards.slice(0, 2) : [empty()]), ...(more ? [more] : [])]);
  });
  if (mergeEmpty) columns.push(box("col merged-empty", [box("colh", [
    box("chips", [label("review"), el("span", "·"), label("blocked")]), el("span", "0", {class: "muted"})])]));
  const board = box("kanban", columns);
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
    el("span", "origin/main", {class: "muted small mono"})]), chip(d.source.sha.slice(0, 7), "mono")]),
    section(`Chờ PO (${num(d.po_waiting_count)})`, waiting.length ? waiting : [empty("Không có việc chờ PO.")], "Những việc cần anh/chị quyết", "po"),
    box("stats", stats.map(([n, label], i) => box("stat", [el("div", num(n), {class: "n"}, i === 3 ? [el("span", ` / ${num(Object.values(count).reduce((a, b) => a + b, 0))}`, {class: "denom"})] : []), el("div", label, {class: "l"})]))),
    section("Kế hoạch", [box("", d.plans.length ? d.plans.map(planRow) : [empty("Chưa có kế hoạch.")])], `${num(d.plans.length)} kế hoạch · ${num(d.plans.filter((p) => p.status === "active").length)} đang chạy`),
    section("Kanban", [board]),
    box("grid2", [section("Hoạt động", [box("feed", activity.length ? activity : [empty("Chưa có hoạt động.")])]),
      section("Quyết định", [box("feed", decisions.length ? decisions : [empty("Chưa có quyết định.")])])]),
    section("Sử dụng", [el("p", `${num(u.totals.runs)} lượt · ${num(u.totals.output)} output`, {class: "usage-summary muted small"}),
      table(["Model", "Lượt", "Input", "Output", "Cache"],
      [...Object.entries(u.models), ["Tổng", u.totals]].map(([m, r]) => [m, num(r.runs), num(r.input), num(r.output), num(r.cache)]),
      "Bảng sử dụng token")], `Vòng review: ${num(u.totals.review_rounds)}`, "panel usage")];
}
function workflow(d) {
  const f = d.frontmatter;
  const steps = d.workflow_steps;
  const currentStep = d.current_step || f.step;
  const at = Array.isArray(steps) ? steps.findIndex((s) => (typeof s === "string" ? s : s.id) === currentStep) : -1;
  const list = Array.isArray(steps) && steps.length ? el("ol", null, {class: "steps"}, steps.map((s, i) => {
    const id = typeof s === "string" ? s : s.id;
    const current = id === currentStep;
    const done = at >= 0 && i < at;
    return el("li", null, current ? {"aria-current": "step"} : {}, [
      el("span", done ? "✓" : String(i + 1), {class: `sn ${current ? "current" : done ? "done" : ""}`}),
      el("span", `${id}${s.gate === "po" ? " · PO" : ""}`)]);
  })) : box("chips", [chip(currentStep || "Chưa có bước", "active")]);
  return section(`Quy trình${f.workflow ? " · " + f.workflow : ""}`, [list], at >= 0 ? `Bước ${at + 1}/${steps.length}` : null);
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
    box("chips", [el("span", id, {class: "mono muted"}), heading(f.title || id), chip(`${GLYPH[f.status] || "○"} ${STATUS[f.status] || f.status || "—"}`, "active")])])]),
    workflow(d), box("layout", [box("main", [
      section("Mục tiêu", [el("p", d.goal || "—", {class: "goal"})]),
      section("Tiêu chí nghiệm thu", [criteria], `${d.criteria.filter((c) => c.checked).length}/${d.criteria.length} xong`),
      section("Checkpoint", [pre(d.checkpoint)]), section("Các bước", [pre(d.steps)]),
      section(`Báo cáo (${reports.length})`, reports.length ? reports : [empty("Chưa có báo cáo.")])]),
    box("side", [section("Thông tin", [meta]), section("Sử dụng", [table(["Role", "Output", "Thời gian"],
      d.usage.rows.map((r) => [r.role, /^\d+$/.test(r.output) ? num(r.output) : r.output, r.duration]), "Bảng sử dụng của task")],
      `${num(d.usage.runs)} lượt · ${num(d.usage.review_rounds)} vòng review`)])])];
}
function updated(source) {
  err.replaceChildren();
  document.getElementById("source").textContent = `${source.repo.replace(/^[a-z]+:\/\//i, "")} @ ${source.sha.slice(0, 7)}`;
  if (source.stale) err.append(el("span", `Dữ liệu cũ - không kết nối được GitHub (lúc ${source.fetched_at ? new Date(source.fetched_at).toLocaleTimeString("vi-VN", {hour12: false}) : "chưa rõ"})`));
  status.replaceChildren(el("span", "Cập nhật lần cuối ", {class: "update-label"}),
    el("span", new Date().toLocaleTimeString("vi-VN", {hour12: false})));
}
async function route() {
  clearInterval(timer);
  const hash = location.hash === "#main" ? current || "#/" : location.hash || "#/";
  const changed = hash !== current;
  current = hash;
  if (changed) { seen = null; openReports = null; }
  const ticket = ++request;
  const abort = new AbortController();
  const limit = setTimeout(() => abort.abort(), 10000);
  try {
    const m = hash.match(/^#\/p\/([^/]+)(?:\/t\/([^/]+))?$/);
    const name = m ? decodeURIComponent(m[1]) : null;
    const id = m?.[2] ? decodeURIComponent(m[2]) : null;
    const path = name ? `/api/projects/${enc(name)}${id ? "/tasks/" + enc(id) : ""}` : "/api/projects";
    const response = await fetch(path, {cache: "no-store", signal: abort.signal});
    if (!response.ok) throw new Error(String(response.status));
    const text = await response.text();
    if (ticket !== request) return;
    const data = JSON.parse(text);
    if (text === seen) { updated(data.source); return; }
    // Render off the page, and only cache a response after its view succeeds.
    const nodes = name ? id ? taskPage(name, id, data) : dashboard(name, data) : home(data.projects);
    const scrolled = window.scrollY;
    view.replaceChildren(...nodes);
    if (!changed) window.scrollTo(0, scrolled);
    setNav(name ? id ? [[name, projectHref(name)], [id]] : [[name]] : []);
    document.title = `${id || name || "Dự án"} — omi board`;
    seen = text;
    updated(data.source);
    if (changed || document.activeElement === document.body) document.getElementById("title").focus();
  } catch (e) {
    if (ticket !== request) return;
    const retry = el("button", "Thử lại", {type: "button", class: "btn"});
    retry.addEventListener("click", route);
    err.replaceChildren(el("span", `Không tải được dữ liệu (${e.name === "AbortError" ? "quá thời gian chờ" : e.message}). `), retry);
  } finally {
    clearTimeout(limit);
    if (ticket === request) schedule();
  }
}
function updateCountdown() {
  countdown.textContent = !auto.checked ? "Đã tắt" : document.hidden ? "Tạm dừng" :
    `Làm mới sau ${Math.max(0, Math.ceil((nextRefresh - Date.now()) / 1000))} giây`;
}
function schedule() {
  clearInterval(timer);
  nextRefresh = Date.now() + 30000;
  updateCountdown();
  timer = auto.checked && !document.hidden ? setInterval(() => {
    updateCountdown();
    if (!document.hidden && Date.now() >= nextRefresh) route();
  }, 1000) : null;
}
try { auto.checked = localStorage.getItem(KEY) !== "off"; } catch (e) { /* Keep the default if storage is blocked. */ }
auto.addEventListener("change", () => {
  try { localStorage.setItem(KEY, auto.checked ? "on" : "off"); } catch (e) { /* Storage may be blocked. */ }
  schedule();
});
document.getElementById("refresh").addEventListener("click", route);
document.addEventListener("visibilitychange", () => {
  schedule();
  if (!document.hidden && auto.checked) route();
});
window.addEventListener("hashchange", route);
schedule();
route();
