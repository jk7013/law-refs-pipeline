-- External reference tables (proposal)

CREATE TABLE IF NOT EXISTS public.law_article_ref (
    ref_id              bigserial PRIMARY KEY,
    base_law_key        varchar(256),
    base_article_no     varchar(64),
    base_article_key    varchar(64),
    ref_type            varchar(32), -- internal_citation, external_citation, delegation
    raw_anchor_text     text,
    raw_snippet         text,
    raw_group_key       text,
    raw_group_anchors_json jsonb,
    normalized_json     jsonb,
    external_link_json  jsonb,
    resolve_status      varchar(16), -- unresolved, resolved, failed, skipped
    resolved_at         timestamp without time zone,
    created_at          timestamp without time zone DEFAULT now(),
    updated_at          timestamp without time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.law_external_ref_cache (
    lsJoLnkSeq          varchar(64) PRIMARY KEY,
    url                 text,
    law_name            text,
    law_key             text,
    article_no          int,
    article_title       text,
    article_text        text,
    fetched_html_hash   text,
    fetched_at          timestamp without time zone,
    fetch_status        varchar(16), -- ok, failed
    error               text
);
