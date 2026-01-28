# 작업지시서: HTML 기반 “연계법령” 추출·정규화·전기사업법.json에 병합

## 목표
- 법령 HTML(예: law.go.kr DRF 응답/본문 HTML)에서 **연계법령(관련 조문/관련 법령/위임·인용 조항)** 정보를 추출한다.
- 추출 결과를 **기존 `전기사업법.json`**(이미 처리 완료된 마스터 JSON) 각 조/항/호(가능하면 “조문 단위”)에 **`related_laws` / `references`** 형태로 병합한다.
- OFFLINE(폐쇄망) / ONLINE(외부망) **듀얼 모드**로 동작하게 한다.

---

## 입력/출력 정의

### 입력
1) `전기사업법.json`  
- 이미 조문 구조(조/항/호/목)와 기본 메타데이터가 정리돼 있다고 가정.

2) HTML 소스
- 이번 작업에서 제공된 예시 파일: `lsInfoR_body.html`
- 이 HTML은 iframe을 포함할 수 있고, 실제 연계정보가 **iframe src 페이지** 또는 내부 스크립트/링크에 존재할 수 있음.

### 출력
1) `전기사업법.enriched.json`
- 기존 구조 유지 + 연계법령 필드 추가
- (선택) `references_edges.jsonl` : 그래프(엣지) 형태로도 저장

---

## 데이터 스키마(제안)

### 조문 노드에 추가할 필드(예시)
```json
{
  "articleKey": "전기사업법|제31조",
  "paragraphKey": "전기사업법|제31조|제2항",
  "related": [
    {
      "type": "citation", 
      "target": {
        "lawName": "전기사업법 시행령",
        "lawId": "000000",
        "article": "제00조",
        "paragraph": "제0항",
        "clause": null
      },
      "evidence": {
        "source": "law.go.kr",
        "htmlSnippet": "…",
        "anchorText": "…",
        "href": "…"
      },
      "confidence": 0.9
    }
  ]
}
```

### 엣지(JSONL) (선택)
```jsonl
{"from":"전기사업법|제31조|제2항","to":"전기사업법 시행령|제00조","type":"delegation","evidenceHref":"...","confidence":0.7}
```

---

## 접근 전략(권장: 2단계 파이프라인)

### 1단계: HTML에서 “연계 후보” 최대한 많이 뽑기 (Recall 우선)
- HTML에서 다음 요소를 모두 탐색:
  - `<a href="...">` 링크
  - `onclick="..."` 내부에 포함된 URL/파라미터
  - `<iframe src="...">`
  - `<script>` 안에 있는 URL 패턴(정규식)
- “연계법령” 가능성이 높은 패턴:
  - `law.go.kr` 도메인
  - `LSW/lsInfoR.do`, `lsInfoP.do`, `lsInfoL.do` 등 **lsInfo*** 계열
  - `DRF/lawService.do?target=...&MST=...` 형태
  - 파라미터에 `MST=`, `LSID=`, `JO=`, `HANG=`, `HO=`, `MOK=` 같은 식별값이 등장
- 결과는 **중복 제거** 후, `candidates.json`으로 저장

### 2단계: 후보를 정규화해서 “타겟 법령/조문” 구조로 변환 (Precision 우선)
- 후보 URL을 다음 규칙으로 정규화:
  1) 상대경로 → 절대경로(기준 URL 필요. 파일 입력일 경우 baseUrl을 설정값으로 받기)
  2) 쿼리스트링 파싱 → `MST` / `LSID` / `JO` 등 구조화
  3) 가능하면 law.go.kr API를 통해 “법령명/조문번호”를 확인(ONLINE일 때만)
- 정규화 결과를 `normalized_refs.jsonl` 로 저장

---

## OFFLINE / ONLINE 모드 설계

### OFFLINE 모드(폐쇄망)
- 외부 통신 금지.
- 정규화는 “문자열/파라미터 기반”으로만 수행.
- law.go.kr 같은 외부 URL은 **저장만** 하고, `lawName` 확정이 어려우면 `unknown` 처리.
- 대신 **내부에 이미 보유한 법령 메타 테이블**이 있다면(예: `law_id_map.json`), 그걸로 보강.

### ONLINE 모드(외부망)
- allowlist 도메인만 접근: `law.go.kr` (필수)
- 후보 URL의 `MST`/`LSID` 등을 이용해 DRF/API를 호출하여:
  - 법령명, 법령ID, 조문(제N조), 항/호(가능하면)까지 정밀 매핑
- 호출 결과는 캐시(`.cache/lawgo_*.json`)로 저장(키/토큰은 런타임 주입, 저장 금지)

---

## 구현 요구사항(코드 구조)

