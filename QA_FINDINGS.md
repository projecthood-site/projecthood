# QA Findings — projecthood.org Preview
**Date:** June 19, 2026  
**Preview URL:** https://projecthood-site.github.io/projecthood/  
**Reviewed by:** Claude (automated + visual check)

---

## ✅ What's working

- All 15 pages load and render correctly
- Nav active state highlights the right item on every page
- Logo, fonts, brand colors all consistent throughout
- 404 page triggers correctly and shows recovery links
- Footer renders correctly on all pages
- Mobile nav toggle is wired
- External link safety (noopener, target=_blank) applied automatically
- NetworkForGood donate URL is correct: `projecthood.networkforgood.com`
- Tiltify WAA URL is correct: `tiltify.com/project-hood/walk-across-america-2025`
- No broken internal page links
- No TODO/FILL_IN placeholder text found in page content
- Preview banner visible (correctly set to be removed before launch)

---

## 🔴 Blocking — must fix before launch

These will cause visible broken behavior on the live site.

### ~~1. Social media links~~ — ✅ RESOLVED (June 19, 2026)
Real URLs wired in via `_build.py`, all 15 pages rebuilt:
- Instagram: https://www.instagram.com/projecthood1/
- Facebook: https://www.facebook.com/ProjectHood1/
- LinkedIn: https://www.linkedin.com/company/project-h-o-o-d
- YouTube: https://www.youtube.com/@projecthood8919

### ~~2. Google Form buttons~~ — ✅ RESOLVED (June 19, 2026)
All three forms created via Apps Script and wired in. All responses go to one Sheet:
- Volunteer: https://docs.google.com/forms/d/e/1FAIpQLSfulIcBaCRzjDaNXuMuV-fgo_LxqOoXNQG8FU7ibIOuI_6-FA/viewform
- Partner: https://docs.google.com/forms/d/e/1FAIpQLSeSqdS_4Cyd4gdWyvAuJEGF3zR4MFqKsiOPDDRUKUsBMEDNKQ/viewform
- Contact: https://docs.google.com/forms/d/e/1FAIpQLSezt7dj_hycF7Y45m-Dcls6-52SCGS2sd-NkMDogWDhh_dIkQ/viewform
- Response sheet: https://docs.google.com/spreadsheets/d/1I1-no7HpP6892JSYTLCODzsnKNtljyFCvcCyj5jkirs/edit

### ~~3. Events page — NOT pulling from Google Calendar~~ — ✅ RESOLVED (June 19, 2026)
Google Calendar iframe embedded (AGENDA mode, live). Hardcoded stale events removed. Subscribe links wired:
- `.ics / Apple Calendar`: public basic.ics URL
- `+ Add to Google Calendar`: direct subscribe link
- Calendar ID: `c_aaab49ab274191a67fd34d3ec23430823e39f8a684eb5358c53ccfc765269ec6@group.calendar.google.com`

### ~~4. Events RSVP link~~ — ✅ RESOLVED (June 19, 2026)
Back to School Giveaway RSVP wired to volunteer form (temporary). Swap for a dedicated RSVP form before the event if needed.

---

## 🟡 Important — fix before launch if possible

### 5. About page — Pastor Brooks letter and booking
- "Read Pastor Brooks' letter" → `href="#"`
- "Book Pastor Brooks" → `href="#"`

These could link to a PDF, a Google Doc, a Calendly link, or an email address.

### 6. About page — 990s and Annual Report — ⚠️ PARTIAL (June 19, 2026)
- ✅ **2024 Form 990** — `docs/ph-990-2024.pdf` (39 pages, ProPublica source, confirmed tax year 2024)
- ❌ **2023 Form 990** — still `href="#"` · Brian to provide PDF
- ❌ **2024 Annual Report** — still `href="#"` · Brian to provide PDF
- ❌ **Audited financials** — still `href="#"` · Brian to provide PDF

**To add a new PDF:** drop it in `site/projecthood/docs/`, update the `href` in `_build.py` → `about_body`, run `python3 _build.py`, commit + push.

### ~~7. Footer Privacy and Financials links~~ — ✅ RESOLVED (June 19, 2026)
- Privacy → `privacy.html` (new page created with full policy)
- Financials & 990s → `about.html` (stewardship/990s section)

### 8. Newsletter subscribe not connected
Footer "Subscribe" button is placeholder copy. Needs the actual NetworkForGood newsletter embed code pasted in.

---

## 🔵 Known / expected — no action needed before launch

- **Photo placeholders (dashed boxes)** — documented in TEAM_REVIEW.md, expected
- **Preview banner** — per LAUNCH_RUNBOOK.md, removed by editing `_build.py` pre-launch
- **`noindex` meta tag** — auto-removed same step as preview banner
- **Staff "how to post an event" box** on events page — copy says it's removed before launch
- **Programs "About X" links all go to same program.html** — known, additional program pages are a post-launch task per README

---

## Summary: What Brian needs to provide

| Item | Who provides | Urgency |
|---|---|---|
| Social media profile URLs (IG, FB, LinkedIn, YT) | Brian / comms | 🔴 Before launch |
| Google Form URL — Volunteer signup | Brian / volunteer coord | 🔴 Before launch |
| Google Form URL — Partner inquiry | Brian / development | 🔴 Before launch |
| Google Form URL — Contact | Brian / ops | 🔴 Before launch |
| Events page decision (Calendar embed vs manual) | Brian | 🔴 Before launch |
| Google Calendar .ics URL (for subscribe link) | Brian | 🔴 Before launch |
| RSVP form URL for Back to School Giveaway | Brian / events | 🔴 Before launch |
| Pastor Brooks letter (PDF or link) | Brian / comms | 🟡 Nice to have |
| Booking link for Pastor Brooks | Brian | 🟡 Nice to have |
| Form 990 PDFs (2023, 2024) | Brian / finance | 🟡 Nice to have |
| Annual Report PDF | Brian / comms | 🟡 Nice to have |
| Privacy policy text | Brian | 🟡 Nice to have |
| NetworkForGood newsletter embed code | Brian / development | 🟡 Nice to have |
| Photos for all placeholder slots | Brian / comms | 🟡 Nice to have |
