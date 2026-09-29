# CLAUDE.md: 이 저장소에서 작업할 때의 규칙

- ㉮ 대화는 한국어 존댓말. 문서는 한국어
- ㉯ 문장 규칙: 줄표(U+2014)와 가운뎃점(U+00B7) 금지. 나열은 ㉮㉯㉰와 ㉠㉡, 주소를 받는 갈래는 `- 1.`. 수리는 덧대기가 아니라 다시 쓰기. 규칙은 긍정문
- ㉰ `plugin/` 안에는 회사 이름, 사업 도메인 이름, 입력 파일 이름을 적지 않는다. 예시는 중립 소재를 쓴다. 커밋 전 `python _checks/check_plugin_terms.py`로 0건을 확인한다
- ㉱ 스크립트는 Python 3 표준 라이브러리만 쓴다. 테스트를 먼저 쓰고 `python -m pytest tests -q`로 확인한다
- ㉲ 커밋 전 `claude plugin validate --strict plugin`을 통과시킨다
- ㉳ 작업 관리는 `_pm/`이며 절차는 `plugin/skills/pm/SKILL.md`를 그대로 따른다 (자기 관리)
- ㉴ 개인 로컬 절대 경로와 계정 정보를 어느 파일에도 적지 않는다
