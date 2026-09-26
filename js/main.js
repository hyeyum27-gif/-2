/*
  해냄수학전문학원 사이트 동작
  ------------------------------------------------------------
  [수정하기 쉬운 곳]
  1) ACADEMY_PHONE : 학원 전화번호 (문자 상담, 전화 버튼에 쓰임)
  2) SCHEDULE      : 학년별 시간표 [예시]. 여기만 바꾸면
                     첫 화면 "오늘의 수업" 카드와 시간표 탭이 함께 바뀝니다.
  ------------------------------------------------------------
*/

const ACADEMY_PHONE = "051-000-0000"; // [예시] 실제 번호로 바꿔 주세요

// days: 0=일, 1=월, 2=화, 3=수, 4=목, 5=금, 6=토
const SCHEDULE = {
  elem: {
    note: "초등부는 숙제 확인과 연산 연습을 수업 안에서 마칩니다.",
    classes: [
      { name: "초5 기초반", target: "교과 개념, 연산", times: [{ days: [1, 3], start: "15:30", end: "17:00" }] },
      { name: "초6 심화반", target: "교과 심화, 중1 준비", times: [{ days: [2, 4], start: "15:30", end: "17:30" }] },
    ],
  },
  middle: {
    note: "시험 4주 전부터 학교별 내신 대비반으로 바뀝니다.",
    classes: [
      { name: "중1", target: "중1 교과, 서술형", times: [{ days: [2, 4], start: "17:30", end: "19:30" }, { days: [6], start: "10:00", end: "12:00" }] },
      { name: "중2", target: "중2 교과, 함수 집중", times: [{ days: [1, 3, 5], start: "17:30", end: "19:30" }] },
      { name: "중3", target: "중3 교과, 고등 선행", times: [{ days: [1, 3, 5], start: "19:40", end: "21:40" }] },
    ],
  },
  high: {
    note: "고등부는 수업 후 30분 질문 시간이 있습니다.",
    classes: [
      { name: "고1", target: "공통수학 1, 2", times: [{ days: [2, 4], start: "19:40", end: "22:00" }, { days: [6], start: "13:00", end: "16:00" }] },
      { name: "고2", target: "수학 I, II, 미적분", times: [{ days: [1, 3, 5], start: "19:00", end: "22:00" }] },
      { name: "고3", target: "수능, 내신 개별 관리", times: [{ days: [2, 4, 6], start: "18:00", end: "22:00" }] },
    ],
  },
};

const GRADE_LABEL = { elem: "초등부", middle: "중등부", high: "고등부" };
const DAY_NAMES = ["일", "월", "화", "수", "목", "금", "토"];

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

/* 전화번호를 페이지 곳곳에 반영 */
function applyPhone() {
  const digits = ACADEMY_PHONE.replace(/\D/g, "");
  $$("[data-phone-link]").forEach((a) => { a.href = `tel:${digits}`; });
  $$("[data-phone-text]").forEach((s) => { s.textContent = ACADEMY_PHONE; });
}

