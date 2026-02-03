from pathlib import Path

from law_refs.parsing.related_law_extract import extract_related_laws
from law_refs.domain.types import RefType


def test_related_extract_citation_and_delegation():
    sample = Path("data/samples/sample_body.html").read_text(encoding="utf-8")
    refs = extract_related_laws(
        sample,
        current_law_name="전기사업법",
        base_law_type="법률",
    )

    types = {ref.type for ref in refs}
    assert RefType.CITATION in types
    assert RefType.DELEGATION in types
