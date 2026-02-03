import re
from typing import Dict, Any, Optional


PROVISION_REF_RE = re.compile(r"(제\d+조(의\d+)?|제\d+항|제\d+호|제[가-힣]목|별표\s*\d+)")
RANGE_RE = re.compile(r"(제[^부터까지]+?)부터\s*(제[^부터까지]+?)까지")
PUNCT_ONLY_RE = re.compile(r"^[\s\(\)\[\]「」『』“”\"'.,ㆍ··…\-–—]*$")


def is_run_joiner(text: Optional[str]) -> bool:
    if text is None:
        return True
    cleaned = text.strip()
    if not cleaned:
        return True
    if cleaned in {"제", "의"}:
        return True
    return bool(PUNCT_ONLY_RE.match(cleaned))


def parse_provision_ref(text: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "article": None,
        "paragraph": None,
        "item": None,
        "subitem": None,
    }
    if not text:
        return result

    m = re.search(r"제(\d+)(?:조|조의(\d+))", text)
    if m:
        try:
            result["article"] = int(m.group(1))
        except ValueError:
            result["article"] = None

    m = re.search(r"제(\d+)항", text)
    if m:
        try:
            result["paragraph"] = int(m.group(1))
        except ValueError:
            result["paragraph"] = None

    m = re.search(r"제(\d+)호", text)
    if m:
        try:
            result["item"] = int(m.group(1))
        except ValueError:
            result["item"] = None

    m = re.search(r"제?([가-힣])목", text)
    if m:
        result["subitem"] = m.group(1)

    return result


def parse_range(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    match = RANGE_RE.search(text)
    if not match:
        return None

    from_text = match.group(1)
    to_text = match.group(2)

    from_ref = parse_provision_ref(from_text)
    to_ref = parse_provision_ref(to_text)

    if not to_ref["article"] and from_ref["article"]:
        to_ref["article"] = from_ref["article"]
    if not to_ref["paragraph"] and from_ref["paragraph"]:
        to_ref["paragraph"] = from_ref["paragraph"]
    if not to_ref["item"] and from_ref["item"]:
        to_ref["item"] = from_ref["item"]

    return {
        "type": "range",
        "from": from_ref,
        "to": to_ref,
        "inclusive": True,
        "raw_text": match.group(0),
    }

