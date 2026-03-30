"""
scorer.py — run all 15 heuristic checks against a CrawlResult.

Each check returns a ScoreResult dataclass. The top-level score() function
runs all checks and returns a list of ScoreResult objects in criteria order.

Score values:  PASS | WARN | FAIL
Confidence:    high (all v1 criteria are high-confidence heuristics)
"""

import re
import sys
from dataclasses import dataclass, field
from typing import Optional

from crawler import CrawlResult, crawl


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ScoreResult:
    id: str
    name: str
    dimension: str
    score: str            # "PASS" | "WARN" | "FAIL"
    confidence: str       # always "high" for v1
    evidence: str         # direct quote or measurable count that drove the score
    suggestion: str       # one-line fix recommendation
    detail: dict = field(default_factory=dict)  # optional numeric detail


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------

# Common passive-voice auxiliary + past-participle pattern
_PASSIVE_PATTERN = re.compile(
    r'\b(is|are|was|were|be|been|being)\s+(\w+(?:ed|en))\b',
    re.IGNORECASE
)

# Sentence splitter (naive but good enough for prose heuristics)
_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')

# Third-person instruction patterns
_THIRD_PERSON_INSTRUCTION = re.compile(
    r'\bthe\s+(user|administrator|developer|operator|reader|customer)'
    r'\s+(should|must|can|will|needs?\s+to|is\s+required\s+to|has\s+to|ought\s+to)\b',
    re.IGNORECASE
)

# Passive instruction patterns
_PASSIVE_INSTRUCTION = re.compile(
    r'\b(should|must|needs?\s+to|has\s+to)\s+be\s+(\w+(?:ed|en))\b'
    r'|\b(can|may)\s+be\s+(\w+(?:ed|en))\s+by\b',
    re.IGNORECASE
)

# All-caps acronym (2+ letters)
_ACRONYM = re.compile(r'\b([A-Z]{2,})\b')

# Common words that look like acronyms but aren't
_NOT_ACRONYMS = {
    "URL", "HTML", "CSS", "HTTP", "HTTPS", "JSON", "XML", "PDF",
    "SQL", "API", "UI", "ID", "OK", "US", "UK", "EU", "UTC",
    "AM", "PM", "FAQ", "I", "A",
    # Directional / common English caps
    "NOTE", "WARNING", "IMPORTANT", "TIP", "CAUTION", "INFO",
}

# Imperative verb starters — common action verbs in documentation
_IMPERATIVE_VERBS = {
    "add", "allow", "apply", "assign", "avoid", "build", "call", "check",
    "choose", "click", "clone", "close", "configure", "connect", "copy",
    "create", "define", "delete", "deploy", "disable", "download", "enable",
    "enter", "export", "find", "follow", "generate", "get", "go", "grant",
    "import", "include", "install", "launch", "list", "load", "log",
    "make", "modify", "move", "navigate", "note", "open", "pass", "paste",
    "press", "provide", "pull", "push", "read", "remove", "replace",
    "restart", "run", "save", "select", "set", "specify", "start", "stop",
    "submit", "switch", "test", "update", "upload", "use", "verify", "view",
    "visit", "wait", "write",
}

# Generic / bad link text patterns
_BAD_LINK_PATTERNS = [
    re.compile(r'^https?://', re.IGNORECASE),
    re.compile(r'^click\s+here$', re.IGNORECASE),
    re.compile(r'^here$', re.IGNORECASE),
    re.compile(r'^this\s+page$', re.IGNORECASE),
    re.compile(r'^link$', re.IGNORECASE),
    re.compile(r'^read\s+more$', re.IGNORECASE),
    re.compile(r'^learn\s+more$', re.IGNORECASE),
    re.compile(r'^more$', re.IGNORECASE),
    re.compile(r'^see\s+more$', re.IGNORECASE),
]

# Related-topics heading patterns
_RELATED_HEADING_PATTERNS = re.compile(
    r'\b(related|see\s+also|next\s+steps|what\'?s?\s+next|'
    r'further\s+reading|learn\s+more|additional\s+resources)\b',
    re.IGNORECASE
)

