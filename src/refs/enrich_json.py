#!/usr/bin/env python3
"""
전기사업법.json에 연계법령 정보 병합
"""
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Set, Optional


def build_article_key(
    law_name: str,
    article_no: str,
    para: Optional[str] = None,
    clause: Optional[str] = None,
    subclause: Optional[str] = None,
) -> str:
    """조문 키 생성"""
    key_parts = [law_name, f"제{article_no}조"]
    if para:
        key_parts.append(f"제{para}항")
    if clause:
        key_parts.append(f"제{clause}호")
    if subclause:
        key_parts.append(f"제{subclause}목")
    return "|".join(key_parts)


def dedupe_references(references: List[Dict]) -> List[Dict]:
    """중복 참조 제거"""
    seen: Set[tuple] = set()
    deduped = []
    
    for ref in references:
        # 중복 키: (type, lawName, lawId, ref.article, ref.paragraph, ref.item, href/onclick)
        key = (
            ref.get("type"),
            ref.get("target", {}).get("lawName"),
            ref.get("target", {}).get("lawId"),
            (ref.get("target", {}).get("ref") or {}).get("article"),
            (ref.get("target", {}).get("ref") or {}).get("paragraph"),
            (ref.get("target", {}).get("ref") or {}).get("item"),
            ref.get("evidence", {}).get("href") or ref.get("evidence", {}).get("onclick"),
        )
        
        if key not in seen:
            seen.add(key)
            deduped.append(ref)
    
    return deduped


def enrich_json(
    law_json_path: Path,
    refs_jsonl_path: Path,
    output_path: Path,
    max_snippet_len: int = 200,
):
    """전기사업법.json에 연계법령 정보 병합"""
    # 법령 JSON 로드
    with open(law_json_path, "r", encoding="utf-8") as f:
        law_json = json.load(f)
    
    law_name = law_json.get("법령", {}).get("기본정보", {}).get("법령명_한글", "전기사업법")
    
    # 정규화된 참조 로드
    refs_by_article: Dict[str, List[Dict]] = {}
    
    with open(refs_jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            
            ref_data = json.loads(line)
            context = ref_data.get("context", {})
            target = ref_data.get("target", {})
            evidence = ref_data.get("evidence", {})

            # context 기반 조문 키 결정
            article_no = context.get("articleNo")
            if article_no:
                article_key = build_article_key(law_name, str(article_no))
            else:
                article_key = f"{law_name}|전체"

            ref_obj = {
                "type": ref_data.get("type"),
                "target": target,
                "evidence": {
                    "source": "law.go.kr",
                    "anchorText": evidence.get("anchorText"),
                    "href": evidence.get("href"),
                    "onclick": evidence.get("onclick"),
                    "snippet": (evidence.get("snippet") or "")[:max_snippet_len],
                    "groupAnchors": evidence.get("groupAnchors"),
                },
                "confidence": ref_data.get("confidence", 0.0),
            }

            if article_key not in refs_by_article:
                refs_by_article[article_key] = []
            refs_by_article[article_key].append(ref_obj)
    
    # 중복 제거
    for key in refs_by_article:
        refs_by_article[key] = dedupe_references(refs_by_article[key])
    
    # JSON에 병합
    articles = law_json.get("법령", {}).get("조문", {}).get("조문단위", [])
    
    for article in articles:
        article_no = article.get("조문번호", "")
        if article_no:
            article_key = build_article_key(law_name, article_no)
            if article_key in refs_by_article:
                if "related_laws" not in article:
                    article["related_laws"] = []
                article["related_laws"].extend(refs_by_article[article_key])
    
    # 출력
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(law_json, f, ensure_ascii=False, indent=2)
    
    # 통계
    total_refs = sum(len(refs) for refs in refs_by_article.values())
    articles_with_refs = len(refs_by_article)
    
    print(f"연계정보가 들어간 조문 수: {articles_with_refs}")
    print(f"조문당 평균 참조 수: {total_refs/articles_with_refs:.2f}" if articles_with_refs > 0 else "0")
    print(f"출력 파일: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="전기사업법.json에 연계법령 정보 병합")
    parser.add_argument("--law-json", required=True, help="입력 법령 JSON 파일")
    parser.add_argument("--refs", required=True, help="입력 정규화된 참조 JSONL 파일")
    parser.add_argument("--out", required=True, help="출력 enriched JSON 파일")
    parser.add_argument("--max-snippet-len", type=int, default=200, help="HTML 스니펫 최대 길이")
    
    args = parser.parse_args()
    
    law_json_path = Path(args.law_json)
    refs_jsonl_path = Path(args.refs)
    output_path = Path(args.out)
    
    if not law_json_path.exists():
        print(f"Error: {law_json_path} 파일을 찾을 수 없습니다.")
        return 1
    
    if not refs_jsonl_path.exists():
        print(f"Error: {refs_jsonl_path} 파일을 찾을 수 없습니다.")
        return 1
    
    enrich_json(law_json_path, refs_jsonl_path, output_path, args.max_snippet_len)
    
    return 0


if __name__ == "__main__":
    exit(main())

