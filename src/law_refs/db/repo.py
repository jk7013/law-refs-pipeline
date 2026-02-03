import json
from typing import Sequence

from law_refs.domain.models import RelatedLawRef


def build_update_related_laws_sql() -> str:
    return (
        "UPDATE public.law_article "
        "SET related_laws = %s, updated_at = now() "
        "WHERE law_key = %s AND article_key = %s"
    )

def resolve_law_key_by_name(conn, *, law_name: str) -> str | None:
    sql = "SELECT law_key FROM public.law WHERE law_name_ko = %s LIMIT 1"
    with conn.cursor() as cur:
        cur.execute(sql, (law_name,))
        row = cur.fetchone()
    return row[0] if row else None


def update_related_laws(
    conn,
    *,
    law_key: str,
    article_key: str,
    related_laws: Sequence[RelatedLawRef],
) -> int:
    sql = build_update_related_laws_sql()
    payload = json.dumps(
        [
            {
                "type": ref.type.value,
                "target": {
                    "lawName": ref.target.law_name,
                    "lawId": ref.target.law_id,
                    "article": ref.target.article,
                    "paragraph": ref.target.paragraph,
                    "item": ref.target.item,
                    "subitem": ref.target.subitem,
                    "ref_range": ref.target.ref_range,
                    "lawType": ref.target.law_type,
                },
                "evidence": {
                    "anchorText": ref.evidence.anchor_text,
                    "href": ref.evidence.href,
                    "onclick": ref.evidence.onclick,
                    "snippet": ref.evidence.snippet,
                    "groupKey": ref.evidence.group_key,
                    "groupAnchors": ref.evidence.group_anchors,
                },
                "confidence": ref.confidence,
                "normalized": {
                    "searchKey": ref.normalized.search_key if ref.normalized else None,
                    "queryTokens": ref.normalized.query_tokens if ref.normalized else None,
                    "resolution": ref.normalized.resolution if ref.normalized else None,
                    "lawKey": ref.normalized.law_key if ref.normalized else None,
                    "issuerHint": ref.normalized.issuer_hint if ref.normalized else None,
                },
            }
            for ref in related_laws
        ],
        ensure_ascii=False,
    )
    with conn.cursor() as cur:
        cur.execute(sql, (payload, law_key, article_key))
        return cur.rowcount

