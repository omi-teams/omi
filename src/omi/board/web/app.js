"use strict";
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
  err.replaceChildren(el("span", `${seen === null ? "Không tải được dữ liệu. Thử làm mới." : "Không làm mới được. Đang hiển thị dữ liệu lần tải trước."} (${e.name === "AbortError" ? "quá thời gian chờ" : e.message}). `), retry);
}
async function route(button = null) {
  const hash = location.hash === "#main" ? current || "#/" : location.hash || "#/";
  const routePath = hash.split("?")[0];
  if (!button && loadedDashboard && routePath === projectHref(loadedDashboard.name) && current.split("?")[0] === routePath && hash !== current) {
    current = hash; updateFilters(); updateSidebar(); focusBoardSection(); return;
  }
  const previous = current;
  const changed = hash !== current;
  current = hash;
  if (changed) {
    clearTimeout(resultTimer);
    seen = null; openReports = null; revision = null;
    if (hash.split("?")[0].split("/t/")[0] !== previous.split("?")[0].split("/t/")[0]) disclosures = new Map();

  }
  loading = true;
  view.setAttribute("aria-busy", "true");
  const label = button ? [...button.childNodes || button.children] : [];
  if (button) { button.disabled = true; button.textContent = "Đang tải…"; }
  const ticket = ++request;
  const abort = new AbortController();
  const limit = setTimeout(() => abort.abort(), 10000);
  try {
    const m = routePath.match(/^#\/p\/([^/]+)(?:\/t\/([^/]+)|\/(cost)|\/(graph)(?:\/([^/]+))?)?$/);
    const name = m ? decodeURIComponent(m[1]) : null;
    const id = m?.[2] ? decodeURIComponent(m[2]) : null;
    const costs = !!m?.[3];
    const graph = !!m?.[4];
    const isInbox = routePath === "#/inbox";
    updateSidebar(name);
    if (changed) {
      filterUI = null;
      view.replaceChildren(heading(isInbox ? "Hộp thư PO" : costs ? "Chi phí và quota" : graph ? "Đồ thị phụ thuộc" : id || name || "Dự án"),
      ...(name && !id && !costs && !graph ? filterWorkspace(name, [], true) : id ? [timelineLoading()] : [el("div", null, {class: "skeleton", "aria-hidden": "true"}), el("p", "Đang tải…")]));
    }
    const path = name ? `/api/projects/${enc(name)}${id ? "/tasks/" + enc(id) : costs ? "/cost" : graph ? "/graph" : ""}` : "/api/projects";
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
    updateSidebar(name || board.projects?.[0]?.name);
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
    const previousUI = filterUI;
    let nodes;
    try { nodes = isInbox ? inboxPage(items) : name ? costs ? costPage(name, data) : graph ? graphPage(name, data, graphScope(data, m[5] && decodeURIComponent(m[5]))) : id ? taskPage(name, id, data) : dashboard(name, data) : home(data.projects); }
    catch (e) { filterUI = previousUI; throw e; }
    loadedDashboard = name && !costs && !graph && !id ? {name, data} : null;
    if (loadedDashboard) {
      const canonical = boardSectionHref(projectHref(name) + filterQuery(filterUI.state));
      if (viewHash() !== canonical) { window.history.replaceState(null, "", canonical); current = canonical; }
    }
    const scrolled = window.scrollY;
    const focused = document.activeElement;
    const focusInView = !changed && view.contains(focused);
    view.replaceChildren(...nodes);
    if (loadedDashboard) carryFilters(name, filterUI.state);
    if (graph) fitGraph();
    if (isInbox) {
      renderNotificationSettings();
      const listTitle = view.querySelectorAll("h2")[1];
      listTitle.setAttribute("id", "inbox-title"); listTitle.setAttribute("tabindex", "-1");
      listTitle.setAttribute("aria-label", `Đang chờ quyết định: ${items.length} việc`);
      view.querySelectorAll("section")[1].querySelectorAll("span")[0]?.setAttribute("role", "status");
    }
    if (focusInView) {
      const control = focused.getAttribute("data-control");
      const replacement = [...view.querySelectorAll("a, summary, button, input, select")].find(n => control ? n.getAttribute("data-control") === control :
        n.tagName === focused.tagName && n.getAttribute("href") === focused.getAttribute("href") &&
        n.textContent === focused.textContent);
      (replacement || (isInbox ? document.getElementById("inbox-title") : view)).focus({preventScroll: true});
    } else if (!changed && focused !== document.body && focused.isConnected === false) {
      view.focus({preventScroll: true});
    } else if (!changed && focused.isConnected && document.activeElement !== focused) {
      focused.focus({preventScroll: true});
    }
    if (!changed) window.scrollTo(0, scrolled);
    if (changed) setNav(isInbox ? [["Hộp thư PO"]] : name ? id || costs || graph ? [[name, id ? filteredProjectHref(name) : projectHref(name)], [id || (graph ? "Đồ thị phụ thuộc" : "Chi phí")]] : [[name]] : []);
    acceptInbox(items);
    seen = contentKey;
    revision = board.source.sha;
    updated(data.source);
    if (changed) { document.getElementById("title").focus(); focusBoardSection(); }
  } catch (e) {
    if (ticket !== request) return;
    if (seen === null && !filterUI) view.replaceChildren(document.getElementById("title"));
    if (seen === null && filterUI) {
      filterUI.results.replaceChildren();
      filterUI.count.textContent = "Bộ lọc khả dụng sau khi tải dữ liệu.";
    }
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
function navigate() {
  // History traversal emits both events; restore once and never refetch for the second.
  if (location.hash !== "#main" && location.hash !== current) return route();
}
window.addEventListener("hashchange", navigate);
window.addEventListener("popstate", navigate);
document.addEventListener("keydown", event => {
  const target = event.target;
  if (event.key !== "/" || event.isComposing || event.ctrlKey || event.metaKey || event.altKey || event.shiftKey ||
      target?.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(target?.tagName?.toUpperCase())) return;
  const search = document.getElementById("board-search");
  if (search && !search.disabled && loadedDashboard && current.split("?")[0] === projectHref(loadedDashboard.name)) {
    event.preventDefault(); search.focus();
  }
});
let sidebarProject = null;
initSidebar();
schedule();
route(refresh);

function selectedBoardSection() {
  const match = viewHash().match(/[?&]section=(tree|kanban|notifications)(?:&|$)/);
  return match ? match[1] : "";
}
function boardSectionHref(href) {
  const section = selectedBoardSection();
  return section ? href + (href.includes("?") ? "&" : "?") + "section=" + section : href;
}
function focusBoardSection() {
  const section = selectedBoardSection();
  const target = document.getElementById(section === "notifications" ? "notification-settings" : "board-" + section);
  if (section && target) {
    target.setAttribute("tabindex", "-1"); target.focus(); target.scrollIntoView({block: "start"});
  }
}
function updateSidebar(name) {
  const list = document.getElementById("sidebar-links");
  if (!list) return;
  if (name) sidebarProject = name;
  const key = JSON.stringify([sidebarProject, viewHash()]);
  if (list.getAttribute("data-view") === key) return;
  list.setAttribute("data-view", key);
  const project = sidebarProject ? projectHref(sidebarProject) : "#/";
  const items = [["Tổng quan dự án", project],
    ...(sidebarProject ? [["Cây công việc", project + "?section=tree"], ["Kanban", project + "?section=kanban"]] : []),
    ["Hộp thư PO", "#/inbox"],
    ...(sidebarProject ? [["Chi phí", project + "/cost"], ["Đồ thị phụ thuộc", project + "/graph"]] : []),
    ["Thông báo", "#/inbox?section=notifications"]];
  list.replaceChildren(...items.map(([label, href]) => el("li", null, {}, [
    el("a", label, {href, ...(viewHash() === href ? {"aria-current": "page"} : {})})])));
}
function initSidebar() {
  const toggle = document.getElementById("sidebar-toggle");
  if (!toggle) return;
  const sidebar = document.getElementById("board-sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  const main = document.getElementById("main");
  const phone = window.matchMedia("(max-width: 767px)");
  let preferred = null;
  try { preferred = window.localStorage.getItem("omi-board-sidebar"); } catch (_) { /* Storage may be disabled. */ }
  function setOpen(open, remember = false) {
    if (!open && sidebar.contains(document.activeElement)) toggle.focus();
    sidebar.hidden = !open;
    toggle.setAttribute("aria-expanded", String(open));
    document.body.classList.toggle("sidebar-open", open);
    backdrop.hidden = !(open && phone.matches);
    main.inert = open && phone.matches;
    if (remember) {
      preferred = open ? "open" : "closed";
      try { window.localStorage.setItem("omi-board-sidebar", preferred); } catch (_) { /* Keep this tab usable. */ }
    }
  }
  toggle.addEventListener("click", () => setOpen(sidebar.hidden, true));
  backdrop.addEventListener("click", () => setOpen(false, true));
  sidebar.addEventListener("click", event => {
    if (!event.target.closest("a")) return;
    if (phone.matches) setOpen(false);
    // Clicking the current section should still move focus to its content.
    if (event.target.closest("a").getAttribute("href") === viewHash()) focusBoardSection();
  });
  document.addEventListener("keydown", event => {
    if (sidebar.hidden) return;
    if (event.key === "Escape") { event.preventDefault(); setOpen(false, true); toggle.focus(); }
    if (event.key === "Tab" && phone.matches) {
      const controls = [toggle, ...sidebar.querySelectorAll("a")];
      const index = controls.indexOf(document.activeElement);
      event.preventDefault(); controls[(index + (event.shiftKey ? -1 : 1) + controls.length) % controls.length].focus();
    }
  });
  phone.addEventListener("change", () => setOpen(!phone.matches && preferred !== "closed"));
  // Phones always start collapsed; the stored choice controls desktop reloads.
  setOpen(!phone.matches && preferred !== "closed");
  updateSidebar();
}
