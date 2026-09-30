# DONE

> 완료 이력. 최근 것이 위.

### 2026-09-30 논문 탐색기 페이지, 사이드바 묶음 이름 변경, 온보딩 사용법 문서, 최적화 도구 안내
papers.db 기반 논문 탐색기(검색어, 연도, 갈래 체크박스), 묶음 이름을 외부 기술문서와 내부 기술문서로, docs/usage.md 양식, 최적화 도구 만드는 순서, 제목과 굵은 글의 색
- **배경**: 사용자가 기존 논문 분석 사이트의 검색 기능을 대시보드 안에 같은 틀로 넣고, 위키(내부)와 논문(외부)의 경계를 출처로 나누고, 온보딩에 플러그인 사용법을, 최적화에 도구 제작 방법을 두자고 했다. 페이지가 건조하다는 지적으로 제목과 굵은 글에 색을 넣었다
- **변경**: collect_papers(상태 요약), papers_rows와 facet_table과 papers_body(탐색기 자료와 갈래, config facet_labels), explorer_nodes(논문과 특허 탐색기 항목), FRAME_FULL과 FRAME_LIGHT(분석 문서는 사이드바 없는 틀, 검색 색인에서 본문 제외), MAX_FOLDER_ITEMS 상한, 묶음 기본 이름과 폴더 이름표, templates/docs/usage.md, param_opt README를 제작 순서 중심으로, 제목 색 토큰(h1, h2, h3, strong)
- **파일**: plugin/scripts/render_dashboard.py, plugin/scripts/collect_status.py, plugin/templates/docs/usage.md, plugin/templates/param_opt/README.md, plugin/templates/dashboard/config.json, plugin/skills/dashboard/SKILL.md, plugin/skills/onboard/SKILL.md, docs/html_guide.md, tests/test_papers_page.py, tests/test_dashboard_nav.py, tests/test_onboard_init.py

### 2026-09-30 대시보드 사이드바를 일 갈래 묶음으로 바꾸고 작업 보드와 변경 이력 페이지를 더함
사이드바는 config의 묶음(온보딩, 작업 관리, 논문, 아이디어 적용, 최적화, 위키)과 그 안의 폴더로 단계별 접기, 첫 화면은 계획, 진행 중, 완료 보드, 완료 작업 단위의 변경 이력 페이지
- **배경**: 사용자가 참고 사이트(Storyblok 사이드바 단계, Greptile과 Railway 문서의 접기와 차례, Railway 로드맵 보드, Handsontable 변경 이력)처럼 바꾸자고 했고, 옛 사이드바는 대시보드 요약 칸을 그대로 옮긴 꼴이라 갈래가 맞지 않았다
- **변경**: build_nav(config 기반 트리, 대표 문서 규칙, 같은 이름 폴더 구분), nav-l1부터 nav-l3 글자 단계, 사이드바 전체 접기와 테마 전환(브라우저에 기억), 오른쪽 차례의 세로 선 표시, 작업 보드 세 칸과 결정 대기 목록, changelog.html(기간과 달 탭 필터), DONE 파서의 상세 줄 수집과 제목 앞 줄표 제거, 기본 문서 폴더에 ideas, papers, optim 추가, 소개 페이지도 같은 틀로
- **파일**: plugin/scripts/render_dashboard.py, plugin/scripts/collect_status.py, plugin/templates/dashboard/config.json, plugin/skills/dashboard/SKILL.md, docs/html_guide.md, docs/intro.html, tests/test_dashboard_nav.py, tests/test_collect_status.py

### 2026-09-30 플러그인 1단계: 저장소 뼈대, pm 스킬, doc-check 스킬
플러그인 뼈대와 자기 관리 도구를 만들고 시험장 실제 실행과 검토자 검토로 확인했다
- **배경**: 다른 모든 스킬이 기대는 작업 관리와 문서 검사부터 플러그인으로 만들어 자기 관리에 썼다
- **변경**: plugin.json, pm과 doc-check 스킬, 세션 시작과 md 수정 뒤 자동 실행, 금지 표현 검사, 검사 사례 2건, 최종 검토의 지적 반영
- **파일**: plugin/skills/{pm,doc-check}, plugin/scripts/{pm_stamp,pm_init,doc_check,doc_check_hook}.py, plugin/hooks/hooks.json, _checks/, tests/

### 2026-09-30 플러그인 2단계: onboard, explore, wiki 스킬과 프로젝트 프로파일
프로파일 양식 6편과 onboard_init, explorer 에이전트, explore와 onboard와 wiki 스킬(tech 갈래), 시험장에서 onboard 실제 실행(45분)으로 프로파일 다섯 문서가 근거와 함께 채워짐을 확인
- **배경**: 다른 모든 스킬이 코드 대신 읽을 프로파일과 그것을 만드는 절차가 먼저 필요했다
- **변경**: 프로파일 양식 6편과 onboard_init, explorer 에이전트, explore와 onboard와 wiki 스킬(tech 갈래), 시험장에서 onboard 실제 실행(45분)으로 프로파일 다섯 문서가 근거와 함께 채워짐을 확인
- **파일**: plugin/skills/{onboard,explore,wiki}, plugin/agents/explorer.md, plugin/scripts/{onboard_init,wiki_init}.py, plugin/templates/{profile,_wiki,CLAUDE.md,docs}

