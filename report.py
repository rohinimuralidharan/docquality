"""
report.py — convert a list of ScoreResult objects into a markdown report.

The report has three sections:
  1. Header — URL, date, overall score summary
  2. Dimension summary table — one row per dimension
  3. Full findings — one block per criterion with evidence and suggestion

Output is a string of markdown. The caller (eval.py) decides where to write it.
"""

import sys
import json
from datetime import datetime, timezone
from collections import defaultdict
from typing import Optional

from scorer import ScoreResult


# ---------------------------------------------------------------------------
# Score icons and labels
# ---------------------------------------------------------------------------

ICONS = {
    "PASS": "✅",
    "WARN": "⚠️",
    "FAIL": "❌",
}

SCORE_ORDER = {"FAIL": 0, "WARN": 1, "PASS": 2}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _overall_grade(results: list[ScoreResult]) -> tuple[str, str]:
    """
    Return (letter_grade, summary_line) based on pass/warn/fail counts.

    Grading:
      A  — 0 FAIL,  0–2 WARN
      B  — 0 FAIL,  3+  WARN
      C  — 1–2 FAIL
      D  — 3–4 FAIL
      F  — 5+  FAIL
    """
    fail = sum(1 for r in results if r.score == "FAIL")
    warn = sum(1 for r in results if r.score == "WARN")
    passed = sum(1 for r in results if r.score == "PASS")
    total = len(results)

    if fail == 0 and warn <= 2:
        grade = "A"
    elif fail == 0:
        grade = "B"
    elif fail <= 2:
        grade = "C"
    elif fail <= 4:
        grade = "D"
    else:
        grade = "F"

    summary = f"{passed} passed · {warn} warnings · {fail} failed (out of {total} criteria)"
    return grade, summary


def _dimension_table(results: list[ScoreResult]) -> str:
    """Build a markdown table summarising results by dimension."""
    by_dim: dict[str, list[ScoreResult]] = defaultdict(list)
    for r in results:
        by_dim[r.dimension].append(r)

    lines = [
        "| Dimension | ✅ Pass | ⚠️ Warn | ❌ Fail | Status |",
        "|-----------|--------|--------|--------|--------|",
    ]

    for dim, dim_results in by_dim.items():
        p = sum(1 for r in dim_results if r.score == "PASS")
        w = sum(1 for r in dim_results if r.score == "WARN")
        f = sum(1 for r in dim_results if r.score == "FAIL")

        if f > 0:
            status = "❌"
        elif w > 0:
            status = "⚠️"
        else:
            status = "✅"

        lines.append(f"| {dim} | {p} | {w} | {f} | {status} |")

    return "\n".join(lines)


def _finding_block(r: ScoreResult) -> str:
    """Render one criterion's finding as a markdown block."""
    icon = ICONS[r.score]
    lines = [
        f"### {icon} {r.id} — {r.name}",
        f"**Dimension:** {r.dimension}  ",
        f"**Score:** {r.score}  ",
        f"**Confidence:** {r.confidence}",
        "",
        f"**Evidence:** {r.evidence}",
        "",
        f"**Suggestion:** {r.suggestion}",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_report(
    results: list[ScoreResult],
    url: str,
    word_count: int = 0,
    fetch_ms: int = 0,
    warnings: Optional[list[str]] = None,
    timestamp: Optional[str] = None,
) -> str:
    """
    Convert scorer output into a full markdown report string.

    Parameters
    ----------
    results    : list of ScoreResult from scorer.score()
    url        : the page URL that was evaluated
    word_count : prose word count from CrawlResult
    fetch_ms   : fetch duration in milliseconds
    warnings   : crawler warnings (e.g. low_content)
    timestamp  : ISO timestamp string; defaults to now (UTC)
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    grade, summary_line = _overall_grade(results)
    warnings = warnings or []

    sections = []

    # ── Header ──────────────────────────────────────────────────────────────
    sections.append(f"# Documentation Quality Report\n")
    sections.append(f"**URL:** {url}  ")
    sections.append(f"**Evaluated:** {timestamp}  ")
    sections.append(f"**Word count:** {word_count}  ")
    sections.append(f"**Fetch time:** {fetch_ms}ms  ")
    sections.append(f"\n## Overall Grade: {grade}\n")
    sections.append(f"{summary_line}\n")

    # ── Crawler warnings ────────────────────────────────────────────────────
    if warnings:
        sections.append("### ⚠️ Crawler Warnings\n")
        for w in warnings:
            sections.append(f"- {w}")
        sections.append("")

    # ── Quick-win callout ───────────────────────────────────────────────────
    fails = [r for r in results if r.score == "FAIL"]
    if fails:
        sections.append("## 🎯 Quick Wins\n")
        sections.append(
            "Fix these first — each is a clear, actionable finding:\n"
        )
        for r in fails:
            sections.append(f"- **{r.id} {r.name}:** {r.suggestion}")
        sections.append("")

    # ── Dimension summary ───────────────────────────────────────────────────
    sections.append("## Results by Dimension\n")
    sections.append(_dimension_table(results))
    sections.append("")

    # ── Full findings ────────────────────────────────────────────────────────
    sections.append("## Full Findings\n")
    sections.append(
        "_Criteria are listed in order. "
        "Evidence is taken directly from the page — no interpretation._\n"
    )

    # Group by dimension, preserve order
    seen_dims = []
    by_dim: dict[str, list[ScoreResult]] = defaultdict(list)
    for r in results:
        by_dim[r.dimension].append(r)
        if r.dimension not in seen_dims:
            seen_dims.append(r.dimension)

    for dim in seen_dims:
        sections.append(f"### {dim}\n")
        for r in by_dim[dim]:
            sections.append(_finding_block(r))

    # ── Footer ───────────────────────────────────────────────────────────────
    sections.append("---\n")
    sections.append(
        "_Generated by [docquality](https://github.com/docquality/docquality) · "
        "Phase 1 heuristic scoring · No LLM, no API cost_"
    )

    return "\n".join(sections)


def save_report(markdown: str, path: str) -> None:
    """Write markdown string to a file."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"Report saved: {path}")


def results_to_json(
    results: list[ScoreResult],
    url: str,
    word_count: int = 0,
    fetch_ms: int = 0,
    warnings: Optional[list[str]] = None,
    timestamp: Optional[str] = None,
) -> dict:
    """Serialize results to a JSON-serialisable dict."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    grade, summary_line = _overall_grade(results)

    return {
        "meta": {
            "url": url,
            "evaluated": timestamp,
            "word_count": word_count,
            "fetch_duration_ms": fetch_ms,
            "grade": grade,
            "summary": summary_line,
            "warnings": warnings or [],
        },
        "scores": [
            {
                "id": r.id,
                "name": r.name,
                "dimension": r.dimension,
                "score": r.score,
                "confidence": r.confidence,
                "evidence": r.evidence,
                "suggestion": r.suggestion,
                "detail": r.detail,
            }
            for r in results
        ],
    }


def save_json(data: dict, path: str) -> None:
    """Write JSON dict to a file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"JSON saved:   {path}")


