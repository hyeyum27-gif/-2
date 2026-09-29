/*
  엑셀(.xlsx)과 CSV 파일을 표(2차원 배열)로 읽는 작은 도구
  - 외부 라이브러리 없이 브라우저 안에서만 읽습니다. 파일은 어디로도 전송되지 않습니다.
  - 첫 번째 시트만 읽고, 날짜 칸이 엑셀 날짜 숫자면 "2026-09-14" 형태로 바꿉니다.
  사용: const rows = await readTable(file);  // [["학생ID", "학교", ...], [...], ...]
*/

async function readTable(file) {
  const buf = new Uint8Array(await file.arrayBuffer());
  const isZip = buf[0] === 0x50 && buf[1] === 0x4b; // "PK"
  if (isZip) return readXlsx(buf);
  return parseCsv(new TextDecoder("utf-8").decode(buf).replace(/^﻿/, ""));
}

/* ---------- zip ---------- */
async function unzip(buf) {
  const view = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
  let eocd = -1;
  for (let i = buf.length - 22; i >= Math.max(0, buf.length - 65557); i--) {
    if (view.getUint32(i, true) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd < 0) throw new Error("zip 형식이 아닙니다");
  const count = view.getUint16(eocd + 10, true);
  let p = view.getUint32(eocd + 16, true);
  const files = {};
  const utf8 = new TextDecoder("utf-8");
  for (let n = 0; n < count; n++) {
    if (view.getUint32(p, true) !== 0x02014b50) break;
    const method = view.getUint16(p + 10, true);
    const size = view.getUint32(p + 20, true);
    const nameLen = view.getUint16(p + 28, true);
    const extraLen = view.getUint16(p + 30, true);
    const commentLen = view.getUint16(p + 32, true);
    const local = view.getUint32(p + 42, true);
    const name = utf8.decode(buf.subarray(p + 46, p + 46 + nameLen));
    const start = local + 30 + view.getUint16(local + 26, true) + view.getUint16(local + 28, true);
    files[name] = { method, data: buf.subarray(start, start + size) };
    p += 46 + nameLen + extraLen + commentLen;
  }
  return async (name) => {
    const f = files[name];
    if (!f) return null;
    if (f.method === 0) return utf8.decode(f.data);
    if (f.method === 8) {
      const stream = new Blob([f.data]).stream().pipeThrough(new DecompressionStream("deflate-raw"));
      return new Response(stream).text();
    }
    throw new Error("지원하지 않는 압축 방식입니다");
  };
}

/* ---------- xlsx ---------- */
const xml = (text) => new DOMParser().parseFromString(text, "application/xml");
const tags = (node, name) => Array.from(node.getElementsByTagNameNS("*", name));
const textOf = (node) => tags(node, "t").map((t) => t.textContent).join("");

function colIndex(ref) {
  let n = 0;
  for (const ch of ref.replace(/\d+/g, "")) n = n * 26 + (ch.charCodeAt(0) - 64);
  return n - 1;
}

/* 엑셀 날짜 숫자 → "YYYY-MM-DD" */
function excelDate(serial) {
  const d = new Date(Math.round((serial - 25569) * 86400000));
  return d.toISOString().slice(0, 10);
}

async function readXlsx(buf) {
  const read = await unzip(buf);

  // 첫 번째 시트 파일 경로 찾기
  let sheetPath = "xl/worksheets/sheet1.xml";
  const wb = await read("xl/workbook.xml");
  const rels = await read("xl/_rels/workbook.xml.rels");
  if (wb && rels) {
    const first = tags(xml(wb), "sheet")[0];
    const rid = first && (first.getAttribute("r:id") || first.getAttributeNS("http://schemas.openxmlformats.org/officeDocument/2006/relationships", "id"));
    const rel = tags(xml(rels), "Relationship").find((r) => r.getAttribute("Id") === rid);
    if (rel) {
      const target = rel.getAttribute("Target");
      sheetPath = target.startsWith("/") ? target.slice(1) : `xl/${target.replace(/^\.\//, "")}`;
    }
  }
  const sheet = await read(sheetPath);
  if (!sheet) throw new Error("시트를 찾지 못했습니다");

  const sst = await read("xl/sharedStrings.xml");
  const shared = sst ? tags(xml(sst), "si").map(textOf) : [];

  // 날짜 서식이 걸린 칸 번호 (엑셀에서 다시 저장한 파일 대비)
  const dateStyles = new Set();
  const stylesXml = await read("xl/styles.xml");
  if (stylesXml) {
    const doc = xml(stylesXml);
    const customDate = new Set(tags(doc, "numFmt")
      .filter((f) => /[yd]/i.test(f.getAttribute("formatCode").replace(/"[^"]*"|\[[^\]]*\]/g, "")))
      .map((f) => f.getAttribute("numFmtId")));
    const cellXfs = tags(doc, "cellXfs")[0];
    if (cellXfs) {
      Array.from(cellXfs.children).forEach((xf, i) => {
        const id = Number(xf.getAttribute("numFmtId"));
        if ((id >= 14 && id <= 22) || (id >= 45 && id <= 47) || customDate.has(String(id))) dateStyles.add(String(i));
      });
    }
  }

  const rows = [];
  tags(xml(sheet), "row").forEach((row) => {
    const r = Number(row.getAttribute("r")) - 1;
    const out = [];
    tags(row, "c").forEach((c, i) => {
      const ref = c.getAttribute("r");
      const col = ref ? colIndex(ref) : i;
      const type = c.getAttribute("t");
      const v = tags(c, "v")[0]?.textContent ?? "";
      let value;
      if (type === "s") value = shared[Number(v)] ?? "";
      else if (type === "inlineStr") value = textOf(c);
      else if (type === "b") value = v === "1" ? "TRUE" : "FALSE";
      else if (type === "str" || type === "e") value = v;
      else if (v !== "" && dateStyles.has(c.getAttribute("s"))) value = excelDate(Number(v));
      else value = v;
      out[col] = value;
    });
    rows[Number.isNaN(r) ? rows.length : r] = Array.from(out, (x) => x ?? "");
  });
  return rows.filter(Boolean);
}

/* ---------- csv ---------- */
function parseCsv(text) {
  const rows = [];
  let row = [], cell = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') { cell += '"'; i++; }
      else if (ch === '"') quoted = false;
      else cell += ch;
    } else if (ch === '"') quoted = true;
    else if (ch === ",") { row.push(cell); cell = ""; }
    else if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && text[i + 1] === "\n") i++;
      row.push(cell); rows.push(row); row = []; cell = "";
    } else cell += ch;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  return rows;
}
