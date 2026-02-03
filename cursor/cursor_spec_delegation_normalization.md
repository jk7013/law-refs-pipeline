# Cursor 작업지시서: 위임입법(대통령령/총리령/부령) 표현을 “검색 가능한 문서명”으로 정규화하기

## 배경
현재 `related_laws`를 만들 때 HTML의 a태그/onclick에서 **“대통령령”, “부령”** 같은 표현이 그대로 들어가면,
- DB/검색엔진에서 **문서명이 아니라 분류어**라서 검색이 안 되거나,
- 잘못된 법령으로 연결되거나,
- 시행령/시행규칙이 **자기 문서인지/하위 문서인지** 구분이 안 되는 문제가 생김.

그래서 파싱 단계에서 **“대통령령/총리령/부령/○○부령”을 ‘실제 문서명(예: 전기사업법 시행령)’으로 정규화**해야 함.

---

## 0) 범위 확인: “현행법령 5,000여건”에 시행령/시행규칙이 포함되나?
결론부터 말하면, **데이터 소스에 따라 다르다.**  
그래서 추측하지 말고, **입력 리스트(법령 메타)로 먼저 분포를 찍어서 확정**해야 함.

### 해야 하는 체크(코드로 5분 컷)
- 현행법령 목록(또는 JSON 메타)에 **법종구분(법률/대통령령/총리령/부령 등)** 이 들어있을 것.
- 그걸로 집계해서 “5,000” 안에 무엇이 포함됐는지 확정.

예시(의사코드):
```python
from collections import Counter

# laws: [{"lawName":..., "lawType":...}, ...] 형태라고 가정
c = Counter([x["lawType"] for x in laws])
print(c)  # 법률/대통령령/총리령/부령 비율 확인
```

### 해석 가이드
- **법률만** 있다면: “대통령령/부령”을 “○○법 시행령/시행규칙”으로 정규화해도 **실제 문서가 DB에 없을 수 있음**  
  → 이때는 `status="unresolved"`로 남기거나, “후속 확장(시행령/규칙 색인)” 작업이 필요.
- **대통령령/총리령/부령도 포함**되어 있다면: 정규화 후 **실제 문서로 연결 가능**.

> 즉, “정규화 로직”은 항상 필요하고, **연결 성공률은 색인 범위에 따라 달라진다.**

---

## 1) 목표 결과물(related_laws에 넣고 싶은 형태)
`related_laws`는 “원문 증거 + 정규화된 검색키”를 같이 들고 있어야 함.

권장 스키마(예시):
```json
{
  "type": "delegation | citation | admin_rule | ambiguous",
  "target": {
    "lawName": "전기사업법 시행령",
    "lawType": "대통령령",
    "ref": { "article": 7, "paragraph": 1, "item": null, "subitem": null }
  },
  "normalized": {
    "searchKey": "전기사업법 시행령",
    "queryTokens": ["전기사업법", "시행령"],
    "resolution": "resolved | unresolved | self"
  },
  "evidence": {
    "anchorText": "대통령령",
    "href": "javascript:;",
    "onclick": "javascript:fncLsPttnLinkPop('118679');",
    "snippet": "…그 밖에 대통령령으로 정하는 것은 제외한다…",
    "groupAnchors": [
      { "anchorText": "대통령령", "href": "javascript:;", "onclick": "javascript:fncLsPttnLinkPop('118679');" }
    ]
  },
  "confidence": 0.7
}
```

핵심:
- `evidence`: HTML에서 캡처한 **원문 근거**
- `normalized.searchKey`: DB/검색에 넣을 **실제 문서명**
- `resolution`: 실제로 DB에서 찾았는지 여부(또는 self)

---

## 2) 정규화 규칙(가장 중요)

### 2.1 먼저 “현재 문서의 법종”을 알아야 함
정규화는 **현재 문서 타입**에 따라 달라져.
- 현재 문서가 **법률**인지
- **시행령(대통령령)**인지
- **시행규칙(총리령/부령)**인지

현재 문서에서 얻을 수 있는 값(예):
- `baseLawName`: “전기사업법” 또는 “전기사업법 시행령”
- `baseLawType`: “법률” / “대통령령” / “총리령” / “부령”

---

### 2.2 “대통령령/총리령/부령/○○부령” 매핑 테이블
아래는 **원문 표현 → 정규화 문서명** 기본 규칙.

#### A) 현재 문서가 “법률”인 경우
| 원문(anchorText) | 정규화 문서명(searchKey) | 설명 |
|---|---|---|
| 대통령령 | `{contextLawName or baseLawName} 시행령` | 법률 위임은 보통 해당 법 시행령 |
| 총리령 | `{contextLawName or baseLawName} 시행규칙` | 총리령은 시행규칙(총리령)로 귀결되는 경우가 많음 |
| 부령 / ○○부령 | `{contextLawName or baseLawName} 시행규칙` | 부령도 시행규칙으로 귀결되는 경우가 많음 |
| ○○부령(기후에너지환경부령 등) | `{...} 시행규칙` + `issuerHint=○○부` | 문서명은 “○○법 시행규칙”, 발령부처는 힌트 |
| 규칙 / 조례 | 정규화 불가(대상 지자체/기관 불명) | `type="ambiguous"`로 남김 |
| 고시/훈령/예규/지침/공고 | 법령이 아니라 행정규칙/공지 | `type="admin_rule"`로 남김 |

#### B) 현재 문서가 “시행령(대통령령)”인 경우
| 원문(anchorText) | 정규화(searchKey) | 설명 |
|---|---|---|
| 대통령령 | `resolution="self"` 처리 | 시행령 본문에서 “대통령령으로 정한다”는 보통 자기 문서 내부 의미 |
| 부령/○○부령 | `{contextLawName or baseLawName(원법)} 시행규칙` | 시행령이 부령으로 재위임하는 케이스 |
| 총리령 | `{...} 시행규칙` | |
| 고시 등 | `admin_rule` | |

