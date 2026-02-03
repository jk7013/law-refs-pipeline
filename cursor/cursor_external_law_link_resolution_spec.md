# [Cursor 작업지시서] 외부 연계법령 링크(조문정보 팝업)까지 추적·저장·해소하기

> 목적: 전기사업법 본문에서 “사방사업법 제14조”처럼 **외부법령 링크가 살아있는 케이스**를 정확히 인식하고,  
> 1) 링크 식별자/URL을 저장하고, 2) 링크를 따라가 **실제 외부법령 조문(법령명/조문/제목/본문)**을 확보해서, 3) 최종적으로 `related_refs`를 “깨끗한 형태”로 만들기.

---

## 0) 문제 증상(현재 결과의 핵심 문제)

### A. 외부법령 참조가 “전기사업법 내부 조문”으로 잘못 붙음
- 예) 본문: `「사방사업법」 제14조 ...`
- 현재 파서 결과: `lawName=전기사업법` / `article=null` / `anchorText=제1항` 같은 형태로 저장되거나,
- 또는 `lawName=전기사업법, article=2 ...`처럼 내부조문으로 오인 매핑됨.

### B. **외부법령**은 실제로 “조문정보 팝업” URL이 존재하는데, 그 URL/식별자를 저장하지 않음
- 사용자가 확인한 팝업 URL 예:
  - `https://www.law.go.kr/LSW/lsLinkCommonInfo.do?lsJoLnkSeq=1029857729&chrClsCd=010202&ancYnChk=`
- 이 링크 하나 + “제14조” 조합이면 최종적으로 **사방사업법 제14조 본문**까지 가져올 수 있음.
- 그런데 현재 JSON에는 `onclick`의 내부 ID만 있고, 외부 링크 추적이 없음.

---

## 1) 목표 결과(원하는 “정상 형태” 정의)

### 1-1. related_refs(혹은 related_laws) 엔트리는 “타겟을 명확히” 가져야 함
- 내부참조: `전기사업법 제7조` 등
- 외부참조: `사방사업법 제14조` 등
- 위임/위탁: `전기사업법 시행령`, `전기사업법 시행규칙` 등

### 1-2. **외부참조**는 아래를 반드시 저장
- (필수) `externalLink.url`  (lsLinkCommonInfo.do 전체 URL)
- (필수) `externalLink.lsJoLnkSeq`
- (가능하면) `externalLink.chrClsCd`, `externalLink.ancYnChk` (URL에 있으면 그대로 저장)
- (필수) `resolved` (크롤링/해소 후)
  - `resolved.lawName`
  - `resolved.article` (+ 필요 시 항/호/목)
  - `resolved.title` (조문제목)
  - `resolved.text` (조문내용 텍스트; HTML->텍스트 정규화)
  - `resolved.sourceUrl` (조문정보 URL 그대로)

---

## 2) DB 스키마 변경안 (권장: “원본”과 “가공결과” 분리)

> 원본 json은 따로 가지고 있다고 했으니, **참조해소 전/후**를 분리해서 저장해.

