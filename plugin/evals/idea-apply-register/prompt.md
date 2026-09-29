---
name: idea-apply-register
description: 아이디어 접수를 시키면 idea-apply 스킬이 현황표 행과 폴더와 README 요약을 만드는지
runs: 1
max_turns: 25
---
먼저 `docs/profile/replacement_points.md`를 만들어 주세요. 내용: "# 교체 지점", "## 1. 교체 단위" 아래에 "기본 클래스 Codec을 상속해 encode 메서드 하나를 재정의한다", "## 2. 교체 지점 표" 아래에 표 한 줄(`| 부호화 규칙 | 메서드 재정의 | src/codec.py:12 | 문자열 | 쌍 목록 | 있음 |`).

그 다음 idea-apply 스킬로 아이디어 1번 "run_length_variant"(출처: 제안)를 접수하고, README의 📌 요약 네 가지를 채워 주세요 (제안 내용: 연속 글자 수가 1인 경우는 쌍을 만들지 않고 글자만 남겨 출력 길이를 줄인다). 실험은 돌리지 마세요.
