from dataclasses import dataclass
from typing import Dict, Any

from bs4 import BeautifulSoup


@dataclass
class LocatedHtml:
    body_html: str
    strategy: str
    debug: Dict[str, Any]


def locate_article_body_html(raw_html: str) -> LocatedHtml:
    soup = BeautifulSoup(raw_html, "lxml")

    # Strategy 1: main scroll area
    con_scroll = soup.find("div", id="conScroll")
    if con_scroll:
        return LocatedHtml(
            body_html=str(con_scroll),
            strategy="div#conScroll",
            debug={"selector": "div#conScroll"},
        )

    # Strategy 2: main content
    body = soup.find("body")
    if body:
        return LocatedHtml(
            body_html=str(body),
            strategy="body",
            debug={"selector": "body"},
        )

    # Fallback: full html
    return LocatedHtml(
        body_html=raw_html,
        strategy="raw_html",
        debug={"selector": "raw_html"},
    )

