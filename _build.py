#!/usr/bin/env python3
"""
Project H.O.O.D. site generator.

To rebuild manually: python3 _build.py
Automated rebuilds: GitHub Actions runs this daily at 6 AM CT,
pulling live events from the Eventbrite API automatically.

Output: all .html pages written to the same directory as this script.

Eventbrite auto-update:
  Set the EVENTBRITE_TOKEN environment variable (or GitHub secret) to a
  private token from eventbrite.com → Account Settings → Developer Links → API Keys.
  When present, the events page renders live events from your Eventbrite
  organizer profile (ID 41178041593) instead of the hardcoded cards.
"""
from pathlib import Path
import re
import os
import json
try:
    import urllib.request as urlreq
    import urllib.error as urlerr
except ImportError:
    urlreq = None

# ---------------------------------------------------------------------------
# Eventbrite live event fetcher
# ---------------------------------------------------------------------------
# Organization ID for the Eventbrite API (from GET /v3/users/me/organizations/).
# NOTE: this is NOT the "41178041593" number in the public /o/ URL — that is the
# organizer-profile ID and the API's events endpoint rejects it. Use the org ID.
EVENTBRITE_ORG_ID = "798710286253"
EVENTBRITE_ORG_URL = "https://www.eventbrite.com/o/project-hood-41178041593"

# Newsletter signup Google Form (created via createNewsletterFormOnly() in create_ph_forms.gs).
# Responses land on the "Newsletter" tab of the Site Form Responses workbook.
NEWSLETTER_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSel7-YfFSxXgX-L6xExCCyMU45e8URnxAxrS-PFTes2TkLbrA/viewform"

# Construction Pre-Apprenticeship cohort application Google Form.
# Paste the PUBLISHED form URL ending in /viewform (the page embeds it in an
# iframe so applicants apply without leaving the site). Leave "" to show the
# fallback "reach out" box until the real link is ready.
CONSTRUCTION_COHORT_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSea3eRxuKg9dUfXfoIUb7trGRFJkLsLCfxKs6UNTGIIttQv3Q/viewform"

def _eb_fetch_events(time_filter="current_future", order="start_asc", status="live", limit=None):
    """
    Fetch events from the Eventbrite API for the organization.
    time_filter: "current_future" (upcoming) or "past".
    status: "live" for upcoming (hides drafts); None for past (returns completed).
    Returns a list of dicts with keys: title, date_str, location, url, image, is_free
    Returns None if token is missing or request fails.
    """
    token = os.environ.get("EVENTBRITE_TOKEN", "").strip()
    if not token:
        return None
    try:
        url = (
            f"https://www.eventbriteapi.com/v3/organizations/{EVENTBRITE_ORG_ID}/events/"
            f"?order_by={order}&expand=venue,logo&time_filter={time_filter}"
        )
        if status:
            url += f"&status={status}"
        req = urlreq.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urlreq.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        events = []
        for ev in data.get("events", []):
            start = ev.get("start", {})
            # Format date string e.g. "Sat, Jun 28 · 10:00 AM"
            from datetime import datetime, timezone
            try:
                dt = datetime.fromisoformat(start.get("local", ""))
                day_str = dt.strftime("%a, %b %-d · %-I:%M %p")
            except Exception:
                day_str = start.get("local", "")
            venue = ev.get("venue") or {}
            location = venue.get("name") or venue.get("address", {}).get("city") or "Woodlawn"
            # Event flyer image (falls back to a colored tile if none)
            logo = ev.get("logo") or {}
            image = ""
            if logo:
                image = (logo.get("original") or {}).get("url") or logo.get("url") or ""
            events.append({
                "title": ev.get("name", {}).get("text", "Untitled Event"),
                "date_str": day_str,
                "location": location,
                "url": ev.get("url", EVENTBRITE_ORG_URL),
                "image": image,
                "is_free": bool(ev.get("is_free", False)),
            })
        if limit:
            events = events[:limit]
        return events if events else None
    except Exception as exc:
        print(f"  [Eventbrite] Could not fetch events: {exc}")
        return None

# BG colors cycle for event cards
_EB_COLORS = ["var(--green)", "var(--blue)", "var(--red)", "var(--purple)", "var(--yellow)"]

# RSVP link overrides: event title (case-insensitive substring) -> replacement URL.
# Use when registration must go somewhere other than the Eventbrite listing —
# e.g. a Google Form that collects details required by an outside agency.
# Applies to both the RSVP button and the Share link for the matching event.
_RSVP_OVERRIDES = {
    "secretary of state dmv community service day":
        "https://docs.google.com/forms/d/e/1FAIpQLSepWJiAXLjX5fHqnX5VqV3lW4tAFHE79s6OHXJULhcDHn5HZw/viewform",
    "trunk party":
        "https://docs.google.com/forms/d/e/1FAIpQLScuY1qVREYg8wENDx7PyMUhlBkkHOGzRh0CepZsOmPSVlyL2w/viewform",
}

def _build_event_cards_html(events, is_past=False):
    """Render a grid of event cards from a list of event dicts."""
    cards = []
    for i, ev in enumerate(events):
        color = _EB_COLORS[i % len(_EB_COLORS)]
        safe_title = ev["title"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        safe_loc   = ev["location"].replace("&", "&amp;")
        url = ev["url"]
        _title_lc = ev["title"].lower()
        for _key, _repl in _RSVP_OVERRIDES.items():
            if _key in _title_lc:
                url = _repl
                break
        # Media: real Eventbrite flyer if available, else a branded colored tile
        if ev.get("image"):
            img_style = "width:100%;height:240px;object-fit:cover;display:block;"
            if is_past:
                img_style += "filter:grayscale(35%);opacity:.9;"
            media = (f'<img src="{ev["image"]}" alt="{safe_title} flyer" loading="lazy" '
                     f'style="{img_style}">')
        else:
            media = (f'<div class="img-ph" style="min-height:240px;background:{color};display:flex;'
                     f'align-items:center;justify-content:center;text-align:center;padding:20px;'
                     f'color:var(--white);font-family:var(--font-display);text-transform:uppercase;'
                     f'letter-spacing:.06em;font-size:14px;line-height:1.3;">{safe_title}</div>')
        loc_line = f'{safe_loc} · Free' if ev.get("is_free") else safe_loc
        if is_past:
            action = (f'<a class="btn btn-outline" href="{url}" target="_blank" rel="noopener" '
                      f'style="font-size:13px;padding:8px 16px;">View details →</a>')
        else:
            action = (f'<a class="btn btn-primary" href="{url}" target="_blank" rel="noopener" '
                      f'style="font-size:13px;padding:8px 16px;">RSVP →</a>')
        cards.append(f"""
      <div class="card" style="padding:0;overflow:hidden;">
        {media}
        <div style="padding:14px 18px 16px;">
          <div style="font-size:11px;font-weight:700;color:var(--red);text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px;">{ev["date_str"]}</div>
          <div style="font-size:17px;font-weight:800;color:var(--dark);font-family:var(--font-display);line-height:1.2;margin-bottom:3px;">{safe_title}</div>
          <div style="font-size:13px;color:var(--muted);margin-bottom:12px;">{loc_line}</div>
          <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
            {action}
            <button class="ph-share-btn" data-title="{safe_title}" data-url="{url}" style="background:transparent;border:1px solid var(--line);border-radius:6px;padding:7px 14px;font-size:13px;cursor:pointer;font-family:var(--font-body);color:var(--ink);">Share</button>
          </div>
        </div>
      </div>""")
    return "\n".join(cards)

# Try fetching live events now; fall back to hardcoded cards if unavailable
_live_events = _eb_fetch_events(time_filter="current_future", order="start_asc", status="live")
if _live_events:
    print(f"  [Eventbrite] Loaded {len(_live_events)} upcoming events from API ✓")
    _event_cards_html = _build_event_cards_html(_live_events)
else:
    print("  [Eventbrite] No token — using hardcoded event cards")
    _event_cards_html = None   # filled in below with the hardcoded block

# Past events (most recent first, capped) — powers the "Past events" tab
_past_events = _eb_fetch_events(time_filter="past", order="start_desc", status=None, limit=6)
if _past_events:
    print(f"  [Eventbrite] Loaded {len(_past_events)} past events from API ✓")
    _past_cards_html = _build_event_cards_html(_past_events, is_past=True)
else:
    _past_cards_html = None   # filled in below with a fallback message

SITE_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# Shared template pieces
# ---------------------------------------------------------------------------

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="robots" content="index,follow">
  <title>{title} · Project H.O.O.D.</title>
  <meta name="description" content="{meta}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;600;700&family=Zilla+Slab:ital,wght@0,400;0,500;0,700;1,400&family=Montserrat:wght@400;700;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="css/styles.css">
  <link rel="icon" href="img/social-icon.jpg">
  <meta property="og:title" content="{title} · Project H.O.O.D.">
  <meta property="og:description" content="{meta}">
  <meta property="og:image" content="img/social-icon.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <!-- Google Analytics 4 -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-NFBL61B4BN"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-NFBL61B4BN');
  </script>
</head>
<body>

<a class="skip-link" href="#main">Skip to main content</a>

<header class="site-header">
  <div class="nav">
    <a class="nav-logo" href="index.html">
      <img src="img/logo-red.png" alt="Project H.O.O.D. stamp logo">
      <span class="wordmark">Project H.O.O.D.<small>Helping Others Obtain Destiny</small></span>
    </a>
    <button class="nav-toggle" aria-label="Toggle menu" aria-expanded="false"><span></span><span></span><span></span></button>
    <nav class="nav-links" aria-label="Primary">
      <a href="programs.html"{a_programs}>Programs</a>
      <a href="events.html"{a_events}>Community Calendar</a>
      <a href="leo-center.html"{a_leo}>LEO Center</a>
      <a href="impact.html"{a_impact}>News &amp; Impact</a>
      <a href="get-help.html" class="get-help">Get Help</a>
      <a href="ways-to-give.html"{a_ways}>Ways to Give</a>
      <a href="https://projecthood.networkforgood.com/" class="donate">Donate</a>
    </nav>
  </div>
</header>

<main id="main">
"""

FOOTER = f"""
</main>

<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <img src="img/logo-knockout-offwhite.png" alt="Project H.O.O.D." style="height:54px;margin-bottom:14px;">
        <p style="font-family:var(--font-display);letter-spacing:.08em;font-size:13px;text-transform:uppercase;color:var(--yellow);margin-bottom:4px;">Helping Others Obtain Destiny</p>
        <p style="font-size:13.5px;opacity:.9;">A community-rooted nonprofit investing in Woodlawn &amp; Chicago's South Side — through violence prevention, workforce development, health &amp; wellness, youth programming, and re-entry services.</p>
      </div>
      <div>
        <h5>Get Help &amp; Give</h5>
        <ul>
          <li><a href="get-help.html">Get Help</a></li>
          <li><a href="get-involved.html">Volunteer</a></li>
          <li><a href="https://projecthood.networkforgood.com/">Donate</a></li>
          <li><a href="events.html">Community Calendar</a></li>
          <li><a href="partner.html">Partner with us</a></li>
          <li><a href="https://tiltify.com/project-hood/walk-across-america-2025">Walk With Us!</a></li>
          <li><a href="https://projecthood.networkforgood.com/projects/301372-2026-brick-by-brick-campaign" target="_blank" rel="noopener">Brick by Brick</a></li>
        </ul>
      </div>
      <div>
        <h5>Learn More</h5>
        <ul>
          <li><a href="about.html">About</a></li>
          <li><a href="pastor-brooks.html">Pastor Brooks</a></li>
          <li><a href="exec-director.html">Executive Director</a></li>
          <li><a href="programs.html">Programs</a></li>
          <li><a href="impact.html">News &amp; Impact</a></li>
          <li><a href="leo-center.html">LEO Center</a></li>
          <li><a href="ways-to-give.html">Ways to Give</a></li>
          <li><a href="contact.html">Contact</a></li>
        </ul>
      </div>
      <div>
        <h5>Get updates monthly</h5>
        <p style="font-size:13.5px;opacity:.9;">LEO Center progress, program milestones, upcoming events — delivered once a month.</p>
        <a class="btn btn-yellow" href="{NEWSLETTER_FORM_URL}" target="_blank" rel="noopener" style="margin-top:6px;display:inline-block;">Subscribe &rarr;</a>
      </div>
    </div>

    <div class="footer-trust" style="display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:center;padding:22px 0 4px;border-top:1px solid rgba(255,255,255,.14);">
      <span style="font-family:var(--font-display);letter-spacing:.08em;font-size:12px;text-transform:uppercase;color:var(--yellow);opacity:.9;">Independently rated &amp; verified</span>
      <a href="https://www.charitynavigator.org/ein/453964886" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:10px;text-decoration:none;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.18);border-radius:10px;padding:9px 14px;">
        <span aria-hidden="true" style="color:var(--yellow);font-size:15px;letter-spacing:2px;">&#9733;&#9733;&#9733;&#9733;</span>
        <span style="color:#fff;font-size:12.5px;line-height:1.25;"><strong>Charity Navigator</strong><br><span style="opacity:.85;">Four-Star Charity &middot; 95%</span></span>
      </a>
      <a href="https://www.guidestar.org/profile/45-3964886" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:10px;text-decoration:none;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.18);border-radius:10px;padding:9px 14px;">
        <span style="color:#fff;font-size:12.5px;line-height:1.25;"><strong>Candid &middot; GuideStar</strong><br><span style="opacity:.85;">View our nonprofit profile &rarr;</span></span>
      </a>
    </div>

    <div class="footer-bottom">
      <div>
        © 2026 Project H.O.O.D. · 6620 S. King Drive, Chicago IL 60637 · EIN 45-3964886<br>
        <a href="privacy.html">Privacy</a> · <a href="about.html">Financials &amp; 990s</a> · <a href="contact.html">Contact</a>
      </div>
      <div class="social-row">
        <a href="https://www.instagram.com/projecthood1/" aria-label="Instagram">IG</a>
        <a href="https://www.facebook.com/ProjectHood1/" aria-label="Facebook">FB</a>
        <a href="https://www.linkedin.com/company/project-h-o-o-d" aria-label="LinkedIn">IN</a>
        <a href="https://www.youtube.com/@projecthood8919" aria-label="YouTube">YT</a>
      </div>
    </div>
  </div>
</footer>

<script src="js/main.js"></script>
</body>
</html>
"""

# Helper — render the acronym tape
ACRONYM_TAPE = """
<div class="acronym-tape"><div class="inner">
  <span class="word"><strong>H</strong>ELPING</span>
  <span class="dot">★</span>
  <span class="word"><strong>O</strong>THERS</span>
  <span class="dot">★</span>
  <span class="word"><strong>O</strong>BTAIN</span>
  <span class="dot">★</span>
  <span class="word"><strong>D</strong>ESTINY</span>
</div></div>
"""

# ---------------------------------------------------------------------------
# Page builder
# ---------------------------------------------------------------------------

def _clean_internal_urls(html):
    """Strip .html from internal page links so URLs read cleanly
    (e.g. href="about.html" -> href="about", "index.html" -> "/").
    Output files stay named *.html; GitHub Pages + Netlify both serve
    /about from about.html. External links (http...) are untouched."""
    def repl(m):
        name = m.group(1)
        frag = m.group(2) or ''
        if name == 'index':
            return 'href="/' + frag + '"' if frag else 'href="/"'
        return 'href="' + name + frag + '"'
    return re.sub(r'href="([a-zA-Z0-9\-]+)\.html(#[^"]*)?"', repl, html)

def render(title, meta, active, body):
    active_flags = dict.fromkeys(
        ['a_about','a_programs','a_impact','a_leo','a_campaigns','a_gi','a_ways','a_news',
         'a_events','a_help'], '')
    if active:
        active_flags[active] = ' class="active"'
    head = HEAD.format(title=title, meta=meta, **active_flags)
    return _clean_internal_urls(head + body + FOOTER)

def write_page(filename, title, meta, active, body):
    path = SITE_DIR / filename
    path.write_text(render(title, meta, active, body), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

# -------- HOME --------
home_body = f"""
<!-- HERO — WALK WITH US -->
<section class="hero bg-black">
  <div class="wrap">
    <div class="hero-split">
      <div>
        <div class="eyebrow" style="color:var(--yellow);">Nationwide Campaign</div>
        <h1>Walk Together. <span class="hl-yellow">Change Communities.</span> Restore Hope.</h1>
        <p class="lead">Walk With Us! is a nationwide movement committed to restoring hope, opportunity, and unity in communities across America. Give, organize a walk, or start a team — and help raise $25M for youth, families, and the LEO Center.</p>
        <div style="margin-top:28px;display:flex;gap:12px;flex-wrap:wrap;">
          <a class="btn btn-yellow" href="https://tiltify.com/project-hood/walk-across-america-2025">Give to the movement</a>
          <a class="btn btn-outline-light" href="campaigns.html">Learn more</a>
        </div>
      </div>
      <div style="position:relative;">
        <img src="img/campaign-walk-hero.png" alt="Pastor Brooks — Walk With Us campaign" style="width:100%;border-radius:8px;display:block;">
        <div class="stamp-corner stamp"><img src="img/logo-knockout-offwhite.png" alt=""></div>
      </div>
    </div>
  </div>
</section>

<!-- BRICK CAMPAIGN -->
<section class="section bg-red" style="padding-top:var(--sp-3);padding-bottom:var(--sp-3);">
  <div class="wrap" style="display:flex;align-items:center;gap:var(--sp-3);flex-wrap:wrap;justify-content:space-between;">
    <div style="flex:1;min-width:260px;">
      <div class="eyebrow" style="color:var(--yellow);">Buy a Brick</div>
      <h2 style="color:#fff;margin:6px 0 10px;">Help us lay the foundation.</h2>
      <p style="color:rgba(255,255,255,.9);font-size:var(--fs-lead);margin:0;">Every brick you buy goes toward the LEO Center — a permanent home for youth, families, and opportunity on Chicago's South Side. Leave your name. Leave your legacy.</p>
    </div>
    <div style="flex-shrink:0;display:flex;gap:12px;flex-wrap:wrap;align-items:center;">
      <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/projects/301372-2026-brick-by-brick-campaign">Buy a Brick</a>
      <a class="btn btn-outline-light" href="leo-center.html">About LEO</a>
    </div>
  </div>
</section>

<!-- STORIES + VIDEO HUB (retention) -->
<section class="section">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--red);">Real Stories</div>
    <h2>This is what transformation looks like.</h2>
    <p style="font-size:var(--fs-lead);max-width:680px;">Behind every number is a person whose life changed on this block. Watch one — then read their stories.</p>
    <div class="grid-2" style="margin-top:var(--sp-3);align-items:center;gap:var(--sp-4);">
      <div style="display:flex;justify-content:center;">
        <div style="width:100%;max-width:360px;aspect-ratio:340/735;border-radius:14px;overflow:hidden;box-shadow:0 14px 44px rgba(0,0,0,.22);background:#000;">
          <iframe src="https://www.facebook.com/plugins/video.php?height=735&href=https%3A%2F%2Fwww.facebook.com%2Freel%2F1375823754382160%2F&show_text=false&width=360&t=0" style="border:none;overflow:hidden;width:100%;height:100%;" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"></iframe>
        </div>
      </div>
      <div style="display:flex;flex-direction:column;gap:14px;">
        <a href="workforce-development.html" class="card" style="display:block;padding:20px 22px;text-decoration:none;border-left:4px solid var(--red);">
          <span style="display:block;font-family:var(--font-display);text-transform:uppercase;letter-spacing:.08em;font-size:11px;color:var(--red);margin-bottom:6px;">Workforce</span>
          <strong style="display:block;color:var(--dark);font-size:18px;margin-bottom:4px;">From our Construction Program to the Chicago Roofers Union</strong>
          <span style="color:var(--muted);font-size:14px;">Terrance now helps build the LEO Center roof &rarr;</span>
        </a>
        <a href="reentry-services.html" class="card" style="display:block;padding:20px 22px;text-decoration:none;border-left:4px solid var(--gold);">
          <span style="display:block;font-family:var(--font-display);text-transform:uppercase;letter-spacing:.08em;font-size:11px;color:var(--dark);margin-bottom:6px;">Re-Entry</span>
          <strong style="display:block;color:var(--dark);font-size:18px;margin-bottom:4px;">Second chances, built two weeks at a time</strong>
          <span style="color:var(--muted);font-size:14px;">The Rebirth Project graduates beating the odds &rarr;</span>
        </a>
        <a href="youth-programming.html" class="card" style="display:block;padding:20px 22px;text-decoration:none;border-left:4px solid var(--blue);">
          <span style="display:block;font-family:var(--font-display);text-transform:uppercase;letter-spacing:.08em;font-size:11px;color:var(--blue);margin-bottom:6px;">Youth</span>
          <strong style="display:block;color:var(--dark);font-size:18px;margin-bottom:4px;">300+ seniors sent off to college</strong>
          <span style="color:var(--muted);font-size:14px;">Our annual Trunk Party launches the next chapter &rarr;</span>
        </a>
      </div>
    </div>
  </div>
</section>

<!-- WHO WE ARE -->
<section class="section bg-offwhite">
  <div class="wrap grid-2" style="align-items:center;">
    <div>
      <div class="eyebrow">Woodlawn, Chicago</div>
      <h2>Five Pillars. One neighborhood. A decade of showing up.</h2>
      <p style="font-size:var(--fs-lead);">Project H.O.O.D. invests directly on the block — in violence prevention, workforce development, health &amp; wellness, youth programming, and re-entry services. No national overhead, no middle layer.</p>
      <div style="margin-top:24px;display:flex;gap:12px;flex-wrap:wrap;">
        <a class="btn btn-primary" href="impact.html">See our impact</a>
        <a class="btn btn-outline-light" href="about.html">About us</a>
      </div>
    </div>
    <div style="min-height:300px;background-image:url('img/home-community.jpg');background-size:cover;background-position:center top"></div>
  </div>
</section>

{ACRONYM_TAPE}

<!-- STAT BAND -->
<section class="section bg-offwhite">
  <div class="wrap">
    <div class="eyebrow">2025 Impact</div>
    <h2>Real people. Real results. On the block.</h2>
    <div class="stat-grid" style="margin-top:var(--sp-3);">
      <div class="stat accent-green"><div class="v">15,000+</div><div class="l">neighbors served — not cases, people</div></div>
      <div class="stat"><div class="v">2M+ lbs</div><div class="l">food on the table</div></div>
      <div class="stat accent-red"><div class="v">$19/hr</div><div class="l">average starting wage for job placements</div></div>
      <div class="stat"><div class="v">84%</div><div class="l">of the LEO Center funded — $7M to go</div></div>
    </div>
    <p style="margin-top:var(--sp-3);font-size:14px;color:var(--muted);"><a href="impact.html">See the full impact report →</a></p>
  </div>
</section>

<!-- PROGRAM RIBBONS -->
<section class="section">
  <div class="wrap">
    <div class="eyebrow">What we do</div>
    <h2>Five Pillars, one strategy.</h2>
    <div class="grid-3" style="margin-top:var(--sp-3);">
      <div class="prog-card pg-green">
        <span class="tag tag-green">Violence Prevention</span>
        <h3 style="margin-top:10px;">Outreach on the block.</h3>
        <p style="font-family:var(--font-serif);">Credible messengers and conflict mediators embedded in the neighborhood, defusing violence before it escalates.</p>
        <a href="programs.html" style="margin-top:auto;">Read more →</a>
      </div>
      <div class="prog-card">
        <span class="tag tag-red">Workforce Development</span>
        <h3 style="margin-top:10px;">Careers, not jobs.</h3>
        <p style="font-family:var(--font-serif);">Training, certifications, and placement in construction, tech, and skilled trades — with an average starting wage of $19/hr.</p>
        <a href="programs.html" style="margin-top:auto;">Read more →</a>
      </div>
      <div class="prog-card pg-blue">
        <span class="tag tag-blue">Youth Programming</span>
        <h3 style="margin-top:10px;">Entrepreneurship &amp; youth enrichment.</h3>
        <p style="font-family:var(--font-serif);">Business skills, mentorship, and after-school programs — investing in who young people are becoming.</p>
        <a href="programs.html" style="margin-top:auto;">Read more →</a>
      </div>
      <div class="prog-card pg-purple">
        <span class="tag tag-purple">Health &amp; Wellness</span>
        <h3 style="margin-top:10px;">Access to care &amp; community wellness.</h3>
        <p style="font-family:var(--font-serif);">Free medical access, counseling, senior programming, recovery navigation, and crisis response — no insurance required, no barriers.</p>
        <a href="programs.html" style="margin-top:auto;">Read more →</a>
      </div>
      <div class="prog-card pg-yellow">
        <span class="tag tag-yellow">Re-Entry Services</span>
        <h3 style="margin-top:10px;">Second chances, real support.</h3>
        <p style="font-family:var(--font-serif);">Employment pathways, housing navigation, and wraparound support for individuals returning from incarceration.</p>
        <a href="programs.html" style="margin-top:auto;">Read more →</a>
      </div>
      <div class="prog-card">
        <span class="tag tag-black">Partnerships</span>
        <h3 style="margin-top:10px;">Built with Woodlawn.</h3>
        <p style="font-family:var(--font-serif);">Churches, schools, businesses, city agencies — rowing in the same direction.</p>
        <a href="about.html" style="margin-top:auto;">Read more →</a>
      </div>
    </div>
  </div>
</section>

<!-- HELP SOMEBODY -->
<section style="background:#111111;padding:80px 24px;text-align:center;">
  <div style="font-family:'Arial Black','Impact','Arial',sans-serif;font-weight:900;font-size:clamp(72px,14vw,180px);line-height:.95;color:#ffffff;letter-spacing:-0.03em;text-transform:uppercase;display:block;">HELP<br>SOMEBODY</div>
  <p style="color:rgba(255,255,255,.55);font-size:clamp(16px,2.5vw,20px);margin:28px auto 0;max-width:560px;font-family:var(--font-serif);font-style:italic;">When is the last time you helped somebody?</p>
  <div style="margin-top:40px;display:flex;gap:14px;justify-content:center;flex-wrap:wrap;">
    <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/" style="font-size:clamp(15px,2vw,17px);padding:14px 28px;">Help somebody today →</a>
  </div>
</section>

<!-- LEO CENTER FEATURE -->
<section class="section bg-black">
  <div class="wrap">
    <div class="grid-2">
      <div style="min-height:420px;background-image:url('img/leo-center-rendering.jpg');background-size:cover;background-position:center top;border-radius:6px;"></div>
      <div>
        <div class="eyebrow" style="color:var(--yellow);">Opening Fall 2026 · Capital Campaign</div>
        <h2>A home for everything we do.</h2>
        <p style="font-size:var(--fs-lead);opacity:.9;">The Robert R. McCormick Leadership &amp; Economic Opportunity Center — 90,000 sq ft on S. King Drive, opening Fall 2026. The physical home of Project H.O.O.D. and a signal that investment belongs on the South Side.</p>
        <div style="margin-top:24px;">
          <div class="progress" style="background:#1a1718;border-color:var(--yellow);">
            <div class="progress-fill" style="width:84%;">84% Funded · $38M of $45M</div>
          </div>
        </div>
        <div style="margin-top:24px;display:flex;gap:12px;flex-wrap:wrap;">
          <a class="btn btn-yellow" href="leo-center.html">Learn about LEO</a>
          <a class="btn btn-outline-light" href="https://projecthood.networkforgood.com/projects/301372-2026-brick-by-brick-campaign">Brick by Brick</a>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- TESTIMONIAL -->
<section class="section bg-bg">
  <div class="wrap">
    <div class="testimonial">
      <blockquote>"Project H.O.O.D. doesn't do programs <em>for</em> us. They do them <em>with</em> us — and they're still here when the cameras leave."</blockquote>
      <cite>— Community member · Woodlawn</cite>
    </div>
  </div>
</section>

