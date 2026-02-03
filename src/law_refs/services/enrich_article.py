from law_refs.parsing.html_locator import locate_article_body_html
from law_refs.parsing.related_law_extract import extract_related_laws
from law_refs.db.repo import update_related_laws
from law_refs.services.related_laws_enricher import resolve_related_laws


def enrich_one_article(
    conn,
    *,
    law_key: str,
    article_key: str,
    raw_html: str,
    current_law_name: str,
    base_law_type: str,
) -> int:
    located = locate_article_body_html(raw_html)
    refs = extract_related_laws(
        located.body_html,
        current_law_name=current_law_name,
        base_law_type=base_law_type,
    )
    refs = resolve_related_laws(conn, refs)
    return update_related_laws(
        conn, law_key=law_key, article_key=article_key, related_laws=refs
    )

