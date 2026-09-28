"""본문·표지 그림을 SVG로 그리고 PNG로 내보낸다.

기존 교재 그림과 같은 규칙을 따른다.
  - 도형 윤곽선: 청록 #227A92, 글자: #253746
  - 채우기: 살구 #FDE2C8 · 노랑 #FFF1BB · 하늘 #D6EBFA · 민트 #D6F0E7 · 보라 #E8DDF7 · 분홍 #FFE5EC
  - 가로 1400px 기준(본문 폭 6.8인치에 맞춤), 흰 배경
"""
import os
import cairosvg
from characters import fox, bird, standalone, INK

LINE = "#227A92"
TEXT = "#253746"
PEACH, YELLOW, SKY, MINT, LAV, PINK = "#FDE2C8", "#FFF1BB", "#D6EBFA", "#D6F0E7", "#E8DDF7", "#FFE5EC"
FONT = "NanumBarunGothic"
def sw(width=4):
    return f'stroke="{LINE}" stroke-width="{width}" stroke-linejoin="round"'


SW = sw()

OUT = os.path.join(os.path.dirname(__file__), "img")


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}" fill="#FFFFFF"/>{body}</svg>')


def label(x, y, t, size=34, weight="normal", color=TEXT, anchor="middle"):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}" text-anchor="{anchor}">{t}</text>')


def save(name, w, h, body, scale=1):
    os.makedirs(OUT, exist_ok=True)
    cairosvg.svg2png(bytestring=svg(w, h, body).encode(), write_to=os.path.join(OUT, name + ".png"),
                     output_width=w * scale, output_height=h * scale)
    return (w, h)


# ── 표지 ─────────────────────────────────────────────
def cover():
    w, h = 1400, 1000
    b = f"""
  <circle cx="1130" cy="230" r="120" fill="{YELLOW}"/>
  <path d="M0 800 C300 740 600 760 800 790 C1000 820 1200 780 1400 760 L1400 1000 L0 1000 Z" fill="{MINT}"/>
  <path d="M0 860 C350 830 700 850 1000 870 C1150 880 1300 870 1400 860" fill="none" stroke="#BFE3D5" stroke-width="6"/>
  <path d="M150 815 L265 600 L380 815 Z" fill="{PEACH}" {sw(6)}/>
  <rect x="860" y="610" width="200" height="200" rx="10" fill="{SKY}" {sw(6)}/>
  <path d="M880 610 L960 480 L1040 610 Z" fill="{LAV}" {sw(6)}/>
  <circle cx="1185" cy="760" r="55" fill="{PINK}" {sw(6)}/>
  {fox(560, 815, 1.05)}
  {bird(960, 484, 1.25, flip=True)}
"""
    return save("cover", w, h, b)


# ── 기본 활동 03: 사각형 (다는 정사각형·직사각형으로 오해받지 않는 사다리꼴) ──
def act03():
    w, h = 1400, 340
    b = f"""
  <rect x="85" y="60" width="150" height="150" fill="{SKY}" {SW}/>
  <rect x="385" y="85" width="260" height="125" fill="{SKY}" {SW}/>
  <path d="M790 210 L1000 210 L960 70 L840 70 Z" fill="{SKY}" {SW}/>
  <path d="M1130 210 L1330 210 L1260 50 Z" fill="{PEACH}" {SW}/>
  {label(160, 285, '가')}{label(515, 285, '나')}{label(895, 285, '다')}{label(1240, 285, '라')}
"""
    return save("act03", w, h, b)


# ── 기본 활동 07: 정사각형 세기 (선 색을 다른 그림과 같은 청록으로) ──
def act07():
    w, h = 1400, 340
    def grid(x, y, n, size):
        c = size / n
        s = f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="#FFFFFF" {sw(5)}/>'
        for i in range(1, n):
            s += f'<line x1="{x + c * i}" y1="{y}" x2="{x + c * i}" y2="{y + size}" {SW}/>'
            s += f'<line x1="{x}" y1="{y + c * i}" x2="{x + size}" y2="{y + c * i}" {SW}/>'
        return s
    b = grid(330, 30, 2, 230) + grid(840, 30, 3, 230) + label(445, 315, '가') + label(955, 315, '나')
    return save("act07", w, h, b)


