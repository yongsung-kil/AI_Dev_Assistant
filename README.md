# AI_Assisted_Dev

Claude Code 플러그인 `ai-assisted-dev`를 만드는 저장소다. 기존 소스코드와 문서가 있는 프로젝트에 설치하면 Claude가 그 코드를 읽어 프로파일을 만들고, 문서화, 논문과 특허 조사, 아이디어 적용 실험, 최적화, 프로젝트 관리를 돕는다.

소개 페이지: [docs/intro.html](docs/intro.html). 작업 현황: [dashboard/index.html](dashboard/index.html). html 규격: [docs/html_guide.md](docs/html_guide.md).

## 설치

```bash
# 이 저장소를 마켓플레이스로 등록하고 설치한다 (GitHub 주소 또는 로컬 경로)
claude plugin marketplace add yongsung-kil/AI_Assisted_Dev
claude plugin install ai-assisted-dev@ai-assisted-dev

# 이 세션에만 싣기 (개발 중)
claude --plugin-dir ./plugin
```

필요한 것: Claude Code, Python 3 (PATH에 `python`), git. 자동 실행 설정(세션 시작 때 TODO 확인, md 수정 뒤 문서 검사)은 `python` 명령으로 스크립트를 부른다. macOS와 Linux처럼 `python3`만 있는 PC에서는 `python`이 `python3`를 가리키게 연결해야 오류 없이 돈다.

## 처음 쓰는 법

- 1. 프로젝트 루트에서 Claude Code를 열고 `/ai-assisted-dev:onboard`를 부른다. 코드를 읽어 `docs/profile/` 다섯 문서, `CLAUDE.md`, `_pm/`을 만든다
- 2. `docs/profile/`을 읽고 틀린 곳을 고친다. 이 문서가 다른 모든 스킬이 읽는 정본이다
- 3. `/ai-assisted-dev:dashboard`로 현황 페이지를 만든다
- 4. 필요한 스킬을 골라 쓴다 (아래 표)

## 스킬

| 갈래 | 스킬 | 하는 일 |
|---|---|---|
| 관리 | pm | `_pm/`으로 작업 등록, 진행, 완료, 판정요청 |
| 관리 | doc-check | 문서 규칙 검사 (줄표, 가운뎃점, 깨진 링크, 금지 낱말) |
| 관리 | dashboard | 작업 현황 정적 html |
| 문서화 | onboard | 프로젝트 프로파일과 뼈대 생성 |
| 문서화 | explore | 관점 4개 병렬 탐색과 교차 검증 |
| 문서화 | wiki | 결정, 시도, 자산, 기술 문서 축적 |
| 조사 | paper-search | arXiv API와 브라우저 내보내기 CSV로 논문과 특허 수집 |
| 조사 | paper-screen | 초록 기준 병렬 선별 (in, out) |
| 조사 | paper-analyze | 전문 분석 (분류표, 요약, 모듈 대응, JSON) |
| 실험 | idea-apply | 아이디어 접수, 지표 계획, 교체 지점에 붙이기, 비교, 기록 |
| 최적화 | speed-opt | 결과를 바꾸지 않는 효율화 (점검표, 한 항목씩) |
| 최적화 | robustness-check | 안정성 검사 (재현, 영향 범위, 수정, 회귀 테스트) |
| 최적화 | param-opt | 표준 라이브러리 파라미터 최적화기 |
| 절차 | plan | 병렬 계획 수립 3라운드 |
| 절차 | review | 리뷰 (관점 도출, 분석, 검증) |
| 절차 | debug | 병렬 가설 탐색 진단 |
| 절차 | test-design | 테스트 케이스 설계 |

에이전트: explorer(읽기 전용 탐색), paper-reader(논문 1편 읽기), reviewer(리뷰 작업자). 자동 실행: 세션 시작 때 `_pm/TODO.md` 확인 시각 기록과 요약 주입, md 수정 뒤 문서 검사 경고.

## 다른 플러그인과 겹칠 때

계획, 리뷰, 디버그 스킬이 다른 플러그인(예: superpowers)과 겹치면 한쪽을 끈다: `claude plugin disable <플러그인 이름>` 또는 `/plugin`에서 해당 플러그인을 끈다. 이 플러그인의 절차는 한국어와 `_pm/` 규약에 맞춰져 있다.

## 폴더

- ㉮ `plugin/`: 플러그인 본체. 이 폴더만 배포한다
- ㉯ `testbed/`: 시험장. 실제 프로젝트 사본을 두고 플러그인을 돌려 본다 (git 무시)
- ㉰ `_pm/`: 이 저장소의 작업 관리 (플러그인의 pm 스킬로 운영)
- ㉱ `_checks/`: 배포 전 검사 (금지 표현)
- ㉲ `tests/`: 스크립트 테스트
- ㉳ `docs/`: 소개 페이지, html 규격
- ㉴ `dashboard/`: 이 저장소의 현황 페이지 (dashboard 스킬 산출물)

## 개발

```bash
python -m pytest tests -q
claude plugin validate --strict plugin
claude plugin validate --strict .
python _checks/check_plugin_terms.py
python plugin/scripts/doc_check.py plugin docs _pm
```
