# 플러그인 7단계 배포와 8단계 소개 페이지

> 작성: 2026-09-30 03:26:05
> 상태: 진행 중
> 변경 등급: Review

## 목적

마켓플레이스 파일과 설치 안내로 배포 준비를 하고, 플러그인 소개 페이지(docs/intro.html)를 규격대로 만든다.

## 배경

원 저장소 태스크 문서의 실행계획_7_8.md.

## 설계

.claude-plugin/marketplace.json, README(설치, 처음 쓰는 법, 스킬 표), plugin/README.md, docs/intro.html(카드, 다섯 단계, 흐름, 프로파일 표, 스킬 접힘, 자주 묻는 것).

## 수정 대상

`.claude-plugin/`, `README.md`, `plugin/README.md`, `docs/intro.html`, `dashboard/`.

## 안전성 체크리스트

- [x] validate --strict (plugin과 marketplace), 금지 표현 0, 문서 검사 0
- [x] 소개 페이지 화면 확인 (Chrome 헤드리스)
- [ ] 라이트 리뷰 (2단계부터 8단계까지)

## 미결정 사항

- ㉮ GitHub 반영과 판 태그는 마지막 판정요청으로
