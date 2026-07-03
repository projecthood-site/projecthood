# Sitemap & Page Intent

One row per page. Use this for QA, content ownership, and onboarding new staff. Owner = who signs off on content for that page.

Live preview: https://projecthood-site.github.io/projecthood/
Production (pending cutover): https://projecthood.org

---

## Pages

### Home — `index.html`
- **Purpose:** Introduce Project H.O.O.D. to a first-time visitor in 15 seconds and move them toward donate, volunteer, or learn-more.
- **Audience:** Donors, prospective volunteers, press, neighbors hearing about PH for the first time.
- **Primary CTA:** Donate (secondary: Get Involved)
- **Integrations:** NetworkForGood (donate button), newsletter embed (footer)
- **Photo slots:** Hero photo (large, wide); 3–4 program tiles; one impact/story image
- **Owner:** Communications / Executive Director
- **Update cadence:** Impact numbers updated annually (or after each program cycle); hero messaging reviewed each quarter

### About — `about.html`
- **Purpose:** Tell the PH story, mission, values, team, and history.
- **Audience:** Donors doing due diligence, press, potential board members, partners.
- **Primary CTA:** Partner with us / Donate
- **Integrations:** None on-page
- **Photo slots:** Hero/mission image; team headshots (one per person); optional archival/history images
- **Owner:** Executive Director / Communications
- **Update cadence:** Team page updated when staff join or depart; history/mission reviewed annually

### Programs (hub) — `programs.html`
- **Purpose:** List and describe all programs at a glance.
- **Audience:** Prospective participants, funders evaluating program portfolio, referral partners.
- **Primary CTA:** Learn more about a specific program / Apply
- **Integrations:** Apricot (program intake, linked from individual program pages)
- **Photo slots:** One photo per program card
- **Owner:** Program Director (overview page)
- **Update cadence:** When programs are added, renamed, or descriptions change

### Program Detail (Violence Prevention template) — `program.html`
- **Purpose:** Deep dive on one program: what it is, who it serves, outcomes, how to join.
- **Audience:** Prospective participants, funders, referral partners.
- **Primary CTA:** Apply (Apricot) / Refer someone
- **Integrations:** Apricot intake form
- **Photo slots:** Hero; 2–3 program-in-action shots; staff portrait
- **Owner:** Program Director (per program)
- **Update cadence:** When application status changes (open/closed/waitlist), outcomes data refreshes, or staff contact changes
- **Note:** This page is the Violence Prevention template. Clone it for workforce, mental health, etc. — each gets its own program director as owner.

### Impact — `impact.html`
- **Purpose:** Show outcomes: numbers, stories, proof that the mission is working.
- **Audience:** Donors (especially foundation/corporate), board, press.
- **Primary CTA:** Donate / Download impact report
- **Integrations:** None on-page (optional: embed annual report PDF link)
- **Photo slots:** Hero; stat-card backgrounds; 2–3 participant story photos (**permission required** before any participant photo goes public)
- **Owner:** Development Director / Evaluation Lead
- **Update cadence:** Annually after program year closes; participant stories only with signed photo/story release on file

### LEO Center — `leo-center.html`
- **Purpose:** Promote the LEO Center capital campaign — what it is, why it matters, how to give.
- **Audience:** Major donors, corporate prospects, foundations, community.
- **Primary CTA:** Give to LEO Center (NetworkForGood designated fund)
- **Integrations:** NetworkForGood (designated fund)
- **Photo slots:** Hero/rendering; construction progress photos; architectural drawings
- **Owner:** Capital Campaign Lead / Development Director
- **Update cadence:** Funding progress bar and milestone updates as campaign hits thresholds; photos updated as construction progresses

### Campaigns (WAA) — `campaigns.html`
- **Purpose:** Promote Walk Across America and any other time-bound campaigns.
- **Audience:** Existing supporters, press, peer-to-peer fundraisers.
- **Primary CTA:** Join WAA (Tiltify)
- **Integrations:** Tiltify (WAA peer-to-peer fundraising platform)
- **Photo slots:** Hero action shot from prior WAA; route map; participant photos
- **Owner:** Events / Communications
- **Update cadence:** When campaign dates, fundraising totals, or WAA story content change

### Get Involved — `get-involved.html`
- **Purpose:** Top-of-funnel page for anyone who wants to help. Routes to Donate, Volunteer, Partner.
- **Audience:** Anyone motivated to act but unsure how.
- **Primary CTA:** Three equal CTAs: Donate, Volunteer, Partner
- **Integrations:** Links out to donate.html, volunteer.html, partner.html
- **Photo slots:** Hero; one photo per CTA tile
- **Owner:** Development Director
- **Update cadence:** Low — only if the routing strategy changes

### Donate — `donate.html`
- **Purpose:** Convert a motivated donor to a completed gift.
- **Audience:** Warm donors.
- **Primary CTA:** Make a gift (NetworkForGood)
- **Integrations:** NetworkForGood (primary donate platform)
- **Photo slots:** One trust-building photo (program in action); optional impact tile images
- **Owner:** Development Director
- **Update cadence:** Gift impact amounts reviewed annually; WAA section updated each campaign cycle
- **Note:** Per project standards, all giving routes through NetworkForGood — do not propose on-site donation forms.

