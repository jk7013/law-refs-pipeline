import json
from related_refs.simplify import simplify_refs


def test_simplify_delegation_and_dedupe():
    raw = {
        "refs": [
            {
                "type": "delegation",
                "target": {"lawName": "전기사업법", "lawType": None},
                "evidence": {
                    "anchorText": "대통령령",
                    "onclick": "javascript:fncLsPttnLinkPop('118678');",
                    "href": "javascript:;",
                    "snippet": "대통령령으로 정하는",
                    "groupKey": "p#x",
                },
                "normalized": {"searchKey": "전기사업법 시행령"},
            },
            {
                "type": "delegation",
                "target": {"lawName": "전기사업법", "lawType": None},
                "evidence": {
                    "anchorText": "대통령령",
                    "onclick": "javascript:fncLsPttnLinkPop('118678');",
                    "href": "javascript:;",
                    "snippet": "대통령령으로 정하는",
                    "groupKey": "p#x",
                },
                "normalized": {"searchKey": "전기사업법 시행령"},
            },
        ]
    }
    result = simplify_refs(raw, source_law_name="전기사업법")
    assert len(result["refs"]) == 1
    assert result["refs"][0]["target"]["lawName"] == "전기사업법 시행령"

