#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
from datetime import datetime

import psycopg2


def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def normalize_date(value):
    if not value:
        return None
    value = str(value).strip()
    if re.fullmatch(r"\d{8}", value):
        return f"{value[0:4]}-{value[4:6]}-{value[6:8]}"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return value
    return None


def flatten_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = []
        for item in value:
            parts.append(flatten_text(item))
        return "\n".join([p for p in parts if p])
    return str(value).strip()


def build_article_no(article):
    base_no = (article.get("조문번호") or "").strip()
    sub_no = (article.get("조문가지번호") or "").strip()
    if sub_no:
        return f"{base_no}의{sub_no}"
    return base_no


def strip_revision_marks(text):
    if not text:
        return text
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"\[[^\]]*\]", "", text)
    return text.strip()


def normalize_id(value):
    if not value:
        return ""
    return re.sub(r"[^0-9A-Za-z가-힣]+", "", value)


def build_article_text(article):
    """
    조문 전체 텍스트를 생성합니다.
    조문 헤더 + 모든 항(①②) + 호(1호, 2호) + 목(가, 나)을 포함합니다.
    """
    parts = []
    
    # 1. 조문 헤더 구성
    article_no = build_article_no(article)
    article_title = article.get("조문제목") or ""
    article_content = strip_revision_marks(flatten_text(article.get("조문내용") or ""))
    
    # 조문내용에 이미 "제X조"가 포함되어 있는지 확인
    if article_content and f"제{article_no}조" in article_content:
        # 조문내용에 이미 헤더가 포함되어 있으면 그대로 사용
        header_text = article_content
    else:
        # 조문 헤더를 새로 구성: "제2조(정의) 이 법에서 사용하는 용어의 뜻은 다음과 같다."
        if article_title:
            header = f"제{article_no}조({article_title})"
        else:
            header = f"제{article_no}조"
        
        if article_content and article_content.strip():
            # 조문내용이 있으면 헤더에 추가
            header_text = f"{header} {article_content}".strip()
        else:
            header_text = header
    
    parts.append(header_text)
    
    # 2. 항 처리
    paras = article.get("항")
    if not paras:
        # 항이 없으면 조문내용만 반환
        result = "\n".join([p for p in parts if p])
        return result
    
    # 항이 dict 형태인 경우 (예: {"호": [...]})
    if isinstance(paras, dict):
        # 항번호와 항내용 처리
        para_no = (paras.get("항번호") or "").strip()
        para_content = strip_revision_marks(flatten_text(paras.get("항내용") or ""))
        
        # 항내용이 있으면 추가
        if para_content:
            if para_no:
                parts.append(f"{para_no} {para_content}")
            else:
                parts.append(para_content)
        
        # 호 처리 (항내용이 없어도 호는 반드시 처리)
        items = paras.get("호", []) or []
        for item in items:
            if isinstance(item, dict):
                item_no = (item.get("호번호") or "").strip()
                item_content_raw = item.get("호내용") or ""
                item_content = strip_revision_marks(flatten_text(item_content_raw))
                
                # 호내용이 비어있지 않으면 처리
                if item_content and item_content.strip():
                    # 호내용에 이미 호번호가 포함되어 있는지 확인
                    # (예: "1.  \"전기사업\"이란..." 형태)
                    if item_no and item_content.startswith(item_no):
                        # 이미 호번호가 포함되어 있으면 그대로 사용
                        parts.append(item_content)
                    elif item_no:
                        # 호번호가 포함되어 있지 않으면 추가
                        parts.append(f"{item_no} {item_content}")
                    else:
                        # 호번호가 없으면 내용만
                        parts.append(item_content)
                    
                    # 목 처리
                    subitems = item.get("목", []) or []
                    if subitems:
                        for subitem in subitems:
                            if isinstance(subitem, dict):
                                subitem_no = (subitem.get("목번호") or "").strip()
                                subitem_content_raw = subitem.get("목내용") or ""
                                subitem_content = strip_revision_marks(flatten_text(subitem_content_raw))
                                
                                if subitem_content and subitem_content.strip():
                                    # 목내용에 이미 목번호가 포함되어 있는지 확인
                                    if subitem_no and subitem_content.startswith(subitem_no):
                                        parts.append(f"  {subitem_content}")
                                    elif subitem_no:
                                        parts.append(f"  {subitem_no} {subitem_content}")
                                    else:
                                        parts.append(f"  {subitem_content}")
                            else:
                                subitem_text = strip_revision_marks(flatten_text(subitem))
                                if subitem_text:
                                    parts.append(f"  {subitem_text}")
                elif item_no:
                    # 호내용이 없지만 호번호는 있는 경우
                    parts.append(item_no)
            else:
                # dict가 아닌 경우
                item_text = strip_revision_marks(flatten_text(item))
                if item_text:
                    parts.append(item_text)
    
    # 항이 list 형태인 경우
    elif isinstance(paras, list):
        for para in paras:
            if isinstance(para, dict):
                para_no = (para.get("항번호") or "").strip()
                para_content = strip_revision_marks(flatten_text(para.get("항내용") or ""))
                
                if para_content:
                    if para_no:
                        parts.append(f"{para_no} {para_content}")
                    else:
                        parts.append(para_content)
                
                # 호 처리
                items = para.get("호", []) or []
                for item in items:
                    if isinstance(item, dict):
                        item_no = (item.get("호번호") or "").strip()
                        item_content_raw = item.get("호내용") or ""
                        item_content = strip_revision_marks(flatten_text(item_content_raw))
                        
                        # 호내용이 비어있지 않으면 처리
                        if item_content and item_content.strip():
                            # 호내용에 이미 호번호가 포함되어 있는지 확인
                            if item_no and item_content.startswith(item_no):
                                # 이미 호번호가 포함되어 있으면 그대로 사용
                                parts.append(item_content)
                            elif item_no:
                                # 호번호가 포함되어 있지 않으면 추가
                                parts.append(f"{item_no} {item_content}")
                            else:
                                # 호번호가 없으면 내용만
                                parts.append(item_content)
                            
                            # 목 처리
                            subitems = item.get("목", []) or []
                            if subitems:
                                for subitem in subitems:
                                    if isinstance(subitem, dict):
                                        subitem_no = (subitem.get("목번호") or "").strip()
                                        subitem_content_raw = subitem.get("목내용") or ""
                                        subitem_content = strip_revision_marks(flatten_text(subitem_content_raw))
                                        
                                        if subitem_content and subitem_content.strip():
                                            # 목내용에 이미 목번호가 포함되어 있는지 확인
                                            if subitem_no and subitem_content.startswith(subitem_no):
                                                parts.append(f"  {subitem_content}")
                                            elif subitem_no:
                                                parts.append(f"  {subitem_no} {subitem_content}")
                                            else:
                                                parts.append(f"  {subitem_content}")
                                    else:
                                        subitem_text = strip_revision_marks(flatten_text(subitem))
                                        if subitem_text:
                                            parts.append(f"  {subitem_text}")
                        elif item_no:
                            # 호내용이 없지만 호번호는 있는 경우
                            parts.append(item_no)
                    else:
                        # dict가 아닌 경우
                        item_text = strip_revision_marks(flatten_text(item))
                        if item_text:
                            parts.append(item_text)
            else:
                # dict가 아닌 경우
                para_text = strip_revision_marks(flatten_text(para))
                if para_text:
                    parts.append(para_text)
    
    result = "\n".join([p for p in parts if p])
    
    # 검증: "호" 단독으로 끝나지 않아야 함
    if result.strip() == "호" or result.strip().endswith("\n호"):
        raise ValueError(f"article_text가 '호' 단독으로 끝남: article_no={article_no}")
    
    # 검증: 최소 길이 확인 (단, "삭제" 같은 특수 케이스는 허용)
    result_stripped = result.strip()
    if len(result_stripped) < 10 and "삭제" not in result_stripped:
        raise ValueError(f"article_text가 너무 짧음: article_no={article_no}, text={result_stripped[:50]}")
    
    return result


