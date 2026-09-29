# AI_Assisted_Dev

Claude Code 플러그인 `ai-assisted-dev`를 만드는 저장소다. 기존 소스코드와 문서가 있는 프로젝트에 설치하면 Claude가 그 코드를 읽어 프로파일을 만들고, 문서화, 논문과 특허 조사, 아이디어 적용 실험, 최적화, 프로젝트 관리를 돕는다.

## 폴더

- ㉮ `plugin/`: 플러그인 본체. 이 폴더만 배포한다
- ㉯ `testbed/`: 시험장. 실제 프로젝트 사본을 두고 플러그인을 돌려 본다 (git 무시)
- ㉰ `_pm/`: 이 저장소의 작업 관리 (플러그인의 pm 스킬로 운영)
- ㉱ `_checks/`: 배포 전 검사 (금지 표현)
- ㉲ `tests/`: 스크립트 테스트

## 로컬에서 써 보기

```bash
claude --plugin-dir ./plugin          # 이 세션에만 플러그인을 싣는다
claude plugin validate --strict plugin
python -m pytest tests -q
```

필요한 것: Claude Code, Python 3 (PATH에 `python`), git.
