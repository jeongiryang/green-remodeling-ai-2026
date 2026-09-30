# 생성형 AI 및 외부 자료 활용

OpenAI Codex: 후보·수상작 조사와 비교, 서비스 범위 결정 보조, 제안 문안, 공식 서식과 제출파일 작성·검토.

OpenAI 이미지 생성: 서비스 흐름도와 웹 화면 구성안 제작. 13쪽 제안서의 출처 페이지와 2쪽 요약서 하단에 도구·범위·내용을 기재했다. 생성 원본 이미지는 deliverables/assets에 보관했다.

제품 AI의 설계는 공개 데이터용 표형 회귀와 사전학습 LLM의 문진·근거 요약을 연결한다. 학습·실행 결과를 달성한 것으로 제시하지 않는다. 실행 환경·비용 등 내부 조건과 최소 코어/LLM 확대의 구분은 research/ideation/I008.md에 보존한다.

외부 원문: 국토안전관리원 「공공건축물 에너지 소비량_20260331」 CSV(https://www.data.go.kr/data/3069931/fileData.do), 그린리모델링 창조센터 Greeny, UC Berkeley CBE Occupant Survey. 건축HUB 월별 API 등 제외한 의존성은 내부 조사 기록에 유지한다.

파일 제작: @oai/artifact-tool(PPTX), PowerPoint(PDF), 공식 HWP의 기존 PDF 헤더·행정 서식, pypdf·ReportLab(본문 배치·이미지 삽입). 서약 9개 조항과 주석은 원문 그대로 유지했다. 사용자 전원 승인 및 손글씨 서명 이미지 요청에 따라 새 이름 표식을 제작·배치했고, 실제 필적 복제나 인증형 서명으로 주장하지 않는다. 서명 원본·프롬프트·행정 서류는 Git 제외 private에만 보관한다.
