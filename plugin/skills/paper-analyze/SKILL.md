---
name: paper-analyze
description: 선별을 통과한 논문의 전문을 paper-reader 에이전트가 프로파일과 함께 읽어 고정 선택지 분류표, 알고리즘 요약, 프로젝트 모듈 대응, JSON을 남기고 db와 카탈로그에 기록한다. 사용자가 "논문 분석", "심층 분석", "전문 분석", "paper-analyze"라고 하면 쓴다
---

# 전문 분석 (2차)

한 논문에 에이전트 하나. 에이전트는 코드를 열지 않고 프로파일과 전문만 읽는다. 스크립트는 이 스킬의 기준 폴더에서 `../../scripts/paper_analyze.py`다.

## 절차

- 1. 양식 확정. `papers/criteria/`의 `categories.md`(고정 선택지)와 `analysis_prompt.md`(분석 지시)에 자리표시(중괄호)가 남아 있으면 프로파일로 채운다. `categories.md`의 "대상 부품" 선택지는 `structure.md`의 모듈 이름으로, "프로젝트 고유 열"은 프로파일에서 뽑은 열로 채운다. 사용자 검토 뒤 확정 (자동 진행이면 보고만)
- 2. 대상 목록. `python "<이 스킬의 기준 폴더>/../../scripts/paper_analyze.py" list -n 10`. 전문(`text_path`)이 없는 논문은 출력의 `expected_path`(예: `papers/pdfs/arxiv_2401.1.pdf`. 파일 이름은 id에서 영문, 숫자, `.`, `_`, `-` 밖의 글자를 `_`로 바꾼 것)에 PDF나 `.txt`를 두라고 안내한다 (라이선스가 있는 PC에서는 브라우저로 내려받는다. paper-search 스킬 4단계)
- 3. 병렬 분석. 전문이 있는 논문마다 `ai-dev-assistant:paper-reader` 에이전트를 background로 부른다 (한 번에 5편 안팎). 각자에게: `analysis_prompt.md` 경로, `categories.md` 경로, `docs/profile/` 경로, 전문 경로, 논문 id와 제목과 연도와 venue. 돌아온 본문(A 분류표, B 요약, C 모듈 대응, D JSON)을 `papers/analysis/{id 안전화}.md`에 저장한다
- 4. `paper_analyze.py apply`로 JSON을 db에 기록한다. 건너뛴 파일(JSON 깨짐, id 없음)은 에이전트를 다시 부르거나 손으로 고친다
- 5. `paper_analyze.py catalog`로 `papers/catalogs/analysis.md`를 만든다 (이식성과 추천도 순)
- 6. 이식성 상이고 추천도 상인 논문을 idea-apply 후보로 보고한다. 기준서를 바꿀 만한 발견은 모아서 보고한다

## 규칙

- ㉮ 분류 값은 고정 선택지만. 값이 선택지 밖이면 apply 전에 고친다
- ㉯ 분석 md의 마지막 json 블록이 db에 들어간다. 손으로 고칠 때도 그 블록을 고친다
- ㉰ 전문 파일은 git이 추적하지 않는다. 분석 md와 카탈로그는 추적한다
