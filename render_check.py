"""DOCX → PDF(LibreOffice) → PNG 렌더링 후 쪽수·글꼴을 점검하고 연락판을 만든다.

사용법:
    python3 render_check.py output/<파일>.docx [렌더링폴더]
"""
import os
import subprocess
import sys

import pymupdf as fitz
from PIL import Image

src = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join("render", os.path.splitext(os.path.basename(src))[0])
os.makedirs(out, exist_ok=True)
subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", out, src],
               check=True, capture_output=True)
pdf = os.path.join(out, os.path.splitext(os.path.basename(src))[0] + ".pdf")
d = fitz.open(pdf)

fonts = sorted({f[3] for p in d for f in p.get_fonts()})
print("쪽수:", d.page_count, "(OK)" if d.page_count == 5 else "(5쪽이 아님!)")
print("글꼴:", ", ".join(fonts))
bad = [f for f in fonts if "Gaegu" not in f]
if bad:
    print("참고: Gaegu에 없는 기호(Ⅴ □ · 등)는 대체 글꼴로 표시:", ", ".join(bad))

# 잘림 검사: DOCX 의 모든 문장이 PDF 에 온전히 나타나는지 확인 (공백 무시)
from docx import Document
from fontTools.ttLib import TTFont
cmap = TTFont(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "Gaegu-KR-Regular.ttf")).getBestCmap()
# 본문 글꼴에 없는 기호(Ⅴ □ · 등)는 대체 글꼴로 그려져 추출 순서가 섞이므로 비교에서 뺀다
norm = lambda x: "".join(ch for ch in x if not ch.isspace() and ord(ch) in cmap)
pdf_text = norm("".join(p.get_text() for p in d))
missing = []
for t in Document(src).tables:
    for row in t.rows:
        for c in row.cells:
            for par in c.paragraphs:
                if norm(par.text) and norm(par.text) not in pdf_text:
                    missing.append(par.text)
print("잘린 문장:", "없음 (OK)" if not missing else "")
for m in dict.fromkeys(missing):
    print("   ✗", m)

imgs = []
for i, p in enumerate(d, 1):
    pix = p.get_pixmap(dpi=110)
    path = os.path.join(out, f"page-{i}.png")
    pix.save(path)
    imgs.append(Image.open(path))
    w, h = p.rect.width, p.rect.height
    bottom = max((dr["rect"][3] for dr in p.get_drawings()), default=0) * 25.4 / 72
    print(f"  {i}쪽 글자 수 {len(p.get_text().strip())}, 표 하단 {bottom:.1f}mm (종이 하단 287mm)")

tw = 500
th = int(imgs[0].height * tw / imgs[0].width)
sheet = Image.new("RGB", (3 * (tw + 16), 2 * (th + 16)), "white")
for i, im in enumerate(imgs[:6]):
    sheet.paste(im.resize((tw, th)), (8 + (i % 3) * (tw + 16), 8 + (i // 3) * (th + 16)))
sheet.save(os.path.join(out, "contact.png"))
print("연락판:", os.path.join(out, "contact.png"))
