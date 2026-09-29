---
name: param-opt
description: 시뮬레이터나 평가 명령을 여러 번 돌려 성능 지표가 가장 좋은 파라미터 조합을 찾는 최적화기를 프로젝트에 만들고 돌린다. 사용자가 "파라미터 최적화", "튜닝", "최적값 찾아", "param-opt"라고 하면 쓴다
---

# 파라미터 최적화

표준 라이브러리만 쓰는 최적화기 뼈대(`optim/`)를 만들고 프로젝트의 평가 명령에 맞춘다. 스크립트는 이 스킬의 기준 폴더에서 `../../scripts/`에 있다.

## 절차

- 1. 프로파일 `overview.md`의 성능 지표와 평가 방법(명령)을 확인한다. 없으면 사용자에게 평가 명령과 지표가 출력에 어떻게 나오는지 묻는다
- 2. `python "<이 스킬의 기준 폴더>/../../scripts/param_opt_init.py" .`로 `optim/config.json`, `optim/optimizer.py`, `optim/README.md`를 만든다
- 3. `config.json`을 채운다. `params`에 파라미터 이름, 형(float는 min, max, step / int는 min, max / choice는 values), `evaluate.command`에 평가 명령(값이 들어갈 자리는 `{이름}`), `evaluate.metric_regex`에 출력에서 지표를 읽는 정규식(첫 괄호가 값), `minimize`, `timeout_seconds`. `search`에 budget, workers(PC 코어 수 안에서), seed, local_ratio
- 4. 시험 실행 `python optim/optimizer.py optim/config.json --budget 3`. 실패(`value: null`)가 나오면 명령과 정규식을 고친다
- 5. 본 실행. `log.jsonl`에 누적되고 다시 돌리면 이어서 한다. 끝나면 `best.json`과 상위 10개 표가 나온다
- 6. 기록. 결과 표와 최적값, 탐색 조건(예산, seed)을 프로젝트 README나 아이디어 README에 적고, 실험로그에 환경과 인사이트를 더한다

## 규칙

- ㉮ 평가 명령은 결정적이어야 한다 (seed를 고정). 아니면 같은 점을 여러 번 평가해 평균을 지표로 내는 감싸는 스크립트를 둔다
- ㉯ 파라미터 공간은 작게 시작해 넓힌다. 한 번에 다섯 개 안팎
- ㉰ 더 정교한 탐색이 필요하면 `optimizer.py`의 후보 생성 부분만 바꾼다 (평가와 기록은 그대로)
