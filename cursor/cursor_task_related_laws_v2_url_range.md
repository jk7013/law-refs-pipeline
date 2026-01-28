# Cursor 작업지시서: URL/앵커 기반 “연계법령(인용/위임/범위참조)” 추출·정규화·병합 파이프라인

## 배경/결론
- 법령 본문에서 연계조항이 `제8조제1항제1호부터 제5호까지` 같은 **범위 표현(부터~까지)** 로도 자주 나오고,
- law.go.kr HTML은 링크(a 태그)가 **법령명/조문/항/호/별표/대통령령** 등으로 잘게 쪼개져 있는 경우가 많음.
- 따라서 **텍스트만으로 추측**하기보다, 가능한 경우 **a 태그의 onclick/href에서 URL/식별자(MST/JO/HANG/HO/MOK/ANNEX 등)를 추출→정규화** 하는 방식이 정확도가 높다.
- 단, a 태그가 여러 개로 분절되어도 문맥상 **하나의 참조로 합쳐야** 하는 케이스가 있으므로, “연속 a태그(run) 그룹화 + 타입 분리” 규칙을 적용한다.

---

## 목표
1) `lsInfoR_body.html` 같은 law.go.kr HTML에서 **연계법령 후보(링크/onclick/iframe)** 를 최대한 뽑는다(Recall).
2) 후보를 구조화(정규화)해서 다음을 구분한다(Precision):
   - **인용(citation)**: (법령명/시행령/시행규칙) + (제N조/제M항/제K호/제L목/별표…)
   - **위임(delegation)**: 대통령령/총리령/부령/…부령 등 “하위 규정으로 정한다” 유형
   - **범위(range)**: `제1호부터 제5호까지`, `제2항부터 제4항까지`, `제8조부터 제10조까지` 등
3) 정규화 결과를 `전기사업법.json`의 각 조문 노드에 `related_laws`로 병합한다.

---

## 입력/출력
### 입력
- `data/전기사업법.json`
- `html/lsInfoR_body.html` (또는 동일 구조의 law.go.kr HTML)

### 출력
- `out/candidates.json`
- `out/normalized_refs.jsonl`
- `out/전기사업법.enriched.json`
- (선택) `out/references_edges.jsonl` (그래프 엣지 형태)

---

## 핵심 설계: “URL 우선 + Run 그룹화 + 타입 분리 + 범위 해석”

### A. 후보 추출(HTML → candidates)
다음 소스에서 URL/식별자를 수집:
1) `<a ... onclick="javascript:fncLsLawPop('MST', ...)" ...>`
2) `<a href="...">` (상대/절대)
3) `<iframe src="...">` (가능하면 follow; OFFLINE에서는 수집만)
4) `<script>` 내 URL 패턴(정규식)

**candidate 최소 필드**
- `source_file`, `context_path`(DOM 경로/부모 p의 id/class 등)
- `anchor_text`(a 태그 텍스트), `title`(있으면)
- `onclick_raw`, `href_raw`, `iframe_src_raw`
- `snippet_before/after`(주변 30~60자)  ← run 결합/범위 판정에 유용

중복 제거 키(초안):
- `abs_url` 또는 `onclick_raw`의 파라미터 조합이 같으면 1개로

---

### B. “연속 a태그(run)” 그룹화 규칙 (문맥 결합)
같은 부모(`p`, `li`, `dd` 등) 안에서 **a 태그가 연속**될 때 “run”으로 묶는다.

**run 유지 조건(중요)**
- a와 a 사이 텍스트가 다음 중 하나면 같은 run:
  - 공백
  - 괄호/따옴표/중점/쉼표/마침표 등 구두점(예: `()[]「」『』“”,.ㆍ·`)
  - `제`, `의` 같은 극소 토큰이 아니라면(= 의미 텍스트가 있으면 run 끊기)

**run 예시**
- (a: 법령명) + (a: 제2조)  → 같은 run
- (a: 법령명) + (텍스트: “에 따른”) + (a: 제2조) → 텍스트가 의미가 있으므로 run 분리 가능(하지만 snippet 기반으로 보수적으로 결합해도 됨)

---

### C. run 내부 “타입 분리” (대통령령은 결합 금지)
run 내부 각 a(또는 URL/텍스트)를 분류:
- `LAW_REF`: `…법`, `…시행령`, `…시행규칙` 등 “법령명”
- `PROVISION_REF`: `제\d+조(의\d+)?`, `제\d+항`, `제\d+호`, `제\d+목`, `별표\s*\d+` 등
- `DELEGATION_KEYWORD`: `대통령령|총리령|부령|…부령|고시|훈령|예규` 등(프로젝트 정책에 맞춰 리스트화)

**조립 규칙**
- `LAW_REF` + `PROVISION_REF(들)` → 1개의 citation으로 결합
- `DELEGATION_KEYWORD`는 **항상 별도 레퍼런스**(결합 금지)
- `PROVISION_REF`만 있고 LAW_REF가 없으면:
  - 같은 문단의 “현재 법령명” 컨텍스트(=전기사업법)로 채워서 내부참조 처리(가능하면)
  - 아니면 `unknown_law`로 남기고 evidence 저장

