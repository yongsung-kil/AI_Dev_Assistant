---
name: paper-search
description: 주제로 논문과 특허를 찾아 papers/papers.db에 쌓는다. arXiv는 공개 API로, IEEE Xplore와 Google Patents는 브라우저에서 검색해 내보낸 CSV를 들여온다. 사용자가 "논문 검색", "특허 검색", "관련 논문 찾아", "paper-search"라고 하면 쓴다
---

# 논문과 특허 검색

결과는 프로젝트의 `papers/papers.db` 한 곳에 쌓인다 (같은 DOI나 같은 제목은 한 번만). 스크립트는 이 스킬의 기준 폴더에서 `../../scripts/paper_search.py`다.

## 절차

- 1. `papers/`가 없으면 `python "<이 스킬의 기준 폴더>/../../scripts/paper_search.py" init`으로 폴더, 기준서 양식, db를 만든다
- 2. 질의를 만든다. 프로파일 `overview.md`의 문제 정의와 `techniques.md`의 기법 이름에서 핵심 낱말을 뽑아 질의 두세 개를 사용자에게 보인다 (예: 기법 이름 + 개선, 문제 이름 + 알고리즘)
- 3. arXiv: `paper_search.py search arxiv "질의" --max 200 --since 연도`. 사내 망이 바깥을 막으면 4의 브라우저 방식으로 arXiv도 검색한다
- 4. IEEE Xplore와 Google Patents: 브라우저에서 검색하고 결과를 CSV로 내보낸다
  - ㉮ Claude Code의 브라우저 도구(Claude in Chrome 또는 내장 브라우저)가 있으면 스킬이 직접 한다: 검색 페이지를 열고, 질의를 넣고, 연도 범위를 잡고, 내보내기(Export)를 눌러 CSV를 받고, 받은 파일 경로를 확인한다. 라이선스가 있는 PC에서는 전문 PDF도 받아 `papers/pdfs/{id 안전화}.pdf`에 둔다
  - ㉯ 브라우저 도구가 없으면 사용자에게 같은 절차를 안내하고 CSV 파일 경로를 받는다
- 5. `paper_search.py import 파일.csv --source ieee` (특허는 `--source patent`). 열 이름은 자동으로 맞춘다 (Document Title, Abstract, Publication Year, DOI, PDF Link, 특허의 id, title, publication date, result link)
- 6. `paper_search.py stats`로 전체 수, 상태별 수, 초록 없는 수를 보고한다. 초록 없는 것(특허 내보내기에는 초록이 없다)은 선별에 들어가지 않으므로, 필요하면 브라우저에서 초록을 받아 db에 넣는 것을 다음 일로 적는다

## 규칙

- ㉮ 검색 결과를 손으로 고르지 않는다. 고르는 일은 paper-screen 스킬이 기준서로 한다
- ㉯ 같은 질의를 다시 돌리면 새 논문만 들어온다 (중복은 셈만 한다)
- ㉰ 전문 파일은 git이 추적하지 않는다 (`papers/pdfs/`)