<!-- FINAL CTA -->
<section class="cta-strip">
  <div class="wrap">
    <h2>Give. Volunteer. <span class="hl-yellow">Tell somebody.</span></h2>
    <p style="max-width:640px;margin:0 auto var(--sp-3);opacity:.95;">The most powerful thing you can do right now might just be sharing this with one person who needs to know this work exists.</p>
    <div class="btn-group">
      <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/">Donate</a>
      <a class="btn btn-outline-light" href="get-involved.html">Volunteer</a>
      <button onclick="if(navigator.share){{navigator.share({{title:'Project H.O.O.D.',text:'Help somebody. Project H.O.O.D. is transforming Chicago\'s South Side — and they need your support.',url:window.location.href}})}}else{{navigator.clipboard.writeText(window.location.href).then(()=>alert('Link copied — share it with someone.'));}}" class="btn btn-outline-light" style="cursor:pointer;">Share this page</button>
    </div>
  </div>
</section>
"""

# -------- ABOUT --------
about_body = f"""
<section class="hero bg-green">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">About</div>
    <h1>Built by Woodlawn. <span class="hl-yellow">For Woodlawn.</span></h1>
    <p class="lead">Project H.O.O.D. was founded by Pastor Corey B. Brooks in 2012 to transform Chicago's South Side through programs rooted in the community, not parachuted in.</p>
  </div>
</section>

{ACRONYM_TAPE}

<section class="section">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">Our mission</div>
      <h2>A decade of showing up.</h2>
      <p>Project H.O.O.D. (Helping Others Obtain Destiny) exists to create sustainable change in Woodlawn and the broader South Side of Chicago. We operate across five interconnected pillars — violence prevention, workforce development, health &amp; wellness, youth programming, and re-entry services — because no one of these alone is enough.</p>
      <p>We believe that the people closest to the problems are closest to the solutions. Everything we do is built with the neighborhood, not for it.</p>
    </div>
    <div style="min-height:340px;background-image:url('img/about-mission.jpg');background-size:cover;background-position:center top"></div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap">
    <div class="eyebrow">The story</div>
    <h2>How we got here.</h2>
    <div class="grid-2" style="margin-top:var(--sp-3);">
      <div>
        <h3>2012 · Founded</h3>
        <p>Pastor Brooks takes a stand against neighborhood violence by spending 94 nights on a motel rooftop across from a funeral parlor to protest youth gun deaths. Project H.O.O.D. launches soon after.</p>
      </div>
      <div>
        <h3>2015–2020 · Programs scale</h3>
        <p>Workforce development partnership with local construction firms grows from dozens to hundreds of placements. Violence interruption team formalizes.</p>
      </div>
      <div>
        <h3>2022–2024 · LEO breaks ground</h3>
        <p>Capital campaign launches for the Leadership and Economic Opportunity Center — a 90,000 sq ft community hub on S. King Drive. Groundbreaking in 2022, 84% funded by 2025.</p>
      </div>
      <div>
        <h3>2025 · Walk Across America</h3>
        <p>Pastor Brooks walks 900+ miles from Chicago to New York to raise the final $45M and spotlight what's possible. 15,000+ served this year. 2M+ lbs of food distributed. $19/hr average starting wage for job placements.</p>
      </div>
    </div>
  </div>
</section>

<section class="section bg-black">
  <div class="wrap grid-2">
    <div style="min-height:320px;background-image:url('img/about-pastor-brooks.jpg');background-size:cover;background-position:center top"></div>
    <div>
      <div class="eyebrow" style="color:var(--yellow);">Founder</div>
      <h2 style="color:var(--white);">Pastor Corey B. Brooks</h2>
      <p style="font-size:var(--fs-lead);opacity:.9;">Pastor, entrepreneur, and community organizer. Founder of Project H.O.O.D. and senior pastor of New Beginnings Church of Chicago. Walked across America in 2025 to fund the LEO Center. Known for meeting kids on the corner before asking them to come to church.</p>
      <div style="margin-top:22px;display:flex;gap:12px;flex-wrap:wrap;">
        <a class="btn btn-yellow" href="letter.html">Read Pastor Brooks' letter</a>
        <a class="btn btn-outline-light" href="#book">Book Pastor Brooks</a>
      </div>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap grid-2" style="align-items:center;gap:var(--sp-4);">
    <div style="min-height:340px;background-image:url('img/desmond-marshall.jpg');background-size:cover;background-position:center top"></div>
    <div>
      <div class="eyebrow">Executive Director</div>
      <h2>Desmond "Dez" Marshall</h2>
      <p style="font-size:var(--fs-lead);">Dez joined Project H.O.O.D. as a volunteer and never left. Today he leads a staff of 83+ across multiple divisions, has raised more than $44M in two years, and oversees programs that serve 15,000+ people annually throughout Chicagoland.</p>
      <div style="margin-top:24px;">
        <a class="btn btn-primary" href="exec-director.html">Meet Dez →</a>
      </div>
    </div>
  </div>
</section>


<section class="section" id="book">
  <div class="wrap">
    <div style="max-width:640px;margin:0 auto;text-align:center;">
      <div class="eyebrow" style="color:var(--red);">Speaking &amp; appearances</div>
      <h2>Book Pastor Brooks</h2>
      <p style="font-size:var(--fs-lead);color:var(--muted);">Pastor Brooks speaks on community transformation, faith-driven leadership, entrepreneurship, and what it takes to stay — in a neighborhood, in a mission, in the work. Tell us about your event and we'll follow up within two business days.</p>
    </div>
    <!-- GOOGLE FORM LINK — run create_ph_forms.gs → createAllForms() → copy "Booking Inquiries" URL → replace href below -->
    <div style="max-width:640px;margin:var(--sp-3) auto 0;text-align:center;">
      <a class="btn btn-primary" href="https://docs.google.com/forms/d/e/1FAIpQLSfFCudwdnRCOwYiK-mWnkWIBhg1jVO37uX2EZnXqPl3Yr38TQ/viewform" target="_blank" rel="noopener" style="font-size:17px;padding:16px 40px;display:inline-block;">Submit a booking inquiry →</a>
      <p style="font-size:13px;color:var(--muted);margin-top:14px;">We respond within two business days. For urgent requests, call <a href="tel:7733548483" style="color:var(--green);">773.354.8483</a>.</p>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow" style="color:var(--green);">Stewardship</div>
      <h2>Stewardship, on paper.</h2>
      <p>Project H.O.O.D. is a 501(c)(3) public charity (EIN 45-3964886). 990s and annual reports are public record. We are independently rated by Charity Navigator and listed on Candid (GuideStar).</p>
    </div>
    <div>
      <ul style="list-style:none;padding:0;">
        <li style="padding:14px 0;border-bottom:1px solid var(--line);"><strong>2025 Annual Report</strong> · <a href="annual-report.html">Read online</a> · <a href="docs/ph-annual-report-2025.pdf" target="_blank" rel="noopener">Download PDF</a></li>
        <li style="padding:14px 0;border-bottom:1px solid var(--line);"><strong>2024 Form 990</strong> · <a href="docs/ph-990-2024.pdf" target="_blank" rel="noopener">Download PDF</a></li>
        <li style="padding:14px 0;border-bottom:1px solid var(--line);"><strong>2023 Form 990</strong> · <a href="#">Download PDF</a></li>
        <li style="padding:14px 0;border-bottom:1px solid var(--line);"><strong>2024 Annual Report</strong> · <a href="#">Download PDF</a></li>
        <li style="padding:14px 0;border-bottom:1px solid var(--line);">
          <a href="https://www.charitynavigator.org/ein/453964886" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:10px;text-decoration:none;">
            <span aria-hidden="true" style="color:#d98f00;font-size:18px;letter-spacing:2px;">&#9733;&#9733;&#9733;&#9733;</span>
            <span style="color:var(--text);"><strong>Charity Navigator</strong> · Four-Star Charity · 95%</span>
          </a>
        </li>
        <li style="padding:14px 0;">
          <a href="https://www.guidestar.org/profile/45-3964886" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:10px;text-decoration:none;color:var(--text);">
            <strong>Candid (GuideStar)</strong> · View our nonprofit profile →
          </a>
        </li>
      </ul>
    </div>
  </div>
</section>
"""

pastor_brooks_body = """
<section class="hero bg-black">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">Founder &amp; CEO</div>
    <h1>Pastor <span class="hl-yellow">Corey B. Brooks</span></h1>
    <p class="lead">The &ldquo;Rooftop Pastor.&rdquo; Founder and CEO of Project H.O.O.D., senior pastor of New Beginnings Church of Chicago, and a relentless voice for Chicago&rsquo;s South Side.</p>
  </div>
</section>

<section class="section bg-black" style="padding-top:0;">
  <div class="wrap grid-2" style="align-items:center;">
    <div style="min-height:420px;background-image:url('img/about-pastor-brooks.jpg');background-size:cover;background-position:center top;border-radius:10px;"></div>
    <div>
      <p style="font-size:var(--fs-lead);color:var(--white);opacity:.92;">In 2011, Pastor Brooks moved onto the rooftop of an abandoned motel across from a funeral parlor and stayed 94 nights &mdash; through a Chicago winter &mdash; to protest the youth gun deaths tearing through Woodlawn. Project H.O.O.D. was born soon after.</p>
      <p style="color:var(--white);opacity:.85;">More than a decade later, he leads an organization that serves 15,000+ people a year and is building the $45M Leadership &amp; Economic Opportunity (LEO) Center. In 2025 he walked 900+ miles from Chicago to New York to help fund it.</p>
      <div style="margin-top:22px;display:flex;gap:12px;flex-wrap:wrap;">
        <a class="btn btn-yellow" href="letter.html">Read Pastor Brooks&rsquo; letter</a>
        <a class="btn btn-outline-light" href="#book">Book Pastor Brooks</a>
      </div>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap">
    <div class="eyebrow">The story</div>
    <h2>How we got here.</h2>
    <div class="grid-2" style="margin-top:var(--sp-3);">
      <div>
        <h3>2012 &middot; Founded</h3>
        <p>Pastor Brooks takes a stand against neighborhood violence by spending 94 nights on a motel rooftop across from a funeral parlor to protest youth gun deaths. Project H.O.O.D. launches soon after.</p>
      </div>
      <div>
        <h3>2015&ndash;2020 &middot; Programs scale</h3>
        <p>Workforce development partnerships grow from dozens to hundreds of placements. The violence-interruption team formalizes across Woodlawn.</p>
      </div>
      <div>
        <h3>2022&ndash;2024 &middot; LEO breaks ground</h3>
        <p>The capital campaign launches for the Leadership and Economic Opportunity Center &mdash; a 90,000 sq ft hub on S. King Drive. Groundbreaking in 2022.</p>
      </div>
      <div>
        <h3>2025 &middot; Walk Across America</h3>
        <p>Pastor Brooks walks 900+ miles from Chicago to New York to raise the final funds for LEO and spotlight what&rsquo;s possible. 15,000+ served this year.</p>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--red);">Rooftop Revelations</div>
    <h2>Latest from the rooftop.</h2>
    <p style="font-size:var(--fs-lead);color:var(--muted);max-width:62ch;">Pastor Brooks&rsquo; ongoing video series on faith, community, and the fight for Chicago&rsquo;s South Side &mdash; short reflections that carry the spirit of the rooftop where it all began.</p>
    <div class="grid-2" style="margin-top:var(--sp-3);gap:20px;">

      <a href="https://www.foxnews.com/video/6387072632112" target="_blank" rel="noopener" style="display:block;text-decoration:none;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:var(--white);"><div style="position:relative;aspect-ratio:16/9;background:#1a1a1a;"><img src="https://a57.foxnews.com/cf-images.us-east-1.prod.boltdns.net/v1/static/694940094001/f3a9c040-fc77-4466-9c9b-de728e5cbc57/c8c596eb-61f5-4568-a93b-e379d3cb4cab/1280x720/match/1024/512/image.jpg?ve=1&amp;tl=1" alt="2026 is the year to listen to opposing views" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block;" onerror="this.style.display='none';this.parentNode.style.background='linear-gradient(135deg,var(--green),var(--ink))';"><span aria-hidden="true" style="position:absolute;left:14px;bottom:12px;display:inline-flex;align-items:center;gap:7px;background:rgba(0,0,0,.72);color:#fff;font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;padding:6px 11px;border-radius:999px;">&#9654; Watch on Fox News</span></div><div style="padding:18px 20px 20px;"><div style="font-size:11px;letter-spacing:.07em;text-transform:uppercase;color:var(--green);font-weight:700;">Latest episode</div><h3 style="margin:6px 0 4px;color:var(--ink);font-size:19px;line-height:1.25;">2026 is the year to listen to opposing views</h3><p style="color:var(--muted);font-size:13.5px;margin:0;">Rooftop Revelations &rarr;</p></div></a>

      <a href="https://www.foxnews.com/video/6384187866112" target="_blank" rel="noopener" style="display:block;text-decoration:none;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:var(--white);"><div style="position:relative;aspect-ratio:16/9;background:#1a1a1a;"><img src="https://a57.foxnews.com/cf-images.us-east-1.prod.boltdns.net/v1/static/694940094001/8a282d19-2b33-46f6-8fe1-56fbb0c14332/43b6f249-334b-4dc1-b7ad-556ebb8d6c08/1280x720/match/1024/512/image.jpg?ve=1&amp;tl=1" alt="The system thrives and profits off of brokenness" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block;" onerror="this.style.display='none';this.parentNode.style.background='linear-gradient(135deg,var(--green),var(--ink))';"><span aria-hidden="true" style="position:absolute;left:14px;bottom:12px;display:inline-flex;align-items:center;gap:7px;background:rgba(0,0,0,.72);color:#fff;font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;padding:6px 11px;border-radius:999px;">&#9654; Watch on Fox News</span></div><div style="padding:18px 20px 20px;"><h3 style="margin:6px 0 4px;color:var(--ink);font-size:19px;line-height:1.25;">The system thrives and profits off of brokenness</h3><p style="color:var(--muted);font-size:13.5px;margin:0;">Rooftop Revelations &rarr;</p></div></a>

      <a href="https://www.foxnews.com/video/6364243117112" target="_blank" rel="noopener" style="display:block;text-decoration:none;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:var(--white);"><div style="position:relative;aspect-ratio:16/9;background:#1a1a1a;"><img src="https://a57.foxnews.com/cf-images.us-east-1.prod.boltdns.net/v1/static/694940094001/12de3c37-4fc5-4ffc-9197-834e2144239e/88c05c71-4598-4348-ac07-28f90693dfe6/1280x720/match/1024/512/image.jpg?ve=1&amp;tl=1" alt="Dear America, I still believe in you. Let me count the ways" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block;" onerror="this.style.display='none';this.parentNode.style.background='linear-gradient(135deg,var(--green),var(--ink))';"><span aria-hidden="true" style="position:absolute;left:14px;bottom:12px;display:inline-flex;align-items:center;gap:7px;background:rgba(0,0,0,.72);color:#fff;font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;padding:6px 11px;border-radius:999px;">&#9654; Watch on Fox News</span></div><div style="padding:18px 20px 20px;"><h3 style="margin:6px 0 4px;color:var(--ink);font-size:19px;line-height:1.25;">Dear America, I still believe in you. Let me count the ways</h3><p style="color:var(--muted);font-size:13.5px;margin:0;">Rooftop Revelations &rarr;</p></div></a>

      <a href="https://www.foxnews.com/video/6366747916112" target="_blank" rel="noopener" style="display:block;text-decoration:none;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:var(--white);"><div style="position:relative;aspect-ratio:16/9;background:#1a1a1a;"><img src="https://a57.foxnews.com/cf-images.us-east-1.prod.boltdns.net/v1/static/694940094001/b3f0451e-d6f5-4e84-8c35-199340b964cf/f273f839-9b6c-4141-94bb-7b059d1fa8c1/1280x720/match/1024/512/image.jpg?ve=1&amp;tl=1" alt="Why do Americans ignore common sense about race relations?" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block;" onerror="this.style.display='none';this.parentNode.style.background='linear-gradient(135deg,var(--green),var(--ink))';"><span aria-hidden="true" style="position:absolute;left:14px;bottom:12px;display:inline-flex;align-items:center;gap:7px;background:rgba(0,0,0,.72);color:#fff;font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;padding:6px 11px;border-radius:999px;">&#9654; Watch on Fox News</span></div><div style="padding:18px 20px 20px;"><h3 style="margin:6px 0 4px;color:var(--ink);font-size:19px;line-height:1.25;">Why do Americans ignore common sense about race relations?</h3><p style="color:var(--muted);font-size:13.5px;margin:0;">Rooftop Revelations &rarr;</p></div></a>

    </div>
    <div style="margin-top:var(--sp-3);">
      <a class="btn btn-primary" href="https://www.foxnews.com/category/us/digital-originals/rooftop-revelations" target="_blank" rel="noopener">Watch the full series on Fox News &rarr;</a>
    </div>
  </div>
</section>

<section class="section bg-green">
  <div class="wrap" style="max-width:var(--w-read);text-align:center;">
    <div class="eyebrow" style="color:var(--yellow);">In his words</div>
    <p style="font-family:var(--font-serif);font-size:clamp(20px,3vw,30px);line-height:1.5;color:var(--white);">&ldquo;When I moved onto the rooftop of an abandoned motel on Chicago&rsquo;s South Side, people thought I was crazy. Maybe I was. But I had made a promise &mdash; I was going to stay until something changed. That something is Project H.O.O.D.&rdquo;</p>
    <div style="margin-top:24px;">
      <a class="btn btn-yellow" href="letter.html">Read the full letter &rarr;</a>
    </div>
  </div>
</section>

<section class="section" id="book">
  <div class="wrap">
    <div style="max-width:640px;margin:0 auto;text-align:center;">
      <div class="eyebrow" style="color:var(--red);">Speaking &amp; appearances</div>
      <h2>Book Pastor Brooks</h2>
      <p style="font-size:var(--fs-lead);color:var(--muted);">Pastor Brooks speaks on community transformation, faith-driven leadership, entrepreneurship, and what it takes to stay &mdash; in a neighborhood, in a mission, in the work. Tell us about your event and we&rsquo;ll follow up within two business days.</p>
    </div>
    <div style="max-width:640px;margin:var(--sp-3) auto 0;text-align:center;">
      <a class="btn btn-primary" href="https://docs.google.com/forms/d/e/1FAIpQLSfFCudwdnRCOwYiK-mWnkWIBhg1jVO37uX2EZnXqPl3Yr38TQ/viewform" target="_blank" rel="noopener" style="font-size:17px;padding:16px 40px;display:inline-block;">Submit a booking inquiry &rarr;</a>
      <p style="font-size:13px;color:var(--muted);margin-top:14px;">We respond within two business days. For urgent requests, call <a href="tel:7733548483" style="color:var(--green);">773.354.8483</a>.</p>
    </div>
  </div>
</section>

"""

# -------- LETTER FROM PASTOR BROOKS --------
letter_body = """
<section class="hero bg-black">
  <div class="wrap" style="max-width:var(--w-read);">
    <div class="eyebrow" style="color:var(--yellow);">A message from our founder</div>
    <h1 style="font-size:clamp(28px,5vw,52px);line-height:1.15;">A letter from<br>Pastor Corey Brooks</h1>
    <p style="font-size:14px;opacity:.55;margin-top:8px;">Founder &amp; CEO, Project H.O.O.D. &middot; Senior Pastor, New Beginnings Church of Chicago</p>
  </div>
</section>

<section class="section">
  <div class="wrap" style="max-width:var(--w-read);">
    <div style="font-family:var(--font-serif);font-size:clamp(16px,2vw,20px);line-height:1.8;color:var(--ink);">

      <p>When I moved onto the rooftop of an abandoned motel on Chicago's South Side in 2011, people thought I was crazy.</p>

      <p>Maybe I was. But I had made a promise — to the young people I was burying every week, to the families who were losing sons and brothers to streets that offered no other options, to a neighborhood that the rest of the world had decided to write off. I was going to stay until something changed.</p>

      <p>That something is Project H.O.O.D.</p>

      <p><strong>Helping Others Obtain Destiny</strong> started with a vision and not much else. No building. No budget. Just the belief that Woodlawn — our neighborhood, <em>your</em> neighborhood — deserved the same investment as any other community in this city. That the people here had gifts, drive, and potential that nobody was being asked to tap.</p>

      <p>Fifteen years later, I watch young men walk out of our workforce program and into jobs that pay a living wage. I watch women who came through our re-entry program open businesses on the same blocks where they once felt trapped. I watch kids who had no safe place to go after school become mentors for the kids coming up behind them. And I watch our new LEO Center — the Leadership and Economic Opportunities Center — rise up as proof that Woodlawn isn't being left behind. We are building forward.</p>

      <p style="font-size:clamp(20px,3vw,28px);font-weight:700;line-height:1.4;color:var(--black);border-left:4px solid var(--yellow);padding-left:20px;margin:40px 0;">None of this happens without you.</p>

      <p>When you give to Project H.O.O.D., you aren't writing a check to an organization. You are investing directly in a person. A young man in our violence interruption program who needed someone to call him at 2 a.m. instead of letting him make a decision he couldn't take back. A mother getting her first apartment after re-entry because we helped her get documents, references, and a second chance. A teenager who learned to code, to lead, to believe that his life could look different than what he'd been handed.</p>

      <p><strong>Every dollar stays here. In Woodlawn. On the block.</strong></p>

      <p>We don't have a national overhead. We don't have layers between your gift and the people it reaches. We have a community — and the people in it are counting on us to keep showing up.</p>

      <p>I am asking you to show up with us.</p>

      <p>Give what you can. Give monthly if you're able. Tell someone else about us. Come to an event. Volunteer. Partner with us. However you choose to be part of this work, I promise you this: we will be faithful stewards of what you invest.</p>

      <p>Woodlawn is not a charity case. It is a community in motion. And with your support, there is no limit to what we build next.</p>

      <div style="margin-top:48px;padding-top:32px;border-top:1px solid var(--line);">
        <p style="margin:0;font-family:var(--font-display);font-size:clamp(22px,3vw,32px);font-weight:700;line-height:1.2;">In faith and service,</p>
        <p style="margin:8px 0 0;font-size:18px;font-weight:600;">Pastor Corey Brooks</p>
        <p style="margin:4px 0 0;font-size:14px;color:var(--muted);">Founder &amp; CEO, Project H.O.O.D.<br>6620 S. King Drive &middot; Chicago, IL 60637<br>EIN 45-3964886 &middot; All gifts are tax-deductible</p>
      </div>

    </div>
  </div>
</section>

<section class="cta-strip">
  <div class="wrap">
    <h2>Give. Volunteer. <span class="hl-yellow">Tell somebody.</span></h2>
    <div class="btn-group">
      <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/" target="_blank" rel="noopener">Give to Project H.O.O.D. →</a>
      <a class="btn btn-outline-light" href="donate.html">All ways to give</a>
      <a class="btn btn-outline-light" href="get-involved.html">Get involved</a>
    </div>
  </div>
</section>
"""

# -------- PROGRAMS HUB --------
programs_body = f"""
<section class="hero bg-red">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">Programs</div>
    <h1>Five Pillars. One <span class="hl-yellow">strategy.</span></h1>
    <p class="lead">Violence prevention, workforce development, health &amp; wellness, youth programming, and re-entry services — interlocking, not siloed. You can't fix one without touching the others.</p>
  </div>
</section>

{ACRONYM_TAPE}

<section class="section">
  <div class="wrap">
    <div class="grid-2">
      <div class="prog-card pg-green">
        <span class="tag tag-green">01 · Violence Prevention</span>
        <h3 style="margin-top:12px;">Outreach on the block.</h3>
        <p>Credible messengers and conflict mediators embedded in the neighborhood — defusing disputes before they escalate, mentoring young people out of the life.</p>
        <ul style="font-size:14px;color:var(--muted);margin:var(--sp-2) 0;">
          <li>24/7 community response team</li>
          <li>Hospital-based intervention</li>
          <li>School partnership mediators</li>
        </ul>
        <a href="violence-prevention.html" class="btn btn-outline" style="align-self:flex-start;margin-top:auto;">About Violence Prevention</a>
      </div>
      <div class="prog-card">
        <span class="tag tag-red">02 · Workforce Development</span>
        <h3 style="margin-top:12px;">Careers, not jobs.</h3>
        <p>Training and placement in construction, tech, and skilled trades. Partnerships with certifiers, unions, and employers who actually hire our grads.</p>
        <ul style="font-size:14px;color:var(--muted);margin:var(--sp-2) 0;">
          <li>OSHA-30 + construction prep</li>
          <li>IT/tech bootcamp</li>
          <li>Direct-hire employer network</li>
        </ul>
        <a href="workforce-development.html" class="btn btn-outline" style="align-self:flex-start;margin-top:auto;">About Workforce</a>
      </div>
      <div class="prog-card pg-blue">
        <span class="tag tag-blue">03 · Youth Programming</span>
        <h3 style="margin-top:12px;">Entrepreneurship &amp; youth enrichment.</h3>
        <p>Business skills, academic support, and mentorship — building the next generation of leaders from Woodlawn up.</p>
        <ul style="font-size:14px;color:var(--muted);margin:var(--sp-2) 0;">
          <li>Entrepreneurship training</li>
          <li>Homework + tutoring</li>
          <li>College/career readiness</li>
        </ul>
        <a href="youth-programming.html" class="btn btn-outline" style="align-self:flex-start;margin-top:auto;">About Youth Programming</a>
      </div>
      <div class="prog-card pg-purple">
        <span class="tag tag-purple">04 · Health &amp; Wellness</span>
        <h3 style="margin-top:12px;">Access to care &amp; community wellness.</h3>
        <p>Free medical access, counseling, recovery navigation, senior programming, and crisis response — because a healthy community is the foundation for everything else.</p>
        <ul style="font-size:14px;color:var(--muted);margin:var(--sp-2) 0;">
          <li>Individual therapy</li>
          <li>Group support circles</li>
          <li>Crisis + post-incident response</li>
        </ul>
        <a href="health-wellness.html" class="btn btn-outline" style="align-self:flex-start;margin-top:auto;">About Health &amp; Wellness</a>
      </div>
      <div class="prog-card pg-yellow">
        <span class="tag tag-yellow">05 · Re-Entry Services</span>
        <h3 style="margin-top:12px;">Second chances, real support.</h3>
        <p>Employment pathways, housing navigation, and wraparound support for individuals returning from incarceration — so they land somewhere stable.</p>
        <ul style="font-size:14px;color:var(--muted);margin:var(--sp-2) 0;">
          <li>Job placement + career coaching</li>
          <li>Housing assistance</li>
          <li>Case management + referrals</li>
        </ul>
        <a href="reentry-services.html" class="btn btn-outline" style="align-self:flex-start;margin-top:auto;">About Re-Entry Services</a>
      </div>
      <div class="prog-card">
        <span class="tag tag-black">Participant Intake</span>
        <h3 style="margin-top:12px;">Connect with us.</h3>
        <p>Our case-management system is Social Solutions Apricot. Apply once, and our intake team will route you to the right program and staff member.</p>
        <a href="https://projecthood.socialsolutionsportal.com/apricot-intake/0eb461e5-38a9-4ad1-9a4e-02bb3ee1414d" class="btn btn-primary" style="align-self:flex-start;margin-top:auto;" target="_blank" rel="noopener">Connect with us →</a>
        <p style="font-size:12px;color:var(--muted);margin-top:8px;font-style:italic;">Opens Apricot intake portal in a new tab.</p>
      </div>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--purple);">Health &amp; Wellness · Partner Spotlight</div>
    <h2>Free medical care, right at New Beginnings Church.</h2>
    <div class="grid-2" style="margin-top:var(--sp-3);align-items:center;gap:var(--sp-4);">
      <div>
        <p style="font-size:var(--fs-lead);">The <strong>Southside Free Clinic (SSFC)</strong> — a collaboration between the University of Chicago Pritzker School of Medicine, Project H.O.O.D., and Friend Health — provides free, quality medical care to South Side residents. No insurance needed. Walk-ins welcome.</p>
        <div style="margin:var(--sp-3) 0;display:flex;flex-direction:column;gap:12px;">
          <div style="display:flex;gap:14px;align-items:flex-start;">
            <span style="font-size:20px;">📍</span>
            <div><strong>New Beginnings Church</strong><br>6620 S. King Dr., Chicago, IL 60637</div>
          </div>
          <div style="display:flex;gap:14px;align-items:flex-start;">
            <span style="font-size:20px;">🗓</span>
            <div><strong>1st &amp; 3rd Sunday of each month</strong><br>12PM – 4PM</div>
          </div>
          <div style="display:flex;gap:14px;align-items:flex-start;">
            <span style="font-size:20px;">📞</span>
            <div><a href="tel:3127256648"><strong>312-725-6648</strong></a><br>Call to schedule an appointment</div>
          </div>
          <div style="display:flex;gap:14px;align-items:flex-start;">
            <span style="font-size:20px;">🏥</span>
            <div><strong>Referrals</strong><br>Patients are referred to Friend Health at 6250 S. Cottage Grove</div>
          </div>
        </div>
        <div style="display:flex;gap:12px;flex-wrap:wrap;">
          <a class="btn btn-primary" href="docs/ssfc-flyer-2025-2026.pdf" target="_blank" rel="noopener">Download flyer</a>
        </div>
        <div style="margin-top:var(--sp-3);border-radius:8px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,.12);">
          <iframe src="docs/ssfc-flyer-2025-2026.pdf" width="100%" height="560" style="display:block;border:none;" title="Southside Free Clinic flyer">
            <p>Your browser doesn't support embedded PDFs. <a href="docs/ssfc-flyer-2025-2026.pdf" target="_blank">Download the flyer here.</a></p>
          </iframe>
        </div>
      </div>
      <div style="background:#fff;border-radius:8px;padding:var(--sp-3);border:1px solid var(--line);">
        <p style="font-size:13px;text-transform:uppercase;letter-spacing:.08em;font-weight:700;color:var(--muted);margin-bottom:var(--sp-2);">Services offered</p>
        <ul style="list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:10px;">
          <li style="padding:10px 14px;background:var(--purple);color:#fff;border-radius:4px;font-weight:600;">Diabetes</li>
          <li style="padding:10px 14px;background:var(--purple);color:#fff;border-radius:4px;font-weight:600;">High Blood Pressure</li>
          <li style="padding:10px 14px;background:var(--purple);color:#fff;border-radius:4px;font-weight:600;">High Cholesterol</li>
          <li style="padding:10px 14px;background:var(--purple);color:#fff;border-radius:4px;font-weight:600;">General Health Check-Ups</li>
          <li style="padding:10px 14px;background:var(--purple);color:#fff;border-radius:4px;font-weight:600;">Rash / Allergies</li>
          <li style="padding:10px 14px;background:var(--purple);color:#fff;border-radius:4px;font-weight:600;">Upset Stomach · Bodily Pain</li>
          <li style="padding:10px 14px;background:var(--bg);border-radius:4px;font-weight:600;color:var(--muted);font-style:italic;">And more — walk-ins welcome</li>
        </ul>
        <p style="margin-top:var(--sp-2);font-size:12px;color:var(--muted);">In collaboration with the University of Chicago Pritzker School of Medicine &amp; Friend Health.</p>
      </div>
    </div>
  </div>
