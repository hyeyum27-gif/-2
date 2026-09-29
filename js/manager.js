/*
  교육비 관리 동작
  ------------------------------------------------------------
  데이터는 localStorage 의 STORAGE_KEY 한 곳에 JSON 으로 저장됩니다.
  {
    students: [{ id, name, grade, className, fee, dueDay, startMonth, endMonth, phone, memo }],
    payments: { "학생id|2026-09": { amount, date, method } }
  }
  startMonth ~ endMonth 사이의 달에만 교육비가 청구됩니다. (endMonth 가 없으면 재원 중)
  재등록한 학생은 쉬었던 기간이 breaks: [{ from, to }] 로 남아 그 달은 청구되지 않습니다.
  ------------------------------------------------------------
*/

const STORAGE_KEY = "haenaem-tuition-v1";
const ACADEMY_NAME = "해냄수학전문학원";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

/* ---------- 날짜, 금액 도우미 ---------- */
const pad = (n) => String(n).padStart(2, "0");
const toMonth = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}`;
const toDate = (d) => `${toMonth(d)}-${pad(d.getDate())}`;
function shiftMonth(month, step) {
  const [y, m] = month.split("-").map(Number);
  return toMonth(new Date(y, m - 1 + step, 1));
}
function monthText(month) {
  const [y, m] = month.split("-").map(Number);
  return `${y}년 ${m}월`;
}
const won = (n) => `${Math.round(n).toLocaleString("ko-KR")}원`;
const parseWon = (s) => Number(String(s).replace(/[^\d]/g, "")) || 0;
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const newId = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 7);

/* ---------- 저장소 ---------- */
function emptyState() { return { students: [], payments: {} }; }
function isValidState(s) {
  return s && Array.isArray(s.students) && s.payments && typeof s.payments === "object";
}
function load() {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY));
    return isValidState(parsed) ? parsed : emptyState();
  } catch { return emptyState(); }
}
function save() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }
  catch { toast("저장하지 못했습니다. 백업 파일을 저장해 두세요."); }
}

let state = load();
let viewMonth = toMonth(new Date());
let filter = "all";
let query = "";

/* ---------- 계산 ---------- */
const payKey = (id, month) => `${id}|${month}`;
const isBilled = (s, month) =>
  s.startMonth <= month && (!s.endMonth || month <= s.endMonth) &&
  !(s.breaks || []).some((b) => b.from <= month && month <= b.to);
const isActiveNow = (s) => !s.endMonth || s.endMonth >= toMonth(new Date());

function statusOf(s, month) {
  const pay = state.payments[payKey(s.id, month)];
  const paid = pay ? pay.amount : 0;
  if (paid >= s.fee) return { code: "paid", label: "완납", pay, paid };
  if (paid > 0) return { code: "partial", label: `${won(s.fee - paid)} 남음`, pay, paid };
  const now = new Date();
  const thisMonth = toMonth(now);
  const late = month < thisMonth || (month === thisMonth && now.getDate() > s.dueDay);
  return late ? { code: "late", label: "미납", pay, paid } : { code: "due", label: "납부 예정", pay, paid };
}

function billedRows(month) {
  return state.students
    .filter((s) => isBilled(s, month))
    .map((s) => ({ s, st: statusOf(s, month) }))
    .sort((a, b) => a.s.name.localeCompare(b.s.name, "ko"));
}

/* ---------- 화면 그리기 ---------- */
function render() {
  $("#month-label").textContent = monthText(viewMonth);
  const rows = billedRows(viewMonth);

  // 요약
  const total = rows.reduce((t, r) => t + r.s.fee, 0);
  const paid = rows.reduce((t, r) => t + Math.min(r.st.paid, r.s.fee), 0);
  const done = rows.filter((r) => r.st.code === "paid").length;
  const rate = total ? Math.round((paid / total) * 100) : 0;
  $("#stat-total").textContent = won(total);
  $("#stat-count").textContent = `${rows.length}명`;
  $("#stat-paid").textContent = won(paid);
  $("#stat-paid-count").textContent = `${done}명 완납`;
  $("#stat-unpaid").textContent = won(total - paid);
  $("#stat-unpaid-count").textContent = `${rows.length - done}명`;
  $("#stat-rate").textContent = `${rate}%`;
  $("#stat-meter").style.width = `${rate}%`;

  // 목록
  const q = query.trim().toLowerCase();
  const visible = rows.filter(({ s, st }) => {
    if (filter === "paid" && st.code !== "paid") return false;
    if (filter === "unpaid" && st.code === "paid") return false;
    if (!q) return true;
    return [s.name, s.grade, s.className, s.phone].some((v) => String(v || "").toLowerCase().includes(q));
  });

  $("#student-list").innerHTML = visible.map(({ s, st }) => {
    const record = st.pay ? `${st.pay.date.slice(5).replace("-", "/")} · ${esc(st.pay.method)} · ${won(st.pay.amount)}` : "";
    const payLabel = st.code === "paid" ? "수정" : "납부";
    return `
      <li class="student" data-id="${s.id}">
        <div class="s-who">
          <span class="s-name">${esc(s.name)}</span>
          <span class="s-meta">${esc([s.grade, s.className].filter(Boolean).join(" · "))}${s.memo ? ` · ${esc(s.memo)}` : ""}</span>
        </div>
        <span class="s-fee">${won(s.fee)}</span>
        <span class="s-due">매월 ${s.dueDay}일</span>
        <span class="badge badge-${st.code}">${st.label}</span>
        <span class="s-record">${record}</span>
        <div class="row-actions">
          <button class="btn btn-sm ${st.code === "paid" ? "btn-ghost" : "btn-pay"}" type="button" data-action="pay">${payLabel}</button>
          <button class="btn btn-ghost btn-sm" type="button" data-action="edit">정보</button>
        </div>
      </li>`;
  }).join("");

  const empty = $("#empty");
  empty.hidden = visible.length > 0;
  if (!state.students.length) {
    $("#empty-title").textContent = "아직 등록된 학생이 없습니다";
    $("#empty-text").textContent = "\"학생 추가\"를 눌러 첫 학생을 등록하세요. 등록한 달부터 교육비가 청구 목록에 올라옵니다.";
  } else if (!rows.length) {
    $("#empty-title").textContent = `${monthText(viewMonth)}에 청구할 학생이 없습니다`;
    $("#empty-text").textContent = "등록한 달보다 이전이거나, 퇴원 이후의 달입니다.";
  } else {
    $("#empty-title").textContent = "조건에 맞는 학생이 없습니다";
    $("#empty-text").textContent = "검색어나 필터를 바꿔 보세요.";
  }

  // 퇴원생
  const archived = state.students.filter((s) => !isActiveNow(s)).sort((a, b) => b.endMonth.localeCompare(a.endMonth));
  $("#archived-wrap").hidden = !archived.length;
  $("#archived-count").textContent = `${archived.length}명`;
  $("#archived-list").innerHTML = archived.map((s) => `
    <li data-id="${s.id}">
      <span class="s-name">${esc(s.name)}</span>
      <span class="s-meta">${esc(s.grade)} · ${monthText(s.startMonth)} ~ ${monthText(s.endMonth)}</span>
      <div class="row-actions">
        <button class="btn btn-ghost btn-sm" type="button" data-action="restore">재등록</button>
        <button class="btn btn-ghost btn-sm danger-text" type="button" data-action="delete">기록 삭제</button>
      </div>
    </li>`).join("");
}

/* ---------- 알림 ---------- */
let toastTimer;
function toast(msg) {
  const el = $("#toast");
  el.textContent = msg;
  el.classList.add("is-show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("is-show"), 2400);
}

/* ---------- 분할 버튼(라디오) ---------- */
function setupSeg(root, attr, onChange) {
  root.addEventListener("click", (e) => {
    const btn = e.target.closest(`[${attr}]`);
    if (!btn) return;
    $$(`[${attr}]`, root).forEach((b) => b.setAttribute("aria-checked", String(b === btn)));
    onChange(btn.getAttribute(attr));
  });
}
function segValue(root, attr) {
  return $(`[aria-checked="true"]`, root)?.getAttribute(attr);
}
function setSeg(root, attr, value) {
  $$(`[${attr}]`, root).forEach((b) => b.setAttribute("aria-checked", String(b.getAttribute(attr) === value)));
}

/* 금액 입력칸: 입력하는 동안 천 단위 쉼표 */
function formatMoneyInput(input) {
  input.addEventListener("input", () => {
    const n = parseWon(input.value);
    input.value = n ? n.toLocaleString("ko-KR") : "";
  });
}

/* ---------- 학생 추가/수정 ---------- */
const studentDialog = $("#student-dialog");
const studentForm = $("#student-form");
let editingId = null;

function openStudent(id = null) {
  editingId = id;
  const s = id ? state.students.find((x) => x.id === id) : null;
  $("#student-dialog-title").textContent = s ? "학생 정보" : "학생 추가";
  $("#f-name").value = s?.name ?? "";
  $("#f-grade").value = s?.grade ?? "중1";
  $("#f-class").value = s?.className ?? "";
  $("#f-fee").value = s ? s.fee.toLocaleString("ko-KR") : "";
  $("#f-due").value = String(s?.dueDay ?? 1);
  $("#f-start").value = s?.startMonth ?? viewMonth;
  $("#f-phone").value = s?.phone ?? "";
  $("#f-memo").value = s?.memo ?? "";
  $("#withdraw-student").hidden = !s || !isActiveNow(s);
  $$("#student-form [aria-invalid]").forEach((el) => el.removeAttribute("aria-invalid"));
  $$("#student-form .field-error").forEach((el) => { el.hidden = true; });
  studentDialog.showModal();
}

studentForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const name = $("#f-name").value.trim();
  const fee = parseWon($("#f-fee").value);
  let ok = true;
  [["#f-name", !name], ["#f-fee", !fee]].forEach(([sel, bad]) => {
    if (bad) $(sel).setAttribute("aria-invalid", "true");
    else $(sel).removeAttribute("aria-invalid");
    $(`${sel}-error`).hidden = !bad;
    if (bad && ok) { $(sel).focus(); ok = false; }
  });
  if (!ok) return;

  const data = {
    name, fee,
    grade: $("#f-grade").value,
    className: $("#f-class").value.trim(),
    dueDay: Number($("#f-due").value),
    startMonth: $("#f-start").value || viewMonth,
    phone: $("#f-phone").value.trim(),
    memo: $("#f-memo").value.trim(),
  };
  if (editingId) {
    Object.assign(state.students.find((x) => x.id === editingId), data);
    toast(`${name} 학생 정보를 저장했습니다`);
  } else {
    state.students.push({ id: newId(), endMonth: null, ...data });
    toast(`${name} 학생을 추가했습니다`);
  }
  save();
  studentDialog.close();
  render();
});

$("#withdraw-student").addEventListener("click", () => {
  const s = state.students.find((x) => x.id === editingId);
  if (!s) return;
  // 이번 달 교육비를 이미 받았으면 이번 달까지, 아니면 지난달까지 청구
  const thisMonth = toMonth(new Date());
  const paidThisMonth = state.payments[payKey(s.id, thisMonth)];
  const end = paidThisMonth ? thisMonth : shiftMonth(thisMonth, -1);
  const lastBilled = end < s.startMonth ? s.startMonth : end;
  if (!confirm(`${s.name} 학생을 퇴원 처리할까요?\n${monthText(lastBilled)}까지만 교육비가 청구됩니다. 납부 기록은 남아 있습니다.`)) return;
  s.endMonth = lastBilled;
  save();
  studentDialog.close();
  render();
  toast(`${s.name} 학생을 퇴원 처리했습니다`);
});

/* ---------- 납부 기록 ---------- */
const payDialog = $("#pay-dialog");
const payForm = $("#pay-form");
let payingId = null;

function openPay(id) {
  payingId = id;
  const s = state.students.find((x) => x.id === id);
  const pay = state.payments[payKey(id, viewMonth)];
  $("#pay-dialog-title").textContent = `${s.name} · ${monthText(viewMonth)}`;
  $("#pay-dialog-sub").textContent = `월 교육비 ${won(s.fee)} · 매월 ${s.dueDay}일`;
  $("#p-amount").value = (pay?.amount ?? s.fee).toLocaleString("ko-KR");
  const today = toDate(new Date());
  // 지난 달을 기록할 때는 그 달 기준일을 기본값으로
  const [y, m] = viewMonth.split("-").map(Number);
  const lastDay = new Date(y, m, 0).getDate();
  const fallback = viewMonth === toMonth(new Date()) ? today : `${viewMonth}-${pad(Math.min(s.dueDay, lastDay))}`;
  $("#p-date").value = pay?.date ?? fallback;
  setSeg($("#p-method"), "data-method", pay?.method ?? lastMethod(id));
  $("#unpay").hidden = !pay;
  payDialog.showModal();
}

/* 그 학생이 가장 최근에 쓴 납부 방법 */
function lastMethod(id) {
  const keys = Object.keys(state.payments).filter((k) => k.startsWith(`${id}|`)).sort();
  return keys.length ? state.payments[keys[keys.length - 1]].method : "계좌이체";
}

payForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const amount = parseWon($("#p-amount").value);
  const date = $("#p-date").value;
  if (!amount) { $("#p-amount").focus(); return; }
  if (!date) { $("#p-date").focus(); return; }
  state.payments[payKey(payingId, viewMonth)] = { amount, date, method: segValue($("#p-method"), "data-method") };
  save();
  payDialog.close();
  render();
  toast("납부 기록을 저장했습니다");
});

$("#unpay").addEventListener("click", () => {
  if (!confirm("이 달 납부 기록을 지울까요?")) return;
  delete state.payments[payKey(payingId, viewMonth)];
  save();
  payDialog.close();
  render();
  toast("납부 기록을 지웠습니다");
});

/* ---------- 미납 안내 복사 ---------- */
async function copyUnpaid() {
  const rows = billedRows(viewMonth).filter((r) => r.st.code !== "paid");
  if (!rows.length) { toast(`${monthText(viewMonth)} 미납자가 없습니다`); return; }
  const [, m] = viewMonth.split("-").map(Number);
  const lines = rows.map(({ s, st }) => {
    const left = s.fee - st.paid;
    return `- ${s.name}(${s.grade}) ${won(left)}${s.phone ? ` / ${s.phone}` : ""}`;
  });
  const text = `[${ACADEMY_NAME}] ${m}월 교육비 미납 ${rows.length}명\n${lines.join("\n")}`;
  try {
    await navigator.clipboard.writeText(text);
    toast("미납 목록을 복사했습니다");
  } catch {
    prompt("아래 내용을 복사하세요", text);
  }
}

/* ---------- 내보내기, 불러오기 ---------- */
function download(filename, content, type) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = Object.assign(document.createElement("a"), { href: url, download: filename });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function exportCsv() {
  const rows = billedRows(viewMonth);
  if (!rows.length) { toast("내보낼 학생이 없습니다"); return; }
  const cell = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const head = ["이름", "학년", "반", "월 교육비", "받은 금액", "납부일", "납부 방법", "상태", "보호자 연락처", "메모"];
  const body = rows.map(({ s, st }) => [
    s.name, s.grade, s.className, s.fee, st.paid, st.pay?.date, st.pay?.method,
    st.code === "partial" ? "일부 납부" : st.label, s.phone, s.memo,
  ].map(cell).join(","));
  // 엑셀에서 한글이 깨지지 않도록 BOM 을 붙임
  download(`교육비_${viewMonth}.csv`, "﻿" + [head.map(cell).join(","), ...body].join("\r\n"), "text/csv;charset=utf-8");
}

function exportJson() {
  download(`교육비_백업_${toDate(new Date())}.json`, JSON.stringify(state, null, 2), "application/json");
  toast("백업 파일을 저장했습니다");
}

async function importJson(file) {
  try {
    const parsed = JSON.parse(await file.text());
    if (!isValidState(parsed)) throw new Error("형식 오류");
    if (!confirm(`백업 파일의 학생 ${parsed.students.length}명 기록으로 지금 기록을 바꿀까요?\n지금 기록은 사라집니다.`)) return;
    state = { students: parsed.students, payments: parsed.payments };
    save();
    render();
    toast("백업을 불러왔습니다");
  } catch {
    toast("백업 파일을 읽지 못했습니다");
  }
}

/* ---------- 이벤트 연결 ---------- */
function init() {
  $("#f-due").innerHTML = Array.from({ length: 31 }, (_, i) => `<option value="${i + 1}">매월 ${i + 1}일</option>`).join("");
  formatMoneyInput($("#f-fee"));
  formatMoneyInput($("#p-amount"));

  $$("[data-month-step]").forEach((b) => b.addEventListener("click", () => {
    viewMonth = shiftMonth(viewMonth, Number(b.dataset.monthStep));
    render();
  }));
  $("#month-label").addEventListener("click", () => { viewMonth = toMonth(new Date()); render(); });

  $("#search").addEventListener("input", (e) => { query = e.target.value; render(); });
  setupSeg($(".toolbar .seg"), "data-filter", (v) => { filter = v; render(); });
  setupSeg($("#p-method"), "data-method", () => {});

  $("#add-student").addEventListener("click", () => openStudent());
  $("#copy-unpaid").addEventListener("click", copyUnpaid);
  $("#export-csv").addEventListener("click", exportCsv);
  $("#export-json").addEventListener("click", exportJson);
  $("#import-json").addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) importJson(file);
    e.target.value = "";
  });

  $("#student-list").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    const id = btn.closest("[data-id]").dataset.id;
    if (btn.dataset.action === "pay") openPay(id);
    if (btn.dataset.action === "edit") openStudent(id);
  });

  $("#archived-list").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    const id = btn.closest("[data-id]").dataset.id;
    const s = state.students.find((x) => x.id === id);
    if (btn.dataset.action === "restore") {
      // 퇴원 다음 달부터 지난달까지는 쉰 기간으로 남겨 청구하지 않음
      const from = shiftMonth(s.endMonth, 1);
      const to = shiftMonth(toMonth(new Date()), -1);
      if (from <= to) s.breaks = [...(s.breaks || []), { from, to }];
      s.endMonth = null;
      toast(`${s.name} 학생을 재등록했습니다`);
    }
    if (btn.dataset.action === "delete") {
      if (!confirm(`${s.name} 학생과 모든 납부 기록을 완전히 지울까요? 되돌릴 수 없습니다.`)) return;
      state.students = state.students.filter((x) => x.id !== id);
      Object.keys(state.payments).forEach((k) => { if (k.startsWith(`${id}|`)) delete state.payments[k]; });
      toast("기록을 삭제했습니다");
    }
    save();
    render();
  });

  $$("dialog [data-close]").forEach((b) => b.addEventListener("click", () => b.closest("dialog").close()));
  // 바깥(어두운 영역)을 누르면 닫기
  $$("dialog").forEach((d) => d.addEventListener("click", (e) => { if (e.target === d) d.close(); }));

  render();
}

init();
