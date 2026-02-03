# 작업지시서: 연계/참조 법령 추출 정확도 개선 (스코프 + 그룹핑 + 정규화)

목표: `law.go.kr`에서 받은 HTML(`type=html`, `div#conScroll`)을 파싱하여 **특정 조문(예: 제2조) 단위로만** 연계/참조(refs)를 추출하고, **인접한 a태그를 결합**하여 사람이 읽는 형태의 참조(“전기사업법 제7조제1항”, “신에너지…법 제2조제3호”)로 정규화한다.

---

## 0) 배경(현재 문제)

현재 결과(`dry_run_result.json`)에서 아래 문제가 동시에 발생:

1. **스코프 터짐**: “제2조”에서만 뽑아야 하는데 법 전체에서 a태그가 섞여 들어옴  
2. **인접 앵커 결합 실패**: `제7조` + `제1항` / `「법률명」` + `제2조` + `제3호`가 한 참조로 결합되지 않음  
3. **외부 법률 링크 누락**: `「…」` 형태의 법률명 링크가 제대로 target으로 반영되지 않음  
4. **위임(대통령령/부령)**: 방향은 맞지만 중복이 너무 많음(조문 내 다회 발생) → dedup 필요

---

## 1) 입력/출력 정의

### 입력
- `lsInfoR_body.html` 또는 `lawService.do?...&type=html` 응답에서 조문 본문이 포함된 HTML 문자열

### 출력(권장 스키마)
각 조문별로 `refs`(리스트) 생성. “원본 증거”와 “정규화 결과”는 분리.

```json
{
  "lawName": "전기사업법",
  "articleNo": 2,
  "refs": [
    {
      "kind": "internal_citation | external_citation | delegation",
      "display": "전기사업법 제7조제1항",
      "target": {
        "lawName": "전기사업법",
        "lawType": null,
        "ref": {"article": 7, "paragraph": 1, "item": null, "subitem": null},
        "link": {"lsJoLnkSeq": null, "url": null}
      },
      "evidence": {
        "groupKey": "p.pty1_de2h@idx=123",
        "anchors": [
          {"text": "제7조", "href": "javascript:;", "onclick": "javascript:fncLsLawPop('1029857531','JO','');"},
          {"text": "제1항", "href": "javascript:;", "onclick": "javascript:fncLsLawPop('...','JO','');"}
        ],
        "snippet": "4. “발전사업자”란 제7조 제1항에 따라 ..."
      }
    }
  ],
  "debug": {...}
}
```

---

## 2) 1차 수정: “조문 스코프”를 정확히 자르기

### 핵심 규칙
- `div#conScroll` 전체를 긁지 말고 **조문 1개를 감싸는 컨테이너(보통 `div.lawcon`) 단위로 분리**한 후, **해당 조문 블록 내부에서만** a태그를 추출한다.

### 구현 가이드
1) `soup.select("div#conScroll div.lawcon")`로 조문 블록 리스트를 가져온다.  
2) 각 `lawcon`에서 “조문번호”를 판별한다.
   - `lawcon.get_text(" ", strip=True)`에서 정규식 `^제\s*(\d+)(의\d+)?조` 매칭
   - 또는 조문제목/조문본문이 들어있는 헤더 영역이 있다면 그쪽을 우선
3) `articleNo==2`인 블록 **단 1개만 선택**하고, 그 블록 내부에서만 refs 추출

#### Acceptance (전기사업법 제2조)
- 제2조 추출 결과에 **제173조, 제98조 등** “제2조 본문에 존재할 수 없는” refs가 섞이면 실패

---

## 3) 2차 수정: “인접 앵커 그룹핑” (가장 중요)

### 목표
같은 문장/문단(같은 parent)에서 **연속으로 등장하는 a태그**를 묶어 “하나의 참조”로 만든다.

### 그룹 키(groupKey)
- 기본: parent element 기준(예: `<p class="pty1_de2h">` 하나)
- `groupKey = f"{parent.tag}.{'.'.join(parent.get('class', []))}@idx={ordinal}"`

### 그룹핑 규칙
- **같은 parent** 안에 있는 `<a>`들의 **순서를 유지**한다.
- 그룹은 “의미 단위”로 끊는다.

#### 그룹 “끊기” 기준(간단)
- 앵커 사이에 **‘법률명 없이’ 조문/항/호만 반복**되는 경우는 같은 내부참조로 이어지지 않게(과확장 방지)
- 외부법령은 **법률명(「…」)** 앵커가 등장하면 새로운 외부참조 그룹 시작
- 위임 키워드(대통령령/총리령/부령/…부령)는 **단독 그룹**(그 자체가 하나의 참조)

### 케이스별 결합 로직

#### A) 내부참조(동일 법령)
예: `제7조` + `제1항` → “전기사업법 제7조제1항”

- 패턴:
  - `제(?P<art>\d+(?:의\d+)?)조`
  - `제(?P<p>\d+)항`
  - `제(?P<i>\d+)호`
  - `제(?P<si>\d+)목`
- 결합:
  - art가 있으면 base=art
  - 뒤따르는 항/호/목을 suffix로 붙임(“제7조제1항제2호…” 형태)
