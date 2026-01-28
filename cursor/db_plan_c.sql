-- Plan C schema: JSON 기반 법령 DB 구축
-- 참고: HTML/연계법령 단계는 제외

CREATE TABLE IF NOT EXISTS public.law (
    law_key             varchar(256) PRIMARY KEY,
    law_id              varchar(64),
    law_name_ko         text,
    law_type_code       varchar(32),
    law_type_name       text,
    ministry_code       varchar(32),
    ministry_name       text,
    promulgation_date   date,
    promulgation_no     varchar(32),
    effective_date      date,
    revision_type       text,
    is_promulgated      varchar(2),
    created_at          timestamp without time zone DEFAULT now(),
    updated_at          timestamp without time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.law_article (
    article_uid         varchar(512) PRIMARY KEY, -- {law_key}:{article_no}
    law_key             varchar(256) NOT NULL REFERENCES public.law(law_key),
    article_key         varchar(64),
    article_no          varchar(64),
    article_title       text,
    article_type        varchar(32),
    effective_date      date,
    revision_type       text,
    is_changed          varchar(2),
    article_text        text,
    source_json_path    text,
    created_at          timestamp without time zone DEFAULT now(),
    updated_at          timestamp without time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.law_provision_chunk (
    chunk_id            varchar(512) PRIMARY KEY,
    law_key             varchar(256) NOT NULL REFERENCES public.law(law_key),
    article_uid         varchar(512) REFERENCES public.law_article(article_uid),
    article_no          varchar(64),
    para_no             varchar(16),
    item_no             varchar(16),
    level               varchar(16),
    path                text,
    text                text,
    search_weight       numeric DEFAULT 1.0,
    created_at          timestamp without time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.law_addendum (
    addendum_uid        varchar(512) PRIMARY KEY,
    law_key             varchar(256) NOT NULL REFERENCES public.law(law_key),
    promulgation_date   date,
    content_text        text,
    source_json_path    text,
    created_at          timestamp without time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.raw_law_json (
    law_key             varchar(256) PRIMARY KEY,
    source              text,
    json_payload        jsonb,
    ingested_at         timestamp without time zone DEFAULT now(),
    checksum            varchar(128)
);