</section>

<section class="cta-strip">
  <div class="wrap">
    <h2>Every program needs people and dollars.</h2>
    <div class="btn-group">
      <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/">Donate</a>
      <a class="btn btn-outline-light" href="get-involved.html">Volunteer</a>
    </div>
  </div>
</section>
"""

# -------- PILLAR 1: VIOLENCE PREVENTION --------
violence_prevention_body = f"""
<section class="hero bg-green">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">Programs · Pillar 1</div>
    <h1>Creating <span class="hl-yellow">Safer Communities.</span></h1>
    <p class="lead">Credible messengers and conflict mediators embedded in the neighborhood — defusing violence before it escalates and mentoring young people out of the life.</p>
  </div>
</section>

<section class="section">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">What we do</div>
      <h2>Prevention before the incident. Response after.</h2>
      <p>Our Violence Prevention pillar takes a multifaceted approach to building safer neighborhoods. Outreach workers are out on the block nightly — mediating disputes, riding to the hospital with shooting victims, and pulling young men aside before a retaliation escalates. Every worker carries a long-term caseload of participants they mentor directly.</p>
      <ul>
        <li>24/7 community response team covering Woodlawn + Washington Park</li>
        <li>Hospital-based intervention partnering with University of Chicago Medicine</li>
        <li>Embedded mediators in local schools</li>
        <li>Weekly peace circles for young men 16–24</li>
        <li>Conflict resolution training for community members</li>
        <li>Community events promoting unity and connection</li>
      </ul>
    </div>
    <div style="position:relative;width:100%;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:8px;box-shadow:0 8px 32px rgba(0,0,0,.15);">
      <iframe
        src="https://www.youtube.com/embed/rsXtXPvaziY"
        title="Project H.O.O.D. credited with reducing violent crime in Woodlawn — CBS Chicago"
        frameborder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen
        style="position:absolute;top:0;left:0;width:100%;height:100%;border-radius:8px;">
      </iframe>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">Who runs it</div>
      <h2>Led by people from the block.</h2>
      <p>Our outreach team is made up of credible messengers — people with lived experience in the community who have earned trust on the street. They work alongside licensed professionals and in close collaboration with law enforcement and community partners.</p>
    </div>
    <div>
      <div class="eyebrow" style="color:var(--green);">Partners</div>
      <h3>Who we work with.</h3>
      <ul style="list-style:none;padding:0;">
        <li style="padding:8px 0;border-bottom:1px solid var(--line);">University of Chicago Medicine</li>
        <li style="padding:8px 0;border-bottom:1px solid var(--line);">Chicago Public Schools — Hyde Park Academy</li>
        <li style="padding:8px 0;border-bottom:1px solid var(--line);">Office of Violence Prevention, City of Chicago</li>
        <li style="padding:8px 0;">New Beginnings Church of Chicago</li>
      </ul>
    </div>
  </div>
</section>

<section class="section bg-green">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">2025 Impact</div>
    <h2 style="color:var(--white);">What the work is producing.</h2>
    <div class="stat-grid" style="margin-top:var(--sp-3);">
      <div class="stat"><div class="v">140+</div><div class="l">incidents mediated</div></div>
      <div class="stat"><div class="v">22</div><div class="l">hospital-bedside interventions</div></div>
      <div class="stat"><div class="v">85</div><div class="l">young men in peace circles</div></div>
      <div class="stat"><div class="v">31%</div><div class="l">reduction in 60637 gun homicides</div></div>
    </div>
    <div class="testimonial" style="margin-top:var(--sp-4);background:var(--black);">
      <blockquote>"They showed up when nobody else did. When my brother got shot, outreach was at the hospital before my mother got there."</blockquote>
      <cite>— Program participant, age 23</cite>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--green);">Real Stories</div>
    <h2>A weekend with no shootings in Woodlawn.</h2>
    <p class="lead" style="max-width:760px;">This year, our team marked something that once felt impossible: an entire weekend in Woodlawn with no shootings. One weekend doesn&rsquo;t end the work &mdash; but it proves what sustained, daily investment in people can do.</p>
    <p style="max-width:760px;">Moments like these don&rsquo;t come from a single event or program. They&rsquo;re the product of credible messengers on the block every night, mentors who pull young people aside before a conflict escalates, and a community that refuses to accept violence as normal.</p>
  </div>
</section>

<section class="cta-strip">
  <div class="wrap">
    <h2>Support the outreach team.</h2>
    <div class="btn-group">
      <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/">Fund this pillar</a>
      <a class="btn btn-outline-light" href="get-involved.html">Volunteer</a>
      <a class="btn btn-outline-light" href="https://projecthood.socialsolutionsportal.com/apricot-intake/0eb461e5-38a9-4ad1-9a4e-02bb3ee1414d" target="_blank" rel="noopener">Connect with us</a>
    </div>
  </div>
</section>
"""

# -------- PILLAR 2: WORKFORCE DEVELOPMENT --------
workforce_development_body = f"""
<section class="hero bg-red">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">Programs · Pillar 2</div>
    <h1>Providing <span class="hl-yellow">Opportunities.</span></h1>
    <p class="lead">Comprehensive job training, placement, and career development — because economic empowerment is how you break the cycle for good.</p>
  </div>
</section>

<section class="section">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">What we do</div>
      <h2>Careers, not just jobs</h2>
      <p>Our Workforce Development pillar equips individuals with the skills, credentials, and connections to build real careers. From construction trades to tech, we partner with employers directly so training leads to placement — not just a certificate.</p>
      <ul>
        <li>Comprehensive job training programs in construction, tech, and logistics</li>
        <li>Job placement support and employer partnerships</li>
        <li>Career development and advancement resources</li>
        <li>Financial literacy and resume building</li>
        <li>Networking opportunities and mentorship</li>
      </ul>
      <div style="margin-top:var(--sp-3);">
        <a class="btn btn-primary" href="construction-cohort.html">Pre-Apprenticeship Construction cohort →</a>
      </div>
    </div>
    <div style="min-height:380px;background-image:url('img/programs-workforce.jpg');background-size:cover;background-position:center top"></div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">Who runs it</div>
      <h2>Practitioners, not just instructors.</h2>
      <p>Our workforce team includes credentialed trainers, industry-connected case managers, and employer partners who hire our graduates. We walk participants from intake through day one on the job — and stay in contact beyond.</p>
    </div>
    <div>
      <div class="eyebrow" style="color:var(--red);">Partners</div>
      <h3>Who we work with.</h3>
      <ul style="list-style:none;padding:0;">
        <li style="padding:8px 0;border-bottom:1px solid var(--line);">Local construction firms + trade unions</li>
        <li style="padding:8px 0;border-bottom:1px solid var(--line);">Chicago Cook Workforce Partnership</li>
        <li style="padding:8px 0;border-bottom:1px solid var(--line);">City Colleges of Chicago</li>
        <li style="padding:8px 0;">New Beginnings Church of Chicago</li>
      </ul>
    </div>
  </div>
</section>

<section class="section bg-red">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">2025 Impact</div>
    <h2 style="color:var(--white);">The numbers.</h2>
    <div class="stat-grid" style="margin-top:var(--sp-3);">
      <div class="stat"><div class="v">$19/hr</div><div class="l">average starting wage</div></div>
      <div class="stat"><div class="v">$19/hr</div><div class="l">average starting wage</div></div>
      <div class="stat"><div class="v">72%</div><div class="l">retained at 6 months</div></div>
      <div class="stat"><div class="v">Multiple</div><div class="l">trades + industries served</div></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--red);">Real Stories</div>
    <h2>When determination meets opportunity.</h2>
    <div class="card" style="margin-top:var(--sp-3);padding:0;overflow:hidden;">
      <div style="background:var(--red);padding:28px 32px;">
        <p style="color:var(--white);font-family:var(--font-display);font-size:1.6rem;line-height:1.3;margin:0;">&ldquo;Terrance didn&rsquo;t just walk through our doors looking for a job. He was searching for a new beginning.&rdquo;</p>
      </div>
      <div style="padding:28px 32px;">
        <p>A father determined to build a better life for his young son, <strong>Terrance H.</strong> enrolled in our Construction Training Program &mdash; and stood out from day one. His eagerness to learn, his consistency, and his commitment to growth made a lasting impression. Whether mastering new technical concepts or getting hands-on experience in the field, he approached every challenge with humility, focus, and drive.</p>
        <p>By graduation, Terrance had developed strong construction skills &mdash; and discovered a new sense of purpose and pride. That dedication led to a position with M. Cannon Roofing Company, and today he is a proud member of the <strong>Chicago Roofers Union</strong>, providing for his family and setting an example for others in the community.</p>
        <p style="margin-bottom:0;">His story has come full circle: Terrance is now using his skills to help build the roof of the Leadership &amp; Economic Opportunity Center &mdash; rising right here in Woodlawn.</p>
      </div>
    </div>
    <p style="margin-top:18px;color:var(--muted);font-size:14px;">More wins from this year: over <strong>100 neighbors hired on the spot</strong> at our UPS hiring event, a Construction Cohort tour of IBEW Local 130, and a pop-up build challenge at the Chicago Furniture Bank.</p>
  </div>
</section>

<section class="cta-strip">
  <div class="wrap">
    <h2>Ready to take the first step?</h2>
    <div class="btn-group">
      <a class="btn btn-yellow" href="https://projecthood.socialsolutionsportal.com/apricot-intake/0eb461e5-38a9-4ad1-9a4e-02bb3ee1414d" target="_blank" rel="noopener">Connect with us</a>
      <a class="btn btn-outline-light" href="https://projecthood.networkforgood.com/">Fund this pillar</a>
      <a class="btn btn-outline-light" href="partner.html">Become an employer partner</a>
    </div>
  </div>
</section>
"""

# -------- CONSTRUCTION PRE-APPRENTICESHIP COHORT --------
# Application block: embed the Google Form when a URL is set, otherwise show a
# contact fallback so the page never renders a broken iframe.
if CONSTRUCTION_COHORT_FORM_URL:
    _cc_embed_src = CONSTRUCTION_COHORT_FORM_URL
    if "embedded=true" not in _cc_embed_src:
        _cc_embed_src += ("&" if "?" in _cc_embed_src else "?") + "embedded=true"
    _cc_apply = f"""
    <div style="max-width:760px;margin:var(--sp-3) auto 0;">
      <iframe src="{_cc_embed_src}" width="100%" height="1100" frameborder="0" marginheight="0" marginwidth="0" style="border:0;background:var(--white);" title="Construction Pre-Apprenticeship application form">Loading the application…</iframe>
      <p style="font-size:13px;color:var(--muted);text-align:center;margin-top:12px;">Having trouble with the form? <a href="{CONSTRUCTION_COHORT_FORM_URL}" target="_blank" rel="noopener">Open it in a new tab →</a></p>
    </div>"""
else:
    _cc_apply = """
    <div class="card" style="max-width:640px;margin:var(--sp-3) auto 0;text-align:center;padding:32px;">
      <p style="margin-top:0;">Applications for the next cohort are handled by our workforce team. To be considered, reach out and we'll send you the application and next start date.</p>
      <a class="btn btn-primary" href="mailto:tawannacotten@projecthood.org?subject=Construction%20Pre-Apprenticeship%20Application" style="margin-top:6px;">Email to apply →</a>
      <p style="font-size:13px;color:var(--muted);margin-top:16px;margin-bottom:0;">Or call our office at <a href="tel:7739238270" style="color:var(--green);">773.923.8270</a>.</p>
    </div>"""

construction_cohort_body = f"""
<section class="hero bg-red">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">Workforce Development · Pre-Apprenticeship</div>
    <h1>Build a career in <span class="hl-yellow">construction.</span></h1>
    <p class="lead">A paid, hands-on pre-apprenticeship — in partnership with Illinois Works — that prepares Woodlawn residents to enter a U.S. Department of Labor apprenticeship or employment in the trades. All are welcome, especially people of color, women, and veterans.</p>
  </div>
</section>

<section class="section">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">The program</div>
      <h2>Our Construction Pre-Apprenticeship Training Program.</h2>
      <p>At Project H.O.O.D., we recognize the vital role economic empowerment plays in transforming lives and communities. For the past several years, our construction training program has helped aspiring individuals lay the foundation for a successful career in the dynamic world of construction.</p>
      <p>Sponsored by Illinois Works, our pre-apprenticeship program provides those with an interest in the construction industry hands-on training to prepare to enter a Department of Labor apprenticeship or employment — <strong>while being paid.</strong></p>
    </div>
    <div style="min-height:380px;background-image:url('img/programs-workforce.jpg');background-size:cover;background-position:center top"></div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow" style="color:var(--red);">What we offer</div>
      <h2>Skills, certifications, and a path.</h2>
      <p>In partnership with the State of Illinois, this comprehensive program equips participants with the essential skills and knowledge needed to excel across construction trades — from basic construction techniques to safety protocols and project management fundamentals.</p>
      <p>Led by experienced instructors and industry professionals, the hands-on approach builds technical proficiency alongside a strong work ethic, teamwork, and problem-solving. <strong>Upon completion, participants earn three certifications.</strong></p>
    </div>
    <div>
      <div class="eyebrow" style="color:var(--green);">Eligibility</div>
      <h3>Who can apply.</h3>
      <ul style="list-style:none;padding:0;">
        <li style="padding:10px 0;border-bottom:1px solid var(--line);">Be a minimum of 18 years of age</li>
        <li style="padding:10px 0;border-bottom:1px solid var(--line);">Have a high school diploma or GED equivalent</li>
        <li style="padding:10px 0;">Be a resident of Illinois</li>
      </ul>
      <p style="margin-top:18px;font-size:14px;"><a href="https://www.projecthood.org/s/PH-ILW-Info-Sheet-2024_Revised.docx" target="_blank" rel="noopener">Read about our curriculum (info sheet) →</a></p>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap" style="text-align:center;">
    <div class="eyebrow" style="color:var(--red);">Apply</div>
    <h2>Interested? Apply for the next cohort.</h2>
    <p style="font-size:var(--fs-lead);max-width:640px;margin:0 auto;color:var(--muted);">Complete the form below to be considered for our next start date. Questions? Reach out to Tawanna Cotten at <a href="mailto:tawannacotten@projecthood.org">tawannacotten@projecthood.org</a>.</p>
    {_cc_apply}
  </div>
</section>

<section class="cta-strip">
  <div class="wrap">
    <h2>More than one way in.</h2>
    <div class="btn-group">
      <a class="btn btn-yellow" href="workforce-development.html">All workforce programs</a>
      <a class="btn btn-outline-light" href="https://projecthood.socialsolutionsportal.com/apricot-intake/0eb461e5-38a9-4ad1-9a4e-02bb3ee1414d" target="_blank" rel="noopener">General intake</a>
      <a class="btn btn-outline-light" href="partner.html">Become an employer partner</a>
    </div>
  </div>
</section>
"""

# -------- PILLAR 3: HEALTH & WELLNESS --------
health_wellness_body = f"""
<section class="hero bg-purple">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">Programs · Pillar 3</div>
    <h1>Health. Access. <span class="hl-yellow">Community Care.</span></h1>
    <p class="lead">Free, quality healthcare for South Side residents of all ages — because where you live should never determine whether you can see a doctor.</p>
  </div>
</section>

<section class="section">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">What we do</div>
      <h2>Access to care. No barriers. No exceptions.</h2>
      <p>Healthcare shouldn't be a privilege. Our Health &amp; Wellness pillar addresses the full picture — physical health, mental health, emotional wellness, and social connection — with a special commitment to seniors and those who have historically been locked out of the healthcare system.</p>
      <ul>
        <li>Free medical screenings and health check-ups</li>
        <li>Access to care for uninsured and underinsured residents</li>
        <li>Senior programming, social engagement, and wellness support</li>
        <li>Mental health counseling and therapy</li>
        <li>Recovery navigation — individualized support for residents in recovery</li>
        <li>Group support circles and crisis response</li>
        <li>Referral network to ongoing care providers</li>
      </ul>
    </div>
    <div style="min-height:380px;background-image:url('img/programs-health-wellness.jpg');background-size:cover;background-position:center top"></div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--purple);">Partner Spotlight · Southside Free Clinic</div>
    <h2>Free medical care, right here in the neighborhood.</h2>
    <div class="grid-2" style="margin-top:var(--sp-3);align-items:center;gap:var(--sp-4);">
      <div>
        <p style="font-size:var(--fs-lead);">The <strong>Southside Free Clinic (SSFC)</strong> — a collaboration between the University of Chicago Pritzker School of Medicine, Project H.O.O.D., and Friend Health — brings free medical care directly to our community at New Beginnings Church. No insurance required. Walk-ins welcome.</p>
        <div style="margin:var(--sp-3) 0;display:flex;flex-direction:column;gap:12px;">
          <div style="display:flex;gap:14px;align-items:flex-start;">
            <span style="font-size:20px;">📍</span>
            <div><strong>New Beginnings Church</strong><br>6620 S. King Dr., Chicago, IL 60637</div>
          </div>
          <div style="display:flex;gap:14px;align-items:flex-start;">
            <span style="font-size:20px;">🗓</span>
            <div><strong>1st &amp; 3rd Sunday of each month</strong><br>12PM – 4PM · Walk-ins welcome</div>
          </div>
          <div style="display:flex;gap:14px;align-items:flex-start;">
            <span style="font-size:20px;">📞</span>
            <div><a href="tel:3127256648"><strong>312-725-6648</strong></a> · To schedule an appointment</div>
          </div>
          <div style="display:flex;gap:14px;align-items:flex-start;">
            <span style="font-size:20px;">🏥</span>
            <div>Patients referred to <strong>Friend Health</strong> at 6250 S. Cottage Grove for ongoing care</div>
          </div>
        </div>
        <div style="display:flex;gap:12px;flex-wrap:wrap;">
          <a class="btn btn-primary" href="tel:3127256648">Call to schedule</a>
          <a class="btn btn-outline" href="docs/ssfc-flyer-2025-2026.pdf" target="_blank" rel="noopener">Download flyer</a>
        </div>
        <div style="margin-top:var(--sp-3);border-radius:8px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,.12);">
          <iframe src="docs/ssfc-flyer-2025-2026.pdf" width="100%" height="620" style="display:block;border:none;" title="Southside Free Clinic flyer">
            <p>Your browser doesn't support embedded PDFs. <a href="docs/ssfc-flyer-2025-2026.pdf" target="_blank">Download the flyer here.</a></p>
          </iframe>
        </div>
      </div>
      <div style="background:#fff;border-radius:8px;padding:var(--sp-3);border:1px solid var(--line);">
        <p style="font-size:13px;text-transform:uppercase;letter-spacing:.08em;font-weight:700;color:var(--muted);margin-bottom:var(--sp-2);">Services offered</p>
        <ul style="list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:8px;">
          <li style="padding:10px 14px;background:var(--purple);color:#fff;border-radius:4px;font-weight:600;">Diabetes</li>
          <li style="padding:10px 14px;background:var(--purple);color:#fff;border-radius:4px;font-weight:600;">High Blood Pressure</li>
          <li style="padding:10px 14px;background:var(--purple);color:#fff;border-radius:4px;font-weight:600;">High Cholesterol</li>
          <li style="padding:10px 14px;background:var(--purple);color:#fff;border-radius:4px;font-weight:600;">General Health Check-Ups</li>
          <li style="padding:10px 14px;background:var(--purple);color:#fff;border-radius:4px;font-weight:600;">Rash / Allergies · Upset Stomach · Bodily Pain</li>
          <li style="padding:10px 14px;background:var(--bg);border-radius:4px;color:var(--muted);font-style:italic;">And more — walk-ins welcome</li>
        </ul>
        <p style="margin-top:12px;font-size:12px;color:var(--muted);">In collaboration with UChicago Pritzker School of Medicine &amp; Friend Health.</p>
      </div>
    </div>
  </div>
</section>

<section class="section bg-purple">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">2025 Impact</div>
    <h2 style="color:var(--white);">The numbers.</h2>
    <div class="stat-grid" style="margin-top:var(--sp-3);">
      <div class="stat"><div class="v">520</div><div class="l">counseling sessions delivered</div></div>
      <div class="stat"><div class="v">$0</div><div class="l">cost to participants</div></div>
      <div class="stat"><div class="v">Free</div><div class="l">SSFC clinic · 1st &amp; 3rd Sunday</div></div>
      <div class="stat"><div class="v">3</div><div class="l">partner organizations delivering care</div></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--purple);">Real Stories</div>
    <h2>Healing happens in community.</h2>
    <p class="lead" style="max-width:760px;">&ldquo;Recovery is not a destination &mdash; it&rsquo;s a journey best traveled together.&rdquo;</p>
    <p style="max-width:760px;">Every week, our <strong>Recovery in the H.O.O.D.</strong> meetings bring neighbors together to support one another, share their experiences, and find strength in community &mdash; a safe space for healing, accountability, and hope. No one has to walk the journey alone.</p>
    <p style="max-width:760px;">Wellness here isn&rsquo;t only about appointments. It&rsquo;s also our seniors gathering for Bingo Saturdays &mdash; fellowship, laughter, and connection that keep our elders rooted in the community they helped build.</p>
    <p style="max-width:760px;margin-top:var(--sp-2);"><a class="btn btn-outline" href="recovery.html">Explore Recovery in the H.O.O.D. &rarr;</a></p>
  </div>
</section>

<section class="cta-strip">
  <div class="wrap">
    <h2>Ready to take the first step?</h2>
    <div class="btn-group">
      <a class="btn btn-yellow" href="https://projecthood.socialsolutionsportal.com/apricot-intake/0eb461e5-38a9-4ad1-9a4e-02bb3ee1414d" target="_blank" rel="noopener">Connect with us</a>
      <a class="btn btn-outline-light" href="tel:3127256648">Call SSFC clinic</a>
      <a class="btn btn-outline-light" href="https://projecthood.networkforgood.com/">Fund this pillar</a>
    </div>
  </div>
</section>
"""

# -------- HEALTH & WELLNESS SUB-PAGE: RECOVERY --------
recovery_body = f"""
<section class="hero bg-purple">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">Health &amp; Wellness · Recovery</div>
    <h1>Recovery in the <span class="hl-yellow">H.O.O.D.</span></h1>
    <p class="lead">Recovery is not a destination &mdash; it&rsquo;s a journey best traveled together. Whatever you&rsquo;re carrying, you don&rsquo;t have to carry it alone. We walk with you, step by step.</p>
  </div>
</section>

<section class="section">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">What it is</div>
      <h2>A community that walks with you.</h2>
      <p>Recovery in the H.O.O.D. is a peer-led support community for neighbors working through addiction, trauma, and the hard road back to wholeness. It was built on a simple truth: healing happens faster, and lasts longer, when no one has to do it alone.</p>
      <p>Here you&rsquo;ll find people who understand &mdash; because many of them have walked the same road. There&rsquo;s no judgment and no cost. Just honest support, real accountability, and a room full of people pulling for you.</p>
      <p>We meet people wherever they are on the journey: someone taking a first tentative step, someone rebuilding after a setback, or someone years into recovery who wants to give back. Every story is welcome.</p>
    </div>
    <div style="display:flex;align-items:flex-start;">
      <img src="img/recovery-community.jpg" alt="Recovery in the H.O.O.D. participants together at Project H.O.O.D." style="width:100%;height:auto;border-radius:8px;display:block;">
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--purple);">How we gather</div>
    <h2>Weekly meetings. Monthly Speakerthons.</h2>
    <div class="grid-2" style="margin-top:var(--sp-3);gap:var(--sp-4);">
      <div style="background:#fff;border-radius:8px;padding:var(--sp-3);border:1px solid var(--line);">
        <div style="display:flex;gap:14px;align-items:flex-start;">
          <span style="font-size:22px;">🗓</span>
          <div>
            <h3 style="margin:0 0 6px;">Weekly meetings</h3>
            <p style="font-family:var(--font-display);letter-spacing:.06em;text-transform:uppercase;font-size:13px;color:var(--purple);font-weight:700;margin:0 0 8px;">Wednesdays · 4:30 PM · at Project H.O.O.D. · Free</p>
            <p style="margin:0;">Every Wednesday, our Recovery in the H.O.O.D. meetings bring neighbors together to support one another, share openly, and find strength in community &mdash; a safe space for healing, accountability, and hope. Come as you are.</p>
          </div>
        </div>
      </div>
      <div style="background:#fff;border-radius:8px;padding:var(--sp-3);border:1px solid var(--line);">
        <div style="display:flex;gap:14px;align-items:flex-start;">
          <span style="font-size:22px;">🎤</span>
          <div>
            <h3 style="margin:0 0 6px;">Monthly Speakerthons</h3>
            <p style="font-family:var(--font-display);letter-spacing:.06em;text-transform:uppercase;font-size:13px;color:var(--purple);font-weight:700;margin:0 0 8px;">One Saturday a month · 1:00 PM · at Project H.O.O.D. · Free</p>
            <p style="margin:0;">Once a month we host a Speakerthon &mdash; an open gathering where people in recovery share their testimonies out loud. These nights remind everyone in the room that change is possible and that recovery is worth fighting for.</p>
          </div>
        </div>
      </div>
    </div>
    <p style="margin-top:var(--sp-3);font-size:14px;color:var(--muted);">See upcoming dates and RSVP on our <a href="events.html">Community Calendar</a>, or <a href="tel:7739238270">call 773-923-8270</a>.</p>
  </div>
</section>

