#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from datetime import datetime
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


DEFAULT_BASE = "https://www.law.go.kr"
DEFAULT_TIMEOUT = 20
DEFAULT_SHOW_TOP_LINKS = 20


def now_iso():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def write_log(log_path, message):
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{now_iso()}] {message}\n")


def normalize_url(href, base_url):
    if not href:
        return None
    href = href.strip()
    if href.startswith("javascript:"):
        return None
    return urljoin(base_url, href)


def extract_iframe_src(html_path, base_url, log_path):
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()

    soup = BeautifulSoup(html, "lxml")
    iframe = soup.find("iframe", id="lawService")
    if iframe is None:
        iframe = soup.find("iframe")

    if iframe is None or not iframe.get("src"):
        write_log(log_path, "iframe src not found")
        return None

    src = iframe.get("src").strip()
    if src.startswith("http://") or src.startswith("https://"):
        absolute_src = src
    else:
        absolute_src = urljoin(base_url, src)

    write_log(log_path, f"iframe src extracted: {absolute_src}")
    return absolute_src


def fetch_html(url, timeout, verify_ssl, log_path):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    }
    try:
        response = requests.get(
            url, headers=headers, timeout=timeout, allow_redirects=True, verify=verify_ssl
        )
        status = response.status_code
        redirected = response.url != url
        response.encoding = response.apparent_encoding or response.encoding
        write_log(
            log_path,
            f"GET {url} status={status} redirected={redirected} final_url={response.url}",
        )
        if status >= 400:
            write_log(log_path, f"error: HTTP {status}")
            return None, response
        return response.text, response
    except Exception as exc:
        write_log(log_path, f"error: request failed: {exc}")
        return None, None


def extract_view_params(raw_html, iframe_src, log_path):
    soup = BeautifulSoup(raw_html, "lxml")
    params = {}

    def get_hidden_value(element_id):
        el = soup.find(id=element_id)
        if not el:
            return ""
        return (el.get("value") or "").strip()

    call_match = re.search(r"lsPopViewAll2\(([^)]*)\)", raw_html)
    call_args = []
    if call_match:
        call_args = re.findall(r"""['"]([^'"]*)['"]""", call_match.group(1))

    if len(call_args) >= 8:
        seq, anc_yd, anc_no, ef_yd, nw_jo_yn, ef_gubun, chr_cls, anc_yn_chk = call_args[:8]
        params["lsiSeq"] = seq
        params["ancYd"] = anc_yd
        params["ancNo"] = anc_no
        params["efYd"] = ef_yd
        params["nwJoYnInfo"] = nw_jo_yn
        params["efGubun"] = ef_gubun
        params["chrClsCd"] = chr_cls
        params["ancYnChk"] = anc_yn_chk
    else:
        write_log(log_path, "lsPopViewAll2 call not found or incomplete; using fallback params")

    if iframe_src:
        parsed = urlparse(iframe_src)
        qs = parse_qs(parsed.query or "")
        if not params.get("efYd"):
            params["efYd"] = qs.get("efYd", [""])[0]
        if not params.get("ancYnChk"):
            params["ancYnChk"] = qs.get("ancYnChk", [""])[0]

    hidden_mappings = {
        "lsId": "lsId",
        "lsNm": "lsNm",
        "lsClsCd": "lsClsCd",
        "ancYd": "ancYd",
        "ancNo": "ancNo",
        "lsBdyChrCls": "chrClsCd",
        "nwYn": "nwYn",
        "efDvPop": "efDvPop",
        "ancYnDv": "ancYnDv",
    }
    for element_id, key in hidden_mappings.items():
        if not params.get(key):
            params[key] = get_hidden_value(element_id)

    if params.get("lsiSeq"):
        params["efYn"] = "Y"

    cleaned = {k: v for k, v in params.items() if v}
    write_log(log_path, f"lsInfoR params: {cleaned}")
    return cleaned


def fetch_body_html(base_url, params, timeout, verify_ssl, log_path, referer=None):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    }
    if referer:
        headers["Referer"] = referer
    url = urljoin(base_url, "/LSW/lsInfoR.do")
    try:
        response = requests.post(
            url, headers=headers, data=params, timeout=timeout, allow_redirects=True, verify=verify_ssl
        )
        status = response.status_code
        redirected = response.url != url
        response.encoding = response.apparent_encoding or response.encoding
        write_log(
            log_path,
            f"POST {url} status={status} redirected={redirected} final_url={response.url}",
        )
        if status >= 400:
            write_log(log_path, f"error: HTTP {status}")
            return None, response
        return response.text, response
    except Exception as exc:
        write_log(log_path, f"error: request failed: {exc}")
        return None, None