# Generic title words that alone constitute a bad title
_GENERIC_TITLE_WORDS = {
    "home", "index", "untitled", "page", "documentation",
    "docs", "welcome", "introduction",
}


def _sentences(text: str) -> list[str]:
    """Split text into sentences."""
    return [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]


def _words(text: str) -> list[str]:
    return [w for w in text.split() if w]


# ---------------------------------------------------------------------------
# C06 — Active voice
# ---------------------------------------------------------------------------

def _score_c06(result: CrawlResult) -> ScoreResult:
    text = result.body_text
    sentences = _sentences(text)
    if not sentences:
        return ScoreResult(
            id="C06", name="Active voice", dimension="Voice & Tone",
            score="FAIL", confidence="high",
            evidence="No prose sentences found on the page.",
            suggestion="Ensure the page has readable prose content.",
        )

    passive_sentences = []
    for s in sentences:
        if _PASSIVE_PATTERN.search(s):
            passive_sentences.append(s)

    ratio = len(passive_sentences) / len(sentences)

    if ratio < 0.15:
        score = "PASS"
    elif ratio < 0.30:
        score = "WARN"
    else:
        score = "FAIL"

    if passive_sentences:
        example = passive_sentences[0][:120]
        evidence = (
            f"{len(passive_sentences)} of {len(sentences)} sentences "
            f"contain passive constructions ({ratio:.0%}). "
            f"Example: \"{example}\""
        )
    else:
        evidence = f"0 of {len(sentences)} sentences contain passive constructions."

    return ScoreResult(
        id="C06", name="Active voice", dimension="Voice & Tone",
        score=score, confidence="high",
        evidence=evidence,
        suggestion=(
            "Rewrite passive constructions so the subject acts: "
            "'Configure the setting' not 'The setting should be configured'."
        ),
        detail={"passive_count": len(passive_sentences),
                "sentence_count": len(sentences),
                "passive_ratio": round(ratio, 3)},
    )


# ---------------------------------------------------------------------------
# C07 — Second person
# ---------------------------------------------------------------------------

def _score_c07(result: CrawlResult) -> ScoreResult:
    text = result.body_text.lower()

    you_count = len(re.findall(r'\byou\b|\byour\b|\byours\b|\byourself\b', text))
    third_count = len(re.findall(
        r'\bthe\s+(?:user|administrator|developer|operator|reader|customer)s?\b',
        text
    ))

    total = you_count + third_count
    if total == 0:
        return ScoreResult(
            id="C07", name="Second person", dimension="Voice & Tone",
            score="WARN", confidence="high",
            evidence="No second-person ('you/your') or third-person references found.",
            suggestion="Address the reader directly using 'you' and 'your'.",
        )

    ratio = you_count / total

    if ratio >= 0.60:
        score = "PASS"
    elif ratio >= 0.30:
        score = "WARN"
    else:
        score = "FAIL"

    evidence = (
        f"'you/your' appears {you_count} times; "
        f"third-person references appear {third_count} times "
        f"({ratio:.0%} second-person ratio)."
    )

    return ScoreResult(
        id="C07", name="Second person", dimension="Voice & Tone",
        score=score, confidence="high",
        evidence=evidence,
        suggestion=(
            "Replace 'the user should' with 'you should'. "
            "Address the reader directly throughout."
        ),
        detail={"you_count": you_count, "third_count": third_count,
                "you_ratio": round(ratio, 3)},
    )


# ---------------------------------------------------------------------------
# C08 — Imperative mood
# ---------------------------------------------------------------------------

