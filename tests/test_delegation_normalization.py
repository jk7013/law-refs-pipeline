from law_refs.domain.normalize_delegation_term import normalize_delegation_term


def test_law_to_presidential_decree():
    result = normalize_delegation_term(
        anchor_text="대통령령",
        base_law_name="전기사업법",
        base_law_type="법률",
        context_law_name=None,
    )
    assert result["normalized"]["searchKey"] == "전기사업법 시행령"


def test_law_to_ministry_rule():
    result = normalize_delegation_term(
        anchor_text="기후에너지환경부령",
        base_law_name="전기사업법",
        base_law_type="법률",
        context_law_name=None,
    )
    assert result["normalized"]["searchKey"] == "전기사업법 시행규칙"


def test_context_law_override():
    result = normalize_delegation_term(
        anchor_text="대통령령",
        base_law_name="전기사업법",
        base_law_type="법률",
        context_law_name="신에너지 및 재생에너지 개발ㆍ이용ㆍ보급 촉진법",
    )
    assert result["normalized"]["searchKey"] == "신에너지 및 재생에너지 개발ㆍ이용ㆍ보급 촉진법 시행령"


def test_self_resolution_in_decree():
    result = normalize_delegation_term(
        anchor_text="대통령령",
        base_law_name="전기사업법 시행령",
        base_law_type="대통령령",
        context_law_name=None,
    )
    assert result["normalized"]["resolution"] == "self"
