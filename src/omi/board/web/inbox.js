"use strict";
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
