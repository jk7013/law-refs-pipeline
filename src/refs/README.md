# 연계법령 추출 및 정규화 모듈 (Deprecated)

이 모듈은 **deprecated** 상태입니다.  
신규 구현은 `src/law_refs/` 패키지를 사용하세요.

HTML에서 연계법령 정보를 추출하고 전기사업법.json에 병합하는 파이프라인입니다.

## 사용법

### 1단계: HTML에서 후보 URL 추출

```bash
python -m src.refs.extract_candidates --html out/lsInfoR_body.html --out out/candidates.json
```

### 2단계: 연속 a태그(run) 그룹화

```bash
python -m src.refs.group_runs --in out/candidates.json --out out/runs.json
```

### 3단계: 후보 URL 정규화

**OFFLINE 모드:**
```bash
python -m src.refs.normalize_refs --in out/runs.json --mode offline --out out/normalized_refs.jsonl
```

**ONLINE 모드:**
```bash
export LAWGO_OC=your_token  # 필요시
python -m src.refs.normalize_refs --in out/runs.json --mode online --out out/normalized_refs.jsonl
```

### 4단계: 전기사업법.json에 병합

```bash
python -m src.refs.enrich_json --law-json 전기사업법.json --refs out/normalized_refs.jsonl --out out/전기사업법.enriched.json
```

## 전체 파이프라인 실행 예시

```bash
# 1. 후보 추출
python -m src.refs.extract_candidates --html out/lsInfoR_body.html --out out/candidates.json

# 2. run 그룹화
python -m src.refs.group_runs --in out/candidates.json --out out/runs.json

# 3. 정규화 (OFFLINE)
python -m src.refs.normalize_refs --in out/runs.json --mode offline --out out/normalized_refs.jsonl

# 4. 병합
python -m src.refs.enrich_json --law-json 전기사업법.json --refs out/normalized_refs.jsonl --out out/전기사업법.enriched.json
```

## 출력 파일

- `out/candidates.json`: 추출된 후보 URL 목록
- `out/runs.json`: 연속 a태그 run 그룹
- `out/normalized_refs.jsonl`: 정규화된 참조 정보 (JSONL 형식)
- `out/전기사업법.enriched.json`: 연계법령 정보가 병합된 법령 JSON

## 모듈 구조

- `types.py`: 데이터 타입 정의
- `extract_candidates.py`: HTML에서 후보 URL 추출
- `group_runs.py`: 연속 a태그(run) 그룹화
- `normalize_refs.py`: URL 정규화 및 구조화
- `range_parser.py`: 범위 표현 파서
- `lawgo_client.py`: law.go.kr API 클라이언트 (ONLINE 모드)
- `enrich_json.py`: 법령 JSON에 연계법령 정보 병합

## 참고사항

- OFFLINE 모드는 외부 통신 없이 파라미터 기반으로만 정규화합니다.
- ONLINE 모드는 law.go.kr API를 호출하여 법령명을 확정합니다 (토큰 필요).
- HTML에서 조문 컨텍스트 파싱은 현재 기본 구현만 되어 있습니다. 더 정확한 매핑을 위해서는 HTML 구조 분석이 필요합니다.

