"""「생각을 그리는 수학」 1단계 01 학생용 DOCX 조판.

기준 파일: textbook/source/생각을그리는수학_1단계_01_학생용(2).docx
  - 사용자가 직접 고친 안내 쪽과 기본 활동 01·02의 본문(문제 그림, 점판, 그리기 칸, 여백)은
    원본 XML을 그대로 옮긴다. 활동 머리(번호·제목·오늘의 목표)와 돌아보기만 공통 틀로 바꾼다.
  - 나머지 활동은 같은 틀과 간격 규칙으로 다시 조판한다.
  - styles.xml, 기존 그림 파일은 기준 파일의 것을 그대로 쓴다.

실행: python3 illustrations.py && python3 build_docx.py
"""
import copy
import os
import re
import zipfile

from lxml import etree
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "source", "생각을그리는수학_1단계_01_학생용(2).docx")
OUT = os.path.join(ROOT, "생각을그리는수학_1단계_01_학생용.docx")
IMG = os.path.join(HERE, "img")

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
}
W = "{%s}" % NS["w"]
NSDECL = " ".join('xmlns:%s="%s"' % kv for kv in NS.items())

# ── 공통 규격 ─────────────────────────────────────────
CORAL = "EC6F48"      # 활동 번호
TEAL = "227A92"       # 오늘의 목표, 돌아보기 머리
NAVY = "213446"       # 기본 활동 제목
AMBER = "A45C16"      # 생각 더하기 제목
GREEN = "147D88"      # 생각 넓히기 제목
HEAD_FILL = "DCEEF7"  # 표 머리칸
NOTE_FILL = "FFF6DD"  # 보기·함께 해 보기 상자
RULE = "C9D7DE"       # 머리 아래 구분선, 쓰기 줄
TW = 1440             # twips / inch
EMU = 914400          # EMU / inch
BODY_W = 10070        # 표 폭 (기준 파일과 동일)
IMG_W = 6.8           # 그림 폭 (기준 파일과 동일, inch)


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── 문단·런 ───────────────────────────────────────────
def run(text, b=False, color=None, sz=None):
    rpr = ""
    if b:
        rpr += "<w:b/>"
    if color:
        rpr += f'<w:color w:val="{color}"/>'
    if sz:
        rpr += f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
    rpr += '<w:lang w:eastAsia="ko-KR"/>'   # 테마 한글 글꼴(맑은 고딕)이 선택되도록
    parts = text.split("\n")
    out = ""
    for i, ptxt in enumerate(parts):
        if i:
            out += f"<w:r><w:rPr>{rpr}</w:rPr><w:br/></w:r>"
        if ptxt:
            out += f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{esc(ptxt)}</w:t></w:r>'
    return out


def para(content="", style=None, jc=None, before=None, after=None, line=None, line_rule=None,
         keep_next=False, page_break=False, border=None, sz=None, b=False, color=None, ind=None,
         frame=None):
    """content: 문자열(기본 런) 또는 run()으로 만든 XML 문자열 목록."""
    ppr = ""
    if style:
        ppr += f'<w:pStyle w:val="{style}"/>'
    if keep_next:
        ppr += "<w:keepNext/>"
    if page_break:
        ppr += "<w:pageBreakBefore/>"
    if frame:
        ppr += frame
    if border:
        ppr += border
    sp = ""
    if before is not None:
        sp += f' w:before="{before}"'
    if after is not None:
        sp += f' w:after="{after}"'
    if line is not None:
        sp += f' w:line="{line}" w:lineRule="{line_rule or "auto"}"'
    if sp:
        ppr += f"<w:spacing{sp}/>"
    if ind:
        ppr += ind
    if jc:
        ppr += f'<w:jc w:val="{jc}"/>'
    if isinstance(content, str):
        body = run(content, b=b, color=color, sz=sz) if content else ""
    else:
        body = "".join(content)
    return f"<w:p><w:pPr>{ppr}</w:pPr>{body}</w:p>"


def rule_border(side="bottom", color=RULE, size=6, space=6, between=False):
    s = f'<w:{side} w:val="single" w:sz="{size}" w:space="{space}" w:color="{color}"/>'
    if between:
        s += f'<w:between w:val="single" w:sz="{size}" w:space="{space}" w:color="{color}"/>'
    return f"<w:pBdr>{s}</w:pBdr>"


# ── 활동 머리: 번호 → 제목 → 오늘의 목표 (모든 활동 동일) ──
KIND_TITLE_COLOR = {"기본 활동": NAVY, "생각 더하기": AMBER, "생각 넓히기": GREEN}


def header(kind, num, title, goal):
    label = [run(kind, b=True, color=CORAL, sz=20)]
    if num:
        label.append(run("  " + num, b=True, color=CORAL, sz=20))
    return [
        para(label, page_break=True, keep_next=True, before=0, after=40, line=240),
        para([run(title, color=KIND_TITLE_COLOR[kind])], style="1", keep_next=True,
             before=0, after=120, line=240),
        para([run("오늘의 목표", b=True, color=TEAL, sz=21), run("   " + goal, sz=21)],
             border=rule_border(space=8), before=0, after=240),
    ]


def text(t, sz=None, after=None, jc=None, b=False, keep_next=False, before=None):
    """본문 문단. 답을 쓰는 빈칸(____)이 있는 줄은 손글씨가 들어갈 만큼 아래 간격을 더 준다."""
    if after is None:
        after = 300 if "__" in t else 160
    return para(t, sz=sz, after=after, jc=jc, b=b, keep_next=keep_next, before=before,
                line=300 if "__" in t else None)


def q(num, t):
    """문제 머리 (기준 파일의 제목 2 스타일)."""
    return para(f"{num}  {t}" if num else t, style="21", keep_next=True, before=360, after=140)


def spacer(h=None):
    return para("", after=0, line=h, line_rule="exact") if h else para("")


def write_lines(n):
    """글로 쓰는 답 칸. 그리기 칸에는 쓰지 않는다."""
    return [para("", border=rule_border(color=RULE, size=6, space=1, between=True),
                 before=0, after=0, line=580, line_rule="exact") for _ in range(n)] + [spacer(160)]


# 돌아보기는 모든 활동에서 쪽 아래 같은 자리에 둔다 (본문 길이와 상관없이 위치 통일).
BOTTOM_FRAME = ('<w:framePr w:w="11220" w:hSpace="0" w:wrap="notBeside" w:vAnchor="margin" '
                'w:hAnchor="margin" w:x="0" w:yAlign="bottom"/>')


def reflect(t="내 생각을 말이나 그림으로 설명했나요?"):
    return [
        para([run("돌아보기", b=True, color=TEAL, sz=21), run("   " + t, sz=21)],
             frame=BOTTOM_FRAME, border=rule_border("top", space=8), before=0, after=60),
        para([run("혼자 했어요 □     도움을 받아 했어요 □     다시 해 볼래요 □", sz=20)],
             frame=BOTTOM_FRAME, before=0, after=0),
    ]


