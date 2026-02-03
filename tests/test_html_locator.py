from pathlib import Path

from law_refs.parsing.html_locator import locate_article_body_html


def test_html_locator_con_scroll():
    sample = Path("data/samples/sample_body.html").read_text(encoding="utf-8")
    located = locate_article_body_html(sample)
    assert "conScroll" in located.body_html
    assert located.strategy == "div#conScroll"
