# related_laws JSON 단순화 설계서 (Cursor 작업지시)

## 0) 상황 요약
현재 `dry_run_result.json` 같은 산출물은 `refs[]` 안에 아래 정보가 한 번에 다 들어가 있어.

- `type`: citation / delegation
- `target`: 법령명/조/항/호 등(부분적으로만 채워짐)
- `evidence`: anchorText / href / onclick / snippet / groupKey / groupAnchors 등(HTML 파싱 흔적)
- `normalized`: searchKey / queryTokens / resolution 등(검색용 후보)

이 구조는 **디버깅에는 유리**하지만,
DB 저장/검색/인덱싱 관점에선 너무 무겁고 변동성이 커서(그룹키, 스니펫 길이 등) 유지보수가 어렵다.

너는 “원본 JSON은 보관하되, 서비스용 JSON은 간단하게” 가고 싶어했고,
특히 **외부 연계법령**은 링크/아이디를 살려서 추후 크롤링까지 연결하려고 해.

---

## 1) 목표
1. 원본(raw) 산출물은 그대로 보관한다. (재현/디버깅/회귀테스트용)
2. 서비스/DB에는 **최소 스키마(min)** 로 저장한다.
3. 외부 연계법령은 가능한 경우 **직접 접근 가능한 URL**(예: `lsLinkCommonInfo.do?lsJoLnkSeq=...`)을 저장한다.
4. “대통령령/총리령/부령/…으로 정한다”는 **위임(delegation)** 은 검색 가능한 실체(시행령/시행규칙 등)로 정규화한다.
5. 동일 조문에서 같은 참조가 여러 번 나오면 **dedupe** 한다. (중복 제거 규칙 정의)

---

## 2) 산출물 분리 전략 (추천)
### A안 (가장 추천): `min.json` + `evidence.jsonl` 2파일
- `*_related_refs.min.json` : 최소 필드만 저장 (DB 적재 대상)
- `*_related_refs.evidence.jsonl` : 원본 evidence를 라인단위로 저장 (디버깅/추적용)

장점
- DB가 가벼워짐
- 서비스에 꼭 필요한 것만 남고, 나머지는 필요할 때만 본다

### B안: 하나의 JSON에 넣되 `evidence`를 축약
- `evidence`에서 `groupAnchors`, `snippet` 등을 삭제하거나 축약(길이 제한)
- 구조는 단순하지만, 계속 커질 위험이 있음

=> **A안을 기본값**으로 진행.

---

## 3) 최소 스키마(min) 제안

### 3.1 `RelatedRefMin` (DB/색인용)
```json
{
  "source": {
    "lawName": "전기사업법",
    "lawKey": "LAW_001854",
    "articleNo": 2,
    "articleKey": "0002001"
  },
  "refs": [
    {
      "id": "rr_0001",
      "type": "citation",
      "scope": "internal",
      "query": {
        "searchKey": "전기사업법",
        "lawTypeHint": null,
        "ref": { "article": 7, "paragraph": 1, "item": null, "subitem": null, "range": null }
      },
      "external": null,
      "evidenceId": "ev_0001",
      "confidence": 0.5
    },
    {
      "id": "rr_0002",
      "type": "delegation",
      "scope": "delegation",
      "query": {
        "searchKey": "전기사업법 시행령",
        "lawTypeHint": "대통령령",
        "ref": null
      },
      "external": {
        "linkSeq": "118678",
        "url": "https://www.law.go.kr/LSW/lsLinkCommonInfo.do?lsJoLnkSeq=118678&chrClsCd=010202&ancYnChk="
      },
      "evidenceId": "ev_0002",
      "confidence": 0.6
    }
  ]
}
```

필드 설명
- `type`
  - `citation`: 조/항/호 등 참조
  - `delegation`: “대통령령/부령으로 정한다” 같은 위임
- `scope`
  - `internal`: 같은 법령 내부 참조(전기사업법 내 제7조 등)
  - `external`: 다른 법령 참조(「…법」 제2조 등)
  - `delegation`: 위임 규정(시행령/시행규칙 등으로 정규화)
- `query.searchKey`
  - **검색엔진/법령DB에서 찾기 위한 문자열** (너희 인덱싱 키 규칙에 맞추기)
- `external.linkSeq/url`
  - 가능한 경우에만 채움. 없으면 `null`.
- `evidenceId`
  - 원본 추적용 연결키 (A안에서 evidence.jsonl의 키)

---

## 4) Evidence 스키마 (JSONL)
파일: `*_related_refs.evidence.jsonl`

한 줄당 1개
```json
{"evidenceId":"ev_0001","anchorText":"제7조","href":"javascript:;","onclick":"javascript:fncLsLawPop('1029857531','JO','');","snippet":"...","groupKey":"p#.pty1_de2h","groupAnchors":[{"anchorText":"제7조","href":"javascript:;","onclick":"..."}]}
```

