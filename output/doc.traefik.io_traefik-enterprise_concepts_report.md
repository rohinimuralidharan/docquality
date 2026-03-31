# Documentation Quality Report

**URL:** https://doc.traefik.io/traefik-enterprise/concepts/  
**Evaluated:** 2026-03-30 18:44 UTC  
**Word count:** 1039  
**Fetch time:** 323ms  

## Overall Grade: D

9 passed · 2 warnings · 4 failed (out of 15 criteria)

## 🎯 Quick Wins

Fix these first — each is a clear, actionable finding:

- **C08 Imperative mood:** Start numbered steps and list items with an action verb: 'Click Save' not 'The Save button should be clicked'.
- **C10 Related Topics section:** Add a 'Related topics' or 'See also' section at the bottom of the page with links to adjacent content.
- **C21 Heading density:** Aim for one H2–H4 heading per 150–400 words. Add headings to break up long sections or merge thin ones.
- **C23 Canonical URL:** Add <link rel='canonical' href='...'> to the <head> to declare the preferred URL for this page.

## Results by Dimension

| Dimension | ✅ Pass | ⚠️ Warn | ❌ Fail | Status |
|-----------|--------|--------|--------|--------|
| Voice & Tone | 2 | 0 | 1 | ❌ |
| Discoverability | 2 | 0 | 1 | ❌ |
| Style Governance | 1 | 1 | 0 | ⚠️ |
| Search Effectiveness | 1 | 0 | 1 | ❌ |
| SEO Compliance | 1 | 0 | 1 | ❌ |
| Second Person Usage | 2 | 1 | 0 | ⚠️ |

## Full Findings

_Criteria are listed in order. Evidence is taken directly from the page — no interpretation._

### Voice & Tone

### ✅ C06 — Active voice
**Dimension:** Voice & Tone  
**Score:** PASS  
**Confidence:** high

**Evidence:** 8 of 61 sentences contain passive constructions (13%). Example: "Traefik Enterprise's service mesh is based on the Kubernetes concept of a DaemonSet , which ensures that a service mesh "

**Suggestion:** Rewrite passive constructions so the subject acts: 'Configure the setting' not 'The setting should be configured'.

---

### ✅ C07 — Second person
**Dimension:** Voice & Tone  
**Score:** PASS  
**Confidence:** high

**Evidence:** 'you/your' appears 21 times; third-person references appear 0 times (100% second-person ratio).

**Suggestion:** Replace 'the user should' with 'you should'. Address the reader directly throughout.

---

### ❌ C08 — Imperative mood
**Dimension:** Voice & Tone  
**Score:** FAIL  
**Confidence:** high

**Evidence:** 2 of 105 list items start with an action verb (2%). Non-imperative example: "Getting Started"

**Suggestion:** Start numbered steps and list items with an action verb: 'Click Save' not 'The Save button should be clicked'.

---

### Discoverability

### ✅ C09 — Internal cross-links
**Dimension:** Discoverability  
**Score:** PASS  
**Confidence:** high

**Evidence:** 12 internal link(s) found. Examples: "introduction", "dynamic configuration", "circuit breaker pattern".

**Suggestion:** Add at least 3 links to related pages on the same domain to connect this page into the documentation graph.

---

### ❌ C10 — Related Topics section
**Dimension:** Discoverability  
**Score:** FAIL  
**Confidence:** high

**Evidence:** No related-topics heading found. Page headings: ['Concepts', 'Architecture Overview', 'Cluster and Nodes', 'Nodes in the Data Plane', 'Nodes in the Control Plane', 'Service Mesh', 'High Availability', 'HA in the Data Plane', 'HA in the Control Plane', 'Common Questions', 'How Many Nodes Do You Need in the Control Plane?', 'What Happens if the Control Plane is Unhealthy?', 'Scalability', 'Security'].

**Suggestion:** Add a 'Related topics' or 'See also' section at the bottom of the page with links to adjacent content.

---

### ✅ C11 — Task-oriented link text
**Dimension:** Discoverability  
**Score:** PASS  
**Confidence:** high

**Evidence:** All 19 links have descriptive anchor text.

**Suggestion:** Replace generic link text ('click here', bare URLs) with descriptive text that tells the reader what they'll find.

---

### Style Governance

### ✅ C14 — Consistent capitalisation
**Dimension:** Style Governance  
**Score:** PASS  
**Confidence:** high

**Evidence:** Dominant style is title case (12/13 headings). Inconsistent headings: "What Happens if the Control Plane is Unhealthy?".

**Suggestion:** Standardise heading capitalisation — pick either Title Case or Sentence case and apply it to all H2–H4 headings.

---

### ⚠️ C15 — Acronym expansion
**Dimension:** Style Governance  
**Score:** WARN  
**Confidence:** high

**Evidence:** 1 acronym(s) used without expansion on first use: HA.

**Suggestion:** Expand acronyms on first use: write 'Role-Based Access Control (RBAC)' before using RBAC alone.

---

### Search Effectiveness

### ✅ C20 — Descriptive page title
**Dimension:** Search Effectiveness  
**Score:** PASS  
**Confidence:** high

**Evidence:** Title is 61 characters: "Traefik Enterprise Architecture Concepts - Traefik Enterprise".

**Suggestion:** Write a descriptive <title> of 30–65 characters that includes the primary topic keyword.

---

### ❌ C21 — Heading density
**Dimension:** Search Effectiveness  
**Score:** FAIL  
**Confidence:** high

**Evidence:** 13 H2–H4 heading(s) for 1039 words = 80 words per heading. Headings are too dense — sections are very short.

**Suggestion:** Aim for one H2–H4 heading per 150–400 words. Add headings to break up long sections or merge thin ones.

---

### SEO Compliance

### ✅ C22 — Meta description present
**Dimension:** SEO Compliance  
**Score:** PASS  
**Confidence:** high

**Evidence:** Meta description is 156 characters: "Traefik Enterprise's architecture consists of nodes spread into two different pl...".

**Suggestion:** Add a <meta name='description'> tag with a 50–160 character summary of the page's purpose.

---

### ❌ C23 — Canonical URL
**Dimension:** SEO Compliance  
**Score:** FAIL  
**Confidence:** high

**Evidence:** No <link rel='canonical'> tag found in <head>.

**Suggestion:** Add <link rel='canonical' href='...'> to the <head> to declare the preferred URL for this page.

---

### Second Person Usage

### ✅ C24 — No third-person self-reference
**Dimension:** Second Person Usage  
**Score:** PASS  
**Confidence:** high

**Evidence:** No third-person self-references found in instructional text.

**Suggestion:** Replace 'the user should configure' with 'you should configure'. Use second person for all instructions.

---

### ⚠️ C25 — No passive instructions
**Dimension:** Second Person Usage  
**Score:** WARN  
**Confidence:** high

**Evidence:** 1 passive instruction(s) found. Example: "must be recovered".

**Suggestion:** Rewrite passive instructions actively: 'Configure the timeout' not 'The timeout should be configured'.

---

### ✅ C26 — Direct address consistency
**Dimension:** Second Person Usage  
**Score:** PASS  
**Confidence:** high

**Evidence:** Consistent second person address style throughout (you/your: 20, third-person refs: 0).

**Suggestion:** Pick one address style and apply it throughout. Prefer second person ('you') for instructional content.

---

---

_Generated by [docquality](https://github.com/docquality/docquality) · Phase 1 heuristic scoring · No LLM, no API cost_