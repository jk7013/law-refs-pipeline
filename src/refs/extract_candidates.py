#!/usr/bin/env python3
"""
HTML에서 연계법령 후보 URL 추출
"""
import argparse
import json
import re
from pathlib import Path
from typing import List, Set, Optional
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup, NavigableString

from .types import CandidateURL


def extract_urls_from_onclick(text: str) -> List[str]:
    """onclick 속성에서 URL 추출"""
    urls = []
    # javascript:fncLsLawPop(...) 패턴
    patterns = [
        r"fncLsLawPop\(['\"]?([^'\")]+)['\"]?",
        r"fncLsPttnLinkPop\(['\"]?([^'\")]+)['\"]?",
        r"https?://[^'\")>\s]+",
        r"/[^'\")>\s]+",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        urls.extend(matches)
    return urls


def extract_urls_from_script(script_text: str) -> List[str]:
    """script 태그에서 URL 추출"""
    urls = []
    # URL 패턴 찾기
    patterns = [
        r"https?://[^\s\"'<>)]+",
        r"/LSW/[^\s\"'<>)]+",
        r"lsInfo[RP]\.do[^\s\"'<>)]*",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, script_text)
        urls.extend(matches)
    return urls


def parse_candidate_url(
    url: str,
    base_url: str = "https://www.law.go.kr/",
    onclick_context: Optional[str] = None,
) -> CandidateURL:
    """URL을 파싱하여 CandidateURL 객체 생성"""
    # fncLsLawPop 함수 호출 파싱
    mst = None
    lsid = None
    jo = None
    hang = None
    ho = None
    mok = None
    
    # onclick 컨텍스트에서 fncLsLawPop 파라미터 추출
    if onclick_context:
        # fncLsLawPop('ID', 'TYPE', 'EXTRA')
        match = re.search(r"fncLsLawPop\(['\"]?([^'\")]+)['\"]?\s*,\s*['\"]?([^'\")]*)['\"]?\s*,\s*['\"]?([^'\")]*)['\"]?\)", onclick_context)
        if match:
            param1 = match.group(1).strip()
            param2 = match.group(2).strip() if match.group(2) else ""
            param3 = match.group(3).strip() if match.group(3) else ""
            
            # 첫 번째 파라미터는 법령/조문 ID
            if param1.isdigit():
                # 숫자만 있으면 법령 ID로 추정
                mst = param1
            elif ":" in param1:
                # "법령ID:조문ID" 형태일 수 있음
                parts = param1.split(":")
                if len(parts) >= 2:
                    mst = parts[0] if parts[0].isdigit() else None
                    lsid = parts[1] if parts[1].isdigit() else None
            
            # 두 번째 파라미터는 타입 (JO, HANG, HO, MOK, ALLJO 등)
            if param2 == "JO":
                jo = "제" + param1.split(":")[-1] + "조" if ":" in param1 else None
            elif param2 == "HANG":
                hang = param1
            elif param2 == "HO":
                ho = param1
            elif param2 == "MOK":
                mok = param1
    
    # URL 파싱
    abs_url = urljoin(base_url, url)
    parsed = urlparse(abs_url)
    query_dict = parse_qs(parsed.query)
    
    # 쿼리 파라미터에서 법령 관련 정보 추출 (URL 파라미터가 우선)
    mst = query_dict.get("MST", [None])[0] or query_dict.get("mst", [None])[0] or mst
    lsid = query_dict.get("LSID", [None])[0] or query_dict.get("lsid", [None])[0] or lsid
    jo = query_dict.get("JO", [None])[0] or query_dict.get("jo", [None])[0] or jo
    hang = query_dict.get("HANG", [None])[0] or query_dict.get("hang", [None])[0] or hang
    ho = query_dict.get("HO", [None])[0] or query_dict.get("ho", [None])[0] or ho
    mok = query_dict.get("MOK", [None])[0] or query_dict.get("mok", [None])[0] or mok
    
    # 숫자만 있는 URL은 법령 ID로 추정
    if not mst and url.isdigit():
        mst = url
    
    return CandidateURL(
        raw_url=url,
        abs_url=abs_url,
        host=parsed.netloc,
        path=parsed.path,
        query={k: v[0] if len(v) == 1 else v for k, v in query_dict.items()},
        mst=mst,
        lsid=lsid,
        jo=jo,
        hang=hang,
        ho=ho,
        mok=mok,
    )

SNIPPET_WINDOW = 80
MAX_SNIPPET_LEN = 200


def build_context_path(tag) -> str:
    """간단한 DOM 경로 생성"""
    parts = []
    current = tag
    while current and current.name and current.name != "[document]":
        ident = current.name
        if current.get("id"):
            ident += f"#{current.get('id')}"
        if current.get("class"):
            ident += "." + ".".join(current.get("class"))
        parts.append(ident)
        current = current.parent
        if current and current.name == "html":
            break
    return " > ".join(reversed(parts))


def collect_following_text(anchor_tag, max_len: int = 60) -> str:
    """앵커 다음 텍스트 일부 수집"""
    texts = []
    length = 0
    for sib in anchor_tag.next_siblings:
        if isinstance(sib, NavigableString):
            text = str(sib)
        else:
            text = sib.get_text(" ", strip=False)
        if not text:
            continue
        texts.append(text)
        length += len(text)
        if length >= max_len:
            break
    return "".join(texts).strip()[:max_len]


def extract_candidates(html_path: Path, base_url: str = "https://www.law.go.kr/") -> List[CandidateURL]:
    """HTML 파일에서 연계법령 후보 URL 추출"""
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, "lxml")
    candidates: List[CandidateURL] = []
    seen_urls: Set[str] = set()
    
    # 1. iframe src 추출
    for iframe in soup.find_all("iframe"):
        src = iframe.get("src")
        if src:
            candidate = parse_candidate_url(src, base_url)
            if candidate.abs_url and candidate.abs_url not in seen_urls:
                candidate.source_element = "iframe"
                candidate.source_file = html_path.name
                candidate.iframe_src_raw = src
                candidates.append(candidate)
                seen_urls.add(candidate.abs_url)
    
    # 2. a 태그 추출 (부모 기준 run 그룹화를 위해 문맥 정보 포함)
    parent_tags = {"p", "li", "dd", "dt", "td", "th", "div"}
    for parent in soup.find_all(parent_tags):
        anchors = parent.find_all("a", recursive=False)
        if not anchors:
            continue
        context_path = build_context_path(parent)
        parent_text_full = parent.get_text(" ", strip=False)
        parent_text = parent_text_full[:400]
        parent_id = parent.get("id")
        parent_class = " ".join(parent.get("class", [])) if parent.get("class") else None

        anchor_index = 0
        between_text = ""
        cursor = 0
        for child in parent.children:
            if isinstance(child, NavigableString):
                text = str(child)
                between_text += text
                cursor += len(text)
                continue

            if child.name != "a":
                text = child.get_text(" ", strip=False)
                between_text += text
                cursor += len(text)
                continue

            anchor_text = child.get_text(strip=True)
            href = child.get("href")
            onclick = child.get("onclick", "")
            title = child.get("title")

            urls: List[str] = []
            if href and href not in ("#AJAX", "#") and not href.lower().startswith("javascript:"):
                urls.append(href)
            if onclick:
                urls.extend(extract_urls_from_onclick(onclick))

            if not urls:
                # URL이 없는 경우도 후보로 기록
                urls = [""]

            # snippet 생성: parent_text_full에서 anchor 위치 기준 window
            anchor_pos = parent_text_full.find(anchor_text, cursor)
            if anchor_pos == -1:
                anchor_pos = cursor
            window_start = max(0, anchor_pos - SNIPPET_WINDOW)
            window_end = min(len(parent_text_full), anchor_pos + len(anchor_text) + SNIPPET_WINDOW)
            snippet = parent_text_full[window_start:window_end].strip()
            if len(snippet) > MAX_SNIPPET_LEN:
                snippet = snippet[:MAX_SNIPPET_LEN]

            for url in urls:
                candidate = parse_candidate_url(url, base_url, onclick_context=onclick)
                candidate.source_element = "onclick" if onclick else "a"
                candidate.source_file = html_path.name
                candidate.context_path = context_path
                candidate.parent_tag = parent.name
                candidate.parent_id = parent_id
                candidate.parent_class = parent_class
                candidate.anchor_index = anchor_index
                candidate.anchor_text = anchor_text
                candidate.title = title
                candidate.onclick_raw = onclick or None
                candidate.href_raw = href
                candidate.snippet_before = between_text.strip()[-60:]
                candidate.snippet_after = collect_following_text(child, 60)
                candidate.snippet = snippet
                candidate.between_prev_text = between_text.strip()
                candidate.parent_text = parent_text
                candidates.append(candidate)

            anchor_index += 1
            between_text = ""
            cursor = anchor_pos + len(anchor_text)
    
    # 3. script 태그에서 URL 추출
    for script in soup.find_all("script"):
        script_text = script.string or ""
        if script_text:
            urls = extract_urls_from_script(script_text)
            for url in urls:
                if url not in seen_urls:
                    candidate = parse_candidate_url(url, base_url)
                    candidate.source_element = "script"
                    candidate.source_file = html_path.name
                    candidates.append(candidate)
                    seen_urls.add(url)
    
    # law.go.kr 도메인 필터링 (선택적)
    law_go_kr_candidates = [
        c for c in candidates
        if c.host and ("law.go.kr" in c.host or "lsInfo" in (c.path or ""))
    ]
    
    return law_go_kr_candidates if law_go_kr_candidates else candidates


