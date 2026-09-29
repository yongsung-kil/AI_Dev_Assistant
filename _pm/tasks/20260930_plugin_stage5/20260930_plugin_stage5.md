# 플러그인 5단계: paper-search, paper-screen, paper-analyze

> 작성: 2026-09-30 03:17:16
> 상태: 진행 중
> 변경 등급: Review

## 목적

논문과 특허를 찾아 db에 쌓고, 초록으로 병렬 선별하고, 전문을 에이전트가 읽어 분류표와 요약과 모듈 대응을 남기는 스킬 셋을 만든다.

## 배경

원 저장소 태스크 문서의 실행계획_5.md. 검색은 공개 API(arXiv)와 브라우저 내보내기 CSV 들여오기 두 통로.

## 설계

papers_db.py, paper_search.py, paper_screen.py, paper_analyze.py, 양식 넷, paper-reader 에이전트, 스킬 셋.

## 수정 대상

`plugin/scripts/`, `plugin/agents/`, `plugin/skills/`, `plugin/templates/papers/`, `tests/`.

## 안전성 체크리스트

- [x] 테스트 통과 (79)
- [x] validate --strict, 금지 표현 0, 문서 검사 0
- [ ] 라이트 리뷰 (2단계부터 5단계까지 한 번에)

## 미결정 사항

- ㉮ 없음