# ── 표 ───────────────────────────────────────────────
def cell(content, w, fill=None, bold=False, sz=24, jc="center", borders="", valign="center"):
    tcpr = f'<w:tcW w:w="{w}" w:type="dxa"/>{borders}'
    if fill:
        tcpr += f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>'
    tcpr += f'<w:vAlign w:val="{valign}"/>'
    paras = content if isinstance(content, list) else [content]
    ps = "".join(p if p.startswith("<w:p>") else
                 para(p, jc=jc, before=80, after=80, line=240, b=bold, sz=sz) for p in paras)
    return f"<w:tc><w:tcPr>{tcpr}</w:tcPr>{ps}</w:tc>"


def table(rows, widths, heights=None, head=True, sz=24, first_col_fill=False, jc_cells="center"):
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    out = (f'<w:tbl><w:tblPr><w:tblStyle w:val="af9"/><w:tblW w:w="0" w:type="auto"/>'
           f'<w:jc w:val="center"/><w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" '
           f'w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>'
           f"<w:tblGrid>{grid}</w:tblGrid>")
    for ri, row in enumerate(rows):
        h = (heights[ri] if heights and ri < len(heights) else 605)
        out += (f'<w:tr><w:trPr><w:cantSplit/><w:trHeight w:val="{h}" w:hRule="atLeast"/>'
                f'<w:jc w:val="center"/></w:trPr>')
        for ci, c in enumerate(row):
            is_head = head and ri == 0
            fill = HEAD_FILL if is_head or (first_col_fill and ci == 0) else None
            out += cell(c, widths[ci], fill=fill, bold=is_head or (first_col_fill and ci == 0), sz=sz,
                        jc="center" if (is_head or ci == 0) else jc_cells)
        out += "</w:tr>"
    return out + "</w:tbl>"


def draw_box(title, height_in, widths=None):
    """그리기 칸: 머리칸 + 빈 칸. 가로줄을 넣지 않는다 (기준: 기본 활동 01의 2번)."""
    widths = widths or [BODY_W]
    titles = title if isinstance(title, list) else [title]
    h = int(height_in * TW)
    out = (f'<w:tbl><w:tblPr><w:tblStyle w:val="af9"/><w:tblW w:w="0" w:type="auto"/>'
           f'<w:jc w:val="center"/><w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" '
           f'w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr><w:tblGrid>'
           + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + "</w:tblGrid>")
    out += '<w:tr><w:trPr><w:cantSplit/><w:trHeight w:val="605" w:hRule="atLeast"/><w:jc w:val="center"/></w:trPr>'
    for t, w in zip(titles, widths):
        out += cell(t, w, fill=HEAD_FILL, bold=True, borders='<w:tcBorders><w:bottom w:val="nil"/></w:tcBorders>')
    out += f'</w:tr><w:tr><w:trPr><w:cantSplit/><w:trHeight w:val="{h}" w:hRule="exact"/><w:jc w:val="center"/></w:trPr>'
    for w in widths:
        out += cell("", w, borders='<w:tcBorders><w:top w:val="nil"/></w:tcBorders>')
    return out + "</w:tr></w:tbl>"


def note(title, lines, fill=NOTE_FILL):
    """보기·함께 해 보기·단서 상자."""
    ps = [para([run(title, b=True, color=AMBER, sz=21)], before=60, after=40, line=260)]
    for ln in lines:
        ps.append(para(ln, before=0, after=40, line=300))
    tc = (f'<w:tc><w:tcPr><w:tcW w:w="{BODY_W}" w:type="dxa"/><w:tcBorders>'
          f'<w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/></w:tcBorders>'
          f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>'
          f'<w:tcMar><w:top w:w="80" w:type="dxa"/><w:left w:w="200" w:type="dxa"/>'
          f'<w:bottom w:w="80" w:type="dxa"/><w:right w:w="200" w:type="dxa"/></w:tcMar></w:tcPr>'
          + "".join(ps) + "</w:tc>")
    return (f'<w:tbl><w:tblPr><w:tblStyle w:val="af9"/><w:tblW w:w="{BODY_W}" w:type="dxa"/>'
            f'<w:jc w:val="center"/><w:tblLook w:val="04A0" w:firstRow="0" w:lastRow="0" '
            f'w:firstColumn="0" w:lastColumn="0" w:noHBand="1" w:noVBand="1"/></w:tblPr>'
            f'<w:tblGrid><w:gridCol w:w="{BODY_W}"/></w:tblGrid><w:tr><w:trPr><w:cantSplit/>'
            f'<w:jc w:val="center"/></w:trPr>{tc}</w:tr></w:tbl>' + after_table())


def after_table():
    return para("", after=0, line=200, line_rule="exact")


# ── 그림 ─────────────────────────────────────────────
class Media:
    def __init__(self):
        self.rels = {}      # rId -> target
        self.files = {}     # target -> bytes
        self.next_id = 100
        self.doc_pr = 3000

    def keep(self, rid, target, data):
        self.rels[rid] = target
        self.files[target] = data

    def add(self, path):
        target = "media/" + os.path.basename(path)
        rid = f"rId{self.next_id}"
        self.next_id += 1
        self.rels[rid] = target
        self.files[target] = open(path, "rb").read()
        return rid


MEDIA = Media()


def image(rid, w_in, h_in, jc="center", after=120):
    MEDIA.doc_pr += 1
    cx, cy = int(w_in * EMU), int(h_in * EMU)
    d = (f'<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
         f'<wp:effectExtent l="0" t="0" r="0" b="0"/><wp:docPr id="{MEDIA.doc_pr}" name="그림 {MEDIA.doc_pr}"/>'
         f'<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
         f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
         f'<pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="그림"/><pic:cNvPicPr/></pic:nvPicPr>'
         f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
         f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
         f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>'
         f"</wp:inline></w:drawing>")
    return para([f"<w:r>{d}</w:r>"], jc=jc, before=60, after=after, line=240)


def fig(name_or_rid, w_in=IMG_W, after=120):
    """새 그림(img/*.png) 또는 기준 파일 그림(rId)을 폭에 맞춰 넣는다."""
    if name_or_rid.startswith("rId"):
        target = MEDIA.rels[name_or_rid]
        im = Image.open(__import__("io").BytesIO(MEDIA.files[target]))
        rid = name_or_rid
    else:
        path = os.path.join(IMG, name_or_rid + ".png")
        im = Image.open(path)
        rid = MEDIA.add(path)
    w, h = im.size
    return image(rid, w_in, w_in * h / w, after=after)