<section class="section">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow" style="color:var(--green);">Getting to treatment</div>
      <h2>Referrals &mdash; and a hand to hold along the way.</h2>
      <p>When someone needs more than peer support, we connect them to trusted treatment facilities and care providers. But we don&rsquo;t just hand you a phone number and wish you luck.</p>
      <p>We walk with you step by step &mdash; helping you understand your options, get to intake, navigate the paperwork, and stay connected through the ups and downs. Our goal isn&rsquo;t only to get you into treatment; it&rsquo;s to make sure you&rsquo;re still supported when you come home.</p>
    </div>
    <div>
      <div class="eyebrow" style="color:var(--purple);">The support</div>
      <h3>What walking with you looks like.</h3>
      <ul style="list-style:none;padding:0;">
        <li style="padding:10px 0;border-bottom:1px solid var(--line);">Referrals to trusted treatment facilities and providers</li>
        <li style="padding:10px 0;border-bottom:1px solid var(--line);">Step-by-step help getting to intake and through the paperwork</li>
        <li style="padding:10px 0;border-bottom:1px solid var(--line);">Weekly peer support meetings &amp; group circles</li>
        <li style="padding:10px 0;border-bottom:1px solid var(--line);">Monthly Speakerthons &mdash; testimony, encouragement, community</li>
        <li style="padding:10px 0;">Ongoing connection and accountability after treatment</li>
      </ul>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--purple);">In the community</div>
    <h2>Showing up for one another.</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:var(--sp-3);margin-top:var(--sp-3);">
      <figure style="margin:0;">
        <img src="img/recovery-gathering.jpg" alt="Neighbors gathered together at a Project H.O.O.D. community gathering" loading="lazy" style="width:100%;height:auto;border-radius:8px;display:block;">
        <figcaption style="font-size:13px;color:var(--muted);margin-top:8px;">Community and connection &mdash; no one walks alone.</figcaption>
      </figure>
      <figure style="margin:0;">
        <img src="img/recovery-outreach.jpg" alt="Project H.O.O.D. team members handing out supplies during neighborhood outreach" loading="lazy" style="width:100%;height:auto;border-radius:8px;display:block;">
        <figcaption style="font-size:13px;color:var(--muted);margin-top:8px;">Meeting neighbors where they are, out in the neighborhood.</figcaption>
      </figure>
    </div>
  </div>
</section>

<section class="cta-strip">
  <div class="wrap">
    <h2>Ready to take the first step?</h2>
    <p class="lead" style="max-width:var(--w-read);margin:12px auto var(--sp-2);">Reach out today. We&rsquo;ll meet you where you are and walk with you from there.</p>
    <div class="btn-group">
      <a class="btn btn-yellow" href="https://projecthood.socialsolutionsportal.com/apricot-intake/0eb461e5-38a9-4ad1-9a4e-02bb3ee1414d" target="_blank" rel="noopener">Connect with us</a>
      <a class="btn btn-outline-light" href="events.html">See meeting dates &amp; RSVP</a>
      <a class="btn btn-outline-light" href="tel:7739238270">Call 773-923-8270</a>
      <a class="btn btn-outline-light" href="health-wellness.html">Back to Health &amp; Wellness</a>
    </div>
  </div>
</section>
"""

# -------- PILLAR 4: YOUTH PROGRAMMING --------
youth_programming_body = f"""
<section class="hero bg-blue">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">Programs · Pillar 4</div>
    <h1>Entrepreneurship &amp; Youth <span class="hl-yellow">Enrichment.</span></h1>
    <p class="lead">Entrepreneurship training, after-school programs, mentorship, and enrichment — investing in who young people are becoming, not just where they are right now.</p>
  </div>
</section>

<section class="section">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">What we do</div>
      <h2>Investing in who they're becoming — not just where they are.</h2>
      <p>Project H.O.O.D.'s Youth Entrepreneurship and Enrichment programming is built on a simple belief: every young person in Woodlawn has something to offer. We create the environment to prove it — with real skills, real mentors, and real pathways forward.</p>
      <ul>
        <li>Entrepreneurship and business skill-building</li>
        <li>After-school tutoring and academic support</li>
        <li>Skills training and enrichment programs</li>
        <li>College and career readiness coaching</li>
        <li>Mentorship from community role models</li>
        <li>Summer internship placement</li>
      </ul>
    </div>
    <div style="min-height:380px;background-image:url('img/programs-youth.jpg');background-size:cover;background-position:center top"></div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">Who runs it</div>
      <h2>Coaches, mentors, and educators from the community.</h2>
      <p>Our youth team is made up of educators, coaches, and community mentors who show up consistently — building relationships that go beyond a single program. Young people who come through often return as mentors themselves.</p>
    </div>
    <div>
      <div class="eyebrow" style="color:var(--blue);">Partners</div>
      <h3>Who we work with.</h3>
      <ul style="list-style:none;padding:0;">
        <li style="padding:8px 0;border-bottom:1px solid var(--line);">Chicago Public Schools</li>
        <li style="padding:8px 0;border-bottom:1px solid var(--line);">Local entrepreneurship and workforce partners</li>
        <li style="padding:8px 0;border-bottom:1px solid var(--line);">Summer internship employers</li>
        <li style="padding:8px 0;">New Beginnings Church of Chicago</li>
      </ul>
    </div>
  </div>
</section>

<section class="section bg-blue">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">2025 Impact</div>
    <h2 style="color:var(--white);">The numbers.</h2>
    <div class="stat-grid" style="margin-top:var(--sp-3);">
      <div class="stat"><div class="v">380</div><div class="l">youth enrolled</div></div>
      <div class="stat"><div class="v">94%</div><div class="l">weekly attendance rate</div></div>
      <div class="stat"><div class="v">42</div><div class="l">placed in summer internships</div></div>
      <div class="stat"><div class="v">LEO</div><div class="l">Youth Enrichment Hub opening soon</div></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--blue);">Real Stories</div>
    <h2>Preparing the next generation.</h2>
    <p class="lead" style="max-width:760px;">This year, Project H.O.O.D. welcomed more than <strong>300 graduating high school seniors and their families</strong> at our annual Trunk Party &mdash; sending students into their next chapter with the dorm and college essentials they needed to succeed.</p>
    <p style="max-width:760px;">Throughout the year, our summer interns gained hands-on leadership experience in our offices and programs, and our Military Fair opened doors to careers, scholarships, and leadership training &mdash; reminding every young person that their future is bigger than their circumstances.</p>
  </div>
</section>

<section class="cta-strip">
  <div class="wrap">
    <h2>Ready to take the first step?</h2>
    <div class="btn-group">
      <a class="btn btn-yellow" href="https://projecthood.socialsolutionsportal.com/apricot-intake/0eb461e5-38a9-4ad1-9a4e-02bb3ee1414d" target="_blank" rel="noopener">Connect with us</a>
      <a class="btn btn-outline-light" href="https://projecthood.networkforgood.com/">Fund this pillar</a>
      <a class="btn btn-outline-light" href="get-involved.html">Volunteer</a>
    </div>
  </div>
</section>
"""

# -------- PILLAR 5: RE-ENTRY SERVICES --------
reentry_services_body = f"""
<section class="hero bg-yellow" style="color:var(--black);">
  <div class="wrap">
    <div class="eyebrow">Programs · Pillar 5</div>
    <h1>Building Bridges <span style="background:var(--black);color:var(--yellow);padding:0 6px;border-radius:4px;">to Success.</span></h1>
    <p class="lead" style="color:var(--ink);">Second chances are real here. We walk with individuals returning from incarceration through every step of reintegration — employment, housing, counseling, and belonging.</p>
  </div>
</section>

<section class="section">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">What we do</div>
      <h2>A pathway, not just a hand-off.</h2>
      <p>Our Re-Entry Services pillar is built on the belief that people deserve real second chances — and that means more than just a referral sheet. We provide comprehensive, wraparound support to individuals with justice involvement as they reintegrate into their communities and rebuild their lives.</p>
      <ul>
        <li>Job readiness training and career coaching</li>
        <li>Job placement and employer partnerships</li>
        <li>Housing navigation and support</li>
        <li>Individual counseling and case management</li>
        <li>Mentorship from people with lived experience</li>
        <li>Connection to community resources and referrals</li>
      </ul>
    </div>
    <div style="min-height:380px;background-image:url('img/programs-reentry.jpg');background-size:cover;background-position:center top"></div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">Who runs it</div>
      <h2>People who understand what returning home actually means.</h2>
      <p>Our re-entry team includes case managers, counselors, and mentors — many with lived experience of the justice system. They understand the real barriers returning citizens face and work to dismantle them one by one.</p>
    </div>
    <div>
      <div class="eyebrow" style="color:var(--green);">Partners</div>
      <h3>Who we work with.</h3>
      <ul style="list-style:none;padding:0;">
        <li style="padding:8px 0;border-bottom:1px solid var(--line);">Legal Aid Society (LAS)</li>
        <li style="padding:8px 0;border-bottom:1px solid var(--line);">Local housing and social service providers</li>
        <li style="padding:8px 0;border-bottom:1px solid var(--line);">Employer partners committed to fair chance hiring</li>
        <li style="padding:8px 0;">New Beginnings Church of Chicago</li>
      </ul>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--red);">Real Stories</div>
    <h2>The Rebirth Project: second chances, built two weeks at a time.</h2>
    <p class="lead" style="max-width:760px;">More than <strong>60% of formerly incarcerated people are still unemployed a year after release.</strong> Our graduates are beating those odds.</p>
    <p style="max-width:760px;">This year we celebrated our 3rd Re-Entry Cohort completing the Rebirth Project &mdash; a two-week immersive covering job skills, r&eacute;sum&eacute; building, workplace ethics, financial literacy, conflict resolution, emotional intelligence, and communication. At the finish, we hosted a job fair connecting graduates directly with employers eager to offer a real second chance.</p>
  </div>
</section>

<section class="section bg-black">
  <div class="wrap">
    <div class="testimonial">
      <blockquote>"When I came home, I didn't know where to start. Project H.O.O.D. helped me find a job, find a place to stay, and find myself again."</blockquote>
      <cite>— Re-entry participant</cite>
    </div>
  </div>
</section>

<section class="cta-strip">
  <div class="wrap">
    <h2>Ready to take the first step?</h2>
    <div class="btn-group">
      <a class="btn btn-yellow" href="https://docs.google.com/forms/d/14iVTtk2vXman0g1mQEH2LwJINUCQsfh1Jy5mmMRAhPQ/viewform" target="_blank" rel="noopener">Begin your journey</a>
      <a class="btn btn-outline-light" href="https://projecthood.networkforgood.com/">Fund this pillar</a>
      <a class="btn btn-outline-light" href="get-involved.html">Volunteer</a>
    </div>
  </div>
</section>
"""

# -------- IMPACT --------
impact_body = f"""
<section class="hero bg-black">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">News &amp; Impact</div>
    <h1>What <span class="hl-yellow">shows up</span> on the block.</h1>
    <p class="lead">The numbers behind the work in 2025 — served, placed, trained, fed, funded — plus the latest news and press from Woodlawn.</p>
  </div>
</section>

{ACRONYM_TAPE}

<section class="section">
  <div class="wrap">
    <div class="eyebrow">2025 at a glance</div>
    <h2>The numbers.</h2>
    <div class="stat-grid" style="margin-top:var(--sp-3);">
      <div class="stat accent-green"><div class="v">15,000+</div><div class="l">community members served</div></div>
      <div class="stat"><div class="v">2,000,000+ lbs</div><div class="l">food distributed</div></div>
      <div class="stat accent-red"><div class="v">$19/hr</div><div class="l">average starting wage for placements</div></div>
      <div class="stat"><div class="v">84%</div><div class="l">LEO Center capital campaign funded</div></div>
      <div class="stat accent-blue"><div class="v">140+</div><div class="l">violence incidents mediated</div></div>
      <div class="stat"><div class="v">380</div><div class="l">youth in education programs</div></div>
      <div class="stat"><div class="v">520</div><div class="l">mental health sessions delivered</div></div>
      <div class="stat accent-yellow"><div class="v">62</div><div class="l">small businesses coached</div></div>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap">
    <div class="eyebrow">Program outcomes</div>
    <h2>Where the work landed.</h2>
    <div class="grid-2" style="margin-top:var(--sp-3);">
      <div class="prog-card pg-green">
        <span class="tag tag-green">Violence Prevention</span>
        <h3>31% fewer gun homicides in 60637</h3>
        <p>Our outreach team mediated 140+ incidents and responded to 22 hospital bedside interventions. The 60637 ZIP saw a 31% reduction in gun homicides 2024→2025.</p>
      </div>
      <div class="prog-card">
        <span class="tag tag-red">Workforce Development</span>
        <h3>Job placements · 72% retained at 6 months</h3>
        <p>Construction trades, tech, and logistics. $19/hr average starting wage. 72% still employed with the same employer six months out.</p>
      </div>
      <div class="prog-card pg-blue">
        <span class="tag tag-blue">Youth Programming</span>
        <h3>380 youth · 94% attendance rate</h3>
        <p>Entrepreneurship training, tutoring, and mentorship. 94% weekly attendance. 42 youth placed in summer internships.</p>
      </div>
      <div class="prog-card pg-purple">
        <span class="tag tag-purple">Health &amp; Wellness</span>
        <h3>520 sessions · 0 cost to participants</h3>
        <p>Individual therapy, group work, and crisis response — entirely free to participants, funded by foundations + individual donors.</p>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="eyebrow">LEO Center progress</div>
    <h2>The building goes up with the dollars.</h2>
    <div style="margin-top:var(--sp-3);">
      <div class="progress" style="height:54px;">
        <div class="progress-fill" style="width:84%;font-size:18px;">$38M raised · 84% of $45M</div>
      </div>
    </div>
    <p style="margin-top:var(--sp-3);max-width:var(--w-read);">Groundbreaking was 2022. Target completion is 2027. Every dollar of the capital campaign goes directly to the build — no operating overhead, fully audited.</p>
    <div style="margin-top:22px;">
      <a class="btn btn-primary" href="leo-center.html">Learn about LEO Center</a>
    </div>
  </div>
</section>

<section class="section bg-black">
  <div class="wrap">
    <div class="testimonial">
      <blockquote>"I came in looking for a construction job. I left with a trade, a clean slate, and a plan. That's not a statistic — that's a life."</blockquote>
      <cite>— Workforce program graduate, 2025 cohort</cite>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap">
    <div class="eyebrow" style="margin-bottom:var(--sp-2);">In the news</div>
    <h2>What they're saying about us.</h2>
    <p style="max-width:var(--w-read);margin-top:8px;">Coverage of Project H.O.O.D. from local and national outlets — the stories others are telling about the work happening in Woodlawn.</p>
    <div class="grid-2" style="margin-top:var(--sp-3);">
      <div class="card card-accent" style="border-top-color:var(--green);">
        <div class="eyebrow">CBS Chicago · Violence Prevention</div>
        <h3>Project HOOD credited for Woodlawn violent crime drop.</h3>
        <p>Homicides in Woodlawn are down roughly 35%. Pastor Brooks and his outreach team — credible messengers from the community — are why.</p>
        <a href="https://www.cbsnews.com/chicago/news/violent-crime-woodlawn-project-hood/" target="_blank" rel="noopener" style="margin-top:auto;">Read on CBS Chicago →</a>
      </div>
      <div class="card card-accent" style="border-top-color:var(--blue);">
        <div class="eyebrow">ABC7 Chicago · Community</div>
        <h3>1,000 Men Unity Gathering: violence-free zone on the South Side.</h3>
        <p>Project HOOD convened more than 1,000 men to celebrate progress at the LEO Center and a growing violence-free zone in Woodlawn.</p>
        <a href="https://abc7chicago.com/post/1000-men-unity-gathering-celebrates-progress-project-hood-center-violence-free-zone-south-side/19121177/" target="_blank" rel="noopener" style="margin-top:auto;">Read on ABC7 →</a>
      </div>
      <div class="card card-accent" style="border-top-color:var(--red);">
        <div class="eyebrow">WGN-TV · Milestone</div>
        <h3>South Side nonprofit Project HOOD rings NYSE opening bell.</h3>
        <p>Project HOOD traveled to New York City to ring the New York Stock Exchange opening bell — a national stage for a South Side mission.</p>
        <a href="https://wgntv.com/news/chicago-news/project-hood-nyc-stock-exchange/" target="_blank" rel="noopener" style="margin-top:auto;">Read on WGN →</a>
      </div>
      <div class="card card-accent" style="border-top-color:var(--purple);">
        <div class="eyebrow">Fox News · Policy</div>
        <h3>Capitol Hill lawmakers visit Project H.O.O.D. — a "major step forward."</h3>
        <p>Members of Congress came to Woodlawn to see Project HOOD's community-driven violence interruption model firsthand.</p>
        <a href="https://www.foxnews.com/media/pastor-brooks-and-project-h-o-o-d-visited-by-capitol-hill-lawmakers-in-major-step-forward" target="_blank" rel="noopener" style="margin-top:auto;">Read on Fox News →</a>
      </div>
      <div class="card card-accent" style="border-top-color:var(--gold);">
        <div class="eyebrow">CBS Chicago · LEO Center</div>
        <h3>Project HOOD receives $8M donation toward new community center.</h3>
        <p>A major gift accelerates the $45M Robert R. McCormick Leadership &amp; Economic Opportunity Center at 66th &amp; King Drive.</p>
        <a href="https://www.cbsnews.com/chicago/news/project-hood-donation-community-center/" target="_blank" rel="noopener" style="margin-top:auto;">Read on CBS Chicago →</a>
      </div>
      <div class="card card-accent" style="border-top-color:var(--green);">
        <div class="eyebrow">Building Up Chicago · May 2024</div>
        <h3>First look inside the LEO Center construction in Woodlawn.</h3>
        <p>A deep-dive site visit into the 85,000 sq ft building rising at King Drive — what's going in each floor, and what it means for the neighborhood.</p>
        <a href="https://buildingupchicago.com/2024/05/02/robert-r-mccormick-leadership-economic-opportunity-center-construction/" target="_blank" rel="noopener" style="margin-top:auto;">Read on Building Up Chicago →</a>
      </div>
      <div class="card card-accent" style="border-top-color:var(--blue);">
        <div class="eyebrow">CBS Chicago · Workforce</div>
        <h3>LEO Center Offering Construction Training Program.</h3>
        <p>Project HOOD's Pre-Apprenticeship Construction cohort gives Woodlawn residents a direct path from training to union-track careers.</p>
        <a href="https://www.cbsnews.com/chicago/news/project-hood-construction-training-program/" target="_blank" rel="noopener" style="margin-top:auto;">Read on CBS Chicago →</a>
      </div>
      <div class="card card-accent" style="border-top-color:var(--red);">
        <div class="eyebrow">Chicago Crusader · Walk Across America</div>
        <h3>Pastor Corey Brooks walks across America for Project H.O.O.D.</h3>
        <p>Coverage from Chicago's oldest Black-owned newspaper of the cross-country walk that raised millions for Woodlawn's LEO Center.</p>
        <a href="https://chicagocrusader.com/pastor-corey-brooks-walks-across-america/" target="_blank" rel="noopener" style="margin-top:auto;">Read on Chicago Crusader →</a>
      </div>
    </div>
  </div>
</section>

<section class="cta-strip">
  <div class="wrap">
    <h2>Help us make 2026 bigger.</h2>
    <div class="btn-group">
      <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/">Donate</a>
      <a class="btn btn-outline-light" href="get-involved.html">Volunteer</a>
      <a class="btn btn-outline-light" href="annual-report.html">Read the 2025 Annual Report</a>
    </div>
  </div>
</section>
"""

# -------- SHARE THE FIRST LOOK (reusable) --------
social_share_section = """
<section class="section bg-black" id="share">
  <div class="wrap" style="max-width:820px;margin:0 auto;">
    <div class="eyebrow" style="color:var(--yellow);text-align:center;">The First Look</div>
    <h2 style="color:var(--white);text-align:center;margin-bottom:8px;">Spread the word.</h2>
    <p style="color:rgba(255,255,255,.8);text-align:center;font-size:var(--fs-lead);margin-bottom:var(--sp-4);">Got a photo from your tour? Post it. A moment with Pastor Brooks? Share it. Copy a caption below &mdash; it&rsquo;s ready to paste.</p>
    <div class="grid-2" style="gap:var(--sp-3);margin-bottom:var(--sp-4);">

      <div style="background:#1a1a1a;border:1px solid #333;border-radius:10px;padding:20px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="white"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.746l7.73-8.835L1.254 2.25H8.08l4.261 5.635L18.244 2.25zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
          <span style="color:var(--white);font-family:var(--font-display);font-size:12px;letter-spacing:.1em;text-transform:uppercase;">X &middot; Twitter</span>
        </div>
        <p style="color:rgba(255,255,255,.8);font-size:13px;line-height:1.75;font-family:var(--font-serif);margin-bottom:14px;" id="cap-x">Just got my First Look at the LEO Center in Woodlawn &mdash; 22,000 sq ft of opportunity going up on the South Side. So proud to support @ProjectHOOD &#x1F49B; #FirstLook #Woodlawn</p>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <button onclick="copyCaption('cap-x',this)" class="share-copy-btn">Copy caption</button>
          <a href="https://twitter.com/intent/tweet?text=Just%20got%20my%20First%20Look%20at%20the%20LEO%20Center%20in%20Woodlawn%20%E2%80%94%2022%2C000%20sq%20ft%20of%20opportunity%20going%20up%20on%20the%20South%20Side.%20So%20proud%20to%20support%20%40ProjectHOOD%20%F0%9F%92%9B%20%23FirstLook%20%23Woodlawn&url=https%3A//projecthood.org/first-look.html" target="_blank" rel="noopener" class="share-link-btn" style="color:var(--white);border-color:rgba(255,255,255,.4);">Post on X &rarr;</a>
        </div>
      </div>

      <div style="background:#1a1a1a;border:1px solid #333;border-radius:10px;padding:20px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="#1877F2"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
          <span style="color:var(--white);font-family:var(--font-display);font-size:12px;letter-spacing:.1em;text-transform:uppercase;">Facebook</span>
        </div>
        <p style="color:rgba(255,255,255,.8);font-size:13px;line-height:1.75;font-family:var(--font-serif);margin-bottom:14px;" id="cap-fb">I just got a First Look at the Leadership &amp; Economic Opportunity Center in Woodlawn, and I had to share it. Project H.O.O.D. is building 22,000 sq ft of workforce training, reentry support, youth programs, and health services &mdash; right on the block where they&rsquo;ve always shown up. I donated today. Every dollar stays in Woodlawn. &#x1F49B; #FirstLook #ProjectHOOD</p>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <button onclick="copyCaption('cap-fb',this)" class="share-copy-btn">Copy caption</button>
          <a href="https://www.facebook.com/sharer/sharer.php?u=https%3A//projecthood.org/first-look.html" target="_blank" rel="noopener" class="share-link-btn" style="color:#1877F2;border-color:#1877F2;">Share on Facebook &rarr;</a>
        </div>
      </div>

      <div style="background:#1a1a1a;border:1px solid #333;border-radius:10px;padding:20px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
          <svg width="18" height="18" viewBox="0 0 24 24"><defs><linearGradient id="ig" x1="0%" y1="100%" x2="100%" y2="0%"><stop offset="0%" stop-color="#f09433"/><stop offset="50%" stop-color="#dc2743"/><stop offset="100%" stop-color="#bc1888"/></linearGradient></defs><path fill="url(#ig)" d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
          <span style="color:var(--white);font-family:var(--font-display);font-size:12px;letter-spacing:.1em;text-transform:uppercase;">Instagram</span>
        </div>
        <p style="color:rgba(255,255,255,.8);font-size:13px;line-height:1.75;font-family:var(--font-serif);margin-bottom:14px;" id="cap-ig">Woodlawn&rsquo;s future is going up. &#x1F49B; Got a First Look at the LEO Center today &mdash; 22,000 sq ft for the community, right on the South Side. @projecthood has been here for years. Now they&rsquo;re building a home for it. Link in bio to give. #FirstLook #ProjectHOOD #Woodlawn #ChicagoSouthSide</p>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <button onclick="copyCaption('cap-ig',this)" class="share-copy-btn">Copy caption</button>
        </div>
        <p style="color:rgba(255,255,255,.4);font-size:11px;margin-top:8px;font-style:italic;">Copy, then open Instagram, start a new post, add your photo, and paste.</p>
      </div>

      <div style="background:#1a1a1a;border:1px solid #333;border-radius:10px;padding:20px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="#0A66C2"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
          <span style="color:var(--white);font-family:var(--font-display);font-size:12px;letter-spacing:.1em;text-transform:uppercase;">LinkedIn</span>
        </div>
        <p style="color:rgba(255,255,255,.8);font-size:13px;line-height:1.75;font-family:var(--font-serif);margin-bottom:14px;" id="cap-li">Had the privilege of touring the Leadership &amp; Economic Opportunity Center in Woodlawn today. Project H.O.O.D. &mdash; led by Pastor Corey Brooks &mdash; is building 22,000 sq ft of workforce development, reentry support, youth programming, and health services for one of Chicago&rsquo;s most resilient communities. I&rsquo;m proud to be a donor. If you&rsquo;re looking for an organization where your support makes a real local difference, I&rsquo;d encourage you to take a look. EIN: 45-3964886 | projecthood.networkforgood.com #FirstLook #ProjectHOOD #Woodlawn</p>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <button onclick="copyCaption('cap-li',this)" class="share-copy-btn">Copy caption</button>
          <a href="https://www.linkedin.com/sharing/share-offsite/?url=https%3A//projecthood.org/first-look.html" target="_blank" rel="noopener" class="share-link-btn" style="color:#0A66C2;border-color:#0A66C2;">Share on LinkedIn &rarr;</a>
        </div>
      </div>

    </div>

    <div style="background:rgba(245,183,0,.07);border:1px solid rgba(245,183,0,.2);border-radius:10px;padding:20px 24px;text-align:center;">
      <p style="color:var(--yellow);font-family:var(--font-display);font-size:12px;letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px;">&#x1F4F8; Got a photo from your tour?</p>
      <p style="color:rgba(255,255,255,.8);font-size:14.5px;font-family:var(--font-serif);margin:0;">A shot with Pastor Brooks, the construction site, or the community carries this story further. Copy a caption, add your photo, and post. Tag <strong style="color:var(--yellow);">@ProjectHOOD</strong> and <strong style="color:var(--yellow);">#FirstLook</strong> so we can reshare.</p>
    </div>
  </div>