def _score_c08(result: CrawlResult) -> ScoreResult:
    from bs4 import BeautifulSoup

    # Re-parse raw HTML to get list items (body_text loses structure)
    soup = BeautifulSoup(result.raw_html, "lxml")

    # Remove code blocks first
    for el in soup.find_all(["pre", "code", "kbd"]):
        el.decompose()

    list_items = []
    for tag in soup.find_all(["li"]):
        text = tag.get_text(separator=" ", strip=True)
        if text and len(text.split()) >= 2:
            list_items.append(text)

    if not list_items:
        return ScoreResult(
            id="C08", name="Imperative mood", dimension="Voice & Tone",
            score="WARN", confidence="high",
            evidence="No list items found on the page — cannot evaluate imperative mood.",
            suggestion="Use numbered steps or bullet lists for instructional content, starting each with an action verb.",
        )

    imperative_count = 0
    non_imperative = []
    for item in list_items:
        first_word = item.split()[0].lower().rstrip(".,:")
        if first_word in _IMPERATIVE_VERBS:
            imperative_count += 1
        else:
            non_imperative.append(item)

    ratio = imperative_count / len(list_items)

    if ratio >= 0.70:
        score = "PASS"
    elif ratio >= 0.40:
        score = "WARN"
    else:
        score = "FAIL"

    if non_imperative:
        example = non_imperative[0][:100]
        evidence = (
            f"{imperative_count} of {len(list_items)} list items start with "
            f"an action verb ({ratio:.0%}). "
            f"Non-imperative example: \"{example}\""
        )
    else:
        evidence = f"All {len(list_items)} list items start with an action verb."

    return ScoreResult(
        id="C08", name="Imperative mood", dimension="Voice & Tone",
        score=score, confidence="high",
        evidence=evidence,
        suggestion=(
            "Start numbered steps and list items with an action verb: "
            "'Click Save' not 'The Save button should be clicked'."
        ),
        detail={"imperative_count": imperative_count,
                "list_item_count": len(list_items),
                "imperative_ratio": round(ratio, 3)},
    )


# ---------------------------------------------------------------------------
# C09 — Internal cross-links
# ---------------------------------------------------------------------------

def _score_c09(result: CrawlResult) -> ScoreResult:
    internal = [l for l in result.links if l.is_internal]
    count = len(internal)

    if count >= 3:
        score = "PASS"
    elif count >= 1:
        score = "WARN"
    else:
        score = "FAIL"

    if internal:
        examples = ", ".join(f'"{l.text}"' for l in internal[:3])
        evidence = f"{count} internal link(s) found. Examples: {examples}."
    else:
        evidence = "No internal links found on this page."

    return ScoreResult(
        id="C09", name="Internal cross-links", dimension="Discoverability",
        score=score, confidence="high",
        evidence=evidence,
        suggestion=(
            "Add at least 3 links to related pages on the same domain "
            "to connect this page into the documentation graph."
        ),
        detail={"internal_link_count": count},
    )


# ---------------------------------------------------------------------------
# C10 — Related Topics section
# ---------------------------------------------------------------------------

def _score_c10(result: CrawlResult) -> ScoreResult:
    matched_heading = None
    for h in result.headings:
        if _RELATED_HEADING_PATTERNS.search(h.text):
            matched_heading = h.text
            break

    if matched_heading:
        score = "PASS"
        evidence = f"Found related-topics heading: \"{matched_heading}\"."
    else:
        score = "FAIL"
        heading_texts = [h.text for h in result.headings]
        evidence = (
            f"No related-topics heading found. "
            f"Page headings: {heading_texts}."
        )

    return ScoreResult(
        id="C10", name="Related Topics section", dimension="Discoverability",
        score=score, confidence="high",
        evidence=evidence,
        suggestion=(
            "Add a 'Related topics' or 'See also' section at the bottom "
            "of the page with links to adjacent content."
        ),
    )


# ---------------------------------------------------------------------------
# C11 — Task-oriented link text
# ---------------------------------------------------------------------------

def _score_c11(result: CrawlResult) -> ScoreResult:
    links = [l for l in result.links if l.text.strip()]
    if not links:
        return ScoreResult(
            id="C11", name="Task-oriented link text", dimension="Discoverability",
            score="WARN", confidence="high",
            evidence="No links with visible text found on this page.",
            suggestion="Use descriptive link text that tells readers what they will find.",
        )

    bad_links = []
    for l in links:
        text = l.text.strip()
        for pattern in _BAD_LINK_PATTERNS:
            if pattern.search(text):
                bad_links.append(text)
                break

    ratio = len(bad_links) / len(links)

    if ratio < 0.10:
        score = "PASS"
    elif ratio < 0.25:
        score = "WARN"
    else:
        score = "FAIL"

    if bad_links:
        examples = ", ".join(f'"{t}"' for t in bad_links[:3])
        evidence = (
            f"{len(bad_links)} of {len(links)} links have poor anchor text "
            f"({ratio:.0%}). Examples: {examples}."
        )
    else:
        evidence = f"All {len(links)} links have descriptive anchor text."

    return ScoreResult(
        id="C11", name="Task-oriented link text", dimension="Discoverability",
        score=score, confidence="high",
        evidence=evidence,
        suggestion=(
            "Replace generic link text ('click here', bare URLs) with "
            "descriptive text that tells the reader what they'll find."
        ),
        detail={"bad_link_count": len(bad_links), "total_links": len(links),
                "bad_ratio": round(ratio, 3)},
    )


