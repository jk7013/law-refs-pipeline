#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from law_refs.services.pipeline import run_dry_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Scratch extract related laws")
    parser.add_argument("--input-html", required=True, help="Input HTML file")
    parser.add_argument("--law-name", required=True, help="Law name")
    parser.add_argument("--law-type", default="법률", help="Law type (법률/대통령령/총리령/부령)")
    args = parser.parse_args()

    input_path = Path(args.input_html)
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        return 1

    raw_html = input_path.read_text(encoding="utf-8")
    result = run_dry_pipeline(
        raw_html,
        current_law_name=args.law_name,
        base_law_type=args.law_type,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
