# refs 모듈 구조 요약

이 문서는 연계법령 추출/정규화/병합 파이프라인의 코드 구조를 트리 형태로 정리한 문서다.

## 디렉터리 트리
```
/Users/parkjinkyung/Documents/work_src/html_par/
├─ src/
│  └─ refs/
│     ├─ __init__.py
│     ├─ types.py
│     ├─ extract_candidates.py
│     ├─ group_runs.py
│     ├─ range_parser.py
│     ├─ normalize_refs.py
│     ├─ enrich_json.py
│     ├─ lawgo_client.py
│     └─ README.md
└─ tests/
   ├─ test_group_runs.py
   └─ test_range_parser.py
```

## 파일별 역할/기능

### `src/refs/__init__.py`
- 패키지 선언용 파일.

### `src/refs/types.py`
- 데이터 구조 정의.
- `CandidateURL`에 context/snippet/onclick 등 추출 메타 정보를 포함.

### `src/refs/extract_candidates.py`
- HTML에서 연계법령 후보 추출.
- 소스: `a[href]`, `onclick`, `iframe src`, `script` 내 URL.
- a태그 기준 스니펫(window) 생성.
- 출력: `out/candidates.json`.

### `src/refs/group_runs.py`
- 같은 부모 블록 내 연속 a태그(run) 그룹화.
- a 사이 텍스트가 공백/구두점이면 같은 run으로 묶음.
- 출력: `out/runs.json`.

### `src/refs/range_parser.py`
- 범위표현 파서(`제1항부터 제5호까지` 등).
- `ref_range` 구조 생성을 위한 from/to 파싱.

### `src/refs/normalize_refs.py`
- run 기반 정규화.
- 분류: `citation`, `delegation`, `range`.
- `target.ref` 스키마 (article/paragraph/item/subitem).
- `evidence`에 anchorText/onclick/href/snippet/groupAnchors 포함.
- 출력: `out/normalized_refs.jsonl`.

### `src/refs/enrich_json.py`
- 정규화 결과를 `전기사업법.json`에 병합.
- `related_laws` 배열로 추가.
- dedupe 규칙 적용.
- 출력: `out/전기사업법.enriched.json`.

### `src/refs/lawgo_client.py`
- ONLINE 모드에서 law.go.kr API 호출(캐시 포함).
- 토큰/키는 환경변수 사용.

### `src/refs/README.md`
- 실행 방법/CLI 예시/파이프라인 설명.

### `tests/test_group_runs.py`
- run 그룹화 동작 테스트.

### `tests/test_range_parser.py`
- 범위표현 파싱 테스트.


