# 법령 연계 파이프라인 리팩토링 작업지시서 (Cursor용)

목표: 이 프로젝트를 **3가지 책임 영역**으로 명확히 분리하고, 테스트/실험 코드를 정리해서 “프로덕션 코드 vs 실험 코드” 경계를 깔끔하게 만든다.

- (1) HTML을 파싱해서 “진짜 조문 HTML”을 찾는 코드
- (2) 조문 HTML에서 **연계법령(참조 링크/onclick 등)** 을 추출하는 코드
- (3) DB(포스트그레스) 연결 및 upsert/update 하는 코드

---

## 0) 리팩토링 원칙

### A. 계층 분리
- **domain(규칙/모델)**: 법령/조문/참조(연계) 구조 정의
- **adapters(입출력)**: HTML 파일 읽기, DB 쓰기, (필요시) URL fetch
- **services(유스케이스)**: “조문 1개 처리” 같은 순서/흐름만 담당
- **cli/scripts**: 실행 엔트리포인트. *테스트/실험은 여기로 격리*

### B. 함수는 “한 가지 일”만
- HTML “찾기” / HTML “파싱” / “정규화” / “DB저장”을 한 함수에 섞지 않는다.

### C. I/O는 바깥으로
- 파서/추출 로직은 **문자열 입력 → 구조화 출력**만 하게 만들고,
- 파일 읽기/쓰기, DB 연결은 별도 레이어로 뺀다.

---

## 1) 추천 디렉토리 구조 (Python)

아래 중 **src 레이아웃**을 추천.

```
repo/
  pyproject.toml
  README.md
  src/
    law_refs/
      __init__.py

      domain/
        models.py          # dataclass/pydantic 모델
        types.py           # Enum, 타입 alias
        normalize.py       # 텍스트/anchor 정규화 규칙

      parsing/
        html_locator.py    # (1) “진짜 HTML” 찾기
        html_extract.py    # HTML에서 필요한 영역만 뽑기(조문 body 등)
        related_law_extract.py  # (2) 연계법령 추출 핵심

      db/
        config.py          # DSN/ENV 로딩
        connection.py      # psycopg/SQLAlchemy 연결
        repo.py            # (3) insert/update/upsert 함수

      services/
        enrich_article.py  # 조문 1개 enrich하는 유스케이스(파싱→추출→저장)
        pipeline.py        # 파일/배치 실행 흐름

      cli/
        main.py            # CLI 엔트리 (argparse/typer 중 택1)
  scripts/
    scratch_*.py           # 실험용/검증용(테스트가 아닌) 스크립트
  tests/
    test_html_locator.py
    test_related_extract.py
    test_repo_upsert.py
  data/
    samples/               # 샘플 HTML/JSON (작게)
```

---

## 2) 핵심 인터페이스 설계 (먼저 “계약”을 고정)

### (1) html_locator: “진짜 조문 HTML” 찾기
**입력**: 원본 HTML 문자열(혹은 BeautifulSoup)  
**출력**: 조문 본문에 해당하는 HTML fragment 문자열 + 메타

권장 시그니처:

```py
# src/law_refs/parsing/html_locator.py
from dataclasses import dataclass

@dataclass
class LocatedHtml:
    body_html: str          # 조문영역 HTML (string)
    strategy: str           # 어떤 규칙으로 찾았는지
    debug: dict             # selector hit 등

def locate_article_body_html(raw_html: str) -> LocatedHtml:
    ...
```

- 여기서는 “찾기”만 한다. 연계법령 추출/정규화는 하지 않는다.

---

### (2) related_law_extract: 연계법령 추출
**입력**: 조문 body_html (위에서 나온 fragment)  
**출력**: `RelatedLawRef[]` 리스트

```py
# src/law_refs/domain/models.py
from dataclasses import dataclass
from typing import Optional, Literal

RefType = Literal["citation", "delegation", "range", "unknown"]

@dataclass
class AnchorEvidence:
    anchor_text: str
    href: Optional[str]
    onclick: Optional[str]
    snippet: str            # “anchor 주변 텍스트” (짧게)
    group_key: Optional[str] = None  # 연속 a태그 그룹핑용

@dataclass
class RelatedLawTarget:
    law_name: Optional[str] = None
    law_id: Optional[str] = None
    article: Optional[int] = None
    paragraph: Optional[int] = None
    item: Optional[int] = None
    subitem: Optional[int] = None

@dataclass
class RelatedLawRef:
    type: RefType
    target: RelatedLawTarget
    evidence: AnchorEvidence
    confidence: float
```

추출 함수:

```py
# src/law_refs/parsing/related_law_extract.py
from typing import List
from law_refs.domain.models import RelatedLawRef

def extract_related_laws(body_html: str, *, current_law_name: str) -> List[RelatedLawRef]:
    ...
```