### 2-1. 테이블 A: law_article_ref  (기본법 조문에서 뽑힌 참조들)
- PK: `ref_id` (uuid or bigserial)
- FK: `base_law_key`, `base_article_no`, `base_article_key` 등 (현재 너희 law_article 기준)
- `ref_type` : enum(`internal_citation`, `external_citation`, `delegation`)
- `raw_anchor_text` : text (예: "제14조", "사방사업법", "대통령령")
- `raw_snippet` : text (해당 anchor가 포함된 근처 문장)
- `raw_group_key` : text (p#.pty1_de2h 같은 그룹키)
- `raw_group_anchors_json` : jsonb (같은 그룹 내 anchor 목록)
- `normalized_json` : jsonb (정규화된 타겟; 예: {"lawName":"사방사업법","ref":{"article":14}})
- `external_link_json` : jsonb NULL 가능
  - 예: {"url": "...lsLinkCommonInfo.do?...",
         "lsJoLnkSeq": "1029857729",
         "chrClsCd": "010202",
         "ancYnChk": ""}
- `resolve_status` : enum(`unresolved`,`resolved`,`failed`,`skipped`)
- `resolved_at` : timestamp
- `created_at`, `updated_at`

### 2-2. 테이블 B: law_external_ref_cache  (외부 링크를 따라가서 얻은 조문 캐시)
- PK: `lsJoLnkSeq` (문자열/빅인트; URL의 핵심키)
- `url` : text
- `law_name` : text
- `law_key` : text NULL (내부 law_key 체계에 매핑 가능하면)
- `article_no` : int NULL
- `article_title` : text NULL
- `article_text` : text NULL
- `fetched_html_hash` : text (변경 감지용)
- `fetched_at` : timestamp
- `fetch_status` : enum(`ok`,`failed`)
- `error` : text NULL

> 핵심: `law_article_ref`는 “참조 발생” 로그, `law_external_ref_cache`는 “참조 해소 결과” 캐시.
> 이렇게 해야 중복 호출도 줄고, 파서 개선해도 재사용 가능해.

---

## 3) 파서/정규화 규칙 수정

### 3-1. 외부법령 감지 우선순위
아래 중 하나라도 만족하면 **external_citation 후보**로 분류:

1) 문장 내에 `「...」` 패턴(법령명 괄호표기)이 있고, 그 뒤로 `제n조`가 나타난다.
2) anchor 태그 중에 URL 또는 onclick/href 패턴에서 `lsLinkCommonInfo.do` 또는 `lsJoLnkSeq=`가 보인다.
3) 그룹(p 태그) 내에 “법령명 anchor + 제n조 anchor”가 연속으로 붙어있다.
   - “사방사업법” (anchor) + “제14조” (anchor) + (공백/구두점 정도만) → 하나로 병합

> IMPORTANT: 외부법령로 판정되면 `target.lawName`을 기본법(전기사업법)으로 두면 안 됨.

### 3-2. “연속 anchor 병합” 규칙 (문맥 오염 방지)
- **병합 허용:** anchor 사이에 “실질 텍스트”가 없을 때만 합쳐라.
  - 허용되는 사이 텍스트: 공백, 줄바꿈, 괄호/따옴표, ‘ㆍ’, ‘,’, ‘및’, ‘의’ 등 아주 짧은 접속부(룰로 제한)
- **병합 금지:** anchor 사이에 일반 명사/서술이 들어가면 분리
  - 예) `「신에너지법」`(anchor) + `제2조`(anchor) + `에 따른`(텍스트) + `대통령령`(anchor)
    - 여기서 앞의 둘은 묶고, 대통령령은 별도

### 3-3. 내부참조(전기사업법 제7조 등) 정규화 규칙
- `제n조` anchor가 있으면: internal_citation으로 `article=n`
- `제1항`만 단독으로 나오면:
  - **앞쪽 텍스트/직전 anchor**에서 가장 가까운 `제n조`를 찾아서 보완
  - 못 찾으면 `resolution=unresolved`로 두되 “전기사업법 제?조”로 확정하지 말 것

### 3-4. 위임/위탁(대통령령/총리령/부령) 정규화
- 기존 만든 매핑 스펙 유지 + 추가:
  - 대통령령 → `{baseLawName} 시행령`
  - 총리령/부령/○○부령 → `{baseLawName} 시행규칙`
- BUT: `onclick`이 `fncLsPttnLinkPop('ID')`면 `pttnId`는 `external_link_json`에 저장해둬.
  - 나중에 “필요한 경우에만” 추가 해소(콜 제한)할 수 있게.

---

## 4) 외부 링크(조문정보) 해소 로직 추가

### 4-1. lsLinkCommonInfo 링크를 발견하면 무조건 저장
- `external_link_json.url`에 **완전한 URL** 저장
- `lsJoLnkSeq` 파라미터는 별도 필드로 파싱해서 저장
- `chrClsCd`, `ancYnChk`도 있으면 저장 (없으면 NULL)