---

### D. 범위(range) 처리 (부터~까지)
범위는 텍스트/앵커 조합으로 판정한다.
- 패턴 예:
  - `제\d+호부터\s*제\d+호까지`
  - `제\d+항부터\s*제\d+항까지`
  - `제\d+조부터\s*제\d+조까지`
  - `제\d+조제\d+항제\d+호부터\s*제\d+호까지`  ← 질문 예시 유형

**정규화 결과 형태(권장)**
- range를 “확장(expand)”하지 말고(=1~5호를 5개로 만들지 말고) 먼저 **구조로 저장**:
```json
{
  "type": "range",
  "lawName": "전기사업법",
  "from": {"article": 8, "paragraph": 1, "clause": 1},
  "to":   {"article": 8, "paragraph": 1, "clause": 5},
  "inclusive": true
}
```
- UI/검색 단계에서 필요하면 expand(옵션) 하도록 설계.

**주의**
- `제8조제1항제1호부터 제5호까지`는 `to`가 “같은 조/항의 5호”로 해석되어야 함.
  - run/snippet에서 “법령명/조/항”이 앞에 있었으면 이를 상속해서 `to`를 보정한다.

---

## OFFLINE / ONLINE 듀얼 모드
### OFFLINE(폐쇄망)
- 외부 fetch 금지. iframe/URL은 수집만.
- `lawName` 확정이 어려우면 `unknown` 허용.
- 단, 사내에 `MST→법령명` 매핑 테이블이 있으면 로컬로 보강 가능.

### ONLINE(허용된 내부망/법령정보센터 접근 가능)
- allowlist: `law.go.kr` 만
- iframe src 및 onclick으로 얻은 URL을 fetch해서
  - MST/LSID 기반으로 법령명/조문번호를 더 정확히 확정
  - 별표/서식 등은 “문서 URL”로 저장(다운로드/표현은 UI에서 링크로 제공)

---

## 병합 정책(전기사업법.json)
- 병합 키(예시): `lawName|제N조` (가능하면 항/호까지 확장 키 추가)
- 각 조문 노드에 다음 필드 추가:
```json
"related_laws": [
  {
    "type": "citation|delegation|range|annex",
    "target": {...},          // 정규화된 구조
    "evidence": {...},        // anchor_text, href/onclick, snippet
    "confidence": 0.0~1.0
  }
]
```
- dedupe 키:
  - `(type, target.lawName, target.article, target.paragraph, target.clause, target.annex, evidence.href_or_onclick)`

---

## 구현 요구사항(파일/모듈)
폴더 제안:
- `src/refs/extract_candidates.py`
- `src/refs/group_runs.py`
- `src/refs/normalize_refs.py`
- `src/refs/enrich_json.py`
- `src/refs/range_parser.py`
- `src/refs/types.py` (dataclass/Pydantic)
- `src/refs/lawgo_fetch.py` (ONLINE only)

CLI:
```bash
python -m refs.extract_candidates --html html/lsInfoR_body.html --out out/candidates.json
python -m refs.group_runs --in out/candidates.json --out out/runs.json
python -m refs.normalize_refs --in out/runs.json --mode offline --out out/normalized_refs.jsonl
python -m refs.enrich_json --law-json data/전기사업법.json --refs out/normalized_refs.jsonl --out out/전기사업법.enriched.json
```

---

## 테스트(필수)
1) 스냅샷 테스트: “전기사업법 제7조 제5항 제5호” 같은 문단 1개에 대해
   - run 그룹이 기대대로 묶이는지
   - `…촉진법` + `제2조`가 1개 citation으로 결합되는지
   - `대통령령`이 별도 delegation으로 분리되는지
2) 범위 테스트:
   - `제8조제1항제1호부터 제5호까지` → range 구조가 맞는지(from/to 보정 포함)
3) 회귀:
   - 병합 후 JSON 스키마가 기존 필드를 깨지 않는지

---

## 커서에게 바로 시킬 작업 체크리스트
- [ ] a/href/onclick/iframe/script에서 후보 URL과 anchor_text 추출
- [ ] 같은 문단 내 연속 a태그를 run으로 그룹화(구두점/공백만 허용)
- [ ] run 내부 분류(LAW_REF/PROVISION_REF/DELEGATION_KEYWORD) 및 조립
- [ ] `부터~까지` 범위 파서 구현(+ 컨텍스트 상속으로 to 보정)
- [ ] OFFLINE/ONLINE 모드 분기(ONLINE이면 allowlist fetch + 캐시)
- [ ] 전기사업법.json에 `related_laws` 병합 + 중복 제거
- [ ] 위 3종 테스트 작성

---

## 참고: 분류 키워드(초안)
- DELEGATION_KEYWORD: `대통령령|총리령|부령|규칙|고시|훈령|예규|지침`
- PROVISION_REF:
  - `제\d+조(의\d+)?`
  - `제\d+항`
  - `제\d+호`
  - `제\d+목`
  - `별표\s*\d+`

(리스트는 실제 HTML/앵커 텍스트를 몇 개 더 보고 보강)
