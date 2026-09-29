# 파라미터 최적화기 (optim/)

시뮬레이터나 평가 명령을 여러 번 돌려 지표가 가장 좋은 파라미터 조합을 찾는다. 표준 라이브러리만 쓴다.

## 사용법

```bash
python optim/optimizer.py optim/config.json              # config의 budget만큼
python optim/optimizer.py optim/config.json --budget 3   # 시험 실행
```

돌릴 때마다 `optim/log.jsonl`에 한 줄씩 남기고, 다시 돌리면 이어서 한다. 끝나면 `optim/best.json`과 결과 표를 출력한다.

## config.json

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

## 결과 읽는 법

- ㉮ `best.json`: 가장 좋은 점과 값
- ㉯ `log.jsonl`: 평가한 모든 점. `value`가 `null`이면 명령이 실패했거나 지표를 못 읽은 것
- ㉰ 출력 표: 상위 10개 점

## 탐색 방식

무작위 표본과 최량점 주변 국소 변이를 `local_ratio`로 섞는다. 같은 점은 두 번 평가하지 않는다. 더 정교한 탐색(진화, 베이지안)이 필요하면 `propose()`만 바꾸면 된다.