</section>
<script>
function copyCaption(id,btn){var el=document.getElementById(id);var text=el?el.innerText:'';var done=function(){var o=btn.textContent;btn.textContent='Copied!';btn.style.background='#1A7A4A';btn.style.color='#fff';setTimeout(function(){btn.textContent=o;btn.style.background='';btn.style.color='';},2200);};if(navigator.clipboard){navigator.clipboard.writeText(text).then(done).catch(function(){var t=document.createElement('textarea');t.value=text;document.body.appendChild(t);t.select();document.execCommand('copy');document.body.removeChild(t);done();});}else{var t=document.createElement('textarea');t.value=text;document.body.appendChild(t);t.select();document.execCommand('copy');document.body.removeChild(t);done();}}
</script>
<style>.share-copy-btn{background:var(--yellow);color:#111;border:none;padding:9px 16px;border-radius:6px;font-family:var(--font-display);font-size:12px;letter-spacing:.06em;text-transform:uppercase;cursor:pointer;font-weight:700;}.share-link-btn{background:transparent;padding:9px 16px;border-radius:6px;border:1px solid;font-family:var(--font-display);font-size:12px;letter-spacing:.06em;text-transform:uppercase;text-decoration:none;display:inline-block;}</style>
"""


# -------- LEO CENTER --------
leo_body = f"""
<!-- HERO -->
<section class="hero bg-black" style="padding-bottom:var(--sp-3);">
  <div class="wrap" style="text-align:center;max-width:820px;">
    <div class="eyebrow" style="color:var(--yellow);letter-spacing:.12em;">Opening Fall 2026 · Woodlawn, Chicago</div>
    <h1>The <span class="hl-yellow">LEO Center.</span> Built for the South Side.</h1>
    <p class="lead" style="margin-left:auto;margin-right:auto;">The Robert R. McCormick Leadership &amp; Economic Opportunity Center — 90,000 sq ft on S. King Drive, opening Fall 2026. Every Project H.O.O.D. program, one permanent address.</p>
    <div style="margin-top:22px;display:flex;gap:12px;flex-wrap:wrap;justify-content:center;">
      <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/projects/301372-2026-brick-by-brick-campaign">Brick by Brick →</a>
      <a class="btn btn-outline-light" href="https://projecthood.networkforgood.com/">Fund the build</a>
    </div>
  </div>
</section>

<!-- RENDERING SHOWCASE (full-bleed) -->
<section style="padding:0;background:var(--black);">
  <img src="img/leo-center-rendering.jpg" alt="Architectural rendering of the LEO Center — 90,000 sq ft on S. King Drive, Woodlawn" style="width:100%;display:block;">
  <div style="text-align:center;padding:14px 20px;color:rgba(255,255,255,.8);font-family:var(--font-serif);font-style:italic;font-size:14px;">A rendering of the Robert R. McCormick Leadership &amp; Economic Opportunity Center, rising now in Woodlawn.</div>
</section>

<!-- OPENING ANNOUNCEMENT BANNER -->
<section style="background:var(--yellow);padding:28px 24px;text-align:center;">
  <div style="max-width:800px;margin:0 auto;">
    <p style="font-family:var(--font-display);font-size:clamp(18px,3vw,26px);font-weight:700;color:var(--black);letter-spacing:.04em;margin:0;">
      🏗 Construction is underway — the LEO Center opens <strong>Fall 2026.</strong>
    </p>
    <p style="font-size:15px;color:var(--black);margin:8px 0 0;opacity:.75;">6621 S. King Drive, Chicago, IL 60637 · The heart of Woodlawn</p>
  </div>
</section>

<!-- FUNDING PROGRESS -->
<section class="section bg-offwhite">
  <div class="wrap" style="text-align:center;">
    <div class="eyebrow">Capital Campaign · Robert R. McCormick Foundation Lead Gift</div>
    <h2>$45M goal. <span style="background:var(--black);color:var(--yellow);padding:2px 12px;border-radius:2px;">Almost there.</span></h2>
    <div style="max-width:760px;margin:var(--sp-3) auto 0;">
      <div class="progress" style="height:56px;border-radius:4px;">
        <div class="progress-fill" style="width:84%;font-size:17px;border-radius:4px 0 0 4px;">$38M raised · 84%</div>
      </div>
      <p style="font-size:14px;color:var(--muted);margin-top:10px;">$7M remaining · Every dollar goes directly to the build</p>
    </div>
    <div style="margin-top:var(--sp-3);display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
      <a class="btn btn-primary" href="https://projecthood.networkforgood.com/">Give to the build</a>
      <a class="btn btn-outline" href="https://projecthood.networkforgood.com/projects/301372-2026-brick-by-brick-campaign">Buy a brick</a>
    </div>
  </div>
</section>

<!-- CONSTRUCTION TIMELINE -->
<section class="section">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--green);">Construction Progress</div>
    <h2>From rooftop to ribbon cutting.</h2>
    <p style="max-width:var(--w-read);font-size:var(--fs-lead);margin-bottom:var(--sp-3);">Pastor Brooks sat on a rooftop for 100 days in winter to raise the first dollars. Now steel is going up on King Drive. Here's where we stand.</p>
    <div style="display:grid;gap:0;max-width:680px;">
      <!-- Timeline item -->
      <div style="display:flex;gap:20px;align-items:flex-start;padding-bottom:32px;position:relative;">
        <div style="flex-shrink:0;width:44px;height:44px;border-radius:50%;background:var(--green);display:flex;align-items:center;justify-content:center;font-size:18px;color:#fff;font-weight:700;z-index:1;">✓</div>
        <div style="position:absolute;left:22px;top:44px;width:2px;height:calc(100% - 12px);background:var(--line);"></div>
        <div>
          <div style="font-weight:700;font-size:13px;color:var(--green);text-transform:uppercase;letter-spacing:.06em;">2021 · Complete</div>
          <h4 style="margin:4px 0 6px;">Rooftop Campaign</h4>
          <p style="color:var(--muted);font-size:14px;margin:0;">Pastor Brooks camped on a Woodlawn rooftop for 100 days — raising awareness and the first major capital dollars. The city took notice.</p>
        </div>
      </div>
      <div style="display:flex;gap:20px;align-items:flex-start;padding-bottom:32px;position:relative;">
        <div style="flex-shrink:0;width:44px;height:44px;border-radius:50%;background:var(--green);display:flex;align-items:center;justify-content:center;font-size:18px;color:#fff;font-weight:700;z-index:1;">✓</div>
        <div style="position:absolute;left:22px;top:44px;width:2px;height:calc(100% - 12px);background:var(--line);"></div>
        <div>
          <div style="font-weight:700;font-size:13px;color:var(--green);text-transform:uppercase;letter-spacing:.06em;">2022 · Complete</div>
          <h4 style="margin:4px 0 6px;">Groundbreaking</h4>
          <p style="color:var(--muted);font-size:14px;margin:0;">Official groundbreaking at 6620 S. King Drive. The Robert R. McCormick Foundation named the building. Land owned by Project H.O.O.D.</p>
        </div>
      </div>
      <div style="display:flex;gap:20px;align-items:flex-start;padding-bottom:32px;position:relative;">
        <div style="flex-shrink:0;width:44px;height:44px;border-radius:50%;background:var(--green);display:flex;align-items:center;justify-content:center;font-size:18px;color:#fff;font-weight:700;z-index:1;">✓</div>
        <div style="position:absolute;left:22px;top:44px;width:2px;height:calc(100% - 12px);background:var(--line);"></div>
        <div>
          <div style="font-weight:700;font-size:13px;color:var(--green);text-transform:uppercase;letter-spacing:.06em;">2024–2025 · Complete</div>
          <h4 style="margin:4px 0 6px;">Foundation &amp; Steel</h4>
          <p style="color:var(--muted);font-size:14px;margin:0;">Foundation poured. Steel erected. Construction training crews — Project H.O.O.D. program graduates — worked the site. The walk from Chicago to New York raised final capital.</p>
        </div>
      </div>
      <div style="display:flex;gap:20px;align-items:flex-start;padding-bottom:32px;position:relative;">
        <div style="flex-shrink:0;width:44px;height:44px;border-radius:50%;background:var(--yellow);display:flex;align-items:center;justify-content:center;font-size:20px;z-index:1;">🔨</div>
        <div style="position:absolute;left:22px;top:44px;width:2px;height:calc(100% - 12px);background:var(--line);"></div>
        <div>
          <div style="font-weight:700;font-size:13px;color:var(--yellow);text-transform:uppercase;letter-spacing:.06em;">2026 · In Progress Now</div>
          <h4 style="margin:4px 0 6px;">Interior Buildout</h4>
          <p style="color:var(--muted);font-size:14px;margin:0;">Classrooms, health suites, cafe and teaching kitchen, multipurpose hall — every space being finished for fall opening. Final $13.5M is the last mile.</p>
        </div>
      </div>
      <div style="display:flex;gap:20px;align-items:flex-start;">
        <div style="flex-shrink:0;width:44px;height:44px;border-radius:50%;background:var(--black);border:2px solid var(--yellow);display:flex;align-items:center;justify-content:center;font-size:18px;color:var(--yellow);font-weight:700;z-index:1;">★</div>
        <div>
          <div style="font-weight:700;font-size:13px;color:var(--yellow);text-transform:uppercase;letter-spacing:.06em;">Fall 2026 · Target Opening</div>
          <h4 style="margin:4px 0 6px;">Ribbon Cutting</h4>
          <p style="color:var(--muted);font-size:14px;margin:0;">The LEO Center opens its doors to Woodlawn. Programming begins. The Walkway of Destiny carries the names of everyone who helped make it real.</p>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- VIDEO -->
<section class="section bg-offwhite">
  <div class="wrap" style="max-width:900px;">
    <div class="eyebrow" style="text-align:center;">See it</div>
    <h2 style="text-align:center;margin-bottom:var(--sp-3);">Watch the LEO Center come to life.</h2>
    <div style="position:relative;width:100%;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:8px;box-shadow:0 8px 32px rgba(0,0,0,.18);">
      <iframe
        src="https://www.youtube.com/embed/NHNPy5tFCiw"
        title="LEO Center — Leadership &amp; Economic Opportunity Center"
        frameborder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen
        style="position:absolute;top:0;left:0;width:100%;height:100%;border-radius:8px;">
      </iframe>
    </div>
  </div>
</section>

<!-- WHAT'S INSIDE -->
<section class="section">
  <div class="wrap grid-2" style="align-items:center;gap:var(--sp-4);">
    <div>
      <div class="eyebrow">What it is</div>
      <h2>One building. Five pillars. One neighborhood.</h2>
      <p style="font-size:var(--fs-lead);">The LEO Center brings every Project H.O.O.D. program under one roof — workforce training classrooms, a youth enrichment hub, health and wellness suites, a business incubator, re-entry services, outreach team offices, a cafe, teaching kitchen, and ghost kitchen, and a 400-seat multipurpose hall featuring a full-fledged, state-of-the-art performing arts theatre.</p>
      <p>It's being built on land owned by Project H.O.O.D., directly on S. King Drive — a deliberate statement that serious investment belongs on the South Side.</p>
    </div>
    <div style="min-height:360px;background-image:url('img/leo-center-floorplan.jpg');background-size:cover;background-position:center"></div>
  </div>
</section>

<!-- 6 FEATURE CARDS -->
<section class="section bg-offwhite">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--green);">Inside the LEO</div>
    <h2>What 90,000 sq ft makes possible.</h2>
    <div class="grid-3" style="margin-top:var(--sp-3);">
      <div class="card card-accent"><h3>Workforce Training Wing</h3><p>Automotive, carpentry, woodworking, and welding trade training, plus a makerspace for 3D printing, laser etching, and textile work, OSHA certification, and direct-hire employer partners — where real careers begin. Average starting wage: $19/hr.</p></div>
      <div class="card card-accent" style="border-top-color:var(--blue);"><h3>Youth Enrichment Hub</h3><p>Entrepreneurship training, after-school programs, tutoring, mentorship, and college and career readiness — all under one roof.</p></div>
      <div class="card card-accent" style="border-top-color:var(--purple);"><h3>Health &amp; Wellness Center</h3><p>Primary care delivered by Friend Health (FQHC) and the South Side Free Clinic, in partnership with the University of Chicago&rsquo;s Pritzker School of Medicine — plus counseling suites, senior services, recovery navigation, and crisis response. No insurance required.</p></div>
      <div class="card card-accent" style="border-top-color:#8a6d00;"><h3>Business Incubator</h3><p>Co-working space for Woodlawn entrepreneurs, grant writing support, and legal and financial clinic — growing local ownership.</p></div>
      <div class="card card-accent" style="border-top-color:var(--green);"><h3>Cafe &amp; Teaching Kitchen</h3><p>A community cafe, a hands-on teaching kitchen for culinary training, and a ghost kitchen supporting food entrepreneurs — the table is always set for the neighborhood.</p></div>
      <div class="card card-accent" style="border-top-color:var(--black);"><h3>400-Seat Multipurpose Hall</h3><p>A full-fledged, state-of-the-art performing arts theatre — town halls, graduations, concerts, and community events, in a venue built for Woodlawn, by Woodlawn.</p></div>
    </div>
  </div>
</section>

<!-- QUOTE -->
<section class="section bg-black">
  <div class="wrap">
    <div class="testimonial" style="border-left-color:var(--yellow);">
      <blockquote>"The LEO Center isn't a building. It's proof that investment belongs here too. When it opens, we stop having to ask for permission."</blockquote>
      <cite>— Pastor Corey B. Brooks, Executive Director, Project H.O.O.D.</cite>
    </div>
  </div>
</section>

<!-- LOCATION / MAP -->
<section class="section bg-offwhite">
  <div class="wrap">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--sp-4);align-items:center;flex-wrap:wrap;">
      <div>
        <div class="eyebrow">Where we're building</div>
        <h2>6621 S. King Drive</h2>
        <p style="font-size:var(--fs-lead);">The LEO Center sits at the heart of Woodlawn — on land Project H.O.O.D. owns, on a block we've served for over a decade. This is intentional.</p>
        <ul style="list-style:none;padding:0;margin:var(--sp-2) 0 0;">
          <li style="padding:10px 0;border-bottom:1px solid var(--line);font-size:15px;"><strong>Address:</strong> 6621 S. King Drive, Chicago, IL 60637</li>
          <li style="padding:10px 0;border-bottom:1px solid var(--line);font-size:15px;"><strong>Neighborhood:</strong> Woodlawn, Chicago's South Side</li>
          <li style="padding:10px 0;border-bottom:1px solid var(--line);font-size:15px;"><strong>Transit:</strong> CTA Green Line — Cottage Grove stop · Multiple bus routes</li>
          <li style="padding:10px 0;font-size:15px;"><strong>Parking:</strong> On-site and street parking available</li>
        </ul>
        <div style="margin-top:var(--sp-2);">
          <a class="btn btn-outline" href="https://maps.google.com/?q=6621+S+King+Drive,+Chicago,+IL+60637" target="_blank" rel="noopener">Get directions →</a>
        </div>
      </div>
      <div style="border-radius:8px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.12);min-height:320px;">
        <iframe
          src="https://maps.google.com/maps?q=6621+S+King+Drive,+Chicago,+IL+60637&z=16&output=embed"
          width="100%"
          height="320"
          style="border:0;display:block;"
          allowfullscreen=""
          loading="lazy"
          referrerpolicy="no-referrer-when-downgrade"
          title="LEO Center location — 6621 S. King Drive, Woodlawn, Chicago">
        </iframe>
      </div>
    </div>
  </div>
</section>

<!-- BRICK BY BRICK CTA -->
<section class="section bg-black" style="color:var(--white);">
  <div class="wrap grid-2" style="align-items:center;gap:var(--sp-4);">
    <div>
      <div class="eyebrow" style="color:var(--yellow);">Brick by Brick · 2026 Capital Campaign</div>
      <h2 style="color:var(--white);">Leave your name in the foundation.</h2>
      <p style="font-size:var(--fs-lead);opacity:.9;">Every brick in the LEO Center's Walkway of Destiny carries the name of someone who believed in Chicago's South Side — before the rest of the world caught up.</p>
      <p style="opacity:.85;margin-top:12px;">Long after the ribbon is cut, families will walk across these names. Young people will step into new futures because of the foundation you helped build. This is your chance to leave more than a donation — it's a legacy engraved in stone.</p>
      <div style="margin-top:var(--sp-3);display:flex;gap:12px;flex-wrap:wrap;">
        <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/projects/301372-2026-brick-by-brick-campaign" target="_blank" rel="noopener">Claim your brick →</a>
        <a class="btn btn-outline-light" href="https://projecthood.networkforgood.com/">Any amount</a>
      </div>
    </div>
    <div>
      <div class="card" style="background:var(--white);color:var(--black);border:none;">
        <div class="eyebrow" style="color:var(--muted);">Named-gift levels</div>
        <ul style="list-style:none;padding:0;margin-top:12px;">
          <li style="padding:14px 0;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;"><span><strong>Cornerstone</strong><br><small style="color:var(--muted);">Name a program room</small></span><span style="font-weight:700;font-size:18px;">$100K+</span></li>
          <li style="padding:14px 0;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;"><span><strong>Builder</strong><br><small style="color:var(--muted);">Walkway of Destiny — large brick</small></span><span style="font-weight:700;font-size:18px;">$25K</span></li>
          <li style="padding:14px 0;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;"><span><strong>Foundation</strong><br><small style="color:var(--muted);">Walkway of Destiny — brick</small></span><span style="font-weight:700;font-size:18px;">$5K</span></li>
          <li style="padding:14px 0;display:flex;justify-content:space-between;align-items:center;"><span><strong>Block by Block</strong><br><small style="color:var(--muted);">Recognition in LEO honor wall</small></span><span style="font-weight:700;font-size:18px;">Any amount</span></li>
        </ul>
        <a class="btn btn-primary" href="https://projecthood.networkforgood.com/projects/301372-2026-brick-by-brick-campaign" target="_blank" rel="noopener" style="width:100%;text-align:center;margin-top:8px;">Give now →</a>
      </div>
    </div>
  </div>
</section>

<!-- FINAL CTA -->
<section class="cta-strip">
  <div class="wrap">
    <h2>Opening <span class="hl-yellow">Fall 2026.</span> Help close the last mile.</h2>
    <p style="max-width:620px;margin:0 auto var(--sp-3);opacity:.95;">The building is rising. The finish line is in sight. Every gift — at every level — gets us there. Don't let someone else write this part of the story without you.</p>
    <div class="btn-group">
      <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/projects/301372-2026-brick-by-brick-campaign">Brick by Brick →</a>
      <a class="btn btn-outline-light" href="https://projecthood.networkforgood.com/">Fund the build</a>
      <a class="btn btn-outline-light" href="contact.html">Name a space</a>
    </div>
  </div>
</section>
{social_share_section}
"""

# -------- CAMPAIGNS (WAA) --------
campaigns_body = f"""
<section class="hero bg-black">
  <div class="wrap">
    <div class="hero-split">
      <div>
        <div class="eyebrow" style="color:var(--yellow);">Campaigns · 2026</div>
        <h1>Walk With <span class="hl-yellow">Us!</span></h1>
        <p class="lead">What started as Pastor Brooks' 900-mile walk from Chicago to New York has grown into a nationwide movement. Walk With Us! invites people everywhere to raise $25M for mentorship, youth development, violence prevention, and the LEO Center.</p>
        <div style="margin-top:22px;display:flex;gap:12px;flex-wrap:wrap;">
          <a class="btn btn-yellow" href="https://tiltify.com/project-hood/walk-across-america-2025">Give to the movement</a>
          <a class="btn btn-outline-light" href="https://tiltify.com/project-hood/walk-across-america-2025">Start a team</a>
        </div>
      </div>
      <img src="img/campaign-walk-poster.png" alt="Walk With Us! — The Movement" style="width:100%;border-radius:8px;display:block;">
    </div>
  </div>
</section>

<section class="section bg-yellow">
  <div class="wrap" style="text-align:center;">
    <div class="eyebrow">The goal</div>
    <h2>$25 million. <span style="background:var(--black);color:var(--yellow);padding:2px 12px;">Every dollar audited.</span></h2>
    <div style="max-width:720px;margin:var(--sp-3) auto 0;">
      <p style="font-size:var(--fs-lead);">Funds go directly to mentorship, youth development, violence prevention, leadership training, education, and economic opportunity — through Project H.O.O.D. and the LEO Center.</p>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">Where it started</div>
      <h2>900 miles. One community. One movement.</h2>
      <p>In 2025, Pastor Brooks walked from Chicago to New York — 900+ miles — to put the South Side on the map and raise the final dollars for the LEO Center. That walk is over. The movement isn't.</p>
      <p>Walk With Us! invites communities across America to keep carrying the mission forward: walks, church activations, volunteer days, and prayer gatherings — everywhere people are ready to step up.</p>
    </div>
    <div style="position:relative;width:100%;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:8px;box-shadow:0 8px 32px rgba(0,0,0,.15);">
      <iframe
        src="https://www.youtube.com/embed/IgEwyLIYv7g"
        title="WALK WITH US! | Official Trailer — Project H.O.O.D."
        frameborder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen
        style="position:absolute;top:0;left:0;width:100%;height:100%;border-radius:8px;">
      </iframe>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap">
    <div class="eyebrow">Three ways in</div>
    <h2>Give. Walk. Start a team.</h2>
    <div class="grid-3" style="margin-top:var(--sp-3);">
      <div class="card card-accent"><h3>Give</h3><p>One-time or monthly gift supporting youth, families, and the LEO Center. Every dollar audited.</p><a class="btn btn-primary" href="https://tiltify.com/project-hood/walk-across-america-2025" style="align-self:flex-start;margin-top:12px;">Give on Tiltify →</a></div>
      <div class="card card-accent" style="border-top-color:var(--blue);"><h3>Organize a walk</h3><p>Host a community walk in your city, congregation, or neighborhood. Fundraise together on Tiltify.</p><a class="btn btn-primary" href="https://tiltify.com/project-hood/walk-across-america-2025" style="align-self:flex-start;margin-top:12px;">See teams →</a></div>
      <div class="card card-accent" style="border-top-color:var(--green);"><h3>Start your own team</h3><p>Rally your company, congregation, or crew. Create a team page in 2 minutes on Tiltify.</p><a class="btn btn-primary" href="https://tiltify.com/project-hood/walk-across-america-2025" style="align-self:flex-start;margin-top:12px;">Create a team →</a></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div style="max-width:680px;margin:0 auto;text-align:center;">
      <div class="eyebrow" style="color:var(--red);">Join the movement</div>
      <h2>Sign up to Walk With Us!</h2>
      <p style="font-size:var(--fs-lead);color:var(--muted);">Tell us you're in — and we'll get you your Walk With Us! gear and keep you connected to the campaign.</p>
    </div>
    <!-- GOOGLE FORM LINK — run create_ph_forms.gs → createAllForms() → copy "Walk With Us!" URL → replace href below -->
    <div style="max-width:640px;margin:var(--sp-3) auto 0;text-align:center;">
      <a class="btn btn-yellow" href="https://docs.google.com/forms/d/e/1FAIpQLSck9_hs4mHhfUNDnAWs3N2e0mqBx4VioqBHj3SzvXBXqRMUyA/viewform" target="_blank" rel="noopener" style="font-size:17px;padding:16px 40px;display:inline-block;">Count me in →</a>
      <p style="font-size:13px;color:var(--muted);margin-top:14px;">Opens a short Google Form — takes 60 seconds.</p>
    </div>
  </div>
</section>

<section class="section bg-black">
  <div class="wrap testimonial" style="border-left-color:var(--yellow);">
    <blockquote>"They told me I was crazy to walk from Chicago to New York. I told them I was crazy to watch another kid get buried."</blockquote>
    <cite>— Pastor Corey B. Brooks</cite>
  </div>
</section>

<!-- BRICK BY BRICK -->
<section class="section bg-black" style="color:var(--white);">
  <div class="wrap grid-2" style="align-items:center;gap:var(--sp-4);">
    <div>
      <div class="eyebrow" style="color:var(--yellow);">Capital Campaign · LEO Center</div>
      <h2 style="color:var(--white);">Brick by Brick.</h2>
      <p style="font-size:var(--fs-lead);opacity:.9;">Get your name engraved in history. Every brick in the LEO Center's Walkway of Destiny represents someone who believed in Chicago's South Side — before the rest of the world caught up.</p>
      <p style="opacity:.85;margin-top:12px;">Long after the ribbon is cut, families will walk across these names. Young people will step into new futures because of the foundation you helped build. This is your chance to leave more than a donation — it's a legacy engraved in stone.</p>
      <div style="margin-top:var(--sp-3);display:flex;gap:12px;flex-wrap:wrap;">
        <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/projects/301372-2026-brick-by-brick-campaign" target="_blank" rel="noopener">Claim your brick →</a>
      </div>
    </div>
    <div>
      <div class="card" style="background:var(--white);color:var(--black);border:none;">
        <div class="eyebrow" style="color:var(--muted);">Named-gift levels</div>
        <ul style="list-style:none;padding:0;margin-top:12px;">
          <li style="padding:16px 0;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;">
            <div><strong>Legacy Brick</strong><p style="font-size:13px;color:var(--muted);margin:2px 0 0;">Prime placement · engraved name</p></div>
            <span style="font-size:1.3rem;font-weight:700;color:var(--green);">$10,000</span>
          </li>
          <li style="padding:16px 0;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;">
            <div><strong>Heritage Brick</strong><p style="font-size:13px;color:var(--muted);margin:2px 0 0;">Engraved name · permanent placement</p></div>
            <span style="font-size:1.3rem;font-weight:700;color:var(--green);">$5,000</span>
          </li>
          <li style="padding:16px 0;display:flex;justify-content:space-between;align-items:center;">
            <div><strong>Foundation Brick</strong><p style="font-size:13px;color:var(--muted);margin:2px 0 0;">Engraved name · lasting legacy</p></div>
            <span style="font-size:1.3rem;font-weight:700;color:var(--green);">$2,500</span>
          </li>
        </ul>
        <a class="btn btn-primary" href="https://projecthood.networkforgood.com/projects/301372-2026-brick-by-brick-campaign" target="_blank" rel="noopener" style="width:100%;text-align:center;margin-top:16px;">Choose your brick →</a>
      </div>
    </div>
  </div>
</section>
"""

# -------- GET INVOLVED HUB --------
gi_body = f"""
<section class="hero bg-red">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">Help Somebody</div>
    <h1>Three ways to <span class="hl-yellow">help somebody today.</span></h1>
    <p class="lead">Give, volunteer, or partner. Each one matters — start with whichever you can bring today.</p>
  </div>
</section>

<section class="section">
  <div class="wrap grid-3">
    <div class="prog-card" style="border-left-color:var(--red);">
      <span class="tag tag-red">Give</span>
      <h3 style="margin-top:12px;">Donate securely.</h3>
      <p>Give one-time or monthly through NetworkForGood, our partner platform since day one. Your gift stays in Woodlawn.</p>
      <a class="btn btn-primary" href="donate.html" style="align-self:flex-start;margin-top:auto;">Donate →</a>
    </div>
    <div class="prog-card pg-green">
      <span class="tag tag-green">Volunteer</span>
      <h3 style="margin-top:12px;">Show up in person.</h3>
      <p>We recruit for specific events, cohorts, and program support. Sign up on our volunteer form — we'll match you to a need.</p>
      <a class="btn btn-secondary" href="volunteer.html" style="align-self:flex-start;margin-top:auto;">Volunteer →</a>
    </div>
    <div class="prog-card pg-blue">
      <span class="tag tag-blue">Partner</span>
      <h3 style="margin-top:12px;">Build with us.</h3>
      <p>Corporate partnerships, church collaborations, employer pipelines, grant partners. Let's find the fit.</p>
      <a class="btn btn-outline" href="partner.html" style="align-self:flex-start;margin-top:auto;">Partner →</a>
    </div>
  </div>
</section>

<!-- PARTICIPANT INTAKE — prominent standalone section -->
<section class="section bg-black" id="apply">
  <div class="wrap" style="max-width:720px;margin:0 auto;text-align:center;">
    <div class="eyebrow" style="color:var(--yellow);">Here when you're ready.</div>
    <h2 style="color:var(--white);">Connect with us.</h2>
    <p style="color:rgba(255,255,255,.9);font-size:var(--fs-lead);margin-bottom:var(--sp-3);">One application puts you in the system — our intake team routes you to the right program (workforce, violence prevention, health &amp; wellness, youth, re-entry) and follows up within 2 business days. Free, confidential, no judgment.</p>
    <a class="btn btn-yellow" style="font-size:15px;padding:16px 36px;" href="https://projecthood.socialsolutionsportal.com/apricot-intake/0eb461e5-38a9-4ad1-9a4e-02bb3ee1414d" target="_blank" rel="noopener">Connect with us →</a>
    <p style="color:rgba(255,255,255,.5);font-size:13px;margin-top:16px;font-style:italic;">Secure, confidential, free · we follow up within 2 business days</p>
    <div style="margin-top:var(--sp-4);padding-top:var(--sp-3);border-top:1px solid #333;display:flex;flex-wrap:wrap;justify-content:center;gap:var(--sp-3);">
      <div style="text-align:center;">
        <div style="font-family:var(--font-display);font-size:28px;font-weight:700;color:var(--yellow);">2 days</div>
        <div style="font-family:var(--font-serif);font-size:13px;color:rgba(255,255,255,.6);">avg. response time</div>
      </div>
      <div style="text-align:center;">
        <div style="font-family:var(--font-display);font-size:28px;font-weight:700;color:var(--yellow);">5 programs</div>
        <div style="font-family:var(--font-serif);font-size:13px;color:rgba(255,255,255,.6);">one application covers all</div>
      </div>
      <div style="text-align:center;">
        <div style="font-family:var(--font-display);font-size:28px;font-weight:700;color:var(--yellow);">$0 cost</div>
        <div style="font-family:var(--font-serif);font-size:13px;color:rgba(255,255,255,.6);">always free to participants</div>
      </div>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap grid-2" style="align-items:center;">
    <div>
      <div class="eyebrow">What's on</div>
      <h2>Upcoming events.</h2>
      <p>Community dinners, fundraisers, workshops, and LEO Center milestones. Live-synced from our Google Calendar.</p>
      <a class="btn btn-primary" href="events.html" style="margin-top:12px;">See all events →</a>
    </div>
    <div style="border:1px solid var(--line);overflow:hidden;">
      <iframe
        src="https://calendar.google.com/calendar/embed?src=c_aaab49ab274191a67fd34d3ec23430823e39f8a684eb5358c53ccfc765269ec6%40group.calendar.google.com&ctz=America%2FChicago&showTitle=0&showNav=0&showPrint=0&showTabs=0&showCalendars=0&mode=AGENDA"
        style="border:0;width:100%;min-height:260px;display:block;"
        frameborder="0"
        scrolling="no"
        title="Upcoming events">
      </iframe>
    </div>
  </div>
