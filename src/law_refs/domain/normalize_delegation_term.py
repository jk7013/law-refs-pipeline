from typing import Dict, Any, Optional


ADMIN_RULE_TERMS = {"고시", "훈령", "예규", "지침", "공고"}


def normalize_delegation_term(
    anchor_text: str,
    base_law_name: str,
    base_law_type: str,
    context_law_name: Optional[str],
) -> Dict[str, Any]:
    context = context_law_name or base_law_name
    result: Dict[str, Any] = {
        "type": "delegation",
        "target": {
            "lawName": None,
            "lawType": None,
            "ref": {"article": None, "paragraph": None, "item": None, "subitem": None},
        },
        "normalized": {
            "searchKey": None,
            "queryTokens": [],
            "resolution": "unresolved",
        },
    }

    if anchor_text in ADMIN_RULE_TERMS:
        result["type"] = "admin_rule"
        result["normalized"]["resolution"] = "ambiguous"
        result["target"]["lawType"] = anchor_text
        return result

    if anchor_text in {"대통령령", "총리령", "부령"} or anchor_text.endswith("부령"):
        if anchor_text == "대통령령":
            result["target"]["lawType"] = "대통령령"
            if base_law_type == "법률":
                search_key = f"{context} 시행령"
                result["target"]["lawName"] = search_key
                result["normalized"]["searchKey"] = search_key
                result["normalized"]["queryTokens"] = [context, "시행령"]
                return result
            if base_law_type == "대통령령":
                result["normalized"]["resolution"] = "self"
                return result
            if base_law_type in {"총리령", "부령"}:
                result["normalized"]["resolution"] = "ambiguous"
                return result

        if anchor_text in {"총리령", "부령"} or anchor_text.endswith("부령"):
            result["target"]["lawType"] = "총리령" if anchor_text == "총리령" else "부령"
            if base_law_type in {"법률", "대통령령"}:
                search_key = f"{context} 시행규칙"
                result["target"]["lawName"] = search_key
                result["normalized"]["searchKey"] = search_key
                result["normalized"]["queryTokens"] = [context, "시행규칙"]
                return result
            if base_law_type in {"총리령", "부령"}:
                result["normalized"]["resolution"] = "self"
                return result

    result["type"] = "ambiguous"
    result["normalized"]["resolution"] = "ambiguous"
    return result

