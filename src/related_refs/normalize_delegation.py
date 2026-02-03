import re
from typing import Optional, Tuple, Dict


ADMIN_RULE_TERMS = {"고시", "훈령", "예규", "지침", "공고"}
LAW_TYPE_MAP = {
    "대통령령": "대통령령",
    "총리령": "총리령",
    "부령": "부령",
}


def normalize_delegation(anchor_text: str, source_law_name: str) -> Tuple[Optional[str], Optional[str], str, Optional[str]]:
    """
    Returns: (law_name, law_type, kind, issuer_hint)
    kind: delegation | admin_rule | ambiguous
    """
    text = (anchor_text or "").strip()
    if not text:
        return None, None, "ambiguous", None

    if text in ADMIN_RULE_TERMS:
        return None, text, "admin_rule", None

    issuer_hint = None
    if text.endswith("부령") and text not in LAW_TYPE_MAP:
        issuer_hint = text.replace("부령", "")
        law_type = "부령"
    else:
        law_type = LAW_TYPE_MAP.get(text)

    if law_type in {"대통령령"}:
        return f"{source_law_name} 시행령", law_type, "delegation", issuer_hint

    if law_type in {"총리령", "부령"}:
        return f"{source_law_name} 시행규칙", law_type, "delegation", issuer_hint

    return None, None, "ambiguous", None
