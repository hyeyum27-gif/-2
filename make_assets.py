"""디자인 자산 생성: 페이지 배경 틀, 「PQ4R 노트」 구름 제목, 「과학」 배지, 내장용 글꼴 서브셋.

원본 글꼴(npm @fontsource/gamja-flower@4.0.0, @fontsource/jua@4.0.0 의 *-all-400-normal.woff 를
TTF로 변환한 것)을 인자로 준다. 결과는 assets/ 에 저장되고 저장소에 함께 커밋한다.

    python3 make_assets.py <GamjaFlower.ttf> <Jua.ttf>
"""
import math
import os
import random
import sys

from fontTools import subset
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(ROOT, "assets")
os.makedirs(A, exist_ok=True)
gamja_src, jua_src = sys.argv[1], sys.argv[2]

CREAM, LINE, UNDER = "#FFFDF6", "#0E6CA5", "#B8E9FF"
TAB_BLUE, TAB_YELLOW = "#1187CF", "#FFCD4A"


# ---------------------------------------------------------------- 글꼴 서브셋
def charset():
    chars = set(chr(c) for c in range(0x20, 0x7F))
    for hi in range(0xB0, 0xC9):          # KS X 1001 한글 완성형 2,350자
        for lo in range(0xA1, 0xFF):
            try:
                chars.add(bytes([hi, lo]).decode("euc-kr"))
            except UnicodeDecodeError:
                pass
    chars |= set(chr(c) for c in range(0x3131, 0x318F))  # 호환 자모
    chars |= set("·ㆍ…‘’“”→←↑↓↔□■○●◎△▲▽▼☆★※Ⅰ-ⅩⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ①②③④⑤⑥⑦⑧⑨⑩℃°±×÷≤≥≠∼～〜㎏㎎㎝㎜㎞㎖㎗㎡㎥ℓ「」『』〈〉《》【】")
    return "".join(sorted(chars))


def make_subset(src, dst, text):
    opt = subset.Options()
    opt.layout_features = ["*"]
    opt.name_IDs = ["*"]
    opt.name_languages = ["*"]
    opt.notdef_outline = True
    f = subset.load_font(src, opt)
    s = subset.Subsetter(opt)
    s.populate(text=text)
    s.subset(f)
    subset.save_font(f, dst, opt)
    print(dst, os.path.getsize(dst) // 1024, "KB")


make_subset(gamja_src, os.path.join(A, "GamjaFlower-KR.ttf"), charset())
make_subset(jua_src, os.path.join(A, "Jua-title.ttf"), "PQ4R 노트과학")


# ---------------------------------------------------------------- 페이지 배경 (A4, 150dpi)
DPI = 150
px = lambda mm: int(round(mm * DPI / 25.4))
W, H = px(210), px(297)
bg = Image.new("RGB", (W, H), CREAM)
d = ImageDraw.Draw(bg)
lw = px(0.7)
# 뒤에 겹친 하늘색 종이와 오른쪽 탭
d.rectangle([px(7.5), px(9.5), px(202.5), px(291.0)], fill=UNDER, outline=LINE, width=lw)
d.rectangle([px(199), px(14.5), px(207.5), px(21.5)], fill=TAB_BLUE, outline=LINE, width=lw)
d.rectangle([px(199), px(24.5), px(207.5), px(31.5)], fill=TAB_YELLOW, outline=LINE, width=lw)
# 앞쪽 흰 종이
d.rectangle([px(4), px(6), px(199.5), px(287.5)], fill="white", outline=LINE, width=lw)
bg.save(os.path.join(A, "page_bg.png"), optimize=True)


# ---------------------------------------------------------------- 물결 모양 도형
def blob(draw, cx, cy, r, fill, seed, bumps=11, amp=0.06, outline=None):
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, 6.28) for _ in range(3)]
    pts = []
    for k in range(360):
        t = math.radians(k)
        rr = r * (1 + amp * math.sin(bumps * t + ph[0]) + amp * 0.5 * math.sin(3 * t + ph[1])
                  + amp * 0.3 * math.sin(17 * t + ph[2]))
        pts.append((cx + rr * math.cos(t), cy + rr * math.sin(t)))
    draw.polygon(pts, fill=fill, outline=outline)


S = 4  # 고해상도로 그린 뒤 축소
jua = os.path.join(A, "Jua-title.ttf")

# 「PQ4R 노트」 구름 제목
tw, th = 560 * S, 160 * S
img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
for i, (cx, r, col) in enumerate([(95, 72, "#8FDCFF"), (190, 76, "#7AD3FF"), (285, 70, "#6FD0FF"),
                                  (375, 74, "#58CCFF"), (465, 72, "#2FD0FF")]):
    blob(d, cx * S, 80 * S, r * S, col, i, bumps=13, amp=0.05)
f = ImageFont.truetype(jua, 92 * S)
words, gap = ["PQ4R", "노트"], 26 * S
boxes = [d.textbbox((0, 0), w, font=f) for w in words]
total = sum(b[2] - b[0] for b in boxes) + gap
x = (tw - total) // 2
for w, bb in zip(words, boxes):
    y = (th - (bb[3] - bb[1])) // 2 - bb[1]
    d.text((x - bb[0] + 3 * S, y + 4 * S), w, font=f, fill=(20, 140, 200, 90))
    d.text((x - bb[0], y), w, font=f, fill="white")
    x += bb[2] - bb[0] + gap
img.resize((tw // S, th // S), Image.LANCZOS).save(os.path.join(A, "title_cloud.png"))

# 「과학」 배지
bw, bh = 200 * S, 110 * S
img = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
blob(d, 72 * S, 55 * S, 48 * S, "#EDC0AE", 7, bumps=12, amp=0.07, outline="#E3A58F")
blob(d, 132 * S, 57 * S, 44 * S, "#F4E58E", 8, bumps=12, amp=0.07, outline="#EAD36A")
f = ImageFont.truetype(jua, 52 * S)
bb = d.textbbox((0, 0), "과학", font=f)
d.text(((bw - (bb[2] - bb[0])) // 2 - bb[0], (bh - (bb[3] - bb[1])) // 2 - bb[1]), "과학", font=f, fill="#1A1A1A")
img.resize((bw // S, bh // S), Image.LANCZOS).save(os.path.join(A, "badge_science.png"))
print("assets ok")
