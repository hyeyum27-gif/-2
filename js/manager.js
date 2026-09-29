/*
  교육비 관리 동작
  ------------------------------------------------------------
  데이터는 localStorage 의 STORAGE_KEY 한 곳에 JSON 으로 저장됩니다.
  {
    students: [{ id, name, grade, school, program, className, perWeek, fee, dueDay, startMonth, endMonth, phone, memo, note,
                 sourceId, enrollDate }],   // sourceId, enrollDate 는 엑셀 명단에서 불러온 학생만
    payments: { "학생id|2026-09": { amount, date, method } }
  }
  startMonth ~ endMonth 사이의 달에만 교육비가 청구됩니다. (endMonth 가 없으면 재원 중)
  fee 가 0 이면 "교육비 미정"으로 보고 합계에서 뺍니다. (엑셀 명단에는 교육비가 없음)
  재등록한 학생은 쉬었던 기간이 breaks: [{ from, to }] 로 남아 그 달은 청구되지 않습니다.
  ------------------------------------------------------------
*/

const STORAGE_KEY = "haenaem-tuition-v1";
const ACADEMY_NAME = "해냄수학전문학원";

/*
  교육비 기준표 (원) — 교육비가 바뀌면 여기만 고치면 됩니다.
  초1~4 학년은 주 수업 횟수에 따라, 나머지는 학년에 따라 정해집니다.
  이미 교육비가 들어간 학생은 바뀌지 않습니다. (학생 정보 창에서 직접 고치세요)
*/
const FEE_TABLE = {
  lowerElementary: { 2: 140000, 3: 160000, 4: 180000, 5: 200000 }, // 초1~4: 주 2회, 3회, 4회, 5회
  upperElementary: 250000, // 초5~6
  middle: 300000,          // 중1~3
  high: 350000,            // 고1~3
  // 학년, 횟수와 상관없이 금액이 정해진 수업. 수업을 늘리려면 한 줄 추가하면 됩니다.
  programs: {
    "공필왕": 120000,
    "책통": 120000,
    "사고력": 120000,
    "요리수연산": 120000,
  },
};

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

/* ---------- 교육비 기준표 ---------- */
const isLowerElementary = (grade) => /^초[1-4]$/.test(grade);
function feeFor(grade, perWeek, program) {
  if (program) return FEE_TABLE.programs[program] || 0;
  if (isLowerElementary(grade)) return FEE_TABLE.lowerElementary[perWeek] || 0;
  if (/^초[56]$/.test(grade)) return FEE_TABLE.upperElementary;
  if (/^중/.test(grade)) return FEE_TABLE.middle;
  if (/^고/.test(grade)) return FEE_TABLE.high;
  return 0;
}
/* 메모에 수업 이름(공필왕 등)이 있으면 그 수업으로 */
function guessProgram(text) {
  return Object.keys(FEE_TABLE.programs).find((name) => String(text || "").includes(name)) || "";
}
/* 메모의 "월, 수, 금" 같은 요일 목록에서 주 수업 횟수 추측 */
function guessPerWeek(text) {
  const m = String(text || "").match(/[월화수목금토일](?:\s*[,，·/]\s*[월화수목금토일])+/);
  return m ? new Set(m[0].match(/[월화수목금토일]/g)).size : 0;
}

/* ---------- 계산 ---------- */
const payKey = (id, month) => `${id}|${month}`;
const isBilled = (s, month) =>
  s.startMonth <= month && (!s.endMonth || month <= s.endMonth) &&
  !(s.breaks || []).some((b) => b.from <= month && month <= b.to);
const isActiveNow = (s) => !s.endMonth || s.endMonth >= toMonth(new Date());