# ── XML 정리: 기준 파일에서 옮긴 요소의 자식 순서를 스키마 순서로 맞춘다 ──
ORDER = {
    "pPr": "pStyle keepNext keepLines pageBreakBefore framePr widowControl numPr suppressLineNumbers pBdr shd tabs "
           "suppressAutoHyphens kinsoku wordWrap overflowPunct topLinePunct autoSpaceDE autoSpaceDN bidi "
           "adjustRightInd snapToGrid spacing ind contextualSpacing mirrorIndents suppressOverlap jc textDirection "
           "textAlignment textboxTightWrap outlineLvl divId cnfStyle rPr sectPr pPrChange",
    "rPr": "rStyle rFonts b bCs i iCs caps smallCaps strike dstrike outline shadow emboss imprint noProof snapToGrid "
           "vanish webHidden color spacing w kern position sz szCs highlight u effect bdr shd fitText vertAlign rtl "
           "cs em lang eastAsianLayout specVanish oMath",
    "tcPr": "cnfStyle tcW gridSpan hMerge vMerge tcBorders shd noWrap tcMar textDirection tcFitText vAlign hideMark",
    "trPr": "cnfStyle divId gridBefore gridAfter wBefore wAfter cantSplit trHeight tblHeader tblCellSpacing jc hidden",
    "tblPr": "tblStyle tblpPr tblOverlap bidiVisual tblStyleRowBandSize tblStyleColBandSize tblW jc tblCellSpacing "
             "tblInd tblBorders shd tblLayout tblCellMar tblLook",
}
ORDER = {k: {n: i for i, n in enumerate(v.split())} for k, v in ORDER.items()}


def normalize(el):
    for node in el.iter():
        if not isinstance(node.tag, str):
            continue
        local = etree.QName(node).localname
        if local in ORDER and node.tag.startswith(W):
            rank = ORDER[local]
            kids = list(node)
            kids.sort(key=lambda k: rank.get(etree.QName(k).localname, 999))
            for k in kids:
                node.remove(k)
            for k in kids:
                node.append(k)
    return el


def frag(xml_list):
    out = []
    for x in xml_list:
        if isinstance(x, list):
            out.extend(frag(x))
        elif isinstance(x, str):
            wrapper = etree.fromstring(f"<w:body {NSDECL}>{x}</w:body>")
            out.extend(list(wrapper))
        else:
            out.append(x)
    return out


# ═════════════════════════════════════════════════════
# 쪽 구성
# ═════════════════════════════════════════════════════
def cover():
    badge = (f'<w:tbl><w:tblPr><w:tblStyle w:val="af9"/><w:tblW w:w="3000" w:type="dxa"/><w:jc w:val="center"/>'
             f'<w:tblBorders><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/>'
             f'<w:insideH w:val="nil"/><w:insideV w:val="nil"/></w:tblBorders>'
             f'<w:tblLook w:val="0000" w:firstRow="0" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="1" w:noVBand="1"/>'
             f'</w:tblPr><w:tblGrid><w:gridCol w:w="3000"/></w:tblGrid><w:tr><w:trPr><w:cantSplit/>'
             f'<w:trHeight w:val="560" w:hRule="exact"/><w:jc w:val="center"/></w:trPr>'
             + cell([para([run("1단계", b=True, color="FFFFFF", sz=28), run("   01 / 12", b=True, color="FFFFFF", sz=28)],
                           jc="center", before=0, after=0, line=240)], 3000, fill=CORAL)
             + "</w:tr></w:tbl>")
    return [
        para("", after=0, line=760, line_rule="exact"),
        para([run("생각을 그리는 수학", b=True, color=NAVY, sz=64)], jc="center", before=0, after=300, line=240),
        badge,
        para("", after=0, line=560, line_rule="exact"),
        fig("cover", 7.2, after=0),
        para("", after=0, line=720, line_rule="exact"),
        para([run("이름  ", b=True, sz=24), run("________________________", sz=24, color="8A99A6")],
             jc="center", before=0, after=0),
    ]


def reused_front(orig):
    """안내 쪽 + 기본 활동 01·02: 사용자가 고친 본문을 그대로 옮긴다."""
    keep = lambda i: normalize(copy.deepcopy(orig[i]))
    out = []
    # 안내 쪽 (5~14). 첫 요소에 쪽 나눔을 명시한다.
    intro = [keep(i) for i in range(5, 15)]
    ppr = intro[0].find(W + "pPr")
    for pb in ppr.findall(W + "pageBreakBefore"):
        ppr.remove(pb)
    ppr.insert(1, etree.fromstring(f'<w:pageBreakBefore {NSDECL}/>'))
    out += intro

    # 기본 활동 01
    out += frag(header("기본 활동", "01", "곧은 선과 굽은 선", "도형을 이루는 선을 보고 분류해요."))
    out += [keep(i) for i in (19, 20, 21, 22)]
    out += frag([
        table([["곧은 선으로만\n이루어짐", "굽은 선으로만\n이루어짐", "곧은 선과 굽은 선이\n함께 있음"], ["", "", ""]],
              [3357, 3357, 3356], heights=[605, 605]),
    ])
    out += [keep(24), keep(25)]
    out += frag([
        para([run("왼쪽 칸에는 곧은 선만, 오른쪽 칸에는 곧은 선과 굽은 선을 함께 써서 그리세요.", sz=24)]),
        draw_box(["곧은 선만 사용한 도형", "곧은 선과 굽은 선을 함께 사용한 도형"], 2239 / TW, [5035, 5035]),
    ])
    out += [keep(28)]
    out += frag([para("내가 그린 도형에서 굽은 선인 부분을 손가락으로 짚어 보세요.")])
    out += frag(reflect())

    # 기본 활동 02
    out += frag(header("기본 활동", "02", "삼각형을 찾아 그려요", "삼각형의 변과 꼭짓점을 알아보아요."))
    out += [keep(i) for i in range(36, 48)]
    out += frag(reflect("방향이 달라도 삼각형임을 설명할 수 있나요?"))
    return out


