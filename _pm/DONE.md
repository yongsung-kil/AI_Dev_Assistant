# DONE

> 완료 이력. 최근 것이 위.

### 2026-09-30 플러그인 1단계: 저장소 뼈대, pm 스킬, doc-check 스킬
플러그인 뼈대와 자기 관리 도구를 만들고 시험장 실제 실행과 검토자 검토로 확인했다
- **배경**: 다른 모든 스킬이 기대는 작업 관리와 문서 검사부터 플러그인으로 만들어 자기 관리에 썼다
- **변경**: plugin.json, pm과 doc-check 스킬, 세션 시작과 md 수정 뒤 자동 실행, 금지 표현 검사, 검사 사례 2건, 최종 검토의 지적 반영
- **파일**: plugin/skills/{pm,doc-check}, plugin/scripts/{pm_stamp,pm_init,doc_check,doc_check_hook}.py, plugin/hooks/hooks.json, _checks/, tests/
