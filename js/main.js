/*
  해냄수학전문학원 사이트 동작
  ------------------------------------------------------------
  ACADEMY_PHONE : 학원 전화번호 (문자 상담, 전화 버튼에 쓰임)
  ------------------------------------------------------------
*/

const ACADEMY_PHONE = "010-2754-1939";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

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
setupForm();
setupReveal();
