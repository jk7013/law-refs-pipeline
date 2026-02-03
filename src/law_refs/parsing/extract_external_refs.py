import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from bs4 import BeautifulSoup, NavigableString

from law_refs.domain.normalize import is_run_joiner, parse_provision_ref
from law_refs.parsing.extract_context_law_name import normalize_law_name_token


ONCLICK_ID_RE = re.compile(r"fncLs(?:Law|Pttn)LinkPop\('([0-9]+)'|fncLsLawPop\('([0-9]+)'")
LSJO_RE = re.compile(r"lsJoLnkSeq=([0-9]+)")


@dataclass
class ExternalLink:
    law_name: Optional[str]
    article: Optional[int]
    paragraph: Optional[int]
    item: Optional[int]
    subitem: Optional[str]
    external_link_json: Dict[str, Any]
    evidence: Dict[str, Any]


def _parse_onclick_id(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    match = ONCLICK_ID_RE.search(value)
    if not match:
        return None
    return match.group(1) or match.group(2)


def _parse_lsJoLnkSeq(onclick: Optional[str], href: Optional[str]) -> Optional[str]:
    for val in (onclick, href):
        if not val:
            continue
        match = LSJO_RE.search(val)
        if match:
            return match.group(1)
    return None


def _build_external_url(lsJoLnkSeq: Optional[str]) -> Optional[str]:
    if not lsJoLnkSeq:
        return None
    return (
        "https://www.law.go.kr/LSW/lsLinkCommonInfo.do?"
        f"lsJoLnkSeq={lsJoLnkSeq}&chrClsCd=010202&ancYnChk="
    )


def _build_run_text(items: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for idx, item in enumerate(items):
        between = item.get("between_prev_text") or ""
        if idx == 0:
            parts.append(item.get("anchor_text") or "")
        else:
            parts.append(between)
            parts.append(item.get("anchor_text") or "")
    return "".join(parts).strip()


def _collect_anchor_items(body_html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(body_html, "lxml")
    parent_tags = {"p", "li", "dd", "dt", "td", "th", "div"}
    items: List[Dict[str, Any]] = []

    for parent_idx, parent in enumerate(soup.find_all(parent_tags)):
        anchors = parent.find_all("a", recursive=False)
        if not anchors:
            continue

        parent_text_full = parent.get_text(" ", strip=False)
        between_text = ""
        cursor = 0
        anchor_index = 0
        group_key = f"{parent.name}#{parent.get('id') or ''}.{'.'.join(parent.get('class', []))}:{parent_idx}"

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
            onclick = child.get("onclick")

            items.append(
                {
                    "anchor_text": anchor_text,
                    "href": href,
                    "onclick": onclick,
                    "between_prev_text": between_text,
                    "anchor_index": anchor_index,
                    "group_key": group_key,
                }
            )
            between_text = ""
            anchor_index += 1

    return items


def _group_runs(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    runs: List[Dict[str, Any]] = []
    if not items:
        return runs

    groups: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:
        key = item.get("group_key") or "__unknown__"
        groups.setdefault(key, []).append(item)

    for _, group_items in groups.items():
        items_sorted = sorted(group_items, key=lambda x: x.get("anchor_index") or 0)
        current: List[Dict[str, Any]] = []
        for item in items_sorted:
            between_text = item.get("between_prev_text") or ""
            if not current:
                current.append(item)
                continue
            if is_run_joiner(between_text):
                current.append(item)
            else:
                runs.append({"items": current, "run_text": _build_run_text(current)})
                current = [item]

        if current:
            runs.append({"items": current, "run_text": _build_run_text(current)})
    return runs


def extract_external_refs(body_html: str) -> List[ExternalLink]:
    items = _collect_anchor_items(body_html)
    runs = _group_runs(items)
    results: List[ExternalLink] = []

    for run in runs:
        run_items = run.get("items", [])
        if not run_items:
            continue

        law_item = None
        law_name = None
        for item in run_items:
            text = (item.get("anchor_text") or "").strip()
            normalized = normalize_law_name_token(text)
            if normalized and not text.startswith("제"):
                law_item = item
                law_name = normalized
                break

        provision_items = []
        for item in run_items:
            text = (item.get("anchor_text") or "").strip()
            if re.search(r"제\d+조", text):
                provision_items.append(item)

        if not law_item or not provision_items:
            continue

        if not law_name:
            law_name = normalize_law_name_token(law_item.get("anchor_text"))
        provision_text = " ".join([i.get("anchor_text") or "" for i in provision_items]).strip()
        provision_ref = parse_provision_ref(provision_text)

        # lsJoLnkSeq: prefer article anchor, fallback to law anchor
        article_item = provision_items[0]
        lsJo = _parse_lsJoLnkSeq(article_item.get("onclick"), article_item.get("href"))
        if not lsJo:
            lsJo = _parse_onclick_id(article_item.get("onclick"))
        if not lsJo:
            lsJo = _parse_lsJoLnkSeq(law_item.get("onclick"), law_item.get("href"))
        if not lsJo:
            lsJo = _parse_onclick_id(law_item.get("onclick"))

        external_link = {
            "url": _build_external_url(lsJo),
            "lsJoLnkSeq": lsJo,
            "chrClsCd": "010202",
            "ancYnChk": "",
        }

        evidence = {
            "anchorText": article_item.get("anchor_text"),
            "groupKey": article_item.get("group_key"),
            "onclick": article_item.get("onclick"),
            "href": article_item.get("href"),
            "onclickId": _parse_onclick_id(article_item.get("onclick")),
        }

        results.append(
            ExternalLink(
                law_name=law_name,
                article=provision_ref.get("article"),
                paragraph=provision_ref.get("paragraph"),
                item=provision_ref.get("item"),
                subitem=provision_ref.get("subitem"),
                external_link_json=external_link,
                evidence=evidence,
            )
        )

    return results
