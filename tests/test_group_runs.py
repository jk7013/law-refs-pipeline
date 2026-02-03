from law_refs.domain.normalize import is_run_joiner


def test_is_run_joiner_punctuation():
    assert is_run_joiner(" ") is True
    assert is_run_joiner("ㆍ") is True
    assert is_run_joiner("의") is True
    assert is_run_joiner("그리고") is False

