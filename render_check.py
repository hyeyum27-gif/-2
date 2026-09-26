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
if not any("NotoSansKR" in f.replace(" ", "") for f in fonts):
    print("경고: Noto Sans KR 이 쓰이지 않았습니다. 글꼴 설치를 확인하세요.")

imgs = []
for i, p in enumerate(d, 1):
    pix = p.get_pixmap(dpi=110)
    path = os.path.join(out, f"page-{i}.png")
    pix.save(path)
    imgs.append(Image.open(path))
    w, h = p.rect.width, p.rect.height
    print(f"  {i}쪽 글자 수 {len(p.get_text().strip())}, 크기 {w:.0f}x{h:.0f}pt")

tw = 500
th = int(imgs[0].height * tw / imgs[0].width)
sheet = Image.new("RGB", (3 * (tw + 16), 2 * (th + 16)), "white")
for i, im in enumerate(imgs[:6]):
    sheet.paste(im.resize((tw, th)), (8 + (i % 3) * (tw + 16), 8 + (i // 3) * (th + 16)))
sheet.save(os.path.join(out, "contact.png"))
print("연락판:", os.path.join(out, "contact.png"))