def main():
    parser = argparse.ArgumentParser(description="HTML에서 연계법령 후보 URL 추출")
    parser.add_argument("--html", required=True, help="입력 HTML 파일 경로")
    parser.add_argument("--out", required=True, help="출력 JSON 파일 경로")
    parser.add_argument("--base-url", default="https://www.law.go.kr/", help="기준 URL (상대경로 변환용)")
    
    args = parser.parse_args()
    
    html_path = Path(args.html)
    if not html_path.exists():
        print(f"Error: {html_path} 파일을 찾을 수 없습니다.")
        return 1
    
    candidates = extract_candidates(html_path, args.base_url)
    
    # JSON 직렬화 가능한 형태로 변환
    candidates_dict = [
        {
            "raw_url": c.raw_url,
            "abs_url": c.abs_url,
            "host": c.host,
            "path": c.path,
            "query": c.query,
            "mst": c.mst,
            "lsid": c.lsid,
            "jo": c.jo,
            "hang": c.hang,
            "ho": c.ho,
            "mok": c.mok,
            "anchor_text": c.anchor_text,
            "source_element": c.source_element,
            "source_file": c.source_file,
            "context_path": c.context_path,
            "parent_tag": c.parent_tag,
            "parent_id": c.parent_id,
            "parent_class": c.parent_class,
            "anchor_index": c.anchor_index,
            "title": c.title,
            "onclick_raw": c.onclick_raw,
            "href_raw": c.href_raw,
            "iframe_src_raw": c.iframe_src_raw,
            "snippet_before": c.snippet_before,
            "snippet_after": c.snippet_after,
            "snippet": c.snippet,
            "between_prev_text": c.between_prev_text,
            "parent_text": c.parent_text,
        }
        for c in candidates
    ]
    
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(candidates_dict, f, ensure_ascii=False, indent=2)
    
    # 통계 출력
    unique_urls = len(set(c.abs_url for c in candidates if c.abs_url))
    law_go_kr_count = sum(1 for c in candidates if c.host and "law.go.kr" in c.host)
    
    print(f"총 후보 수: {len(candidates)}")
    print(f"유니크 URL 수: {unique_urls}")
    print(f"law.go.kr 도메인 비율: {law_go_kr_count}/{len(candidates)} ({law_go_kr_count/len(candidates)*100:.1f}%)" if candidates else "0%")
    print(f"출력 파일: {output_path}")
    
    return 0


if __name__ == "__main__":
    exit(main())

