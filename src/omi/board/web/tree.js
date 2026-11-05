"use strict";
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
function taskTree(name, items, matches = null) {
  const byId = new Map(items.map(t => [t.id, t]));
  function node(t, ancestors = new Set()) {
    const path = new Set([...ancestors, t.id]);
    const kids = (t.children || []).map(id => byId.get(id)).filter(k => k && !path.has(k.id));
    const badges = [typeChip(t), el("span", t.id, {class: "mono"}), statusChip(t, !!t.children?.length),
      ...(matches && !matches.has(t.id) ? [el("span", "Ngữ cảnh; không khớp bộ lọc", {class: "context-label small muted"})] : [])];
    if (!kids.length) return box("leaf", [box("chips", badges), link(t.frontmatter.title || t.id, taskHref(name, t.id))]);
    const done = kids.filter(k => statusOf(k) === "done").length;
    const bar = progress(done, kids.length);
    bar.setAttribute("aria-label", `${t.id}: ${done}/${kids.length} con trực tiếp đã xong`);
    return disclosure(`tree:${t.id}`, el("summary", null, {}, [box("chips", badges), el("span", t.frontmatter.title || "—"),
      box("progress-row", [bar, el("span", `${done}/${kids.length}`, {class: "small"})])]),
      [box("children", kids.filter(k => !isDoneLeaf(k)).map(k => node(k, path)))],
      !["done", "blocked"].includes(statusOf(t)), "", !!matches);
  }
  // Every done leaf joins one closed group after the tree; its state lives in `disclosures`.
  const isDoneLeaf = k => statusOf(k) === "done" && !(k.children || []).some(id => byId.has(id));
  const roots = items.filter(t => !byId.has(t.parent)).sort((a, b) => a.id.localeCompare(b.id));
  const finished = items.filter(isDoneLeaf);
  const rows = roots.filter(t => !isDoneLeaf(t)).map(t => node(t));
  return box("tree", roots.length ? [...rows, ...(finished.length ? [disclosure("tree-done", el("summary", `${num(finished.length)} task đã xong`),
    finished.map(k => node(k)), false, "done-leaves", !!matches)] : [])] : [empty("Chưa có task. Các task sẽ xuất hiện sau lần cập nhật dữ liệu kế tiếp.")]);
}
function leafCounts(d) {
  const count = Object.fromEntries(Object.keys(STATUS).map(s => [s, 0]));
  for (const t of Object.values(d.kanban).flat().filter(t => !t.children?.length)) count[statusOf(t)] = (count[statusOf(t)] || 0) + 1;
  return count;
}
const FILTER_KEYS = ["q", "status", "type", "plan", "role"];
const FILTER_NOTICE = "Một số bộ lọc không còn khả dụng đã được bỏ qua.";
let loadedDashboard = null;
let filterUI = null;
let resultTimer = null;
const metadataValue = value => value === undefined || value === null || value === "" ? "~none" : String(value).replace(/^~/, "~~");
const typeOf = t => t.type || "task";
function filterOptions(tasks) {
  return {status: Object.entries(STATUS), type: Object.entries(TYPES),
    plan: metadataOptions(tasks, "plan", "Không có kế hoạch"),
    role: metadataOptions(tasks, "role", "Chưa có vai trò")};
}
function metadataOptions(tasks, key, missing) {
  const values = [...new Set(tasks.map(t => metadataValue(t.frontmatter[key])))].sort();
  return values.map(value => [value, value === "~none" ? missing : value.replace(/^~~/, "~")]);
}
function readFilters(hash, tasks = null) {
  const state = {};
  let invalid = false;
  const options = tasks === null ? null : filterOptions(tasks);
  const found = new Set();
  for (const pair of (hash.split("?").slice(1).join("?") || "").split("&")) {
    const [rawKey, ...rest] = pair.split("=");
    let key;
    try { key = decodeURIComponent(rawKey.replace(/\+/g, " ")); } catch (_) { continue; }
    if (!FILTER_KEYS.includes(key) || found.has(key)) continue;
    found.add(key);
    let value;
    try { value = decodeURIComponent(rest.join("=").replace(/\+/g, " ")); }
    catch (_) { invalid = true; continue; }
    if (key === "q") { if (value.trim()) state.q = value.trim(); }
    else if (value && (!options || options[key].some(([v]) => v === value))) state[key] = value;
    else if (value) invalid = true;
  }
  return {state, invalid};
}
function filterQuery(state) {
  const pairs = FILTER_KEYS.filter(key => state[key]).map(key => `${key}=${enc(state[key])}`);
  return pairs.length ? "?" + pairs.join("&") : "";
}
const activeFilters = state => FILTER_KEYS.some(key => !!state[key]);
function matchesFilters(t, state) {
  const query = (state.q || "").trim().toLocaleLowerCase("vi");
  return (!query || t.id.toLocaleLowerCase("vi").includes(query) || String(t.frontmatter.title || "").toLocaleLowerCase("vi").includes(query)) &&
    (!state.status || statusOf(t) === state.status) && (!state.type || typeOf(t) === state.type) &&
    ["plan", "role"].every(key => !state[key] || metadataValue(t.frontmatter[key]) === state[key]);
}
function filterDescription(state, tasks) {
  const labels = {status: "Trạng thái", type: "Loại", plan: "Kế hoạch", role: "Vai trò"};
  const options = filterOptions(tasks);
  const parts = FILTER_KEYS.filter(key => state[key]).map(key => key === "q" ? `từ khóa “${state.q}”` :
    `${labels[key]} ${options[key].find(([value]) => value === state[key])?.[1] || state[key]}`);
  return parts.length ? "Đang lọc: " + parts.join(" · ") : "";
}
function changeFilters(state, method) {
  if (!filterUI || !loadedDashboard) return;
  const hash = projectHref(loadedDashboard.name) + filterQuery(state);
  window.history[method](null, "", hash);
  current = hash;
  updateFilters(method === "replaceState", method === "replaceState");
}
function updateFilters(fromControl = false, typing = false) {
  if (!filterUI || !loadedDashboard) return;
  const {name, data} = loadedDashboard;
  const tasks = Object.values(data.kanban).flat();
  const {state, invalid} = readFilters(viewHash(), tasks);
  filterUI.state = state;
  filterUI.feedback.textContent = "";
  filterUI.fallback.replaceChildren();
  const canonical = projectHref(name) + filterQuery(state);
  if (viewHash() !== canonical) { window.history.replaceState(null, "", canonical); current = canonical; }
  for (const key of FILTER_KEYS) {
    // Leave the exact text and caret alone during input; matching trims it.
    if (!fromControl || key !== "q") filterUI.controls[key].value = state[key] || "";
  }
  filterUI.reset.disabled = !activeFilters(state);
  filterUI.notice.textContent = invalid ? FILTER_NOTICE : "";
  filterUI.summary.textContent = filterDescription(state, tasks);
  const matches = tasks.filter(t => matchesFilters(t, state));
  const text = `${num(matches.length)} / ${num(tasks.length)} công việc khớp · ${num(matches.filter(t => !t.children?.length).length)} task lá trên Kanban`;
  clearTimeout(resultTimer);
  const count = filterUI.count;
  if (typing) resultTimer = setTimeout(() => { count.textContent = text; }, 250);
  else filterUI.count.textContent = text;
  filterUI.results.replaceChildren(...taskResults(name, tasks, state));
  carryFilters(name, state);
}
function carryFilters(name, state) {
  // All task links, including the PO/activity sections, carry the view.
  for (const node of view.querySelectorAll("a")) {
    const href = node.getAttribute("href");
    if (href?.startsWith(`${projectHref(name)}/t/`)) node.setAttribute("href", href.split("?")[0] + filterQuery(state));
  }
}
function filterWorkspace(name, tasks, disabled = false) {
  const {state, invalid} = readFilters(viewHash(), disabled ? null : tasks);
  const controls = {};
  const defaults = {status: "Tất cả trạng thái", type: "Tất cả loại", plan: "Tất cả kế hoạch", role: "Tất cả vai trò"};
  const labels = {q: "Tìm ID hoặc tiêu đề", status: "Trạng thái", type: "Loại", plan: "Kế hoạch", role: "Vai trò"};
  const options = filterOptions(tasks);
  const fields = FILTER_KEYS.map(key => {
    const id = key === "q" ? "board-search" : `filter-${key}`;
    const control = key === "q" ? el("input", null, {id, type: "search", placeholder: "VD: TASK-129 hoặc board",
      "aria-keyshortcuts": "/", "aria-describedby": "filter-help", "data-control": id}) : el("select", null, {id, "data-control": id},
      [["", defaults[key]], ...options[key]].map(([value, label]) => el("option", label, {value})));
    if (disabled && key !== "q" && state[key] && !options[key].some(([value]) => value === state[key]))
      control.append(el("option", state[key], {value: state[key]}));
    control.value = state[key] || "";
    control.disabled = disabled;
    controls[key] = control;
    control.addEventListener(key === "q" ? "input" : "change", () => {
      const next = {...filterUI.state, [key]: key === "q" ? control.value.trim() : control.value};
      changeFilters(next, key === "q" ? "replaceState" : "pushState");
    });
    if (key === "q") control.addEventListener("keydown", event => {
      if (event.key === "Escape" && !event.isComposing) {
        event.preventDefault(); control.value = ""; changeFilters({...filterUI.state, q: ""}, "replaceState");
      }
      if (event.key === "Enter") event.preventDefault();
    });
    return el("label", labels[key], {for: id, class: key === "q" ? "filter-search" : ""}, [control]);
  });
  const reset = el("button", "Đặt lại bộ lọc", {type: "button", class: "btn", "data-control": "filter-reset"});
  reset.disabled = disabled || !activeFilters(state);
  reset.addEventListener("click", () => { controls.q.value = ""; changeFilters({}, "pushState"); });
  const feedback = el("p", "", {role: "status", class: "small"});
  const fallback = box("share-fallback", []);
  const copy = el("button", "Sao chép liên kết", {type: "button", class: "btn", "data-control": "filter-copy"});
  copy.disabled = disabled;
  copy.addEventListener("click", async () => {
    const url = location.href.split("#")[0] + projectHref(name) + filterQuery(filterUI.state);
    fallback.replaceChildren();
    try {
      await window.navigator.clipboard.writeText(url);
      feedback.textContent = "Đã sao chép liên kết.";
    } catch (_) {
      feedback.textContent = "Không sao chép được. Chọn và sao chép liên kết bên dưới.";
      const input = el("input", null, {id: "share-url", type: "text", readonly: ""}); input.value = url;
      fallback.append(el("label", "Liên kết chế độ xem", {for: "share-url"}, [input]));
    }
  });
  const count = el("p", disabled ? "Đang tải…" : "", {role: "status", class: "filter-count"});
  const notice = el("p", invalid ? FILTER_NOTICE : "", {role: "status", class: "filter-notice small"});
  const results = box("task-results stack", []);
  const summary = el("p", disabled ? "" : filterDescription(state, tasks), {class: "filter-summary small muted"});
  const panel = section("Tìm và lọc công việc", [
    el("p", "Tổng quan dự án giữ nguyên; bộ lọc áp dụng cho cây công việc và Kanban bên dưới.", {class: "small muted"}), box("filters", fields),
    el("p", "/ để tìm kiếm · Esc xóa từ khóa · Các bộ lọc kết hợp với nhau.", {id: "filter-help", class: "muted small"}),
    box("filter-actions", [reset, copy]), feedback, fallback, notice, count, summary], "Chỉ đọc");
  filterUI = {state, controls, reset, count, notice, results, summary, feedback, fallback};
  if (disabled) results.append(el("div", null, {class: "skeleton", "aria-hidden": "true"}));
  else {
    const matches = tasks.filter(t => matchesFilters(t, state));
    count.textContent = `${num(matches.length)} / ${num(tasks.length)} công việc khớp · ${num(matches.filter(t => !t.children?.length).length)} task lá trên Kanban`;
    results.append(...taskResults(name, tasks, state));
  }
  return [panel, results];
}
function taskResults(name, tasks, state) {
  const matching = tasks.filter(t => matchesFilters(t, state));
  const matches = new Set(matching.map(t => t.id));
  const visible = new Set(matches);
  const byId = new Map(tasks.map(t => [t.id, t]));
  for (const t of matching) {
    let parent = t.parent;
    const path = new Set([t.id]);
    while (byId.has(parent) && !path.has(parent)) {
      visible.add(parent); path.add(parent); parent = byId.get(parent).parent;
    }
  }
  const leaves = tasks.filter(t => matches.has(t.id) && !t.children?.length);
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
    const head = el("summary", null, {class: "colh"}, [chip(label, key), el("span", num(items.length), {class: "muted"})]);
    const column = items.length ? disclosure(`col:${key}`, head, cards, key !== "done", `col col-${key}`)
      : box(`col col-${key}`, [box("colh", [chip(label, key), el("span", "0", {class: "muted"})]), empty("Chưa có task.")]);
    (items.length ? columns : vacant).push(column);
  }
  const board = leaves.length ? box("stack", [box("kanban", columns), ...(vacant.length ? [disclosure("empty-phases",
    el("summary", `${vacant.length} giai đoạn trống`), [box("kanban", vacant)], false, "empty-phases")] : [])]) : empty("Không có task lá khớp bộ lọc trên Kanban.");
  if (!tasks.length) return [empty("Chưa có công việc trong dự án này."),
    el("p", "Board chỉ đọc. Thêm task trong repo rồi làm mới.", {class: "muted small"})];
  if (!matching.length) {
    const reset = el("button", "Đặt lại bộ lọc", {type: "button", class: "btn"});
    reset.addEventListener("click", () => { changeFilters({}, "pushState"); document.getElementById("board-search").focus(); });
    return [box("no-results", [el("h2", "Không tìm thấy công việc phù hợp."),
      el("p", "Thử từ khóa khác hoặc đặt lại bộ lọc."), reset])];
  }
  return [section("Cây công việc", [el("p", "Trạng thái cha tổng hợp từ con trực tiếp; mở một hàng để xem cấp dưới.", {class: "muted small"}),
    disclosure("tree-block", el("summary", "Thu gọn / mở cây công việc"),
      [taskTree(name, tasks.filter(t => visible.has(t.id)), activeFilters(state) ? matches : null)], true, "tree-block")]),
    section("Kanban", [el("p", "Chỉ task lá · thứ tự pha cố định · cột trống thu gọn", {class: "muted small"}), board])];
}
