# 데이터 작성 예시

아래 예시는 형식 설명이다. 실제 데이터 파일에는 빈 목록만 넣어두었으며 아래 문구를 근거로 사용하지 않는다.

## 출처 — research/sources.json

```json
{"sources":[{"id":"S001","title":"실제로 읽은 원문 제목","url":"https://기관/원문","checked_on":"2026-09-27","locator":"쪽·절·표·필드 위치","finding":"원문에서 확인한 사실과 한계"}]}
```

URL이 있다는 이유만으로 확인 완료로 취급하지 않는다. 데이터는 제공기관, 기간·지역·단위·컬럼, 실제 다운로드·인증 필요 여부, 라이선스와 결측·제약까지 조사 메모에 남긴다. 동적인 정보는 사용 시점에 다시 조회한다.

## 후보 — research/candidates.json

```json
{"candidates":[{
  "id":"I001","title":"후보명","building":"노후 건물 유형",
  "user":"주 사용자와 행동","problem":"구체적 문제",
  "problem_evidence":"확인한 사실·출처와 아직 검증하지 못한 가설",
  "green_link":"단열·창호·설비·운영·사후관리와의 연결",
  "ai_role":"AI 역할의 한 문장 요약",
  "ai_input":"AI에 넣을 실제 필드와 입력 주체",
  "ai_method":"분류·추출·검색결합·추천 등 처리 방법과 실패 시 동작",
  "ai_output":"사용자에게 보이는 결과와 다음 행동",
  "ai_necessity":"규칙·검색·계산 방식보다 AI가 필요한 이유",
  "data_plan":"사용할 데이터·확보 상태·부족한 데이터와 대안",
  "data_access":"실제 열어본 자료·접근 조건·권한·결측과 대체 입력",
  "baseline":"AI 없이 하는 방법과 비교·검증 방법",
  "verification":"샘플·기준선·평가 방식·성공 및 실패 판정",
  "differentiation":"실제 기존 서비스와의 차이",
  "user_flow":"이용자가 하는 행동→AI 출력→결정의 최소 흐름",
  "preliminary_visual":"예선 제안서에 넣을 한 화면·흐름도의 구체 내용",
  "finalist_scope":"본선에서 구현할 최소 이용 흐름",
  "prototype_plan":{
    "readiness":"ready",
    "core_flow":"사용자 입력→AI 결과→사용자 확인의 시연 가능한 한 경로",
    "data_mode":"실데이터/동의받은 입력/샘플 중 무엇을 어떻게 확보하는지",
    "components":"화면·AI·저장·규칙검사 등 필요한 최소 구성요소",
    "dependencies":"API 키·권한·장비·외부 승인·팀 기술 등 의존성",
    "effort_estimate":"팀 가용시간을 고려한 예상 작업량과 가정",
    "fallback":"데이터·모델·네트워크가 안 될 때의 대체 시연",
    "acceptance_test":"본선 시연이 성공했다고 판정할 재현 가능한 입력과 기대 출력"
  },
  "risks":"한계·오류 시 처리·외부 의존성",
  "source_ids":["S001"],
  "evidence":{"problem":["S001"],"green_link":["S001"],"data":["S001"],"alternative":["S001"]},
  "scores":{
    "problem":{"score":0,"reason":"근거에 따른 내부 평가"},
    "fit":{"score":0,"reason":"근거"},
    "originality":{"score":0,"reason":"근거"},
    "feasibility":{"score":0,"reason":"근거"},
    "development":{"score":0,"reason":"근거"}
  }
}]}
```

위 S001 반복은 **형식 예시**일 뿐이다. 실제 후보에서는 `evidence`의 문제·그린리모델링 연결·데이터·기존 방식별로 원문에서 해당 내용을 확인한 출처 ID만 넣는다. `source_ids`에도 해당 ID가 있어야 한다. `harness/IDEATION.md`에 조사·반대 검토 절차가 있다.

`prototype_plan.readiness`는 `ready`(현재 확인한 자료·팀 역량·시간으로 최소 시연 가능), `conditional`(특정 접근권한·장비·팀 역량 확인 필요), `blocked`(핵심 의존성 없음) 중 하나다. 이는 **팀의 내부 판단**이지 구현 완료나 본선 합격 보장이 아니다. `conditional`/`blocked` 후보도 비교할 수 있지만, 선정하려면 걸림돌을 해결하고 근거를 갱신해 `ready`로 바꿔야 한다. `effort_estimate`는 사람·시간 가정을 밝힌 추정치다.

각 점수는 0~5. `status`는 공식 예선 가중치로 100점 환산한 내부 비교값을 표시한다. 최고점 자동 선정은 하지 않는다. `research/comparison.md`에 비교 이유·탈락 사유·추천과 불확실성을 설명한다. 결정 후 state의 `selected_candidate`와 `research/decision.md`에 근거·결정 주체·날짜를 기록한다.

## 주장 — research/claims.json

```json
{"claims":[{"id":"C001","text":"문서에 사용할 주장","kind":"fact","source_ids":["S001"],"method_path":"","used_in":"제안서 2쪽 / 요약서 제안배경"}]}
```

kind는 `fact`, `estimate`, `target`, `hypothesis`. fact·estimate는 출처가 필요하고 estimate는 계산식·가정·재현 방법을 적은 method_path가 필요하다. target·hypothesis는 목표·가설임을 문서에서 표시한다. 자료가 없으면 사실로 쓰지 않는다.

## 예선 제출 묶음 — submissions/preliminary/manifest.json

```json
{"guardian_required":false,"files":[
  {"kind":"proposal_pptx","path":"deliverables/submission/proposal.pptx","sha256":"파일 해시","opened":true},
  {"kind":"proposal_pdf","path":"deliverables/submission/proposal.pdf","sha256":"파일 해시","pages":15,"opened":true},
  {"kind":"summary","path":"deliverables/submission/summary.pdf","sha256":"파일 해시","pages":2,"opened":true},
  {"kind":"application","path":"private/application.pdf","sha256":"파일 해시","opened":true},
  {"kind":"pledge","path":"private/pledge.pdf","sha256":"파일 해시","opened":true},
  {"kind":"eligibility","path":"private/member1.pdf","sha256":"파일 해시","member_id":"member1","opened":true}
]}
```

eligibility는 팀원별 하나씩 등록한다. member_id는 `member1`~`member3`처럼 개인정보 없는 식별자. 전원 서명은 검토자가 확인한다. `guardian_required=true`이면 guardian 파일도 필요하다. 합쳐진 신청·서약 PDF를 쓰면 두 kind가 같은 경로를 참조할 수 있다. pages는 PDF/HWP를 실제 열어 확인한 값이다.

실제 접수 후 `harness/state.json`의 submission에 `at`(시간대 포함 ISO 시각)와 `receipt`(로컬 확인 증빙 경로)를 기록한다. 접수 전 빈 값으로 둔다. results에서 outcome은 `advanced` 또는 `not_selected`와 공식 결과 evidence 경로를 기록한다.

## 본선 제출 묶음 — submissions/final/manifest.json

운영기관의 실제 본선 안내를 보관한 rules_evidence 경로와 files 목록을 채운다. files 각 항목은 kind·path·sha256·opened를 가진다. 예선의 15쪽/2쪽 제한을 본선에 자동 적용하지 않는다. 새 규격은 최종 검토 기록에서 항목별 확인한다. 실제 제출 후 state의 final_submission에 시각·증빙을 기록한다.
