from typing import Sequence

from law_refs.domain.models import RelatedLawRef, NormalizedInfo
from law_refs.db.repo import resolve_law_key_by_name


def resolve_related_laws(conn, refs: Sequence[RelatedLawRef]) -> Sequence[RelatedLawRef]:
    resolved = []
    for ref in refs:
        if not ref.normalized or not ref.normalized.search_key:
            resolved.append(ref)
            continue

        law_key = resolve_law_key_by_name(conn, law_name=ref.normalized.search_key)
        if law_key:
            ref.normalized = NormalizedInfo(
                search_key=ref.normalized.search_key,
                query_tokens=ref.normalized.query_tokens,
                resolution="resolved",
                law_key=law_key,
                issuer_hint=ref.normalized.issuer_hint,
            )
        else:
            ref.normalized = NormalizedInfo(
                search_key=ref.normalized.search_key,
                query_tokens=ref.normalized.query_tokens,
                resolution=ref.normalized.resolution or "unresolved",
                law_key=None,
                issuer_hint=ref.normalized.issuer_hint,
            )
        resolved.append(ref)
    return resolved

