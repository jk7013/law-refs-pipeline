import re
from dataclasses import dataclass
from typing import List, Optional

from bs4 import BeautifulSoup


ARTICLE_NO_RE = re.compile(r"제(\d+)(?:조|조의\d+)")


@dataclass
class ArticleBlock:
    article_no: Optional[int]
    html: str


def extract_article_blocks(body_html: str) -> List[ArticleBlock]:
    soup = BeautifulSoup(body_html, "lxml")
    blocks: List[ArticleBlock] = []

    for lawcon in soup.find_all("div", class_="lawcon"):
        text = lawcon.get_text(" ", strip=True)
        m = ARTICLE_NO_RE.search(text)
        article_no = int(m.group(1)) if m else None
        blocks.append(ArticleBlock(article_no=article_no, html=str(lawcon)))

    if not blocks:
        # Fallback: treat whole body as one block
        blocks.append(ArticleBlock(article_no=None, html=body_html))

    return blocks