권장 축약 규칙
- `snippet`은 길이 제한: 200~300자에서 컷 + 말줄임표
- `groupAnchors`는 **최대 10개**까지만 (나머지 버림)
- 원본이 필요하면 raw html/원본 JSON을 별도 보관하니까, 여기까지는 “추적 가능한 최소”로만.

---

## 5) 정규화/파싱 규칙 (핵심)

### 5.1 내부 vs 외부 판정
- 기본: `citation`은 내부로 시작하되,
- anchor 주변에 법령명이 함께 등장(예: `「환경친화적 자동차…」` + `제2조`)하면 외부 가능성 ↑
- 지금 구조에서는 `dry_run_result`에 “법령명 anchor”가 항상 잡히지 않을 수 있음.
  - 그래서 **외부 판정은 2단계**로 간다:
    1) 1차: evidence.snippet / groupAnchors 텍스트에 `「` `」`가 있으면 외부 후보
    2) 2차: 외부 후보면 `lsLinkCommonInfo`를 통해 실제 법령명/조항이 나오는지 확인(가능한 경우만)

### 5.2 `onclick`에서 ID 추출
- `fncLsLawPop('1029857531','JO','')`
  - 첫 번째 인자 `1029857531` 같은 값은 **law.go.kr 내부 팝업용 링크 시퀀스**로 보인다.
  - 이 값만으로 바로 “법령키(law_key)”를 확정하기는 어렵고,
  - 다만 `lsLinkCommonInfo.do?lsJoLnkSeq=...`로 연결 가능한 경우(특히 외부법령일 때)는 URL을 만들 수 있다.

추출 정규식(예시)
- `fncLsLawPop\('(?P<seq>\d+)'`
- `fncLsPttnLinkPop\('(?P<seq>\d+)'`

### 5.3 위임(delegation) 정규화 (검색키 만들기)
현재 법령명이 `X`일 때:
- `대통령령` → `X 시행령`
- `총리령` → (대부분) `X 시행규칙` (예외 가능)
- `부령` 또는 `…부령` → `X 시행규칙` (부처명은 evidence에 남겨두고, 검색키는 시행규칙으로 통일)

예:
- 전기사업법 + `기후에너지환경부령` → `전기사업법 시행규칙`
- 전기사업법 + `대통령령` → `전기사업법 시행령`

※ 목표는 “정확히 어느 조인지”가 아니라, 1차 컨텍스트 확장 시 **해당 하위법령을 찾게 하는 것**.

---

## 6) Dedupe 규칙 (중복 제거)
동일 조문 내에서 아래 키가 같으면 1개만 남긴다.
- `type`
- `query.searchKey`
- `query.ref` (article/paragraph/item/subitem/range)
- `external.url` (있으면 포함)

중복 중 어떤 것을 남길지:
- `confidence`가 높은 것 우선
- 같으면 `evidenceId`가 더 앞선 것(첫 발견) 유지

---

## 7) Cursor가 구현해야 할 것 (TODO)
### 7.1 변환기
- 입력: `dry_run_result.json`
- 출력:
  - `*_related_refs.min.json`
  - `*_related_refs.evidence.jsonl`

필수 구현 포인트
1) refs 순회하며 `evidenceId` 부여
2) `onclick`에서 `seq` 추출 → `external.linkSeq` 후보로 저장
3) `type=delegation`이면 `searchKey`를 `X 시행령/시행규칙`로 생성
4) `snippet/groupAnchors` 기반으로 외부 후보 판정 + URL 생성(가능하면)
5) dedupe 적용

### 7.2 DB 적재(선택)
- 테이블을 만든다면 최소는 이렇게:
  - `law_related_ref(law_key, article_key, ref_id, type, scope, search_key, ref_json, ext_url, confidence, evidence_id, created_at)`
  - evidence는 파일로 두거나, 별도 테이블(`law_related_ref_evidence`)로 분리

---

## 8) 산출물 검증 체크리스트
- [ ] `refs[].query.searchKey`가 항상 채워지는가?
- [ ] delegation이 `X 시행령/시행규칙`로 정규화되는가?
- [ ] `onclick` seq가 파싱되는가?
- [ ] `evidence.jsonl`의 snippet 길이가 과도하지 않은가?
- [ ] dedupe로 “제7조” 같은 게 수십 개로 폭증하지 않는가?

---

## 9) 다음 결정 포인트 (너가 정해야 하는 것)
1) DB에 `evidence`까지 넣을지, 파일로 둘지 (난 파일 추천)
2) 외부법령 확정(resolution)을 “즉시 크롤링”으로 할지, “나중에 배치”로 할지
3) `range` 표현(“제1항부터 제5항까지”)을 구조화할지(지금은 문자열로 두는 걸 추천)

끝.