def normalize_marker(value, fallback):
    if not value:
        return fallback
    circled = {
        "①": "1",
        "②": "2",
        "③": "3",
        "④": "4",
        "⑤": "5",
        "⑥": "6",
        "⑦": "7",
        "⑧": "8",
        "⑨": "9",
        "⑩": "10",
        "⑪": "11",
        "⑫": "12",
        "⑬": "13",
        "⑭": "14",
        "⑮": "15",
        "⑯": "16",
        "⑰": "17",
        "⑱": "18",
        "⑲": "19",
        "⑳": "20",
    }
    value = value.strip()
    value = circled.get(value, value)
    value = value.replace(".", "")
    value = re.sub(r"\s+", "", value)
    normalized = re.sub(r"[^0-9A-Za-z가-힣]+", "", value)
    return normalized or fallback


def parse_chunks(law_key, article_uid, article_no, article_text, article):
    chunks = []
    paras = article.get("항") or []
    if paras:
        for para_idx, para in enumerate(paras, start=1):
            if isinstance(para, dict):
                para_no = (para.get("항번호") or "").strip()
                para_text = strip_revision_marks(flatten_text(para.get("항내용")))
                items = para.get("호", []) or []
            else:
                para_no = ""
                para_text = strip_revision_marks(flatten_text(para))
                items = []
            if para_text:
                para_norm = normalize_marker(para_no, f"p{para_idx}")
                chunk_id = f"CHUNK_{law_key}_{article_no}_{para_norm}"
                path = f"제{article_no}조/{para_no}" if para_no else f"제{article_no}조"
                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "article_no": article_no,
                        "para_no": para_no or None,
                        "item_no": None,
                        "level": "paragraph",
                        "path": path,
                        "text": para_text,
                    }
                )

            for item_idx, item in enumerate(items, start=1):
                if isinstance(item, dict):
                    item_no = (item.get("호번호") or "").strip()
                    item_text = strip_revision_marks(flatten_text(item.get("호내용")))
                else:
                    item_no = ""
                    item_text = strip_revision_marks(flatten_text(item))
                if not item_text:
                    continue
                para_norm = normalize_marker(para_no, f"p{para_idx}")
                item_norm = normalize_marker(item_no, f"i{item_idx}")
                chunk_id = f"CHUNK_{law_key}_{article_no}_{para_norm}_{item_norm}"
                path = f"제{article_no}조/{para_no}/{item_no}" if para_no else f"제{article_no}조/{item_no}"
                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "article_no": article_no,
                        "para_no": para_no or None,
                        "item_no": item_no or None,
                        "level": "item",
                        "path": path,
                        "text": item_text,
                    }
                )
    else:
        if article_text:
            chunk_id = f"CHUNK_{law_key}_{article_no}"
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "article_no": article_no,
                    "para_no": None,
                    "item_no": None,
                    "level": "article",
                    "path": f"제{article_no}조",
                    "text": article_text,
                }
            )
    return chunks