### 2026-09-30 플러그인 3단계: 대시보드와 HTML 작성 가이드
표준 라이브러리 md 변환기, 현황 수집(status.json), 정적 대시보드(사이드바 접기, 검색, 오른쪽 차례, 진행 중 카드, 문서 지도, 깨진 링크 검사), html_guide.md, 자기 적용과 시험장 적용
- **배경**: 작업 현황을 한 화면에 보이고 md가 정본인 문서를 html로 내는 틀이 필요했다
- **변경**: 표준 라이브러리 md 변환기, 현황 수집(status.json), 정적 대시보드(사이드바 접기, 검색, 오른쪽 차례, 진행 중 카드, 문서 지도, 깨진 링크 검사), html_guide.md, 자기 적용과 시험장 적용
- **파일**: plugin/scripts/{md_to_html,collect_status,render_dashboard}.py, plugin/skills/dashboard, docs/html_guide.md, dashboard/

### 2026-09-30 플러그인 4단계: idea-apply, speed-opt, robustness-check, param-opt
아이디어 접수 스크립트와 양식, 효율화와 안정성 점검표 양식(항목 풀), 표준 라이브러리 파라미터 최적화기, 스킬 넷
- **배경**: 논문 기법을 붙여 실험하고, 결과를 바꾸지 않는 효율화와 경계 조건 안정성을 점검하고, 파라미터를 자동으로 고르는 절차를 옮겼다
- **변경**: 아이디어 접수 스크립트와 양식, 효율화와 안정성 점검표 양식(항목 풀), 표준 라이브러리 파라미터 최적화기, 스킬 넷
- **파일**: plugin/scripts/{idea_init,checklist_init,param_opt_init}.py, plugin/templates/{idea,checklists,param_opt}, plugin/skills/{idea-apply,speed-opt,robustness-check,param-opt}

### 2026-09-30 플러그인 5단계: paper-search, paper-screen, paper-analyze
SQLite 논문 db, arXiv API와 내보내기 CSV 들여오기, 배치 선별과 검증과 기록, 전문 분석의 대상 목록과 JSON 기록과 카탈로그, 양식 넷, paper-reader 에이전트, 스킬 셋
- **배경**: 논문 아카이브의 선별과 분석 절차를 도메인 낱말 없이 일반화했다. 검색은 공개 API와 브라우저 내보내기 두 통로
- **변경**: SQLite 논문 db, arXiv API와 내보내기 CSV 들여오기, 배치 선별과 검증과 기록, 전문 분석의 대상 목록과 JSON 기록과 카탈로그, 양식 넷, paper-reader 에이전트, 스킬 셋
- **파일**: plugin/scripts/{papers_db,paper_search,paper_screen,paper_analyze}.py, plugin/templates/papers, plugin/agents/paper-reader.md, plugin/skills/paper-*

### 2026-09-30 플러그인 6단계: plan, review, debug, test-design 스킬 이관
홈 폴더의 병렬 에이전트 절차 넷을 스킬로 옮기고 reviewer 에이전트를 둠. 저장은 메인이, 팀 리더 역할도 메인이 맡는 꼴로 바꿈
- **배경**: 계획, 리뷰, 디버그, 테스트 설계 절차를 플러그인 자체 스킬로 두기로 결정했다
- **변경**: 홈 폴더의 병렬 에이전트 절차 넷을 스킬로 옮기고 reviewer 에이전트를 둠. 저장은 메인이, 팀 리더 역할도 메인이 맡는 꼴로 바꿈
- **파일**: plugin/skills/{plan,review,debug,test-design}, plugin/agents/reviewer.md

### 2026-09-30 플러그인 7단계 배포와 8단계 소개 페이지
마켓플레이스 파일과 설치 안내, plugin/README, 소개 페이지 docs/intro.html(카드, 다섯 단계, 흐름, 스킬 접힘, 자주 묻는 것). 2단계부터 8단계 라이트 리뷰의 Important 7건 반영
- **배경**: 남에게 주는 물건이라 설치 경로와 소개가 필요했다
- **변경**: 마켓플레이스 파일과 설치 안내, plugin/README, 소개 페이지 docs/intro.html(카드, 다섯 단계, 흐름, 스킬 접힘, 자주 묻는 것). 2단계부터 8단계 라이트 리뷰의 Important 7건 반영
- **파일**: .claude-plugin/marketplace.json, README.md, plugin/README.md, docs/intro.html