> “baseLawName(원법)”은 시행령 문서명에서 “ 시행령” 제거한 이름으로 만들면 됨.

#### C) 현재 문서가 “시행규칙(총리령/부령)”인 경우
| 원문(anchorText) | 정규화(searchKey) | 설명 |
|---|---|---|
| 부령/총리령 | `resolution="self"` 처리 | 시행규칙 내부로 보는 게 안전 |
| 대통령령 | 상위 시행령/법률 문맥 확인 필요 | 단독 토큰이면 `ambiguous` |

---

## 3) “컨텍스트 법령명” 우선 규칙 (다른 법의 시행령/규칙으로 튀는 케이스)
문장에 다른 법령명이 같이 나오면 “대통령령”이 **현재 법이 아니라 다른 법의 시행령**일 수 있어.

### 컨텍스트 추출 우선순위
1) “대통령령/총리령/부령” **직전에 등장한 법령명 토큰**
   - `「…법」`, `「…법률」`
   - `…법 시행령`, `…법 시행규칙`
2) 없으면 현재 법령(baseLawName)

예:
- “「신에너지…촉진법」 제2조 … 대통령령으로 정하는 …”  
  → 컨텍스트 lawName = “신에너지…촉진법”  
  → 대통령령 정규화 = “신에너지…촉진법 시행령”

### 구현 힌트(HTML 기준)
- a태그가 “법령명”, “제2조”, “대통령령”처럼 쪼개져 있으니,
  - **같은 p/div 블록 안에서 a태그 순서를 보고**
  - “대통령령” 직전에 등장한 “법령명(「…」 포함)”을 컨텍스트로 잡아.

---

## 4) 파서 구현 요구사항(구체 지시)

### 4.1 입력
- HTML에서 추출한 `groupAnchors`(연속 a태그 묶음) 또는 단일 a태그
- 현재 법령 메타: `baseLawName`, `baseLawType`

### 4.2 출력
- `related_laws[]`의 각 엔트리마다:
  - `evidence`는 원문 그대로
  - `target`은 가능한 만큼 구조화(법령명/조/항/호…)
  - `normalized.searchKey`는 **검색 가능한 문서명**으로
  - `normalized.resolution`은 `resolved/unresolved/self/ambiguous` 중 하나

### 4.3 정규화 함수(필수)
시그니처 예:
```python
def normalize_delegation_term(
    anchor_text: str,
    base_law_name: str,
    base_law_type: str,
    context_law_name: str | None,
) -> dict:
    ...
```

### 4.4 normalize_delegation_term 로직(요약)
1) `context = context_law_name or base_law_name`
2) if anchor_text == "대통령령":
   - if base_law_type == "법률": return searchKey = f"{context} 시행령"
   - elif base_law_type == "대통령령": return resolution="self"
   - elif base_law_type in ["총리령","부령"]: return resolution="ambiguous"
3) if anchor_text in ["총리령", "부령"] or anchor_text.endswith("부령"):
   - if base_law_type == "법률": return searchKey = f"{context} 시행규칙"
   - elif base_law_type == "대통령령": return searchKey = f"{context} 시행규칙"
   - elif base_law_type in ["총리령","부령"]: return resolution="self"
4) if anchor_text in ["고시","훈령","예규","지침","공고"]:
   - return type="admin_rule", resolution="ambiguous"
5) 그 외: unresolved/ambiguous

---

## 5) DB/검색과의 연결(해결/미해결 플래그)
정규화된 `searchKey`가 생기면 DB에서 조회를 한 번 더 해:
- `SELECT law_key FROM law WHERE law_name = :searchKey AND is_current='Y' LIMIT 1;`
- 찾으면 `resolution="resolved"` + `lawKey` 세팅
- 못 찾으면 `resolution="unresolved"`로 남김

---

## 6) 테스트 케이스(필수로 통과)

### 케이스 1: 법률에서 대통령령
입력:
- baseLawName="전기사업법", baseLawType="법률"
- anchorText="대통령령"
출력:
- searchKey="전기사업법 시행령"

### 케이스 2: 법률에서 ○○부령
입력:
- baseLawName="전기사업법", baseLawType="법률"
- anchorText="기후에너지환경부령"
출력:
- searchKey="전기사업법 시행규칙"
- issuerHint="기후에너지환경부"(옵션)

### 케이스 3: 다른 법 컨텍스트
문장: “「신에너지…법」 제2조 … 대통령령으로 정하는 …”  
입력:
- contextLawName="신에너지 및 재생에너지 개발ㆍ이용ㆍ보급 촉진법"
- anchorText="대통령령"
출력:
- searchKey="신에너지 및 재생에너지 개발ㆍ이용ㆍ보급 촉진법 시행령"

### 케이스 4: 시행령 안의 대통령령
입력:
- baseLawName="전기사업법 시행령", baseLawType="대통령령"
- anchorText="대통령령"
출력:
- resolution="self" (외부 문서 링크로 만들지 않음)

---

## 7) 구현 시 주의(품질 기준)
- “대통령령=무조건 시행령”은 **현재 문서가 법률일 때만** 기본 적용.
- 컨텍스트 법령명이 있으면 **그 법의 시행령/규칙으로 우선**.
- `related_laws`는 “많이”보다 “정확히”가 우선이라, 애매하면 `unresolved/ambiguous`로 남겨.

---

## 8) 산출물
- `normalize_delegation_term.py`
- `extract_context_law_name.py`
- `related_laws_enricher.py` (HTML 파싱→정규화→DB resolve)
- 유닛테스트: 위 4개 케이스 포함