def connect_db():
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
    )


def upsert_law(cur, law_row):
    cur.execute(
        """
        INSERT INTO public.law (
            law_key, law_id, law_name_ko, law_type_code, law_type_name,
            ministry_code, ministry_name, promulgation_date, promulgation_no,
            effective_date, revision_type, is_promulgated, created_at, updated_at
        ) VALUES (
            %(law_key)s, %(law_id)s, %(law_name_ko)s, %(law_type_code)s, %(law_type_name)s,
            %(ministry_code)s, %(ministry_name)s, %(promulgation_date)s, %(promulgation_no)s,
            %(effective_date)s, %(revision_type)s, %(is_promulgated)s, %(created_at)s, %(updated_at)s
        )
        ON CONFLICT (law_key) DO UPDATE SET
            law_id = EXCLUDED.law_id,
            law_name_ko = EXCLUDED.law_name_ko,
            law_type_code = EXCLUDED.law_type_code,
            law_type_name = EXCLUDED.law_type_name,
            ministry_code = EXCLUDED.ministry_code,
            ministry_name = EXCLUDED.ministry_name,
            promulgation_date = EXCLUDED.promulgation_date,
            promulgation_no = EXCLUDED.promulgation_no,
            effective_date = EXCLUDED.effective_date,
            revision_type = EXCLUDED.revision_type,
            is_promulgated = EXCLUDED.is_promulgated,
            updated_at = EXCLUDED.updated_at
        """,
        law_row,
    )


