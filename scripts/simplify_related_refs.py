#!/usr/bin/env python3
import argparse

from related_refs.simplify import simplify_from_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Simplify related refs JSON")
    parser.add_argument("--input", required=True, help="dry_run_result.json")
    parser.add_argument("--output", required=True, help="related_refs.simple.json")
    parser.add_argument("--law-name", required=True, help="source law name")
    parser.add_argument("--law-key", default=None, help="source law key")
    parser.add_argument("--article-no", type=int, default=None, help="article number")
    args = parser.parse_args()

    simplify_from_file(
        args.input,
        args.output,
        source_law_name=args.law_name,
        source_law_key=args.law_key,
        article_no=args.article_no,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
