# 최적화 도구 만들기와 쓰기 (optim/)

시뮬레이터나 평가 명령을 여러 번 돌려 지표가 가장 좋은 파라미터 조합을 찾는 도구다. 표준 라이브러리만 쓴다. 이 문서는 먼저 도구를 이 프로젝트에 맞게 만드는 순서를, 그다음 쓰는 법을 적는다.

## 1. 도구를 만드는 순서

- 1. 무엇을 좋게 할지 정한다. 지표 하나(예: 오류율, 실행 시간, 손실)와 그 방향(작을수록 좋은지)을 고른다. 지표는 평가 명령의 출력에서 정규식으로 읽을 수 있어야 한다
- 2. 무엇을 바꿀지 정한다. 파라미터마다 이름, 종류(`float`, `int`, `choice`), 범위를 적는다. 프로파일 `techniques.md`와 `replacement_points.md`에서 "값으로 조절되는 것"을 고르면 된다
- 3. 한 점을 평가하는 명령을 만든다. 파라미터 값을 명령줄 인자나 설정 파일로 받아 지표 한 줄을 출력하는 명령이다. 이미 있는 실행 명령이 인자를 받지 않으면, 설정 파일을 쓰고 실행하는 짧은 감싸기 스크립트를 `optim/`에 둔다
- 4. `config.json`에 1부터 3을 적는다 (아래 표). `--budget 3`으로 시험 실행해 지표가 읽히는지 본다. `value`가 `null`이면 명령이 실패했거나 정규식이 맞지 않는 것이다
- 5. 예산(`budget`)과 동시 실행 수(`workers`)를 정하고 돌린다. 한 점 평가 시간에 예산을 곱한 것이 전체 시간이다
- 6. 결과를 `best.json`과 상위 10개 표로 읽고, 좋은 점을 프로젝트 설정에 반영한다. 반영한 값과 근거(`log.jsonl`)는 위키의 결정 문서로 남긴다

## 2. 쓰는 법

```bash
python optim/optimizer.py optim/config.json              # config의 budget만큼
python optim/optimizer.py optim/config.json --budget 3   # 시험 실행
```

돌릴 때마다 `optim/log.jsonl`에 한 줄씩 남기고, 다시 돌리면 이어서 한다. 끝나면 `optim/best.json`과 결과 표를 출력한다.

## 3. config.json

| 항목 | 뜻 |
|---|---|
| `params[].name` | 파라미터 이름. 평가 명령의 자리표시 `{이름}`과 같아야 한다 |
| `params[].type` | `float`(min, max, step), `int`(min, max), `choice`(values) |
| `evaluate.command` | 한 점을 평가하는 명령. `{이름}` 자리에 값이 들어간다 |
| `evaluate.metric_regex` | 명령 출력에서 지표를 읽는 정규식. 첫 괄호가 값 |
| `evaluate.minimize` | true면 작을수록 좋음 |
| `evaluate.timeout_seconds` | 한 점 평가의 최대 시간 |
| `search.budget` | 평가할 점의 수 (누적) |
| `search.workers` | 동시에 돌릴 평가 수 |
| `search.seed` | 난수 seed (재현용) |
| `search.local_ratio` | 최량점 주변을 조금 바꾼 후보의 비율 (나머지는 무작위) |

## 4. 결과 읽는 법

- ㉮ `best.json`: 가장 좋은 점과 값
- ㉯ `log.jsonl`: 평가한 모든 점. `value`가 `null`이면 명령이 실패했거나 지표를 못 읽은 것
- ㉰ 출력 표: 상위 10개 점

## 5. 탐색 방식과 넓히기

무작위 표본과 최량점 주변 국소 변이를 `local_ratio`로 섞는다. 같은 점은 두 번 평가하지 않는다. 더 정교한 탐색(진화, 베이지안)이 필요하면 `optimizer.py`의 `propose()`만 바꾸면 된다. 파라미터가 표(행렬)처럼 여럿이 묶여 있으면, 표를 파일로 쓰는 감싸기 스크립트를 두고 `choice`나 `int` 파라미터 몇 개로 표의 모양을 고르게 하는 편이 낫다.