def upsert_raw_json(cur, law_key, payload, checksum):
    cur.execute(
        """
        INSERT INTO public.raw_law_json (law_key, source, json_payload, ingested_at, checksum)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (law_key) DO UPDATE SET
            json_payload = EXCLUDED.json_payload,
            checksum = EXCLUDED.checksum,
            ingested_at = EXCLUDED.ingested_at
        """,
        (law_key, "law.go.kr", json.dumps(payload, ensure_ascii=False), now_ts(), checksum),
    )


def upsert_articles(cur, law_key, articles):
    """
    조문 데이터를 DB에 저장합니다.
    컬럼 수 검증 및 article_text 검증을 수행합니다.
    """
    for article in articles:
        # 컬럼 수 검증 (13개 컬럼)
        expected_keys = {
            "article_uid", "law_key", "article_key", "article_no", "article_title",
            "article_type", "effective_date", "revision_type", "is_changed",
            "article_text", "source_json_path", "created_at", "updated_at"
        }
        actual_keys = set(article.keys())
        if actual_keys != expected_keys:
            missing = expected_keys - actual_keys
            extra = actual_keys - expected_keys
            raise ValueError(
                f"컬럼 수 불일치: article_uid={article.get('article_uid')}, "
                f"missing={missing}, extra={extra}"
            )
        
        # article_text 검증
        article_text = article.get("article_text", "")
        if not article_text or not article_text.strip():
            raise ValueError(
                f"article_text가 비어있음: article_uid={article.get('article_uid')}"
            )
        
        # "호" 단독 체크
        text_stripped = article_text.strip()
        if text_stripped == "호" or text_stripped.endswith("\n호"):
            raise ValueError(
                f"article_text가 '호' 단독으로 끝남: article_uid={article.get('article_uid')}"
            )
        
        # 최소 길이 확인 (단, "삭제" 같은 특수 케이스는 허용)
        if len(text_stripped) < 10 and "삭제" not in text_stripped:
            raise ValueError(
                f"article_text가 너무 짧음: article_uid={article.get('article_uid')}, "
                f"text={text_stripped[:50]}"
            )
        
        cur.execute(
            """
            INSERT INTO public.law_article (
                article_uid, law_key, article_key, article_no, article_title, article_type,
                effective_date, revision_type, is_changed, article_text, source_json_path,
                created_at, updated_at
            ) VALUES (
                %(article_uid)s, %(law_key)s, %(article_key)s, %(article_no)s, %(article_title)s,
                %(article_type)s, %(effective_date)s, %(revision_type)s, %(is_changed)s,
                %(article_text)s, %(source_json_path)s, %(created_at)s, %(updated_at)s
            )
            ON CONFLICT (article_uid) DO UPDATE SET
                article_key = EXCLUDED.article_key,
                article_title = EXCLUDED.article_title,
                article_type = EXCLUDED.article_type,
                effective_date = EXCLUDED.effective_date,
                revision_type = EXCLUDED.revision_type,
                is_changed = EXCLUDED.is_changed,
                article_text = EXCLUDED.article_text,
                source_json_path = EXCLUDED.source_json_path,
                updated_at = EXCLUDED.updated_at
            """,
            article,
        )


def upsert_chunks(cur, law_key, chunks):
    for chunk in chunks:
        cur.execute(
            """
            INSERT INTO public.law_provision_chunk (
                chunk_id, law_key, article_uid, article_no, para_no, item_no,
                level, path, text, search_weight, created_at
            ) VALUES (
                %(chunk_id)s, %(law_key)s, %(article_uid)s, %(article_no)s, %(para_no)s, %(item_no)s,
                %(level)s, %(path)s, %(text)s, 1.0, %(created_at)s
            )
            ON CONFLICT (chunk_id) DO UPDATE SET
                text = EXCLUDED.text,
                path = EXCLUDED.path
            """,
            {**chunk, "law_key": law_key, "created_at": now_ts()},
        )