def inject_body(raw_html, body_html, log_path):
    soup = BeautifulSoup(raw_html, "lxml")
    target = soup.find(id="bodyContent")
    if not target:
        write_log(log_path, "bodyContent div not found; skip HTML merge")
        return None

    target.clear()
    fragment = BeautifulSoup(body_html, "lxml")
    if fragment.body:
        nodes = list(fragment.body.contents)
    else:
        nodes = list(fragment.contents)
    for node in nodes:
        target.append(node)
    return str(soup)


def parse_links(html_path, base_url, log_path):
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()

    soup = BeautifulSoup(html, "lxml")
    links = []
    skipped_js = 0
    for a in soup.find_all("a"):
        href = a.get("href")
        if not href:
            continue
        if href.strip().startswith("javascript:"):
            skipped_js += 1
            continue
        absolute = normalize_url(href, base_url)
        if not absolute:
            continue
        text = a.get_text(strip=True)
        links.append({"text": text, "href": absolute})

    write_log(log_path, f"links parsed: {len(links)} (skipped javascript: {skipped_js})")
    return links


def main():
    parser = argparse.ArgumentParser(description="Extract iframe src and fetch HTML.")
    parser.add_argument("--in", dest="input_html", required=True, help="Input HTML file")
    parser.add_argument("--outdir", default="out", help="Output directory")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="HTTP timeout")
    parser.add_argument("--verify-ssl", action="store_true", default=True, help="Verify SSL")
    parser.add_argument(
        "--no-verify-ssl", dest="verify_ssl", action="store_false", help="Disable SSL verify"
    )
    parser.add_argument("--show-top-links", type=int, default=DEFAULT_SHOW_TOP_LINKS)
    parser.add_argument("--fetch-body", dest="fetch_body", action="store_true", default=True)
    parser.add_argument(
        "--no-fetch-body", dest="fetch_body", action="store_false", help="Skip lsInfoR body fetch"
    )
    parser.add_argument("--mode", choices=["ONLINE", "OFFLINE"], help="Override JIDO_MODE")

    args = parser.parse_args()

    mode = args.mode or os.getenv("JIDO_MODE", "ONLINE")
    if mode not in {"ONLINE", "OFFLINE"}:
        mode = "ONLINE"

    os.makedirs(args.outdir, exist_ok=True)
    log_path = os.path.join(args.outdir, "run.log")
    write_log(log_path, f"start mode={mode}")

    iframe_src = extract_iframe_src(args.input_html, DEFAULT_BASE, log_path)
    if not iframe_src:
        write_log(log_path, "failed: iframe src not found")
        sys.exit(1)

    iframe_path = os.path.join(args.outdir, "iframe_src.txt")
    with open(iframe_path, "w", encoding="utf-8") as f:
        f.write(iframe_src)
    write_log(log_path, f"iframe src saved: {iframe_path}")

    if mode == "OFFLINE":
        write_log(log_path, "offline mode: skip HTTP request")
        return

    html, response = fetch_html(iframe_src, args.timeout, args.verify_ssl, log_path)
    if html is None:
        write_log(log_path, "failed: no HTML fetched")
        sys.exit(1)

    raw_html_path = os.path.join(args.outdir, "lsInfoP_raw.html")
    with open(raw_html_path, "w", encoding="utf-8") as f:
        f.write(html)
    write_log(log_path, f"raw HTML saved: {raw_html_path}")

    base_for_links = response.url if response else iframe_src
    merged_html_path = None
    if args.fetch_body:
        params = extract_view_params(html, iframe_src, log_path)
        body_html, body_response = fetch_body_html(
            base_for_links, params, args.timeout, args.verify_ssl, log_path, referer=base_for_links
        )
        if body_html:
            body_path = os.path.join(args.outdir, "lsInfoR_body.html")
            with open(body_path, "w", encoding="utf-8") as f:
                f.write(body_html)
            write_log(log_path, f"body HTML saved: {body_path}")

            merged_html = inject_body(html, body_html, log_path)
            if merged_html:
                merged_html_path = os.path.join(args.outdir, "lsInfoP_full.html")
                with open(merged_html_path, "w", encoding="utf-8") as f:
                    f.write(merged_html)
                write_log(log_path, f"merged HTML saved: {merged_html_path}")

    link_source = merged_html_path or raw_html_path
    links = parse_links(link_source, base_for_links, log_path)

    links_path = os.path.join(args.outdir, "links.json")
    with open(links_path, "w", encoding="utf-8") as f:
        json.dump(links, f, ensure_ascii=False, indent=2)
    write_log(log_path, f"links saved: {links_path}")

    show_count = max(0, args.show_top_links)
    if show_count > 0:
        top = links[:show_count]
        for item in top:
            print(f"{item.get('text','')}\t{item.get('href','')}")


if __name__ == "__main__":
    main()

