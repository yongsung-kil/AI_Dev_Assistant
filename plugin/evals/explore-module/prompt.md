---
name: explore-module
description: 작은 모듈을 explore 스킬로 탐색시키면 컴포넌트 표와 흐름이 든 탐색 문서가 나오는지
runs: 1
max_turns: 40
---
먼저 다음 파일 두 개를 만들어 주세요.

`src/queue.py`: 고정 길이 순환 버퍼 `RingQueue` 클래스 (push, pop, is_full, is_empty).
`src/worker.py`: RingQueue에서 항목을 꺼내 처리하고 처리 수를 세는 `Worker` 클래스.

그 다음 `src/`를 explore 스킬로 탐색해 이해 문서를 만들어 주세요. 목적은 "수정하기 위한 이해"입니다. 중간에 사용자 확인을 기다리지 말고 끝까지 진행해 주세요.
