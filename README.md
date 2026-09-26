# PQ4R 과학 학습노트 (미래엔 중등 과학)

기존 「PQ4R 미래엔 교과서 3-1 비열」 노트의 구성을 유지한 **편집 가능한 Word(DOCX), A4 세로 5쪽** 학습노트를 소단원별로 만든다.
학생이 교과서를 직접 읽고 답을 찾아 쓰는 자기주도 학습노트이므로 **답안칸에는 답·힌트를 넣지 않는다.**

## 폴더 구성

| 경로 | 내용 |
| --- | --- |
| `build_pq4r.py` | 디자인·표 구조 생성기(python-docx). 특별한 요청이 없으면 수정하지 않는다. |
| `units/*.py` | 소단원별 내용(출력 파일명, 제목, 쪽수, 질문·핵심어 등). 새 소단원은 파일만 추가한다. |
| `make_assets.py` | 배경 틀·구름 제목·과학 배지 그림과 내장용 글꼴 서브셋을 `assets/`에 만든다(한 번만 실행, 결과는 커밋됨). |
| `assets/` | `page_bg.png`, `title_cloud.png`, `badge_science.png`, `GamjaFlower-KR.ttf`(내장 글꼴), `Jua-title.ttf` |
| `render_check.py` | DOCX → PDF → PNG 렌더링, 쪽수·글꼴 점검, 연락판(contact.png) 생성 |
| `output/` | 완성된 DOCX |

## 사용법

```bash
python3 build_pq4r.py units/elastic_force.py
python3 render_check.py output/PQ4R_탄성력_교과서_편집용.docx
```

## 디자인 (참고 PDF 「힘의 표현·힘의 평형」 PQ4R 노트 기준)

- 크림색(`FFFDF6`) 바탕에 파란 테두리(`0E6CA5`) 흰 종이, 뒤에 겹친 하늘색 종이와 오른쪽 파랑·노랑 탭.
  이 틀은 머리글에 '텍스트 뒤' 전체 쪽 그림으로 넣었고, 본문은 모두 Word 표·텍스트라 그대로 편집된다.
- 1쪽 위 「PQ4R 노트」 구름 제목, 모든 쪽 오른쪽 위 「과학」 배지(그림).
- 글꼴: 손글씨체 **Gamja Flower**. 한글 완성형 2,350자와 영문·숫자·기호만 남긴 서브셋(약 2MB)을
  DOCX 안에 **내장**하므로, 학생 PC에 글꼴이 없어도 같은 모양으로 보인다.
- 단계 띠는 왼쪽 진한 칸에 `P / Preview`처럼 두 줄로, 오른쪽 연한 칸에 「먼저 훑기 - …」 설명을 쓴다.
  표 머리글은 진한 색 바탕에 흰 글씨.

`units/` 파일의 항목 수(생성기가 검사한다):

| 단계 | 색상 | 항목 수 | 구성 |
| --- | --- | --- | --- |
| P Preview | 파랑 `0E7FCC` / `E0F1FA` | 확인 항목 `PREVIEW_CHECK` 3, 적을 항목 `PREVIEW` 4~5 (첫 항목은 `학습 목표`) | 「1. 학습 목표 :」 형식의 빈칸 |
| Q Question | 주황 `FF9F28` / `FFF0C8` | 3 | 번호 / 질문 / 교과서에서 찾은 답 |
| R Read | 초록 `68A941` / `EAF6DC` | 4 | 핵심어 / 교과서에서 찾은 뜻 · 설명 |
| R Reflect | 코랄 `FF8A68` / `FFCFC0` | 4 (문장 또는 `("라벨", "문장")`) | 연결 활동 / 나의 생각. 기본 라벨: 탐구·자료, 탐구·자료, 조건·관계, 생활·확장 연결 |
| R Recite | 보라 `6C2596` / `F6E4FA` | 3 (질문만 적으면 「책을 덮고 "…"의 핵심을 1~2문장으로 말하세요.」로 감싸 파란색 표시) | 회상 질문 / 내 답 |
| R Review | 청록 `2BA89E` / `E0FAF6` | 3 (`~할 수 있다.`) | □ 체크 목록 |

## 새 소단원 제작 순서

1. 첨부 PDF의 실제 교과서 쪽수와 내용을 확인한다(파일명과 요청 문장이 다르면 PDF 내용 우선).
2. 학습 목표·핵심 개념을 찾아 Preview 4항목, 질문 3, 핵심어 4, Reflect 4, Recite 3, Review 3을 작성한다.
   - 답이 교과서 본문·그림·표·그래프에서 직접 찾아져야 하며, 교과서 밖 지식은 넣지 않는다.
   - Reflect는 자료(탐구·그림·표·그래프·생활 사례)를 근거로 설명하게 한다.
3. `units/<새소단원>.py`를 만들고 `OUT`을 **새 파일명**으로 정한다(기존 결과 덮어쓰기 방지).
4. 생성 → 렌더링 → 5쪽, 잘린 문장 없음(render_check.py 자동 검사), 표 깨짐, 열 너비 비율을 눈으로 확인한다.
   모든 표는 한 쪽 안에 들어가야 하며, 생성기가 쪽별 높이 합을 검사한다.

## 렌더링 환경 준비 (새 컨테이너에서)

- `pip install python-docx pymupdf pillow fonttools`
- LibreOffice **Writer** 모듈이 필요하다: `apt-get install -y libreoffice-writer`
  (core만 있으면 “source file could not be loaded” 오류가 난다.)
- 글꼴 확인용으로 Gamja Flower·Jua를 `~/.fonts`에 설치하면 좋다(없어도 DOCX 내장 글꼴로 렌더링됨).
  GitHub·jsDelivr가 막힌 환경이면 npm의 `@fontsource/gamja-flower@4.0.0`, `@fontsource/jua@4.0.0` 안
  `*-all-400-normal.woff`를 fonttools로 TTF 변환해 쓴다(`make_assets.py`의 입력도 이 파일).

## 지켜야 할 설계

- 표는 `table()`에서 `columns.width` + `tblGrid/gridCol` + 셀 `tcW` + `tblLayout=fixed`를 모두 지정한다.
  하나라도 빠지면 LibreOffice에서 열 너비가 같아진다.
- 행 높이는 고정(exact)이다. 표 하단이 흰 종이 하단(287mm)보다 위(약 265~275mm)에 오도록 맞춰 두었다.
- 배경 틀은 VML이 아닌 DrawingML 앵커 그림(behindDoc)이라 LibreOffice에서도 보인다.
- PDF를 배경 이미지로 깔고 글자를 덮는 방식은 LibreOffice에서 흰 페이지가 되어 실패했다. Word 표와 텍스트로만 구성한다.

## 제작 현황

| 소단원 | 교과서 | 상태 |
| --- | --- | --- |
| Ⅴ-1. 탄성력 | 164~167쪽 | `units/elastic_force.py` → `output/PQ4R_탄성력_교과서_편집용.docx` (참고 PDF 디자인 적용, 5쪽 검수 완료) |
| Ⅴ-1. 중력 | 160~163쪽 | 이전 작업 환경에서 완료(Library). 이 저장소에는 내용 파일 없음 |
| Ⅴ-2. 광합성산물의 저장과 이용 | 과학2 186~189쪽 | 이전 작업 환경에서 완료(Library). 이 저장소에는 내용 파일 없음 |
