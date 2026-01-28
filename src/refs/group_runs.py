#!/usr/bin/env python3
"""
연속 a태그(run) 그룹화
"""
import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple


PUNCTUATION_ONLY_RE = re.compile(r'^[\s\(\)\[\]「」『』“”"\'.,ㆍ··…\-–—]*$')
SMALL_TOKENS = {"제", "의"}


def is_run_joiner(between_text: str) -> bool:
    """a태그 사이 텍스트가 run을 유지할 수 있는지 판단"""
    if between_text is None:
        return True
    text = between_text.strip()
    if not text:
        return True
    if text in SMALL_TOKENS:
        return True
    if PUNCTUATION_ONLY_RE.match(text):
        return True
    return False


def build_run_text(items: List[Dict[str, Any]]) -> str:
    """run 텍스트 구성"""
    parts = []
    for idx, item in enumerate(items):
        between = item.get("between_prev_text") or ""
        anchor_text = item.get("anchor_text") or ""
        if idx == 0:
            parts.append(anchor_text)
        else:
            parts.append(between)
            parts.append(anchor_text)
    return "".join(parts).strip()


def group_runs(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """후보 URL을 run 단위로 그룹화"""
    # a/onclick 후보만 대상
    anchor_candidates = [
        c for c in candidates if c.get("source_element") in ("a", "onclick")
    ]

    # 그룹 키: source_file + context_path + parent 정보
    groups: Dict[Tuple, List[Dict[str, Any]]] = {}
    for c in anchor_candidates:
        key = (
            c.get("source_file"),
            c.get("context_path"),
            c.get("parent_tag"),
            c.get("parent_id"),
            c.get("parent_class"),
        )
        groups.setdefault(key, []).append(c)

    runs: List[Dict[str, Any]] = []
    run_id = 0

    for key, items in groups.items():
        items_sorted = sorted(items, key=lambda x: (x.get("anchor_index") or 0))
        current_run: List[Dict[str, Any]] = []

        for item in items_sorted:
            between_text = item.get("between_prev_text") or ""
            if not current_run:
                current_run.append(item)
                continue

            if is_run_joiner(between_text):
                current_run.append(item)
            else:
                run_id += 1
                runs.append(
                    {
                        "run_id": run_id,
                        "source_file": key[0],
                        "context_path": key[1],
                        "parent_tag": key[2],
                        "parent_id": key[3],
                        "parent_class": key[4],
                        "parent_text": current_run[0].get("parent_text"),
                        "items": current_run,
                        "run_text": build_run_text(current_run),
                    }
                )
                current_run = [item]

        if current_run:
            run_id += 1
            runs.append(
                {
                    "run_id": run_id,
                    "source_file": key[0],
                    "context_path": key[1],
                    "parent_tag": key[2],
                    "parent_id": key[3],
                    "parent_class": key[4],
                    "parent_text": current_run[0].get("parent_text"),
                    "items": current_run,
                    "run_text": build_run_text(current_run),
                }
            )

    return runs


def main():
    parser = argparse.ArgumentParser(description="연속 a태그(run) 그룹화")
    parser.add_argument("--in", dest="input_file", required=True, help="입력 candidates.json")
    parser.add_argument("--out", required=True, help="출력 runs.json")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: {input_path} 파일을 찾을 수 없습니다.")
        return 1

    with open(input_path, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    runs = group_runs(candidates)

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(runs, f, ensure_ascii=False, indent=2)

    print(f"총 run 수: {len(runs)}")
    print(f"출력 파일: {output_path}")

    return 0


if __name__ == "__main__":
    exit(main())

