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
const viewHash = () => location.hash === "#main" ? current : location.hash;
function viewQuery(p) {
  const [path, ...query] = viewHash().split("?");
  return (path === projectHref(p) || path.startsWith(`${projectHref(p)}/t/`)) && query.length ? "?" + query.join("?") : "";
}
const filteredProjectHref = (p) => projectHref(p) + viewQuery(p);
const taskHref = (p, id) => `${projectHref(p)}/t/${enc(id)}${viewQuery(p)}`;
const chip = (text, cls) => el("span", text, {class: `chip ${cls || ""}`});
const empty = (text) => el("p", text || "Trống", {class: "empty"});
const heading = (text) => el("h1", text, {id: "title", tabindex: "-1"});
const pre = (text) => el("pre", text || "—");
function section(text, kids, note, cls, hid) {
  return el("section", null, {class: cls || "panel", ...(hid ? {"aria-labelledby": hid} : {})}, [
    box("ph", [el("h2", text, hid ? {id: hid} : {}), ...(note ? [el("span", note, {class: "muted small"})] : [])]), ...kids]);
}
function progress(done, total) {
  return el("progress", null, {class: "track", max: String(total || 1), value: String(done || 0),
    "aria-label": `${done || 0}/${total || 0} mục đã xong`});
}
function planRow(p) {
  const row = box(`plan ${p.status === "done" ? "completed" : ""}`, [el("span", p.id, {class: "mono strong"}), el("span", p.title || "—"),
    progress(p.done, p.total), el("span", `${p.done}/${p.total} mục`, {class: "r small"})]);
  return box("plan-detail", [row, ...(p.goal ? [el("p", p.goal)] : []),
    el("ul", null, {class: "info-list"}, (p.criteria || []).map(c => el("li", `${c.checked ? "✓ Xong" : "○ Chưa xong"}: ${c.text}`)))]);
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
const PHASES = {not_started: "Chưa bắt đầu", planning: "Lên kế hoạch", design: "Thiết kế", working: "Đang làm",
  review: "Đang review", qa: "Đang QA", po: "Chờ PO", blocked: "Bị chặn", done: "Xong"};
const TYPES = {milestone: "Milestone", epic: "Epic", fr: "FR", nfr: "NFR", task: "Task", bug: "Bug", security: "Security", incident: "Incident", change: "Change", spike: "Spike", chore: "Chore"};
const typeChip = (t) => chip(TYPES[t.type] || t.type || "Task", t.type || "task");
const statusOf = (t) => t.status || t.frontmatter.status || "planned";
const statusChip = (t, derived = false) => chip(`${GLYPH[statusOf(t)] || "○"} ${STATUS[statusOf(t)] || statusOf(t)}${derived ? " · tổng hợp" : ""}`, statusOf(t) === "in-progress" ? "working" : statusOf(t));
const phaseOf = (t) => t.phase || {key: {planned: "not_started", "in-progress": "working"}[statusOf(t)] || statusOf(t), label: STATUS[statusOf(t)]};
const stepText = (t) => `bước ${t.step_index || "?"}/${t.step_count || "?"} · ${t.current_step || t.frontmatter.step || "—"}`;
function disclosure(key, title, kids, opened = false, cls = "", forced = false) {
  const det = el("details", null, {class: cls, ...(forced || (disclosures.get(key) ?? opened) ? {open: ""} : {})}, [title, ...kids]);
  det.addEventListener("toggle", () => { if (!forced) disclosures.set(key, det.open); });
  return det;
}
