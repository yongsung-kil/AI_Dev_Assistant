# AI-Dev-Assistant 사용법

> 처음 온 사람과 쓰는 법을 잊은 사람이 맨 먼저 여는 문서. (온보딩 스킬이 괄호 자리를 채우고 이 줄을 지운다)

## 프로젝트 소개

- ㉮ 이름: (프로젝트 이름)
- ㉯ 하는 일: (한 문장. 프로파일 `overview.md`의 첫 문장과 같게)
- ㉰ 자세한 설명은 프로파일 다섯 문서에: `docs/profile/overview.md`(개요), `structure.md`(구조), `replacement_points.md`(교체 지점), `techniques.md`(보유 기법), `constraints.md`(제약)

## 폴더 구성

| 폴더 | 내용 | 여는 스킬 |
|---|---|---|
| `docs/profile/` | 프로젝트 프로파일 다섯 문서. 모든 스킬이 읽는 정본 | onboard |
| `_pm/` | 작업 목록(TODO), 완료 이력(DONE), 진행 중 작업 문서, 판정요청 | pm |
| `papers/` | 논문과 특허의 수집 DB, 선별 기준, 분석 문서 | paper-search, paper-screen, paper-analyze |
| `ideas/` | 논문 아이디어의 현황표와 아이디어별 실험 기록 | idea-apply |
| `docs/speed_opt/`, `docs/robustness/` | 속도 최적화와 안정성 검사 점검표 | speed-opt, robustness-check |
| `optim/` | 파라미터 최적화 도구와 실행 기록 | param-opt |
| `_wiki/` | 결정, 시도, 재사용 패턴, 기술 문서 (프로젝트 안에서 나온 지식) | wiki |
| `dashboard/` | 위 전부를 한 화면에 보이는 정적 html | dashboard |

(실제로 있는 폴더만 남기고, 없는 줄은 지운다)

## 사용 방법

- 1. 지금 무엇을 하고 있는지 보기: `dashboard/index.html`을 연다 (없으면 `/ai-dev-assistant:dashboard`). 작업 보드, 결정 대기, 최근 완료가 첫 화면에 있다
- 2. 새 작업 시작: Claude Code에서 `/ai-dev-assistant:pm`으로 작업을 등록한다. 세션을 열면 `_pm/TODO.md` 요약이 자동으로 들어온다
- 3. 코드 한 부분 이해하기: `/ai-dev-assistant:explore` 뒤에 모듈이나 질문을 적는다
- 4. 논문 찾기와 읽기: `/ai-dev-assistant:paper-search` (수집), `paper-screen` (선별), `paper-analyze` (분석). 결과는 대시보드의 논문 탐색기에서 검색한다
- 5. 논문 기법을 코드에 붙여 보기: `/ai-dev-assistant:idea-apply`
- 6. 빠르게 또는 튼튼하게 만들기: `/ai-dev-assistant:speed-opt`, `/ai-dev-assistant:robustness-check`. 파라미터를 자동으로 찾으려면 `/ai-dev-assistant:param-opt`
- 7. 배운 것 남기기: `/ai-dev-assistant:wiki`가 결정, 시도, 재사용 패턴, 기술 문서를 `_wiki/`에 쌓는다

## 실행 명령

- ㉮ 빌드: (명령 또는 "없음")
- ㉯ 실행: (명령)
- ㉰ 테스트: (명령 또는 "없음")

## 규칙

- ㉮ 문서는 md로 쓰고 줄표(U+2014)와 가운뎃점(U+00B7)을 쓰지 않는다. md를 고치면 문서 검사가 자동으로 돈다
- ㉯ 프로파일이 코드와 어긋나면 프로파일을 먼저 고친다. 프로파일은 스킬들이 읽는 정본이다
- ㉰ 결정이 필요한 것은 판정요청 문서로 모아 한 번에 묻는다 (pm 스킬)