# ── 생각 넓히기 1: 세 자리 ──
def seats():
    w, h = 1400, 330
    b = ""
    for i, (x, t) in enumerate([(300, '왼쪽'), (700, '가운데'), (1100, '오른쪽')]):
        b += f"""
  <rect x="{x - 110}" y="40" width="220" height="130" rx="18" fill="{[PEACH, MINT, SKY][i]}" {SW}/>
  <rect x="{x - 130}" y="160" width="260" height="40" rx="10" fill="#FFFFFF" {SW}/>
  <line x1="{x - 100}" y1="200" x2="{x - 100}" y2="255" {sw(6)}/>
  <line x1="{x + 100}" y1="200" x2="{x + 100}" y2="255" {sw(6)}/>
  {label(x, 305, t, 34, 'bold')}"""
    b += f'<line x1="120" y1="258" x2="1280" y2="258" stroke="#B9C7CF" stroke-width="4"/>'
    return save("seats", w, h, b)


# ── 기본 활동 14 3번: 빈 계단 ──
def stairs_blank():
    w, h = 700, 330
    def box(x, y, t=""):
        return (f'<rect x="{x}" y="{y}" width="150" height="86" fill="{SKY}" {SW}/>'
                + (label(x + 75, y + 58, t, 40) if t else ""))
    b = box(275, 20, "10") + box(190, 120) + box(360, 120) + box(105, 220) + box(275, 220) + box(445, 220)
    return save("stairs_blank", w, h, b)


# ── 생각 넓히기 2: 도토리 거꾸로 ──
def acorns():
    w, h = 1400, 420
    def card(x, fill, top, body):
        return (f'<rect x="{x}" y="120" width="260" height="170" rx="22" fill="{fill}" {SW}/>'
                + label(x + 130, 95, top, 30, 'bold') + label(x + 130, 228, body, 64, 'bold'))
    def arrow(x, t):
        return (f'<line x1="{x}" y1="205" x2="{x + 110}" y2="205" stroke="{TEXT}" stroke-width="6"/>'
                f'<path d="M{x + 110} 190 L{x + 135} 205 L{x + 110} 220 Z" fill="{TEXT}"/>'
                + label(x + 62, 178, t, 32, 'bold', LINE) )
    b = (card(150, PEACH, '처음', '?') + arrow(435, '+3') + card(590, MINT, '받은 뒤', '?')
         + arrow(875, '-2') + card(1030, SKY, '먹은 뒤', '9'))
    b += (label(575, 370, '콩이가 3개를 줘요', 28, color=TEXT)
          + label(1010, 370, '보리가 2개를 먹어요', 28, color=TEXT))
    b += fox(75, 400, 0.28) + bird(1330, 395, 0.55, flip=True)
    return save("acorns", w, h, b)


# ── 생각 더하기 16: 수 카드와 풍선 ──
def cards_balloons():
    w, h = 1400, 470
    b = ""
    for i, n in enumerate([1, 2, 4]):
        x = 150 + i * 170
        b += (f'<rect x="{x}" y="120" width="130" height="180" rx="16" fill="{YELLOW}" {sw(5)}/>'
              + label(x + 65, 237, str(n), 80, 'bold'))
    b += label(355, 370, '수 카드', 32, 'bold')
    fills = [PEACH, SKY, MINT, LAV, PINK, YELLOW, PEACH]
    for i in range(7):
        x = 760 + (i % 4) * 150 + (75 if i >= 4 else 0)
        y = 110 if i < 4 else 300
        b += (f'<path d="M{x} {y + 52} L{x - 10} {y + 70} L{x + 10} {y + 70} Z" fill="{LINE}"/>'
              f'<path d="M{x} {y + 70} C{x - 12} {y + 95} {x + 12} {y + 110} {x} {y + 135}" fill="none" stroke="{LINE}" stroke-width="3"/>'
              f'<ellipse cx="{x}" cy="{y}" rx="50" ry="56" fill="{fills[i]}" {SW}/>'
              + label(x, y + 16, str(i + 1), 44, 'bold'))
    return save("cards_balloons", w, h, b)


