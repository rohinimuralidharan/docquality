# Documentation Quality Report

**URL:** https://docs.example.com/auth/getting-started  
**Evaluated:** 2024-01-15 09:30 UTC  
**Word count:** 53  
**Fetch time:** 38ms  

## Overall Grade: C

9 passed · 4 warnings · 2 failed (out of 15 criteria)

## 🎯 Quick Wins

Fix these first — each is a clear, actionable finding:

- **C14 Consistent capitalisation:** Standardise heading capitalisation — pick either Title Case or Sentence case and apply it to all H2–H4 headings.
- **C21 Heading density:** Aim for one H2–H4 heading per 150–400 words. Add headings to break up long sections or merge thin ones.

## Results by Dimension

| Dimension | ✅ Pass | ⚠️ Warn | ❌ Fail | Status |
|-----------|--------|--------|--------|--------|
| Voice & Tone | 2 | 1 | 0 | ⚠️ |
| Discoverability | 3 | 0 | 0 | ✅ |
| Style Governance | 0 | 1 | 1 | ❌ |
| Search Effectiveness | 1 | 0 | 1 | ❌ |
| SEO Compliance | 2 | 0 | 0 | ✅ |
| Second Person Usage | 1 | 2 | 0 | ⚠️ |

## Full Findings

_Criteria are listed in order. Evidence is taken directly from the page — no interpretation._

### Voice & Tone

### ✅ C06 — Active voice
**Dimension:** Voice & Tone  
**Score:** PASS  
**Confidence:** high

**Evidence:** 0 of 5 sentences contain passive constructions.

**Suggestion:** Rewrite passive constructions so the subject acts: 'Configure the setting' not 'The setting should be configured'.

---

### ✅ C07 — Second person
**Dimension:** Voice & Tone  
**Score:** PASS  
**Confidence:** high

**Evidence:** 'you/your' appears 2 times; third-person references appear 1 times (67% second-person ratio).

**Suggestion:** Replace 'the user should' with 'you should'. Address the reader directly throughout.

---

### ⚠️ C08 — Imperative mood
**Dimension:** Voice & Tone  
**Score:** WARN  
**Confidence:** high

**Evidence:** 2 of 4 list items start with an action verb (50%). Non-imperative example: "OAuth flow reference"

**Suggestion:** Start numbered steps and list items with an action verb: 'Click Save' not 'The Save button should be clicked'.

---

### Discoverability

### ✅ C09 — Internal cross-links
**Dimension:** Discoverability  
**Score:** PASS  
**Confidence:** high

**Evidence:** 3 internal link(s) found. Examples: "API Keys page", "OAuth flow reference", "Available scopes".

**Suggestion:** Add at least 3 links to related pages on the same domain to connect this page into the documentation graph.

---

### ✅ C10 — Related Topics section
**Dimension:** Discoverability  
**Score:** PASS  
**Confidence:** high

**Evidence:** Found related-topics heading: "See also".

**Suggestion:** Add a 'Related topics' or 'See also' section at the bottom of the page with links to adjacent content.

---

### ✅ C11 — Task-oriented link text
**Dimension:** Discoverability  
**Score:** PASS  
**Confidence:** high

**Evidence:** All 3 links have descriptive anchor text.

**Suggestion:** Replace generic link text ('click here', bare URLs) with descriptive text that tells the reader what they'll find.

---

### Style Governance

### ❌ C14 — Consistent capitalisation
**Dimension:** Style Governance  
**Score:** FAIL  
**Confidence:** high

**Evidence:** Dominant style is sentence case (1/3 headings). Inconsistent headings: "Option 1: API Key Authentication"; "See also".

**Suggestion:** Standardise heading capitalisation — pick either Title Case or Sentence case and apply it to all H2–H4 headings.

---

### ⚠️ C15 — Acronym expansion
**Dimension:** Style Governance  
**Score:** WARN  
**Confidence:** high

**Evidence:** 1 acronym(s) used without expansion on first use: ADMIN.

**Suggestion:** Expand acronyms on first use: write 'Role-Based Access Control (RBAC)' before using RBAC alone.

---

### Search Effectiveness

### ✅ C20 — Descriptive page title
**Dimension:** Search Effectiveness  
**Score:** PASS  
**Confidence:** high

**Evidence:** Title is 35 characters: "Getting Started with Authentication".

**Suggestion:** Write a descriptive <title> of 30–65 characters that includes the primary topic keyword.

---

### ❌ C21 — Heading density
**Dimension:** Search Effectiveness  
**Score:** FAIL  
**Confidence:** high

**Evidence:** 3 H2–H4 heading(s) for 53 words = 18 words per heading. Headings are too dense — sections are very short.

**Suggestion:** Aim for one H2–H4 heading per 150–400 words. Add headings to break up long sections or merge thin ones.

---

### SEO Compliance

### ✅ C22 — Meta description present
**Dimension:** SEO Compliance  
**Score:** PASS  
**Confidence:** high

**Evidence:** Meta description is 55 characters: "Learn how to authenticate using OAuth 2.0 and API keys.".

**Suggestion:** Add a <meta name='description'> tag with a 50–160 character summary of the page's purpose.

---

### ✅ C23 — Canonical URL
**Dimension:** SEO Compliance  
**Score:** PASS  
**Confidence:** high

**Evidence:** Canonical URL declared: "https://docs.example.com/auth/getting-started".

**Suggestion:** Add <link rel='canonical' href='...'> to the <head> to declare the preferred URL for this page.

---

### Second Person Usage

### ⚠️ C24 — No third-person self-reference
**Dimension:** Second Person Usage  
**Score:** WARN  
**Confidence:** high

**Evidence:** 1 third-person instruction(s) found. Example: "The user should".

**Suggestion:** Replace 'the user should configure' with 'you should configure'. Use second person for all instructions.

---

### ✅ C25 — No passive instructions
**Dimension:** Second Person Usage  
**Score:** PASS  
**Confidence:** high

**Evidence:** No passive instructional constructions found.

**Suggestion:** Rewrite passive instructions actively: 'Configure the timeout' not 'The timeout should be configured'.

---

### ⚠️ C26 — Direct address consistency
**Dimension:** Second Person Usage  
**Score:** WARN  
**Confidence:** high

**Evidence:** Mostly second person style, but 1 instance(s) of the other style found (you/your: 2, third-person refs: 1).

**Suggestion:** Pick one address style and apply it throughout. Prefer second person ('you') for instructional content.

---

---

_Generated by [docquality](https://github.com/docquality/docquality) · Phase 1 heuristic scoring · No LLM, no API cost_