### 4-2. “해소(resolution)”는 캐시 우선
- `law_external_ref_cache`에 `lsJoLnkSeq`가 있으면 재사용
- 없으면 HTTP GET으로 해당 URL 호출해서 HTML 확보 후 파싱
- 파싱 결과를 cache에 저장하고, `law_article_ref.resolved_json`(또는 normalized_json 업데이트)로 연결

### 4-3. 조문정보 페이지 HTML에서 뽑아야 하는 값
(페이지 구조는 실제 확인해서 selector를 고정)
- 법령명: 화면 상단 큰 제목 (예: “사방사업법”)
- 조문번호/제목: `제14조(사방지에서의 행위 제한)` 형태에서
  - article_no=14
  - article_title="사방지에서의 행위 제한"
- 조문 본문 텍스트: 해당 조문 본문(항/호 포함) 전체
- sourceUrl: 호출한 URL

> 추출 결과는 “텍스트 정규화” 필수(여백/개행 규칙 통일).  
> HTML 그대로 저장은 optional(캐시 용량 이슈 있으면 hash만).

---

## 5) 최종 “사방사업법 제14조까지 가져오기” 조건 정의

사용자가 말한 요구를 코드로 정리하면:

- (입력) 기본법 조문 HTML에서
  - a태그: “사방사업법” 링크
  - a태그: “제14조” 링크
- (목표) 최종적으로 `resolved`에
  - `lawName=사방사업법`
  - `article=14`
  - `title`과 `text`까지 채움

구현 포인트:
- “사방사업법” anchor가 단독으로 lsLinkCommonInfo를 갖고 있고,
- “제14조” anchor가 단독으로 lsLinkCommonInfo를 갖는 경우가 있으니,
  - 둘 중 어느 쪽에서든 `lsJoLnkSeq`를 발견하면 저장하고,
  - **병합 규칙**으로 “사방사업법 + 제14조”를 하나의 external_citation으로 만들어라.
- 만약 두 anchor의 lsJoLnkSeq가 서로 다르면:
  - “제14조” 쪽 lsJoLnkSeq를 우선 (조문 단위니까)

---

## 6) 테스트(필수)

### 6-1. 단위 테스트
- 입력: 전기사업법 HTML 일부(문장+anchor 조합)
- 기대:
  - external_citation 1개 생성
  - normalized.lawName="사방사업법"
  - normalized.ref.article=14
  - external_link_json.lsJoLnkSeq가 저장됨

### 6-2. 통합 테스트(네트워크 호출은 mock or 기록 재생)
- lsLinkCommonInfo URL 호출 결과 HTML fixture 저장
- resolver가 `law_external_ref_cache`에 저장하고 참조가 resolved로 바뀌는지 확인

### 6-3. 콜 제한(차단 방지)
- 동일 lsJoLnkSeq는 cache hit로 2회 이상 호출 금지
- 전체 배치 시 QPS 제한(예: 1~3 rps) + exponential backoff + 429/5xx 대응

---

## 7) 산출물(코드 구조 제안)

- `src/extract_refs.py` : base HTML에서 anchor 추출 + 초기 정규화
- `src/resolve_external.py` : lsLinkCommonInfo 기반 해소 + cache 저장
- `src/db.py` : DB 세션/쿼리
- `tests/fixtures/` : HTML fixture
- `tests/test_extract_refs.py`
- `tests/test_resolve_external.py`

---

## 8) Done 조건(완료 판정)

- 전기사업법 HTML에서 “사방사업법 제14조” 같은 외부참조를 발견하면,
  - `law_article_ref`에 external_citation이 생기고,
  - `external_link_json`에 lsLinkCommonInfo URL+lsJoLnkSeq가 저장되며,
  - resolver 실행 후 `law_external_ref_cache`에 (사방사업법, 제14조, 제목, 본문)이 채워지고,
  - `law_article_ref.resolve_status=resolved`가 된다.