### Volunteer — `volunteer.html`
- **Purpose:** Capture volunteer interest and route to onboarding.
- **Audience:** Community members, students, corporate volunteer groups.
- **Primary CTA:** Volunteer signup (Google Form → Google Sheet)
- **Integrations:** Google Forms (volunteer intake)
- **Photo slots:** Volunteers in action; group shots
- **Owner:** Program Director / Volunteer Coordinator
- **Update cadence:** When volunteer opportunities or requirements change

### Events — `events.html`
- **Purpose:** Show upcoming PH events so people can RSVP or attend.
- **Audience:** Supporters, community, partners.
- **Primary CTA:** RSVP (Google Form) / Add to calendar
- **Integrations:** Google Forms (RSVPs per event); events are currently **manually maintained HTML** — not yet auto-synced from Google Calendar (see QA_FINDINGS.md §3 for options)
- **Photo slots:** Hero; featured event photo
- **Owner:** Events / Communications
- **Update cadence:** As events are added or removed; stale past events should be cleared monthly
- **⚠️ Pre-launch action:** Decide on Calendar embed vs. manual HTML, update stale placeholder events

### Partner — `partner.html`
- **Purpose:** Attract corporate, faith-based, and institutional partners; route to a conversation.
- **Audience:** Corporate CSR leads, faith communities, institutional partners.
- **Primary CTA:** Partner inquiry form (Google Form)
- **Integrations:** Google Forms (partner inquiries)
- **Photo slots:** Hero; logos of existing partners; one photo of a partnership in action
- **Owner:** Development Director
- **Update cadence:** When partner tiers, benefits, or existing partner logos change

### News — `news.html`
- **Purpose:** Press hits, announcements, and PH-authored updates.
- **Audience:** Press, board, donors, anyone checking "is this org active?"
- **Primary CTA:** Read / Share
- **Integrations:** None
- **Photo slots:** One image per post
- **Owner:** Communications
- **Update cadence:** As news is published; aim for at least one post per month to show active presence

### Contact — `contact.html`
- **Purpose:** Provide office address, phone, email, and a general contact form.
- **Audience:** Anyone who needs to reach PH for anything not covered by another page.
- **Primary CTA:** Submit contact form (Google Form) / Email / Call
- **Integrations:** Google Forms (contact inquiries)
- **Photo slots:** Office exterior; Woodlawn neighborhood image
- **Owner:** Executive Director / Operations
- **Update cadence:** When address, phone, or primary contact email changes

### Jobs — `jobs.html`
- **Purpose:** Announce open positions and attract community-embedded candidates.
- **Audience:** Job seekers, Woodlawn residents, nonprofit sector talent.
- **Primary CTA:** Apply (Google Form per role)
- **Integrations:** Google Forms (one per open role — see CONTENT_UPDATES.md for process)
- **Photo slots:** None (copy and card-based layout)
- **Owner:** Executive Director / HR
- **Update cadence:** As roles open and close; the "No open positions" placeholder shows by default when nothing is posted

### 404 — `404.html`
- **Purpose:** Catch broken/mistyped URLs and route the visitor back to a useful page.
- **Audience:** Anyone who landed on a dead link.
- **Primary CTA:** Back to Home / Contact us
- **Integrations:** None on-page; redirect JS for legacy Squarespace URLs (see [LAUNCH_RUNBOOK.md](LAUNCH_RUNBOOK.md))
- **Photo slots:** Optional one friendly brand image
- **Owner:** Brian (technical page)

---

## Integrations master reference

| Service | Used on | Owner | What it does |
|---|---|---|---|
| NetworkForGood | donate, home, leo-center, get-involved | Development Director | Donation processing, recurring gifts, LEO Center designated fund, newsletter |
| Tiltify | campaigns | Events / Communications | Walk Across America peer-to-peer fundraising |
| Apricot | programs, program | Program Director | Program applicant intake + case management |
| Google Forms | volunteer, contact, partner, event RSVPs | Varies by form | Inbound forms → single shared Google Sheet |
| Google Calendar | events | Events / Communications | ⚠️ **NOT YET CONNECTED** — events.html currently uses manually maintained HTML. Decide pre-launch: Option A = embed calendar iframe (recommended, free), Option B = leave manual and update docs. See QA_FINDINGS.md §3. |
| Google Analytics 4 | site-wide | Brian | Traffic, conversions, referrers |
| Google Search Console | site-wide | Brian | Search performance, indexing errors |

---

## Photo permission notes

- Any identifiable photo of a **program participant** (especially minors) needs written photo release on file before it goes on the public site
- Staff/team photos: verbal OK is fine, but give each person a preview and an easy "take it down" path
- Stock photos are acceptable as placeholder but should be swapped for authentic PH photography within 90 days of launch

---

## Related docs
- [README.md](README.md) — Repo overview
- [CONTENT_UPDATES.md](CONTENT_UPDATES.md) — How to update content after launch
- [LAUNCH_RUNBOOK.md](LAUNCH_RUNBOOK.md) — Cutover procedure
- [TEAM_REVIEW.md](TEAM_REVIEW.md) — QA instructions for the current review pass
