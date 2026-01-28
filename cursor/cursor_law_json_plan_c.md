# Cursor 작업지시서 (실행용)
## 법령 JSON 기반 DB 구축 — Plan C (조문/부칙 정합 파싱)

---

## 0. 문서 목적

이 문서는 **Cursor에게 그대로 전달하여 코드 생성을 시키기 위한 실행 지시서**다.  
목표는 **국가법령정보센터 JSON 원문을 입력으로 받아**,  
LLM / RAG / 검색엔진 서비스에 바로 사용할 수 있는 **법령 DB 구조(Plan C)** 를 정확하게 구축하는 것이다.

이번 단계에서는 **JSON만 사용**하며,  
HTML / iframe / 연계법령 / API 재호출은 **절대 포함하지 않는다**.

---

## 1. 이번 단계의 범위 정의

### ✅ 반드시 할 것
- JSON 구조 분석 및 안정적인 파싱
- PostgreSQL 테이블 5개 생성 (Plan C)
- JSON → DB 적재 파이프라인 구현
- 조문 전체 텍스트를 **정합하게 재구성**
- 부칙을 **조문과 완전히 분리된 독립 엔티티**로 저장

### ❌ 절대 하지 말 것
- HTML 렌더링 / iframe 해석
- 연계법령(lsiSeq, lsInfoR 등) 처리
- XML 기반 파싱
- 검색엔진(FGF) 변환
- 외부 네트워크 호출

---

## 2. 전체 아키텍처 개요

입력:
- raw_law_json.json_payload (법령 1건의 원본 JSON)

출력:
- law
- law_article
- law_provision_chunk (선택)
- law_addendum
- raw_law_json

원칙:
- raw JSON은 **절대 수정하지 않음**
- 모든 파생 데이터는 raw JSON으로부터 **재생성 가능**해야 함

---

## 3. 기준 스키마 (Plan C)

### 3.1 law — 법령 메타 (법령당 1행)

컬럼:
- law_key (PK)
- law_id
- law_name_ko
- law_type_code
- law_type_name
- ministry_code
- ministry_name
- promulgation_date
- promulgation_no
- effective_date
- revision_type
- is_promulgated
- created_at
- updated_at

규칙:
- law_key = "LAW_" + 법령ID
- 법령 하나당 반드시 1행만 존재

---

### 3.2 law_article — 조문 단위 (주소 기준점)

컬럼:
- article_uid (PK) → {law_key}:{article_no}
- law_key (FK)
- article_key (JSON 제공 조문키)
- article_no (정수)
- article_title
- article_type ("조문")
- effective_date
- revision_type
- is_changed
- article_text  ⭐ 중요
- source_json_path
- created_at
- updated_at

#### ⭐ article_text 생성 규칙 (중요)

article_text에는 반드시 **조 전체 내용**이 들어가야 한다.

1. 조문 헤더
   - 예: "제2조(정의) 이 법에서 사용하는 용어의 뜻은 다음과 같다."

2. 해당 조문에 속한 **모든 항(①②③…)**
3. 각 항에 속한 **호 / 목까지 전부 포함**
4. 원문 순서 유지
5. 개정 이력 문자열 (<개정 …>)은 제거하거나 별도 컬럼으로 분리

예시 결과:

```
제2조(정의) 이 법에서 사용하는 용어의 뜻은 다음과 같다.
① "전기사업"이란 전기를 생산·공급하는 사업을 말한다.
② "전기설비"란 전기의 생산·공급에 필요한 설비를 말한다.
```

❌ 잘못된 예:
- 조문 제목만 저장
- "호" 같은 구조 표시만 저장
- 항/호를 제외한 상태

---

### 3.3 law_provision_chunk — 검색/RAG 단위 (선택)

컬럼:
- chunk_id (PK)
- law_key
- article_uid
- article_no
- para_no (nullable)
- item_no (nullable)
- level (article | paragraph | item | subitem)
- path (예: 제2조/①/1호)
- text
- search_weight
- created_at

규칙:
- 최소 단위는 **항**
- 항이 없으면 조 전체를 1 chunk
- chunk는 검색/LLM용, DB 정합 기준은 아님

---

### 3.4 law_addendum — 부칙 (조문과 완전 분리)

컬럼:
- addendum_uid (PK)
- law_key (FK)
- promulgation_date
- content_text ⭐ 중요
- source_json_path
- created_at

#### 부칙 처리 원칙

- 부칙은 **조문이 아님**
- 부칙 내부의 "제1조", "제2조"는 **조문으로 취급하지 않음**
- 부칙 1개 = law_addendum 1행

content_text 생성 규칙:
- 부칙내용은 배열/중첩 배열 형태
- 모든 문자열을 **원문 순서 유지**
- 줄바꿈("\n")으로 join

---

### 3.5 raw_law_json — 원본 JSON 보관

컬럼:
- law_key (PK)
- source ("law.go.kr")
- json_payload (jsonb)
- ingested_at
- checksum

규칙:
- 원본 JSON 그대로 저장
- 수정/가공 금지

---

## 4. JSON 파싱 세부 규칙

### 4.1 공통
- key 접근은 명시적으로 할 것
- 누락 필드에 대비한 방어 코드 작성
- 실패 시 law_key 기준 로깅

### 4.2 조문 파싱 순서
1. 조문단위 배열 순회
2. 조문여부 == "조문" 만 처리
3. article_text는 하위 항/호를 재귀적으로 수집
4. source_json_path 반드시 기록

### 4.3 부칙 파싱
- json_payload.법령.부칙.부칙단위[]
- 조문과 절대 혼합 금지

---

## 5. 구현 요구사항

필수:
- Python 사용
- PostgreSQL 대응 (psycopg / sqlalchemy 중 택1)
- upsert 로직 포함
- 함수 단위 분리 (law / article / addendum)

권장:
- JSON → 컬럼 매핑 dict 명시
- article_text 빌더 함수 분리

---

## 6. 검증 체크리스트 (필수 통과)

- [ ] law 테이블: 법령당 1행
- [ ] law_article.article_text에 항/호 누락 없음
- [ ] law_article에 부칙 텍스트 없음
- [ ] law_addendum에 조문 텍스트 없음
- [ ] source_json_path 전부 기록됨
- [ ] raw JSON만으로 재생성 가능

---

## 7. 이번 단계의 완료 조건

> "법령 JSON 1건을 입력하면,  
>  조문 전체와 부칙이 정합하게 분리된  
>  LLM/RAG용 법령 DB 구조가 자동으로 채워진다."

이 상태가 되면 이번 단계는 성공이다.