/* 모바일 메뉴 */
function setupNav() {
  const toggle = $(".nav-toggle");
  const list = $("#nav-list");
  if (!toggle || !list) return;
  const setOpen = (open) => {
    list.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", String(open));
    toggle.querySelector(".ph").className = open ? "ph ph-x" : "ph ph-list";
    toggle.querySelector(".sr-only").textContent = open ? "메뉴 닫기" : "메뉴 열기";
  };
  toggle.addEventListener("click", () => setOpen(!list.classList.contains("is-open")));
  list.addEventListener("click", (e) => { if (e.target.closest("a")) setOpen(false); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") setOpen(false); });
}

/* 시간표 탭 */
function renderPanels() {
  Object.entries(SCHEDULE).forEach(([key, grade]) => {
    const panel = $(`[data-panel="${key}"]`);
    if (!panel) return;
    const grid = el("div", "class-grid");
    grade.classes.forEach((c) => {
      const card = el("article", "class-card");
      card.append(el("h3", "", c.name), el("p", "class-target", c.target));
      const list = el("ul", "class-times");
      c.times.forEach((t) => {
        const li = el("li");
        li.append(
          el("span", "class-days", t.days.map((d) => DAY_NAMES[d]).join(" ")),
          el("span", "class-hours", `${t.start} ~ ${t.end}`)
        );
        list.append(li);
      });
      card.append(list);
      grid.append(card);
    });
    panel.replaceChildren(grid, el("p", "panel-note", grade.note));
  });
}

function setupTabs() {
  const tabs = $$('[role="tab"]');
  const select = (tab) => {
    tabs.forEach((t) => {
      const on = t === tab;
      t.setAttribute("aria-selected", String(on));
      t.tabIndex = on ? 0 : -1;
      document.getElementById(t.getAttribute("aria-controls")).hidden = !on;
    });
  };
  tabs.forEach((tab, i) => {
    tab.addEventListener("click", () => select(tab));
    tab.addEventListener("keydown", (e) => {
      let next = null;
      if (e.key === "ArrowRight") next = tabs[(i + 1) % tabs.length];
      if (e.key === "ArrowLeft") next = tabs[(i - 1 + tabs.length) % tabs.length];
      if (e.key === "Home") next = tabs[0];
      if (e.key === "End") next = tabs[tabs.length - 1];
      if (next) { e.preventDefault(); select(next); next.focus(); }
    });
  });
}

/* 첫 화면 "오늘의 수업" 카드 */
function classesOn(day) {
  const rows = [];
  Object.entries(SCHEDULE).forEach(([key, grade]) => {
    grade.classes.forEach((c) => {
      c.times.forEach((t) => {
        if (t.days.includes(day)) rows.push({ grade: GRADE_LABEL[key], name: c.name, start: t.start, end: t.end });
      });
    });
  });
  return rows.sort((a, b) => a.start.localeCompare(b.start));
}

function renderToday(now = new Date()) {
  const list = $("[data-today-list]");
  const label = $("[data-today-label]");
  if (!list || !label) return;

  let day = now.getDay();
  let rows = classesOn(day);
  let title = `오늘(${DAY_NAMES[day]}) 수업`;

  if (rows.length === 0) {
    // 수업이 없는 날은 다음 수업일을 보여 줍니다
    for (let i = 1; i <= 7; i++) {
      const d = (day + i) % 7;
      const r = classesOn(d);
      if (r.length) { rows = r; title = `오늘은 쉬는 날, ${DAY_NAMES[d]}요일 수업`; break; }
    }
  }
  label.textContent = title;

  if (rows.length === 0) {
    list.replaceChildren(el("li", "today-empty", "등록된 수업이 없습니다. 시간표를 확인해 주세요."));
    return;
  }
  const shown = rows.slice(0, 4);
  list.replaceChildren(
    ...shown.map((r) => {
      const li = el("li");
      li.append(el("span", "today-time", `${r.start} ~ ${r.end}`), el("span", "today-class", `${r.grade} ${r.name}`));
      return li;
    })
  );
  if (rows.length > shown.length) {
    list.append(el("li", "today-empty", `외 ${rows.length - shown.length}개 수업`));
  }
}

/* 상담 신청 폼: 확인 후 문자 앱으로 내용을 보냅니다 (서버 없음) */
function setupForm() {
  const form = $("[data-consult-form]");
  if (!form) return;
  const result = $("[data-form-result]", form);
  const message = $("[data-result-message]", form);
  const smsLink = $("[data-sms-link]", form);
  const copyBtn = $("[data-copy]", form);

  const checks = {
    name: (v) => v.trim().length >= 2,
    grade: (v) => v !== "",
    phone: (v) => /^01[016789]-?\d{3,4}-?\d{4}$/.test(v.trim()),
  };

  const showError = (field, bad) => {
    const input = form.elements[field];
    const err = document.getElementById(`f-${field}-err`);
    input.setAttribute("aria-invalid", String(bad));
    err.hidden = !bad;
  };

  Object.keys(checks).forEach((field) => {
    const input = form.elements[field];
    const evt = input.tagName === "SELECT" ? "change" : "blur";
    input.addEventListener(evt, () => { if (input.value) showError(field, !checks[field](input.value)); });
    input.addEventListener("input", () => {
      if (input.getAttribute("aria-invalid") === "true" && checks[field](input.value)) showError(field, false);
    });
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    let firstBad = null;
    Object.keys(checks).forEach((field) => {
      const bad = !checks[field](form.elements[field].value);
      showError(field, bad);
      if (bad && !firstBad) firstBad = form.elements[field];
    });
    if (firstBad) { result.hidden = true; firstBad.focus(); return; }

    const d = Object.fromEntries(new FormData(form));
    const text = [
      "[해냄수학 상담 신청]",
      `학생: ${d.name.trim()} (${d.grade})`,
      `연락처: ${d.phone.trim()}`,
      d.memo && d.memo.trim() ? `문의: ${d.memo.trim()}` : null,
    ].filter(Boolean).join("\n");

    const digits = ACADEMY_PHONE.replace(/\D/g, "");
    const sep = /iPhone|iPad|iPod/.test(navigator.userAgent) ? "&" : "?";
    smsLink.href = `sms:${digits}${sep}body=${encodeURIComponent(text)}`;
    message.textContent = text;
    result.hidden = false;
    result.focus();

    // 휴대폰에서는 바로 문자 앱을 엽니다
    if (window.matchMedia("(pointer: coarse)").matches) window.location.href = smsLink.href;
  });

  copyBtn.addEventListener("click", async () => {
    const original = copyBtn.innerHTML;
    try {
      await navigator.clipboard.writeText(message.textContent);
      copyBtn.textContent = "복사했습니다";
    } catch {
      copyBtn.textContent = "복사하지 못했습니다. 직접 선택해 주세요";
    }
    setTimeout(() => { copyBtn.innerHTML = original; }, 2000);
  });
}

/* 스크롤하면 부드럽게 나타나기 */
function setupReveal() {
  const items = $$(".reveal");
  if (!("IntersectionObserver" in window)) { items.forEach((i) => i.classList.add("is-visible")); return; }
  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) { entry.target.classList.add("is-visible"); io.unobserve(entry.target); }
    });
  }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
  items.forEach((i) => io.observe(i));
}

applyPhone();
setupNav();
renderPanels();
setupTabs();
renderToday();
setupForm();
setupReveal();