#### 그룹핑 규칙(중요)
- **중간에 일반 텍스트 없이 연속된 a태그**는 한 그룹으로 묶어서 “법령명 + 조문” 형태를 최대한 구성
- BUT “대통령령 / 기후에너지환경부령” 같은 위임 표현은 별도 type=`delegation`로 분리 가능
- range 표현(“제n항부터 제m항까지”)은 type=`range`로 만들고, target.ref에 `from/to`를 별도 필드로 둘지(추천) 결정

---

### (3) db repo: 저장 계층
**입력**: law_key, article_key(or uid) + related_laws JSON  
**출력**: rows affected / 성공 여부

권장:

```py
# src/law_refs/db/repo.py
from typing import Sequence
from law_refs.domain.models import RelatedLawRef

def update_related_laws(
    conn,
    *,
    law_key: str,
    article_key: str,
    related_laws: Sequence[RelatedLawRef],
) -> int:
    ...
```

- 여기서 JSON 직렬화는 repo에서 하거나, service에서 미리 dict로 바꿔서 내려도 됨.
- DB는 “연결/커밋/롤백” 전략을 한 곳으로 모은다.

---

## 3) “실행 흐름”은 services로 묶기

```py
# src/law_refs/services/enrich_article.py
from law_refs.parsing.html_locator import locate_article_body_html
from law_refs.parsing.related_law_extract import extract_related_laws
from law_refs.db.repo import update_related_laws

def enrich_one_article(conn, *, law_key: str, article_key: str, raw_html: str, current_law_name: str) -> int:
    located = locate_article_body_html(raw_html)
    refs = extract_related_laws(located.body_html, current_law_name=current_law_name)
    return update_related_laws(conn, law_key=law_key, article_key=article_key, related_laws=refs)
```

- 이 함수는 “오케스트레이션”만 한다.

---

## 4) 테스트/실험 코드 정리 방식

### A. 진짜 테스트는 tests/로
- 파서/추출기는 **샘플 HTML 한두 개**로 단위테스트가 가장 효과적임.
- DB는 integration test로 분리하거나, repo.py는 SQL만 검증(스냅샷)하는 방식도 가능.

### B. 실험/검증 스크립트는 scripts/로
- `scripts/scratch_extract_related.py` 같은 파일로 옮기고,
- “이 파일은 실험용” 주석 + argparse로 입력 파일 경로만 받게

---

## 5) Cursor에게 시킬 “구체 작업 목록”(순서 고정)

1. **src/law_refs/** 패키지 생성하고 기존 코드들을 “책임별 파일”로 이동
2. 기존에 섞여 있던 함수들을 아래 3개로 쪼개기
   - `locate_article_body_html(raw_html)`
   - `extract_related_laws(body_html, current_law_name=...)`
   - `update_related_laws(conn, law_key, article_key, related_laws)`
3. 기존 테스트/프린트/노트북성 코드 전부 `scripts/`로 이동
4. `cli/main.py` 하나 만들고, 아래 옵션 지원
   - `--input-html path`
   - `--law-key`, `--article-key`, `--law-name`
   - `--dry-run` (DB 저장 없이 stdout에 결과 JSON 출력)
5. `tests/`에 최소 3개 테스트 추가
   - locator: 특정 selector에서 body_html을 제대로 뽑는지
   - extractor: 연속 a태그 그룹핑이 기대대로 나오는지
   - repo: JSON 저장 컬럼 업데이트 SQL이 기대대로 생성되는지(또는 통합 테스트)

---

## 6) “지금 상황”에 맞춘 현실적인 단순화 옵션

### 옵션 1) onclick은 Evidence로만 두고, Target 파싱은 최소화
- `lawName + anchorText` 정도만 target에 담고
- 나중에 별도 파이프라인에서 “정규화(법령ID, 조문번호 확정)”를 수행

### 옵션 2) Target을 최대한 확정(파싱 난이도↑)
- anchorText 그룹핑 + 정규식으로 `법령명/제n조/제m항/제k호`를 최대한 분해
- 실패하면 type=`unknown`, confidence 낮게

---

## 7) Done 기준 (리팩토링 완료 정의)

- `python -m law_refs.cli.main --dry-run ...` 으로 결과 JSON이 한번에 나온다
- DB update는 `services/enrich_article.py` 한 군데에서만 호출된다
- `scripts/`에 있는 파일이 없어도 패키지가 동작한다
- tests 3개 이상 통과

---

## 8) Cursor에게 붙여넣을 짧은 명령 프롬프트(요약)

- “기존 코드를 src/law_refs/로 옮기고, locator/extractor/repo 3개로 책임 분리해라.”
- “scripts/로 실험 코드 이동, tests 3개 추가, CLI 엔트리 만들어라.”
- “extractor는 연속 a태그 그룹핑을 지원하고 evidence.snippet은 anchor 주변 텍스트로 짧게 만든다.”
