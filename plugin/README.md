# ai-dev-assistant

기존 프로젝트에 설치하면 Claude가 코드를 읽어 프로파일을 만들고, 문서화, 논문과 특허 조사, 아이디어 적용 실험, 효율화와 안정성 검사, 파라미터 최적화, 작업 관리와 대시보드를 돕는다.

시작: `/ai-dev-assistant:onboard` (프로파일과 뼈대 생성) → `docs/profile/` 검토 → 필요한 스킬 사용.

스킬 17개: pm, doc-check, dashboard, onboard, explore, wiki, paper-search, paper-screen, paper-analyze, idea-apply, speed-opt, robustness-check, param-opt, plan, review, debug, test-design. 에이전트 3개: explorer, paper-reader, reviewer. 자동 실행 2개: 세션 시작 때 `_pm/TODO.md` 확인, md 수정 뒤 문서 검사 경고.

필요한 것: Python 3 (`python` 명령), git. 스크립트는 표준 라이브러리만 쓴다.
