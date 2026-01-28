#!/usr/bin/env python3
"""
범위(range) 표현 파서
"""
import re
from typing import Optional, Dict, Any


RANGE_RE = re.compile(r"(제[^부터까지]+?)부터\s*(제[^부터까지]+?)까지")


def parse_provision_ref(text: str) -> Dict[str, Any]:
    """조문/항/호/목 텍스트를 구조화 (int 기준)"""
    result: Dict[str, Any] = {
        "article": None,
        "paragraph": None,
        "item": None,
        "subitem": None,
    }
    if not text:
        return result

    # 제N조(의M) -> article: N (의M은 무시)
    m = re.search(r"제(\d+)(?:조|조의(\d+))", text)
    if m:
        try:
            result["article"] = int(m.group(1))
        except ValueError:
            result["article"] = None

    # 제M항
    m = re.search(r"제(\d+)항", text)
    if m:
        try:
            result["paragraph"] = int(m.group(1))
        except ValueError:
            result["paragraph"] = None

    # 제K호
    m = re.search(r"제(\d+)호", text)
    if m:
        try:
            result["item"] = int(m.group(1))
        except ValueError:
            result["item"] = None

    # 제L목 (가/나/다...)
    m = re.search(r"제?([가-힣])목", text)
    if m:
        result["subitem"] = m.group(1)

    return result


def parse_range(text: str) -> Optional[Dict[str, Any]]:
    """범위 표현을 구조화"""
    if not text:
        return None

    match = RANGE_RE.search(text)
    if not match:
        return None

    from_text = match.group(1)
    to_text = match.group(2)

    from_ref = parse_provision_ref(from_text)
    to_ref = parse_provision_ref(to_text)

    # from의 조/항이 to에 없으면 상속
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

