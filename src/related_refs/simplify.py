import json
import re
from typing import Any, Dict, List, Optional, Tuple

from .normalize_delegation import normalize_delegation


ONCLICK_ID_RE = re.compile(r"fncLs(?:Law|Pttn)LinkPop\('([0-9]+)'")
LAWPOP_RE = re.compile(r"fncLsLawPop\('([0-9]+)'")
LSJO_RE = re.compile(r"lsJoLnkSeq=([0-9]+)")


def parse_onclick_id(onclick: Optional[str]) -> Optional[str]:
    if not onclick:
        return None
    match = ONCLICK_ID_RE.search(onclick)
    return match.group(1) if match else None


def parse_lsJoLnkSeq(onclick: Optional[str], href: Optional[str]) -> Optional[str]:
    for val in (onclick, href):
        if not val:
            continue
        match = LSJO_RE.search(val)
        if match:
            return match.group(1)
    return None


def parse_lawpop_id(onclick: Optional[str]) -> Optional[str]:
    if not onclick:
        return None
    match = LAWPOP_RE.search(onclick)
    return match.group(1) if match else None


def build_external_url(lsJoLnkSeq: Optional[str]) -> Optional[str]:
    if not lsJoLnkSeq:
        return None
    return f"https://www.law.go.kr/LSW/lsLinkCommonInfo.do?lsJoLnkSeq={lsJoLnkSeq}&chrClsCd=010202&ancYnChk="


def dedupe_key(ref: Dict[str, Any]) -> Tuple:
    target = ref.get("target", {})
    ref_obj = target.get("ref", {})
    ref_range = ref_obj.get("range", {})
    return (
        ref.get("kind"),
        target.get("lawName"),
        ref_obj.get("article"),
        ref_obj.get("paragraph"),
        ref_obj.get("item"),
        ref_obj.get("subitem"),
        ref_range.get("articleFrom"),
        ref_range.get("articleTo"),
        ref_range.get("paragraphFrom"),
        ref_range.get("paragraphTo"),
        (target.get("link", {}) or {}).get("lsJoLnkSeq"),
        (ref.get("evidence", {}) or {}).get("anchorText"),
        (ref.get("evidence", {}) or {}).get("groupKey"),
    )


def simplify_refs(raw: Dict[str, Any], *, source_law_name: str, source_law_key: Optional[str] = None, article_no: Optional[int] = None) -> Dict[str, Any]:
    refs = raw.get("refs", [])
    simple: List[Dict[str, Any]] = []
    seen = set()

    for ref in refs:
        ref_type = ref.get("type")
        target = ref.get("target", {})
        evidence = ref.get("evidence", {})
        normalized = ref.get("normalized", {})

        anchor_text = evidence.get("anchorText")
        onclick = evidence.get("onclick")
        href = evidence.get("href")
        group_key = evidence.get("groupKey")
        onclick_id = parse_onclick_id(onclick)
        lsJo = parse_lsJoLnkSeq(onclick, href)
        if not lsJo:
            lsJo = parse_lawpop_id(onclick)

        kind = "external" if lsJo else ("delegation" if ref_type == "delegation" else "citation")
        law_name = normalized.get("searchKey") or target.get("lawName")
        law_type = target.get("lawType")

        if ref_type == "delegation":
            law_name, law_type, kind_override, issuer_hint = normalize_delegation(anchor_text, source_law_name)
            kind = "delegation" if kind_override == "delegation" else kind_override
        else:
            issuer_hint = None

        simple_ref = {
            "kind": kind,
            "target": {
                "lawName": law_name,
                "lawType": law_type,
                "ref": {
                    "article": target.get("article"),
                    "paragraph": target.get("paragraph"),
                    "item": target.get("item"),
                    "subitem": target.get("subitem"),
                    "range": {
                        "articleFrom": None,
                        "articleTo": None,
                        "paragraphFrom": None,
                        "paragraphTo": None,
                    },
                },
                "link": {
                    "url": build_external_url(lsJo),
                    "lsJoLnkSeq": lsJo,
                },
            },
            "evidence": {
                "anchorText": anchor_text,
                "snippet": evidence.get("snippet"),
                "groupKey": group_key,
                "onclick": onclick,
                "onclickId": onclick_id,
                "href": href,
            },
        }

        if issuer_hint:
            simple_ref["target"]["issuerHint"] = issuer_hint

        key = dedupe_key(simple_ref)
        if key in seen:
            continue
        seen.add(key)
        simple.append(simple_ref)

    def sort_key(item: Dict[str, Any]) -> Tuple:
        target = item.get("target", {})
        ref_obj = target.get("ref", {})
        article = ref_obj.get("article")
        paragraph = ref_obj.get("paragraph")
        item_no = ref_obj.get("item")
        subitem = ref_obj.get("subitem")
        law_name = target.get("lawName")
        kind = item.get("kind")

        def to_int(val):
            return val if isinstance(val, int) else 10**9

        return (
            to_int(article),
            to_int(paragraph),
            to_int(item_no),
            subitem or "",
            law_name or "",
            kind or "",
        )

    simple_sorted = sorted(simple, key=sort_key)

    return {
        "schemaVersion": "relatedRefs.simple.v1",
        "source": {
            "lawName": source_law_name,
            "lawKey": source_law_key,
            "articleNo": article_no,
        },
        "refs": simple_sorted,
    }


def simplify_from_file(input_path: str, output_path: str, *, source_law_name: str, source_law_key: Optional[str] = None, article_no: Optional[int] = None) -> None:
    with open(input_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    result = simplify_refs(raw, source_law_name=source_law_name, source_law_key=source_law_key, article_no=article_no)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
