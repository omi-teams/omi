"use strict";
// All state text goes through textContent and DOM node creation only.
const view = document.getElementById("view");
const title = document.getElementById("title");
const nav = document.getElementById("nav");
const auto = document.getElementById("auto");
const status = document.getElementById("status");
const err = document.getElementById("err");
const KEY = "omi-board-auto";
const GLYPH = {planned: "○", "in-progress": "▶", review: "◐", blocked: "✖", done: "✔"};
const STATUS = {planned: "Kế hoạch", "in-progress": "Đang làm", review: "Review", blocked: "Bị chặn", done: "Xong"};
const REASON = {blocked: "Bị chặn", next_task: "Việc kế tiếp", next: "Bước tiếp theo", po_gate: "Chờ PO duyệt bước"};
let timer = null;
let current = "";
const seen = {};
const UNCHANGED = new Error("unchanged");

function el(tag, text, attrs, kids) {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = text;
  for (const [k, v] of Object.entries(attrs || {})) node.setAttribute(k, v);
  for (const kid of kids || []) node.append(kid);
  return node;
}
const num = (n) => Number(n).toLocaleString("vi-VN");
const link = (text, href, attrs) => el("a", text, {href, ...attrs});
const enc = encodeURIComponent;
const taskHref = (p, id) => `#/p/${enc(p)}/t/${enc(id)}`;

function section(heading, ...kids) {
  return el("section", null, {}, [el("h2", heading), ...kids]);
}
function list(items, empty) {
  if (!items.length) return el("p", empty || "Không có.", {class: "muted"});
  return el("ul", null, {}, items.map((i) => el("li", null, {}, [].concat(i))));
}
function table(head, rows, caption) {
  const t = el("table", null, {}, [el("caption", caption, {class: "muted", tabindex: "0"}),
    el("thead", null, {}, [el("tr", null, {}, head.map((h) => el("th", h, {scope: "col"})))]),
    el("tbody", null, {}, rows.map((r) => el("tr", null, {}, r.map((c) => el("td", c)))))]);
  return el("div", null, {class: "scroll"}, [t]);
}
function prog(done, total) {
  return [el("span", `${done}/${total} `), el("progress", null, {max: String(total || 1), value: String(done), "aria-label": `${done}/${total}`})];
}

async function get(path) {
  const res = await fetch(path, {cache: "no-store"});
  if (!res.ok) throw new Error(`${res.status}`);
  const text = await res.text();
  if (seen[path] === text) throw UNCHANGED;
  seen[path] = text;
  return JSON.parse(text);
}
function setNav(parts) {
  nav.replaceChildren(link("Trang chủ", "#/"));
  for (const [text, href] of parts) nav.append(el("span", "›"), href ? link(text, href) : el("span", text, {"aria-current": "page"}));
}

async function home() {
  const items = await get("/api/projects");
  document.title = "omi board";
  title.textContent = "Dự án";
  setNav([]);
  view.replaceChildren(list(items.map((p) => [
    link(p.name, `#/p/${enc(p.name)}`),
    el("span", ` — chờ PO: ${p.po_waiting_count}; kế hoạch: ${p.plans.map((x) => x.id).join(", ") || "—"}; ` +
      Object.entries(p.task_counts).map(([s, n]) => `${STATUS[s] || s} ${n}`).join(", "), {class: "muted"})]),
    "Chưa có dự án."));
}

