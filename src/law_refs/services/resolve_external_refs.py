import re
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup


ARTICLE_HEADER_RE = re.compile(r"제(\d+)조(?:\(([^)]+)\))?")


@dataclass
class ResolvedExternalRef:
    law_name: Optional[str]
    article_no: Optional[int]
    article_title: Optional[str]
    article_text: Optional[str]
    source_url: str


def _extract_article_text(section) -> str:
    texts = []
    for p in section.find_all("p"):
        text = p.get_text(" ", strip=True)
        if text:
            texts.append(text)
    return "\n".join(texts)


def parse_external_popup_html(html: str, source_url: str) -> ResolvedExternalRef:
    soup = BeautifulSoup(html, "lxml")

    law_name = None
    h2 = soup.find("h2")
    if h2:
        law_name = h2.get_text(strip=True)

    article_no = None
    article_title = None
    article_text = None

    # Try to locate first article header
    header = soup.find("p", class_="pty1_p4")
    if header:
        header_text = header.get_text(" ", strip=True)
        m = ARTICLE_HEADER_RE.search(header_text)
        if m:
            try:
                article_no = int(m.group(1))
            except ValueError:
                article_no = None
            article_title = m.group(2)

        # Use surrounding container for text
        container = header.find_parent("div", class_="lawcon") or header.parent
        if container:
            article_text = _extract_article_text(container)

    return ResolvedExternalRef(
        law_name=law_name,
        article_no=article_no,
        article_title=article_title,
        article_text=article_text,
        source_url=source_url,
    )


def resolve_external_link(url: str, *, timeout: int = 10) -> ResolvedExternalRef:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return parse_external_popup_html(response.text, url)
