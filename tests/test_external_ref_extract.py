from pathlib import Path

from law_refs.parsing.extract_external_refs import extract_external_refs


def test_extract_external_ref_law_and_article():
    html = Path("data/samples/sample_body.html").read_text(encoding="utf-8")
    refs = extract_external_refs(html)
    assert refs
    ref = refs[0]
    assert ref.law_name
    assert ref.article is not None
    assert ref.external_link_json["lsJoLnkSeq"] == "123457"
