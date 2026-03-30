# docquality

A free, no-API, pure Python CLI tool that evaluates any documentation page against 15 quality criteria and produces a JSON score file and a markdown report.

**No LLM. No API key. No cost.**

---

## What it does

Give it a URL. It fetches the page, strips navigation and chrome, analyses the prose, and scores it against 15 heuristic criteria across 6 dimensions:

| Dimension | Criteria |
|---|---|
| Voice & Tone | Active voice, Second person, Imperative mood |
| Discoverability | Internal cross-links, Related Topics section, Task-oriented link text |
| Style Governance | Consistent capitalisation, Acronym expansion |
| Search Effectiveness | Descriptive page title, Heading density |
| SEO Compliance | Meta description present, Canonical URL |
| Second Person Usage | No third-person self-reference, No passive instructions, Direct address consistency |

Every score is backed by a direct quote or a measurable count from the page. No interpretation. No guessing.

---

## Install

Python 3.8+ required.

```bash
git clone https://github.com/docquality/docquality.git
cd docquality
pip install -r requirements.txt
```

---

## Usage

**Evaluate a single URL:**
```bash
python eval.py --url https://docs.example.com/getting-started
```

**Scores-only summary (no files written):**
```bash
python eval.py --url https://docs.example.com/getting-started --summary
```

**Evaluate a list of URLs:**
```bash
python eval.py --urls urls.txt
```

**Custom output directory:**
```bash
python eval.py --url https://docs.example.com/getting-started --out results/
```

**Compare two score files (before and after a fix):**
```bash
python compare.py output/before_score.json output/after_score.json
```

---

## Output

For each URL evaluated, two files are written to `output/` (gitignored):

| File | Contents |
|---|---|
| `<slug>_score.json` | Full JSON score file — one object per criterion |
| `<slug>_report.md` | Markdown report with grade, dimension table, and full findings |

### JSON score format

```json
{
  "meta": {
    "url": "https://docs.example.com/auth/getting-started",
    "evaluated": "2024-01-15 09:30 UTC",
    "word_count": 850,
    "fetch_duration_ms": 312,
    "grade": "C",
    "summary": "9 passed · 4 warnings · 2 failed (out of 15 criteria)"
  },
  "scores": [
    {
      "id": "C06",
      "name": "Active voice",
      "dimension": "Voice & Tone",
      "score": "FAIL",
      "confidence": "high",
      "evidence": "5 of 18 sentences contain passive constructions (28%). Example: \"The setting should be configured before use.\"",
      "suggestion": "Rewrite passive constructions so the subject acts: 'Configure the setting' not 'The setting should be configured'.",
      "detail": {
        "passive_count": 5,
        "sentence_count": 18,
        "passive_ratio": 0.278
      }
    }
  ]
}
```

### Grading scale

| Grade | Meaning |
|---|---|
| A | 0 failures, 0–2 warnings |
| B | 0 failures, 3+ warnings |
| C | 1–2 failures |
| D | 3–4 failures |
| F | 5+ failures |

---

## The evaluate → fix → re-score loop

The intended workflow is:

```
1. python eval.py --url <url>          # baseline score
2. Fix the issues in your docs
3. python eval.py --url <url>          # re-score
4. python compare.py before.json after.json   # see what changed
```

`compare.py` exits with code `0` (improved), `1` (regression), or `2` (no change) — suitable for CI integration.

---

## urls.txt format

One URL per line. Lines starting with `#` are treated as comments.

```
# Authentication docs
https://docs.example.com/auth/getting-started
https://docs.example.com/auth/oauth-flows

# API reference
https://docs.example.com/api/overview
```

---

## Known limitations

**JavaScript-rendered pages.** The crawler uses `requests` + `BeautifulSoup` and cannot execute JavaScript. Pages that render their content client-side (some Docusaurus v2/v3 sites, Notion exports, certain GitBook deployments) may return thin HTML before hydration. When this happens, the tool warns: `low_content: only N words extracted`. The scores will still run but may not be representative. A Playwright-based crawler is a Phase 2 item.

**Content selector misses.** The crawler tries a priority list of CSS selectors to find the main content block — covering MkDocs, Docusaurus, Sphinx, GitBook, ReadTheDocs, and plain HTML. Heavily customised doc platforms may not match any selector and fall back to `<body>` with chrome stripped. If you see unexpectedly low word counts, check which content block was selected by running `python crawler.py <url>` directly.

**Passive voice false positives.** The passive-voice heuristic uses a regex pattern that catches `is/are/was/were + past participle`. It will occasionally flag non-passive constructions (e.g. "the feature is deprecated"). The ratio threshold (FAIL at ≥30%) is designed to tolerate a small number of false positives without masking genuinely passive-heavy pages.

**Short pages.** The heading density criterion (C21) scores pages with fewer than 150 words per heading as FAIL. Very short pages (under ~300 words) will almost always fail this check regardless of quality. Use your judgement on short reference pages.

---

## Phase 2 — coming later

The following criteria require semantic understanding and will be scored using an LLM (Claude API or Ollama local model) in a future release:

| ID | Criterion | Why deferred |
|---|---|---|
| C16 | Style guide compliance | Too broad — requires holistic tone/tense/punctuation judgment |
| C17 | Clear user outcome | Requires understanding the intent of the intro paragraph |
| C18 | Task-oriented headings | Requires distinguishing topic headings from task headings semantically |
| C19 | No orphan content | Requires understanding section-level narrative flow |

Phase 2 will be opt-in and will require an API key. Phase 1 (this tool) will always remain free.

---

## Project structure

```
docquality/
├── README.md
├── requirements.txt
├── .gitignore
├── eval.py          # CLI entry point
├── crawler.py       # Fetch URL, strip chrome, extract content signals
├── scorer.py        # 15 heuristic checks → ScoreResult objects
├── report.py        # ScoreResult list → markdown report + JSON
├── compare.py       # Diff two score files, print delta table
├── criteria/
│   └── criteria.yaml    # 15 criteria definitions
├── output/          # Generated files land here (gitignored)
└── examples/
    ├── sample_score.json
    └── sample_report.md
```

---

## Running individual modules

Each module has a built-in smoke test you can run directly:

```bash
# Test the crawler on a URL
python crawler.py https://docs.example.com/getting-started

# Test the scorer (uses built-in fixture)
python scorer.py https://docs.example.com/getting-started

# Test the report renderer (uses built-in fixture)
python report.py
```

---

## Licence

MIT
