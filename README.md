# law-refs-pipeline

법령 HTML에서 연계법령(참조 링크/onclick 등)을 추출하고, 구조화된 결과를 DB에 저장하는 파이프라인입니다.  
코드는 책임 영역별로 분리되어 있으며, `law_refs` 패키지가 **프로덕션 기준**입니다.

## 핵심 기능
- HTML에서 조문 본문 영역 탐색
- 조문 내 연계법령 추출 (citation / delegation / range)
- 결과 JSON 구조화 및 DB 업데이트

## 디렉터리 구조
```
src/
  law_refs/
    domain/     # 모델/정규화 규칙
    parsing/    # HTML locator, 추출 로직
    db/         # DB 연결/업데이트
    services/   # 파이프라인 오케스트레이션
    cli/        # 실행 엔트리
scripts/
  scratch_extract_related.py  # 실험용 실행 스크립트
tests/
  test_html_locator.py
  test_related_extract.py
  test_repo_upsert.py
data/
  samples/      # 샘플 HTML
```

## 설치
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 환경 변수 (DB)
```bash
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=law_info
export PGUSER=postgres
export PGPASSWORD=postgres
```

## 사용법

### 1) Dry-run (DB 없이 JSON 출력)
```bash
python -m law_refs.cli.main \
  --input-html out/lsInfoR_body.html \
  --law-key LAW_001854 \
  --article-key 0002001 \
  --law-name 전기사업법 \
  --law-type 법률 \
  --dry-run
```

### 2) DB 업데이트
```bash
python -m law_refs.cli.main \
  --input-html out/lsInfoR_body.html \
  --law-key LAW_001854 \
  --article-key 0002001 \
  --law-name 전기사업법
  --law-type 법률
```

## DB 스키마
`law_article`에 `related_laws jsonb` 컬럼이 필요합니다.  
SQL: `cursor/db_plan_c.sql` 참고.

## 위임입법 정규화
`대통령령/총리령/부령` 표현은 **검색 가능한 문서명**으로 정규화됩니다.  
현재 문서의 법종(`--law-type`)과 컨텍스트 법령명에 따라 `시행령/시행규칙`으로 변환됩니다.

## 테스트
```bash
pytest -q
```

## 단순화 JSON 생성
```bash
python scripts/simplify_related_refs.py \
  --input out/dry_run_result.json \
  --output out/related_refs.simple.json \
  --law-name 전기사업법 \
  --law-key LAW_001854 \
  --article-no 2
```

## Deprecated
`src/refs`는 기존 구현이며 **deprecated** 상태입니다.  
신규 개발은 반드시 `src/law_refs`를 사용하세요.