# ---------------------------------------------------------------------------
# CLI smoke test  (python report.py)  — uses the same fixture as scorer test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from bs4 import BeautifulSoup
    from crawler import (
        _remove_comments, _strip_chrome, _find_main_content,
        _extract_headings, _extract_links, _extract_code_blocks,
        _extract_meta, _clean_body_text, CrawlResult,
    )
    from scorer import score

    sample_html = '''<!DOCTYPE html>
<html>
<head>
  <title>Getting Started with Authentication | MyProduct Docs</title>
  <meta name="description" content="Learn how to authenticate using OAuth 2.0 and API keys.">
  <link rel="canonical" href="https://docs.example.com/auth/getting-started">
</head>
<body>
  <nav class="nav-sidebar"><a href="/docs">Home</a></nav>
  <article class="md-content__inner">
    <h1>Getting Started with Authentication</h1>
    <p>You can authenticate with the MyProduct API using either OAuth 2.0 or API keys.
    This guide explains both methods so you can choose the right one.</p>
    <h2>Before you begin</h2>
    <p>Make sure you have an account. The user should have the ADMIN role assigned
    before proceeding. This is required to generate credentials.</p>
    <h2>Option 1: API Key Authentication</h2>
    <p>To get your API key:</p>
    <ol>
      <li>Navigate to the <a href="/dashboard/keys">API Keys page</a>.</li>
      <li>Click <strong>Generate new key</strong>.</li>
      <li>Copy the key.</li>
    </ol>
    <pre><code>curl -H "Authorization: Bearer YOUR_KEY" https://api.example.com/ping</code></pre>
    <h2>Option 2: OAuth 2.0</h2>
    <p>OAuth 2.0 should be used when acting on behalf of a user.
    The token must be refreshed every 60 minutes. RBAC is evaluated at issuance.</p>
    <h2>See also</h2>
    <ul>
      <li><a href="/docs/auth/oauth-flows">OAuth flow reference</a></li>
      <li><a href="/docs/auth/scopes">Available scopes</a></li>
    </ul>
  </article>
  <footer>© 2024 MyProduct</footer>
</body>
</html>'''

    soup = BeautifulSoup(sample_html, "lxml")
    title, meta_desc, canonical = _extract_meta(soup)
    _remove_comments(soup)
    _strip_chrome(soup)
    content = _find_main_content(soup)
    headings = _extract_headings(content)
    links = _extract_links(content, "docs.example.com",
                           "https://docs.example.com/auth/getting-started")
    code_blocks = _extract_code_blocks(content)
    body_text = _clean_body_text(content)

    crawl_result = CrawlResult(
        url="https://docs.example.com/auth/getting-started",
        domain="docs.example.com",
        title=title, meta_description=meta_desc, canonical_url=canonical,
        headings=headings, links=links, body_text=body_text,
        code_blocks=code_blocks, word_count=len(body_text.split()),
        raw_html=sample_html, warnings=[], fetch_duration_ms=42,
    )

    score_results = score(crawl_result)

    # Build and print the markdown report
    md = build_report(
        score_results,
        url=crawl_result.url,
        word_count=crawl_result.word_count,
        fetch_ms=crawl_result.fetch_duration_ms,
        warnings=crawl_result.warnings,
        timestamp="2024-01-15 09:30 UTC",
    )

    print(md)

    # Also show the JSON structure
    print("\n\n── JSON output (first score entry) ──")
    data = results_to_json(
        score_results,
        url=crawl_result.url,
        word_count=crawl_result.word_count,
        fetch_ms=crawl_result.fetch_duration_ms,
        timestamp="2024-01-15 09:30 UTC",
    )
    print(json.dumps(data["meta"], indent=2))
    print(json.dumps(data["scores"][0], indent=2))
