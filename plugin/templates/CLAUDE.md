# CLAUDE.md: AI 작업 진입점

> 모든 작업 시작 전 이 파일을 읽을 것.

## 프로젝트

- ㉮ 이름: (프로젝트 이름)
- ㉯ 한 문장: (docs/profile/overview.md 1절과 같게)
- ㉰ 실행: (명령)

## 지식의 정본

- ㉮ `docs/profile/`의 다섯 문서(overview, structure, replacement_points, techniques, constraints)가 이 프로젝트 지식의 정본이다. 코드를 넓게 읽기 전에 먼저 읽는다
- ㉯ 코드가 바뀌면 프로파일을 먼저 고친다
- ㉰ 설계 결정은 `docs/adr/`에 기록한다 (코드에서 읽을 수 없는 "왜"만)
- ㉱ 탐색 결과는 `docs/explore/`, 위키는 `_wiki/`

## 작업 관리

- ㉮ `_pm/` (TODO, DONE, tasks, done). 절차는 pm 스킬
- ㉯ 변경 등급: Safe(로그, 주석, 포맷)는 자동 진행, Review(로직 변경)는 브리핑 뒤 진행, Decision(설계 변경)은 멈추고 사용자 확인

## 문장 규칙 (코드 주석과 문서 공통)

- ㉮ 수리는 덧대기가 아니라 다시 쓰기
- ㉯ 규칙은 긍정문
- ㉰ 이름과 용어는 명확성 우선. 약어는 첫 등장에서 풀어 쓴다
- ㉱ 줄표(U+2014)와 가운뎃점(U+00B7)을 쓰지 않는다. 나열은 ㉮㉯㉰와 ㉠㉡, 주소를 받는 갈래는 `- 1.`
- ㉲ 변경 금지 대상과 기밀 규칙은 `docs/profile/constraints.md`를 따른다