</section>

<section class="cta-strip">
  <div class="wrap">
    <h2>Got a gift, an hour, or a network?</h2>
    <div class="btn-group">
      <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/">Donate</a>
      <a class="btn btn-outline-light" href="volunteer.html">Volunteer</a>
      <a class="btn btn-outline-light" href="partner.html">Partner</a>
    </div>
  </div>
</section>
"""

# -------- DONATE --------
donate_body = f"""
<section class="section" style="text-align:center;min-height:50vh;display:flex;align-items:center;justify-content:center;">
  <div class="wrap" style="max-width:520px;">
    <div class="eyebrow" style="color:var(--red);">Donate</div>
    <h1>Taking you to our secure giving page&hellip;</h1>
    <p class="lead">If you&rsquo;re not redirected automatically, give through NetworkForGood below.</p>
    <a class="btn btn-primary" href="https://projecthood.networkforgood.com/" target="_blank" rel="noopener" style="margin-top:10px;">Give now &rarr;</a>
    <p style="font-size:13px;color:var(--muted);margin-top:16px;"><a href="ways-to-give.html" style="color:var(--green);">See all the ways to give &rarr;</a></p>
  </div>
</section>
"""


# -------- FIRST LOOK --------
first_look_body = f"""
<section class="hero bg-black">
  <div class="wrap" style="text-align:center;max-width:760px;margin:0 auto;">
    <div class="eyebrow" style="color:var(--yellow);">Donor Day</div>
    <h1 style="color:var(--white);">The <span class="hl-yellow">First Look.</span></h1>
    <p class="lead" style="color:rgba(255,255,255,.9);">One day. One community. One building that changes everything. Join Project H.O.O.D. for an exclusive first look at the Leadership &amp; Economic Opportunity Center &mdash; and help us fund its future.</p>
    <div style="margin-top:var(--sp-4);display:flex;gap:14px;justify-content:center;flex-wrap:wrap;">
      <a class="btn btn-yellow" style="font-size:16px;padding:16px 32px;" href="https://projecthood.networkforgood.com/" target="_blank" rel="noopener">Give today &rarr;</a>
      <a class="btn btn-outline-light" href="#share">Share the moment</a>
    </div>
    <p style="color:rgba(255,255,255,.5);font-size:12px;margin-top:14px;">Tax-deductible &middot; EIN 45-3964886 &middot; Every dollar stays in Woodlawn</p>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--green);">The impact</div>
    <h2>What your gift builds.</h2>
    <div class="grid-4" style="margin-top:var(--sp-3);">
      <div class="stat"><div class="v">$50</div><div class="l">feeds a family for a week</div></div>
      <div class="stat"><div class="v">$250</div><div class="l">sponsors a training cohort seat</div></div>
      <div class="stat"><div class="v">$1,000</div><div class="l">funds an outreach worker&rsquo;s week</div></div>
      <div class="stat"><div class="v">$5,000+</div><div class="l">names a LEO Center space</div></div>
    </div>
    <div style="margin-top:var(--sp-4);text-align:center;">
      <a class="btn btn-primary" style="font-size:15px;padding:14px 32px;" href="https://projecthood.networkforgood.com/" target="_blank" rel="noopener">Donate now &rarr;</a>
      <p style="font-size:12px;color:var(--muted);margin-top:8px;">Opens projecthood.networkforgood.com &middot; secure &middot; takes under 2 minutes</p>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap grid-2" style="align-items:center;gap:var(--sp-6);">
    <div>
      <div class="eyebrow" style="color:var(--red);">About the LEO Center</div>
      <h2>22,000 sq ft of opportunity.</h2>
      <p>The Leadership &amp; Economic Opportunity Center is a 90,000 sq ft community hub going up on S. King Drive in Woodlawn. It will be the permanent home of every Project H.O.O.D. program &mdash; workforce development, reentry services, youth programming, and health &amp; wellness &mdash; plus community space for the entire neighborhood.</p>
      <p style="font-size:14px;color:var(--muted);">Currently 84% funded. Your First Look gift brings us closer to opening day.</p>
      <a class="btn btn-outline" href="leo-center.html" style="margin-top:var(--sp-2);">Learn more about the LEO Center &rarr;</a>
    </div>
    <div style="background:var(--black);padding:28px;border-radius:4px;">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
        <div style="text-align:center;padding:16px;border:1px solid #333;border-radius:6px;"><div style="font-family:var(--font-display);font-size:28px;font-weight:700;color:var(--yellow);">90K</div><div style="color:rgba(255,255,255,.7);font-size:12px;margin-top:4px;">sq ft total</div></div>
        <div style="text-align:center;padding:16px;border:1px solid #333;border-radius:6px;"><div style="font-family:var(--font-display);font-size:28px;font-weight:700;color:var(--yellow);">84%</div><div style="color:rgba(255,255,255,.7);font-size:12px;margin-top:4px;">funded</div></div>
        <div style="text-align:center;padding:16px;border:1px solid #333;border-radius:6px;"><div style="font-family:var(--font-display);font-size:28px;font-weight:700;color:var(--yellow);">5</div><div style="color:rgba(255,255,255,.7);font-size:12px;margin-top:4px;">programs housed</div></div>
        <div style="text-align:center;padding:16px;border:1px solid #333;border-radius:6px;"><div style="font-family:var(--font-display);font-size:28px;font-weight:700;color:var(--yellow);">1</div><div style="color:rgba(255,255,255,.7);font-size:12px;margin-top:4px;">community</div></div>
      </div>
    </div>
  </div>
</section>

{social_share_section}

<section class="section">
  <div class="wrap" style="max-width:680px;margin:0 auto;">
    <div class="eyebrow" style="color:var(--green);text-align:center;">FAQ</div>
    <h2 style="text-align:center;">Common questions.</h2>
    <div style="margin-top:var(--sp-3);">
      <div style="border-bottom:1px solid var(--line);padding:16px 0;">
        <h4 style="margin:0 0 8px;">Is my donation tax-deductible?</h4>
        <p style="margin:0;font-size:14px;color:var(--muted);">Yes. Project H.O.O.D. is a 501(c)(3) nonprofit. EIN 45-3964886. You will receive an emailed receipt immediately after your gift.</p>
      </div>
      <div style="border-bottom:1px solid var(--line);padding:16px 0;">
        <h4 style="margin:0 0 8px;">Where does my money go?</h4>
        <p style="margin:0;font-size:14px;color:var(--muted);">Every dollar stays in Woodlawn. Gifts made through NetworkForGood go directly to Project H.O.O.D. program operations and the LEO Center construction fund.</p>
      </div>
      <div style="border-bottom:1px solid var(--line);padding:16px 0;">
        <h4 style="margin:0 0 8px;">Can I give stock or through my DAF?</h4>
        <p style="margin:0;font-size:14px;color:var(--muted);">Absolutely. See our <a href="donate.html" style="color:var(--green);">Ways to Give page</a> for stock transfer instructions, DAF links, and planned giving options.</p>
      </div>
      <div style="padding:16px 0;">
        <h4 style="margin:0 0 8px;">I have more questions.</h4>
        <p style="margin:0;font-size:14px;color:var(--muted);">Email <a href="mailto:info@projecthood.org" style="color:var(--green);">info@projecthood.org</a> &mdash; our team responds within one business day.</p>
      </div>
    </div>
  </div>
</section>

<section class="cta-strip">
  <div class="wrap" style="text-align:center;">
    <h2>This is the moment.</h2>
    <p style="max-width:540px;margin:0 auto var(--sp-3);opacity:.95;">22,000 sq ft. One community. Your gift makes it real.</p>
    <div class="btn-group" style="justify-content:center;">
      <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/" target="_blank" rel="noopener">Give now &rarr;</a>
      <a class="btn btn-outline-light" href="#share">Share the moment</a>
      <a class="btn btn-outline-light" href="donate.html">All giving options</a>
    </div>
  </div>
</section>
"""

# -------- WAYS TO GIVE --------
ways_to_give_body = f"""
<!-- HELP SOMEBODY — attention grabber -->
<section style="background:#111111;padding:72px 24px 60px;text-align:center;">
  <div style="font-family:'Arial Black','Impact','Arial',sans-serif;font-weight:900;font-size:clamp(64px,13vw,168px);line-height:.95;color:#ffffff;letter-spacing:-0.03em;text-transform:uppercase;">HELP<br>SOMEBODY</div>
  <p style="color:rgba(255,255,255,.6);font-size:clamp(16px,2.5vw,20px);margin:24px auto 0;max-width:600px;font-family:var(--font-serif);font-style:italic;">When is the last time you helped somebody? Every gift stays right here in Woodlawn.</p>
  <div style="margin-top:32px;display:flex;gap:14px;justify-content:center;flex-wrap:wrap;">
    <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/" target="_blank" rel="noopener" style="font-size:clamp(15px,2vw,17px);padding:14px 30px;">Give now &rarr;</a>
    <a class="btn btn-outline-light" href="#ways">See all ways to give &darr;</a>
  </div>
</section>

<!-- INTRO -->
<section class="section" id="ways">
  <div class="wrap" style="text-align:center;max-width:720px;">
    <div class="eyebrow" style="color:var(--green);">Ways to Give</div>
    <h1>Give the way that works for you.</h1>
    <p class="lead">Online, by stock, through your donor-advised fund, a brick in the LEO Center, or by mail &mdash; every method is secure, tax-deductible, and stays in the neighborhood. EIN 45-3964886.</p>
  </div>
</section>

<!-- WAYS GRID -->
<section class="section bg-offwhite" style="padding-top:0;">
  <div class="wrap">
    <div class="grid-3" style="gap:var(--sp-4);">

      <div class="card card-accent" style="border-top-color:var(--green);">
        <h3>Give online</h3>
        <p style="font-size:14px;">One-time or monthly through NetworkForGood. Pick your amount, designate a program, done in two minutes.</p>
        <a class="btn btn-primary" href="https://projecthood.networkforgood.com/" target="_blank" rel="noopener" style="margin-top:14px;">Give now &rarr;</a>
      </div>

      <div class="card card-accent" style="border-top-color:var(--gold);">
        <h3>Brick by Brick</h3>
        <p style="font-size:14px;">Engrave your name in the LEO Center's Walkway of Destiny. Named-gift levels from $2,500.</p>
        <a href="#brick" style="margin-top:14px;font-weight:600;color:var(--green);">Claim a brick &rarr;</a>
      </div>

      <div class="card card-accent" style="border-top-color:var(--blue);">
        <h3>Walk With Us!</h3>
        <p style="font-size:14px;">Join the nationwide movement &mdash; give, walk, or start a team to help raise $25M.</p>
        <a href="campaigns.html" style="margin-top:14px;font-weight:600;color:var(--green);">About the movement &rarr;</a>
      </div>

      <div class="card card-accent" style="border-top-color:var(--green);">
        <h3>Stock &amp; securities</h3>
        <p style="font-size:14px;">Donate appreciated stock, avoid capital gains, and deduct the full market value.</p>
        <a href="#stock" style="margin-top:14px;font-weight:600;color:var(--green);">How it works &rarr;</a>
      </div>

      <div class="card card-accent" style="border-top-color:var(--blue);">
        <h3>Donor-advised fund</h3>
        <p style="font-size:14px;">Recommend a grant from Fidelity, Schwab, Vanguard, or any DAF using our EIN.</p>
        <a href="#daf" style="margin-top:14px;font-weight:600;color:var(--green);">DAF details &rarr;</a>
      </div>

      <div class="card card-accent" style="border-top-color:var(--red);">
        <h3>Check, match &amp; planned giving</h3>
        <p style="font-size:14px;">Give by mail, double your gift through your employer, or leave a legacy.</p>
        <a href="#other" style="margin-top:14px;font-weight:600;color:var(--green);">See options &rarr;</a>
      </div>

    </div>
  </div>
</section>

<!-- BRICK BY BRICK -->
<section class="section bg-black" id="brick" style="color:var(--white);">
  <div class="wrap grid-2" style="align-items:center;gap:var(--sp-4);">
    <div>
      <div class="eyebrow" style="color:var(--yellow);">Capital Campaign · LEO Center</div>
      <h2 style="color:var(--white);">Brick by Brick.</h2>
      <p style="font-size:var(--fs-lead);opacity:.9;">Get your name engraved in history. Every brick in the LEO Center's Walkway of Destiny represents someone who believed in Chicago's South Side — before the rest of the world caught up.</p>
      <p style="opacity:.85;margin-top:12px;">Long after the ribbon is cut, families will walk across these names. This is your chance to leave more than a donation — a legacy engraved in stone.</p>
      <div style="margin-top:var(--sp-3);display:flex;gap:12px;flex-wrap:wrap;">
        <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/projects/301372-2026-brick-by-brick-campaign" target="_blank" rel="noopener">Claim your brick →</a>
      </div>
    </div>
    <div>
      <div class="card" style="background:var(--white);color:var(--black);border:none;">
        <div class="eyebrow" style="color:var(--muted);">Named-gift levels</div>
        <ul style="list-style:none;padding:0;margin-top:12px;">
          <li style="padding:16px 0;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;">
            <div><strong>Legacy Brick</strong><p style="font-size:13px;color:var(--muted);margin:2px 0 0;">Prime placement · engraved name</p></div>
            <span style="font-size:1.3rem;font-weight:700;color:var(--green);">$10,000</span>
          </li>
          <li style="padding:16px 0;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;">
            <div><strong>Heritage Brick</strong><p style="font-size:13px;color:var(--muted);margin:2px 0 0;">Engraved name · permanent placement</p></div>
            <span style="font-size:1.3rem;font-weight:700;color:var(--green);">$5,000</span>
          </li>
          <li style="padding:16px 0;display:flex;justify-content:space-between;align-items:center;">
            <div><strong>Foundation Brick</strong><p style="font-size:13px;color:var(--muted);margin:2px 0 0;">Engraved name · lasting legacy</p></div>
            <span style="font-size:1.3rem;font-weight:700;color:var(--green);">$2,500</span>
          </li>
        </ul>
        <a class="btn btn-primary" href="https://projecthood.networkforgood.com/projects/301372-2026-brick-by-brick-campaign" target="_blank" rel="noopener" style="width:100%;text-align:center;margin-top:16px;">Choose your brick →</a>
      </div>
    </div>
  </div>
</section>

<!-- WALK WITH US -->
<section class="section bg-blue" id="walk">
  <div class="wrap grid-2" style="align-items:center;">
    <div>
      <div class="eyebrow" style="color:var(--yellow);">Walk With Us!</div>
      <h3 style="color:var(--white);">Supporting the movement? Give directly on Tiltify.</h3>
      <p style="font-size:15px;opacity:.95;">Walk With Us! donations are tracked separately so team fundraising totals stay accurate.</p>
    </div>
    <div style="text-align:right;">
      <a class="btn btn-outline-light" href="https://tiltify.com/project-hood/walk-across-america-2025">Walk With Us! →</a>
      <p style="font-size:11.5px;margin-top:6px;opacity:.8;font-style:italic;">opens tiltify.com/project-hood</p>
    </div>
  </div>
</section>

<!-- STOCK -->
<section class="section bg-offwhite" id="stock">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--green);">Tax-smart giving</div>
    <h2>Donate stock or securities</h2>
    <p style="max-width:640px;font-size:15.5px;line-height:1.75;">Donating appreciated stock lets you avoid capital gains tax <em>and</em> deduct the full market value — often worth 20–37% more than selling and donating cash. Ideal for stocks, mutual funds, or ETFs held more than one year.</p>
    <div class="grid-2" style="margin-top:var(--sp-4);gap:var(--sp-4);">
      <div class="card" style="border-top:4px solid var(--green);">
        <h4 style="margin-top:0;">Option A — DonateStock (recommended)</h4>
        <p style="font-size:13.5px;">DonateStock is a free platform that handles the full transfer for you — no paperwork, no faxing. Your broker initiates the transfer and DonateStock converts it and sends the proceeds directly to Project H.O.O.D.</p>
        <ol style="font-size:13.5px;padding-left:18px;line-height:1.85;margin-bottom:16px;">
          <li>Click the button below</li>
          <li>Select your brokerage</li>
          <li>Choose your stock and share count</li>
          <li>DonateStock handles the rest</li>
        </ol>
        <a class="btn btn-primary" href="https://www.donatestock.com" target="_blank" rel="noopener" style="font-size:14px;">Donate Stock →</a>
      </div>
      <div class="card" style="border-top:4px solid var(--blue);">
        <h4 style="margin-top:0;">Option B — Direct broker transfer</h4>
        <p style="font-size:13.5px;">Contact your broker and instruct them to transfer shares directly, then email <a href="mailto:info@projecthood.org">info@projecthood.org</a> with your name, stock name, and share count so we can credit your gift.</p>
        <table style="font-size:13.5px;width:100%;border-collapse:collapse;margin:8px 0 0;">
          <tr style="border-bottom:1px solid var(--line);"><td style="padding:7px 4px;font-weight:700;color:var(--muted);width:42%;">Account name</td><td style="padding:7px 4px;">Project H.O.O.D.</td></tr>
          <tr><td style="padding:7px 4px;font-weight:700;color:var(--muted);">For credit to</td><td style="padding:7px 4px;">Project H.O.O.D. — EIN 45-3964886</td></tr>
        </table>
        <p style="font-size:12px;color:var(--muted);margin-top:10px;">Email us for our brokerage and DTC details to share with your broker.</p>
      </div>
    </div>
  </div>
</section>

<!-- DAF -->
<section class="section" id="daf">
  <div class="wrap grid-2" style="align-items:start;gap:var(--sp-6);">
    <div>
      <div class="eyebrow" style="color:var(--blue);">Fidelity · Schwab · Vanguard · any DAF</div>
      <h2>Donor-Advised Fund</h2>
      <p>Already have a donor-advised fund? Recommend a grant to Project H.O.O.D. from Fidelity Charitable, Schwab Charitable, Vanguard Charitable, or any community foundation DAF.</p>
      <div style="background:var(--offwhite);padding:20px;border-left:4px solid var(--blue);margin-top:16px;">
        <p style="font-family:var(--font-display);text-transform:uppercase;font-size:11px;letter-spacing:.1em;color:var(--muted);margin:0 0 10px;">Use this information with your DAF sponsor</p>
        <table style="font-size:14px;width:100%;border-collapse:collapse;">
          <tr style="border-bottom:1px solid var(--line);"><td style="padding:8px 4px;font-weight:700;color:var(--muted);width:40%;">Legal name</td><td style="padding:8px 4px;">Project H.O.O.D.</td></tr>
          <tr style="border-bottom:1px solid var(--line);"><td style="padding:8px 4px;font-weight:700;color:var(--muted);">EIN</td><td style="padding:8px 4px;font-weight:700;">45-3964886</td></tr>
          <tr><td style="padding:8px 4px;font-weight:700;color:var(--muted);">Address</td><td style="padding:8px 4px;">6620 S. King Drive<br>Chicago, IL 60637</td></tr>
        </table>
      </div>
    </div>
    <div style="margin-top:8px;">
      <div class="card card-accent" style="border-top-color:var(--blue);">
        <h4>Quick links by platform</h4>
        <ul style="list-style:none;padding:0;margin:0;font-size:14px;line-height:2.4;">
          <li><a href="https://www.fidelitycharitable.org/giving-account/grant.html" target="_blank" rel="noopener" style="color:var(--green);">Fidelity Charitable → Grant now ↗</a></li>
          <li><a href="https://www.schwabcharitable.org/nonprofit-search" target="_blank" rel="noopener" style="color:var(--green);">Schwab Charitable → Search nonprofits ↗</a></li>
          <li><a href="https://vanguardcharitable.org/grantmaking" target="_blank" rel="noopener" style="color:var(--green);">Vanguard Charitable → Recommend a grant ↗</a></li>
        </ul>
      </div>
      <div class="card" style="margin-top:16px;">
        <h4>Can't find us in your DAF portal?</h4>
        <p style="font-size:13.5px;">Search by EIN <strong>45-3964886</strong> or email <a href="mailto:info@projecthood.org">info@projecthood.org</a> — we can provide any documentation your sponsor needs.</p>
      </div>
    </div>
  </div>
</section>

<!-- CHECK + MATCH + PLANNED -->
<section class="section bg-offwhite" id="other">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--green);">More ways to give</div>
    <h2 style="margin-bottom:var(--sp-3);">Check, corporate match &amp; planned giving</h2>
    <div class="grid-3" style="gap:var(--sp-4);">
      <div class="card card-accent" style="border-top-color:var(--green);">
        <h4>Check or money order</h4>
        <p style="font-size:13.5px;">Make checks payable to <strong>Project H.O.O.D.</strong> and mail to:</p>
        <address style="font-style:normal;font-size:14px;line-height:1.85;padding:12px;background:var(--offwhite);margin:12px 0;">
          Project H.O.O.D.<br>
          6620 S. King Drive<br>
          Chicago, IL 60637
        </address>
        <p style="font-size:12.5px;color:var(--muted);">Include your name and email on the memo line to receive a tax receipt.</p>
      </div>
      <div class="card card-accent" id="match" style="border-top-color:var(--blue);">
        <h4>Corporate matching</h4>
        <p style="font-size:13.5px;">Many employers match charitable gifts dollar-for-dollar — doubling or tripling your impact at no extra cost.</p>
        <ol style="font-size:13.5px;padding-left:18px;line-height:1.85;margin-bottom:12px;">
          <li>Check with your HR or benefits team</li>
          <li>Submit your donation receipt through your company's matching portal</li>
          <li>Your employer sends a matching gift to Project H.O.O.D.</li>
        </ol>
        <p style="font-size:12.5px;color:var(--muted);">Need our EIN or W-9? Email <a href="mailto:info@projecthood.org">info@projecthood.org</a></p>
      </div>
      <div class="card card-accent" id="planned" style="border-top-color:var(--red);">
        <h4>Planned giving</h4>
        <p style="font-size:13.5px;">Leave a legacy in Woodlawn. Common planned gift types include:</p>
        <ul style="font-size:13.5px;padding-left:18px;line-height:1.85;margin-bottom:12px;">
          <li>Bequest in your will</li>
          <li>IRA or retirement account beneficiary designation</li>
          <li>Life insurance beneficiary</li>
          <li>Charitable remainder trust</li>
        </ul>
        <p style="font-size:12.5px;color:var(--muted);">To discuss options, contact <a href="mailto:info@projecthood.org">info@projecthood.org</a>.</p>
      </div>
    </div>
  </div>
</section>

<!-- DONOR RESOURCES -->
<section class="section-sm" style="border-top:1px solid var(--line);">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--green);margin-bottom:var(--sp-2);">Donor Resources</div>
    <div class="grid-2" style="gap:var(--sp-3);">
      <div class="card" style="border-top:4px solid var(--yellow);">
        <h4 style="margin-top:0;">&#x1F4C4; Donor Toolkit</h4>
        <p style="font-size:13.5px;">Sample social posts, impact stats, and everything you need to champion Project H.O.O.D. in your network.</p>
        <a href="docs/ph-donor-toolkit.pdf" target="_blank" rel="noopener" style="font-size:13px;color:var(--green);font-weight:600;">Download toolkit (PDF) &rarr;</a>
      </div>
      <div class="card" style="border-top:4px solid var(--blue);">
        <h4 style="margin-top:0;">&#x1F4F0; Media Kit</h4>
        <p style="font-size:13.5px;">Organization overview, LEO Center facts, leadership bios, logos, and press contact for media use.</p>
        <a href="docs/ph-media-kit.pdf" target="_blank" rel="noopener" style="font-size:13px;color:var(--blue);font-weight:600;">Download media kit (PDF) &rarr;</a>
      </div>
    </div>
  </div>
</section>

<!-- CLOSING CTA -->
<section class="cta-strip">
  <div class="wrap" style="text-align:center;">
    <h2>Every gift stays in Woodlawn.</h2>
    <p style="max-width:540px;margin:0 auto var(--sp-3);opacity:.95;">No national overhead. No middle layer. Just your neighbors &mdash; and the people counting on us to keep showing up.</p>
    <div class="btn-group" style="justify-content:center;">
      <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/" target="_blank" rel="noopener">Donate now &rarr;</a>
      <a class="btn btn-outline-light" href="#ways">All giving details</a>
      <a class="btn btn-outline-light" href="mailto:info@projecthood.org">Questions? Email us</a>
    </div>
  </div>
</section>
"""

# -------- VOLUNTEER --------
volunteer_body = f"""
<section class="hero bg-green">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">Volunteer</div>
    <h1>Show up <span class="hl-yellow">in person.</span></h1>
    <p class="lead">We recruit volunteers for specific events, cohorts, and program support. Fill out the form and we'll match you to the right opportunity within a week.</p>
  </div>
</section>

<section class="section">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">What you might do</div>
      <h2>Where volunteers plug in.</h2>
      <ul>
        <li><strong>Events:</strong> community dinners, back-to-school, holiday drives, galas</li>
        <li><strong>Workforce program:</strong> mock interviews, résumé coaching, cohort mentors</li>
        <li><strong>Youth programs:</strong> tutoring, entrepreneurship coaching, mentorship, field trips</li>
        <li><strong>LEO Center build:</strong> tours, donor events, community open houses</li>
        <li><strong>Operations:</strong> food pantry, logistics, admin support</li>
      </ul>
      <p style="margin-top:var(--sp-3);font-size:14px;color:var(--muted);">Background check required for any role working directly with youth.</p>
    </div>
    <div>
      <div class="eyebrow" style="color:var(--red);">Volunteer signup</div>
      <div style="background:var(--offwhite);padding:var(--sp-4);border:2px dashed var(--line);">
        <p style="font-family:var(--font-display);text-transform:uppercase;letter-spacing:.1em;font-size:12px;color:var(--muted);">Google Form embed · on real site</p>
        <h3 style="margin:10px 0;">Project H.O.O.D. Volunteer Signup</h3>
        <p style="font-size:14px;">Name, email, phone, areas of interest, availability, background-check consent — responses go directly to our volunteer coordinator's Google Sheet.</p>
        <a class="btn btn-primary" href="https://docs.google.com/forms/d/e/1FAIpQLSfSJM9VCqgcNPJN8ji3-3-W41BHlyoTtLrlWzqFu4LvgoxDow/viewform" style="margin-top:12px;">Volunteer signup form →</a>
      </div>
    </div>
  </div>
</section>

<section class="section bg-bg">
  <div class="wrap testimonial">
    <blockquote>"I came to help at one event. A year later I'm a cohort mentor and I know everyone's name on the block."</blockquote>
    <cite>— Volunteer since 2024</cite>
  </div>
</section>
"""

# -------- EVENTS --------
# Fallback shown only if the Eventbrite API can't be reached at build time.
# Deliberately date-free so stale/past events can never appear as "upcoming."
_hardcoded_cards = """
      <div class="card" style="padding:32px;text-align:center;grid-column:1/-1;">
        <p style="font-family:var(--font-serif);color:var(--muted);font-size:15px;margin:0;">
          Our upcoming events are posted on Eventbrite. See what's coming up on
          <a href="https://www.eventbrite.com/o/project-hood-41178041593" target="_blank" rel="noopener">our Eventbrite page</a>.
        </p>
      </div>
"""

# Pick live API cards if available, otherwise hardcoded fallback
_eb_cards = _event_cards_html if _event_cards_html else _hardcoded_cards

# Past-events grid: live API cards, or a friendly fallback message
_past_fallback = """
      <div class="card" style="padding:32px;text-align:center;grid-column:1/-1;">
        <p style="font-family:var(--font-serif);color:var(--muted);font-size:15px;margin:0;">
          Past events show up here once we've hosted them. In the meantime, see everything on
          <a href="https://www.eventbrite.com/o/project-hood-41178041593" target="_blank" rel="noopener">our Eventbrite page</a>.
        </p>
      </div>
