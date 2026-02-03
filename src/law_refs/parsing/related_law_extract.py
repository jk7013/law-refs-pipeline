import re
from typing import List, Dict, Any, Optional

from bs4 import BeautifulSoup, NavigableString

from law_refs.domain.models import (
    RelatedLawRef,
    RelatedLawTarget,
    AnchorEvidence,
    NormalizedInfo,
)
from law_refs.domain.types import RefType
from law_refs.domain.normalize import parse_provision_ref, parse_range, is_run_joiner
from law_refs.domain.normalize_delegation_term import normalize_delegation_term
from law_refs.parsing.extract_context_law_name import extract_context_law_name


LAW_REF_RE = re.compile(r".*(법|시행령|시행규칙)$")
PROVISION_REF_RE = re.compile(r"(제\d+조(의\d+)?|제\d+항|제\d+호|제[가-힣]목|별표\s*\d+)")
DELEGATION_KEYWORDS = ["대통령령", "총리령", "부령", "규칙", "고시", "훈령", "예규", "지침"]


def _build_snippet(parent_text: str, anchor_text: str, start_pos: int) -> str:
    if not parent_text:
        return anchor_text
    window = 80
    max_len = 200
    anchor_pos = parent_text.find(anchor_text, start_pos)
    if anchor_pos == -1:
        anchor_pos = start_pos
    window_start = max(0, anchor_pos - window)
    window_end = min(len(parent_text), anchor_pos + len(anchor_text) + window)
    snippet = parent_text[window_start:window_end].strip()
    return snippet[:max_len]