async function dashboard(name) {
  const d = await get(`/api/projects/${enc(name)}`);
  document.title = `${name} — omi board`;
  title.textContent = name;
  setNav([[name]]);
  const waiting = section(`Chờ PO (${d.po_waiting_count})`, list(d.po_waiting.map((w) =>
    [link(w.id, taskHref(name, w.id)), el("span", ` ${REASON[w.reason] || w.reason}${w.text ? ": " + w.text : ""}`)]), "Không có việc chờ PO."));
  waiting.classList.add("waiting");
  const plans = section("Kế hoạch", list(d.plans.map((p) =>
    [el("strong", `${p.id} `), el("span", `${p.title || ""} [${p.status || ""}] `), ...prog(p.done, p.total)])));
  const board = el("div", null, {class: "kanban"}, Object.entries(d.kanban).map(([status, items]) =>
    el("div", null, {class: "col"}, [el("h3", `${GLYPH[status] || ""} ${STATUS[status] || status} (${items.length})`),
      ...items.map((t) => link(`${t.id} ${t.frontmatter.title || ""}`, taskHref(name, t.id), {class: "card"}))])));
  const activity = section("Hoạt động", list(d.activity.slice(0, 30).map((a) =>
    [link(a.id, taskHref(name, a.id)), el("span", ` ${a.text}`)]), "Chưa có hoạt động."));
  const decisions = section("Quyết định", list(d.decisions.slice(0, 20).map((x) => x.replace(/^- /, "")), "Chưa có quyết định."));
  const t = d.usage.totals;
  const usage = section("Sử dụng", table(["Model", "Lượt", "Input", "Output", "Cache"],
    [...Object.entries(d.usage.models), ["Tổng", t]].map(([m, u]) => [m, num(u.runs), num(u.input), num(u.output), num(u.cache)]),
    `Vòng review: ${t.review_rounds}`));
  const s = d.sync;
  const sync = section("Đồng bộ", el("dl", null, {}, [
    el("dt", "Trước (ahead)"), el("dd", s.ahead === null ? "—" : String(s.ahead)),
    el("dt", "Sau (behind)"), el("dd", s.behind === null ? "—" : String(s.behind)),
    el("dt", "Thay đổi chưa commit"), el("dd", s.dirty === null ? "—" : s.dirty ? "Có" : "Không"),
    el("dt", "Commit cuối"), el("dd", s.last_commit || "—")]));
  view.replaceChildren(waiting, plans, section("Kanban", board), activity, decisions, usage, sync);
}

async function taskPage(name, id) {
  const d = await get(`/api/projects/${enc(name)}/tasks/${enc(id)}`);
  const f = d.frontmatter;
  document.title = `${id} — omi board`;
  title.textContent = `${id} ${f.title || ""}`;
  setNav([[name, `#/p/${enc(name)}`], [id]]);
  const meta = el("dl", null, {}, Object.entries(f).flatMap(([k, v]) => [el("dt", k), el("dd", String(v))]));
  const pre = (text) => el("pre", text || "—");
  const u = d.usage;
  view.replaceChildren(section("Thông tin", meta), section("Mục tiêu", pre(d.goal)),
    section("Tiêu chí nghiệm thu", list(d.criteria.map((c) => `${c.checked ? "✔" : "○"} ${c.text}`))),
    section("Checkpoint", pre(d.checkpoint)), section("Các bước", pre(d.steps)), section("Báo cáo", pre(d.reports)),
    section("Sử dụng", table(["Role", "Model", "Effort", "Input", "Output", "Cache", "Thời gian", "Verdict"],
      u.rows.map((r) => [r.role, r.model, r.effort, r.input, r.output, r.cache, r.duration, r.verdict || ""]),
      `${u.runs} lượt; vòng review: ${u.review_rounds}`)));
}

async function route() {
  const hash = location.hash || "#/";
  const m = hash.match(/^#\/p\/([^/]+)(?:\/t\/([^/]+))?$/);
  const changed = hash !== current;
  current = hash;
  if (changed) for (const k of Object.keys(seen)) delete seen[k];
  try {
    if (!m) await home();
    else if (m[2]) await taskPage(decodeURIComponent(m[1]), decodeURIComponent(m[2]));
    else await dashboard(decodeURIComponent(m[1]));
    err.replaceChildren();
    status.textContent = `Cập nhật lần cuối ${new Date().toLocaleTimeString("vi-VN", {hour12: false})}`;
  } catch (e) {
    if (e === UNCHANGED) {
      status.textContent = `Cập nhật lần cuối ${new Date().toLocaleTimeString("vi-VN", {hour12: false})}`;
      return;
    }
    // Keep the old view on a failed poll; only a new page starts empty.
    if (changed) {
      title.textContent = "Lỗi";
      view.replaceChildren();
    }
    const retry = el("button", "Thử lại", {type: "button"});
    retry.addEventListener("click", route);
    err.replaceChildren(el("span", `Không tải được dữ liệu (${e.message}). `), retry);
  }
  if (changed) title.focus();
}

function schedule() {
  clearInterval(timer);
  timer = auto.checked ? setInterval(() => { if (!document.hidden) route(); }, 30000) : null;
}
try { auto.checked = localStorage.getItem(KEY) !== "off"; } catch (e) { /* storage blocked: keep default */ }
auto.addEventListener("change", () => {
  try { localStorage.setItem(KEY, auto.checked ? "on" : "off"); } catch (e) { /* storage blocked */ }
  schedule();
});
document.getElementById("refresh").addEventListener("click", route);
document.addEventListener("visibilitychange", () => { if (!document.hidden && auto.checked) route(); });
window.addEventListener("hashchange", route);
route();
schedule();
