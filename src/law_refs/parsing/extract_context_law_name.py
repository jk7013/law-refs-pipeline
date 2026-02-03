import re
from typing import List, Dict, Any, Optional


LAW_NAME_TOKEN_RE = re.compile(r".*(법|법률)( 시행령| 시행규칙)?$")


def normalize_law_name_token(text: str) -> Optional[str]:
    if not text:
        return None
    cleaned = text.strip().replace("「", "").replace("」", "")
    if "법률" in cleaned:
        cleaned = cleaned.replace("법률", "법")
    return cleaned if "법" in cleaned else None


def extract_context_law_name(
    run_items: List[Dict[str, Any]],
    current_index: int,
) -> Optional[str]:
    if not run_items:
        return None

    for item in reversed(run_items[: current_index]):
        text = (item.get("anchor_text") or "").strip()
        if not text:
            continue
        if LAW_NAME_TOKEN_RE.match(text) or "법" in text:
            return normalize_law_name_token(text)

    return None

