# 플러그인 3단계: 대시보드와 HTML 작성 가이드

> 작성: 2026-09-30 02:54:39
> 상태: 진행 중
> 변경 등급: Review

## 목적

작업 현황을 한 화면에 보이는 정적 대시보드(사이드바 접기, 검색, 오른쪽 차례, 진행 중 카드, 문서 지도)와 그 규격 정본 docs/html_guide.md를 만든다.

## 배경

원 저장소 태스크 문서의 실행계획_3.md.

## 설계

md_to_html.py(표준 라이브러리 변환기), collect_status.py(status.json), render_dashboard.py(html), dashboard 스킬, html_guide.md.

## 수정 대상

`plugin/scripts/`, `plugin/skills/dashboard/`, `plugin/templates/dashboard/`, `docs/html_guide.md`, `dashboard/`(자기 적용 산출물), `tests/`.

## 안전성 체크리스트

- [x] 테스트 통과 (53)
- [ ] 자기 적용과 시험장 적용, 깨진 링크 0
- [ ] 라이트 리뷰

## 미결정 사항

- ㉮ 없음
