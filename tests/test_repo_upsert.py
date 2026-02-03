from law_refs.db.repo import build_update_related_laws_sql


def test_repo_update_sql():
    sql = build_update_related_laws_sql()
    assert "UPDATE public.law_article" in sql
    assert "related_laws" in sql
    assert "law_key" in sql
    assert "article_key" in sql
