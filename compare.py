"""
compare.py — diff two docquality score files and show what changed.

Usage
-----
  python compare.py output/before_score.json output/after_score.json

Output
------
  A delta table showing score changes per criterion, plus a summary of
  improvements, regressions, and unchanged criteria.

Exit codes
----------
  0 — at least one improvement, no regressions
  1 — regressions present (score got worse)
  2 — no changes detected
  3 — usage/file error
"""

import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCORE_RANK = {"FAIL": 0, "WARN": 1, "PASS": 2}

CHANGE_ICONS = {
    "improved": "↑",
    "regressed": "↓",
    "unchanged": "·",
}

SCORE_ICONS = {
    "PASS": "✓",
    "WARN": "~",
    "FAIL": "✗",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(3)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _index_scores(data: dict) -> dict[str, dict]:
    """Return a dict keyed by criterion ID."""
    return {s["id"]: s for s in data.get("scores", [])}


def _grade_delta(before_grade: str, after_grade: str) -> str:
    """Return a human-readable grade change string."""
    grade_rank = {"F": 0, "D": 1, "C": 2, "B": 3, "A": 4}
    b = grade_rank.get(before_grade, -1)
    a = grade_rank.get(after_grade, -1)
    if a > b:
        return f"{before_grade} → {after_grade}  ↑ improved"
    elif a < b:
        return f"{before_grade} → {after_grade}  ↓ regressed"
    else:
        return f"{before_grade} → {after_grade}  · unchanged"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compare(before_path: str, after_path: str) -> int:
    """
    Compare two score files. Print delta table. Return exit code.
    """
    before = _load(before_path)
    after = _load(after_path)

    before_meta = before.get("meta", {})
    after_meta = after.get("meta", {})

    before_scores = _index_scores(before)
    after_scores = _index_scores(after)

    all_ids = sorted(
        set(before_scores.keys()) | set(after_scores.keys()),
        key=lambda x: int(x[1:]) if x[1:].isdigit() else 0
    )

    improvements = []
    regressions = []
    unchanged = []

    rows = []
    for cid in all_ids:
        b = before_scores.get(cid)
        a = after_scores.get(cid)

        if b is None:
            rows.append((cid, a["name"], "—", a["score"], "new"))
            continue
        if a is None:
            rows.append((cid, b["name"], b["score"], "—", "removed"))
            continue

        b_rank = SCORE_RANK.get(b["score"], -1)
        a_rank = SCORE_RANK.get(a["score"], -1)

        if a_rank > b_rank:
            direction = "improved"
            improvements.append(cid)
        elif a_rank < b_rank:
            direction = "regressed"
            regressions.append(cid)
        else:
            direction = "unchanged"
            unchanged.append(cid)

        rows.append((cid, b["name"], b["score"], a["score"], direction))

    # ── Header ────────────────────────────────────────────────────────────
    print("\ndocquality — compare\n")
    print(f"  Before : {before_meta.get('url', before_path)}")
    print(f"           evaluated {before_meta.get('evaluated', '?')} · "
          f"grade {before_meta.get('grade', '?')}")
    print(f"  After  : {after_meta.get('url', after_path)}")
    print(f"           evaluated {after_meta.get('evaluated', '?')} · "
          f"grade {after_meta.get('grade', '?')}")
    print()

    before_grade = before_meta.get("grade", "?")
    after_grade = after_meta.get("grade", "?")
    print(f"  Overall grade: {_grade_delta(before_grade, after_grade)}")
    print()

    # ── Delta table ───────────────────────────────────────────────────────
    print(f"  {'ID':<6} {'Criterion':<35} {'Before':<8} {'After':<8} {'Change'}")
    print("  " + "─" * 72)

    for cid, name, b_score, a_score, direction in rows:
        icon = CHANGE_ICONS.get(direction, " ")
        b_icon = SCORE_ICONS.get(b_score, b_score)
        a_icon = SCORE_ICONS.get(a_score, a_score)

        # Colour the change column
        if direction == "improved":
            change_str = f"{icon} {direction}"
        elif direction == "regressed":
            change_str = f"{icon} {direction}  ← ACTION NEEDED"
        else:
            change_str = f"{icon}"

        print(
            f"  {cid:<6} {name:<35} "
            f"{b_icon} {b_score:<6} {a_icon} {a_score:<6} {change_str}"
        )

    # ── Summary ───────────────────────────────────────────────────────────
    print()
    print(f"  Summary")
    print(f"  ───────")
    print(f"  ↑ Improved  : {len(improvements)}  "
          + (f"({', '.join(improvements)})" if improvements else ""))
    print(f"  ↓ Regressed : {len(regressions)}  "
          + (f"({', '.join(regressions)})" if regressions else ""))
    print(f"  · Unchanged : {len(unchanged)}")
    print()

    # ── Evidence for regressions ──────────────────────────────────────────
    if regressions:
        print("  ⚠  Regressions — review these changes:\n")
        for cid in regressions:
            a = after_scores[cid]
            print(f"     [{cid}] {a['name']}")
            print(f"     Evidence  : {a['evidence']}")
            print(f"     Suggestion: {a['suggestion']}")
            print()

    # ── Evidence for improvements ─────────────────────────────────────────
    if improvements:
        print("  ✓  Improvements:\n")
        for cid in improvements:
            b = before_scores[cid]
            a = after_scores[cid]
            print(
                f"     [{cid}] {a['name']}  "
                f"{b['score']} → {a['score']}"
            )
        print()

    # ── Exit code ─────────────────────────────────────────────────────────
    if regressions:
        return 1
    if not improvements and not regressions:
        return 2
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare.py <before_score.json> <after_score.json>")
        sys.exit(3)

    exit_code = compare(sys.argv[1], sys.argv[2])
    sys.exit(exit_code)
