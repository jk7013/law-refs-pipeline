#!/usr/bin/env python3
"""
run 기반 정규화: 연속 a태그 결합 + 타입 분리 + 범위 처리
"""
import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from .lawgo_client import LawGoClient
from .range_parser import parse_range, parse_provision_ref


LAW_REF_RE = re.compile(r".*(법|시행령|시행규칙)$")
PROVISION_REF_RE = re.compile(r"(제\d+조(의\d+)?|제\d+항|제\d+호|제[가-힣]목|별표\s*\d+)")
DELEGATION_KEYWORDS = [
    "대통령령", "총리령", "부령", "규칙", "고시", "훈령", "예규", "지침"
]


def detect_law_ref(items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for item in items:
        text = (item.get("anchor_text") or "").strip()
        if text and LAW_REF_RE.match(text) and not text.startswith("제"):
            return item
    return None


def detect_provision_refs(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    refs = []
    for item in items:
        text = (item.get("anchor_text") or "").strip()
        if text and PROVISION_REF_RE.search(text):
            refs.append(item)
    return refs


def detect_delegation(run_text: str) -> List[str]:
    found = []
    for kw in DELEGATION_KEYWORDS:
        if kw in run_text:
            found.append(kw)
    return found


def detect_context_article_no(text: str) -> Optional[int]:
    if not text:
        return None
    m = re.search(r"제(\d+)(?:조|조의\d+)", text)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None


def build_reference(
    ref_type: str,
    target: Dict[str, Any],
    evidence: Dict[str, Any],
    confidence: float = 0.0,
) -> Dict[str, Any]:
    return {
        "type": ref_type,
        "target": target,
        "evidence": evidence,
        "confidence": confidence,
    }


def normalize_run(
    run: Dict[str, Any],
    mode: str = "offline",
    lawgo_client: Optional[LawGoClient] = None,
    default_law_name: str = "전기사업법",
) -> List[Dict[str, Any]]:
    items = run.get("items", [])
    run_text = run.get("run_text") or ""
    parent_text = run.get("parent_text") or ""

    references: List[Dict[str, Any]] = []

    # 1) 범위(range) 처리
    range_info = parse_range(run_text)
    if range_info:
        references.append(
            build_reference(
                "range",
                {
                    "lawName": default_law_name,
                    "lawId": None,
                    "ref": range_info["from"],
                    "ref_range": {
                        "item_from": range_info["from"].get("item"),
                        "item_to": range_info["to"].get("item"),
                    },
                },
                {
                    "anchorText": items[0].get("anchor_text") if items else None,
                    "href": items[0].get("href_raw") if items else None,
                    "onclick": items[0].get("onclick_raw") if items else None,
                    "snippet": (items[0].get("snippet") or run_text)[:200],
                },
                0.6,
            )
        )

    # 2) delegation 처리 (대통령령 등은 별도)
    for item in items:
        anchor_text = (item.get("anchor_text") or "").strip()
        for kw in DELEGATION_KEYWORDS:
            if anchor_text == kw:
                references.append(
                    build_reference(
                        "delegation",
                        {"lawName": kw},
                        {
                            "anchorText": anchor_text,
                            "href": item.get("href_raw"),
                            "onclick": item.get("onclick_raw"),
                            "snippet": (item.get("snippet") or "")[:200],
                            "groupAnchors": [
                                {
                                    "anchorText": anchor_text,
                                    "href": item.get("href_raw"),
                                    "onclick": item.get("onclick_raw"),
                                }
                            ],
                        },
                        0.6,
                    )
                )

    # 3) LAW_REF + PROVISION_REF 조립
    law_item = detect_law_ref(items)
    provision_items = detect_provision_refs(items)

    if provision_items:
        # law_name 결정
        law_name = default_law_name
        law_id = None
        if law_item:
            law_name = law_item.get("anchor_text") or law_name
            law_id = law_item.get("mst") or law_item.get("lsid")

        # provision 조립 (첫 번째 provision 기준)
        provision_text = " ".join([p.get("anchor_text") or "" for p in provision_items]).strip()
        provision_ref = parse_provision_ref(provision_text)

        target = {
            "lawName": law_name,
            "lawId": law_id,
            "ref": {
                "article": provision_ref.get("article"),
                "paragraph": provision_ref.get("paragraph"),
                "item": provision_ref.get("item"),
                "subitem": provision_ref.get("subitem"),
            },
        }

        references.append(
            build_reference(
                "citation",
                target,
                {
                    "anchorText": provision_items[0].get("anchor_text"),
                    "href": provision_items[0].get("href_raw"),
                    "onclick": provision_items[0].get("onclick_raw"),
                    "snippet": (provision_items[0].get("snippet") or "")[:200],
                    "groupAnchors": [
                        {
                            "anchorText": i.get("anchor_text"),
                            "href": i.get("href_raw"),
                            "onclick": i.get("onclick_raw"),
                        }
                        for i in provision_items
                    ],
                },
                0.7 if law_item else 0.5,
            )
        )

    # 4) a태그 단위 기본 참조 생성 (병합 대상 제외)
    if not provision_items and not law_item:
        for item in items:
            anchor_text = (item.get("anchor_text") or "").strip()
            if not anchor_text:
                continue
            if anchor_text in DELEGATION_KEYWORDS:
                continue
            if not PROVISION_REF_RE.search(anchor_text) and not LAW_REF_RE.match(anchor_text):
                continue

            provision_ref = parse_provision_ref(anchor_text)
            target = {
                "lawName": default_law_name,
                "lawId": None,
                "ref": {
                    "article": provision_ref.get("article"),
                    "paragraph": provision_ref.get("paragraph"),
                    "item": provision_ref.get("item"),
                    "subitem": provision_ref.get("subitem"),
                },
            }

            references.append(
                build_reference(
                    "citation",
                    target,
                    {
                        "anchorText": anchor_text,
                        "href": item.get("href_raw"),
                        "onclick": item.get("onclick_raw"),
                        "snippet": (item.get("snippet") or "")[:200],
                        "groupAnchors": [
                            {
                                "anchorText": anchor_text,
                                "href": item.get("href_raw"),
                                "onclick": item.get("onclick_raw"),
                            }
                        ],
                    },
                    0.4,
                )
            )

    # context 정보 추가
    context_article_no = detect_context_article_no(parent_text) or detect_context_article_no(run_text)
    for ref in references:
        ref["context"] = {
            "articleNo": context_article_no,
            "contextPath": run.get("context_path"),
            "runId": run.get("run_id"),
        }

    return references


def normalize_refs(
    runs: List[Dict[str, Any]],
    mode: str = "offline",
    lawgo_client: Optional[LawGoClient] = None,
    default_law_name: str = "전기사업법",
) -> List[Dict[str, Any]]:
    normalized = []
    for run in runs:
        normalized.extend(normalize_run(run, mode, lawgo_client, default_law_name))
    return normalized


def main():
    parser = argparse.ArgumentParser(description="run 기반 정규화")
    parser.add_argument("--in", dest="input_file", required=True, help="입력 runs.json 파일")
    parser.add_argument("--mode", choices=["offline", "online"], default="offline", help="OFFLINE 또는 ONLINE 모드")
    parser.add_argument("--out", required=True, help="출력 JSONL 파일 경로")
    parser.add_argument("--law-name", default="전기사업법", help="현재 법령명 (내부참조용)")

    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: {input_path} 파일을 찾을 수 없습니다.")
        return 1

    with open(input_path, "r", encoding="utf-8") as f:
        runs = json.load(f)

    # ONLINE 모드일 때 클라이언트 생성
    lawgo_client = None
    if args.mode == "online":
        lawgo_client = LawGoClient()

    normalized = normalize_refs(runs, args.mode, lawgo_client, args.law_name)

    # JSONL 형식으로 저장
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for ref in normalized:
            f.write(json.dumps(ref, ensure_ascii=False) + "\n")

    print(f"정규화된 참조 수: {len(normalized)}")
    print(f"출력 파일: {output_path}")

    return 0


if __name__ == "__main__":
    exit(main())