# ── 생각 더하기 17: 십자 모양 ──
def crosses():
    w, h = 1400, 400
    def cross(cx, cy, vals, title):
        c = 78
        pos = {'u': (0, -2), 'l': (-2, 0), 'c': (0, 0), 'r': (2, 0), 'd': (0, 2)}
        s = ""
        for k, (dx, dy) in pos.items():
            x = cx + dx * c / 2 - c / 2 + (dx / 2) * 0
            x = cx + (dx // 2) * c - c / 2
            y = cy + (dy // 2) * c - c / 2
            fill = YELLOW if k == 'c' else SKY
            s += f'<rect x="{x}" y="{y}" width="{c}" height="{c}" fill="{fill}" {SW}/>'
            v = vals.get(k, "")
            if v != "":
                s += label(x + c / 2, y + c / 2 + 16, str(v), 44, 'bold')
        s += label(cx, cy + 2 * c - 5 + 40, title, 32, 'bold')
        return s
    b = (cross(250, 170, {'u': 2, 'l': 1, 'c': 3, 'r': 5, 'd': 4}, '보기')
         + cross(700, 170, {'c': 1}, '1번')
         + cross(1150, 170, {'c': 5}, '2번'))
    return save("crosses", w, h, b)


# ── 생각 더하기 18: 구슬 주머니 ──
def bags():
    w, h = 1400, 400
    RED, BLUE, YEL = "#F28B82", "#7FB7E6", "#F7D54A"
    def bag(cx, marbles, name):
        s = (f'<path d="M{cx - 150} 150 C{cx - 190} 250 {cx - 170} 320 {cx - 100} 330 '
             f'L{cx + 100} 330 C{cx + 170} 320 {cx + 190} 250 {cx + 150} 150 Z" fill="#FBF3E4" {SW}/>'
             f'<path d="M{cx - 150} 150 C{cx - 60} 118 {cx + 60} 118 {cx + 150} 150" fill="none" {SW}/>'
             f'<path d="M{cx - 125} 142 C{cx - 150} 95 {cx - 105} 70 {cx - 60} 110" fill="none" {SW}/>')
        n = len(marbles)
        for i, col in enumerate(marbles):
            x = cx - (n - 1) * 34 + i * 68
            y = 240 + (18 if i % 2 else 0)
            s += f'<circle cx="{x}" cy="{y}" r="28" fill="{col}" stroke="{INK}" stroke-width="3"/>'
        s += label(cx, 385, name, 34, 'bold')
        return s
    b = (bag(260, [RED, RED, RED, RED], '가 주머니')
         + bag(700, [RED, BLUE, RED], '나 주머니')
         + bag(1140, [], '다 주머니'))
    return save("bags", w, h, b)


# ── 생각 더하기 23: 보리의 소풍 준비 ──
def picnic():
    w, h = 1400, 330
    def hat(cx, col, name):
        return (f'<path d="M{cx - 70} 170 C{cx - 70} 80 {cx + 70} 80 {cx + 70} 170 Z" fill="{col}" stroke="{INK}" stroke-width="4"/>'
                f'<path d="M{cx - 70} 170 L{cx + 110} 170 C{cx + 110} 190 {cx - 70} 195 {cx - 70} 170 Z" fill="{col}" stroke="{INK}" stroke-width="4"/>'
                + label(cx + 15, 260, name, 32, 'bold'))
    def bag_round(cx, name):
        return (f'<path d="M{cx - 38} 110 C{cx - 38} 60 {cx + 38} 60 {cx + 38} 110" fill="none" stroke="{INK}" stroke-width="5"/>'
                f'<circle cx="{cx}" cy="160" r="62" fill="{YELLOW}" stroke="{INK}" stroke-width="4"/>'
                + label(cx, 260, name, 32, 'bold'))
    def bag_square(cx, name):
        return (f'<path d="M{cx - 38} 110 C{cx - 38} 60 {cx + 38} 60 {cx + 38} 110" fill="none" stroke="{INK}" stroke-width="5"/>'
                f'<rect x="{cx - 62}" y="100" width="124" height="120" rx="10" fill="{YELLOW}" stroke="{INK}" stroke-width="4"/>'
                + label(cx, 260, name, 32, 'bold'))
    b = (hat(180, "#F28B82", '빨강 모자') + hat(480, "#7FB7E6", '파랑 모자')
         + f'<line x1="700" y1="50" x2="700" y2="280" stroke="#C9D3D9" stroke-width="4" stroke-dasharray="10 10"/>'
         + bag_round(890, '동그란 가방') + bag_square(1170, '네모난 가방'))
    return save("picnic", w, h, b)


def all_images():
    sizes = {}
    for f in (cover, act03, act07, seats, stairs_blank, acorns, cards_balloons, crosses, bags, picnic):
        sizes[f.__name__] = f()
    return sizes


def characters_to_folder(folder):
    os.makedirs(folder, exist_ok=True)
    for k in ("fox", "bird"):
        s = standalone(k)
        open(os.path.join(folder, k + ".svg"), "w").write(s)
        cairosvg.svg2png(bytestring=s.encode(), write_to=os.path.join(folder, k + ".png"))


if __name__ == "__main__":
    print(all_images())
    characters_to_folder(os.path.join(os.path.dirname(__file__), "..", "characters"))