def pages():
    P = []
    # ── 기본 활동 03 ──
    P += header("기본 활동", "03", "사각형의 같은 점을 찾아요", "모양이 달라도 변이 4개인 도형을 찾아요.")
    P += [text("곧은 선 4개로 둘러싸인 도형은 사각형이에요. 네 모서리가 모두 종이의 모서리처럼 반듯한 사각형은 "
               "직사각형이에요. 직사각형 중에서 네 변의 길이가 모두 같으면 정사각형이에요."),
          fig("act03"),
          q("1", "알맞은 기호를 모두 쓰세요"),
          table([["사각형", "직사각형", "정사각형"], ["", "", ""]], [3357, 3357, 3356]),
          after_table(),
          text("라는 왜 사각형이 아닐까요?  ______________________________________"),
          q("2", "점을 이어 사각형 두 개를 그리세요"),
          para([run("하나는 정사각형으로, 다른 하나는 정사각형이 아닌 사각형으로 그려요.", sz=24)]),
          fig("rId3", IMG_W, after=160),
          text("두 도형의 같은 점  _______________________________________")]
    P += reflect("정사각형도 사각형이라고 말할 수 있나요?")

    # ── 기본 활동 04 ──
    P += header("기본 활동", "04", "변을 세어 도형 이름을 알아요", "오각형과 육각형을 구별해요.")
    P += [text("곧은 변이 5개면 오각형, 6개면 육각형이에요. 한 꼭짓점에서 시작해 같은 방향으로 돌며 변을 세어 보세요."),
          fig("rId6"),
          q("1", "빈칸을 채우세요"),
          table([["이름표", "곧은 변의 수", "도형 이름"], ["가", "", ""], ["나", "", ""]], [3356, 3357, 3357]),
          after_table(),
          text("다는 오각형이나 육각형일까요?  ________"),
          text("그렇게 생각한 까닭  ______________________________________________"),
          q("2", "점을 이어 오각형 하나를 그리세요"),
          para([run("그린 뒤 꼭짓점마다 작은 동그라미를 하고, 변의 수를 세어 확인해요.", sz=24)]),
          fig("rId7", IMG_W, after=0)]
    P += reflect("한 변을 두 번 세지 않고 셀 수 있나요?")

    # ── 생각 더하기 05 ──
    P += header("생각 더하기", "05", "막대로 도형을 만들어요", "막대의 수를 단서로 도형을 찾아요.")
    P += [text("같은 길이의 막대를 준비하세요. 막대 1개가 변 1개가 돼요. 막대를 꺾거나 겹치지 않고, 두 도형은 떨어뜨려 만들어요."),
          note("함께 해 보기", ["막대 7개로 삼각형과 사각형을 하나씩 만들면 3 + 4 = 7이므로 막대가 남지 않아요."]),
          q("1", "막대 8개로 도형 두 개를 만드세요"),
          text("한 도형은 삼각형이에요. 다른 도형은 변이 몇 개일까요?"),
          text("8 - 3 = ____        다른 도형의 이름  ________________"),
          draw_box("두 도형을 그려 보세요", 1.45),
          after_table(),
          q("2", "막대 9개로 도형 두 개를 만드세요"),
          text("한 도형의 변이 다른 도형보다 1개 더 많아요."),
          text("변의 수  ____개와 ____개        도형 이름  ____________과 ____________"),
          text("확인하는 식  ______________________________")]
    P += reflect("막대의 수와 변의 수를 식으로 확인했나요?")

    # ── 기본 활동 06 ──
    P += header("기본 활동", "06", "생활 속에서 도형을 찾아요", "물건의 그림에서 도형을 발견해요.")
    P += [text("그림을 살펴보세요. 찾은 도형의 테두리를 손가락으로 따라가 보세요."),
          fig("rId8"),
          q("1", "도형이 보이는 부분을 쓰세요"),
          table([["삼각형이 보이는 곳", "사각형이 보이는 곳", "원이 보이는 곳"], ["", "", ""]], [3357, 3357, 3356]),
          after_table(),
          q("2", "교실이나 집에서 도형을 찾아 쓰세요"),
          text("찾은 물건  ____________________        보이는 도형  ______________"),
          draw_box("찾은 물건을 간단히 그려 보세요", 1.75)]
    P += reflect()

    # ── 기본 활동 07 ──
    P += header("기본 활동", "07", "숨어 있는 정사각형을 세어요", "크기별로 나누어 빠짐없이 세어요.")
    P += [text("작은 정사각형뿐 아니라 여러 칸을 합친 큰 정사각형도 찾아요. 그림에 그려진 선만 변으로 사용해요."),
          fig("act07"),
          q("1", "가 그림의 정사각형을 세세요"),
          text("작은 정사각형 ____개 + 큰 정사각형 ____개 = 모두 ____개"),
          q("2", "나 그림의 정사각형을 크기별로 세세요"),
          table([["한 변이 1칸", "한 변이 2칸", "한 변이 3칸", "모두"], ["____개", "____개", "____개", "____개"]],
                [2518, 2518, 2517, 2517]),
          after_table(),
          q("3", "겹쳐 있는 정사각형도 찾아보세요"),
          text("나 그림에서 한 변이 2칸인 정사각형을 서로 다른 색연필로 하나씩 따라 그리세요. 모두 몇 개인가요?  ____개"),
          text("빠짐없이 세기 위해 내가 쓴 방법"),
          *write_lines(2)]
    P += reflect("크기별로 나누어 빠짐없이 세었나요?")

    # ── 기본 활동 08 ──
    P += header("기본 활동", "08", "숨어 있는 삼각형을 세어요", "작은 삼각형과 합쳐진 삼각형을 찾아요.")
    P += [text("세 변이 모두 그려져 있어야 삼각형으로 셀 수 있어요. 없는 선을 새로 그어서 세지는 않아요."),
          fig("rId10"),
          q("1", "가 그림을 살펴보세요"),
          text("작은 삼각형 ____개 + 큰 삼각형 ____개 = 모두 ____개"),
          q("2", "나 그림을 살펴보세요"),
          text("작은 삼각형 ____개 + 큰 삼각형 ____개 = 모두 ____개"),
          text("거꾸로 놓인 삼각형 하나를 색연필로 따라 그리세요."),
          q("3", "친구의 생각을 살펴보세요"),
          text("친구가 “나는 나 그림에서 삼각형을 4개 찾았어.”라고 말했어요.\n친구가 빠뜨린 삼각형은 무엇인지 쓰고, 어떻게 찾았는지 설명해 보세요."),
          *write_lines(2)]
    P += reflect()

    # ── 기본 활동 09 ──
    P += header("기본 활동", "09", "다음에 올 모양을 찾아요", "되풀이되는 묶음과 늘어나는 규칙을 찾아요.")
    P += [note("보기", ["○ △ ○ △ ○ △  →  ○ △가 되풀이돼요.", "되풀이되는 가장 짧은 묶음을 찾아 ○표 해 보세요."]),
          q("1", "빈칸에 알맞은 모양을 그리세요"),
          para([run("가   ○  △  ○  △  ○  ____  ____", sz=36)], after=120),
          para([run("나   □  □  ○  □  □  ○  ____  ____  ____", sz=36)], after=120),
          text("나에서 되풀이되는 가장 짧은 묶음  _________________________"),
          q("2", "수의 규칙을 찾아 쓰세요"),
          text("2, 4, 6, ____, ____        수가 어떻게 달라지나요?  ________________"),
          text("1, 2, 3, ____, ____        수가 어떻게 달라지나요?  ________________"),
          q("3", "나만의 모양 규칙을 만드세요"),
          text("모양 2가지를 골라 되풀이되는 묶음을 만들고, 묶음을 세 번 이어 그려요."),
          draw_box("나만의 규칙", 1.2)]
    P += reflect()

    # ── 기본 활동 10 ──
    P += header("기본 활동", "10", "쌓인 모양과 위치를 살펴요", "위치와 높이를 말로 설명해요.")
    P += [text("같은 크기의 블록을 쌓고 앞에서 보았어요. 숨겨진 블록은 없어요. 그림을 보는 내 쪽을 기준으로 왼쪽과 오른쪽을 말해요."),
          fig("rId11"),
          q("1", "블록을 세고 비교하세요"),
          text("가 ____개      나 ____개      다 ____개      모두 ____개"),
          text("가장 높은 것은 ____이고, 가장 낮은 것은 ____예요."),
          q("2", "위치를 말해 보세요"),
          text("가와 다 사이에 있는 것은 ____예요."),
          text("나의 오른쪽에 있는 것은 ____예요."),
          q("3", "높이를 같게 만들어 보세요"),
          text("가에서 블록 1개를 떼어 다 위에 놓았어요."),
          text("이제 가 ____개, 나 ____개, 다 ____개가 되었어요."),
          text("모두 합한 블록의 수는 바뀌었나요?  ________    까닭  ______________________________")]
    P += reflect()

    # ── 생각 넓히기: 자리 ──
    P += header("생각 넓히기", "", "단서로 자리를 정해요", "단서를 하나씩 따져 가능한 경우를 줄여요.")
    P += [text("민지, 준이, 소라가 의자 세 개에 한 명씩 앉아요. 두 단서에 모두 맞는 자리를 찾아보세요."),
          fig("seats", 5.6),
          note("단서", ["①  소라는 준이의 바로 오른쪽에 앉아요.", "②  민지는 맨 오른쪽에 앉지 않아요."]),
          q("1", "단서 ①만 생각하세요"),
          text("준이와 소라가 앉을 수 있는 방법을 모두 표에 쓰세요. 빈 의자에는 민지를 써요."),
          table([["", "왼쪽", "가운데", "오른쪽"], ["방법 1", "", "", ""], ["방법 2", "", "", ""]],
                [1700, 2790, 2790, 2790], first_col_fill=True),
          after_table(),
          q("2", "단서 ②도 생각하세요"),
          text("위의 표에서 단서 ②에 맞지 않는 방법에 ×표 하고, 남은 방법으로 세 친구의 자리를 쓰세요."),
          text("왼쪽  __________      가운데  __________      오른쪽  __________"),
          q("3", "단서 ②가 없다면 자리를 하나로 정할 수 있을까요?"),
          text("정할 수 (있어요 , 없어요).  까닭"),
          *write_lines(1)]
    P += reflect("단서를 하나씩 확인하며 맞지 않는 경우를 지웠나요?")

    # ── 기본 활동 11 ──
    P += header("기본 활동", "11", "수 이야기를 그림으로 풀어요", "순서와 묶음을 그림으로 나타내요.")
    P += [text("이야기를 읽고 중요한 수에 동그라미를 하세요. 바둑돌을 놓거나 동그라미를 그려 풀어도 좋아요."),
          q("1", "줄을 선 친구들"),
          text("어린이 7명이 한 줄로 서 있어요. 유나는 뒤에서 세 번째에 서 있어요.\n유나의 앞에는 몇 명이 서 있을까요?"),
          para([run("앞   ○  ○  ○  ○  ○  ○  ○   뒤", sz=36)], jc="center", after=120),
          text("위 그림에서 유나에게 ✓표 하고, 유나 앞의 친구들을 세어 보세요."),
          text("답  ______명        내가 센 방법  ________________________________"),
          q("2", "긴 의자에 앉아요"),
          text("의자 하나에 3명씩 앉을 수 있어요. 어린이 10명이 첫째 의자부터 빈자리 없이 앉아요.\n마지막 의자에는 몇 명이 앉을까요?"),
          table([["첫째 의자", "둘째 의자", "셋째 의자", "넷째 의자"], ["○  ○  ○", "", "", ""]],
                [2518, 2518, 2517, 2517], heights=[605, 820]),
          after_table(),
          text("빈 의자에 앉은 어린이를 동그라미로 그려 보세요."),
          text("3 + 3 + 3 + ____ = 10        마지막 의자에는 ____명이 앉아요.")]
    P += reflect("무엇을 구하는 문제인지 확인했나요?")

    # ── 기본 활동 12 ──
    P += header("기본 활동", "12", "10을 두 무리로 나누어요", "빠뜨리지 않고 수를 가르는 방법을 찾아요.")
    P += [text("바둑돌 10개를 두 접시에 나누어 놓아요. 한쪽 접시가 비어 있어도 괜찮아요."),
          note("보기", ["왼쪽 접시 0개 + 오른쪽 접시 10개 = 모두 10개"]),
          q("1", "빈칸을 채우세요"),
          table([["왼쪽 접시", "오른쪽 접시", "모두"], ["0", "10", "10"], ["1", "", "10"], ["2", "", "10"],
                 ["3", "", "10"], ["4", "", "10"], ["5", "", "10"]], [3356, 3357, 3357],
                heights=[520] * 7),
          after_table(),
          q("2", "왼쪽 접시에 6개부터 10개까지 놓으세요"),
          text("6 + ____ = 10        7 + ____ = 10        8 + ____ = 10"),
          text("9 + ____ = 10        10 + ____ = 10"),
          q("3", "어떤 규칙이 있나요"),
          text("왼쪽이 1개 늘 때, 오른쪽은 ____개 (늘어나요 , 줄어들어요)."),
          text("왼쪽과 오른쪽을 구별하면 10을 나누는 방법은 모두 ____가지예요.")]
    P += reflect()

    # ── 생각 더하기 13 ──
    P += header("생각 더하기", "13", "그림 속에 숨은 수를 찾아요", "같은 그림을 같은 수로 바꾸어 생각해요.")
    P += [text("이 쪽에서는 같은 그림이 언제나 같은 수를 나타내요."),
          note("보기", ["△ + 2 = 5라면 △는 3이에요. 3 + 2 = 5로 확인해요."]),
          q("1", "동그라미의 수를 찾으세요"),
          para([run("○ + ○ = 8", sz=40)], after=80),
          text("○ = ____        확인하는 식  ____________________________"),
          q("2", "1번에서 찾은 수를 이용하세요"),
          para([run("○ + □ = 10", sz=40)], after=80),
          text("□ = ____        확인하는 식  ____________________________"),
          q("3", "같은 그림에는 같은 수를 넣으세요"),
          para([run("□ - ○ = ☆", sz=40)], after=80),
          text("☆ = ____        확인하는 식  ____________________________"),
          q("4", "내 수수께끼를 만드세요"),
          text("○, □, ☆ 중 하나 이상을 써서 덧셈식이나 뺄셈식을 만들어요. 친구와 바꿔 풀어 보세요."),
          *write_lines(2)]
    P += reflect()

    # ── 생각 더하기 14 ──
    P += header("생각 더하기", "14", "덧셈 계단을 올라가요", "이웃한 두 수를 더하고 거꾸로도 생각해요.")
    P += [text("바로 아래의 이웃한 두 칸을 더하면 그 위 칸의 수가 돼요."),
          note("보기", ["아래가 1, 2, 3이면 가운데는 1 + 2 = 3, 2 + 3 = 5이고 꼭대기는 3 + 5 = 8이에요."]),
          q("1", "왼쪽 계단을 아래부터 채우세요"),
          q("2", "오른쪽 계단의 빈칸을 채우세요"),
          fig("rId13"),
          para([run("도움말", b=True, color=AMBER, sz=21), run("   오른쪽 가운데의 빈칸은 12 - 5로 찾을 수 있어요.", sz=21)]),
          q("3", "꼭대기를 10으로 만드세요"),
          text("맨 아래 세 칸에 1, 2, 5를 한 번씩 써요. 어느 수를 아래쪽 가운데에 놓아야 할까요?\n수를 바꿔 놓으며 확인해 보세요."),
          fig("stairs_blank", 3.6),
          text("아래쪽 가운데에 놓은 수  ________")]
    P += reflect("거꾸로 계산해 빈칸을 찾았나요?")

    # ── 생각 넓히기: 거꾸로 ──
    P += header("생각 넓히기", "", "거꾸로 따라가요", "마지막 결과에서 거꾸로 계산해 처음 수를 찾아요.")
    P += [text("여우 보리가 도토리를 몇 개 가지고 있었어요. 새 콩이가 도토리 3개를 주었고, 보리가 2개를 먹었더니 "
               "9개가 남았어요. 처음에 보리는 도토리를 몇 개 가지고 있었을까요?"),
          fig("acorns"),
          q("1", "먹기 전에는 몇 개였을까요?"),
          text("먹은 2개를 되돌려 놓아요.      9 + 2 = ____"),
          q("2", "콩이에게 받기 전에는 몇 개였을까요?"),
          text("받은 3개를 되돌려 주어요.      ____ - 3 = ____"),
          q("3", "처음 수로 다시 계산해 확인하세요"),
          text("____ + 3 - 2 = ____        마지막 수가 9가 되었나요?  ________"),
          q("4", "처음 도토리가 1개 더 많았다면 남은 도토리는 몇 개일까요?"),
          text("답  ______개        까닭"),
          *write_lines(1)]
    P += reflect("거꾸로 갈 때 더하기와 빼기를 바꾸어 계산했나요?")

    # ── 기본 활동 15 ──
    P += header("기본 활동", "15", "배운 생각을 다시 써 보아요", "도형과 수를 살펴보고 까닭을 설명해요.")
    P += [q("1", "도형을 찾아요"),
          text("곧은 변이 6개인 도형의 이름은  ______________________"),
          text("정사각형도 사각형일까요?  ______      까닭  ______________________________"),
          q("2", "규칙을 찾아요"),
          para([run("△  ○  ○  △  ○  ○  ____  ____  ____", sz=36)], after=120),
          q("3", "10을 나누어요"),
          text("7 + ____ = 10        ____ + 6 = 10"),
          q("4", "수수께끼를 풀어요"),
          text("이 문제에서만 ♥ + ♥ = 6이에요.      ♥ = ____        ♥ + 4 = ____"),
          q("5", "막대 도형을 생각해요"),
          text("막대 10개로 도형 두 개를 떨어뜨려 만들어요. 한 도형이 사각형이라면\n다른 도형의 변은 ____개이고, 이름은 ______________이에요."),
          q("", "나의 학습 기록"),
          text("가장 재미있었던 활동 번호  ______        다시 해 보고 싶은 활동 번호  ______"),
          text("전에는 어려웠지만 이제 할 수 있는 것"),
          *write_lines(2)]

    # ── 생각 더하기 16 ──
    P += header("생각 더하기", "16", "수 카드로 풍선을 맞혀요", "카드를 골라 더하며 만들 수 있는 수를 모두 찾아요.")
    P += [text("수 카드 1, 2, 4가 한 장씩 있어요. 카드를 한 장만 골라도 되고, 두 장이나 세 장을 골라 더해도 돼요. "
               "한 카드는 한 식에서 한 번만 써요."),
          fig("cards_balloons", 5.4),
          q("1", "풍선을 맞힌 방법을 쓰세요"),
          text("풍선 3은 보기로 먼저 채워 두었어요. 카드 1과 2를 골라  1 + 2 = 3으로 맞혀요."),
          table([["풍선", "고른 카드", "식"], ["1", "", ""], ["2", "", ""], ["3", "1, 2", "1 + 2 = 3"],
                 ["4", "", ""], ["5", "", ""], ["6", "", ""], ["7", "", ""]],
                [1800, 3400, 4870], heights=[450] * 8, sz=22),
          after_table(),
          q("2", "만드는 방법이 두 가지인 풍선이 있나요?"),
          text("(있어요 , 없어요)      있다면 풍선의 수  ______"),
          q("3", "카드 1, 2, 4로 만들 수 없는 가장 작은 수는 얼마일까요?"),
          text("답  ______        까닭  ____________________________________")]
    P += reflect("풍선 1부터 7까지 빠뜨리지 않고 확인했나요?")

    # ── 생각 더하기 17 ──
    P += header("생각 더하기", "17", "십자 모양의 합을 맞춰요", "가운데 수를 바꾸어 보며 합이 같아지는 방법을 찾아요.")
    P += [text("십자 모양의 다섯 칸에 1, 2, 3, 4, 5를 한 번씩 써요. 가로 세 칸의 합과 세로 세 칸의 합이 같아야 해요. "
               "가운데 칸은 가로에도 세로에도 들어가요."),
          fig("crosses", 5.6, after=60),
          para([run("보기", b=True, color=AMBER, sz=21), run("   가로  1 + 3 + 5 = 9        세로  2 + 3 + 4 = 9", sz=21)],
               jc="center", after=120),
          q("1", "가운데에 1을 넣었어요"),
          text("남은 2, 3, 4, 5를 1번 십자에 넣으세요.      가로의 합  ______      세로의 합  ______"),
          q("2", "가운데에 5를 넣었어요"),
          text("남은 1, 2, 3, 4를 2번 십자에 넣으세요.      가로의 합  ______      세로의 합  ______"),
          q("3", "가운데에 2를 넣어도 될까요?"),
          text("남은 1, 3, 4, 5를 두 수씩 나누는 방법은 세 가지예요. 두 합을 모두 구해 비교하세요."),
          table([["나누는 방법", "한쪽의 합", "다른 쪽의 합", "합이 같나요?"],
                 ["1과 3  |  4와 5", "", "", ""], ["1과 4  |  3과 5", "", "", ""], ["1과 5  |  3과 4", "", "", ""]],
                [3070, 2330, 2330, 2340], heights=[460] * 4, sz=22),
          after_table(),
          text("가운데에 2를 넣으면 합을 같게 만들 수 (있어요 , 없어요)."),
          q("4", "가운데에 올 수 있는 수를 모두 쓰세요"),
          text("답  ________________________")]
    P += reflect("가운데 수를 뺀 네 수를 똑같이 나누어 보았나요?")

    # ── 생각 더하기 18 ──
    P += header("생각 더하기", "18", "주머니에서 무엇이 나올까요", "반드시 나오는 것, 나올 수도 있는 것, 나올 수 없는 것을 구별해요.")
    P += [text("새 콩이가 주머니 안을 보지 않고 구슬을 1개 꺼내요. 주머니 안의 구슬을 보고 알맞은 말에 ○표 하세요."),
          fig("bags", 6.4),
          q("1", "알맞은 말에 ○표 하세요"),
          table([["꺼낸 구슬", "알맞은 말"],
                 ["가 주머니에서 빨간 구슬", "반드시 나와요 · 나올 수도 있어요 · 나올 수 없어요"],
                 ["가 주머니에서 파란 구슬", "반드시 나와요 · 나올 수도 있어요 · 나올 수 없어요"],
                 ["나 주머니에서 파란 구슬", "반드시 나와요 · 나올 수도 있어요 · 나올 수 없어요"],
                 ["나 주머니에서 노란 구슬", "반드시 나와요 · 나올 수도 있어요 · 나올 수 없어요"]],
                [3700, 6370], heights=[520] * 5, sz=22),
          after_table(),
          q("2", "콩이가 나 주머니에서 빨간 구슬을 1개 꺼내 밖에 두었어요"),
          text("주머니에 남은 구슬은 빨간 구슬 ____개, 파란 구슬 ____개예요."),
          text("한 개를 더 꺼낼 때 파란 구슬은 (반드시 나와요 , 나올 수도 있어요 , 나올 수 없어요)."),
          q("3", "다 주머니를 채우세요"),
          text("꺼낸 구슬이 반드시 노란 구슬이 되도록 그림의 다 주머니에 구슬 3개를 그리고 색칠하세요."),
          text("다 주머니에서 빨간 구슬은 (반드시 나와요 , 나올 수도 있어요 , 나올 수 없어요).")]
    P += reflect("주머니 안의 구슬을 보고 까닭을 말할 수 있나요?")

    # ── 생각 더하기 19 ──
    P += header("생각 더하기", "19", "빠진 숫자를 찾아요", "십의 자리와 일의 자리를 살펴 계산해요.")
    P += [text("숫자 두 개로 쓴 수에서 왼쪽 숫자는 10이 몇 개인지, 오른쪽 숫자는 낱개가 몇 개인지 알려 줘요. "
               "□에는 숫자 하나가 들어가요."),
          note("함께 해 보기", ["1□ + 2 = 15", "낱개가 2개 늘어 5개가 되었으니 □는 3이에요. 완성하면 13 + 2 = 15예요."]),
          q("1", "빈칸에 들어갈 숫자를 찾으세요"),
          table([["문제", "□에 들어갈 숫자"], ["1□ + 3 = 17", ""], ["2□ - 5 = 21", ""], ["□2 + 4 = 16", ""],
                 ["3□ - 2 = 31", ""]], [5035, 5035], sz=26),
          after_table(),
          q("2", "한 문제를 골라 완성한 식을 쓰세요"),
          text("완성한 식  ______________________      확인한 방법  ______________________"),
          q("3", "친구에게 낼 문제를 만드세요"),
          text("먼저 바른 식을 쓴 뒤 숫자 하나를 □로 가려요."),
          text("내 문제  ______________________      □에 들어갈 숫자  ________")]
    P += reflect()

    # ── 생각 더하기 20 ──
    P += header("생각 더하기", "20", "가로 세로 숫자 퍼즐을 풀어요", "겹치는 칸의 숫자가 같은지 확인해요.")
    P += [text("한 칸에 숫자를 하나씩 써요. 두 칸을 이어 읽으면 두 자리 수가 돼요. 가로는 왼쪽부터, 세로는 위에서부터 읽어요."),
          note("보기", ["1과 2를 나란히 쓰면 12예요. 1 + 2를 뜻하지 않아요."]),
          fig("rId18", 6.0),
          q("1", "가로 문제를 풀어 넣으세요"),
          text("가  위 가로줄      7 + 5 = ______"),
          text("나  아래 가로줄    19 - 6 = ______"),
          q("2", "세로 문제와도 맞는지 확인하세요"),
          text("다  왼쪽 세로줄    6 + 5 = ______"),
          text("라  오른쪽 세로줄  20 + 3 = ______"),
          q("3", "잘못 쓴 수를 찾아보세요"),
          text("친구가 아래 가로줄에 14를 썼어요. 그러면 오른쪽 세로줄은 어떤 수가 되나요?  ______"),
          text("라 문제의 답과 같나요?  ______      고쳐야 할 숫자는  ____를  ____로 바꿔요.")]
    P += reflect("가로뿐 아니라 세로도 확인했나요?")

    # ── 생각 더하기 21 ──
    P += header("생각 더하기", "21", "숫자 원을 따라 식을 만들어요", "이웃한 수의 순서를 지키며 계산해요.")
    P += [text("원 둘레에서 이웃한 숫자 3개를 골라요. 한 방향으로만 따라가며 덧셈식이나 뺄셈식을 만들어요. 숫자를 건너뛰면 안 돼요."),
          fig("rId19", 6.0),
          note("함께 해 보기", ["1 → 2 → 3을 따라가면  1 + 2 = 3이에요.", "거꾸로 3 → 2 → 1을 따라가면  3 - 2 = 1이에요."]),
          q("1", "다른 덧셈식 두 개를 쓰세요"),
          text("____ + ____ = ____            ____ + ____ = ____"),
          q("2", "거꾸로 따라가며 뺄셈식 두 개를 쓰세요"),
          text("____ - ____ = ____            ____ - ____ = ____"),
          q("3", "내 식을 확인하세요"),
          text("식에 쓴 세 수를 원에서 차례대로 짚어 보세요."),
          text("함께 해 보기와 내가 쓴 식을 모두 합치면 원의 다섯 수가 모두 나오나요?  ________")]
    P += reflect()

    # ── 생각 더하기 22 ──
    P += header("생각 더하기", "22", "단서를 읽고 나이를 찾아요", "표에 가능한 것과 아닌 것을 표시해요.")
    P += [text("나리, 도윤, 민서, 하준의 나이는 4살, 6살, 7살, 9살 중 하나씩이고, 네 사람의 나이는 모두 달라요."),
          note("세 가지 단서", ["①  도윤이 가장 나이가 많아요.", "②  민서의 나이는 홀수예요.",
                             "③  나리는 하준보다 나이가 많아요."]),
          para([run("홀수는 둘씩 짝지으면 하나가 남는 수예요. 여기서는 7과 9예요.", sz=20)]),
          table([["이름", "4살", "6살", "7살", "9살"], ["나리", "", "", "", ""], ["도윤", "", "", "", ""],
                 ["민서", "", "", "", ""], ["하준", "", "", "", ""]], [2014] * 5, first_col_fill=True),
          after_table(),
          text("맞는 칸에는 ○, 아닌 칸에는 ×를 표시해요."),
          q("1", "네 사람의 나이를 쓰세요"),
          text("나리 ____살      도윤 ____살      민서 ____살      하준 ____살"),
          q("2", "나리의 나이를 어떻게 알았나요"),
          text("도윤과 민서의 나이를 찾고 나니 남은 나이는 ____살과 ____살이에요."),
          text("나리가 하준보다 나이가 많으므로  ______________________________")]
    P += reflect()

    # ── 생각 더하기 23 ──
    P += header("생각 더하기", "23", "보리의 소풍 차림을 골라요", "한 가지씩 바꾸며 모든 짝을 찾아요.")
    P += [text("여우 보리가 소풍 때 쓸 모자 1개와 멜 가방 1개를 골라요. 모자 색이 같아도 가방 모양이 다르면 다른 차림이에요."),
          fig("picnic", 6.4),
          q("1", "서로 다른 차림을 모두 쓰세요"),
          table([["모자", "가방"], ["빨강 모자", "동그란 가방"], ["빨강 모자", ""], ["파랑 모자", ""], ["파랑 모자", ""]],
                [5035, 5035]),
          after_table(),
          text("서로 다른 차림은 모두 ____가지예요."),
          q("2", "노랑 모자가 하나 더 생겼어요"),
          text("노랑 모자와 짝지을 수 있는 가방  ______________________"),
          text("새로 생긴 차림은 ____가지, 모두 ____가지예요."),
          q("3", "빠뜨리지 않고 찾은 방법을 쓰세요"),
          text("모자 하나를 먼저 정한 뒤"),
          *write_lines(1)]
    P += reflect()
    return P


