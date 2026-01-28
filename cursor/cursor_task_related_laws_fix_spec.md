# Cursor 작업지시서 (수정본): HTML 기반 연계법령(related_laws) 추출·정규화·병합 품질개선

> 목적: `cursor_task_related_laws_v2_url_range.md` 기반으로 구현된 현재 결과(`전기사업법.enriched.json`)가 **연계법령이 깨끗하게 발리지 않는 문제**를 해결하기 위한 **수정 지시사항**이다.  
> 핵심 원인: 기존 로직이 “a태그 단위”가 아니라 “조문/페이지 전체 텍스트 단위”로 candidate/snippet을 만들면서 anchorText/snippet/target이 뒤섞임.

---

## 0) 배경 / 현재 증상 요약

현재 `related_laws`가 아래처럼 생성되는 문제가 있음:

- `evidence.snippet`에 조문 전체 텍스트가 들어감 (금지)
- `evidence.anchorText`가 여러 링크의 텍스트를 join한 값으로 생성됨 (금지)
- `target.article/paragraph/clause`가 실제 a태그 1개를 기준으로 파싱되지 않고 “섞인 상태”로 들어감 (금지)
- `"대통령령"` 같은 delegation 신호가 다른 조문참조들과 섞여 다수의 잘못된 엔트리가 생성됨

---

## 1) 최종 목표 결과(JSON 구조 원칙)

### 1.1 핵심 원칙 (강제)
1) **related_laws는 HTML의 a태그 기반으로만 생성한다.**
2) 기본: **a태그 1개 → related_laws 1개**  
3) 예외: 특정 패턴에서는 **연속된 a태그를 “한 덩어리 참조”로 병합**한다.  
4) 범위표현(“제1항부터 제5호까지”)은 별도 구조로 담는다.

---

## 2) 구현 변경사항 (필수)

### (A) evidence.snippet 생성 방식 수정
#### 금지
- `<body>.get_text()` 또는 `<p>.get_text()` 전체를 snippet으로 넣는 방식
- 페이지 전체/조문 전체 텍스트를 snippet으로 저장

#### 요구
- snippet은 반드시 “해당 a태그 주변 문맥(window)”만 저장한다.
- 추출 규칙
  - 기준 노드: `anchor.parent` (가능하면 가장 가까운 block: p/li/dd/td)
  - a태그 위치 기준 양쪽으로 window를 잡는다 (예: ±80자)
  - `max_snippet_len = 200`

---

### (B) evidence.anchorText 강제 규칙
- `anchorText`는 반드시 **단일 a태그 텍스트**여야 한다.
- 여러 링크 텍스트를 join() 하는 로직 제거

---

### (C) related_laws 엔트리 생성 로직 변경 (가장 중요)
#### 기존 문제
- “a태그들”을 모아서 한 번에 처리하여 target이 섞임
- join된 텍스트에서 article/paragraph 파싱하면서 오류 발생

#### 요구
- 기본적으로 **a태그를 단위로 엔트리 생성**  
- 단, 아래 (D) 병합 규칙이 적용되는 경우는 “그룹 처리”

---

### (D) 연속 a태그 병합 규칙 구현 (핵심)
법령 사이트 HTML은 다음처럼 분리되어 있음:

- `법령명` a태그 1개
- `제n조` a태그 1개
- `제m항` a태그 1개
- `제k호` a태그 1개
- ...

문맥상 하나의 참조인데 태그가 분리되어 있으므로 병합이 필요함.

#### 병합 조건
- 같은 부모 block (`<p>`, `<li>`, `<dd>` 등) 안에서
- a태그가 **연속**으로 나타나며
- a태그 사이의 텍스트가 아래 조건을 만족할 때 “병합 가능”:
  - 공백만 존재
  - 또는 `"", " ", "\n", "\t", "(", ")", "ㆍ", "·", ",", "，", ".", "“", "”", "「", "」"` 등 구두점 수준
  - 즉 “실질 단어”가 끼어있지 않음

#### 병합 결과 (정규화 문자열)
병합 후 normalized_ref_text는 아래처럼 만들어야 함:

- `신에너지 및 재생에너지 개발ㆍ이용ㆍ보급 촉진법 제2조 제3호`
- `전기사업법 제7조 제1항`
- `전기사업법 시행령 제25조 제4항`

#### 병합 단위
- 병합된 그룹은 **related_laws 1개로 만든다**.
- group evidence에는 첫 a태그/마지막 a태그 정보를 남긴다.

---

### (E) delegation (“대통령령/부령/총리령”) 분리 규칙
다음 문자열/링크는 법령참조가 아니라 **위임(delegation)**임.

- “대통령령”, “총리령”, “부령”, “기후에너지환경부령” 등

#### 요구
- delegation은 **다른 참조 그룹과 병합 금지**
- type=`delegation`
- target 최소 구조:

```json
{
  "type": "delegation",
  "target": { "lawName": "대통령령" },
  "evidence": { "anchorText": "대통령령", "...": "..." }
}
```

---

### (F) 범위표현 처리 (from~to)
예:  
- `제1항부터 제5호까지`
- `제8조제1항제1호부터 제5호까지`

#### 요구
- 단일 point 참조로 만들지 말고 `ref_range`를 추가한다.

추천 구조:

```json
"target": {
  "lawName": "전기사업법",
  "lawId": "LAW_001854",
  "ref": { "article": 8, "paragraph": 1, "item": 1, "subitem": null },
  "ref_range": {
    "item_from": 1,
    "item_to": 5
  }
}
```

---

## 3) target 정규화 스키마 변경 (추천 + 사실상 필수)

### 기존 방식 문제
- `"article": "2"` 같은 string 기반 필드는 파싱/비교/중복제거 모두 불안정

### 요구 스키마 (권장)
```json
"target": {
  "lawName": "...",
  "lawId": "...",
  "ref": {
    "article": 7,
    "paragraph": 1,
    "item": 5,
    "subitem": null
  }
}
```

- 숫자는 int로 저장
- 없는 값은 null

---

## 4) 중복제거(dedupe) 규칙 수정

### 새로운 dedupe key
다음 tuple로 중복 제거:

- `(type, target.lawName, target.lawId, target.ref.article, target.ref.paragraph, target.ref.item, evidence.onclick || evidence.href)`

---

## 5) 증거(evidence) 보강 규칙

### evidence 필드
- `source`: "law.go.kr"
- `href`: a태그 href (없을 수 있음)
- `onclick`: onclick 값 (있으면 매우 중요)
- `anchorText`: 단일 a태그 텍스트
- `snippet`: 문맥 window
- `groupAnchors` (병합일 때만)
  - `[{anchorText, href, onclick}, ...]`

---

## 6) 품질검증 체크리스트 (작업 완료 기준)

- [ ] 조문당 related_laws 평균 개수 출력
- [ ] delegation type 개수 출력
- [ ] range(ref_range) 개수 출력
- [ ] dedupe로 제거된 개수 출력
- [ ] 스냅샷 테스트: `전기사업법 제7조 제5항 제5호`에서
  - `신에너지~법`+`제2조`는 **한 엔트리로 병합**
  - `대통령령`은 **delegation으로 분리**
- [ ] “n항부터 m호까지” 범위표현은 `ref_range`로 저장

---