function statusOf(s, month) {
  const pay = state.payments[payKey(s.id, month)];
  const paid = pay ? pay.amount : 0;
  if (!s.fee) return { code: "nofee", label: "교육비 미정", pay, paid };
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
  const all = billedRows(viewMonth);
  const rows = all.filter((r) => r.st.code !== "nofee");
  const noFee = all.length - rows.length;

  // 요약
  const total = rows.reduce((t, r) => t + r.s.fee, 0);
  const paid = rows.reduce((t, r) => t + Math.min(r.st.paid, r.s.fee), 0);
  const done = rows.filter((r) => r.st.code === "paid").length;
  const rate = total ? Math.round((paid / total) * 100) : 0;
  $("#stat-total").textContent = won(total);
  $("#stat-count").textContent = noFee ? `${rows.length}명 · 미정 ${noFee}명` : `${rows.length}명`;
  $("#nofee-notice").hidden = !state.students.some((s) => isActiveNow(s) && !s.fee);
  $("#nofee-count").textContent = `${state.students.filter((s) => isActiveNow(s) && !s.fee).length}명`;
  $("#stat-paid").textContent = won(paid);
  $("#stat-paid-count").textContent = `${done}명 완납`;
  $("#stat-unpaid").textContent = won(total - paid);
  $("#stat-unpaid-count").textContent = `${rows.length - done}명`;
  $("#stat-rate").textContent = `${rate}%`;
  $("#stat-meter").style.width = `${rate}%`;

  // 목록
  const q = query.trim().toLowerCase();
  const visible = all.filter(({ s, st }) => {
    if (filter === "paid" && st.code !== "paid") return false;
    if (filter === "unpaid" && (st.code === "paid" || st.code === "nofee")) return false;
    if (!q) return true;
    return [s.name, s.grade, s.school, s.className, s.phone].some((v) => String(v || "").toLowerCase().includes(q));
  });

  $("#student-list").innerHTML = visible.map(({ s, st }) => {
    const record = st.pay ? `${st.pay.date.slice(5).replace("-", "/")} · ${esc(st.pay.method)} · ${won(st.pay.amount)}` : "";
    const noFee = st.code === "nofee";
    const payLabel = st.code === "paid" ? "수정" : "납부";
    const meta = [s.grade, s.program, s.perWeek ? `주${s.perWeek}회` : "", shortSchool(s.school), s.className, s.memo].filter(Boolean).join(" · ");
    return `
      <li class="student" data-id="${s.id}">
        <div class="s-who">
          <span class="s-name">${esc(s.name)}</span>
          <span class="s-meta">${esc(meta)}</span>
        </div>
        <span class="s-fee${noFee ? " is-empty" : ""}">${noFee ? "미정" : won(s.fee)}</span>
        <span class="s-due">매월 ${s.dueDay}일</span>
        <span class="badge badge-${st.code}">${st.label}</span>
        <span class="s-record">${record}</span>
        <div class="row-actions">
          ${noFee
            ? `<button class="btn btn-primary btn-sm" type="button" data-action="edit">교육비 입력</button>`
            : `<button class="btn btn-sm ${st.code === "paid" ? "btn-ghost" : "btn-pay"}" type="button" data-action="pay">${payLabel}</button>`}
          <button class="btn btn-ghost btn-sm" type="button" data-action="edit">정보</button>
        </div>
      </li>`;
  }).join("");

  const empty = $("#empty");
  empty.hidden = visible.length > 0;
  $("#empty-import").hidden = state.students.length > 0;
  if (!state.students.length) {
    $("#empty-title").textContent = "아직 등록된 학생이 없습니다";
    $("#empty-text").textContent = "\"학생 추가\"를 눌러 첫 학생을 등록하세요. 등록한 달부터 교육비가 청구 목록에 올라옵니다.";
  } else if (!all.length) {
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

/* "두실초등학교" → "두실초" */
function shortSchool(name) {
  if (!name || name === "기타" || name === "-") return "";
  return name.replace(/초등학교$/, "초").replace(/(여자)?중학교$/, (m, f) => (f ? "여중" : "중"))
    .replace(/(여자)?고등학교$/, (m, f) => (f ? "여고" : "고"));
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
  const grade = s?.grade ?? "중1";
  if (!$$("#f-grade option").some((o) => o.value === grade)) $("#f-grade").append(new Option(grade));
  $("#f-grade").value = grade;
  $("#f-school").value = s?.school ?? "";
  $("#f-week").value = String(s?.perWeek || "");
  $("#f-program").value = s?.program || "";
  $("#f-note").value = s?.note ?? "";
  $("#f-class").value = s?.className ?? "";
  $("#f-fee").value = s?.fee ? s.fee.toLocaleString("ko-KR") : "";
  lastAutoFee = feeFor(grade, s?.perWeek, s?.program);
  $("#f-fee").value ||= lastAutoFee ? lastAutoFee.toLocaleString("ko-KR") : "";
  updateFeeHelp();
  $("#f-due").value = String(s?.dueDay ?? 1);
  $("#f-start").value = s?.startMonth ?? viewMonth;
  $("#f-phone").value = s?.phone ?? "";
  $("#f-memo").value = s?.memo ?? "";
  $("#withdraw-student").hidden = !s || !isActiveNow(s);
  $$("#student-form [aria-invalid]").forEach((el) => el.removeAttribute("aria-invalid"));
  $$("#student-form .field-error").forEach((el) => { el.hidden = true; });
  studentDialog.showModal();
  if (s && !s.fee) $("#f-fee").focus();
}

/* 학년이나 주 횟수를 바꾸면, 기준표 금액을 그대로 쓰던 경우에만 교육비를 따라 바꿈 */
let lastAutoFee = 0;
function updateFeeHelp() {
  const grade = $("#f-grade").value;
  const auto = feeFor(grade, Number($("#f-week").value), $("#f-program").value);
  const help = $("#f-fee-help");
  if (auto) help.textContent = `기준표: ${won(auto)}`;
  else if (isLowerElementary(grade) && !$("#f-program").value) help.textContent = "초1~4는 주 수업 횟수(2~5회)를 고르면 기준표 금액이 들어갑니다.";
  else help.textContent = "";
  help.hidden = !help.textContent;
}
function onFeeBasisChange() {
  const current = parseWon($("#f-fee").value);
  const auto = feeFor($("#f-grade").value, Number($("#f-week").value), $("#f-program").value);
  if (!current || current === lastAutoFee) $("#f-fee").value = auto ? auto.toLocaleString("ko-KR") : "";
  lastAutoFee = auto;
  updateFeeHelp();
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
    school: $("#f-school").value.trim(),
    perWeek: Number($("#f-week").value) || 0,
    program: $("#f-program").value,
    className: $("#f-class").value.trim(),
    dueDay: Number($("#f-due").value),
    startMonth: $("#f-start").value || viewMonth,
    phone: $("#f-phone").value.trim(),
    memo: $("#f-memo").value.trim(),
    note: $("#f-note").value.trim(),
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
  const rows = billedRows(viewMonth).filter((r) => r.st.code !== "paid" && r.st.code !== "nofee");
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
  const head = ["이름", "학년", "수업", "주 횟수", "학교", "반", "월 교육비", "받은 금액", "납부일", "납부 방법", "상태", "보호자 연락처", "메모"];
  const body = rows.map(({ s, st }) => [
    s.name, s.grade, s.program || "정규", s.perWeek ? `주${s.perWeek}회` : "", s.school, s.className, s.fee || "", st.paid, st.pay?.date, st.pay?.method,
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

/* ---------- 원생 명단 엑셀 불러오기 ---------- */
// 학원 관리 프로그램에서 내려받은 명단의 열 이름. 앞에 있는 이름을 먼저 찾습니다.
const ROSTER_COLUMNS = {
  id: ["학생ID", "학생 ID", "원생ID"],
  name: ["이름", "학생명", "학생 이름", "원생명"],
  school: ["학교", "학교명"],
  grade: ["학년"],
  className: ["수업반", "반", "클래스"],
  studentPhone: ["학생연락처", "학생 연락처"],
  parentPhone: ["보호자1연락처", "보호자 연락처", "보호자연락처", "학부모 연락처", "학부모연락처"],
  parentPhone2: ["보호자2연락처"],
  enrollDate: ["입학일", "등록일", "입원일"],
  fee: ["교육비", "수강료", "월 교육비"],
  note: ["메모", "비고"],
};
const blank = (v) => {
  const t = String(v ?? "").trim();
  return t === "-" || t === ", " || t === "," ? "" : t;
};
function normDate(v) {
  const m = blank(v).match(/(\d{4})\D+(\d{1,2})\D+(\d{1,2})/);
  return m ? `${m[1]}-${pad(m[2])}-${pad(m[3])}` : "";
}

function rosterFromRows(rows) {
  const headerAt = rows.findIndex((r) => r.some((c) => ROSTER_COLUMNS.id.concat(ROSTER_COLUMNS.name).includes(blank(c))));
  if (headerAt < 0) throw new Error("학생ID 또는 이름 열을 찾지 못했습니다");
  const header = rows[headerAt].map(blank);
  const col = {};
  Object.entries(ROSTER_COLUMNS).forEach(([key, names]) => {
    col[key] = names.map((n) => header.indexOf(n)).find((i) => i >= 0) ?? -1;
  });
  const get = (r, key) => (col[key] >= 0 ? blank(r[col[key]]) : "");

  return rows.slice(headerAt + 1).map((r) => {
    const sourceId = get(r, "id");
    // 학생ID 는 "김찬호0" 처럼 이름 뒤에 동명이인 구분 숫자가 붙어 있음
    const name = get(r, "name") || sourceId.replace(/\d+$/, "");
    if (!name) return null;
    const cls = get(r, "className");
    const grade = get(r, "grade") || "기타";
    const perWeek = guessPerWeek(`${get(r, "note")} ${cls}`);
    const program = guessProgram(`${get(r, "note")} ${cls}`);
    return {
      sourceId: sourceId || name,
      name,
      school: get(r, "school"),
      grade, perWeek, program,
      className: cls.length <= 12 ? cls : "",
      phone: get(r, "parentPhone") || get(r, "studentPhone") || get(r, "parentPhone2"),
      enrollDate: normDate(get(r, "enrollDate")),
      fee: parseWon(get(r, "fee")) || feeFor(grade, perWeek, program),
      note: [get(r, "note"), cls.length > 12 ? `수업반: ${cls}` : ""].filter(Boolean).join("\n"),
    };
  }).filter(Boolean);
}

async function importRoster(file) {
  let roster;
  try {
    roster = rosterFromRows(await readTable(file));
  } catch (err) {
    toast(`명단을 읽지 못했습니다: ${err.message}`);
    return;
  }
  if (!roster.length) { toast("명단에 학생이 없습니다"); return; }

  const thisMonth = toMonth(new Date());
  const bySource = new Map(state.students.filter((s) => s.sourceId).map((s) => [s.sourceId, s]));
  const fresh = roster.filter((r) => !bySource.has(r.sourceId));
  const known = roster.length - fresh.length;
  const withFee = fresh.filter((r) => r.fee).length;
  const noFee = fresh.length - withFee;

  const msg = [
    `명단에서 학생 ${roster.length}명을 찾았습니다.`,
    fresh.length ? `· 새로 추가: ${fresh.length}명 (${monthText(thisMonth)}부터 청구)` : "",
    known ? `· 이미 있는 학생 ${known}명: 학교, 학년, 연락처만 새로 고침 (교육비와 납부 기록은 그대로)` : "",
    withFee ? `· 교육비 기준표대로 ${withFee}명의 교육비를 넣습니다.` : "",
    noFee ? `· ${noFee}명은 주 수업 횟수를 몰라 "교육비 미정"으로 들어갑니다. 다음 화면에서 고를 수 있습니다.` : "",
  ].filter(Boolean).join("\n") + "\n\n불러올까요?";
  if (!confirm(msg)) return;

  roster.forEach((r) => {
    const existing = bySource.get(r.sourceId);
    if (existing) {
      Object.assign(existing, {
        name: r.name, school: r.school, grade: r.grade, enrollDate: r.enrollDate,
        phone: r.phone || existing.phone,
        className: existing.className || r.className,
        note: existing.note || r.note,
        perWeek: existing.perWeek || r.perWeek,
        program: existing.program || r.program,
        fee: existing.fee || feeFor(r.grade, existing.perWeek || r.perWeek, existing.program || r.program) || r.fee,
      });
      return;
    }
    // 입학일이 지난 학생도 청구는 이번 달부터 (이전 달이 모두 미납으로 보이지 않도록)
    const enrollMonth = r.enrollDate.slice(0, 7);
    state.students.push({
      id: newId(), endMonth: null, memo: "", ...r,
      startMonth: enrollMonth > thisMonth ? enrollMonth : thisMonth,
      dueDay: r.enrollDate ? Number(r.enrollDate.slice(8, 10)) : 1,
    });
  });
  save();
  viewMonth = thisMonth;
  render();
  toast(`학생 ${roster.length}명을 불러왔습니다`);
  if (state.students.some((s) => isActiveNow(s) && !s.fee)) openBulkFee();
}

/* ---------- 교육비 채우기 (기준표) ---------- */
const GRADE_ORDER = ["초1", "초2", "초3", "초4", "초5", "초6", "중1", "중2", "중3", "고1", "고2", "고3"];
const gradeRank = (g) => (GRADE_ORDER.includes(g) ? GRADE_ORDER.indexOf(g) : 99);
const missingFee = () => state.students.filter((s) => isActiveNow(s) && !s.fee);

function openBulkFee() {
  const missing = missingFee();
  if (!missing.length) { toast("교육비가 비어 있는 학생이 없습니다"); return; }
  const auto = missing.filter((s) => feeFor(s.grade, s.perWeek, s.program));
  const ask = missing.filter((s) => isLowerElementary(s.grade) && !feeFor(s.grade, s.perWeek, s.program))
    .sort((a, b) => gradeRank(a.grade) - gradeRank(b.grade) || a.name.localeCompare(b.name, "ko"));
  const other = missing.length - auto.length - ask.length;
  const t = FEE_TABLE.lowerElementary;

  const programs = Object.entries(FEE_TABLE.programs);
  const programText = programs.length ? ` / ${programs.map(([n]) => n).join(", ")} ${won(programs[0][1])}` : "";
  $("#fee-table").textContent = `초1~4 주2회 ${won(t[2])} · 주3회 ${won(t[3])} · 주4회 ${won(t[4])} · 주5회 ${won(t[5])} / 초5~6 ${won(FEE_TABLE.upperElementary)} / 중등 ${won(FEE_TABLE.middle)} / 고등 ${won(FEE_TABLE.high)}${programText}`;
  $("#fee-summary").textContent = [
    auto.length ? `${auto.length}명은 학년에 맞춰 바로 들어갑니다.` : "",
    ask.length ? `아래 초1~4 학생 ${ask.length}명은 주 몇 회인지, 또는 어떤 수업인지 골라 주세요.` : "",
    other ? `학년이 "기타"인 ${other}명은 목록에서 직접 넣어 주세요.` : "",
  ].filter(Boolean).join(" ");
  $("#fee-rows").innerHTML = ask.map((s) => `
    <div class="fee-row">
      <label for="week-${s.id}">${esc(s.name)} <span>${esc([s.grade, shortSchool(s.school)].filter(Boolean).join(" · "))}${s.perWeek ? ` · 메모상 주${s.perWeek}회` : ""}</span></label>
      <select id="week-${s.id}" data-id="${s.id}">
        <option value="">모름 (미정)</option>
        ${[2, 3, 4, 5].map((n) => `<option value="${n}">주${n}회 · ${won(t[n])}</option>`).join("")}
        ${programs.map(([n, fee]) => `<option value="p:${esc(n)}">${esc(n)} · ${won(fee)}</option>`).join("")}
      </select>
    </div>`).join("");
  $("#fee-dialog").showModal();
  ($("#fee-rows select") || $("#fee-form [type=submit]")).focus();
}

$("#fee-form").addEventListener("submit", (e) => {
  e.preventDefault();
  $$("#fee-rows select").forEach((sel) => {
    const s = state.students.find((x) => x.id === sel.dataset.id);
    if (!s || !sel.value) return;
    if (sel.value.startsWith("p:")) s.program = sel.value.slice(2);
    else s.perWeek = Number(sel.value);
  });
  let changed = 0;
  missingFee().forEach((s) => {
    const fee = feeFor(s.grade, s.perWeek, s.program);
    if (fee) { s.fee = fee; changed++; }
  });
  save();
  $("#fee-dialog").close();
  render();
  toast(changed ? `${changed}명의 교육비를 넣었습니다` : "바뀐 내용이 없습니다");
});

/* ---------- 이벤트 연결 ---------- */
function init() {
  $("#f-due").innerHTML = Array.from({ length: 31 }, (_, i) => `<option value="${i + 1}">매월 ${i + 1}일</option>`).join("");
  formatMoneyInput($("#f-fee"));
  $("#f-grade").addEventListener("change", onFeeBasisChange);
  $("#f-week").addEventListener("change", onFeeBasisChange);
  $("#f-program").innerHTML = `<option value="">정규 수업 (학년·횟수 기준)</option>` +
    Object.entries(FEE_TABLE.programs).map(([n, fee]) => `<option value="${esc(n)}">${esc(n)} · ${won(fee)}</option>`).join("");
  $("#f-program").addEventListener("change", onFeeBasisChange);
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
  $("#open-bulk-fee").addEventListener("click", openBulkFee);
  $$("[data-import-roster]").forEach((input) => input.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) importRoster(file);
    e.target.value = "";
  }));
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
