# Launch Runbook — projecthood.org

The play-by-play for cutting over from Squarespace to the GitHub Pages build. Follow top-to-bottom on launch day. Owner: Brian.

---

## Pre-flight (complete at least 72 hours before cutover)

### Content + QA
- [ ] Every page reviewed and signed off by section owners (see `SITEMAP.md` for owners)
- [ ] All image placeholders filled (no dashed-box gaps left on any page)
- [ ] Footer address, phone, and email verified against current sources of truth
- [ ] All external links clicked and land on the right page (Tiltify, NetworkForGood, Apricot, Google Forms, Google Calendar, social)
- [ ] Preview banner + `noindex` meta **removed** from all pages — edit `_build.py` HEAD template, then `python3 _build.py`, commit, push
- [ ] `404.html` tested (visit a made-up URL like `/xyz123.html` and confirm it renders)

### Accounts + access
- [ ] Access to Squarespace admin confirmed (for shutting the old site down / pointing DNS)
- [ ] Access to DNS registrar confirmed (where projecthood.org is registered — likely Google Domains / Squires / GoDaddy)
- [ ] GitHub repo `projecthood-site/projecthood` is still set to **Deploy from branch: main / root**
- [ ] NetworkForGood, Tiltify, Apricot, Google Workspace accounts all still active — verify by logging in

### Analytics + measurement
- [ ] Google Analytics 4 property created (or existing one identified)
- [ ] GA4 Measurement ID copied
- [ ] GA4 snippet added to `_build.py` HEAD template, pages rebuilt, pushed
- [ ] Test event visible in GA4 real-time report when visiting preview URL

### SEO
- [ ] Google Search Console property created for `projecthood.org` (verify via DNS TXT record or GA linkage)
- [ ] `sitemap.xml` generated and uploaded to repo root (I'll write this when we're closer)
- [ ] `robots.txt` updated to allow all + link to sitemap

### Accessibility audit
- [ ] Every page passes axe DevTools scan (Chrome extension) at the AA level
- [ ] Every image has meaningful `alt` text (not filenames)
- [ ] Color contrast checked on color-tile sections (the green/red/blue tiles — dark text on light, light text on dark)
- [ ] Keyboard-only navigation tested: Tab through the header, land on every link, hit Enter to navigate

---

## Cutover day

### Step 1 — Final push (T-1 hour)
- [ ] Merge any last-minute content edits to `main`
- [ ] Confirm GitHub Pages has rebuilt (green checkmark in Settings → Pages)
- [ ] Load https://projecthood-site.github.io/projecthood/ and click through all 15 pages one more time

### Step 2 — Configure custom domain in GitHub Pages (T-30 min)
- [ ] Repo → Settings → Pages → Custom domain: enter `projecthood.org`
- [ ] Click Save — GitHub will add a `CNAME` file to the repo
- [ ] Leave **Enforce HTTPS** unchecked for now (we'll turn it on after DNS propagates)

### Step 3 — DNS cutover (T-0)
At your DNS registrar, update the records for `projecthood.org`:

| Type  | Name | Value |
|-------|------|-------|
| A     | @    | 185.199.108.153 |
| A     | @    | 185.199.109.153 |
| A     | @    | 185.199.110.153 |
| A     | @    | 185.199.111.153 |
| CNAME | www  | projecthood-site.github.io. |

Remove or disable any existing A records pointing to Squarespace.

- [ ] Save DNS changes
- [ ] Note the timestamp — DNS propagation typically 15 min to 2 hours, up to 48 hours in rare cases

### Step 4 — Wait for DNS + turn on HTTPS
- [ ] Check https://projecthood.org every 15 min until it loads the new site (not Squarespace)
- [ ] Once new site is live: repo → Settings → Pages → check **Enforce HTTPS**
- [ ] Wait another ~10 min for GitHub to provision the Let's Encrypt cert
- [ ] Confirm https://projecthood.org loads with a valid padlock (no warning)

### Step 5 — Shut down Squarespace
- [ ] Log into Squarespace → downgrade or cancel the site subscription (after confirming new site is fully live for ≥24 hours)
- [ ] Export Squarespace content as a final backup before canceling

### Step 6 — Smoke test
Clicked from a browser you've never used before (to avoid cached old site):
- [ ] Home loads, nav works
- [ ] Donate button opens NetworkForGood
- [ ] Walk Across America button opens Tiltify
- [ ] Volunteer form loads (Google Form)
- [ ] Events page shows current events (confirm no stale past-date events; if Google Calendar embed was implemented, confirm it loads)
- [ ] Contact form submits successfully (check Google Sheet)

---

## Post-launch (first 7 days)

- [ ] Submit sitemap to Google Search Console
- [ ] Monitor GA4 for traffic drops vs. Squarespace baseline (expect some; big drops = broken link somewhere)
- [ ] Check Google Search Console for crawl errors daily
- [ ] Social share check: paste `https://projecthood.org` into Slack, Facebook, LinkedIn — confirm preview card shows logo + title + description
- [ ] Announce the new site (email list + social)

---

## Redirect map (Squarespace → new)

Squarespace used different URL slugs. If any of these old URLs are bookmarked, shared, or indexed, they need to forward to the right page on the new site. Because GitHub Pages doesn't natively do server-side redirects, we handle this with a tiny JavaScript redirect on `404.html`.

| Old Squarespace URL | New URL |
|---|---|
| `/about-us` | `/about.html` |
| `/our-programs` | `/programs.html` |
| `/violence-prevention` | `/program.html` |
| `/the-leo-center` | `/leo-center.html` |
| `/walk-across-america` | `/campaigns.html` |
| `/get-involved-1` | `/get-involved.html` |
| `/donate-now` | `/donate.html` |
| `/volunteer-1` | `/volunteer.html` |
| `/events-1` | `/events.html` |
| `/partner-with-us` | `/partner.html` |
| `/news-1` | `/news.html` |
| `/contact-us` | `/contact.html` |

**Action:** pull the real Squarespace URL list before cutover (Squarespace admin → Analytics → Traffic → All Sources → Top Pages). Replace the guesses above with actual URLs. I'll wire the redirects into `404.html` once we have the list.

---

## Rollback plan

If something catastrophic happens (site down, DNS misconfigured, etc.):

1. Revert DNS A records to the Squarespace pointers (have the old values copied somewhere **before** you change anything in Step 3)
2. Squarespace site comes back online within 15 min to 2 hours (same DNS propagation window)
3. Re-test on the new setup in the preview URL before retrying cutover

Keep the Squarespace subscription active for **at least 7 days** after launch as insurance.

---

## Contacts for launch day

- **GitHub / site build** — Brian
- **DNS registrar** — *⚠️ Brian: fill in who owns the domain registration (GoDaddy / Google Domains / other) and confirm you have login access*
- **NetworkForGood account** — *⚠️ Brian: fill in the admin login contact*
- **Tiltify account** — *⚠️ Brian: fill in the admin login contact*
- **Google Workspace admin** — *⚠️ Brian: fill in who can create/modify Google Forms and the shared calendar*

> **Action needed:** Update the four lines above before launch day. You need to be able to reach each service owner within 30 minutes on cutover day in case something needs to be rolled back or reconfigured.