# ---------------------------------------------------------------------------
# C14 — Consistent capitalisation
# ---------------------------------------------------------------------------

def _classify_heading_case(text: str) -> str:
    """
    Return 'title', 'sentence', or 'other' for a heading string.
    Title case: most words capitalised.
    Sentence case: only first word (and proper nouns) capitalised.
    """
    words = text.split()
    if not words:
        return "other"

    # Strip punctuation for analysis
    clean_words = [re.sub(r'[^a-zA-Z]', '', w) for w in words]
    alpha_words = [w for w in clean_words if w]
    if not alpha_words:
        return "other"

    cap_count = sum(1 for w in alpha_words if w and w[0].isupper())
    cap_ratio = cap_count / len(alpha_words)

    if cap_ratio >= 0.70:
        return "title"
    elif alpha_words[0][0].isupper() and cap_ratio <= 0.35:
        return "sentence"
    else:
        return "other"


def _score_c14(result: CrawlResult) -> ScoreResult:
    # Focus on H2–H4 (H1 is usually the page title, different rules)
    headings = [h for h in result.headings if 2 <= h.level <= 4]

    if len(headings) < 2:
        return ScoreResult(
            id="C14", name="Consistent capitalisation", dimension="Style Governance",
            score="WARN", confidence="high",
            evidence=f"Only {len(headings)} H2–H4 heading(s) found — not enough to assess consistency.",
            suggestion="Add more subheadings and ensure they use a consistent capitalisation style.",
        )

    styles = [_classify_heading_case(h.text) for h in headings]
    from collections import Counter
    counts = Counter(styles)
    dominant_style, dominant_count = counts.most_common(1)[0]
    consistency = dominant_count / len(headings)

    if consistency >= 0.85:
        score = "PASS"
    elif consistency >= 0.65:
        score = "WARN"
    else:
        score = "FAIL"

    outliers = [
        headings[i].text for i, s in enumerate(styles)
        if s != dominant_style
    ]

    if outliers:
        examples = "; ".join(f'"{t}"' for t in outliers[:3])
        evidence = (
            f"Dominant style is {dominant_style} case "
            f"({dominant_count}/{len(headings)} headings). "
            f"Inconsistent headings: {examples}."
        )
    else:
        evidence = (
            f"All {len(headings)} H2–H4 headings use {dominant_style} case consistently."
        )

    return ScoreResult(
        id="C14", name="Consistent capitalisation", dimension="Style Governance",
        score=score, confidence="high",
        evidence=evidence,
        suggestion=(
            "Standardise heading capitalisation — pick either Title Case or "
            "Sentence case and apply it to all H2–H4 headings."
        ),
        detail={"dominant_style": dominant_style, "consistency": round(consistency, 3),
                "heading_count": len(headings)},
    )


# ---------------------------------------------------------------------------
# C15 — Acronym expansion
# ---------------------------------------------------------------------------