def upsert_addenda(cur, law_key, addenda):
    for addendum in addenda:
        cur.execute(
            """
            INSERT INTO public.law_addendum (
                addendum_uid, law_key, promulgation_date, content_text, source_json_path, created_at
            ) VALUES (
                %(addendum_uid)s, %(law_key)s, %(promulgation_date)s, %(content_text)s,
                %(source_json_path)s, %(created_at)s
            )
            ON CONFLICT (addendum_uid) DO UPDATE SET
                content_text = EXCLUDED.content_text,
                source_json_path = EXCLUDED.source_json_path
            """,
            addendum,
        )


def main():
    parser = argparse.ArgumentParser(description="Load law JSON into Plan C schema.")
    parser.add_argument("--in", dest="input_json", required=True, help="Input JSON file path")
    args = parser.parse_args()

    with open(args.input_json, "rb") as f:
        raw_bytes = f.read()
    checksum = hashlib.sha256(raw_bytes).hexdigest()
    data = json.loads(raw_bytes.decode("utf-8"))
    law = data.get("법령", {})
    meta = law.get("기본정보", {})

    law_id = str(meta.get("법령ID") or "").strip()
    law_key = f"LAW_{law_id}"

    law_row = {
        "law_key": law_key,
        "law_id": law_id,
        "law_name_ko": meta.get("법령명_한글"),
        "law_type_code": (meta.get("법종구분") or {}).get("법종구분코드"),
        "law_type_name": (meta.get("법종구분") or {}).get("content"),
        "ministry_code": (meta.get("소관부처") or {}).get("소관부처코드"),
        "ministry_name": (meta.get("소관부처") or {}).get("content"),
        "promulgation_date": normalize_date(meta.get("공포일자")),
        "promulgation_no": meta.get("공포번호"),
        "effective_date": normalize_date(meta.get("시행일자")),
        "revision_type": meta.get("제개정구분"),
        "is_promulgated": meta.get("공포법령여부"),
        "created_at": now_ts(),
        "updated_at": now_ts(),
    }

    articles = []
    chunks = []
    for idx, article in enumerate((law.get("조문") or {}).get("조문단위") or []):
        if article.get("조문여부") != "조문":
            continue
        article_no = build_article_no(article)
        if not article_no:
            continue
        article_uid = f"{law_key}:{article_no}"
        article_text = build_article_text(article)
        articles.append(
            {
                "article_uid": article_uid,
                "law_key": law_key,
                "article_key": article.get("조문키"),
                "article_no": article_no,
                "article_title": article.get("조문제목"),
                "article_type": article.get("조문여부"),
                "effective_date": normalize_date(article.get("조문시행일자")),
                "revision_type": article.get("조문제개정유형"),
                "is_changed": article.get("조문변경여부"),
                "article_text": article_text,
                "source_json_path": f"법령.조문.조문단위[{idx}]",
                "created_at": now_ts(),
                "updated_at": now_ts(),
            }
        )
        for chunk in parse_chunks(law_key, article_uid, article_no, article_text, article):
            chunk["article_uid"] = article_uid
            chunks.append(chunk)

    addenda = []
    for idx, addendum in enumerate((law.get("부칙") or {}).get("부칙단위") or []):
        addendum_uid = f"{law_key}:{addendum.get('부칙키') or idx}"
        addenda.append(
            {
                "addendum_uid": addendum_uid,
                "law_key": law_key,
                "promulgation_date": normalize_date(addendum.get("부칙공포일자")),
                "content_text": flatten_text(addendum.get("부칙내용")),
                "source_json_path": f"법령.부칙.부칙단위[{idx}]",
                "created_at": now_ts(),
            }
        )

    conn = connect_db()
    conn.autocommit = False
    cur = conn.cursor()
    try:
        upsert_law(cur, law_row)
        upsert_raw_json(cur, law_key, data, checksum)
        upsert_articles(cur, law_key, articles)
        upsert_chunks(cur, law_key, chunks)
        upsert_addenda(cur, law_key, addenda)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

    print(f"law_key={law_key}")
    print(f"articles={len(articles)} chunks={len(chunks)} addenda={len(addenda)}")
    print("ok")


if __name__ == "__main__":
    main()

