---
name: param-opt-scaffold
description: 평가 명령이 있는 프로젝트에서 param-opt 스킬이 최적화기 뼈대를 만들고 시험 실행까지 하는지
runs: 1
max_turns: 25
---
먼저 `sim.py`를 만들어 주세요. 인자 `--alpha`(실수)를 받아 `score=` 뒤에 `(alpha - 0.7)`의 제곱을 출력합니다.

그 다음 param-opt 스킬로 최적화기를 만들고, 파라미터 alpha(0.0에서 1.0, 간격 0.05)와 평가 명령 `python sim.py --alpha {alpha}`를 설정한 뒤, `--budget 5`로 시험 실행까지 해 주세요.
