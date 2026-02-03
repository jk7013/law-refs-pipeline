from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from .types import RefType


@dataclass
class AnchorEvidence:
    anchor_text: str
    href: Optional[str]
    onclick: Optional[str]
    snippet: str
    group_key: Optional[str] = None
    group_anchors: Optional[List[Dict[str, Any]]] = None


@dataclass
class NormalizedInfo:
    search_key: Optional[str] = None
    query_tokens: Optional[List[str]] = None
    resolution: Optional[str] = None
    law_key: Optional[str] = None
    issuer_hint: Optional[str] = None


@dataclass
class RelatedLawTarget:
    law_name: Optional[str] = None
    law_id: Optional[str] = None
    article: Optional[int] = None
    paragraph: Optional[int] = None
    item: Optional[int] = None
    subitem: Optional[str] = None
    ref_range: Optional[Dict[str, Any]] = None
    law_type: Optional[str] = None


@dataclass
class RelatedLawRef:
    type: RefType
    target: RelatedLawTarget
    evidence: AnchorEvidence
    confidence: float
    normalized: Optional[NormalizedInfo] = None

