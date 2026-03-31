"""
crawler.py — fetch a documentation URL and return a clean content bundle.

Responsibilities:
  - Fetch the page with a sensible timeout and user-agent
  - Strip navigation, footer, sidebar, cookie banners, and other page chrome
  - Extract the main content block (platform-aware heuristics)
  - Return a CrawlResult dataclass with both raw HTML signals and clean text

Platform handling:
  MkDocs, Docusaurus, Sphinx, GitBook, ReadTheDocs, and plain HTML are all
  handled via a priority list of main-content selectors. The first selector
  that matches and contains a meaningful word count wins. If none match, the
  tool falls back to <main> then <body> with chrome stripped.

Known limitation:
  JavaScript-rendered pages (some Docusaurus v2/v3 sites, Notion exports) may
  return thin HTML before JS hydration. The tool cannot execute JavaScript.
  If word_count < 100 the CrawlResult carries a low_content warning.
"""

import re
import sys
import time
import requests
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup, Comment


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REQUEST_TIMEOUT = 15  # seconds
MIN_WORD_COUNT = 100  # below this triggers low_content warning

USER_AGENT = (
    "Mozilla/5.0 (compatible; docquality/1.0; "
    "+https://github.com/docquality/docquality)"
)

# Selectors tried in order to find the main content block.
# First selector that yields >= MIN_WORD_COUNT words wins.
MAIN_CONTENT_SELECTORS = [
    # MkDocs Material — article body only, not the full md-content wrapper
    # which includes the sidebar table of contents
    "article.md-content__inner",
    "div.md-content__inner",
    "div.md-content",
    # Docusaurus
    "article.theme-doc-markdown",
    "div.theme-doc-markdown",
    "main .container .row article",
    # ReadTheDocs / Sphinx
    "div.document",
    "div[role='main']",
    "div.body",
    # GitBook
    "div.page-inner",
    "section.normal",
    # Generic fallbacks
    "main",
    "article",
    '[role="main"]',
    "#content",
    "#main-content",
    ".content",
    ".main-content",
    ".documentation",
    ".docs-content",
]

# After selecting the main content block, strip these selectors from within it.
# Material for MkDocs places in-page nav and other chrome inside the article.
CONTENT_INNER_STRIP_SELECTORS = [
    # Material for MkDocs — in-page table of contents nav
    "nav.md-nav",
    "nav.md-nav--secondary",
    ".md-nav",
    # Material for MkDocs — edit/source links, tags, feedback
    ".md-content__button",
    ".md-source-file",
    ".md-tags",
    # Docusaurus — pagination links at bottom
    ".pagination-nav",
    ".theme-doc-footer",
    # General — any remaining nav elements inside content
    "nav",
    # Lists that are purely navigation (aria-label signals)
    "[aria-label='Table of contents']",
    "[aria-label='breadcrumb']",
]

# Tags whose entire subtree should be removed before text extraction.
STRIP_TAGS = [
    "nav", "header", "footer", "aside",
    "script", "style", "noscript",
    # Common class/id patterns for chrome
]

# CSS selectors for chrome elements to remove.
STRIP_SELECTORS = [
    # Navigation and sidebars
    "[class*='sidebar']",
    "[class*='nav']",
    "[class*='menu']",
    "[id*='sidebar']",
    "[id*='nav']",
    # Headers and footers
    "[class*='header']",
    "[class*='footer']",
    "[id*='header']",
    "[id*='footer']",
    # Banners and overlays
    "[class*='banner']",
    "[class*='cookie']",
    "[class*='toast']",
    "[class*='announcement']",
    "[class*='feedback']",
    # Table of contents (we detect headings from the actual content)
    "[class*='toc']",
    "[class*='table-of-contents']",
    "[id*='toc']",
    # Breadcrumbs
    "[class*='breadcrumb']",
    # Edit/GitHub links
    "[class*='edit-page']",
    "[class*='github-link']",
    # Search
    "[class*='search']",
    "[id*='search']",
]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CodeBlock:
    """Represents a code block extracted from the page."""
    text: str
    tag: str  # 'code', 'pre', or 'kbd'


@dataclass
class Heading:
    """A heading element with its level and text."""
    level: int   # 1–6
    text: str


@dataclass
class Link:
    """An anchor tag with href and link text."""
    href: str
    text: str
    is_internal: bool