def anchor_reflections(elements):
    """쪽 아래에 고정되는 돌아보기 프레임을 그 활동의 '오늘의 목표' 바로 뒤로 옮긴다.
    프레임은 뒤따르는 문단의 쪽에 놓이므로, 활동 끝에 두면 다음 쪽으로 밀린다."""
    def is_frame(el):
        return el.tag == W + "p" and el.find(f"{W}pPr/{W}framePr") is not None

    def is_goal(el):
        return el.tag == W + "p" and "".join(el.itertext()).startswith("오늘의 목표")

    out, goal_pos, pending = [], None, []
    for el in elements:
        if is_goal(el):
            goal_pos = len(out) + 1
            out.append(el)
        elif is_frame(el):
            pending.append(el)
            if el.find(f"{W}pPr/{W}pBdr") is None:      # 두 번째 줄까지 모이면 옮긴다
                out[goal_pos:goal_pos] = pending
                pending = []
        else:
            out.append(el)
    return out


# ═════════════════════════════════════════════════════
def build():
    z = zipfile.ZipFile(SRC)
    doc = etree.fromstring(z.read("word/document.xml"))
    body = doc.find(W + "body")
    orig = list(body)

    # 다시 쓰는 기준 파일 그림
    rels_xml = z.read("word/_rels/document.xml.rels").decode()
    for rid, target in re.findall(r'Id="(rId\d+)"[^>]*Target="(media/[^"]+)"', rels_xml):
        if rid in ("rId1", "rId2", "rId3", "rId6", "rId7", "rId8", "rId10", "rId11", "rId13", "rId18", "rId19"):
            MEDIA.keep(rid, target, z.read("word/" + target))

    new = []
    new += frag(cover())
    new += reused_front(orig)
    new += frag(pages())
    new = [normalize(el) for el in anchor_reflections(new)]

    sect = etree.fromstring(
        f'<w:sectPr {NSDECL}><w:footerReference w:type="default" r:id="rId21"/>'
        f'<w:footerReference w:type="first" r:id="rId22f"/>'
        f'<w:pgSz w:w="12240" w:h="15840"/>'
        f'<w:pgMar w:top="720" w:right="720" w:bottom="720" w:left="720" w:header="720" w:footer="432" w:gutter="0"/>'
        f'<w:cols w:space="720"/><w:titlePg/><w:docGrid w:linePitch="360"/></w:sectPr>')
    for el in list(body):
        body.remove(el)
    for el in new:
        body.append(el)
    body.append(sect)

    # 쪽 번호가 들어간 바닥글, 표지용 빈 바닥글
    footer = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr {NSDECL}><w:p><w:pPr>'
              f'<w:pStyle w:val="a6"/><w:jc w:val="right"/></w:pPr>'
              f'<w:r><w:rPr><w:color w:val="7A8A96"/><w:sz w:val="17"/></w:rPr>'
              f'<w:t xml:space="preserve">생각을 그리는 수학  ·  1단계 01     </w:t></w:r>'
              f'<w:r><w:rPr><w:b/><w:color w:val="{TEAL}"/><w:sz w:val="18"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r>'
              f'<w:r><w:rPr><w:b/><w:color w:val="{TEAL}"/><w:sz w:val="18"/></w:rPr><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
              f'<w:r><w:rPr><w:b/><w:color w:val="{TEAL}"/><w:sz w:val="18"/></w:rPr><w:fldChar w:fldCharType="separate"/></w:r>'
              f'<w:r><w:rPr><w:b/><w:color w:val="{TEAL}"/><w:sz w:val="18"/></w:rPr><w:t>2</w:t></w:r>'
              f'<w:r><w:rPr><w:b/><w:color w:val="{TEAL}"/><w:sz w:val="18"/></w:rPr><w:fldChar w:fldCharType="end"/></w:r>'
              f"</w:p></w:ftr>")
    footer_first = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr {NSDECL}>'
                    f'<w:p><w:pPr><w:pStyle w:val="a6"/></w:pPr></w:p></w:ftr>')

    rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
    for rid, target in MEDIA.rels.items():
        rels.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{target}"/>')
    for rid, typ, target in [("rId21", "footer", "footer1.xml"), ("rId22f", "footer", "footer2.xml"),
                             ("rId22", "styles", "styles.xml"), ("rId23", "settings", "settings.xml"),
                             ("rId24", "fontTable", "fontTable.xml"), ("rId25", "webSettings", "webSettings.xml"),
                             ("rId26", "theme", "theme/theme1.xml")]:
        rels.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/{typ}" Target="{target}"/>')
    rels.append("</Relationships>")

    ct = z.read("[Content_Types].xml").decode()
    if 'PartName="/word/footer2.xml"' not in ct:
        ct = ct.replace("</Types>", '<Override PartName="/word/footer2.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/></Types>')
    if 'Extension="png"' not in ct:
        ct = ct.replace("</Types>", '<Default Extension="png" ContentType="image/png"/></Types>')

    core = z.read("docProps/core.xml").decode()
    core = re.sub(r"<dc:title>.*?</dc:title>", "<dc:title>생각을 그리는 수학 1단계 01</dc:title>", core)
    core = re.sub(r"<dc:subject>.*?</dc:subject>", "<dc:subject>도형과 수를 그리며 생각하는 사고력 수학 (학생용)</dc:subject>", core)
    core = re.sub(r"<dc:description>.*?</dc:description>", "<dc:description/>", core)

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as o:
        for item in z.infolist():
            n = item.filename
            if n.startswith("word/media/") or n in ("word/document.xml", "word/_rels/document.xml.rels",
                                                    "word/footer1.xml", "[Content_Types].xml", "docProps/core.xml"):
                continue
            o.writestr(item, z.read(n))
        o.writestr("[Content_Types].xml", ct)
        o.writestr("docProps/core.xml", core)
        o.writestr("word/document.xml", etree.tostring(doc, xml_declaration=True, encoding="UTF-8", standalone=True))
        o.writestr("word/_rels/document.xml.rels", "".join(rels))
        o.writestr("word/footer1.xml", footer)
        o.writestr("word/footer2.xml", footer_first)
        for target, data in MEDIA.files.items():
            o.writestr("word/" + target, data)
    print("저장:", OUT)


if __name__ == "__main__":
    build()