"""
_past_cards = _past_cards_html if _past_cards_html else _past_fallback

events_body = f"""
<section class="hero bg-yellow" style="color:var(--black);">
  <div class="wrap">
    <div class="eyebrow">Community Calendar</div>
    <h1>On the <span style="background:var(--red);color:var(--white);padding:2px 10px;transform:rotate(-1.5deg);display:inline-block;">calendar.</span></h1>
    <p class="lead" style="opacity:1;color:var(--ink);">Programming, workshops, health fairs, and community gatherings across Woodlawn. Free and open to the community.</p>
  </div>
</section>

<!-- TAB BAR -->
<section class="section-sm" style="border-bottom:1px solid var(--line);background:var(--white);">
  <div class="wrap" style="display:flex;gap:24px;font-family:var(--font-display);text-transform:uppercase;font-size:12.5px;letter-spacing:.14em;align-items:center;flex-wrap:wrap;">
    <button type="button" class="ph-tab" data-target="ph-upcoming" style="background:none;border:none;cursor:pointer;font:inherit;letter-spacing:inherit;text-transform:inherit;color:var(--red);border-bottom:2px solid var(--red);padding:0 0 4px;">Upcoming</button>
    <button type="button" class="ph-tab" data-target="ph-past" style="background:none;border:none;cursor:pointer;font:inherit;letter-spacing:inherit;text-transform:inherit;color:var(--muted);border-bottom:2px solid transparent;padding:0 0 4px;">Past events</button>
    <div style="margin-left:auto;">
      <a href="https://www.eventbrite.com/o/project-hood-41178041593" target="_blank" rel="noopener" style="font-family:var(--font-serif);text-transform:none;letter-spacing:0;font-size:12.5px;color:var(--muted);font-style:italic;">View all on Eventbrite →</a>
    </div>
  </div>
</section>

<!-- EVENT CARDS — auto-populated from Eventbrite API when EVENTBRITE_TOKEN is set;
     otherwise uses the hardcoded cards below. See _build.py header for setup. -->
<section class="section">
  <div class="wrap">

    <div id="ph-upcoming" class="ph-panel" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:20px;">
{_eb_cards}
    </div>

    <div id="ph-past" class="ph-panel" style="display:none;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:20px;">
{_past_cards}
    </div>
  </div>
</section>

<script>
(function() {{
  // Share buttons
  document.querySelectorAll('.ph-share-btn').forEach(function(btn) {{
    btn.addEventListener('click', function() {{
      var url = this.getAttribute('data-url') || window.location.href;
      var title = this.getAttribute('data-title') || 'Project H.O.O.D. Event';
      var self = this;
      var orig = self.textContent;
      if (navigator.share) {{
        navigator.share({{ title: title, url: url }}).catch(function() {{}});
      }} else if (navigator.clipboard && navigator.clipboard.writeText) {{
        navigator.clipboard.writeText(url).then(function() {{
          self.textContent = 'Link copied!';
          setTimeout(function() {{ self.textContent = orig; }}, 2000);
        }});
      }}
    }});
  }});
  // Upcoming / Past tab toggle
  var tabs = document.querySelectorAll('.ph-tab');
  tabs.forEach(function(tab) {{
    tab.addEventListener('click', function() {{
      var target = this.getAttribute('data-target');
      document.querySelectorAll('.ph-panel').forEach(function(panel) {{
        panel.style.display = (panel.id === target) ? 'grid' : 'none';
      }});
      tabs.forEach(function(t) {{
        var on = (t === tab);
        t.style.color = on ? 'var(--red)' : 'var(--muted)';
        t.style.borderBottomColor = on ? 'var(--red)' : 'transparent';
      }});
    }});
  }});
}})();
</script>
"""

# -------- PARTNER --------
partner_body = f"""
<section class="hero bg-purple">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">Partner with us</div>
    <h1>Build with the <span class="hl-yellow">neighborhood.</span></h1>
    <p class="lead">Corporate partnerships, church collaborations, employer pipelines, foundation partners — let's find the fit that moves both missions forward.</p>
  </div>
</section>

<section class="section">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">What partnership looks like</div>
      <h2>Four lanes we work in.</h2>
      <ul>
        <li><strong>Corporate:</strong> matching gifts, employee volunteer days, sponsored cohorts, in-kind donations</li>
        <li><strong>Employer pipeline:</strong> direct-hire partnerships for workforce graduates</li>
        <li><strong>Foundation / grant:</strong> multi-year program funding, capital campaign partners</li>
        <li><strong>Church / community:</strong> collaboration on outreach, mutual-aid coordination, event hosting</li>
      </ul>
    </div>
    <div>
      <div class="eyebrow" style="color:var(--red);">Partner inquiry</div>
      <div style="background:var(--offwhite);padding:var(--sp-4);border:2px solid var(--line);">
        <p style="font-family:var(--font-display);text-transform:uppercase;letter-spacing:.1em;font-size:12px;color:var(--muted);">Google Form embed · on real site</p>
        <h3 style="margin:10px 0;">Partner Inquiry Form</h3>
        <p style="font-size:14px;">Org name, contact, type of partnership, what you bring, what you need. Routes to our development team.</p>
        <a class="btn btn-primary" href="https://docs.google.com/forms/d/e/1FAIpQLSd7KybYr4o6lRtz49HpgBuxmC-tiPPqwO_VKDQlQ_OvQzdrYg/viewform" style="margin-top:12px;">Partner inquiry form →</a>
      </div>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap">
    <div class="eyebrow">Current partners</div>
    <h2>Who we work with.</h2>
    <div class="grid-4" style="margin-top:var(--sp-3);">
      <div class="card" style="display:flex;align-items:center;justify-content:center;padding:var(--sp-2);min-height:110px;">
        <img src="img/partners/jpmorgan-chase.png" alt="JPMorgan Chase" style="max-width:100%;max-height:55px;object-fit:contain;">
      </div>
      <div class="card" style="display:flex;align-items:center;justify-content:center;padding:var(--sp-2);min-height:110px;">
        <img src="img/partners/mccormick-foundation.png" alt="Robert R. McCormick Foundation" style="max-width:100%;max-height:90px;object-fit:contain;">
      </div>
      <div class="card" style="display:flex;align-items:center;justify-content:center;padding:var(--sp-2);min-height:110px;">
        <img src="img/partners/wintrust.png" alt="Wintrust — Chicago's Bank" style="max-width:100%;max-height:80px;object-fit:contain;">
      </div>
      <div class="card" style="display:flex;align-items:center;justify-content:center;padding:var(--sp-2);min-height:110px;">
        <img src="img/partners/ozinga.png" alt="Ozinga" style="max-width:100%;max-height:65px;object-fit:contain;">
      </div>
      <div class="card" style="display:flex;align-items:center;justify-content:center;padding:var(--sp-2);min-height:110px;">
        <img src="img/partners/crane-co.png" alt="Crane Co." style="max-width:100%;max-height:80px;object-fit:contain;">
      </div>
      <div class="card" style="display:flex;align-items:center;justify-content:center;padding:var(--sp-2);min-height:110px;">
        <img src="img/partners/reed-construction.png" alt="Reed Construction" style="max-width:100%;max-height:80px;object-fit:contain;">
      </div>
      <div class="card" style="display:flex;align-items:center;justify-content:center;padding:var(--sp-2);min-height:110px;">
        <img src="img/partners/metro-ford.png" alt="Metro Ford Chicago" style="max-width:100%;max-height:80px;object-fit:contain;">
      </div>
      <div class="card" style="display:flex;align-items:center;justify-content:center;padding:var(--sp-2);min-height:110px;background:var(--offwhite);">
        <div style="text-align:center;">
          <div style="font-weight:700;font-size:13px;color:var(--dark);letter-spacing:0.04em;">DANIEL J. EDELMAN</div>
          <div style="font-size:11px;color:var(--muted);margin-top:4px;">Family Foundation</div>
        </div>
      </div>
    </div>
  </div>
</section>
"""

# -------- NEWS --------
news_body = """
<section class="hero bg-black">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">News &amp; Impact</div>
    <h1>This page <span class="hl-yellow">moved.</span></h1>
    <p class="lead">Our news now lives alongside our impact numbers. Taking you there…</p>
    <div style="margin-top:var(--sp-3);"><a class="btn btn-yellow" href="impact.html">Go to News &amp; Impact &rarr;</a></div>
  </div>
</section>
<script>window.location.replace('impact.html');</script>
"""

# -------- CONTACT --------
contact_body = f"""
<section class="hero bg-green">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">Contact</div>
    <h1 style="font-size:clamp(40px,7vw,72px);">Talk to us.</h1>
    <p class="lead">Press, partnership, participant inquiry, or general question — we answer every message.</p>
  </div>
</section>

<section class="section">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">Reach us</div>
      <h2>One inbox.<br>We'll get it to the right person.</h2>
      <p style="font-size:var(--fs-lead);margin-top:12px;">Use the form to tell us what you're reaching out about — donations, volunteering, press, events, or participant services. We route every message to the right person and respond within one business day.</p>
      <div style="margin-top:var(--sp-3);display:flex;flex-direction:column;gap:14px;">
        <div style="display:flex;gap:12px;align-items:flex-start;">
          <span style="font-size:18px;flex-shrink:0;">✉</span>
          <div><strong>Email</strong><br><a href="mailto:info@projecthood.org" style="color:var(--green);">info@projecthood.org</a></div>
        </div>
        <div style="display:flex;gap:12px;align-items:flex-start;">
          <span style="font-size:18px;flex-shrink:0;">📞</span>
          <div><strong>Phone</strong><br><a href="tel:7739238270">773-923-8270</a></div>
        </div>
        <div style="display:flex;gap:12px;align-items:flex-start;">
          <span style="font-size:18px;flex-shrink:0;">📍</span>
          <div><strong>Office</strong><br>Project H.O.O.D.<br>6620 S. King Drive<br>Chicago, IL 60637</div>
        </div>
      </div>
    </div>
    <div>
      <div class="eyebrow" style="color:var(--red);">Send a message</div>
      <h3 style="margin-bottom:12px;">What are you reaching out about?</h3>
      <p style="font-size:14px;color:var(--muted);margin-bottom:var(--sp-3);">Select your interest in the form — donations, volunteering, press &amp; media, events, or connecting with our programs. Every submission goes directly to the team member who can help.</p>
      <div style="display:flex;flex-direction:column;gap:10px;margin-bottom:var(--sp-3);">
        <div style="padding:10px 14px;background:var(--offwhite);border-left:3px solid var(--green);border-radius:0 4px 4px 0;font-size:14px;">💚 <strong>Donations &amp; development</strong></div>
        <div style="padding:10px 14px;background:var(--offwhite);border-left:3px solid var(--blue);border-radius:0 4px 4px 0;font-size:14px;">💙 <strong>Volunteer with us</strong></div>
        <div style="padding:10px 14px;background:var(--offwhite);border-left:3px solid var(--red);border-radius:0 4px 4px 0;font-size:14px;">❤️ <strong>Press &amp; media</strong><span style="display:block;color:var(--muted);font-size:12px;margin-top:3px;">Direct line: <a href="tel:7733548483" style="color:var(--red);">773.354.8483</a></span></div>
        <div style="padding:10px 14px;background:var(--offwhite);border-left:3px solid var(--yellow);border-radius:0 4px 4px 0;font-size:14px;">💛 <strong>Events &amp; partnerships</strong></div>
        <div style="padding:10px 14px;background:var(--offwhite);border-left:3px solid var(--purple);border-radius:0 4px 4px 0;font-size:14px;">💜 <strong>Connect with our programs</strong></div>
      </div>
      <a class="btn btn-primary" href="https://docs.google.com/forms/d/e/1FAIpQLScXh7YTveg_BRJLetB7Tclr0MFGhi_QDetgc-iPCCJZ1Narww/viewform" style="width:100%;text-align:center;">Send a message →</a>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap">
    <iframe
      src="https://maps.google.com/maps?q=6620+S+King+Dr,+Chicago,+IL+60637&z=16&output=embed"
      width="100%" height="380" style="border:0;border-radius:8px;display:block;"
      allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"
      title="Project H.O.O.D. — 6620 S. King Drive, Chicago, IL 60637"></iframe>
  </div>
</section>
"""

# -------- PRIVACY POLICY --------
privacy_body = """
<section class="hero bg-black">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">Legal</div>
    <h1>Privacy Policy</h1>
    <p class="lead" style="opacity:.85;">Project H.O.O.D. is committed to protecting your personal information. This policy explains what we collect, why, and how you can reach us with questions.</p>
    <p style="font-size:13px;opacity:.6;margin-top:8px;">Last updated: June 2026</p>
  </div>
</section>

<section class="section">
  <div class="wrap" style="max-width:var(--w-read);">

    <h2>Who we are</h2>
    <p>Project H.O.O.D. (Helping Others Obtain Destiny) is a 501(c)(3) nonprofit organization located at 6620 S. King Drive, Chicago, IL 60637. EIN 45-3964886. You can reach us at <a href="mailto:info@projecthood.org">info@projecthood.org</a>.</p>

    <h2 style="margin-top:var(--sp-3);">What information we collect</h2>
    <p>We only collect information you choose to give us. Depending on how you interact with this site, that may include:</p>
    <ul>
      <li><strong>Contact information</strong> (name, email, phone) — when you fill out a volunteer signup, partner inquiry, contact, or event RSVP form</li>
      <li><strong>Program intake information</strong> — when you apply to a Project H.O.O.D. program through our Apricot intake portal (operated by Social Solutions)</li>
      <li><strong>Donation information</strong> — when you give through NetworkForGood or Tiltify; those platforms handle payment processing and their own privacy policies apply</li>
      <li><strong>Newsletter subscription</strong> — email address, if you sign up for our monthly updates through NetworkForGood</li>
      <li><strong>Usage data</strong> — pages visited, time on site, referral source, and similar analytics data collected automatically via Google Analytics 4. This data is anonymized and aggregated — we cannot identify individual visitors from it.</li>
    </ul>

    <h2 style="margin-top:var(--sp-3);">How we use your information</h2>
    <ul>
      <li>To respond to your inquiry or match you to a volunteer opportunity</li>
      <li>To process or acknowledge donations</li>
      <li>To send our monthly newsletter, if you subscribed</li>
      <li>To improve the website (via anonymized analytics)</li>
      <li>To fulfill program services, if you applied to a program</li>
    </ul>
    <p>We do not sell, rent, or trade your personal information. We do not use it for advertising. We will not share it with third parties except as described below.</p>

    <h2 style="margin-top:var(--sp-3);">Third-party services</h2>
    <p>This site uses the following external services. Each has its own privacy policy:</p>
    <ul>
      <li><strong>Google Forms &amp; Google Analytics 4</strong> — form responses and site analytics (<a href="https://policies.google.com/privacy" target="_blank" rel="noopener noreferrer">Google Privacy Policy</a>)</li>
      <li><strong>Google Calendar</strong> — public event calendar embedded on this site</li>
      <li><strong>NetworkForGood</strong> — donation processing and newsletter (<a href="https://www.networkforgood.com/about/privacy/" target="_blank" rel="noopener noreferrer">NetworkForGood Privacy Policy</a>)</li>
      <li><strong>Tiltify</strong> — Walk Across America peer-to-peer fundraising (<a href="https://info.tiltify.com/policies/privacy-policy" target="_blank" rel="noopener noreferrer">Tiltify Privacy Policy</a>)</li>
      <li><strong>Social Solutions Apricot</strong> — program intake and case management</li>
    </ul>
    <p>When you click a link to any of these services, you leave projecthood.org and their privacy policies apply.</p>

    <h2 style="margin-top:var(--sp-3);">Cookies</h2>
    <p>Google Analytics uses cookies to distinguish repeat visitors and track sessions. No personally identifiable information is stored in these cookies. You can opt out using the <a href="https://tools.google.com/dlpage/gaoptout" target="_blank" rel="noopener noreferrer">Google Analytics Opt-out Browser Add-on</a>.</p>

    <h2 style="margin-top:var(--sp-3);">Data retention</h2>
    <p>Form responses are stored in Google Sheets accessible only to Project H.O.O.D. staff. We retain responses as long as they are operationally relevant. You may request deletion at any time.</p>

    <h2 style="margin-top:var(--sp-3);">Your rights</h2>
    <p>You may request to view, correct, or delete any personal information we hold about you. To make a request, email <a href="mailto:info@projecthood.org">info@projecthood.org</a> with "Privacy Request" in the subject line. We will respond within 30 days.</p>

    <h2 style="margin-top:var(--sp-3);">Changes to this policy</h2>
    <p>If we make material changes to this policy, we will update the "Last updated" date at the top of this page. We will not retroactively reduce your rights without explicit notice.</p>

    <h2 style="margin-top:var(--sp-3);">Contact</h2>
    <p>Questions about this policy? Email <a href="mailto:info@projecthood.org">info@projecthood.org</a> or write to us at 6620 S. King Drive, Chicago, IL 60637.</p>

  </div>
</section>
"""

# -------- EXECUTIVE DIRECTOR --------
exec_director_body = f"""
<section class="hero bg-black">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">Leadership</div>
    <h1>Meet Our <span class="hl-yellow">Executive Director</span></h1>
    <p class="lead">Desmond "Dez" Marshall leads the team, the strategy, and the relationships that make Project H.O.O.D. run.</p>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="grid-2" style="align-items:start;gap:var(--sp-4);">
      <div>
        <!-- TODO: Save Dez's photo to img/desmond-marshall.jpg
             Source: https://www.projecthood.org/desmondmarshall -->
        <div style="min-height:480px;background-image:url('img/desmond-marshall.jpg');background-size:cover;background-position:center top"></div>
      </div>
      <div>
        <div class="eyebrow">Executive Director</div>
        <h2 style="margin-bottom:6px;">Desmond "Dez" Marshall</h2>
        <p style="font-size:14px;color:var(--muted);margin-bottom:var(--sp-3);">B.S., Hampton University · Broadcast Journalism &amp; Marketing</p>
        <p><strong>Desmond "Dez" Marshall</strong> is an accomplished and visionary leader who serves as Executive Director of Project H.O.O.D., a nonprofit dedicated to empowering underserved communities through education, economic development, and holistic support services.</p>
        <p>A proud graduate of Hampton University, Dez holds a Bachelor of Science degree in Broadcast Journalism and Marketing. His professional journey began at Burger King Corporation in Miami, where he entered the recent college graduate program. His talent and drive quickly propelled him into a leadership role overseeing sales, marketing, and operations for more than 40 locations across Upstate New York.</p>
        <p>Dez later returned to his hometown of Chicago, traveling nationwide in a sales role securing advertising partnerships for a small media outlet. After four and a half years in corporate sales, Dez felt a deeper calling to serve his community — and that calling led him to volunteer with Project H.O.O.D., where he discovered his true purpose.</p>
        <p>Since joining Project H.O.O.D., Dez has transformed the organization from a grassroots initiative into a thriving enterprise. Under his leadership, the team has grown from just three employees to over 83 staff members across multiple divisions. He successfully led a capital campaign that raised more than $44 million in financial and in-kind donations in just two years.</p>
        <p>Dez's strategic mindset, dedication to community impact, and talent for building powerful partnerships have helped Project H.O.O.D. touch the lives of over 15,000 individuals annually throughout the Chicagoland area.</p>
        <p>Desmond is married to his lovely wife, <strong>Skye D. Marshall</strong>, and together they have two children: a daughter, <strong>Sunni</strong>, and a son, <strong>Desmond II</strong>.</p>
        <div style="margin-top:var(--sp-3);display:flex;gap:12px;flex-wrap:wrap;">
          <a class="btn btn-primary" href="about.html">About Project H.O.O.D.</a>
          <a class="btn btn-outline" href="contact.html">Get in touch</a>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap">
    <div class="eyebrow" style="text-align:center;">By the numbers</div>
    <div class="stat-grid" style="margin-top:var(--sp-3);">
      <div class="stat accent-green"><div class="v">83+</div><div class="l">staff members led</div></div>
      <div class="stat accent-red"><div class="v">$44M+</div><div class="l">raised in two years</div></div>
      <div class="stat"><div class="v">15,000+</div><div class="l">individuals served annually</div></div>
      <div class="stat accent-green"><div class="v">3 → 83</div><div class="l">team growth under Dez</div></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap" style="max-width:900px;">
    <div class="eyebrow" style="text-align:center;">Hear from Dez</div>
    <h2 style="text-align:center;margin-bottom:var(--sp-3);">A deeper look at the leadership.</h2>
    <div style="position:relative;width:100%;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:8px;box-shadow:0 8px 32px rgba(0,0,0,.18);">
      <iframe
        src="https://www.youtube.com/embed/EqQJP6ZLiSo"
        title="Desmond Marshall — Executive Director, Project H.O.O.D."
        frameborder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen
        style="position:absolute;top:0;left:0;width:100%;height:100%;">
      </iframe>
    </div>
  </div>
</section>

<section class="cta-strip">
  <div class="wrap">
    <h2>Move the work forward.</h2>
    <p style="max-width:560px;margin:0 auto var(--sp-3);opacity:.95;">Give to the mission Dez is building — or get involved directly.</p>
    <div class="btn-group">
      <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/">Donate</a>
      <a class="btn btn-outline-light" href="get-involved.html">Volunteer</a>
    </div>
  </div>
</section>
"""

# -------- 404 --------
notfound_body = f"""
<!-- Squarespace → new URL redirect map
     When someone hits an old Squarespace URL, redirect them to the correct new page.
     To add a redirect: add a new entry to the redirects object below. -->
<script>
(function() {{
  var redirects = {{
    '/about-us':          'about.html',
    '/about-us/':         'about.html',
    '/our-programs':      'programs.html',
    '/our-programs/':     'programs.html',
    '/violence-prevention': 'violence-prevention.html',
    '/the-leo-center':    'leo-center.html',
    '/the-leo-center/':   'leo-center.html',
    '/walk-across-america': 'campaigns.html',
    '/get-involved-1':    'get-involved.html',
    '/donate-now':        'donate.html',
    '/donate-now/':       'donate.html',
    '/volunteer-1':       'volunteer.html',
    '/events-1':          'events.html',
    '/partner-with-us':   'partner.html',
    '/partner-with-us/':  'partner.html',
    '/news-1':            'news.html',
    '/news-1/':           'news.html',
    '/contact-us':        'contact.html',
    '/contact-us/':       'contact.html'
  }};
  var path = window.location.pathname.replace(/\\/+$/, '') || '/';
  var dest = redirects[path];
  if (dest) {{ window.location.replace(dest); }}
}})();
</script>

<section class="hero bg-yellow" style="color:var(--black);text-align:center;padding:var(--sp-6) 0;">
  <div class="wrap">
    <div class="eyebrow">404</div>
    <h1 style="font-size:clamp(60px,10vw,140px);">Nothing here.</h1>
    <p class="lead" style="opacity:1;color:var(--ink);max-width:560px;margin:0 auto;">That page either moved, never existed, or is about to. Here's where to go next.</p>
    <div style="margin-top:var(--sp-3);display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
      <a class="btn btn-primary" href="index.html">Home</a>
      <a class="btn btn-outline" href="programs.html">Programs</a>
      <a class="btn btn-outline" href="impact.html">Impact</a>
      <a class="btn btn-outline" href="https://projecthood.networkforgood.com/">Donate</a>
    </div>
  </div>
</section>
"""

# -------- GET HELP --------
get_help_body = """
<section class="hero bg-green">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">Get Help</div>
    <h1>How can we <span class="hl-yellow">help?</span></h1>
    <p class="lead">Wherever you are — just beginning your journey or continuing it toward your destiny — Project H.O.O.D. is here. Everything below is free and open to the neighborhood. No insurance, no barriers, no judgment.</p>
    <div style="margin-top:var(--sp-3);display:flex;gap:12px;flex-wrap:wrap;">
      <a class="btn btn-yellow" href="tel:7739238270">Call 773-923-8270</a>
      <a class="btn btn-outline-light" href="#services">See how we can help &darr;</a>
    </div>
  </div>
</section>

<!-- Quick-start contact band -->
<section class="section-sm bg-offwhite">
  <div class="wrap" style="display:flex;gap:24px;flex-wrap:wrap;align-items:flex-start;justify-content:space-between;">
    <div style="display:flex;gap:10px;align-items:flex-start;"><span style="font-size:20px;flex-shrink:0;">&#128222;</span><div><strong>Call or text</strong><br><a href="tel:7739238270" style="color:var(--green);">773-923-8270</a></div></div>
    <div style="display:flex;gap:10px;align-items:flex-start;"><span style="font-size:20px;flex-shrink:0;">&#9993;</span><div><strong>Email</strong><br><a href="mailto:info@projecthood.org" style="color:var(--green);">info@projecthood.org</a></div></div>
    <div style="display:flex;gap:10px;align-items:flex-start;"><span style="font-size:20px;flex-shrink:0;">&#128205;</span><div><strong>Visit</strong><br>6620 S. King Drive, Chicago</div></div>
  </div>
</section>

<section class="section" id="services">
  <div class="wrap">
    <div class="eyebrow">What do you need?</div>
    <h2>Find the right kind of help.</h2>
    <p style="max-width:var(--w-read);margin-top:8px;">Pick what fits where you are right now. Not sure? Call us &mdash; we'll point you to the right person.</p>
    <div class="grid-2" style="margin-top:var(--sp-3);">

      <div class="prog-card pg-green">
        <span class="tag tag-green">Safety</span>
        <h3>I need to stay safe.</h3>
        <p>Violence interruption, conflict mediation, and support after a crisis &mdash; from credible messengers who live on the block.</p>
        <a href="violence-prevention.html" style="margin-top:auto;">Violence prevention &rarr;</a>
      </div>

      <div class="prog-card">
        <span class="tag tag-red">Jobs</span>
        <h3>I need a job or training.</h3>
        <p>Free job training, certifications, and placement in construction, tech, and the trades &mdash; average starting wage $19/hr.</p>
        <a href="workforce-development.html" style="margin-top:auto;">Workforce development &rarr;</a>
      </div>

      <div class="prog-card pg-purple">
        <span class="tag tag-purple">Wellness</span>
        <h3>I need care or someone to talk to.</h3>
        <p>Free medical access, counseling, recovery navigation, and senior programming &mdash; no insurance required.</p>
        <a href="health-wellness.html" style="margin-top:auto;">Health &amp; wellness &rarr;</a>
      </div>

      <div class="prog-card pg-blue">
        <span class="tag tag-blue">Youth</span>
        <h3>Something for my child.</h3>
        <p>After-school enrichment, mentorship, and entrepreneurship programs that invest in who young people are becoming.</p>
        <a href="youth-programming.html" style="margin-top:auto;">Youth programming &rarr;</a>
      </div>

      <div class="prog-card pg-green">
        <span class="tag tag-green">Re-entry</span>
        <h3>I'm coming home.</h3>
        <p>Employment pathways, housing navigation, and wraparound support for people returning from incarceration.</p>
        <a href="reentry-services.html" style="margin-top:auto;">Re-entry services &rarr;</a>
      </div>

      <div class="prog-card">
        <span class="tag tag-red">Food &amp; events</span>
        <h3>Food &amp; community support.</h3>
        <p>Food distributions, health fairs, and free community events happen year-round. See what's coming up on the calendar.</p>
        <a href="events.html" style="margin-top:auto;">Community Calendar &rarr;</a>
      </div>

    </div>
  </div>
</section>

<!-- Not sure where to start -->
<section class="section bg-black">
  <div class="wrap" style="text-align:center;">
    <div class="eyebrow" style="color:var(--yellow);">Not sure where to start?</div>
    <h2 style="color:var(--white);">Just reach out. We'll take it from there.</h2>
    <p class="lead" style="max-width:var(--w-read);margin:12px auto 0;">Tell us a little about what you're looking for and we'll connect you with the right person &mdash; usually within one business day.</p>
    <div style="margin-top:var(--sp-3);display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
      <a class="btn btn-yellow" href="https://docs.google.com/forms/d/e/1FAIpQLScXh7YTveg_BRJLetB7Tclr0MFGhi_QDetgc-iPCCJZ1Narww/viewform" target="_blank" rel="noopener">Send us a message</a>
      <a class="btn btn-outline-light" href="tel:7739238270">Call 773-923-8270</a>
    </div>
  </div>
