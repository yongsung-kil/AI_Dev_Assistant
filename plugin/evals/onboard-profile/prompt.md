---
name: onboard-profile
description: 작은 파이썬 프로젝트에서 onboard를 시키면 프로파일 다섯 문서와 CLAUDE.md, _pm/이 생기는지
runs: 1
max_turns: 40
---
먼저 다음 파일 두 개를 만들어 주세요.

`src/codec.py`: 문자열을 받아 연속된 같은 글자를 (글자, 개수) 쌍으로 줄이는 `compress(text)` 함수와 그것을 되돌리는 `expand(pairs)` 함수.
`run.py`: 표준 입력 한 줄을 읽어 compress한 결과를 출력하는 진입점.

그 다음 이 프로젝트를 onboard 스킬로 온보딩해 주세요. 중간에 사용자 확인을 기다리지 말고 끝까지 진행해 주세요.
