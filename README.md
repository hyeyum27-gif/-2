# PQ4R 과학 학습노트 (미래엔 중등 과학)

기존 「PQ4R 미래엔 교과서 3-1 비열」 노트의 구성을 유지한 **편집 가능한 Word(DOCX), A4 세로 5쪽** 학습노트를 소단원별로 만든다.
학생이 교과서를 직접 읽고 답을 찾아 쓰는 자기주도 학습노트이므로 **답안칸에는 답·힌트를 넣지 않는다.**

## 폴더 구성

| 경로 | 내용 |
| --- | --- |
| `build_pq4r.py` | 디자인·표 구조 생성기(python-docx). 특별한 요청이 없으면 수정하지 않는다. |
| `units/*.py` | 소단원별 내용(출력 파일명, 제목, 쪽수, 질문·핵심어 등). 새 소단원은 파일만 추가한다. |
| `render_check.py` | DOCX → PDF → PNG 렌더링, 쪽수·글꼴 점검, 연락판(contact.png) 생성 |
| `output/` | 완성된 DOCX |

## 사용법

```bash
python3 build_pq4r.py units/elastic_force.py
python3 render_check.py output/PQ4R_탄성력_교과서_편집용.docx
```

`units/` 파일에는 항목 수가 정해져 있다(생성기가 개수를 검사한다).

| 단계 | 색상 | 항목 수 | 표 머리글 |
| --- | --- | --- | --- |
| P Preview | 파랑 `138BC6` / `DCEFF7` | 4 (첫 칸은 반드시 `학습 목표`) | 항목 / 학습 목표 및 핵심 내용 |
| Q Question | 주황 `FF9F28` / `FFF1D9` | 3 | 번호 / 질문 / 교과서에서 찾은 답 |
| R Read | 초록 `65B33F` / `EDF7DF` | 4 | 핵심어 / 교과서에서 찾은 뜻·설명 |
| R Reflect | 코랄 `FF8A68` / `FFE2D8` | 4 | 연결 활동 / 나의 생각 |
| R Recite | 보라 `72269E` / `F3E6FA` | 3 | 회상 질문 / 내 답 |
| R Review | 청록 `2BA89E` / `DDF6F3` | 3 (`~할 수 있다.`) | 자기 점검 / 잘함 / 보충 |

## 새 소단원 제작 순서

1. 첨부 PDF의 실제 교과서 쪽수와 내용을 확인한다(파일명과 요청 문장이 다르면 PDF 내용 우선).
2. 학습 목표·핵심 개념을 찾아 Preview 4항목, 질문 3, 핵심어 4, Reflect 4, Recite 3, Review 3을 작성한다.
   - 답이 교과서 본문·그림·표·그래프에서 직접 찾아져야 하며, 교과서 밖 지식은 넣지 않는다.
   - Reflect는 자료(탐구·그림·표·그래프·생활 사례)를 근거로 설명하게 한다.
3. `units/<새소단원>.py`를 만들고 `OUT`을 **새 파일명**으로 정한다(기존 결과 덮어쓰기 방지).
4. 생성 → 렌더링 → 5쪽, 한글, 잘림·넘침, 표 깨짐, 열 너비 비율을 눈으로 확인한다.

## 렌더링 환경 준비 (새 컨테이너에서)

- `pip install python-docx pymupdf pillow fonttools`
- LibreOffice **Writer** 모듈이 필요하다: `apt-get install -y libreoffice-writer`
  (core만 있으면 “source file could not be loaded” 오류가 난다.)
- **Noto Sans KR** Regular/Bold를 `~/.fonts`에 설치한다. 이 환경에서는 GitHub·jsDelivr가 막혀 있어
  npm의 `@fontsource/noto-sans-kr@4.0.0` 안의 `noto-sans-kr-all-{400,700}-normal.woff`를
  fonttools로 OTF로 변환해 설치했다. 글꼴이 없으면 한글이 깨지거나 대체된다.
- Windows 호환을 우선하면 `FONT = "맑은 고딕"`으로 바꾸되, 줄바꿈과 표 높이를 다시 검수한다.

## 지켜야 할 설계

- 표는 `table()`에서 `columns.width` + `tblGrid/gridCol` + 셀 `tcW` + `tblLayout=fixed`를 모두 지정한다.
  하나라도 빠지면 LibreOffice에서 열 너비가 같아진다.
- 행 높이는 고정(exact)이며, 각 쪽 내용 하단이 약 276~280mm(한계 285mm)가 되도록 맞춰 두었다.
- PDF를 배경 이미지로 깔고 글자를 덮는 방식은 LibreOffice에서 흰 페이지가 되어 실패했다. Word 표와 텍스트로만 구성한다.

## 제작 현황

| 소단원 | 교과서 | 상태 |
| --- | --- | --- |
| Ⅴ-1. 탄성력 | 164~167쪽 | `units/elastic_force.py` → `output/PQ4R_탄성력_교과서_편집용.docx` (이 저장소에서 재생성, 5쪽 검수 완료) |
| Ⅴ-1. 중력 | 160~163쪽 | 이전 작업 환경에서 완료(Library). 이 저장소에는 내용 파일 없음 |
| Ⅴ-2. 광합성산물의 저장과 이용 | 과학2 186~189쪽 | 이전 작업 환경에서 완료(Library). 이 저장소에는 내용 파일 없음 |