def _score_c15(result: CrawlResult) -> ScoreResult:
    text = result.body_text

    # Find all acronyms in the text
    all_acronyms = _ACRONYM.findall(text)
    unique_acronyms = set(all_acronyms) - _NOT_ACRONYMS

    # Check which ones are expanded: look for "ACRONYM (expansion)" or
    # "expansion (ACRONYM)" patterns
    unexpanded = []
    for acronym in sorted(unique_acronyms):
        # Pattern: preceded or followed by parenthetical expansion
        expansion_pattern = re.compile(
            rf'\b{re.escape(acronym)}\s*\([^)]+\)'   # ACRONYM (expansion)
            rf'|[^(]+\({re.escape(acronym)}\)',        # expansion (ACRONYM)
            re.IGNORECASE
        )
        if not expansion_pattern.search(text):
            unexpanded.append(acronym)

    count = len(unexpanded)

    if count == 0:
        score = "PASS"
    elif count <= 2:
        score = "WARN"
    else:
        score = "FAIL"

    if unexpanded:
        examples = ", ".join(unexpanded[:5])
        evidence = (
            f"{count} acronym(s) used without expansion on first use: {examples}."
        )
    else:
        if unique_acronyms:
            evidence = (
                f"All {len(unique_acronyms)} acronym(s) found are either "
                f"exempt or expanded on first use."
            )
        else:
            evidence = "No unexpanded acronyms found on this page."

    return ScoreResult(
        id="C15", name="Acronym expansion", dimension="Style Governance",
        score=score, confidence="high",
        evidence=evidence,
        suggestion=(
            "Expand acronyms on first use: write "
            "'Role-Based Access Control (RBAC)' before using RBAC alone."
        ),
        detail={"unexpanded_count": count, "unexpanded": unexpanded},
    )


# ---------------------------------------------------------------------------
# C20 — Descriptive page title
# ---------------------------------------------------------------------------

def _score_c20(result: CrawlResult) -> ScoreResult:
    title = result.title.strip()

    if not title:
        return ScoreResult(
            id="C20", name="Descriptive page title", dimension="Search Effectiveness",
            score="FAIL", confidence="high",
            evidence="No <title> tag found.",
            suggestion="Add a descriptive <title> of 30–65 characters including the primary topic keyword.",
        )

    # Strip site name suffix (e.g. "Page Title | Site Name")
    core_title = re.split(r'\s*[\|–—]\s*', title)[0].strip()

    length = len(core_title)
    lower = core_title.lower()

    is_generic = lower in _GENERIC_TITLE_WORDS or len(lower.split()) <= 1

    if is_generic:
        score = "FAIL"
        evidence = f"Title is too generic: \"{core_title}\"."
    elif 30 <= length <= 65:
        score = "PASS"
        evidence = f"Title is {length} characters: \"{core_title}\"."
    else:
        score = "WARN"
        if length < 30:
            evidence = f"Title is short ({length} chars): \"{core_title}\". Aim for 30–65."
        else:
            evidence = f"Title is long ({length} chars): \"{core_title}\". Aim for 30–65."

    return ScoreResult(
        id="C20", name="Descriptive page title", dimension="Search Effectiveness",
        score=score, confidence="high",
        evidence=evidence,
        suggestion=(
            "Write a descriptive <title> of 30–65 characters "
            "that includes the primary topic keyword."
        ),
        detail={"title_length": length, "core_title": core_title},
    )


# ---------------------------------------------------------------------------
# C21 — Heading density
# ---------------------------------------------------------------------------

def _score_c21(result: CrawlResult) -> ScoreResult:
    # H2–H4 only (H1 is the page title)
    heading_count = sum(1 for h in result.headings if 2 <= h.level <= 4)
    word_count = result.word_count

    if word_count == 0:
        return ScoreResult(
            id="C21", name="Heading density", dimension="Search Effectiveness",
            score="FAIL", confidence="high",
            evidence="No prose text found on the page.",
            suggestion="Ensure the page has readable prose content with subheadings.",
        )

    if heading_count == 0:
        return ScoreResult(
            id="C21", name="Heading density", dimension="Search Effectiveness",
            score="FAIL", confidence="high",
            evidence=f"No H2–H4 headings found. Page has {word_count} words with no subheadings.",
            suggestion="Add subheadings (H2–H4) to break up the content — aim for one per 150–400 words.",
        )

    words_per_heading = word_count / heading_count

    if 150 <= words_per_heading <= 400:
        score = "PASS"
    elif 100 <= words_per_heading < 150 or 400 < words_per_heading <= 600:
        score = "WARN"
    else:
        score = "FAIL"

    evidence = (
        f"{heading_count} H2–H4 heading(s) for {word_count} words "
        f"= {words_per_heading:.0f} words per heading."
    )

    if words_per_heading < 100:
        evidence += " Headings are too dense — sections are very short."
    elif words_per_heading > 600:
        evidence += " Sections are too long between headings."

    return ScoreResult(
        id="C21", name="Heading density", dimension="Search Effectiveness",
        score=score, confidence="high",
        evidence=evidence,
        suggestion=(
            "Aim for one H2–H4 heading per 150–400 words. "
            "Add headings to break up long sections or merge thin ones."
        ),
        detail={"heading_count": heading_count, "word_count": word_count,
                "words_per_heading": round(words_per_heading, 1)},
    )


