"""PQ4R 학습노트(편집 가능한 Word DOCX, A4 세로 5쪽) 생성기.

사용법:
    python3 build_pq4r.py units/elastic_force.py

소단원 내용은 units/*.py 파일에만 적는다. 이 파일의 디자인(색상, 표 너비,
행 높이, fixed layout, tblGrid 처리)은 특별한 요청이 없으면 수정하지 않는다.
배경 틀·구름 제목·과학 배지·내장 글꼴은 make_assets.py 가 만든 assets/ 파일을 쓴다.
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
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")
FONT = "Gamja Flower"  # assets/GamjaFlower-KR.ttf 를 DOCX에 내장한다
FONT_FILE = os.path.join(ASSETS, "GamjaFlower-KR.ttf")

# 단계별 색상 (진한 색 / 연한 배경)
P_C, P_PALE = "0E7FCC", "E0F1FA"      # Preview 파랑
Q_C, Q_PALE = "FF9F28", "FFF0C8"      # Question 주황
R1_C, R1_PALE = "68A941", "EAF6DC"    # Read 초록
R2_C, R2_PALE = "FF8A68", "FFCFC0"    # Reflect 코랄
R3_C, R3_PALE = "6C2596", "F6E4FA"    # Recite 보라
R4_C, R4_PALE = "2BA89E", "E0FAF6"    # Review 청록
INFO_FILL = "FFFBF0"                  # 쪽수 안내 칸
TEXT_C, QUOTE_C = "111111", "1A3CFF"

# 본문 영역: 흰 종이(4~199.5mm) 안쪽
LEFT, RIGHT, TOP, BOTTOM = 8.5, 15.5, 11, 14
PAGE_W = 210 - LEFT - RIGHT  # 186mm

doc = Document()


# ---------------------------------------------------------------- 기본 함수
def shading(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def border(cell, color="000000", size=12, sides=("top", "left", "bottom", "right")):
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


def margins(cell, top=1.2, left=2.2, bottom=1.2, right=2.2):
    tcPr = cell._tc.get_or_add_tcPr()
    old = tcPr.find(qn("w:tcMar"))
    if old is not None:
        tcPr.remove(old)
    m = OxmlElement("w:tcMar")
    for k, v in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        e = OxmlElement(f"w:{k}")
        e.set(qn("w:w"), str(int(v * 56.7)))
        e.set(qn("w:type"), "dxa")
        m.append(e)
    tcPr.append(m)


def _font(run, size, bold, color):
    run.font.name = FONT
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def _para(p, align, spacing):
    p.alignment = {"left": WD_ALIGN_PARAGRAPH.LEFT, "center": WD_ALIGN_PARAGRAPH.CENTER,
                   "right": WD_ALIGN_PARAGRAPH.RIGHT}[align]
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing = spacing


def write(cell, text, size=13, bold=False, color=TEXT_C, align="left",
          valign="center", spacing=1.2):
    """셀 내용을 text로 교체한다. 줄바꿈(\\n)은 문단, "따옴표" 구간은 파란색으로 쓴다."""
    cell.vertical_alignment = {"top": WD_CELL_VERTICAL_ALIGNMENT.TOP,
                               "center": WD_CELL_VERTICAL_ALIGNMENT.CENTER}[valign]
    p = cell.paragraphs[0]
    for i, line in enumerate(text.split("\n")):
        if i:
            p = cell.add_paragraph()
        _para(p, align, spacing)
        for j, part in enumerate(re.split(r'("[^"]*")', line)):
            if part:
                _font(p.add_run(part), size, bold or j % 2 == 1, QUOTE_C if j % 2 else color)
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


def check_page():
    n = len(PAGE_LOG) + 1
    PAGE_LOG.append(round(page_used[0], 1))
    assert page_used[0] <= USABLE - SAFETY, (
        f"{n}쪽 표 높이 합 {page_used[0]:.1f}mm 가 한 쪽({USABLE - SAFETY}mm)을 넘습니다. 행 높이를 줄이세요.")
    page_used[0] = 0.0


PAGE_LOG = []


def page_break():
    check_page()
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = Pt(1)
    r = p.add_run()
    r.font.size = Pt(1)
    r.add_break(WD_BREAK.PAGE)


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


def top_bar(first_page):
    """1쪽: 구름 제목, 2~5쪽: 소단원 제목. 오른쪽에 과학 배지."""
    t = table(1, 3, [40, 106, 40])
    height(t.rows[0], 23 if first_page else 13)
    a, b, c = t.row_cells(0)
    no_border(a, b, c)
    if first_page:
        picture(b, os.path.join(ASSETS, "title_cloud.png"), 70)
    else:
        write(b, U.TITLE, 16, True, align="center")
    c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
    picture(c, os.path.join(ASSETS, "badge_science.png"), 22, "right")


def band(letter, english, phrase, color, pale):
    t = table(1, 2, [60, 126], color)
    height(t.rows[0], 15)
    a, b = t.row_cells(0)
    shading(a, color)
    shading(b, pale)
    write(a, f"{letter}\n{english}", 13.5, True, "FFFFFF", "center", spacing=1.0)
    write(b, phrase, 14, True)


def head_row(t, labels, color, fill=None, text_color="FFFFFF"):
    height(t.rows[0], 11)
    for cell, text in zip(t.rows[0].cells, labels):
        shading(cell, fill or color)
        write(cell, text, 12.5, True, text_color, "center")


# ---------------------------------------------------------------- 내용 불러오기
if len(sys.argv) != 2:
    sys.exit("사용법: python3 build_pq4r.py units/<소단원>.py")
spec = importlib.util.spec_from_file_location("unit", sys.argv[1])
U = importlib.util.module_from_spec(spec)
spec.loader.exec_module(U)
assert len(U.PREVIEW) in (4, 5) and U.PREVIEW[0] == "학습 목표", "PREVIEW는 '학습 목표'로 시작하는 4~5개"
assert len(U.PREVIEW_CHECK) == 3, "PREVIEW_CHECK는 3개"
for name, n in (("QUESTIONS", 3), ("KEYWORDS", 4), ("REFLECT", 4), ("RECITE", 3), ("REVIEW", 3)):
    assert len(getattr(U, name)) == n, f"{name} 항목은 {n}개여야 합니다."
OUT = os.path.join(ROOT, "output", U.OUT)

sec = doc.sections[0]
sec.page_width, sec.page_height = Mm(210), Mm(297)
sec.top_margin, sec.bottom_margin = Mm(TOP), Mm(BOTTOM)
sec.left_margin, sec.right_margin = Mm(LEFT), Mm(RIGHT)
sec.header_distance, sec.footer_distance = Mm(0), Mm(0)
st = doc.styles["Normal"]
st.font.name = FONT
st.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
st.font.size = Pt(13)
st.paragraph_format.space_after = Pt(0)
page_background()

# ---------------------------------------------------------------- 1쪽 Preview
top_bar(True)
spacer(0.5)
t = table(1, 1, [PAGE_W])
height(t.rows[0], 8.5)
no_border(t.cell(0, 0))
write(t.cell(0, 0), U.TITLE, 16, True, align="center")
spacer(2)
t = table(1, 2, [42, 144], "000000")
height(t.rows[0], 11)
for c in t.row_cells(0):
    shading(c, INFO_FILL)
    border(c, "111111", 14)
write(t.cell(0, 0), f"교과서 {U.PAGES}", 13, False, align="center")
write(t.cell(0, 1), "교과서를 옆에 펴고 아래 순서대로 직접 적으세요.", 13, False, align="center")
spacer(4)
band("P", "Preview", "먼저 훑기 - 교과서에서 확인할 내용", P_C, P_PALE)
spacer(1)
n = len(U.PREVIEW)
t = table(n + 1, 1, [PAGE_W], P_C)  # 확인 상자와 적는 칸을 한 표로(표가 붙어 합쳐지는 문제 방지)
height(t.rows[0], 34)
shading(t.cell(0, 0), P_PALE)
write(t.cell(0, 0), "교과서에서 먼저 확인할 내용\n" + "\n".join("□ " + x for x in U.PREVIEW_CHECK),
      12.5, valign="top", spacing=1.25)
for i, item in enumerate(U.PREVIEW):
    height(t.rows[i + 1], 163 / n)
    c = t.cell(i + 1, 0)
    sides = ["left", "right", "top"] if i == 0 else ["left", "right"]
    border(c, P_C, 12, sides + (["bottom"] if i == n - 1 else []))
    write(c, f"{i + 1}. {item} :", 13.5, True, valign="top")
page_break()

# ---------------------------------------------------------------- 2쪽 Question
top_bar(False)
spacer(4)
band("Q", "Question", "질문 만들기 - 교과서에서 답 찾기", Q_C, Q_PALE)
spacer(1)
t = table(4, 3, [19, 61, 106], Q_C)
head_row(t, ["번호", "질문", "교과서에서 찾은 답"], Q_C)
for i, q in enumerate(U.QUESTIONS, 1):
    height(t.rows[i], 72)
    a, b, c = t.row_cells(i)
    write(a, str(i), 14, False, align="center")
    write(b, q, 13, True, align="center", spacing=1.35)
page_break()

# ---------------------------------------------------------------- 3쪽 Read
top_bar(False)
spacer(4)
band("R", "Read", "답 찾으며 읽기 - 핵심어 정리", R1_C, R1_PALE)
spacer(1)
t = table(5, 2, [44, 142], R1_C)
head_row(t, ["핵심어", "교과서에서 찾은 뜻 · 설명"], R1_C)
for i, k in enumerate(U.KEYWORDS, 1):
    height(t.rows[i], 54)
    write(t.cell(i, 0), k, 14, True, align="center")
page_break()

# ---------------------------------------------------------------- 4쪽 Reflect
REFLECT_LABELS = ["탐구·자료 연결", "탐구·자료 연결", "조건·관계 연결", "생활·확장 연결"]
top_bar(False)
spacer(4)
band("R", "Reflect", "연결하기 - 탐구 · 자료 · 생활과 연결", R2_C, R2_PALE)
spacer(1)
t = table(5, 2, [74, 112], R2_C)
head_row(t, ["연결 활동", "나의 생각"], R2_C)
for i, r in enumerate(U.REFLECT, 1):
    label, text = r if isinstance(r, tuple) else (REFLECT_LABELS[i - 1], r)
    height(t.rows[i], 54)
    write(t.cell(i, 0), f"{label} | 질문 {i}\n{text}", 12.5, align="center", spacing=1.35)
page_break()

# ---------------------------------------------------------------- 5쪽 Recite · Review
top_bar(False)
spacer(4)
band("R", "Recite", "내 말로 말하기 - 책을 덮고 쓰기", R3_C, R3_PALE)
spacer(1)
t = table(4, 2, [74, 112], R3_C)
head_row(t, ["회상 질문", "내 답"], R3_C)
for i, r in enumerate(U.RECITE, 1):
    height(t.rows[i], 52)
    write(t.cell(i, 0), f'책을 덮고 "{r}"의 핵심을 1~2문장으로 말하세요.', 12.5,
          align="center", spacing=1.35)
spacer(6)
band("R", "Review", "다시 확인하기 - 자기 점검", R4_C, R4_PALE)
spacer(1)
t = table(1, 1, [PAGE_W], R4_C)
height(t.rows[0], 30)
shading(t.cell(0, 0), R4_PALE)
write(t.cell(0, 0), "\n".join("□ " + r for r in U.REVIEW), 13, spacing=1.4)


# ---------------------------------------------------------------- 메타데이터·저장·글꼴 내장
def embed_font(path, ttf, name):
    """TrueType 글꼴을 난독화(odttf)해 DOCX에 내장한다(Word '파일의 글꼴 포함'과 같은 구조)."""
    key = "{" + str(uuid.uuid4()).upper() + "}"
    kb = bytes.fromhex(key.strip("{}").replace("-", ""))[::-1]
    data = bytearray(open(ttf, "rb").read())
    for i in range(32):
        data[i] ^= kb[i % 16]
    zin = zipfile.ZipFile(path)
    files = {n: zin.read(n) for n in zin.namelist()}
    zin.close()
    ct = files["[Content_Types].xml"].decode()
    if 'Extension="odttf"' not in ct:
        ct = ct.replace("<Default ", '<Default Extension="odttf" ContentType="application/'
                        'vnd.openxmlformats-officedocument.obfuscatedFont"/><Default ', 1)
    files["[Content_Types].xml"] = ct.encode()
    ft = files["word/fontTable.xml"].decode()
    font_xml = (f'<w:font w:name="{name}"><w:charset w:val="81"/><w:family w:val="auto"/>'
                f'<w:pitch w:val="variable"/><w:embedRegular r:id="rIdF1" w:fontKey="{key}"/></w:font>')
    if 'xmlns:r=' not in ft.split(">", 2)[1]:
        ft = ft.replace("<w:fonts ", '<w:fonts xmlns:r="http://schemas.openxmlformats.org/'
                        'officeDocument/2006/relationships" ', 1)
    ft = ft.replace("</w:fonts>", font_xml + "</w:fonts>")
    files["word/fontTable.xml"] = ft.encode()
    files["word/_rels/fontTable.xml.rels"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rIdF1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
        'relationships/font" Target="fonts/font1.odttf"/></Relationships>').encode()
    files["word/fonts/font1.odttf"] = bytes(data)
    stx = files["word/settings.xml"].decode()
    if "embedTrueTypeFonts" not in stx:
        stx = re.sub(r"(<w:zoom[^>]*/>)", r"\1<w:embedTrueTypeFonts/>", stx, 1)
    files["word/settings.xml"] = stx.encode()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for n, b in files.items():
            z.writestr(n, b)


doc.core_properties.title = f"PQ4R 노트 - {U.TITLE}"
doc.core_properties.subject = f"미래엔 중등 과학 {U.TITLE} ({U.PAGES})"
doc.core_properties.author = "PQ4R 학습노트"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
check_page()
assert len(PAGE_LOG) == 5, f"5쪽이어야 하는데 {len(PAGE_LOG)}쪽입니다."
print("쪽별 사용 높이(mm):", PAGE_LOG, f"/ 한도 {USABLE - SAFETY}")
doc.save(OUT)
embed_font(OUT, FONT_FILE, FONT)
print(OUT)
