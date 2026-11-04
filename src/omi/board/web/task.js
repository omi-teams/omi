"use strict";
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
const TL_STATE = {done: ["✓ Xong", "done"], running: ["● Đang chạy", "working"], skipped: ["Bỏ qua", "planned"]};
const TL_VERDICT = {DONE: ["✓ DONE", "done"], PASS: ["✓ PASS", "done"], FAIL: ["✕ FAIL", "blocked"], BLOCKED: ["BLOCKED", "blocked"], "NEEDS SCOPE": ["NEEDS SCOPE", "warn"]};
const TL_MARK = {done: "✓", running: "●", skipped: "–", fail: "✕", memo: "·"};
function tlWhen(stamp) {
  const m = /^\d{4}-(\d\d)-(\d\d) (\d\d:\d\d)/.exec(stamp || "");
  return m ? `${m[2]}/${m[1]} · ${m[3]}` : "";
}
function tlRow(id, r, now) {
  const when = el("span", tlWhen(r.start), {class: "when"});
  if (r.kind === "note") return el("li", null, {class: "tl-note"}, [when, el("span", "·", {class: "mk memo", "aria-hidden": "true"}), box("ev", [el("span", r.text, {class: "small muted"})])]);
  const kind = r.fail ? "fail" : r.state;
  const [label, tone] = TL_STATE[r.state];
  const top = [el("span", r.name, {class: "name"}), ...(r.po ? [chip("◇ PO duyệt", "warn")] : []), ...(r.fail ? [chip("✕ Có vòng FAIL", "blocked")] : []), chip(label, tone),
    el("span", r.state === "running" ? `đang chạy · ${r.duration}` : r.duration, {class: "dur"})];
  const rounds = (r.rounds || []).map((x) => {
    const [vl, vt] = TL_VERDICT[x.verdict] || [x.verdict || "—", "planned"];
    return disclosure(`round:${id}:${r.name}:${x.stamp}:${x.n}`, el("summary", null, {}, [el("span", `Vòng ${x.n}`, {class: "name"}),
      el("span", `${x.role} · ${x.stamp.slice(11, 16)}`, {class: "small muted"}), chip(vl, vt)]), [pre(x.body)], x.open, "round");
  });
  return el("li", null, {}, [when, el("span", TL_MARK[kind], {class: `mk ${kind}`, "aria-hidden": "true"}), box("ev", [box("tl-top", top),
    ...(r.percent ? [el("progress", null, {class: "track bar-t", max: "100", value: String(r.percent), "aria-hidden": "true"})] : []),
    ...(r.state === "running" ? [el("p", `Tính đến ${now}, cập nhật khi làm mới board.`, {class: "small muted"})] : []), ...rounds])]);
}
function timelineSection(id, d) {
  const t = d.timeline || {rows: []};
  const raw = disclosure(`raw:${id}`, el("summary", "Văn bản gốc"), [pre(d.steps)], false, "panel raw");
  if (!t.rows.length) return [section("Dòng thời gian", [el("div", null, {class: "empty-box"}, [el("p", "Chưa có bước nào được ghi", {class: "strong"}),
    el("p", "Dòng thời gian xuất hiện khi omi step ghi dòng “started” đầu tiên vào mục ## Steps của task.", {class: "muted small"})])], null, "panel", "tl-h"), raw];
  const s = t.summary;
  return [section("Dòng thời gian", [box("sum", [el("span", `Tổng thời gian: ${t.summary.duration}`),
    el("span", `Bước: ${s.steps} (${s.done} xong${s.running ? `, ${s.running} đang chạy` : ""})`),
    ...(s.rounds ? [el("span", `Review: ${s.rounds} vòng${s.fails ? ` · ${s.fails} FAIL` : ""}`)] : [])]),
    el("ol", null, {class: "tl"}, t.rows.map((r) => tlRow(id, r, t.now)))], "Giờ địa phương · cũ → mới", "panel", "tl-h"), raw];
}
function filesSection(files) {
  if (!files?.length) return [];
  const panel = section(`Tệp đã đổi · ${files.length}`, [el("ul", null, {class: "files mono"}, files.map((f) => {
    const cut = f.lastIndexOf("/") + 1;
    return el("li", null, {}, [el("span", f.slice(0, cut), {class: "dir"}), el("span", f.slice(cut))]);
  }))], null, "panel", "files-h");
  panel.children[0].append(el("span", null, {class: "muted small"}, [el("span", "Ghi bởi "), el("code", "omi step"), el("span", " · so với development")]));
  return [panel];
}
function timelineLoading() {
  return el("section", null, {class: "panel", "aria-busy": "true", "aria-labelledby": "tl-h"}, [el("h2", "Dòng thời gian", {id: "tl-h"}),
    el("p", "Đang tải…", {class: "muted small", role: "status"}),
    ...["", " short", ""].map((c) => el("div", null, {class: `skeleton${c}`, "aria-hidden": "true"}))]);
}
function taskPage(name, id, d) {
  const f = d.frontmatter, timeline = timelineSection(id, d);
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
  return [box("stack", [link(`← Về dự án ${name}`, filteredProjectHref(name), "small"), box("row", [
    box("chips", [el("span", id, {class: "mono muted"}), heading(f.title || id), typeChip(d), statusChip(d, !!d.children?.length)])])]),
    workflow(d), box("layout", [box("main", [
      section("Mục tiêu", [el("p", d.goal || "—", {class: "goal"})]),
      section("Tiêu chí nghiệm thu", [criteria], `${d.criteria.filter((c) => c.checked).length}/${d.criteria.length} xong`),
      section("Checkpoint", [pre(d.checkpoint)]), ...timeline.slice(0, 1), ...filesSection(d.files), ...timeline.slice(1),
      section(`Báo cáo (${reports.length})`, reports.length ? reports : [empty("Chưa có báo cáo.")])]),
    el("aside", null, {class: "side"}, [section("Thông tin", [meta]), section("Sử dụng", [taskUsage(d.usage)],
      `${num(d.usage.runs)} lượt · ${num(d.usage.review_rounds)} vòng review`)])])];
}
