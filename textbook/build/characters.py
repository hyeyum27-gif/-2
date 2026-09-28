"""「생각을 그리는 수학」 캐릭터 정의: 여우 '보리'와 새 '콩이'.

모든 권의 표지와 본문 삽화는 이 파일의 도형과 색만 사용한다.
권마다 동물의 모습이 달라지지 않도록 비율·색·표정을 여기에서만 고친다.
좌표는 캐릭터 한 마리를 원점 기준으로 그린 값이며,
fox()/bird()가 위치(x, y), 크기(s), 좌우 반전(flip)을 적용한다.
"""

INK = "#2F3B45"          # 캐릭터 윤곽선
FOX = "#EE8A4E"          # 여우 털
FOX_DARK = "#D9713A"     # 여우 그림자·꼬리 줄
CREAM = "#FFF4E6"        # 얼굴·가슴·꼬리 끝
SOCK = "#5A4038"         # 여우 발
BLUSH = "#F4A7A0"
BIRD = "#6FB7D6"         # 새 몸
BIRD_DARK = "#4C98BD"    # 새 날개
BIRD_BELLY = "#EAF6FB"
BEAK = "#F2A04A"

STROKE = 'stroke="%s" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"' % INK


def _fox_body(head_only=False):
    # 원점: 여우가 앉은 바닥 가운데. 높이 약 600.
    full = _FOX_PARTS()
    if head_only:
        return full[full.index("  <path d=\"M-150 -385"):]
    return full


def _FOX_PARTS():
    return f"""
  <clipPath id="foxTail"><path d="M70 -40 C190 -20 250 -120 225 -215 C215 -260 175 -285 150 -262
           C170 -200 150 -120 60 -105 Z"/></clipPath>
  <path d="M70 -40 C190 -20 250 -120 225 -215 C215 -260 175 -285 150 -262
           C170 -200 150 -120 60 -105 Z" fill="{FOX}"/>
  <circle cx="200" cy="-262" r="62" fill="{CREAM}" clip-path="url(#foxTail)"/>
  <path d="M70 -40 C190 -20 250 -120 225 -215 C215 -260 175 -285 150 -262
           C170 -200 150 -120 60 -105 Z" fill="none" {STROKE}/>
  <path d="M-95 -270 C-125 -170 -130 -60 -95 0 L95 0 C130 -60 125 -170 95 -270 Z"
        fill="{FOX}" {STROKE}/>
  <path d="M-58 -262 C-72 -180 -50 -95 0 -80 C50 -95 72 -180 58 -262 Z" fill="{CREAM}"/>
  <ellipse cx="-48" cy="-8" rx="40" ry="22" fill="{SOCK}" {STROKE}/>
  <ellipse cx="48" cy="-8" rx="40" ry="22" fill="{SOCK}" {STROKE}/>
  <path d="M-150 -385 L-120 -520 L-55 -430 Z" fill="{FOX}" {STROKE}/>
  <path d="M-130 -410 L-116 -482 L-80 -432 Z" fill="{CREAM}"/>
  <path d="M150 -385 L120 -520 L55 -430 Z" fill="{FOX}" {STROKE}/>
  <path d="M130 -410 L116 -482 L80 -432 Z" fill="{CREAM}"/>
  <path d="M-150 -380 C-150 -450 -80 -470 0 -470 C80 -470 150 -450 150 -380
           C150 -345 175 -318 185 -300 C140 -300 120 -268 0 -258
           C-120 -268 -140 -300 -185 -300 C-175 -318 -150 -345 -150 -380 Z"
        fill="{FOX}" {STROKE}/>
  <path d="M-150 -330 C-100 -345 -45 -330 0 -300 C45 -330 100 -345 150 -330
           C130 -290 80 -262 0 -258 C-80 -262 -130 -290 -150 -330 Z" fill="{CREAM}"/>
  <ellipse cx="-55" cy="-360" rx="13" ry="18" fill="{INK}"/>
  <ellipse cx="55" cy="-360" rx="13" ry="18" fill="{INK}"/>
  <circle cx="-50" cy="-367" r="4.5" fill="#FFFFFF"/>
  <circle cx="60" cy="-367" r="4.5" fill="#FFFFFF"/>
  <ellipse cx="-92" cy="-318" rx="20" ry="11" fill="{BLUSH}" opacity="0.75"/>
  <ellipse cx="92" cy="-318" rx="20" ry="11" fill="{BLUSH}" opacity="0.75"/>
  <ellipse cx="0" cy="-310" rx="15" ry="10" fill="{INK}"/>
  <path d="M-14 -290 Q0 -278 14 -290" fill="none" {STROKE}/>
"""


def _bird_body():
    # 원점: 새가 딛고 선 바닥 가운데. 높이 약 130.
    return f"""
  <path d="M-48 -62 L-88 -80 L-80 -40 Z" fill="{BIRD_DARK}" {STROKE}/>
  <ellipse cx="0" cy="-58" rx="58" ry="50" fill="{BIRD}" {STROKE}/>
  <ellipse cx="12" cy="-42" rx="32" ry="26" fill="{BIRD_BELLY}"/>
  <path d="M-38 -66 C-20 -84 12 -70 6 -48 C-10 -36 -34 -44 -38 -66 Z" fill="{BIRD_DARK}" {STROKE}/>
  <path d="M-4 -106 C2 -124 16 -126 18 -114" fill="none" {STROKE}/>
  <circle cx="26" cy="-72" r="7" fill="{INK}"/>
  <circle cx="28.5" cy="-74.5" r="2.4" fill="#FFFFFF"/>
  <path d="M54 -70 L80 -62 L54 -53 Z" fill="{BEAK}" {STROKE}/>
  <ellipse cx="34" cy="-54" rx="9" ry="5" fill="{BLUSH}" opacity="0.8"/>
  <path d="M-12 -9 L-12 0 M12 -9 L12 0" stroke="{BEAK}" stroke-width="6" stroke-linecap="round"/>
"""


def fox(x, y, s=1.0, flip=False):
    sx = -s if flip else s
    return f'<g transform="translate({x} {y}) scale({sx} {s})">{_fox_body()}</g>'


def bird(x, y, s=1.0, flip=False):
    sx = -s if flip else s
    return f'<g transform="translate({x} {y}) scale({sx} {s})">{_bird_body()}</g>'


def standalone(kind):
    """캐릭터 한 마리만 담은 SVG (characters/ 폴더에 보관하는 기준 그림)."""
    if kind == "fox":
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="-260 -540 520 560" '
                'width="520" height="560">' + fox(0, 0) + '</svg>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="-100 -140 200 150" '
            'width="400" height="300">' + bird(0, 0) + '</svg>')