# ---------------------------------------------------------------------------
# C22 — Meta description present
# ---------------------------------------------------------------------------

def _score_c22(result: CrawlResult) -> ScoreResult:
    meta = result.meta_description.strip()

    if not meta:
        score = "FAIL"
        evidence = "No <meta name='description'> tag found."
    else:
        length = len(meta)
        if 50 <= length <= 160:
            score = "PASS"
            evidence = f"Meta description is {length} characters: \"{meta[:80]}{'...' if length > 80 else ''}\"."
        elif length < 50:
            score = "WARN"
            evidence = f"Meta description is too short ({length} chars): \"{meta}\"."
        else:
            score = "WARN"
            evidence = f"Meta description is too long ({length} chars) — search engines will truncate it."

    return ScoreResult(
        id="C22", name="Meta description present", dimension="SEO Compliance",
        score=score, confidence="high",
        evidence=evidence,
        suggestion=(
            "Add a <meta name='description'> tag with a "
            "50–160 character summary of the page's purpose."
        ),
        detail={"meta_length": len(meta) if meta else 0},
    )


# ---------------------------------------------------------------------------
# C23 — Canonical URL
# ---------------------------------------------------------------------------

def _score_c23(result: CrawlResult) -> ScoreResult:
    canonical = result.canonical_url.strip()

    if canonical:
        score = "PASS"
        evidence = f"Canonical URL declared: \"{canonical}\"."
    else:
        score = "FAIL"
        evidence = "No <link rel='canonical'> tag found in <head>."

    return ScoreResult(
        id="C23", name="Canonical URL", dimension="SEO Compliance",
        score=score, confidence="high",
        evidence=evidence,
        suggestion=(
            "Add <link rel='canonical' href='...'> to the <head> "
            "to declare the preferred URL for this page."
        ),
    )


# ---------------------------------------------------------------------------
# C24 — No third-person self-reference
# ---------------------------------------------------------------------------

def _score_c24(result: CrawlResult) -> ScoreResult:
    matches = _THIRD_PERSON_INSTRUCTION.findall(result.body_text)
    # findall returns list of tuples (role, verb) — flatten to count
    count = len(matches)

    # Also get the actual matching strings for evidence
    match_strings = _THIRD_PERSON_INSTRUCTION.findall(result.body_text)
    raw_matches = _THIRD_PERSON_INSTRUCTION.finditer(result.body_text)
    examples = [m.group(0) for m in raw_matches]

    if count == 0:
        score = "PASS"
        evidence = "No third-person self-references found in instructional text."
    elif count <= 2:
        score = "WARN"
        evidence = (
            f"{count} third-person instruction(s) found. "
            f"Example: \"{examples[0]}\"."
        )
    else:
        score = "FAIL"
        ex = "; ".join(f'"{e}"' for e in examples[:3])
        evidence = f"{count} third-person instructions found: {ex}."

    return ScoreResult(
        id="C24", name="No third-person self-reference", dimension="Second Person Usage",
        score=score, confidence="high",
        evidence=evidence,
        suggestion=(
            "Replace 'the user should configure' with 'you should configure'. "
            "Use second person for all instructions."
        ),
        detail={"count": count, "examples": examples[:5]},
    )


# ---------------------------------------------------------------------------
# C25 — No passive instructions
# ---------------------------------------------------------------------------