</section>
"""

# -------- 2025 ANNUAL REPORT: embedded flipbook (plain string; keeps JS/CSS braces literal) --------
annual_report_gallery = """
<section class="section bg-black" id="read-report">
  <div class="wrap" style="text-align:center;">
    <div class="eyebrow" style="color:var(--yellow);">Read the full report</div>
    <h2 style="color:var(--white);">Flip through all 13 pages.</h2>
    <p class="lead" style="color:rgba(255,255,255,.85);max-width:var(--w-read);margin:8px auto 0;">Tap any page to zoom in. Use the arrows &mdash; or your keyboard&rsquo;s left/right keys &mdash; to turn the pages.</p>

    <div class="flipbook">
      <div class="flip-stage">
        <button class="flip-nav flip-prev" type="button" aria-label="Previous page">&#8249;</button>
        <img id="flip-img" class="flip-img" src="img/annual-report-2025/page-01.jpg" alt="Project H.O.O.D. 2025 Annual Report — page 1 of 13" loading="lazy">
        <button class="flip-nav flip-next" type="button" aria-label="Next page">&#8250;</button>
      </div>
      <div class="flip-meta"><span id="flip-count">Page 1 of 13</span> &middot; tap to zoom</div>
    </div>

    <div style="margin-top:var(--sp-3);">
      <a class="btn btn-yellow" href="docs/ph-annual-report-2025.pdf" target="_blank" rel="noopener">Download PDF</a>
      <a class="btn btn-outline-light" href="#report-highlights">Skip to highlights</a>
    </div>
  </div>
</section>

<div id="flip-lightbox" class="flip-lightbox" aria-hidden="true" role="dialog" aria-label="Annual report full-page view">
  <button class="flip-close" type="button" aria-label="Close">&times;</button>
  <button class="flip-nav flip-prev" type="button" aria-label="Previous page">&#8249;</button>
  <img id="flip-lb-img" src="" alt="Project H.O.O.D. 2025 Annual Report page">
  <button class="flip-nav flip-next" type="button" aria-label="Next page">&#8250;</button>
</div>

<style>
.flipbook{max-width:760px;margin:var(--sp-3) auto 0;}
.flip-stage{position:relative;display:flex;align-items:center;justify-content:center;gap:12px;}
.flip-img{max-width:100%;height:auto;border-radius:6px;box-shadow:0 12px 44px rgba(0,0,0,.55);cursor:zoom-in;background:var(--white);}
.flip-nav{background:rgba(255,255,255,.12);color:var(--white);border:1px solid rgba(255,255,255,.32);border-radius:50%;width:46px;height:46px;font-size:26px;line-height:1;cursor:pointer;flex:0 0 auto;transition:background .15s;}
.flip-nav:hover{background:rgba(255,255,255,.28);}
.flip-meta{margin-top:14px;color:rgba(255,255,255,.82);font-family:var(--font-display);letter-spacing:.06em;text-transform:uppercase;font-size:12.5px;}
.flip-lightbox{display:none;position:fixed;inset:0;background:rgba(0,0,0,.93);z-index:9999;align-items:center;justify-content:center;gap:14px;padding:20px;}
.flip-lightbox.open{display:flex;}
.flip-lightbox img{max-width:90vw;max-height:90vh;height:auto;border-radius:4px;box-shadow:0 12px 44px rgba(0,0,0,.6);}
.flip-close{position:absolute;top:14px;right:20px;background:none;border:none;color:var(--white);font-size:42px;line-height:1;cursor:pointer;}
@media(max-width:600px){.flip-nav{width:40px;height:40px;font-size:22px;}.flip-lightbox .flip-nav{position:absolute;bottom:22px;}.flip-lightbox .flip-prev{left:24px;}.flip-lightbox .flip-next{right:24px;}}
</style>
<script>
(function(){
  var total=13,i=0,base="img/annual-report-2025/page-";
  function src(n){return base+(n<9?"0":"")+(n+1)+".jpg";}
  var img=document.getElementById("flip-img"),count=document.getElementById("flip-count");
  var lb=document.getElementById("flip-lightbox"),lbimg=document.getElementById("flip-lb-img");
  function render(){img.src=src(i);img.alt="Project H.O.O.D. 2025 Annual Report — page "+(i+1)+" of "+total;count.textContent="Page "+(i+1)+" of "+total;if(lb.classList.contains("open"))lbimg.src=src(i);}
  function go(d){i=(i+d+total)%total;render();}
  function open(){lb.classList.add("open");lb.setAttribute("aria-hidden","false");lbimg.src=src(i);document.body.style.overflow="hidden";}
  function close(){lb.classList.remove("open");lb.setAttribute("aria-hidden","true");document.body.style.overflow="";}
  document.querySelectorAll(".flip-prev").forEach(function(b){b.addEventListener("click",function(e){e.stopPropagation();go(-1);});});
  document.querySelectorAll(".flip-next").forEach(function(b){b.addEventListener("click",function(e){e.stopPropagation();go(1);});});
  img.addEventListener("click",open);
  document.querySelector(".flip-close").addEventListener("click",close);
  lb.addEventListener("click",function(e){if(e.target===lb)close();});
  document.addEventListener("keydown",function(e){
    if(e.key==="ArrowLeft")go(-1);
    else if(e.key==="ArrowRight")go(1);
    else if(e.key==="Escape"&&lb.classList.contains("open"))close();
  });
  render();
})();
</script>
"""

# -------- 2025 ANNUAL REPORT --------
annual_report_body = f"""
<section class="hero bg-black">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">Annual Report · 2025</div>
    <h1>A year of <span class="hl-yellow">restoration</span> and hope.</h1>
    <p class="lead">Mentorship, training, and community for the residents of Woodlawn and Englewood. This is what your support built in 2025 &mdash; the lives changed, the doors opened, and the block that keeps showing up.</p>
    <div class="btn-group" style="margin-top:var(--sp-3);">
      <a class="btn btn-yellow" href="#read-report">Read the report now</a>
      <a class="btn btn-outline-light" href="docs/ph-annual-report-2025.pdf" target="_blank" rel="noopener">Download PDF</a>
    </div>
  </div>
</section>

{annual_report_gallery}

<div id="report-highlights"></div>

{ACRONYM_TAPE}

<section class="section">
  <div class="wrap">
    <div class="eyebrow">2025 at a glance</div>
    <h2>The year in numbers.</h2>
    <div class="stat-grid" style="margin-top:var(--sp-3);">
      <div class="stat accent-green"><div class="v">91</div><div class="l">mediations &amp; conflict interventions to prevent community violence</div></div>
      <div class="stat"><div class="v">1,000+</div><div class="l">job seekers connected to employers through job fairs &amp; hiring events</div></div>
      <div class="stat accent-red"><div class="v">34</div><div class="l">graduates earned Carpentry Level 1 &amp; OSHA certifications</div></div>
      <div class="stat"><div class="v">2M+ lbs</div><div class="l">food distributed &mdash; serving 6,500+ families through &ldquo;Everybody Eats&rdquo;</div></div>
      <div class="stat accent-blue"><div class="v">500</div><div class="l">youth served with real pathways forward</div></div>
      <div class="stat accent-yellow"><div class="v">110+</div><div class="l">supported through expungement &amp; job readiness services</div></div>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow" style="color:var(--red);">A letter from our founder</div>
      <h2>Dear friends and supporters,</h2>
      <p>As I reflect on 2025, I am filled with deep gratitude &mdash; for your faith, your generosity, and your willingness to stand with us as we continue building something that is transforming lives every single day on the South Side of Chicago.</p>
      <p>One of the most visible signs of that progress is the continued development of the Leadership &amp; Economic Opportunity Center. With each phase of construction, we are getting closer to opening the doors to a space that will serve as a hub for education, workforce training, entrepreneurship, and opportunity for generations to come.</p>
      <p>On a personal level, this year has been a journey of endurance and faith. While a medical setback and necessary surgery prevented me from continuing the Walk Across America as planned, the mission itself has never stopped. What began as my walk has become something much bigger &mdash; a movement of people across the country choosing to stand for hope, opportunity, and unity. I invite you to #WalkWithUs.</p>
      <p>Thank you for walking with us. Thank you for believing. And thank you for helping us build hope where it is needed most.</p>
      <p style="font-family:var(--font-display);text-transform:uppercase;letter-spacing:.05em;margin-top:var(--sp-2);"><strong>Pastor Corey B. Brooks</strong><br><span style="font-size:14px;color:var(--muted);">Founder &amp; CEO</span></p>
    </div>
    <div style="display:flex;align-items:flex-start;">
      <img src="img/about-pastor-brooks.jpg" alt="Pastor Corey B. Brooks, Founder &amp; CEO of Project H.O.O.D." loading="lazy" style="width:100%;height:auto;border-radius:8px;display:block;">
    </div>
  </div>
</section>

<section class="section bg-green">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">Walk Across America &middot; Walk With Us</div>
    <h2 style="color:var(--white);">One walk became a movement.</h2>
    <p class="lead" style="color:rgba(255,255,255,.9);max-width:var(--w-read);">In 2025, Pastor Corey Brooks took a bold step of faith &mdash; walking across America to raise awareness and support for Project H.O.O.D. When a foot injury required surgery and forced him to pause, the mission didn&rsquo;t stop. It evolved into <strong>Walk With Us</strong>, a nationwide movement inviting supporters to carry the vision forward in their own communities.</p>
    <div class="stat-grid" style="margin-top:var(--sp-3);">
      <div class="stat"><div class="v">$4.3M+</div><div class="l">raised to support the mission</div></div>
      <div class="stat"><div class="v">1,000s</div><div class="l">of miles walked across multiple states</div></div>
      <div class="stat"><div class="v">Nationwide</div><div class="l">awareness generated for Project H.O.O.D.</div></div>
      <div class="stat"><div class="v">Movement</div><div class="l">Walk With Us launched, turning one journey into many</div></div>
    </div>
    <p style="color:rgba(255,255,255,.9);margin-top:var(--sp-3);max-width:var(--w-read);">These funds fuel two critical goals: completing the Leadership &amp; Economic Opportunity Center <strong>debt-free</strong>, and building a sustainable Project H.O.O.D. endowment.</p>
    <div style="margin-top:var(--sp-3);">
      <a class="btn btn-yellow" href="campaigns.html">Join Walk With Us</a>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="eyebrow">Our five pillars</div>
    <h2>Where the work landed in 2025.</h2>
    <p style="max-width:var(--w-read);margin-top:8px;">Violence Prevention · Entrepreneurship &amp; Job Readiness · Health &amp; Wellness · Youth Programming · Re-Entry Services.</p>

    <div class="grid-2" style="margin-top:var(--sp-3);">
      <div class="prog-card pg-green">
        <span class="tag tag-green">Violence Prevention</span>
        <h3>91 mediations · 7,000+ families served</h3>
        <p>Our 12-member Violence Interruption Team works daily to de-escalate conflict and build trust. In 2025 they hosted 88 community events and launched the FLIP Housing Initiative, providing stipends to 7 participants to support housing stability.</p>
        <p style="font-size:14px;color:var(--muted);margin-top:auto;"><strong>Success story:</strong> Facing unemployment and housing instability, Demetrius Pouncy Jr. earned OSHA 10, Forklift, Flagger, and Construction Safety certifications, enrolled in a GED program, and secured a paid role with Windy City Harvest Corps &mdash; and now encourages other young people to choose a different path.</p>
      </div>
      <div class="prog-card">
        <span class="tag tag-red">Entrepreneurship &amp; Job Readiness</span>
        <h3>34 graduates · 1,048 job seekers connected</h3>
        <p>Construction cohorts served 36 participants with 34 graduates. Six job fairs brought together 41+ employers, and we supported 23 entrepreneurs in forming 21 new LLCs &mdash; building a foundation for community wealth.</p>
        <p style="font-size:14px;color:var(--muted);margin-top:auto;"><strong>Success story:</strong> Two graduates were accepted into the Roofers Union and now work with M. Cannon Roofing &mdash; contributing directly to the construction of Project H.O.O.D.&rsquo;s new LEO Center. Full circle.</p>
      </div>
      <div class="prog-card pg-purple">
        <span class="tag tag-purple">Health &amp; Wellness</span>
        <h3>2M+ lbs of food · 6,500+ families</h3>
        <p>Our &ldquo;Everybody Eats&rdquo; drives anchor this work, while the South Side Free Clinic ran 14 clinic days serving 55 patients, and 700+ attended senior &amp; wellness events including Fall Prevention and the Health Care Hiring Job Fair.</p>
        <p style="font-size:14px;color:var(--muted);margin-top:auto;"><strong>Success story:</strong> Seeing rising rates of high blood pressure and diabetes, SSFC launched the HEART Program &mdash; free home blood-pressure monitors, training, physician consultations, and referrals &mdash; helping neighbors take control of their health.</p>
      </div>
      <div class="prog-card pg-blue">
        <span class="tag tag-blue">Youth Programming</span>
        <h3>200 at summer camp · 228 after-school</h3>
        <p>Free &ldquo;Secure The Bag&rdquo; Summer Camp reached 200 youth, with 228 enrolled in after-school programming. Sixteen youth traveled on an international mission trip to Zimbabwe, and our Teen Worker Program delivered hands-on job experience.</p>
        <p style="font-size:14px;color:var(--muted);margin-top:auto;"><strong>Success story:</strong> Camp participant Marcus Easley stood out during our Aviation Nation partnership. His curiosity opened the door to continue exploring aviation beyond the summer &mdash; a camp activity that became a potential career pathway.</p>
      </div>
    </div>

    <div style="margin-top:var(--sp-3);">
      <div class="prog-card" style="border-top-color:var(--gold);">
        <span class="tag" style="background:var(--gold);color:var(--white);">Re-Entry Services · The Rebirth Project</span>
        <h3>110+ supported · 46 through expungement clinics</h3>
        <p>We walk alongside returning citizens through every stage of reentry &mdash; expungement support, job readiness, housing connections, and life skills. In 2025: 25 participants in the reentry cohort, 10 job placements &amp; referrals, 300+ community service hours, and a growing network of 11 partner organizations.</p>
        <p style="font-size:14px;color:var(--muted);"><strong>Success story:</strong> A 25-year-old mother and survivor of domestic violence entered the Rebirth Project seeking a fresh start. After completing the cohort and life-skills training, she secured stable housing and employment, purchased a vehicle, and now takes her son to school each day &mdash; not just stable, but thriving.</p>
      </div>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--purple);">Leadership &amp; Economic Opportunity Center</div>
    <h2>The building goes up.</h2>
    <p style="max-width:var(--w-read);">What began as an idea has taken shape as a transformative space for education, workforce development, entrepreneurship, and community connection on Chicago&rsquo;s South Side. Construction is <strong>about 70% complete.</strong></p>
    <div style="margin-top:var(--sp-3);">
      <div class="progress" style="height:54px;">
        <div class="progress-fill" style="width:70%;font-size:18px;">Construction ~70% complete</div>
      </div>
    </div>
    <div class="grid-2" style="margin-top:var(--sp-3);">
      <ul style="list-style:none;padding:0;margin:0;">
        <li style="padding:10px 0;border-bottom:1px solid var(--line);"><strong>Structural construction</strong> fully completed &mdash; steel framework and exterior buildout</li>
        <li style="padding:10px 0;border-bottom:1px solid var(--line);"><strong>Roofing &amp; building enclosure</strong> completed, securing the full structure</li>
        <li style="padding:10px 0;border-bottom:1px solid var(--line);"><strong>Major interior buildout</strong> underway &mdash; classrooms, workforce training spaces, and common areas</li>
        <li style="padding:10px 0;">Electrical, plumbing &amp; HVAC systems significantly advanced</li>
      </ul>
      <ul style="list-style:none;padding:0;margin:0;">
        <li style="padding:10px 0;border-bottom:1px solid var(--line);"><strong>Gymnasium</strong> and recreational spaces progressing toward completion</li>
        <li style="padding:10px 0;border-bottom:1px solid var(--line);"><strong>Second Chance Hub</strong> and entrepreneurship spaces beginning interior development</li>
        <li style="padding:10px 0;">Site work and surrounding infrastructure continuing to take shape</li>
      </ul>
    </div>
    <div style="margin-top:var(--sp-3);">
      <a class="btn btn-primary" href="leo-center.html">Explore the LEO Center</a>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="eyebrow">2025 Financial Overview</div>
    <h2>Disciplined stewardship.</h2>
    <p style="max-width:var(--w-read);">Project H.O.O.D. closed the year with <strong>$8.9M in total income</strong> and a net surplus of <strong>$348,846</strong> &mdash; reflecting continued growth and disciplined financial stewardship. Nearly <strong>80 cents of every dollar</strong> spent went directly toward mission delivery. Figures below reflect programming operations and do not include construction costs of the LEO Center.</p>
    <div class="stat-grid" style="margin-top:var(--sp-3);">
      <div class="stat accent-green"><div class="v">$8,901,190</div><div class="l">total income</div></div>
      <div class="stat accent-red"><div class="v">$8,554,108</div><div class="l">total expenditures</div></div>
      <div class="stat accent-yellow"><div class="v">$348,846</div><div class="l">net surplus</div></div>
    </div>
    <div class="grid-2" style="margin-top:var(--sp-4);gap:var(--sp-4);">
      <div>
        <h3>Where the income came from</h3>
        <ul style="list-style:none;padding:0;">
          <li style="padding:10px 0;border-bottom:1px solid var(--line);"><strong>63%</strong> &mdash; Contributions &amp; special events (individual, corporate, online, gifts-in-kind, fundraising)</li>
          <li style="padding:10px 0;border-bottom:1px solid var(--line);"><strong>31%</strong> &mdash; Grants (foundation, government, restricted)</li>
          <li style="padding:10px 0;"><strong>7%</strong> &mdash; Violence prevention grant (dedicated safety &amp; prevention programming)</li>
        </ul>
      </div>
      <div>
        <h3>How it was spent</h3>
        <ul style="list-style:none;padding:0;">
          <li style="padding:8px 0;border-bottom:1px solid var(--line);"><strong>49%</strong> &mdash; Programs &amp; direct impact</li>
          <li style="padding:8px 0;border-bottom:1px solid var(--line);"><strong>31%</strong> &mdash; Personnel</li>
          <li style="padding:8px 0;border-bottom:1px solid var(--line);"><strong>7%</strong> &mdash; Marketing &amp; advertising</li>
          <li style="padding:8px 0;border-bottom:1px solid var(--line);"><strong>4%</strong> &mdash; Annual gala</li>
          <li style="padding:8px 0;border-bottom:1px solid var(--line);"><strong>3%</strong> &mdash; Travel &amp; meetings &middot; <strong>3%</strong> other &middot; <strong>2%</strong> outreach &amp; meals</li>
          <li style="padding:8px 0;"><strong>1%</strong> &mdash; Occupancy</li>
        </ul>
      </div>
    </div>
    <p style="margin-top:var(--sp-3);font-size:14px;color:var(--muted);">For full audited financials and 990s, see our <a href="about.html">About page</a>.</p>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap">
    <div class="eyebrow">Leadership</div>
    <h2>Board &amp; staff.</h2>
    <div class="grid-2" style="margin-top:var(--sp-3);gap:var(--sp-4);">
      <div>
        <h3>Board of Directors</h3>
        <p style="margin:0;">Pastor Corey Brooks <span style="color:var(--muted);">(President &amp; Founder)</span>, Steve Bozeman <span style="color:var(--muted);">(Secretary)</span>, Isaac Greene <span style="color:var(--muted);">(Treasurer)</span>, Mike Paulsen, and Patrick Milligan Sr.</p>
        <h3 style="margin-top:var(--sp-3);">Staff leadership</h3>
        <p style="margin:0;">Desmond &ldquo;Dez&rdquo; Marshall <span style="color:var(--muted);">(Executive Director)</span>, Brian Alexander <span style="color:var(--muted);">(COO)</span>, Jeff &ldquo;Rafi&rdquo; Boyd <span style="color:var(--muted);">(Re-Entry Director)</span>, TaWanna Cotton <span style="color:var(--muted);">(Workforce &amp; Resource Director)</span>, Maurita Gholston <span style="color:var(--muted);">(Programming Manager)</span>, Maia Goins <span style="color:var(--muted);">(Director of Operations)</span>, James Highsmith <span style="color:var(--muted);">(Non-Violence Director)</span>, Kristen Kell <span style="color:var(--muted);">(Communications)</span>, Shari Lewis <span style="color:var(--muted);">(Grants &amp; Data)</span>, LaDonna Peppers <span style="color:var(--muted);">(Program Success)</span>, and Arenda Troutman <span style="color:var(--muted);">(Government &amp; Community Relations)</span>.</p>
      </div>
      <div>
        <h3>Advisory Board</h3>
        <p style="margin:0;font-size:14.5px;color:var(--muted);line-height:1.9;">Chuck Adler · Nathan Arant · Larry Berlin · Rick Doering · Richard Edelman · Tom Gallagher · Pastor Keith Gordon · Bill Gorsline · Nick Gowen · Kanye Grau · Jim Hayes · Susan Heymann · Rashod Johnson · Ta&rsquo;Rhonda Jones · Ryan Kunkel · Dan Madura · Talia Maschiach · Patrick Milligan · Leslie Munger · John Munger · Bill O&rsquo;Kane · Jim Oberweis · Marty Ozinga · Mike Paulsen · Jim Purcell · Dr. John Radford · John Reaves · Sean Seay · David Selbst · Dr. Eric Wallace · John Williams · Rob Zappia</p>
      </div>
    </div>
  </div>
</section>

<section class="cta-strip">
  <div class="wrap">
    <h2>Read it all &mdash; then help us make 2026 bigger.</h2>
    <p class="lead" style="max-width:var(--w-read);margin:12px auto var(--sp-2);">The full report has every story, stat, and photo from the year. Your gift keeps this work on the block.</p>
    <div class="btn-group">
      <a class="btn btn-yellow" href="docs/ph-annual-report-2025.pdf" target="_blank" rel="noopener">Download the 2025 report (PDF)</a>
      <a class="btn btn-outline-light" href="https://projecthood.networkforgood.com/">Donate</a>
      <a class="btn btn-outline-light" href="get-involved.html">Get involved</a>
    </div>
  </div>
</section>
"""

# ---------------------------------------------------------------------------
# Registry — (filename, title, meta, active key, body)
# ---------------------------------------------------------------------------
pages = [
    ("index.html",       "Home",                         "Project H.O.O.D. — a community-rooted nonprofit investing in Chicago's South Side through violence prevention, workforce development, health & wellness, youth programming, and re-entry services.", None,            home_body),
    ("about.html",       "About",                        "Project H.O.O.D. was founded by Pastor Corey B. Brooks in 2012. A decade of showing up in Woodlawn.",                                   "a_about",        about_body),
    ("letter.html",      "A Letter from Pastor Brooks",  "A personal message from Project H.O.O.D. founder Pastor Corey Brooks — why he started this work and why he's still here.",                 "a_about",        letter_body),
    ("pastor-brooks.html", "Pastor Corey Brooks",         "Meet Pastor Corey B. Brooks — the “Rooftop Pastor,” founder and CEO of Project H.O.O.D. His story, his letter, and the latest Rooftop Revelations.", "a_about",        pastor_brooks_body),
    ("exec-director.html", "Executive Director",         "Meet Desmond 'Dez' Marshall — Executive Director of Project H.O.O.D. Led the team from 3 to 83 staff, raised $44M+, serves 15,000+ annually.", "a_about",    exec_director_body),
    ("programs.html",    "Programs",                     "Five Pillars, one neighborhood. Violence prevention, workforce development, health & wellness, youth programming, and re-entry services.",         "a_programs",     programs_body),
    ("violence-prevention.html",   "Violence Prevention",    "Creating safer communities in Woodlawn — credible messengers, conflict mediation, and hospital-based intervention.",           "a_programs",     violence_prevention_body),
    ("workforce-development.html", "Workforce Development",  "Job training, placement, and career development on Chicago's South Side. $19/hr average starting wage.",          "a_programs",     workforce_development_body),
    ("construction-cohort.html", "Construction Pre-Apprenticeship", "Paid pre-apprenticeship construction training in Woodlawn, in partnership with Illinois Works. Earn three certifications and a path into the trades. Apply for the next cohort.", "a_programs", construction_cohort_body),
    ("health-wellness.html",       "Health & Wellness",      "Free medical care, counseling, and wellness programs for South Side residents — including the Southside Free Clinic (SSFC).",     "a_programs",     health_wellness_body),
    ("recovery.html",              "Recovery in the H.O.O.D.", "Recovery in the H.O.O.D. — weekly peer-support meetings, monthly Speakerthons, and step-by-step navigation to treatment for South Side neighbors in recovery.", "a_programs",     recovery_body),
    ("youth-programming.html",     "Youth Programming",      "Entrepreneurship training, mentorship, and after-school enrichment — 380 youth enrolled, 94% attendance, 42 summer internships in 2025.", "a_programs",     youth_programming_body),
    ("reentry-services.html",      "Re-Entry Services",      "Second chances, real support — job readiness, housing, counseling, and mentorship for individuals returning from incarceration.",  "a_programs",     reentry_services_body),
    ("impact.html",      "News & Impact",                "Project H.O.O.D. news and 2025 impact — 15,000+ served, 2M+ lbs of food distributed, $19/hr average starting wage, 84% LEO Center funded, plus the latest press.", "a_impact",       impact_body),
    ("annual-report.html", "2025 Annual Report",         "Project H.O.O.D. 2025 Annual Report — $8.9M in total income, the five programming pillars, Walk With Us ($4.3M+ raised), LEO Center at ~70% complete, financials, and board & staff. Download the full PDF.", "a_impact",       annual_report_body),
    ("first-look.html",   "The First Look",               "The First Look \u2014 Project H.O.O.D. donor day. Give, share, and be part of this moment.",                                              "a_gi",           first_look_body),
    ("leo-center.html",  "LEO Center",                   "The Leadership and Economic Opportunity Center — 84% funded, a 90,000 sq ft community hub on S. King Drive.",                        "a_leo",          leo_body),
    ("campaigns.html",   "Walk With Us!",                "Walk With Us! — a nationwide movement to raise $25M for youth, families, and the LEO Center. Give, walk, or start a team on Tiltify.",  "a_campaigns",    campaigns_body),
    ("get-help.html",    "Get Help",                     "How can we help? Free, no-barrier support in Woodlawn — safety, jobs and training, health and counseling, youth programs, re-entry, and food. Call 773-923-8270.", None,             get_help_body),
    ("get-involved.html","Help Somebody",                "Help somebody today — give, volunteer, or partner with Project H.O.O.D.",                                                              "a_gi",           gi_body),
    ("donate.html",      "Donate",                       "Donate securely through NetworkForGood. Your gift stays in Woodlawn.",                                                                 "a_gi",           donate_body),
    ("ways-to-give.html","Ways to Give",                 "Every way to give to Project H.O.O.D. — give online, name a brick in the LEO Center, donate stock or from your DAF, give by check, corporate match, or planned giving. EIN 45-3964886.",              "a_ways",          ways_to_give_body),
    ("volunteer.html",   "Volunteer",                    "Volunteer with Project H.O.O.D. — sign up and we'll match you to an opportunity.",                                                      "a_gi",           volunteer_body),
    ("events.html",      "Community Calendar",           "Community Calendar — upcoming events, workshops, health fairs, youth programs, and gatherings in Woodlawn. RSVP powered by Eventbrite.",  "a_events",       events_body),
    ("partner.html",     "Partner with us",              "Partner with Project H.O.O.D. — corporate, employer, foundation, church partnerships.",                                                 "a_gi",           partner_body),
    ("news.html",        "News & Impact",                "Project H.O.O.D. news and impact — this page now lives at News & Impact.",                                                             None,             news_body),
    ("contact.html",     "Contact",                      "Talk to us — press, partnership, participant, or general inquiry.",                                                                    None,             contact_body),
    ("privacy.html",     "Privacy Policy",               "Project H.O.O.D. privacy policy — what we collect, how we use it, and your rights.",                                               None,             privacy_body),
    ("404.html",         "Page not found",               "This page moved or never existed — here's where to go next.",                                                                          None,             notfound_body),
]

if __name__ == "__main__":
    for fname, title, meta, active, body in pages:
        p = write_page(fname, title, meta, active, body)
        print(f"  wrote {p.name}")
    print(f"\n{len(pages)} pages built at {SITE_DIR}")
