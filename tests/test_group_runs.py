from src.refs.group_runs import group_runs


def test_group_runs_join_by_punctuation():
    candidates = [
        {
            "source_element": "a",
            "source_file": "sample.html",
            "context_path": "p.test",
            "parent_tag": "p",
            "parent_id": None,
            "parent_class": "test",
            "anchor_index": 0,
            "anchor_text": "「법률」",
            "between_prev_text": "",
        },
        {
            "source_element": "a",
            "source_file": "sample.html",
            "context_path": "p.test",
            "parent_tag": "p",
            "parent_id": None,
            "parent_class": "test",
            "anchor_index": 1,
            "anchor_text": "제2조",
            "between_prev_text": " ",
        },
    ]
    runs = group_runs(candidates)
    assert len(runs) == 1
    assert runs[0]["run_text"] == "「법률」 제2조"

