import argparse
import json
from pathlib import Path

from law_refs.db.config import DbConfig
from law_refs.db.connection import get_connection
from law_refs.services.enrich_article import enrich_one_article
from law_refs.services.pipeline import run_dry_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Law refs pipeline CLI")
    parser.add_argument("--input-html", required=True, help="Input HTML file")
    parser.add_argument("--law-key", required=True, help="Law key (LAW_...)")
    parser.add_argument("--article-key", required=True, help="Article key (조문키)")
    parser.add_argument("--law-name", required=True, help="Law name")
    parser.add_argument("--law-type", default="법률", help="Law type (법률/대통령령/총리령/부령)")
    parser.add_argument("--dry-run", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    input_path = Path(args.input_html)
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        return 1

    raw_html = input_path.read_text(encoding="utf-8")

    if args.dry_run:
        result = run_dry_pipeline(
            raw_html,
            current_law_name=args.law_name,
            base_law_type=args.law_type,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    config = DbConfig.from_env()
    with get_connection(config) as conn:
        updated = enrich_one_article(
            conn,
            law_key=args.law_key,
            article_key=args.article_key,
            raw_html=raw_html,
            current_law_name=args.law_name,
            base_law_type=args.law_type,
        )
        print(f"updated={updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
