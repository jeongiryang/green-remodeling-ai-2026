# 그린리모델링 AI 아이디어 공모전

「제6회 그린리모델링 챌린지」 대학생 해커톤 — AI 플랫폼 아이디어 부문 전용 작업 공간.

[GitHub 저장소](https://github.com/jeongiryang/green-remodeling-ai-2026) — 비공개. 신진하(`ginaginaring`)·최길웅(`choigilung`)·황왕석(`hwang030915`)에게 Write 권한 초대 발송(2026-09-29 재확인, 모두 수락 대기).

2026-09-27에 ‘공모전 계획’ 프로젝트의 관련 대화와 파일을 확인해 인계했다. 공식 자료 9개를 복사하고 SHA-256 일치를 확인했다.

| 항목 | 현재 내용 |
|---|---|
| 팀 | 정이량·신진하·최길웅 / 국립창원대학교 재학 중인 학부생 |
| 아이디어 | 미정 |
| 접수 마감 | 2026-09-30 23:59, 한국 시간 |
| 핵심 제출물 | 표지 포함 15쪽 이내 PPT 및 PDF 각 1부 + A4 2쪽 이내 요약서 + 신청·동의·서약·자격 증빙 |
| 다음 작업 | 대상 건물·이용자 문제와 데이터 확보 가능성을 기준으로 아이디어 후보 비교 |

## 하네스 사용

아이디어 탐색 → 주제 결정 → 제안서·요약서 → 검토·접수 → 결과 확인 → 본선 구현 계획 → 구현·시연 → 최종 검토로 이어진다. 현재 단계는 `ideation`이며 제품 구현은 본선 진출 후 진행한다.

```powershell
python scripts/harness.py status
python scripts/harness.py next
python scripts/harness.py check
```

Python 3.11 이상, 외부 패키지 불필요. `check`는 현재 미완료 항목을 보여준다. 지금은 후보가 없으므로 실패가 정상이다. `validate`는 하네스 구조와 원본 보존을 검사한다.

- [운영 절차·단계별 완료 기준](harness/WORKFLOW.md)
- [AI 아이디어 주제 도출·심층 검토 절차](harness/IDEATION.md)
- [후보·근거·제출 파일 기록 형식](harness/DATA.md)
- [후보 탐색 시작 요청](harness/START.md)
- [집필·비교·본선 계획 틀](harness/templates/)

아이디어 후보는 문제·그린리모델링 연계·데이터·기존 방식별 원문 근거를 연결하고, AI 입력·방법·출력·필요성과 검증 계획을 따로 작성한다. 본선에서 시연할 최소 흐름의 데이터·작업량·의존성·대체안도 확인하며, 구현 가능 상태의 후보만 선정한다. 내부 점수는 추천의 보조 자료이며 주제를 자동으로 선정하지 않는다. 현재는 후보 조사 전으로, 접수 준비 완료가 아니다.

GitHub Actions에서 구조·원본 검사와 하네스 동작 테스트를 실행한다. 실제 조사·집필은 Codex 작업으로 수행하며, 백그라운드 자동 연구나 자동 접수는 설정되어 있지 않다.

- [현재 상태와 다음 행동](STATUS.md)
- [이전 대화의 결정 사항·출처](docs/인계기록.md)
- [팀원 정보와 미수령 항목](docs/팀현황.md)
- [공식 요건·일정·평가기준](contest/요구사항.md)
- [제출 체크리스트](checks/제출체크리스트.md)
- [공식 공고·서식 사본](contest/originals/)
- [파일 출처 및 동일성 검증](contest/source_manifest.json)

[그린 AI Notion 페이지](https://app.notion.com/p/3e7b3295f8cb81da9d53f535c3cc4604) · [2026 공모전 대시보드](https://app.notion.com/p/3e7b3295f8cb8165a146d70ab4c0e8d6) · [공식 참가 안내](https://www.2026grchallenge.com/front/board/boardDetail?bo_id=1&index_no=3&curPage=1)

Notion과의 자동 동기화는 설정되어 있지 않다. 확인된 주요 진행 경과는 `AGENTS.md`의 기준에 따라 수동 갱신한다. 2026-09-28에 저장소·하네스 및 현재 주제 미정 상태를 두 페이지에 반영했다.
