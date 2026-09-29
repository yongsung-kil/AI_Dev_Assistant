# tasks/ 폴더 규칙 (삭제 금지)

TODO에 작업을 추가할 때 `_pm/tasks/{YYYYMMDD}_{작업명}/` 폴더를 만들고 상세 문서를 쓴다.

- ㉮ `{YYYYMMDD}_{작업명}.md`: 메인 태스크 문서 (양식은 `_template/task.md`)
- ㉯ 관련 분석과 메모는 같은 폴더에 둔다
- ㉰ TODO 항목에 `상세: _pm/tasks/{폴더}/` 링크를 단다
- ㉱ 사용자 결정이 필요하면 `판정요청_{주제}_{YYMMDD}.md`를 같은 폴더에 둔다 (양식은 `_template/decision_request.md`)
- ㉲ 완료하면 폴더를 `_pm/done/`으로 옮기고 `DONE.md` 맨 위에 요약을 더한다
- ㉳ 문서 정리처럼 단순한 작업은 tasks 문서 없이 TODO에만 적는다