@dataclass
class CrawlResult:
    """
    Everything downstream modules need. Produced by crawl().

    Fields
    ------
    url             : final URL after any redirects
    domain          : netloc of the URL (used for internal link detection)
    title           : text content of <title> tag, or empty string
    meta_description: content of <meta name="description">, or empty string
    canonical_url   : href of <link rel="canonical">, or empty string
    headings        : ordered list of Heading objects (H1–H6)
    links           : all <a> tags found in the main content block
    body_text       : clean prose text, code blocks removed
    code_blocks     : list of CodeBlock objects (excluded from voice checks)
    word_count      : word count of body_text
    raw_html        : full page HTML (for any checks that need it)
    warnings        : list of warning strings (e.g. low_content, js_rendered)
    fetch_duration_ms: time taken to fetch the page
    """
    url: str
    domain: str
    title: str
    meta_description: str
    canonical_url: str
    headings: list = field(default_factory=list)
    links: list = field(default_factory=list)
    body_text: str = ""
    code_blocks: list = field(default_factory=list)
    word_count: int = 0
    raw_html: str = ""
    cleaned_html: str = ""   # serialised content block after all chrome stripping
    warnings: list = field(default_factory=list)
    fetch_duration_ms: int = 0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _fetch(url: str) -> tuple[str, str]:
    """
    Fetch URL, follow redirects, return (final_url, html).
    Raises requests.RequestException on network failure.
    """
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.url, resp.text


def _remove_comments(soup: BeautifulSoup) -> None:
    """Strip HTML comments in-place."""
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()


def _strip_chrome(soup: BeautifulSoup) -> None:
    """Remove navigation, footer, sidebar, and other page chrome in-place."""
    # Remove by tag name
    for tag in STRIP_TAGS:
        for el in soup.find_all(tag):
            el.decompose()

    # Remove by CSS selector
    for selector in STRIP_SELECTORS:
        for el in soup.select(selector):
            el.decompose()


def _extract_code_blocks(soup: BeautifulSoup) -> list[CodeBlock]:
    """
    Extract and REMOVE all code blocks from soup in-place.
    Returns list of CodeBlock so scorer can inspect them separately.
    Code blocks must be removed before body_text extraction so they don't
    pollute voice/person heuristics.
    """
    blocks = []
    for el in soup.find_all(["pre", "code", "kbd"]):
        text = el.get_text(separator=" ", strip=True)
        if text:
            blocks.append(CodeBlock(text=text, tag=el.name))
        el.decompose()
    return blocks


def _find_main_content(soup: BeautifulSoup) -> BeautifulSoup:
    """
    Return the subtree that best represents the main content.
    Tries platform-specific selectors first, falls back to <body>.
    """
    for selector in MAIN_CONTENT_SELECTORS:
        el = soup.select_one(selector)
        if el:
            words = len(el.get_text(separator=" ", strip=True).split())
            if words >= MIN_WORD_COUNT:
                return el

    # Last resort: return whatever is left in body
    return soup.find("body") or soup


def _strip_content_chrome(content: BeautifulSoup) -> None:
    """
    Second-pass chrome removal inside the selected content block.

    Some platforms (Material for MkDocs, Docusaurus) embed navigation,
    table-of-contents, and feedback widgets *inside* the main article element.
    These survive the first _strip_chrome pass because they're inside the
    content selector match. This pass removes them from the content block
    before text extraction and list-item analysis.
    """
    for selector in CONTENT_INNER_STRIP_SELECTORS:
        for el in content.select(selector):
            el.decompose()


def _extract_headings(content: BeautifulSoup) -> list[Heading]:
    """Return all H1–H6 elements in document order."""
    headings = []
    for tag in content.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        level = int(tag.name[1])
        text = tag.get_text(separator=" ", strip=True)
        if text:
            headings.append(Heading(level=level, text=text))
    return headings


def _extract_links(content: BeautifulSoup, domain: str, base_url: str) -> list[Link]:
    """Return all <a href> elements with internal/external classification."""
    links = []
    for tag in content.find_all("a", href=True):
        href = tag["href"].strip()
        text = tag.get_text(separator=" ", strip=True)

        # Resolve relative URLs for domain comparison
        if href.startswith("#"):
            # Anchor-only link — skip (same-page navigation, not cross-links)
            continue
        if href.startswith("mailto:") or href.startswith("tel:"):
            continue

        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        is_internal = parsed.netloc == domain or parsed.netloc == ""

        links.append(Link(href=absolute, text=text, is_internal=is_internal))
    return links


