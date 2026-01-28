Cursor 작업지시서 (수정 지침)

law_article.article_text 깨짐 문제 해결 가이드

⸻

0. 문제 요약 (현재 발생 중인 오류)

현재 law_article 테이블에 아래와 같은 잘못된 데이터가 저장되고 있다.

article_text:
제2조(정의) 이 법에서 사용하는 용어의 뜻은 다음과 같다.
호

이는 조문 전체 텍스트가 아니라, 조문 헤더 + 구조 토큰(호) 만 저장된 상태이며,
또한 줄바꿈(\n)과 구분자 처리 문제로 인해 컬럼 밀림 가능성도 내포하고 있다.

이 상태는 다음 요구사항을 만족하지 못한다:
	•	조문 전체 의미 전달 ❌
	•	검색 / RAG 컨텍스트 제공 ❌
	•	법령 DB 정합성 ❌

⸻

1. 근본 원인

문제는 크게 두 가지 중 하나(혹은 둘 다)다.

1️⃣ article_text 생성 로직 오류
	•	조문 헤더만 사용하고
	•	하위 항(①②), 호(1호, 2호), 목을 article_text에 포함하지 않음
	•	호를 구조 토큰처럼 처리하여 텍스트에서 분리

2️⃣ 중간 산출물 포맷 오류
	•	조문 결과를 Markdown table (|) 또는 CSV 형태로 중간 생성
	•	줄바꿈이 포함된 article_text가 컬럼 구분자로 오인되어
값이 다음 컬럼으로 밀림

⸻

2. 핵심 수정 원칙 (절대 규칙)

🚫 금지 사항 (중요)
	•	조문 파싱 결과를 Markdown table로 생성하지 말 것
	•	줄바꿈이 포함된 텍스트를 CSV 문자열 결합으로 INSERT 하지 말 것
	•	호, 항, 목을 별도 컬럼처럼 분리하지 말 것

⸻

✅ 필수 원칙
	1.	article_text는 하나의 문자열 필드다
	•	줄바꿈 허용
	•	항/호/목 포함
	2.	JSON → Python dict → parameterized INSERT
	•	문자열 직접 결합 SQL 금지
	3.	컬럼 수 검증
	•	law_article는 항상 13개 컬럼
	•	하나라도 밀리면 즉시 실패 처리

⸻

3. article_text 생성 규칙 (수정 버전)

3.1 article_text에 반드시 포함할 요소
	1.	조문 헤더

제2조(정의) 이 법에서 사용하는 용어의 뜻은 다음과 같다.


	2.	하위 항(있다면)

① "전기사업"이란 전기를 생산·공급하는 사업을 말한다.
② "전기설비"란 전기의 생산·공급에 필요한 설비를 말한다.


	3.	항 아래 호/목이 있으면 들여쓰기 또는 줄바꿈으로 포함

⸻

3.2 article_text 생성 의사코드

lines = []
lines.append(article_header)

for para in paragraphs:
    lines.append(f"{para.no} {para.text}")
    for item in para.items:
        lines.append(f"  {item.no} {item.text}")

article_text = "\n".join(lines)

📌 호 같은 단어는 절대 단독으로 남지 않아야 함

⸻

4. DB INSERT 방식 (강제)

4.1 올바른 방식
	•	Python dict 생성
	•	parameterized INSERT 사용

cursor.execute(
    """
    INSERT INTO law_article (
        article_uid, law_key, article_key, article_no,
        article_title, article_type, effective_date,
        revision_type, is_changed, article_text,
        source_json_path, created_at, updated_at
    ) VALUES (%(article_uid)s, %(law_key)s, ...)
    """,
    data_dict
)


⸻

4.2 금지된 방식
	•	문자열 포맷 SQL
	•	Markdown table → 재파싱
	•	CSV 문자열 직접 생성 후 INSERT

⸻

5. 방어 로직 (반드시 추가)

5.1 컬럼 밀림 감지

INSERT 직전 검증:

assert len(data_dict) == 13

5.2 article_text 최소 검증

assert "호" != article_text.strip()
assert "①" in article_text or "②" in article_text or len(article_text) > 50


⸻

6. 검증 체크리스트 (통과 필수)
	•	article_text에 항/호 누락 없음
	•	article_text가 단독 “호”로 끝나지 않음
	•	law_article에 부칙 텍스트 없음
	•	컬럼 수 13개 정확
	•	중간 산출물에 Markdown/CSV 없음

⸻

7. Cursor에게 한 줄 요약 (중요)

“article_text는 줄바꿈·항·호·목을 포함하는 단일 텍스트 필드다. 중간 결과를 Markdown/CSV로 만들지 말고 JSON → dict → parameterized INSERT로 바로 적재해. 컬럼 수가 밀리면 즉시 실패 처리해.”

⸻

8. 수정 완료 기준

제2조(정의)를 포함한 모든 조문에서
	•	article_text에 조 전체가 들어가고
	•	컬럼 밀림 없이
	•	검색/RAG에 바로 사용 가능하면

이 수정은 완료다.