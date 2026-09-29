---
name: paper-screen
description: db에 쌓인 논문을 초록만 보고 기준서대로 포함(in)과 제외(out)로 병렬 판정하고 기록한다. 사용자가 "논문 선별", "1차 선별", "in out 판정", "paper-screen"이라고 하면 쓴다
---

# 초록 선별 (1차)

판단 규칙은 `papers/criteria/selection_criteria.md`, 판단 실행은 paper-reader 에이전트, db 입출력은 `../../scripts/paper_screen.py`(이 스킬의 기준 폴더 기준)다. 메인은 초록을 읽지 않는다 (파일로만 나눈다).

## 절차 (한 청크)

- 1. 기준서 확정. `papers/criteria/selection_criteria.md`에 자리표시(중괄호)가 남아 있으면 프로파일(`overview.md`의 문제 정의, `structure.md`의 부품 사슬, `techniques.md`의 보유 기법)로 채우고 사용자 검토를 받는다 (자동 진행이면 채운 내용을 보고만 한다)
- 2. 배치 분할. `python "<이 스킬의 기준 폴더>/../../scripts/paper_screen.py" batch -n 100 --per 10 [--year 연도] [--tag 이름]`. 출력의 `RUN_DIR`과 에이전트 수 N을 기억한다. 0편이면 선별 완료를 보고하고 끝낸다
- 3. 병렬 판정. `ai-assisted-dev:paper-reader` 에이전트 N명을 background로 부른다. 각자에게: 기준서 경로, 자기 파일 `RUN_DIR/agent_NN.json` 경로, 반환 꼴(`judgments`: 담당 논문 전부의 `{id, decision, reason}`, `criteria_suggestions`: 문장 목록). 돌아온 것을 모아 `RUN_DIR/judgments.json`에 저장한다
- 4. 검증. `paper_screen.py verify RUN_DIR`. 오류(없는 id, 배치 밖 id, decision 값 오류, 중복)가 있으면 기록하지 않고 보고한다. 누락은 다음 청크에서 다시 나오므로 보고만 한다
- 5. 기록. in과 out 수와 표본 몇 건을 보고하고 사용자 확인 뒤 `paper_screen.py apply RUN_DIR/judgments.json` (자동 진행이면 바로)
- 6. 기준 변경 제안은 모아서 최종 보고에 적는다. 기준서 본문은 사용자가 고친다
- 7. `paper_screen.py stats`로 현황을 보고한다. 남은 것이 있으면 다음 청크로

## 에이전트에게 주는 지시

```
당신은 논문 1차 선별자다. {프로젝트의 문제}에 적용 가능한지 초록만 보고 in/out을 판정한다.
1) {기준서 경로}를 읽어 포함과 제외 갈래와 판단 절차를 익힌다.
2) {agent_NN.json 경로}를 읽는다 (담당 논문 목록: id, title, year, venue, abstract).
3) 각 논문을 초록만 보고 판정한다. 애매하면 in으로 살리고 reason에 근거를 남긴다 (전문 분석에서 다시 본다).
반환: judgments (담당 논문 전부, [{id, decision: "in"|"out", reason: 한 줄}]), criteria_suggestions (기준을 바꿀 만한 것만, 없으면 빈 목록).
```
