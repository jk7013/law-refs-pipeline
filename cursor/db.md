Cursor 작업지시서 — 법령 JSON 기반 DB 구축 (Plan C)

0. 목적

이 작업은 국가법령정보센터 JSON 원문을 입력으로 사용하여,
LLM/RAG 서비스용 법령 데이터베이스의 1차 정규화 구조(Plan C) 를 구축하기 위한 것이다.

이번 단계의 범위는 JSON만 사용하며, HTML/연계법령 파트는 포함하지 않는다.
(HTML 렌더링, 연계법령 파싱은 후속 단계)

⸻

1. 전체 작업 범위 (이번 단계에서 할 것 / 안 할 것)

✅ 이번 단계에서 할 것
	•	전기사업법 JSON 구조 분석
	•	Plan C 기준 DB 테이블 5개 생성
	•	JSON → 테이블 적재 로직 구현
	•	조 단위 + 항 단위까지 파싱하여 law_provision_chunk 생성

❌ 이번 단계에서 하지 말 것
	•	iframe / HTML / lsInfoR / 연계법령 처리
	•	검색엔진 색인(FGF 변환)
	•	XML 기반 파싱

⸻

2. 기준 스키마 (Plan C)

2.1 law (법령 메타)
	•	law_key (PK)
	•	law_id
	•	law_name_ko
	•	law_type_code
	•	law_type_name
	•	ministry_code
	•	ministry_name
	•	promulgation_date
	•	promulgation_no
	•	effective_date
	•	revision_type
	•	is_promulgated
	•	created_at
	•	updated_at

⸻

2.2 law_article (조 단위)
	•	article_uid (PK) → {law_key}:{article_no}
	•	law_key (FK)
	•	article_key (JSON 제공 값)
	•	article_no
	•	article_title
	•	article_type
	•	effective_date
	•	revision_type
	•	is_changed
	•	article_text (조 전체 텍스트)
	•	source_json_path
	•	created_at
	•	updated_at

⸻

2.3 law_provision_chunk (검색/RAG 단위)
	•	chunk_id (PK)
	•	law_key (FK)
	•	article_uid (FK)
	•	article_no
	•	para_no (nullable)
	•	item_no (nullable)
	•	level (article | paragraph | item)
	•	path (예: 제31조/②/3호)
	•	text
	•	search_weight (default = 1.0)
	•	created_at

⸻

2.4 law_addendum (부칙)
	•	addendum_uid (PK)
	•	law_key (FK)
	•	promulgation_date
	•	content_text
	•	source_json_path
	•	created_at

⸻

2.5 raw_law_json (원본 JSON 보관)
	•	law_key (PK)
	•	source (예: law.go.kr)
	•	json_payload (jsonb)
	•	ingested_at
	•	checksum

⸻

3. JSON 파싱 규칙

3.1 공통
	•	JSON 원문은 절대 수정하지 않고 raw_law_json에 그대로 저장
	•	모든 파생 데이터는 원본 JSON을 기준으로 재생성 가능해야 함

⸻

3.2 law 테이블 파싱 규칙
	•	JSON 최상위 메타 필드에서 직접 매핑
	•	날짜 필드는 YYYY-MM-DD로 정규화
	•	law_key는 내부 통합 키 (예: LAW_{법령ID} 형식)

⸻

3.3 law_article 파싱 규칙
	•	JSON의 조문 배열(조문.조문단위[]) 기준
	•	article_no = 숫자 조문번호
	•	article_text = 조문에 포함된 모든 항/호 텍스트를 줄바꿈으로 합친 값
	•	article_uid는 자연키로 생성

⸻

3.4 law_provision_chunk 파싱 규칙
	•	최소 단위는 항(paragraph)
	•	항이 없는 조문은 조 전체를 하나의 chunk로 생성
	•	chunk_id 규칙:
	•	조: CHUNK_{law_key}_{article_no}
	•	항: CHUNK_{law_key}_{article_no}_{para_no}
	•	level 값은 명확히 구분

⸻

3.5 law_addendum 파싱 규칙
	•	JSON의 부칙 배열 기준
	•	여러 줄일 경우 하나의 문자열로 합쳐 content_text 생성

⸻

4. 구현 요구사항

필수
	•	Python 사용
	•	JSONPath 또는 명시적 key 접근 사용
	•	중복 적재 방지 (law_key 기준 upsert)
	•	오류 발생 시 law_key 단위로 로깅

권장
	•	파싱 로직을 함수 단위로 분리
	•	JSON → DB 매핑 테이블(dict) 명시적으로 작성

⸻

5. 결과물

Cursor는 아래 결과물을 생성해야 한다:
	1.	PostgreSQL DDL (5개 테이블)
	2.	JSON → DB 적재 Python 스크립트
	3.	조/항 파싱 로직 함수
	4.	샘플 JSON 1건 기준 정상 적재 확인 로그

⸻

6. 주의사항
	•	HTML/연계법령은 절대 이번 단계에서 건드리지 말 것
	•	컬럼 추가/삭제가 필요하면 반드시 사유 주석 남길 것
	•	성능 최적화는 고려하되, 가독성 우선

⸻

7. 최종 목표 요약

“법령 JSON 하나를 넣으면,
LLM/RAG에 바로 쓸 수 있는
조/항 단위 법령 DB 구조가 자동으로 채워지는 상태”

이 상태를 만드는 것이 이번 단계의 완료 조건이다.