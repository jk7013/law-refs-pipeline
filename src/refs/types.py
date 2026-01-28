"""
연계법령 추출을 위한 타입 정의
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class ReferenceType(str, Enum):
    """참조 유형"""
    CITATION = "citation"  # 인용
    DELEGATION = "delegation"  # 위임
    RELATED = "related"  # 관련
    UNKNOWN = "unknown"  # 알 수 없음


@dataclass
class TargetLaw:
    """참조 대상 법령 정보"""
    law_name: Optional[str] = None
    law_id: Optional[str] = None
    article: Optional[str] = None  # 제N조
    paragraph: Optional[str] = None  # 제M항
    clause: Optional[str] = None  # 제K호
    subclause: Optional[str] = None  # 제L목


@dataclass
class Evidence:
    """참조 증거 정보"""
    source: str  # "law.go.kr" 등
    html_snippet: Optional[str] = None  # HTML 스니펫 (최대 200자)
    anchor_text: Optional[str] = None  # 링크 텍스트
    href: Optional[str] = None  # 원본 URL


@dataclass
class RelatedLaw:
    """연계법령 정보"""
    type: ReferenceType
    target: TargetLaw
    evidence: Evidence
    confidence: float = 0.0  # 0.0 ~ 1.0


@dataclass
class CandidateURL:
    """추출된 후보 URL"""
    raw_url: str
    abs_url: Optional[str] = None
    host: Optional[str] = None
    path: Optional[str] = None
    query: Dict[str, Any] = field(default_factory=dict)
    mst: Optional[str] = None  # 법령 ID
    lsid: Optional[str] = None
    jo: Optional[str] = None  # 조
    hang: Optional[str] = None  # 항
    ho: Optional[str] = None  # 호
    mok: Optional[str] = None  # 목
    anchor_text: Optional[str] = None
    source_element: Optional[str] = None  # "a", "iframe", "onclick", "script"
    source_file: Optional[str] = None
    context_path: Optional[str] = None
    parent_tag: Optional[str] = None
    parent_id: Optional[str] = None
    parent_class: Optional[str] = None
    anchor_index: Optional[int] = None
    title: Optional[str] = None
    onclick_raw: Optional[str] = None
    href_raw: Optional[str] = None
    iframe_src_raw: Optional[str] = None
    snippet_before: Optional[str] = None
    snippet_after: Optional[str] = None
    snippet: Optional[str] = None
    between_prev_text: Optional[str] = None
    parent_text: Optional[str] = None


@dataclass
class NormalizedReference:
    """정규화된 참조"""
    candidate: CandidateURL
    normalized: RelatedLaw
    success: bool = True
    error: Optional[str] = None

