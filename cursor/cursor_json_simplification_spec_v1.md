# Cursor 작업지시서: 연계법령 JSON 단순화 규칙 (v1)

## 0) 목적
현재 파서 출력(dry_run_result.json)의 `refs[]`가 너무 복잡해서,
- **검색/색인에 필요한 최소 정보만 남긴 “단순화 JSON”**을 만들고
- 원본은 그대로 보관하여(원본 JSON/HTML) **추적 가능성**을 유지한다.

이 문서는 **단순화 JSON을 생성하는 코드**를 구현하기 위한 작업지시서다.

---

## 1) 입력/출력

### 입력
- `dry_run_result.json`
  - 최상위: `strategy`, `debug`, `refs[]`
  - `refs[]` 각 원소: `type`, `target`, `evidence`, `confidence`, `normalized` 등

### 출력
- `related_refs.simple.json` (또는 파이프라인 결과에 포함)
- DB 저장용이면 `law_article.related_laws_simple` 같은 컬럼/필드에 저장

---

## 2) 단순화 JSON 스키마

### 2.1 Top-level
```json
{
  "schemaVersion": "relatedRefs.simple.v1",
  "source": {
    "lawName": "<현재 법령명>",
    "lawKey": "<현재 law_key (있으면)>",
    "articleNo": "<현재 조문번호(있으면)>"
  },
  "refs": [
    {
      "kind": "citation|delegation|external",
      "target": {
        "lawName": "<대상 법령명(정규화된 검색키)>",
        "lawType": "법률|시행령|시행규칙|대통령령|총리령|부령|규칙|기타|null",
        "ref": {
          "article": 7,
          "paragraph": 1,
          "item": 2,
          "subitem": null,
          "range": {
            "articleFrom": null,
            "articleTo": null,
            "paragraphFrom": null,
            "paragraphTo": null
          }
        },
        "link": {
          "url": null,
          "lsJoLnkSeq": null
        }
      },
      "evidence": {
        "anchorText": "제7조",
        "snippet": "…제7조 제1항…",
        "groupKey": "p#.pty1_de2h",
        "onclick": "javascript:fncLsLawPop('1029857531','JO','');",
        "onclickId": "1029857531",
        "href": "javascript:;"
      }
    }
  ]
}
```

### 2.2 필드 설명
- `kind`
  - `citation`: 조/항/호/목 참조(같은 법 or 다른 법)
  - `delegation`: “대통령령/부령/총리령/…으로 정한다”류 위임
  - `external`: 외부법령 링크(= `lsJoLnkSeq`로 실제 링크 접근 가능)

- `target.lawName`
  - 검색/조인에 쓰는 **정규화된 법령명 키**
  - 예) “대통령령” → (규칙 적용 후) “전기사업법 시행령”
  - 예) “기후에너지환경부령” → “전기사업법 시행규칙”
  - 예) “「신에너지 및 재생에너지 개발ㆍ이용ㆍ보급 촉진법」” → 그 법령명 그대로

- `target.link`
  - 외부법령 링크가 **살아있으면** `lsJoLnkSeq`를 저장
  - URL 예시: `https://www.law.go.kr/LSW/lsLinkCommonInfo.do?lsJoLnkSeq=<ID>&chrClsCd=010202&ancYnChk=`
  - `lsJoLnkSeq` 추출 규칙은 4장 참고

- `evidence`
  - 디버깅/추적용 최소 정보만 저장
  - `onclickId`: `fncLsLawPop('...')` 또는 `fncLsPttnLinkPop('...')`의 첫 번째 숫자만 파싱

---

## 3) 단순화 규칙

### 3.1 “중복 제거” 규칙 (필수)
`refs[]`가 같은 참조를 여러 번 내는 경우가 많다. 다음 키로 **dedupe** 한다.
- `dedupeKey` =
  - `kind`
  - `target.lawName`
  - `target.ref.article|paragraph|item|subitem|range.*` (없으면 null)
  - `target.link.lsJoLnkSeq` (없으면 null)
  - `evidence.anchorText`
  - `evidence.groupKey`

> `snippet`은 dedupeKey에 포함하지 않는다(같은 참조가 다른 문맥에 등장 가능).
> 대신, dedupe된 결과에는 `snippet`을 **하나만** 남기거나(첫 등장),
> 혹은 `snippets[]`로 여러 개를 모아도 된다(선택).

### 3.2 “같은 문단 그룹” 처리 (선택)
현재 결과에 `groupAnchors[]`가 있는 경우,
- 단순화 결과에는 `groupAnchors` 전체를 보관하지 말고,
- 대표 anchor(`anchorText`, `onclick`, `href`)만 남긴다.

### 3.3 `kind` 분류
입력 `ref.type` 기준:
- `type == "citation"` → `kind = "citation"`
- `type == "delegation"` → `kind = "delegation"`
- 그 외, 아래 4.2 규칙으로 외부 링크 판별되면 `kind = "external"`

