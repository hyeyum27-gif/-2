# 생각을 그리는 수학

- `생각을그리는수학_1단계_01_학생용.docx` — 1단계 01권 학생용 편집본 (Word, 편집 가능)
- `정답_검토표.md` — 정답과 수학 검토 메모 (교사용)
- `source/` — 편집 기준으로 받은 사용자 수정본
- `characters/` — 여우 '보리'와 새 '콩이' 기준 그림. 다음 권에서도 이 그림을 그대로 쓴다.
- `build/` — 그림(`illustrations.py`, `characters.py`)과 DOCX 조판(`build_docx.py`) 스크립트

다시 만들기:

```bash
pip install lxml pillow cairosvg
cd textbook/build && python3 illustrations.py && python3 build_docx.py
```

조판 규칙 (모든 활동 공통)

- 활동 머리: 번호(10pt, 주황) → 제목(17pt) → 오늘의 목표(10.5pt, 아래 구분선). 왼쪽 기준선에 맞추고, 활동마다 새 쪽에서 시작한다.
- 돌아보기: 쪽 아래 같은 자리에 고정한다.
- 그리기 칸: 머리칸이 있는 빈 칸만 둔다. 가로줄을 넣지 않는다. 글로 쓰는 답에만 줄을 긋는다.
- 그림: 폭 6.8인치 이하, 청록 선(#227A92)과 파스텔 채우기.