- 내부참조의 lawName은 **현재 조문 lawName**으로 강제(“전기사업법”)

#### B) 외부법령(다른 법)
예: `「신에너지 및 재생에너지 개발ㆍ이용ㆍ보급 촉진법」` + `제2조` + `제3호`

- 그룹 내에 `「...」` 형태가 있으면 external 시작
- 법률명 앵커에서 lawName=그 텍스트(괄호 포함/제거는 표준화에서 처리)
- 뒤따르는 조문/항/호는 external target ref로 채움
- 최종 display: “신에너지 및 재생에너지 개발ㆍ이용ㆍ보급 촉진법 제2조제3호”

#### C) 위임(대통령령/부령/총리령/…)
예: “대통령령” → “전기사업법 시행령”
예: “기후에너지환경부령” → “전기사업법 시행규칙”

- 조문 lawName이 “OOO법”이면
  - 대통령령 → “OOO법 시행령”
  - 총리령/부령/…부령 → “OOO법 시행규칙”
- 단, 법령이 “OOO령/OOO규칙”인 경우 매핑은 별도 규칙(가능하면 후속)

#### Acceptance (전기사업법 제2조)
최소 아래 항목이 출력에 존재해야 함(중복은 dedup 처리):
- 전기사업법 제7조제1항
- 전기사업법 제7조의2제1항
- 전기사업법 제35조
- 전기사업법 시행령(대통령령 위임)
- 전기사업법 시행규칙(기후에너지환경부령 위임)
- 환경친화적 자동차의 개발 및 보급 촉진에 관한 법률 제2조제3호
- 신에너지 및 재생에너지 개발ㆍ이용ㆍ보급 촉진법 제2조제2호
- 신에너지 및 재생에너지 개발ㆍ이용ㆍ보급 촉진법 제2조제3호
- 전기안전관리법 (법률명만)
- 댐건설ㆍ관리 및 주변지역지원 등에 관한 법률 (법률명만)

---

## 4) 3차 수정: Dedup 전략(조문 단위)

조문 내에서 같은 참조가 여러 번 나오므로 dedup 필요.

### Dedup Key (권장)
- `kind + normalized_lawName + ref.article + ref.paragraph + ref.item + ref.subitem + lawType + link.lsJoLnkSeq`
- 위임은 `normalized_lawName`만으로 dedup (시행령/시행규칙 각각 1개)

### 남길 정보
- 대표 evidence 1개 + occurrenceCount(몇 번 등장했는지)
- 또는 evidence를 3개까지만 보존(디버깅용)

---

## 5) 외부법령 “링크/아이디” 보강(가능하면)

관찰: 외부법령은 `lsJoLnkSeq`가 살아있는 경우가 있음.
예:  
`https://www.law.go.kr/LSW/lsLinkCommonInfo.do?lsJoLnkSeq=1029857505&chrClsCd=010202&ancYnChk=`

### 처리 방침
- 외부법령 그룹에서 onclick 또는 별도 링크 파라미터로 `lsJoLnkSeq`를 파싱할 수 있으면 저장
- 저장만 하고, 본문 크롤링(fetch)까지는 **옵션 플래그**로 분리 (콜 폭증 방지)

---

## 6) 구현 파일 구조(리팩토링 가이드)

- `src/html_fetcher.py`
  - `fetch_law_html(oc, mst) -> html`
- `src/article_scope.py`
  - `split_articles(html) -> list[ArticleBlock]`
  - `pick_article(blocks, article_no) -> ArticleBlock`
- `src/ref_extractor.py`
  - `extract_anchor_groups(article_block) -> list[AnchorGroup]`
  - `normalize_group(group, current_law_name) -> Ref | None`
  - `dedup_refs(refs) -> refs`
- `src/models.py`
  - dataclasses/pydantic: Anchor, AnchorGroup, Ref, Evidence, TargetRef
- `tests/test_article2_refs.py`
  - 전기사업법 제2조 HTML fixture 기반으로 acceptance 검증

---

## 7) 테스트(필수)

### 7.1 단위 테스트
- 입력: 전기사업법 HTML(최소 제2조 포함)
- 기대: 위 “Acceptance 목록”이 모두 존재 + 스코프 오염(제173조 등) 없음

### 7.2 회귀 테스트(스코프)
- article_no=2로 뽑았는데 refs 중 `article >= 100` 같은 값이 섞이면 실패(전기사업법 기준)

---

## 8) 구현 순서(권장)

1) `article_scope`로 lawcon 분리 + 제2조 단일 블록만 추출
2) 그 블록에서 parent 기준으로 anchor groups 생성
3) group normalize(내부/외부/위임)
4) dedup + occurrenceCount
5) 테스트 통과 후 다른 조문으로 확장

---

## 9) Done 정의

- 전기사업법 제2조의 refs가 “조문 범위 내”로만 추출됨
- 인접 앵커 결합으로 사람이 읽는 참조가 생성됨
- 외부법령(「…」)이 target으로 빠짐 없이 남음
- 위임은 시행령/시행규칙으로 매핑되어 1개씩만 남음(dedup)