---

## 4) 외부법령 링크/아이디 처리

### 4.1 `onclickId` 파싱
- 패턴:
  - `fncLsLawPop('<ID>','JO','');`
  - `fncLsPttnLinkPop('<ID>');`
- `<ID>`만 추출해서 `evidence.onclickId`로 저장

### 4.2 `lsJoLnkSeq` 판별 (external)
다음 중 하나라도 만족하면 `kind="external"`로 취급하고 `lsJoLnkSeq` 저장:
- `evidence.href` 또는 `onclick`에서 직접 `lsJoLnkSeq=`가 보이는 경우
- 또는, 프로젝트에서 이미 확인한 것처럼 **외부법령 참조 링크**가
  `lsLinkCommonInfo.do?lsJoLnkSeq=...` 형태로 만들어지는 경우

> 주의: `fncLsLawPop`의 숫자 ID는 **항상 외부 링크로 바로 접근 가능한 ID가 아닐 수 있음**.
> 따라서 “external” 판별은 `lsJoLnkSeq` 확인 가능한 케이스에 한정한다.

---

## 5) 위임명령(대통령령/부령/총리령 등) 정규화 규칙
입력에 “대통령령”, “총리령”, “부령”, “기후에너지환경부령”처럼 나오면
**검색 가능한 법령명**으로 바꿔야 한다.

### 5.1 기본 매핑 (현재 법률이 X법일 때)
- `대통령령` → `X법 시행령`
- `총리령` → `X법 시행규칙` (일반적으로 “총리령=시행규칙” 케이스가 많음)
- `부령` 또는 `OO부령` → `X법 시행규칙`
  - 예: `기후에너지환경부령` → `전기사업법 시행규칙`

> 구현 방식: 현재 법명 `X법`을 source에서 받아서 문자열 합성.

### 5.2 예외/유지 규칙
- 만약 본문/앵커에 **이미 “시행령/시행규칙”**이 명시되어 있으면 그대로 사용
- “대통령령으로 정하는 바에 따라” 같은 위임은
  조문 레벨에서 “시행령”을 던져도 길이가 과하면,
  후속 단계에서 **추가 검색**으로 필요한 조문만 가져오도록 설계(단순화 단계에서는 링크만 정리)

---

## 6) 조문/항/호 범위(ref_range) 표준화 (선택)
현재 입력에서 `ref_range`가 null인 경우가 많다.
향후 “제1항부터 제5항까지” 같은 표현을 지원하려면:
- `target.ref.range.paragraphFrom=1`, `paragraphTo=5` 같이 저장
- `anchorText`나 `snippet`에서 정규식으로 추출(후속 작업으로 분리 가능)

단, **이번 단순화 작업(v1)**에서는 `ref_range`를 그대로 null로 두고,
범위 파싱은 v2로 미룬다.

---

## 7) 구현 체크리스트
- [ ] `dry_run_result.json` 로드
- [ ] `refs[]` 순회하면서 `SimpleRef` 생성
- [ ] `onclickId` 파싱
- [ ] `kind` 결정(citation/delegation/external)
- [ ] 위임명령 매핑(대통령령/부령/총리령 등 → X법 시행령/시행규칙)
- [ ] dedupeKey 생성 후 중복 제거
- [ ] 결과를 `related_refs.simple.json`로 저장
- [ ] 단위테스트: “대통령령 → X법 시행령”, “기후에너지환경부령 → X법 시행규칙”, dedupe 동작

---

## 8) 샘플(기대 결과 예시)
입력에 아래가 있으면:
- anchorText: `대통령령`
- normalized.searchKey: `전기사업법 시행령`

출력은 최소로:
```json
{
  "kind": "delegation",
  "target": {
    "lawName": "전기사업법 시행령",
    "lawType": "대통령령",
    "ref": { "article": null, "paragraph": null, "item": null, "subitem": null, "range": { "articleFrom": null, "articleTo": null, "paragraphFrom": null, "paragraphTo": null } },
    "link": { "url": null, "lsJoLnkSeq": null }
  },
  "evidence": {
    "anchorText": "대통령령",
    "snippet": "…대통령령으로 정하는…",
    "groupKey": "p#.pty1_de2h",
    "onclick": "javascript:fncLsPttnLinkPop('118678');",
    "onclickId": "118678",
    "href": "javascript:;"
  }
}
```

---

## 9) 파일/모듈 구조 제안(리팩토링과 호환)
- `src/related_refs/simplify.py`
  - `simplify_refs(raw_refs, source_ctx) -> simple_refs`
- `src/related_refs/normalize_delegation.py`
  - `normalize_delegation(anchor_text, source_law_name) -> (lawName, lawType)`
- `tests/test_simplify_refs.py`

