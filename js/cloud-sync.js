/*
  온라인 저장 — Claude 페이지(아티팩트) 안에서 열었을 때만 동작합니다.
  ------------------------------------------------------------
  기록을 그 페이지 전용 저장소(db)에 보관해서 휴대폰, 컴퓨터 어디서 열어도 같은 기록이 보이고
  브라우저를 정리해도 남습니다. 일반 웹사이트에서 열면(window.claude 없음) 아무것도 하지 않고
  지금처럼 이 기기 브라우저에만 저장합니다.

  저장소 구성 (컬렉션 "tuition"):
    students        { list: [학생, ...] }
    settings        { settings: { smsTemplate, ... } }
    m-2026-09       { payments: {학생id: ...}, adjustments: {...}, reminders: {...} }  // 달마다 하나
*/
(function () {
  if (!window.claude?.use) return;

  const COLLECTION = "tuition";
  const LOCAL_BACKUP_KEY = STORAGE_KEY + "-before-online";
  const KINDS = ["payments", "adjustments", "reminders"];
  const emptyMonth = () => ({ payments: {}, adjustments: {}, reminders: {} });
  const clone = (v) => JSON.parse(JSON.stringify(v));

  let db = null;
  let ready = false;          // 서버의 첫 확정 스냅샷을 받았는지
  let writing = false;
  let failed = false;
  const lastJson = {};        // 문서별로 서버와 맞춰진 내용
  const queue = new Map();    // 보낼 문서 (문서마다 가장 최근 내용만)

  /* ---------- 상태 표시 ---------- */
  const statusEl = document.getElementById("sync-status");
  function setStatus(kind) {
    if (!statusEl) return;
    const text = {
      connecting: "온라인 저장소에 연결하는 중…",
      saving: "온라인에 저장하는 중…",
      saved: "온라인에 저장됨 · 휴대폰, 컴퓨터 어디서 열어도 같은 기록이 보입니다",
      example: "예시 데이터는 온라인에 저장되지 않습니다. 예시를 지우거나 명단을 불러오면 저장이 시작됩니다",
      error: "온라인 저장이 되지 않았습니다. 이 기기에는 남아 있으니 잠시 뒤 다시 열어 보거나 백업 파일을 저장해 두세요",
      offline: "온라인 저장소를 쓸 수 없는 화면입니다. 이 기기에만 저장됩니다",
    }[kind];
    statusEl.textContent = text;
    statusEl.dataset.kind = kind;
    statusEl.hidden = false;
  }

  /* ---------- 상태 ↔ 문서 ---------- */
  function toDocs(st) {
    const docs = {
      students: { list: st.students },
      settings: { settings: st.settings || {} },
    };
    KINDS.forEach((kind) => {
      Object.entries(st[kind] || {}).forEach(([key, value]) => {
        const cut = key.lastIndexOf("|");
        const id = key.slice(0, cut);
        const month = key.slice(cut + 1);
        (docs[`m-${month}`] ||= emptyMonth())[kind][id] = value;
      });
    });
    return docs;
  }

  function fromDocs(snapDocs) {
    const st = emptyState();
    snapDocs.forEach((d) => {
      const body = d.exists ? clone(d.data()) : null;
      if (!body) return;
      if (d.id === "students") st.students = (body.list || []).map(normalizeStudent);
      else if (d.id === "settings") st.settings = body.settings || {};
      else if (d.id.startsWith("m-")) {
        const month = d.id.slice(2);
        KINDS.forEach((kind) => {
          Object.entries(body[kind] || {}).forEach(([id, value]) => { st[kind][`${id}|${month}`] = value; });
        });
      }
    });
    return st;
  }

  /* ---------- 보내기 ---------- */
  function push() {
    if (!db || !ready) return;
    if (state.example) { setStatus("example"); return; }
    const docs = toDocs(state);
    // 기록이 모두 지워진 달은 빈 문서로 덮어씀
    Object.keys(lastJson).forEach((id) => { if (id.startsWith("m-") && !docs[id]) docs[id] = emptyMonth(); });
    Object.entries(docs).forEach(([id, body]) => {
      const json = JSON.stringify(body);
      if (lastJson[id] !== json) { lastJson[id] = json; queue.set(id, clone(body)); }
    });
    drain();
  }

  async function writeDoc(id, body) {
    try { await db.collection(COLLECTION).doc(id).set(body); }
    catch (e) {
      if (e?.code !== "unavailable") throw e;
      await new Promise((r) => setTimeout(r, 600 + Math.random() * 900));
      await db.collection(COLLECTION).doc(id).set(body);
    }
  }

  async function drain() {
    if (writing || !queue.size) { if (!writing && !failed) setStatus("saved"); return; }
    writing = true;
    failed = false;
    setStatus("saving");
    while (queue.size) {
      const [id, body] = queue.entries().next().value;
      queue.delete(id);
      try { await writeDoc(id, body); }
      catch (e) {
        failed = true;
        delete lastJson[id]; // 다음 저장 때 다시 보냄
        if (e?.code === "quota_exceeded") toast("온라인 저장 공간이 가득 찼습니다. 오래된 퇴원생 기록을 지워 주세요.");
      }
    }
    writing = false;
    setStatus(failed ? "error" : "saved");
  }

  /* ---------- 받기 ---------- */
  function applyServer(snap) {
    snap.docs.forEach((d) => { if (d.exists) lastJson[d.id] = JSON.stringify(d.data()); });
    if (writing || queue.size) return; // 내 저장이 끝난 뒤의 스냅샷으로 맞춤
    if (snap.empty) return;            // 빈 저장소가 이 기기 기록(예시 포함)을 지우지 않게
    const next = fromDocs(snap.docs);
    if (JSON.stringify(toDocs(next)) === JSON.stringify(toDocs(state))) return;
    state = next;
    saveLocal();
    render();
  }

  function onFirstSnapshot(snap) {
    ready = true;
    if (snap.empty) {
      // 온라인 저장소가 비어 있음: 이 기기에 실제 기록이 있으면 올림
      if (!state.example && state.students.length) {
        push();
        toast("이 기기의 기록을 온라인 저장소로 옮겼습니다");
      } else setStatus(state.example ? "example" : "saved");
      return;
    }
    // 온라인 기록이 우선. 이 기기에 다른 실제 기록이 있었다면 따로 보관해 둠
    const local = toDocs(state);
    const server = toDocs(fromDocs(snap.docs));
    if (!state.example && state.students.length && JSON.stringify(local) !== JSON.stringify(server)) {
      try { localStorage.setItem(LOCAL_BACKUP_KEY, JSON.stringify(state)); } catch { /* 보관 실패는 무시 */ }
    }
    applyServer(snap);
    setStatus("saved");
  }

  async function start() {
    setStatus("connecting");
    db = await window.claude.use("db");
    if (!db) { setStatus("offline"); return; }
    afterSave = push;
    db.collection(COLLECTION).onSnapshot((snap) => {
      if (!ready) {
        if (snap.metadata.fromCache) return; // 서버가 확정한 첫 상태를 기다림
        onFirstSnapshot(snap);
        return;
      }
      applyServer(snap);
    }, () => {
      afterSave = null;
      setStatus("error");
    });
  }

  window.addEventListener("beforeunload", (e) => {
    if (writing || queue.size) { e.preventDefault(); e.returnValue = ""; }
  });

  start();
})();