def _extract_meta(soup: BeautifulSoup) -> tuple[str, str, str]:
    """Return (title, meta_description, canonical_url)."""
    title = ""
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)

    meta_description = ""
    meta_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    if meta_tag and meta_tag.get("content"):
        meta_description = meta_tag["content"].strip()

    canonical_url = ""
    canonical_tag = soup.find("link", attrs={"rel": re.compile(r"^canonical$", re.I)})
    if canonical_tag and canonical_tag.get("href"):
        canonical_url = canonical_tag["href"].strip()

    return title, meta_description, canonical_url


def _clean_body_text(content: BeautifulSoup) -> str:
    """
    Extract prose text from the content block.
    Code blocks have already been removed by _extract_code_blocks().
    Collapse whitespace and return a single string.
    """
    text = content.get_text(separator=" ", strip=True)
    # Collapse runs of whitespace / newlines
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def crawl(url: str) -> CrawlResult:
    """
    Fetch url and return a CrawlResult.

    Raises
    ------
    requests.RequestException  — network or HTTP error
    ValueError                 — URL does not look fetchable
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"URL must start with http:// or https:// — got: {url!r}")

    t0 = time.monotonic()
    final_url, html = _fetch(url)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    domain = urlparse(final_url).netloc
    soup = BeautifulSoup(html, "lxml")

    # --- Extract head-level signals before any stripping ---
    title, meta_description, canonical_url = _extract_meta(soup)

    # --- Clean the tree ---
    _remove_comments(soup)
    _strip_chrome(soup)

    # --- Find main content block ---
    content = _find_main_content(soup)

    # --- Second-pass: strip nav/chrome embedded inside the content block ---
    # (Material for MkDocs, Docusaurus embed in-page TOC nav inside the article)
    _strip_content_chrome(content)

    # --- Extract headings and links before code removal ---
    headings = _extract_headings(content)
    links = _extract_links(content, domain, final_url)

    # --- Remove code blocks (mutates content) ---
    code_blocks = _extract_code_blocks(content)

    # --- Serialise cleaned content for use by scorer (e.g. C08 list items) ---
    cleaned_html = str(content)

    # --- Extract clean prose text ---
    body_text = _clean_body_text(content)
    word_count = len(body_text.split()) if body_text else 0

    # --- Warnings ---
    warnings = []
    if word_count < MIN_WORD_COUNT:
        warnings.append(
            f"low_content: only {word_count} words extracted. "
            "Page may be JavaScript-rendered or content selector missed the main block."
        )

    return CrawlResult(
        url=final_url,
        domain=domain,
        title=title,
        meta_description=meta_description,
        canonical_url=canonical_url,
        headings=headings,
        links=links,
        body_text=body_text,
        code_blocks=code_blocks,
        word_count=word_count,
        raw_html=html,
        cleaned_html=cleaned_html,
        warnings=warnings,
        fetch_duration_ms=fetch_ms,
    )


# ---------------------------------------------------------------------------
# CLI smoke test  (python crawler.py <url>)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python crawler.py <url>")
        sys.exit(1)

    target = sys.argv[1]
    print(f"Fetching: {target}\n")

    try:
        result = crawl(target)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"Final URL       : {result.url}")
    print(f"Domain          : {result.domain}")
    print(f"Fetch time      : {result.fetch_duration_ms}ms")
    print(f"Title           : {result.title!r}")
    print(f"Meta description: {result.meta_description!r}")
    print(f"Canonical URL   : {result.canonical_url!r}")
    print(f"Word count      : {result.word_count}")
    print(f"Headings        : {len(result.headings)}")
    print(f"Links           : {len(result.links)} total, "
          f"{sum(1 for l in result.links if l.is_internal)} internal")
    print(f"Code blocks     : {len(result.code_blocks)}")
    print()

    if result.warnings:
        print("WARNINGS:")
        for w in result.warnings:
            print(f"  ⚠  {w}")
        print()

    print("── Headings ──")
    for h in result.headings:
        indent = "  " * (h.level - 1)
        print(f"  {indent}H{h.level}: {h.text}")

    print()
    print("── Body text preview (first 400 chars) ──")
    print(f"  {result.body_text[:400]}...")
