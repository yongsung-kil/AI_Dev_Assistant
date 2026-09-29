# 플러그인 4단계: idea-apply, speed-opt, robustness-check, param-opt

> 작성: 2026-09-30 03:08:52
> 상태: 진행 중
> 변경 등급: Review

## 목적

아이디어 적용, 효율화, 안정성 검사, 파라미터 최적화 스킬 넷과 그 양식, 스크립트를 만든다.

## 배경

원 저장소 태스크 문서의 실행계획_4.md.

## 설계

idea_init.py, checklist_init.py, param_opt_init.py와 templates/param_opt/optimizer.py, 스킬 넷, 검사 사례 둘.

## 수정 대상

`plugin/scripts/`, `plugin/skills/`, `plugin/templates/`, `plugin/evals/`, `tests/`.

## 안전성 체크리스트

- [x] 테스트 통과 (65)
- [x] validate --strict, 금지 표현 0, 문서 검사 0
- [ ] 라이트 리뷰 (5단계 뒤 2단계부터 5단계까지 한 번에)

## 미결정 사항

- ㉮ 없음