### 폴더/모듈 제안
- `src/refs/`
  - `extract_candidates.py` : HTML → 후보 URL/텍스트 추출
  - `normalize_refs.py` : 후보 → 구조화된 참조로 정규화
  - `enrich_json.py` : 전기사업법.json + refs → enriched JSON 생성
  - `lawgo_client.py` : (ONLINE만) law.go.kr 호출 + 캐시
  - `types.py` : Pydantic/dataclass 스키마
- `tests/`
  - `test_extract_candidates.py`
  - `test_normalize_refs.py`

### CLI(필수)
- `python -m refs.extract_candidates --html lsInfoR_body.html --out candidates.json`
- `python -m refs.normalize_refs --in candidates.json --mode offline --out normalized_refs.jsonl`
- `python -m refs.enrich_json --law-json 전기사업법.json --refs normalized_refs.jsonl --out 전기사업법.enriched.json`

---

## 핵심 파서 로직(구체 지시)

### A) HTML 파싱
- BeautifulSoup 사용 권장(빠르고 단순).
- 아래를 모두 수집:
  1) iframe src
  2) a[href]
  3) onclick 내부 문자열에서 URL 패턴(정규식: `https?://[^'")\s]+` 및 `\/` 이스케이프 처리)
  4) script 텍스트에서 URL 패턴

### B) URL 정규화
- `urllib.parse.urljoin`, `urlparse`, `parse_qs` 사용
- normalize 함수 출력:
  - `raw_url`
  - `abs_url`
  - `host`
  - `path`
  - `query`(dict)
  - `mst`(있으면)
  - `lsid`(있으면)
  - `jo/hang/ho/mok`(있으면)
  - `anchorText`(가능하면)

### C) 전기사업법.json에 병합
- 조문 키 규칙을 통일:
  - 최소: `lawName|제N조`
  - 확장: `lawName|제N조|제M항|제K호|제L목`
- 기존 JSON에서 조문/항/호를 식별하는 키가 이미 있다면 그 키를 그대로 쓰고, 없으면 위 규칙으로 생성.
- 병합 규칙:
  - 같은 조문 키에 여러 참조가 붙으면 배열에 append
  - 중복은 `(type, target.lawId, target.article, target.paragraph, target.clause, href)` 조합으로 제거
  - “증거”는 가능한 한 남기되 길이는 제한(예: snippet 200자)

---

## 품질 체크(필수)
1) 후보 추출 수량/중복률 로그:
   - 총 후보 수 / 유니크 URL 수 / law.go.kr 도메인 비율
2) 정규화 성공률:
   - `mst` 추출 성공률, `lawName` 확정률(ONLINE)
3) 병합 결과:
   - 연계정보가 들어간 조문 수
   - 조문당 평균 참조 수
4) 리그레션:
   - `전기사업법.enriched.json`이 기존 필드 구조를 깨지 않는지(스키마 검사)

---

## 보안/운영 원칙(필수 준수)
- 키/토큰/OC 값은 **코드/파일에 하드코딩 금지**. 환경변수로만 주입.
- 로그에는 URL 전체를 남기되, 토큰/키 파라미터가 있으면 마스킹.
- 캐시는 OFFLINE에서는 생성하지 않거나(선택), 내부경로에만 저장.
- 컨테이너 실행 시 비루트/읽기전용을 기본값으로 고려(프로젝트 원칙).

---

## Cursor에게 시킬 “구체 작업” 체크리스트
- [ ] `lsInfoR_body.html`을 읽어서 후보 URL을 뽑는 함수 구현
- [ ] iframe src도 재귀적으로 따라갈 수 있게 설계(ONLINE일 때만 fetch)
- [ ] URL 정규화 + 파라미터 추출 구현
- [ ] OFFLINE/ONLINE 스위치 구현(모드별 동작 분리)
- [ ] `전기사업법.json` 병합기 구현 + 중복 제거
- [ ] 샘플 출력 1개 조문에 대해 결과 확인(스냅샷 테스트)
- [ ] README에 실행 예시 3줄 추가

---

## 이번 파일 기반 “즉시 실행” 예시
```bash
python -m refs.extract_candidates --html lsInfoR_body.html --out out/candidates.json
python -m refs.normalize_refs --in out/candidates.json --mode offline --out out/normalized_refs.jsonl
python -m refs.enrich_json --law-json data/전기사업법.json --refs out/normalized_refs.jsonl --out out/전기사업법.enriched.json
```

---

## 추가 옵션(있으면 좋음)
- `--max-snippet-len 200`
- `--dedupe true`
- `--base-url https://www.law.go.kr/` (파일 입력일 때 절대경로 만들기용)
- `--allow-domains law.go.kr` (ONLINE allowlist)

