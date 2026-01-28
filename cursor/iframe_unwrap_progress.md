# 진행 상황 정리: iframe → 본문 HTML 추출 및 저장 구조

## 1) 목표
- `전기사업법.html`의 iframe(src)에서 본문 HTML을 받아오고,
- 브라우저 렌더링 결과(`answer.html`) 수준의 HTML을 재현,
- 연계법령(링크) 추출 및 대량 수집을 위한 기반 마련.

## 2) 확인된 구조
- `전기사업법.html` → iframe src → `lsInfoP_raw.html` 수신
- `lsInfoP_raw.html` 내부 JS가 `lsInfoR.do`에 **POST**로 본문 HTML을 요청
- 브라우저에서 `document.documentElement.outerHTML`로 얻는 `answer.html`은
  **`lsInfoP_raw.html` + `lsInfoR.do` 응답을 DOM에 주입**한 결과

## 3) 구현된 스크립트
### `fetch_iframe.py`
기능:
- iframe src 추출 (`out/iframe_src.txt`)
- iframe src GET (`out/lsInfoP_raw.html`)
- `lsPopViewAll2(...)` 파라미터 추출
- `lsInfoR.do` POST로 본문 HTML 수신
- 원문/본문 병합 HTML 생성
- 링크 파싱(`links.json`)

추가된 산출물:
- `out/lsInfoR_body.html`: `lsInfoR.do` 응답 HTML
- `out/lsInfoP_full.html`: `lsInfoP_raw.html` + 본문 주입 결과
- `out/run.log`: 요청/상태/오류 로그

## 4) 실행 결과 (샘플)
- `lsInfoR.do` POST 성공(HTTP 200)
- `out/lsInfoP_full.html` 생성
- `answer.html`과 동일 계열 DOM 재현 확인

## 5) 대량 수집 관점 결론
- 현재 구조는 **건당 2회 요청**(iframe + lsInfoR)
- 최적화를 위해서는 `lsiSeq`를 **처음부터 DB에 저장**해야 1회 호출로 줄일 수 있음
- `전기사업법.json`에는 `lsiSeq`가 없음 → 별도 매핑 저장 필요

## 6) PostgreSQL 상태
### 기존 테이블
- `public.law_list`
- `public.law_detail` (컬럼: `law_id`, `json`, `html`, `xml`, ...)

### 신규 테이블 생성
테이블: `public.law_rendered`
```
law_id        varchar(256) NOT NULL
lsi_seq       varchar(64)  NOT NULL
anc_yd        varchar(8)
anc_no        varchar(16)
ef_yd         varchar(8)
chr_cls_cd    varchar(6)
anc_yn_chk    varchar(2)
iframe_src    text
lsinfoR_params jsonb
html_body     text
html_full     text
status_code   integer
fetch_error   text
fetched_at    timestamp default now()
updated_at    timestamp default now()
PRIMARY KEY (law_id, lsi_seq)
```
인덱스:
- `UNIQUE (lsi_seq)`
- `INDEX (law_id)`

## 7) 현 상태 요약
- 스크립트로 `answer.html` 계열 HTML 생성 가능
- 본문 요청 파라미터 및 `lsiSeq` 확보 성공
- DB에 `lsiSeq` 및 렌더링 결과 저장할 테이블 확보

## 8) 다음 단계
- `fetch_iframe.py`에서 `law_rendered` 테이블로 저장 로직 추가
- 대량 수집 시: 속도 제한/재시도/캐시 적용