def _score_c25(result: CrawlResult) -> ScoreResult:
    raw_matches = list(_PASSIVE_INSTRUCTION.finditer(result.body_text))
    count = len(raw_matches)
    examples = [m.group(0) for m in raw_matches]

    if count == 0:
        score = "PASS"
        evidence = "No passive instructional constructions found."
    elif count <= 2:
        score = "WARN"
        evidence = (
            f"{count} passive instruction(s) found. "
            f"Example: \"{examples[0]}\"."
        )
    else:
        score = "FAIL"
        ex = "; ".join(f'"{e}"' for e in examples[:3])
        evidence = f"{count} passive instructions found: {ex}."

    return ScoreResult(
        id="C25", name="No passive instructions", dimension="Second Person Usage",
        score=score, confidence="high",
        evidence=evidence,
        suggestion=(
            "Rewrite passive instructions actively: "
            "'Configure the timeout' not 'The timeout should be configured'."
        ),
        detail={"count": count, "examples": examples[:5]},
    )


# ---------------------------------------------------------------------------
# C26 — Direct address consistency
# ---------------------------------------------------------------------------

def _score_c26(result: CrawlResult) -> ScoreResult:
    text = result.body_text.lower()

    you_count = len(re.findall(r'\byou\b|\byour\b', text))
    third_count = len(re.findall(
        r'\bthe\s+(?:user|administrator|developer|operator|reader|customer)s?\b',
        text
    ))

    total = you_count + third_count
    if total == 0:
        return ScoreResult(
            id="C26", name="Direct address consistency", dimension="Second Person Usage",
            score="WARN", confidence="high",
            evidence="No address-style markers found — page may be purely conceptual.",
            suggestion="Use a consistent address style throughout instructional content.",
        )

    you_ratio = you_count / total
    third_ratio = third_count / total

    # Determine dominant and minority
    if you_ratio >= third_ratio:
        dominant = "second person"
        minor_count = third_count
    else:
        dominant = "third person"
        minor_count = you_count

    if minor_count == 0:
        score = "PASS"
        evidence = (
            f"Consistent {dominant} address style throughout "
            f"(you/your: {you_count}, third-person refs: {third_count})."
        )
    elif minor_count <= 2:
        score = "WARN"
        evidence = (
            f"Mostly {dominant} style, but {minor_count} instance(s) of the "
            f"other style found (you/your: {you_count}, third-person refs: {third_count})."
        )
    else:
        score = "FAIL"
        evidence = (
            f"Mixed address style: {you_count} second-person and "
            f"{third_count} third-person references. Pick one and apply consistently."
        )

    return ScoreResult(
        id="C26", name="Direct address consistency", dimension="Second Person Usage",
        score=score, confidence="high",
        evidence=evidence,
        suggestion=(
            "Pick one address style and apply it throughout. "
            "Prefer second person ('you') for instructional content."
        ),
        detail={"you_count": you_count, "third_count": third_count,
                "dominant_style": dominant, "minor_count": minor_count},
    )


# ---------------------------------------------------------------------------
# Top-level scorer
# ---------------------------------------------------------------------------

_CHECKS = [
    _score_c06, _score_c07, _score_c08,
    _score_c09, _score_c10, _score_c11,
    _score_c14, _score_c15,
    _score_c20, _score_c21,
    _score_c22, _score_c23,
    _score_c24, _score_c25, _score_c26,
]


def score(result: CrawlResult) -> list[ScoreResult]:
    """Run all 15 checks and return results in criteria order."""
    return [check(result) for check in _CHECKS]


# ---------------------------------------------------------------------------
# CLI smoke test  (python scorer.py <url>)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scorer.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    print(f"Crawling: {url}\n")

    crawl_result = crawl(url)

    if crawl_result.warnings:
        for w in crawl_result.warnings:
            print(f"⚠  {w}")
        print()

    results = score(crawl_result)

    pass_count = sum(1 for r in results if r.score == "PASS")
    warn_count = sum(1 for r in results if r.score == "WARN")
    fail_count = sum(1 for r in results if r.score == "FAIL")

    print(f"{'ID':<6} {'Score':<6} {'Criterion':<35} Evidence")
    print("-" * 100)
    for r in results:
        icon = {"PASS": "✓", "WARN": "~", "FAIL": "✗"}[r.score]
        print(f"{r.id:<6} {icon} {r.score:<4} {r.name:<35} {r.evidence[:60]}")

    print()
    print(f"Summary: {pass_count} PASS  {warn_count} WARN  {fail_count} FAIL  "
          f"(out of {len(results)} criteria)")
