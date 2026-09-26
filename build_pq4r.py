"""PQ4R 학습노트(편집 가능한 Word DOCX, A4 세로 5쪽) 생성기.

사용법:
    python3 build_pq4r.py units/elastic_force.py

소단원 내용은 units/*.py 파일에만 적는다. 이 파일의 디자인은 특별한 요청이 없으면 수정하지 않는다.
- 간격·표 구성·글자 크기: 사용자 양식 파일(PQ4R 통합과학2 1-1-1, 1-1-2 학생용/교사용)의 실측값 (SPACING.md)
- 그림(배경 틀·구름 제목·과학 배지): 참고 PDF 「힘의 표현」 디자인, make_assets.py 가 만든 assets/ 파일
- 글꼴: Gaegu (보통·굵게 서브셋을 DOCX에 내장)
"""
import copy
import importlib.util
import os
import re
import sys
import uuid
import zipfile

from docx import Document
from docx.enum.table import WD_ROW_HEIGHT_RULE, WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")
FONT = "Gaegu"
FONT_FILES = {"Regular": os.path.join(ASSETS, "Gaegu-KR-Regular.ttf"),
              "Bold": os.path.join(ASSETS, "Gaegu-KR-Bold.ttf")}

# 단계별 색상 (진한 색 / 연한 배경) — 사용자 양식 파일과 같은 값
P_C, P_PALE = "138BC6", "DCEFF7"      # Preview 파랑
Q_C, Q_PALE = "FF9F28", "FFF1D9"      # Question 주황
R1_C, R1_PALE = "65B33F", "EDF7DF"    # Read 초록
R2_C, R2_PALE = "FF8A68", "FFE2D8"    # Reflect 코랄
R3_C, R3_PALE = "72269E", "F3E6FA"    # Recite 보라
R4_C, R4_PALE = "2BA89E", "DDF6F3"    # Review 청록
TEXT_C, REVIEW_TEXT_C = "222222", "234C48"

# 쪽 여백·본문 폭 (양식 파일 실측: 위아래 9mm, 좌우 14mm, 본문 182mm)
LEFT = RIGHT = 14
TOP = BOTTOM = 9
PAGE_W = 210 - LEFT - RIGHT  # 182mm
CELL_PAD = 1.9               # 칸 안쪽 여백(상하좌우)
LINE = 1.05                  # 칸 안 줄 간격(252/240)
GAP_S, GAP_L = 3.0, 4.0      # 표 사이 간격: 제목줄→띠 3mm, 띠→표·표→띠 4mm (Review 띠→표 3mm)

doc = Document()


