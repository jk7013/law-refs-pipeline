import json
from typing import Dict, Any

from law_refs.parsing.html_locator import locate_article_body_html
from law_refs.parsing.related_law_extract import extract_related_laws
from law_refs.parsing.extract_external_refs import extract_external_refs


def run_dry_pipeline(
    raw_html: str,
    *,
    current_law_name: str,
    base_law_type: str,
) -> Dict[str, Any]:
    located = locate_article_body_html(raw_html)
    refs = extract_related_laws(
        located.body_html,
        current_law_name=current_law_name,
        base_law_type=base_law_type,
    )
    external_refs = extract_external_refs(located.body_html)

    serialized_refs = [
        {
            "type": ref.type.value,
            "target": {
                "lawName": ref.target.law_name,
                "lawId": ref.target.law_id,
                "article": ref.target.article,
                "paragraph": ref.target.paragraph,
                "item": ref.target.item,
                "subitem": ref.target.subitem,
                "ref_range": ref.target.ref_range,
                "lawType": ref.target.law_type,
            },
            "evidence": {
                "anchorText": ref.evidence.anchor_text,
                "href": ref.evidence.href,
                "onclick": ref.evidence.onclick,
                "snippet": ref.evidence.snippet,
                "groupKey": ref.evidence.group_key,
                "groupAnchors": ref.evidence.group_anchors,
            },
            "confidence": ref.confidence,
            "normalized": {
                "searchKey": ref.normalized.search_key if ref.normalized else None,
                "queryTokens": ref.normalized.query_tokens if ref.normalized else None,
                "resolution": ref.normalized.resolution if ref.normalized else None,
                "lawKey": ref.normalized.law_key if ref.normalized else None,
                "issuerHint": ref.normalized.issuer_hint if ref.normalized else None,
            },
        }
        for ref in refs
    ]

    external_serialized = [
        {
            "type": "external_citation",
            "target": {
                "lawName": ext.law_name,
                "lawId": None,
                "article": ext.article,
                "paragraph": ext.paragraph,
                "item": ext.item,
                "subitem": ext.subitem,
                "ref_range": None,
                "lawType": None,
            },
            "evidence": {
                "anchorText": ext.evidence.get("anchorText"),
                "href": ext.evidence.get("href"),
                "onclick": ext.evidence.get("onclick"),
                "snippet": None,
                "groupKey": ext.evidence.get("groupKey"),
                "groupAnchors": None,
            },
            "confidence": 0.7,
            "normalized": {
                "searchKey": ext.law_name,
                "queryTokens": [ext.law_name] if ext.law_name else None,
                "resolution": "unresolved",
                "lawKey": None,
                "issuerHint": None,
            },
        }
        for ext in external_refs
    ]

    return {
        "strategy": located.strategy,
        "debug": located.debug,
        "refs": serialized_refs + external_serialized,
    }