def _collect_anchor_items(body_html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(body_html, "lxml")
    parent_tags = {"p", "li", "dd", "dt", "td", "th", "div"}
    items: List[Dict[str, Any]] = []

    for parent in soup.find_all(parent_tags):
        anchors = parent.find_all("a", recursive=False)
        if not anchors:
            continue

        parent_text_full = parent.get_text(" ", strip=False)
        parent_text = parent_text_full[:400]
        between_text = ""
        cursor = 0
        anchor_index = 0
        group_key = f"{parent.name}#{parent.get('id') or ''}.{'.'.join(parent.get('class', []))}"

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
            snippet = _build_snippet(parent_text_full, anchor_text, cursor)

            items.append(
                {
                    "anchor_text": anchor_text,
                    "href": href,
                    "onclick": onclick,
                    "snippet": snippet,
                    "between_prev_text": between_text,
                    "anchor_index": anchor_index,
                    "parent_text": parent_text,
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

    items_sorted = sorted(items, key=lambda x: x.get("anchor_index") or 0)
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


def _detect_law_ref(items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for item in items:
        text = (item.get("anchor_text") or "").strip()
        if text and LAW_REF_RE.match(text) and not text.startswith("제"):
            return item
    return None


def _detect_provision_refs(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    refs = []
    for item in items:
        text = (item.get("anchor_text") or "").strip()
        if text and PROVISION_REF_RE.search(text):
            refs.append(item)
    return refs


def extract_related_laws(
    body_html: str,
    *,
    current_law_name: str,
    base_law_type: str,
) -> List[RelatedLawRef]:
    items = _collect_anchor_items(body_html)
    runs = _group_runs(items)
    results: List[RelatedLawRef] = []

    for run in runs:
        run_text = run.get("run_text") or ""
        run_items = run.get("items", [])
        if not run_items:
            continue

        # Range
        range_info = parse_range(run_text)
        if range_info:
            target = RelatedLawTarget(
                law_name=current_law_name,
                article=range_info["from"].get("article"),
                paragraph=range_info["from"].get("paragraph"),
                item=range_info["from"].get("item"),
                subitem=range_info["from"].get("subitem"),
                ref_range={
                    "item_from": range_info["from"].get("item"),
                    "item_to": range_info["to"].get("item"),
                },
            )
            evidence = AnchorEvidence(
                anchor_text=run_items[0].get("anchor_text") or "",
                href=run_items[0].get("href"),
                onclick=run_items[0].get("onclick"),
                snippet=run_items[0].get("snippet") or run_text[:200],
                group_key=run_items[0].get("group_key"),
            )
            results.append(
                RelatedLawRef(
                    type=RefType.RANGE,
                    target=target,
                    evidence=evidence,
                    confidence=0.6,
                    normalized=NormalizedInfo(
                        search_key=current_law_name,
                        query_tokens=[current_law_name],
                        resolution="unresolved",
                    ),
                )
            )

        # Delegation
        for item in run_items:
            anchor_text = (item.get("anchor_text") or "").strip()
            if anchor_text in DELEGATION_KEYWORDS or anchor_text.endswith("부령"):
                context_law_name = extract_context_law_name(
                    run_items, item.get("anchor_index") or 0
                )
                norm = normalize_delegation_term(
                    anchor_text,
                    base_law_name=current_law_name,
                    base_law_type=base_law_type,
                    context_law_name=context_law_name,
                )
                evidence = AnchorEvidence(
                    anchor_text=anchor_text,
                    href=item.get("href"),
                    onclick=item.get("onclick"),
                    snippet=item.get("snippet") or "",
                    group_key=item.get("group_key"),
                    group_anchors=[
                        {
                            "anchorText": anchor_text,
                            "href": item.get("href"),
                            "onclick": item.get("onclick"),
                        }
                    ],
                )
                target = RelatedLawTarget(
                    law_name=norm["target"].get("lawName"),
                    law_type=norm["target"].get("lawType"),
                )
                normalized = NormalizedInfo(
                    search_key=norm["normalized"].get("searchKey"),
                    query_tokens=norm["normalized"].get("queryTokens"),
                    resolution=norm["normalized"].get("resolution"),
                )
                if norm["type"] == "admin_rule":
                    ref_type = RefType.ADMIN_RULE
                elif norm["type"] == "ambiguous":
                    ref_type = RefType.AMBIGUOUS
                else:
                    ref_type = RefType.DELEGATION
                results.append(
                    RelatedLawRef(
                        type=ref_type,
                        target=target,
                        evidence=evidence,
                        confidence=0.6,
                        normalized=normalized,
                    )
                )

        # Citation
        law_item = _detect_law_ref(run_items)
        provision_items = _detect_provision_refs(run_items)
        if provision_items:
            law_name = current_law_name
            law_id = None
            if law_item:
                law_name = law_item.get("anchor_text") or law_name

            provision_text = " ".join([i.get("anchor_text") or "" for i in provision_items]).strip()
            provision_ref = parse_provision_ref(provision_text)
            evidence = AnchorEvidence(
                anchor_text=provision_items[0].get("anchor_text") or "",
                href=provision_items[0].get("href"),
                onclick=provision_items[0].get("onclick"),
                snippet=provision_items[0].get("snippet") or run_text[:200],
                group_key=provision_items[0].get("group_key"),
                group_anchors=[
                    {
                        "anchorText": i.get("anchor_text"),
                        "href": i.get("href"),
                        "onclick": i.get("onclick"),
                    }
                    for i in provision_items
                ],
            )
            target = RelatedLawTarget(
                law_name=law_name,
                law_id=law_id,
                article=provision_ref.get("article"),
                paragraph=provision_ref.get("paragraph"),
                item=provision_ref.get("item"),
                subitem=provision_ref.get("subitem"),
            )
            results.append(
                RelatedLawRef(
                    type=RefType.CITATION,
                    target=target,
                    evidence=evidence,
                    confidence=0.7 if law_item else 0.5,
                    normalized=NormalizedInfo(
                        search_key=law_name,
                        query_tokens=[law_name] if law_name else None,
                        resolution="unresolved",
                    ),
                )
            )

        # Single anchor fallback
        if not provision_items and not law_item:
            for item in run_items:
                text = (item.get("anchor_text") or "").strip()
                if not text:
                    continue
                if text in DELEGATION_KEYWORDS:
                    continue
                if not PROVISION_REF_RE.search(text) and not LAW_REF_RE.match(text):
                    continue

                provision_ref = parse_provision_ref(text)
                evidence = AnchorEvidence(
                    anchor_text=text,
                    href=item.get("href"),
                    onclick=item.get("onclick"),
                    snippet=item.get("snippet") or "",
                    group_key=item.get("group_key"),
                    group_anchors=[
                        {
                            "anchorText": text,
                            "href": item.get("href"),
                            "onclick": item.get("onclick"),
                        }
                    ],
                )
                target = RelatedLawTarget(
                    law_name=current_law_name,
                    article=provision_ref.get("article"),
                    paragraph=provision_ref.get("paragraph"),
                    item=provision_ref.get("item"),
                    subitem=provision_ref.get("subitem"),
                )
                results.append(
                    RelatedLawRef(
                        type=RefType.CITATION,
                        target=target,
                        evidence=evidence,
                        confidence=0.4,
                        normalized=NormalizedInfo(
                            search_key=current_law_name,
                            query_tokens=[current_law_name],
                            resolution="unresolved",
                        ),
                    )
                )

    return results