# ---------------------------------------------------------------- 기본 함수
def shading(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def border(cell, color="000000", size=11, sides=("top", "left", "bottom", "right")):
    tcPr = cell._tc.get_or_add_tcPr()
    old = tcPr.find(qn("w:tcBorders"))
    if old is not None:
        tcPr.remove(old)
    b = OxmlElement("w:tcBorders")
    tcPr.append(b)
    for s in ("top", "left", "bottom", "right"):
        e = OxmlElement(f"w:{s}")
        if s in sides:
            e.set(qn("w:val"), "single")
            e.set(qn("w:sz"), str(size))
            e.set(qn("w:color"), color)
        else:
            e.set(qn("w:val"), "nil")
        b.append(e)


def margins(cell, pad=CELL_PAD):
    tcPr = cell._tc.get_or_add_tcPr()
    old = tcPr.find(qn("w:tcMar"))
    if old is not None:
        tcPr.remove(old)
    m = OxmlElement("w:tcMar")
    for k in ("top", "left", "bottom", "right"):
        e = OxmlElement(f"w:{k}")
        e.set(qn("w:w"), str(int(pad * 56.7)))
        e.set(qn("w:type"), "dxa")
        m.append(e)
    tcPr.append(m)


def _font(run, size, bold, color):
    run.font.name = FONT
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def _para(p, align, spacing=LINE):
    p.alignment = {"left": WD_ALIGN_PARAGRAPH.LEFT, "center": WD_ALIGN_PARAGRAPH.CENTER,
                   "right": WD_ALIGN_PARAGRAPH.RIGHT}[align]
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing = spacing


def write(cell, text, size=11.5, bold=False, color=TEXT_C, align="left",
          valign="center", spacing=LINE):
    """셀 내용을 text로 교체한다. 줄바꿈(\\n)은 문단으로, **굵게** 구간은 굵은 글씨로 쓴다."""
    cell.vertical_alignment = {"top": WD_CELL_VERTICAL_ALIGNMENT.TOP,
                               "center": WD_CELL_VERTICAL_ALIGNMENT.CENTER}[valign]
    p = cell.paragraphs[0]
    for i, line in enumerate(text.split("\n")):
        if i:
            p = cell.add_paragraph()
        _para(p, align, spacing)
        for j, part in enumerate(line.split("**")):
            if part:
                _font(p.add_run(part), size, bold or j % 2 == 1, color)
    return p


def picture(cell, path, mm, align="center"):
    p = cell.paragraphs[0]
    _para(p, align, 1.0)
    p.add_run().add_picture(path, width=Mm(mm))


def width(cell, mm):
    cell.width = Mm(mm)
    tcPr = cell._tc.get_or_add_tcPr()
    w = tcPr.find(qn("w:tcW"))
    if w is None:
        w = OxmlElement("w:tcW")
        tcPr.insert(0, w)
    w.set(qn("w:w"), str(int(mm * 56.7)))
    w.set(qn("w:type"), "dxa")


def table(rows, cols, widths, color="000000"):
    """열 너비가 Word·LibreOffice 모두에서 유지되도록
    columns.width + tblGrid/gridCol + 셀 tcW + tblLayout=fixed 를 모두 지정한다."""
    t = doc.add_table(rows=rows, cols=cols)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tblPr = t._tbl.tblPr
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tblPr.append(lay)
    tw = OxmlElement("w:tblW")
    tw.set(qn("w:w"), str(int(sum(widths) * 56.7)))
    tw.set(qn("w:type"), "dxa")
    old = tblPr.find(qn("w:tblW"))
    if old is not None:
        tblPr.remove(old)
    tblPr.append(tw)
    grid = t._tbl.tblGrid
    for i, gc in enumerate(grid.findall(qn("w:gridCol"))):
        gc.set(qn("w:w"), str(int(widths[i] * 56.7)))
    for i, w in enumerate(widths):
        t.columns[i].width = Mm(w)
        for c in t.columns[i].cells:
            width(c, w)
            margins(c)
            border(c, color)
    return t


# 쪽마다 쓴 높이(mm)를 모아 한 쪽을 넘지 않는지 검사한다.
USABLE = 297 - TOP - BOTTOM   # 본문이 들어갈 수 있는 높이
SAFETY = 5                    # Word·LibreOffice 차이를 위한 여유
page_used = [0.0]
PAGE_LOG = []


def height(row, mm, rule=WD_ROW_HEIGHT_RULE.EXACTLY):
    """행 높이 고정 + 행 나눔 금지 + 다음 행과 같은 쪽 유지(표 전체가 한 쪽에 머문다)."""
    row.height = Mm(mm)
    row.height_rule = rule
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:cantSplit"))
    page_used[0] += mm
    tbl = row._tr.getparent()
    if row._tr is not tbl.findall(qn("w:tr"))[-1]:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.keep_with_next = True


def spacer(mm):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing = Mm(mm)
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    p.add_run().font.size = Pt(1)
    page_used[0] += mm
    return p


def check_page():
    n = len(PAGE_LOG) + 1
    PAGE_LOG.append(round(page_used[0], 1))
    assert page_used[0] <= USABLE - SAFETY, (
        f"{n}쪽 표 높이 합 {page_used[0]:.1f}mm 가 한 쪽({USABLE - SAFETY}mm)을 넘습니다. 행 높이를 줄이세요.")
    page_used[0] = 0.0


def new_page():
    """쪽 나눔: 다음 쪽 첫 표 앞 1pt 문단에 '페이지 나누기 전'을 건다(빈 쪽이 생기지 않는다)."""
    check_page()
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing = Pt(1)
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.page_break_before = True
    p.add_run().font.size = Pt(1)


def no_border(*cells):
    for c in cells:
        border(c, sides=())


# ---------------------------------------------------------------- 페이지 구성 요소
def page_background():
    """머리글에 A4 전체 크기 배경 틀 그림을 '텍스트 뒤'로 고정한다(본문은 그대로 편집 가능)."""
    hdr = doc.sections[0].header
    p = hdr.paragraphs[0]
    _para(p, "left", 1.0)
    p.paragraph_format.line_spacing = Pt(1)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    run = p.add_run()
    run.add_picture(os.path.join(ASSETS, "page_bg.png"), width=Mm(210), height=Mm(297))
    inline = run._r.find(".//" + qn("wp:inline"))
    graphic = copy.deepcopy(inline.find(qn("a:graphic")))
    docpr = inline.find(qn("wp:docPr"))
    cx, cy = inline.find(qn("wp:extent")).get("cx"), inline.find(qn("wp:extent")).get("cy")
    anchor = parse_xml(
        '<wp:anchor xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'distT="0" distB="0" distL="0" distR="0" simplePos="0" relativeHeight="0" behindDoc="1" '
        'locked="1" layoutInCell="1" allowOverlap="1">'
        '<wp:simplePos x="0" y="0"/>'
        '<wp:positionH relativeFrom="page"><wp:posOffset>0</wp:posOffset></wp:positionH>'
        '<wp:positionV relativeFrom="page"><wp:posOffset>0</wp:posOffset></wp:positionV>'
        f'<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
        f'<wp:wrapNone/><wp:docPr id="{docpr.get("id")}" name="PQ4R 배경"/>'
        '<wp:cNvGraphicFramePr/></wp:anchor>')
    anchor.append(graphic)
    inline.getparent().replace(inline, anchor)


def first_header():
    """1쪽 머리: [구름 제목(2칸 병합)] / [소단원 제목 | 과학 배지], 142+40mm, 17+17mm."""
    t = table(2, 2, [142, 40])
    height(t.rows[0], 17)
    height(t.rows[1], 17)
    top = t.cell(0, 0).merge(t.cell(0, 1))
    no_border(top, t.cell(1, 0), t.cell(1, 1))
    top.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    picture(top, os.path.join(ASSETS, "title_cloud.png"), 50)
    border(t.cell(1, 0), "D9D9D9", 8)
    write(t.cell(1, 0), U.TITLE, 15, True, "000000", "center")
    t.cell(1, 1).vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    picture(t.cell(1, 1), os.path.join(ASSETS, "badge_science.png"), 26)


def small_header():
    """2~5쪽 머리: [소단원 제목 | 과학 배지], 142+40mm, 11mm."""
    t = table(1, 2, [142, 40])
    height(t.rows[0], 11)
    a, b = t.row_cells(0)
    no_border(a, b)
    write(a, U.TITLE, 16, True, "000000", "center")
    b.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    picture(b, os.path.join(ASSETS, "badge_science.png"), 19, "right")


def band(letter, english, phrase, color, pale, widths=(25, 48, 109)):
    """단계 띠: [글자 | 영어 | 설명], 25+48+109mm, 15mm."""
    t = table(1, 3, list(widths), color)
    height(t.rows[0], 15)
    a, b, c = t.row_cells(0)
    for x in (a, b, c):
        border(x, color, 12)
    shading(a, color)
    shading(b, color)
    shading(c, pale)
    write(a, letter, 22, True, "FFFFFF", "center")
    write(b, english, 13, True, "FFFFFF", "center")
    write(c, phrase, 11.5, True, color)


def head_row(t, labels, color, h):
    height(t.rows[0], h)
    for cell, text in zip(t.rows[0].cells, labels):
        shading(cell, color)
        write(cell, text, 11.5, True, "FFFFFF", "center")


# ---------------------------------------------------------------- 내용 불러오기
if len(sys.argv) != 2:
    sys.exit("사용법: python3 build_pq4r.py units/<소단원>.py")
spec = importlib.util.spec_from_file_location("unit", sys.argv[1])
U = importlib.util.module_from_spec(spec)
spec.loader.exec_module(U)
for name, n in (("PREVIEW_CHECK", 3), ("PREVIEW", 4), ("QUESTIONS", 3), ("KEYWORDS", 4),
                ("REFLECT", 4), ("RECITE", 3), ("REVIEW", 3)):
    assert len(getattr(U, name)) == n, f"{name} 항목은 {n}개여야 합니다."
GOAL = getattr(U, "GOAL", "")  # 비우면 학생이 교과서 학습 목표를 직접 쓴다
OUT = os.path.join(ROOT, "output", U.OUT)

sec = doc.sections[0]
sec.page_width, sec.page_height = Mm(210), Mm(297)
sec.top_margin, sec.bottom_margin = Mm(TOP), Mm(BOTTOM)
sec.left_margin, sec.right_margin = Mm(LEFT), Mm(RIGHT)
sec.header_distance, sec.footer_distance = Mm(0), Mm(0)
st = doc.styles["Normal"]
st.font.name = FONT
st.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
st.font.size = Pt(11.5)
st.paragraph_format.space_after = Pt(0)
page_background()

# ---------------------------------------------------------------- 1쪽 Preview
first_header()
spacer(GAP_S)
p = spacer(5.4)                         # 교과서 쪽수 (오른쪽 정렬)
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
_font(p.add_run(f"교과서 {U.PAGES}"), 10.5, True, TEXT_C)
spacer(1.8)
band("P", "Preview", "먼저 훑기 - 교과서에서 확인할 내용", P_C, P_PALE)
spacer(GAP_S)
t = table(2, 2, [42, 140], P_C)         # 교과서 확인 22mm / 학습 목표 35mm
height(t.rows[0], 22)
height(t.rows[1], 35)
for r, label in enumerate(("교과서 확인", "학습 목표")):
    shading(t.cell(r, 0), P_PALE)
    write(t.cell(r, 0), label, 12, True, P_C, "center")
write(t.cell(0, 1), "\n".join("□ " + x for x in U.PREVIEW_CHECK), 12)
write(t.cell(1, 1), GOAL, 11.5)
spacer(GAP_L)
t = table(5, 2, [14, 168], P_C)         # 학습 전 핵심 내용 예상 13mm + 26mm×4
height(t.rows[0], 13)
head = t.cell(0, 0).merge(t.cell(0, 1))
shading(head, P_C)
write(head, "학습 전 핵심 내용 예상", 15, True, "FFFFFF", "center")
for i, item in enumerate(U.PREVIEW, 1):
    height(t.rows[i], 26)
    shading(t.cell(i, 0), P_PALE)
    write(t.cell(i, 0), str(i), 12, True, P_C, "center")
    write(t.cell(i, 1), item, 11.5, valign="top")

# ---------------------------------------------------------------- 2쪽 Question
new_page()
small_header()
spacer(GAP_S)
band("Q", "Question", "질문 만들기 - 교과서에서 답 찾기", Q_C, Q_PALE)
spacer(GAP_L)
t = table(4, 3, [14, 60, 108], Q_C)     # 14mm + 58mm×3
head_row(t, ["번호", "질문", "교과서에서 찾은 답"], Q_C, 14)
for i, q in enumerate(U.QUESTIONS, 1):
    height(t.rows[i], 58)
    write(t.cell(i, 0), str(i), 13, True, Q_C, "center")
    write(t.cell(i, 1), q, 11.5)

# ---------------------------------------------------------------- 3쪽 Read
new_page()
small_header()
spacer(GAP_S)
band("R", "Read", "답 찾으며 읽기 - 핵심어 정리", R1_C, R1_PALE)
spacer(GAP_L)
t = table(5, 2, [47, 135], R1_C)        # 14mm + 44mm×4
head_row(t, ["핵심어", "교과서에서 찾은 뜻·설명"], R1_C, 14)
for i, k in enumerate(U.KEYWORDS, 1):
    height(t.rows[i], 44)
    write(t.cell(i, 0), k, 12, False, TEXT_C, "center")

# ---------------------------------------------------------------- 4쪽 Reflect
new_page()
small_header()
spacer(GAP_S)
band("R", "Reflect", "연결하기 - 탐구·자료·생활과 연결", R2_C, R2_PALE, (25, 44.7, 112.3))
spacer(GAP_L)
t = table(5, 2, [70.6, 111.4], R2_C)    # 14mm + 약 49mm×4
head_row(t, ["연결 활동", "나의 생각"], R2_C, 14)
for i, r in enumerate(U.REFLECT, 1):
    height(t.rows[i], 49)
    ref, _, rest = r.partition("  ")    # "164쪽  설명…" → 쪽 표시는 굵게
    text = f"**{i}. {ref}** {rest}" if rest else f"**{i}.** {r}"
    write(t.cell(i, 0), text, 10.5)

# ---------------------------------------------------------------- 5쪽 Recite · Review
new_page()
small_header()
spacer(GAP_S)
band("R", "Recite", "내 말로 말하기 - 책을 덮고 쓰기", R3_C, R3_PALE)
spacer(GAP_S)
t = table(4, 2, [73.8, 108.2], R3_C)    # 13mm + 33mm×3
head_row(t, ["회상 질문", "내 답"], R3_C, 13)
for i, r in enumerate(U.RECITE, 1):
    height(t.rows[i], 33)
    write(t.cell(i, 0), f"**{i}.** {r}", 10.5)
spacer(GAP_L)
band("R", "Review", "다시 확인하기 - 자기 점검", R4_C, R4_PALE)
spacer(GAP_S)
t = table(4, 2, [14, 168], R4_C)        # 12mm + 17mm×3
height(t.rows[0], 12)
head = t.cell(0, 0).merge(t.cell(0, 1))
shading(head, R4_C)
write(head, "자기 점검", 11.5, True, "FFFFFF", "center")
for i, r in enumerate(U.REVIEW, 1):
    height(t.rows[i], 17)
    shading(t.cell(i, 0), R4_PALE)
    write(t.cell(i, 0), "□", 13, False, R4_C, "center")
    write(t.cell(i, 1), r, 11, False, REVIEW_TEXT_C)


# ---------------------------------------------------------------- 메타데이터·저장·글꼴 내장
def embed_fonts(path, name, files):
    """TrueType 글꼴을 난독화(odttf)해 DOCX에 내장한다(Word '파일의 글꼴 포함'과 같은 구조)."""
    zin = zipfile.ZipFile(path)
    parts = {n: zin.read(n) for n in zin.namelist()}
    zin.close()
    ct = parts["[Content_Types].xml"].decode()
    if 'Extension="odttf"' not in ct:
        ct = ct.replace("<Default ", '<Default Extension="odttf" ContentType="application/'
                        'vnd.openxmlformats-officedocument.obfuscatedFont"/><Default ', 1)
    parts["[Content_Types].xml"] = ct.encode()
    rels, embeds = [], []
    for i, (style, ttf) in enumerate(files.items(), 1):
        key = "{" + str(uuid.uuid4()).upper() + "}"
        kb = bytes.fromhex(key.strip("{}").replace("-", ""))[::-1]
        data = bytearray(open(ttf, "rb").read())
        for j in range(32):
            data[j] ^= kb[j % 16]
        parts[f"word/fonts/font{i}.odttf"] = bytes(data)
        rels.append(f'<Relationship Id="rIdF{i}" Type="http://schemas.openxmlformats.org/'
                    f'officeDocument/2006/relationships/font" Target="fonts/font{i}.odttf"/>')
        embeds.append(f'<w:embed{style} r:id="rIdF{i}" w:fontKey="{key}"/>')
    ft = parts["word/fontTable.xml"].decode()
    if 'xmlns:r=' not in ft.split(">", 2)[1]:
        ft = ft.replace("<w:fonts ", '<w:fonts xmlns:r="http://schemas.openxmlformats.org/'
                        'officeDocument/2006/relationships" ', 1)
    ft = ft.replace("</w:fonts>", f'<w:font w:name="{name}"><w:charset w:val="81"/>'
                    f'<w:family w:val="auto"/><w:pitch w:val="variable"/>{"".join(embeds)}'
                    '</w:font></w:fonts>')
    parts["word/fontTable.xml"] = ft.encode()
    parts["word/_rels/fontTable.xml.rels"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(rels) + '</Relationships>').encode()
    stx = parts["word/settings.xml"].decode()
    if "embedTrueTypeFonts" not in stx:
        stx = re.sub(r"(<w:zoom[^>]*/>)", r"\1<w:embedTrueTypeFonts/>", stx, 1)
    parts["word/settings.xml"] = stx.encode()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for n, b in parts.items():
            z.writestr(n, b)


check_page()
assert len(PAGE_LOG) == 5, f"5쪽이어야 하는데 {len(PAGE_LOG)}쪽입니다."
print("쪽별 사용 높이(mm):", PAGE_LOG, f"/ 한도 {USABLE - SAFETY}")
doc.core_properties.title = f"PQ4R 노트 - {U.TITLE}"
doc.core_properties.subject = f"미래엔 중등 과학 {U.TITLE} ({U.PAGES})"
doc.core_properties.author = "PQ4R 학습노트"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
doc.save(OUT)
embed_fonts(OUT, FONT, FONT_FILES)
print(OUT)
