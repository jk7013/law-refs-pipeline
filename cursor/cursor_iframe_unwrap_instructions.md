# Cursor 지시사항: iframe(src) 풀어서 본문 HTML 가져오기 (전기사업법)

## 목표
- 지금 가진 `전기사업법.html`은 **iframe 래퍼(껍데기)**라서 본문/연계링크가 안 들어있어.
- 이 파일에서 `<iframe ... src="...">`의 **src URL을 추출**하고,
- 그 src URL을 **직접 HTTP GET** 해서 **실제 본문 HTML**을 저장/파싱하는 코드를 만들어줘.

---

## 입력 파일
- `./전기사업법.html` (업로드된 파일)
- (참고) `./전기사업법.json`, `./전기사업법.xml` 은 이번 작업에 필수는 아님

---

## 산출물(파일)
1) `out/iframe_src.txt`  
   - 추출한 iframe src URL 1줄로 저장

2) `out/lsInfoP_raw.html`  
   - iframe src를 GET 해서 받은 원문 HTML 저장

3) `out/links.json`  
   - (가능하면) 본문 HTML에서 발견한 링크들(특히 law.go.kr 도메인)과 앵커텍스트를 JSON 배열로 저장  
   - 예: `[{ "text": "...", "href": "..." }, ...]`

4) `out/run.log`  
   - 실행 로그(추출 성공/실패, HTTP 상태코드, 리다이렉트 여부, 저장 경로)

---

## 구현 요구사항
### A. iframe src 추출
- 파서: `BeautifulSoup` 또는 `lxml` 사용
- `<iframe id="lawService">`가 있으면 그걸 우선 사용
- 없으면 첫 번째 iframe을 사용
- src가 상대경로일 수 있으니 base URL을 보정:
  - 상대경로면 `https://www.law.go.kr`를 prefix로 붙여서 절대 URL로 만들기

### B. HTTP GET로 본문 HTML 다운로드
- Python `requests` 사용
- 기본 헤더 권장:
  - `User-Agent`: 브라우저 비슷하게
  - `Accept-Language`: `ko-KR,ko;q=0.9,en;q=0.8`
- 리다이렉트 허용(`allow_redirects=True`)
- 응답 인코딩 처리:
  - `response.apparent_encoding` 또는 `response.encoding` 확인 후 `response.text` 사용
- 실패 시(4xx/5xx) 에러 메시지와 상태코드 로그 남기기

### C. 링크 파싱(가능하면)
- 저장한 `lsInfoP_raw.html`을 다시 파싱해서:
  - `<a href=...>` 전부 수집
  - `href`가 `javascript:`면 일단 제외(또는 별도 리스트로 분리)
  - 절대/상대 URL 정규화
- 특히 law.go.kr 관련 링크가 있으면 우선적으로 확인

### D. CLI 형태로 만들기
- 실행 예:
  - `python fetch_iframe.py --in 전기사업법.html --outdir out`
- 옵션:
  - `--timeout` (기본 20초)
  - `--verify-ssl` (기본 True)
  - `--show-top-links N` (기본 20, 콘솔에 상위 N개 출력)

### E. 보안/환경 모드(듀얼)
- `ONLINE` 모드: 실제 law.go.kr에 요청
- `OFFLINE` 모드: 네트워크 요청 금지
  - `OFFLINE`에서는 **src 추출까지만** 하고 종료(로그에 안내)
- 모드 선택:
  - 환경변수 `JIDO_MODE=OFFLINE|ONLINE` 또는 CLI `--mode`

---

## 폴더 구조 제안
```
.
├─ fetch_iframe.py
├─ requirements.txt
├─ out/
│  ├─ iframe_src.txt
│  ├─ lsInfoP_raw.html
│  ├─ links.json
│  └─ run.log
└─ 전기사업법.html
```

`requirements.txt`:
- beautifulsoup4
- lxml
- requests

---

## 테스트 체크리스트
- [ ] `전기사업법.html`에서 iframe src가 추출되고 `out/iframe_src.txt` 생성됨
- [ ] ONLINE 모드에서 `out/lsInfoP_raw.html`이 생성됨
- [ ] `links.json`에 최소 몇 개 이상의 링크가 수집됨
- [ ] OFFLINE 모드에서는 네트워크 호출이 발생하지 않음
- [ ] 실패 시에도 `run.log`에 원인(상태코드/예외)이 남음

---

## 주의
- 이 작업은 “iframe src가 가리키는 HTML을 그대로 받기”가 1차 목표야.
- 연계법령 링크가 추가 호출(JS/AJAX)로 생성되는 경우, 다음 단계에서 **네트워크 트래픽 기반으로 추가 API를 추적**해야 할 수 있어. (이번 지시에서는 1차까지만)
