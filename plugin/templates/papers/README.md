# papers/ (논문과 특허 조사)

| 경로 | 내용 |
|---|---|
| `papers.db` | 모든 메타데이터와 판정과 분석 (SQLite 하나) |
| `criteria/` | 선별 기준서, 분류 스키마, 분석 지시 (양식을 프로파일로 채워 확정한 것) |
| `pdfs/` | 전문 파일 (`{id 안전화}.pdf` 또는 `.txt`). id 안전화는 영문, 숫자, `.`, `_`, `-` 밖의 글자를 `_`로 바꾼 것 (예: `doi:10.1/x` → `doi_10.1_x.pdf`). 예상 경로는 `paper_analyze.py list`가 보여 준다. git이 추적하지 않는다 |
| `analysis/` | 논문별 분석 md (`{id 안전화}.md`) |
| `catalogs/` | 사람이 읽는 카탈로그 md |
| `_work/` | 선별 배치와 판정 결과 (실행별 폴더) |

흐름: 검색(paper-search) → 초록 선별(paper-screen, in 또는 out) → 전문 분석(paper-analyze) → 아이디어 접수(idea-apply).

id 규칙: `arxiv:{번호}`, `doi:{DOI}`, 그 밖에는 `{출처}:{제목 해시 12자}`. 같은 DOI나 같은 제목은 한 번만 넣는다.
