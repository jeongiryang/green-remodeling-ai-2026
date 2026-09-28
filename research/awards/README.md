# 2023–2025 그린리모델링 챌린지 수상작 조사

읽기 시작: [조사 보고서](수상작조사_2023-2025.md), [전체 목록](전체목록.md).

| 파일 | 내용 |
|---|---|
| official-awards.json / .csv | 공식 공개 아카이브 102건, 20개 화면, 확인 시각·해시·링크 |
| supplemental-awards.json | 대학·연구실에서 추가 확인한 입선 3건 |
| review-notes.json | 설계 18건·아이디어 6건·정책 5건의 요약·해석 제한 |
| artifact-checks.json | 작품별 대표 원본 URL 응답, 문서 해시·추출 결과 |
| github-search.json | 공개 저장소 검색 10개 질의의 결과 스냅샷 |
| github-readme-checks.json | 관련 저장소의 README·루트 목록 확인 결과 |
| qr-links.json | 설계 패널 QR에서 얻은 외부 링크와 접근 결과 |
| cache/ | 원문·추출본·렌더링·임시 의존성. Git 제외 |

공식 메타데이터 수집은 `python research/awards/crawl_archive.py`로 실행한다. 현재 사이트의 HTML 구조에 맞춘 추출기이므로 사이트가 바뀌면 수집 개수·표본을 다시 대조해야 한다. 실행 시 JSON/CSV 스냅샷이 갱신된다.

대표 원본 검사와 문서 추출은 `python research/awards/inspect_artifacts.py`로 실행한다. Python의 `requests`, `pypdf`, `olefile`이 필요하다. 이번 조사에서는 임시 라이브러리를 `cache/deps`에 두었으므로 다른 환경에서는 별도 준비가 필요하다. 영상·음원·이미지는 스트림 앞부분만 검사한다. HWP 추출은 본문 문자열 확인용이며 한글 편집기의 화면 검수나 완전한 HWP 해석기가 아니다.

수집된 JSON으로 전체 목록을 만드는 명령은 `python research/awards/build_catalog.py`다. 이 명령은 네트워크 없이 목록을 다시 만든다. 외부 보완 기록과 검토 메모는 근거를 읽고 수동 작성했다. 과거 GitHub 검색은 현재 공개 상태와 달라질 수 있으며 비공개·삭제 자료는 범위 밖이다.

원본을 다운로드했다고 재사용 권한이 생기는 것은 아니다. 제출자료에는 필요한 범위의 요약과 출처를 사용한다. 원문에 포함된 민감한 인적사항은 옮기지 않는다.
