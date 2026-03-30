"""
eval.py — CLI entry point for docquality.

Usage
-----
  python eval.py --url https://example.com/docs/intro.html
  python eval.py --url https://example.com/docs/intro.html --summary
  python eval.py --urls urls.txt
  python eval.py --urls urls.txt --summary
  python eval.py --url https://example.com/docs/intro.html --out output/my_score.json

Outputs (written to output/ by default)
-----------------------------------------
  <slug>_score.json     — full JSON score file
  <slug>_report.md      — full markdown report
  (with --summary: prints a compact score table to stdout, no files written)
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

from crawler import crawl, CrawlResult
from scorer import score
from report import build_report, save_report, results_to_json, save_json


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path("output")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _url_to_slug(url: str) -> str:
    """
    Convert a URL to a filesystem-safe slug for output filenames.
    e.g. https://docs.example.com/auth/getting-started
         → docs.example.com_auth_getting-started
    """
    parsed = urlparse(url)
    path = parsed.path.strip("/").replace("/", "_")
    slug = f"{parsed.netloc}_{path}" if path else parsed.netloc
    # Remove any characters that aren't alphanumeric, dash, dot, or underscore
    slug = re.sub(r"[^\w.\-]", "_", slug)
    # Truncate to avoid absurdly long filenames
    return slug[:80]


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _print_summary_table(results, url: str, grade: str, summary: str) -> None:
    """Print a compact score table to stdout."""
    print(f"\nURL: {url}")
    print(f"Grade: {grade}  —  {summary}\n")
    print(f"{'ID':<6} {'Score':<6} {'Criterion':<35} {'Dimension'}")
    print("─" * 80)
    for r in results:
        icon = {"PASS": "✓", "WARN": "~", "FAIL": "✗"}[r.score]
        print(f"{r.id:<6} {icon} {r.score:<4} {r.name:<35} {r.dimension}")
    print()


def _print_full_findings(results) -> None:
    """Print WARN and FAIL findings with evidence to stdout."""
    issues = [r for r in results if r.score != "PASS"]
    if not issues:
        print("No issues found.\n")
        return
    print("\nFindings requiring attention:\n")
    for r in issues:
        icon = {"WARN": "⚠", "FAIL": "✗"}[r.score]
        print(f"  {icon}  [{r.id}] {r.name} — {r.score}")
        print(f"     Evidence  : {r.evidence}")
        print(f"     Suggestion: {r.suggestion}")
        print()


def _load_urls(path: str) -> list[str]:
    """Read a newline-separated list of URLs from a file."""
    p = Path(path)
    if not p.exists():
        print(f"ERROR: URL file not found: {path}", file=sys.stderr)
        sys.exit(1)
    urls = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    if not urls:
        print(f"ERROR: No URLs found in {path}", file=sys.stderr)
        sys.exit(1)
    return urls


def _eval_one(url: str, summary_only: bool, out_dir: Path) -> dict:
    """
    Crawl, score, and report a single URL.
    Returns the JSON data dict (for multi-URL aggregation).
    """
    print(f"\n{'─' * 60}")
    print(f"Evaluating: {url}")
    print(f"{'─' * 60}")

    # ── Crawl ──────────────────────────────────────────────────────────────
    try:
        crawl_result = crawl(url)
    except requests.RequestException as e:
        print(f"  ERROR (network): {e}", file=sys.stderr)
        return {}
    except ValueError as e:
        print(f"  ERROR (invalid URL): {e}", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"  ERROR (unexpected): {e}", file=sys.stderr)
        return {}

    print(f"  Fetched in {crawl_result.fetch_duration_ms}ms  "
          f"({crawl_result.word_count} words)")

    if crawl_result.warnings:
        for w in crawl_result.warnings:
            print(f"  ⚠  {w}")

    # ── Score ──────────────────────────────────────────────────────────────
    score_results = score(crawl_result)
    ts = _timestamp()
    json_data = results_to_json(
        score_results,
        url=crawl_result.url,
        word_count=crawl_result.word_count,
        fetch_ms=crawl_result.fetch_duration_ms,
        warnings=crawl_result.warnings,
        timestamp=ts,
    )

    grade = json_data["meta"]["grade"]
    summary_line = json_data["meta"]["summary"]

    # ── Output ─────────────────────────────────────────────────────────────
    if summary_only:
        _print_summary_table(score_results, crawl_result.url, grade, summary_line)
    else:
        # Print findings to stdout
        _print_summary_table(score_results, crawl_result.url, grade, summary_line)
        _print_full_findings(score_results)

        # Write files
        out_dir.mkdir(parents=True, exist_ok=True)
        slug = _url_to_slug(crawl_result.url)

        json_path = out_dir / f"{slug}_score.json"
        md_path = out_dir / f"{slug}_report.md"

        save_json(json_data, str(json_path))

        md = build_report(
            score_results,
            url=crawl_result.url,
            word_count=crawl_result.word_count,
            fetch_ms=crawl_result.fetch_duration_ms,
            warnings=crawl_result.warnings,
            timestamp=ts,
        )
        save_report(md, str(md_path))

    return json_data


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eval.py",
        description=(
            "Evaluate documentation quality for one or more URLs.\n"
            "Produces a JSON score file and a markdown report per URL."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python eval.py --url https://docs.example.com/intro
  python eval.py --url https://docs.example.com/intro --summary
  python eval.py --urls urls.txt
  python eval.py --urls urls.txt --out results/
        """,
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--url",
        metavar="URL",
        help="Single documentation URL to evaluate.",
    )
    source.add_argument(
        "--urls",
        metavar="FILE",
        help="Path to a text file containing one URL per line.",
    )

    parser.add_argument(
        "--summary",
        action="store_true",
        help=(
            "Print a compact score table only. "
            "No files are written with this flag."
        ),
    )
    parser.add_argument(
        "--out",
        metavar="DIR",
        default=str(OUTPUT_DIR),
        help=f"Directory to write output files (default: {OUTPUT_DIR}).",
    )

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    out_dir = Path(args.out)

    if args.url:
        urls = [args.url]
    else:
        urls = _load_urls(args.urls)

    print(f"\ndocquality — Phase 1 heuristic scorer")
    print(f"15 criteria · no LLM · no API cost")

    results_all = []
    for url in urls:
        data = _eval_one(url, summary_only=args.summary, out_dir=out_dir)
        if data:
            results_all.append(data)

    # ── Multi-URL summary ─────────────────────────────────────────────────
    if len(urls) > 1 and results_all:
        print(f"\n{'═' * 60}")
        print(f"Batch summary — {len(results_all)} of {len(urls)} URLs evaluated")
        print(f"{'═' * 60}")
        print(f"\n{'URL':<55} {'Grade':<6} Summary")
        print("─" * 90)
        for d in results_all:
            m = d["meta"]
            url_short = m["url"][:52] + "..." if len(m["url"]) > 55 else m["url"]
            print(f"{url_short:<55} {m['grade']:<6} {m['summary']}")
        print()

        if not args.summary:
            # Write a combined JSON file for the batch
            out_dir.mkdir(parents=True, exist_ok=True)
            batch_ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            batch_path = out_dir / f"batch_{batch_ts}.json"
            with open(batch_path, "w", encoding="utf-8") as f:
                json.dump(results_all, f, indent=2, ensure_ascii=False)
            print(f"Batch JSON saved: {batch_path}")


if __name__ == "__main__":
    main()
