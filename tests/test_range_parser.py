from law_refs.domain.normalize import parse_range


def test_parse_range_inherit_clause():
    text = "제8조제1항제1호부터 제5호까지"
    result = parse_range(text)
    assert result is not None
    assert result["from"]["article"] == 8
    assert result["from"]["paragraph"] == 1
    assert result["from"]["item"] == 1
    assert result["to"]["article"] == 8
    assert result["to"]["paragraph"] == 1
    assert result["to"]["item"] == 5

