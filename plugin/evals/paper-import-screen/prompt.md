---
name: paper-import-screen
description: 내보내기 CSV를 들여오고 배치를 만들어 판정을 기록하는 흐름이 paper-search와 paper-screen 스킬로 도는지
runs: 1
max_turns: 40
---
먼저 다음을 만들어 주세요.

- `docs/profile/overview.md`: "# 프로젝트 개요" 아래 "## 1. 한 문장 정체성"에 "문자열을 반복 글자 쌍으로 줄이는 압축 도구"라고 적어 주세요.
- `docs/profile/techniques.md`: "# 이미 가진 기법" 아래 표 한 줄에 "run-length 부호화".
- `export.csv`: 열은 `"Document Title","Publication Year","Abstract","DOI"`이고 두 줄. 하나는 "Adaptive run-length coding for text" (2024, 초록: 반복 길이에 따라 부호 길이를 바꾸는 방법, DOI 10.1/a), 다른 하나는 "A survey of image codecs" (2023, 초록: 이미지 코덱 서베이, DOI 10.1/b).

그 다음 paper-search 스킬로 `export.csv`를 들여오고, paper-screen 스킬로 선별을 끝까지(기록까지) 진행해 주세요. 기준서의 자리표시는 프로파일로 채워 주세요. 중간에 사용자 확인을 기다리지 마세요.
