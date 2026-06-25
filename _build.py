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
EVENTBRITE_ORG_ID = "41178041593"
EVENTBRITE_ORG_URL = "https://www.eventbrite.com/o/project-hood-41178041593"

def _eb_fetch_events():
    """
    Fetch upcoming events from Eventbrite API.
    Returns a list of dicts with keys: title, date_str, location, url
    Returns None if token is missing or request fails.
    """
    token = os.environ.get("EVENTBRITE_TOKEN", "").strip()
    if not token:
        return None
    try:
        url = (
            f"https://www.eventbriteapi.com/v3/organizers/{EVENTBRITE_ORG_ID}/events/"
            f"?status=live&order_by=start_asc&expand=venue&time_filter=current_future"
        )
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
            events.append({
                "title": ev.get("name", {}).get("text", "Untitled Event"),
                "date_str": day_str,
                "location": location,
                "url": ev.get("url", EVENTBRITE_ORG_URL),
            })
        return events if events else None
    except Exception as exc:
        print(f"  [Eventbrite] Could not fetch events: {exc}")
        return None

# BG colors cycle for event cards
_EB_COLORS = ["var(--green)", "var(--blue)", "var(--red)", "var(--purple)", "var(--yellow)"]

def _build_event_cards_html(events):
    """Render a grid of event cards from a list of event dicts."""
    cards = []
    for i, ev in enumerate(events):
        color = _EB_COLORS[i % len(_EB_COLORS)]
        safe_title = ev["title"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        safe_loc   = ev["location"].replace("&", "&amp;")
        url = ev["url"]
        cards.append(f"""
      <div class="card" style="padding:0;overflow:hidden;">
        <div class="img-ph" style="min-height:220px;background:{color};">FLYER · save to img/events/</div>
        <div style="padding:16px 18px 18px;">
          <div style="font-size:12px;font-weight:700;color:var(--green);text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;">{ev["date_str"]}</div>
          <h4 style="margin:0 0 6px;">{safe_title}</h4>
          <p style="font-size:13.5px;margin:0 0 12px;color:var(--muted);">{safe_loc} · Free</p>
          <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
            <a class="btn btn-primary" href="{url}" target="_blank" rel="noopener" style="font-size:13px;padding:8px 16px;">RSVP →</a>
            <button class="ph-share-btn" data-title="{safe_title}" data-url="{url}" style="background:transparent;border:1px solid var(--line);border-radius:6px;padding:7px 14px;font-size:13px;cursor:pointer;font-family:var(--font-body);color:var(--ink);">Share</button>
          </div>
        </div>
      </div>""")
    return "\n".join(cards)

# Try fetching live events now; fall back to hardcoded cards if unavailable
_live_events = _eb_fetch_events()
if _live_events:
    print(f"  [Eventbrite] Loaded {len(_live_events)} live events from API ✓")
    _event_cards_html = _build_event_cards_html(_live_events)
else:
    print("  [Eventbrite] No token — using hardcoded event cards")
    _event_cards_html = None   # filled in below with the hardcoded block

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
    <button class="nav-toggle" aria-label="Toggle menu"><span></span><span></span><span></span></button>
    <nav class="nav-links" aria-label="Primary">
      <a href="about.html"{a_about}>About</a>
      <a href="programs.html"{a_programs}>Programs</a>
      <a href="impact.html"{a_impact}>Impact</a>
      <a href="leo-center.html"{a_leo}>LEO Center</a>
      <a href="campaigns.html"{a_campaigns}>Campaigns</a>
      <a href="get-involved.html"{a_gi}>Get Involved</a>
      <a href="news.html"{a_news}>News</a>
      <a href="https://projecthood.networkforgood.com/" class="donate">Donate</a>
    </nav>
  </div>
</header>

<main id="main">
"""

FOOTER = """
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
        <h5>Get Involved</h5>
        <ul>
          <li><a href="get-involved.html">Volunteer</a></li>
          <li><a href="https://projecthood.networkforgood.com/">Donate</a></li>
          <li><a href="events.html">Events</a></li>
          <li><a href="partner.html">Partner with us</a></li>
          <li><a href="https://tiltify.com/project-hood/walk-across-america-2025">Walk With Us!</a></li>
          <li><a href="https://projecthood.networkforgood.com/projects/301372-2026-brick-by-brick-campaign" target="_blank" rel="noopener">Brick by Brick</a></li>
        </ul>
      </div>
      <div>
        <h5>Learn More</h5>
        <ul>
          <li><a href="about.html">About</a></li>
          <li><a href="exec-director.html">Executive Director</a></li>
          <li><a href="programs.html">Programs</a></li>
          <li><a href="impact.html">Impact</a></li>
          <li><a href="leo-center.html">LEO Center</a></li>
          <li><a href="news.html">News</a></li>
          <li><a href="contact.html">Contact</a></li>
        </ul>
      </div>
      <div>
        <h5>Get updates monthly</h5>
        <p style="font-size:13.5px;opacity:.9;">LEO Center progress, program milestones, upcoming events — delivered once a month.</p>
        <div class="nl-input">
          <input type="email" placeholder="you@email.com" aria-label="Email">
          <button type="button">Subscribe</button>
        </div>
        <p style="font-size:11.5px;opacity:.6;margin-top:8px;font-style:italic;">NetworkForGood newsletter embed</p>
      </div>
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

def render(title, meta, active, body):
    active_flags = dict.fromkeys(
        ['a_about','a_programs','a_impact','a_leo','a_campaigns','a_gi','a_news'], '')
    if active:
        active_flags[active] = ' class="active"'
    head = HEAD.format(title=title, meta=meta, **active_flags)
    return head + body + FOOTER

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
    <div class="img-ph" style="min-height:300px;background-image:url('img/home-community.jpg');background-size:cover;background-position:center top;">PHOTO · neighborhood / staff / programs<br><span style="font-size:11px;opacity:.5;">→ img/home-community.jpg</span></div>
  </div>
</section>

{ACRONYM_TAPE}

<!-- STAT BAND -->
<section class="section bg-offwhite">
  <div class="wrap">
    <div class="eyebrow">2025 Impact</div>
    <h2>The numbers on the block.</h2>
    <div class="stat-grid" style="margin-top:var(--sp-3);">
      <div class="stat accent-green"><div class="v">15,000+</div><div class="l">community members served</div></div>
      <div class="stat"><div class="v">2M+ lbs</div><div class="l">food distributed</div></div>
      <div class="stat accent-red"><div class="v">1,048</div><div class="l">job placements</div></div>
      <div class="stat"><div class="v">70%</div><div class="l">LEO Center funded</div></div>
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
        <p style="font-family:var(--font-serif);">Training, certifications, and placement in construction, tech, and skilled trades. 1,048 placements in 2025.</p>
        <a href="programs.html" style="margin-top:auto;">Read more →</a>
      </div>
      <div class="prog-card pg-blue">
        <span class="tag tag-blue">Youth Programming</span>
        <h3 style="margin-top:10px;">Esports &amp; youth enrichment.</h3>
        <p style="font-family:var(--font-serif);">After-school programs, tournaments, and mentorship — meeting kids where they already are.</p>
        <a href="programs.html" style="margin-top:auto;">Read more →</a>
      </div>
      <div class="prog-card pg-purple">
        <span class="tag tag-purple">Health &amp; Wellness</span>
        <h3 style="margin-top:10px;">Counseling &amp; community care.</h3>
        <p style="font-family:var(--font-serif);">Free counseling, group sessions, and crisis response — run by licensed clinicians and peer specialists.</p>
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

<!-- LEO CENTER FEATURE -->
<section class="section bg-black">
  <div class="wrap">
    <div class="grid-2">
      <div class="img-ph dark" style="min-height:300px;background-image:url('img/leo-center-rendering.jpg');background-size:cover;background-position:center top;">LEO CENTER RENDERING<br><span style="font-size:11px;opacity:.5;">→ img/leo-center-rendering.jpg</span></div>
      <div>
        <div class="eyebrow" style="color:var(--yellow);">Capital Campaign</div>
        <h2>A home for everything we do.</h2>
        <p style="font-size:var(--fs-lead);opacity:.9;">The Leadership and Economic Opportunity Center is the physical home of Project H.O.O.D. — a gathering place, a training facility, and a symbol that investment belongs here too.</p>
        <div style="margin-top:24px;">
          <div class="progress" style="background:#1a1718;border-color:var(--yellow);">
            <div class="progress-fill" style="width:70%;">70% Funded</div>
          </div>
        </div>
        <div style="margin-top:24px;display:flex;gap:12px;flex-wrap:wrap;">
          <a class="btn btn-yellow" href="leo-center.html">Learn about LEO</a>
          <a class="btn btn-outline-light" href="https://projecthood.networkforgood.com/">Fund the build</a>
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
    <h2>Give. Volunteer. <span class="hl-yellow">Show up.</span></h2>
    <p style="max-width:640px;margin:0 auto var(--sp-3);opacity:.95;">Three ways to move the work forward. Start with whichever one you can give today.</p>
    <div class="btn-group">
      <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/">Donate</a>
      <a class="btn btn-outline-light" href="get-involved.html">Volunteer</a>
      <a class="btn btn-outline-light" href="events.html">Upcoming events</a>
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
    <div class="img-ph" style="min-height:340px;background-image:url('img/about-mission.jpg');background-size:cover;background-position:center top;">MISSION PHOTO · community or founder<br><span style="font-size:11px;opacity:.5;">→ img/about-mission.jpg</span></div>
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
        <p>Capital campaign launches for the Leadership and Economic Opportunity Center — a 90,000 sq ft community hub on S. King Drive. Groundbreaking in 2022, 70% funded by 2025.</p>
      </div>
      <div>
        <h3>2025 · Walk Across America</h3>
        <p>Pastor Brooks walks 900+ miles from Chicago to New York to raise the final $35M and spotlight what's possible. 15,000+ served this year. 1,048 job placements. 2M+ lbs of food distributed.</p>
      </div>
    </div>
  </div>
</section>

<section class="section bg-black">
  <div class="wrap grid-2">
    <div class="img-ph dark" style="min-height:320px;background-image:url('img/about-pastor-brooks.jpg');background-size:cover;background-position:center top;">FOUNDER PORTRAIT · Pastor Brooks<br><span style="font-size:11px;opacity:.5;">→ img/about-pastor-brooks.jpg</span></div>
    <div>
      <div class="eyebrow" style="color:var(--yellow);">Founder</div>
      <h2 style="color:var(--white);">Pastor Corey B. Brooks</h2>
      <p style="font-size:var(--fs-lead);opacity:.9;">Pastor, entrepreneur, and community organizer. Founder of Project H.O.O.D. and senior pastor of New Beginnings Church of Chicago. Walked across America in 2025 to fund the LEO Center. Known for meeting kids on the corner before asking them to come to church.</p>
      <div style="margin-top:22px;display:flex;gap:12px;flex-wrap:wrap;">
        <a class="btn btn-yellow" href="#">Read Pastor Brooks' letter</a>
        <a class="btn btn-outline-light" href="#">Book Pastor Brooks</a>
      </div>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap grid-2" style="align-items:center;gap:var(--sp-4);">
    <div class="img-ph" style="min-height:340px;font-size:13px;background-image:url('img/desmond-marshall.jpg');background-size:cover;background-position:center top;">
      PHOTO · Desmond "Dez" Marshall<br>
      <span style="font-size:11px;opacity:.5;">→ img/desmond-marshall.jpg</span>
    </div>
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


<section class="section bg-offwhite">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow" style="color:var(--green);">Stewardship</div>
      <h2>Stewardship, on paper.</h2>
      <p>Project H.O.O.D. is a 501(c)(3) public charity. 990s, audited financials, and annual reports are all public.</p>
    </div>
    <div>
      <ul style="list-style:none;padding:0;">
        <li style="padding:14px 0;border-bottom:1px solid var(--line);"><strong>2024 Form 990</strong> · <a href="docs/ph-990-2024.pdf" target="_blank" rel="noopener">Download PDF</a></li>
        <li style="padding:14px 0;border-bottom:1px solid var(--line);"><strong>2023 Form 990</strong> · <a href="#">Download PDF</a></li>
        <li style="padding:14px 0;border-bottom:1px solid var(--line);"><strong>2024 Annual Report</strong> · <a href="#">Download PDF</a></li>
        <li style="padding:14px 0;"><strong>Audited financials</strong> · <a href="#">Download PDF</a></li>
      </ul>
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
        <h3 style="margin-top:12px;">Esports &amp; youth enrichment.</h3>
        <p>After-school programs, academic support, and youth mentorship — built around what kids actually want to do.</p>
        <ul style="font-size:14px;color:var(--muted);margin:var(--sp-2) 0;">
          <li>Esports tournaments + leagues</li>
          <li>Homework + tutoring</li>
          <li>College/career readiness</li>
        </ul>
        <a href="youth-programming.html" class="btn btn-outline" style="align-self:flex-start;margin-top:auto;">About Youth Programming</a>
      </div>
      <div class="prog-card pg-purple">
        <span class="tag tag-purple">04 · Health &amp; Wellness</span>
        <h3 style="margin-top:12px;">Counseling &amp; community care.</h3>
        <p>Free counseling, group work, and crisis response — delivered by licensed clinicians and peer specialists.</p>
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
        <h3 style="margin-top:12px;">Apply to a program.</h3>
        <p>Our case-management system is Social Solutions Apricot. Apply once, and our intake team will route you to the right program and staff member.</p>
        <a href="https://projecthood.socialsolutionsportal.com/apricot-intake/0eb461e5-38a9-4ad1-9a4e-02bb3ee1414d" class="btn btn-primary" style="align-self:flex-start;margin-top:auto;" target="_blank" rel="noopener">Start an application →</a>
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
        src="https://www.youtube.com/embed/lcz6K_F53Fo"
        title="Project H.O.O.D. Summer Camp — Youth Programming"
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

<section class="cta-strip">
  <div class="wrap">
    <h2>Support the outreach team.</h2>
    <div class="btn-group">
      <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/">Fund this pillar</a>
      <a class="btn btn-outline-light" href="get-involved.html">Volunteer</a>
      <a class="btn btn-outline-light" href="https://projecthood.socialsolutionsportal.com/apricot-intake/0eb461e5-38a9-4ad1-9a4e-02bb3ee1414d" target="_blank" rel="noopener">Apply as participant</a>
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
      <h2>Careers, not just jobs.</h2>
      <p>Our Workforce Development pillar equips individuals with the skills, credentials, and connections to build real careers. From construction trades to tech, we partner with employers directly so training leads to placement — not just a certificate.</p>
      <ul>
        <li>Comprehensive job training programs in construction, tech, and logistics</li>
        <li>Job placement support and employer partnerships</li>
        <li>Career development and advancement resources</li>
        <li>Financial literacy and resume building</li>
        <li>Networking opportunities and mentorship</li>
        <li>Pre-Apprenticeship Construction cohort program</li>
      </ul>
      <div style="margin-top:var(--sp-3);">
        <a class="btn btn-primary" href="https://www.projecthood.org/construction-cohort" target="_blank" rel="noopener">Pre-Apprenticeship Construction cohort →</a>
      </div>
    </div>
    <div class="img-ph" style="min-height:380px;background-image:url('img/programs-workforce.jpg');background-size:cover;background-position:center top;">PHOTO · job training / construction cohort<br><span style="font-size:11px;opacity:.5;">→ img/programs-workforce.jpg</span></div>
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
      <div class="stat"><div class="v">1,048</div><div class="l">job placements in 2025</div></div>
      <div class="stat"><div class="v">$19/hr</div><div class="l">average starting wage</div></div>
      <div class="stat"><div class="v">72%</div><div class="l">retained at 6 months</div></div>
      <div class="stat"><div class="v">Multiple</div><div class="l">trades + industries served</div></div>
    </div>
  </div>
</section>

<section class="cta-strip">
  <div class="wrap">
    <h2>Ready to take the first step?</h2>
    <div class="btn-group">
      <a class="btn btn-yellow" href="https://projecthood.socialsolutionsportal.com/apricot-intake/0eb461e5-38a9-4ad1-9a4e-02bb3ee1414d" target="_blank" rel="noopener">Apply as participant</a>
      <a class="btn btn-outline-light" href="https://projecthood.networkforgood.com/">Fund this pillar</a>
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
    <h1>Elevating <span class="hl-yellow">Your Well-Being.</span></h1>
    <p class="lead">Free, quality healthcare and wellness services for South Side residents — because a healthier community is a stronger community.</p>
  </div>
</section>

<section class="section">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">What we do</div>
      <h2>Holistic care, no barriers.</h2>
      <p>Our Health &amp; Wellness pillar addresses the full picture — physical health, mental health, emotional wellness, and social connection. We recognize that healthcare disparities are real, and we work to ensure every South Side resident has equitable access to the care they need regardless of insurance status or income.</p>
      <ul>
        <li>Free medical screenings and health check-ups</li>
        <li>Mental health counseling and therapy</li>
        <li>Group support circles and crisis response</li>
        <li>Fitness programs and social engagement</li>
        <li>Health education and wellness resources</li>
        <li>Referral network to ongoing care providers</li>
      </ul>
    </div>
    <div class="img-ph" style="min-height:380px;background-image:url('img/programs-health-wellness.jpg');background-size:cover;background-position:center top;">PHOTO · health clinic / wellness event<br><span style="font-size:11px;opacity:.5;">→ img/programs-health-wellness.jpg</span></div>
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

<section class="cta-strip">
  <div class="wrap">
    <h2>Ready to take the first step?</h2>
    <div class="btn-group">
      <a class="btn btn-yellow" href="https://projecthood.socialsolutionsportal.com/apricot-intake/0eb461e5-38a9-4ad1-9a4e-02bb3ee1414d" target="_blank" rel="noopener">Apply as participant</a>
      <a class="btn btn-outline-light" href="tel:3127256648">Call SSFC clinic</a>
      <a class="btn btn-outline-light" href="https://projecthood.networkforgood.com/">Fund this pillar</a>
    </div>
  </div>
</section>
"""

# -------- PILLAR 4: YOUTH PROGRAMMING --------
youth_programming_body = f"""
<section class="hero bg-blue">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">Programs · Pillar 4</div>
    <h1>Empowering <span class="hl-yellow">Futures.</span></h1>
    <p class="lead">After-school programs, esports, mentorship, and enrichment — meeting young people where they are and investing in where they're going.</p>
  </div>
</section>

<section class="section">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">What we do</div>
      <h2>Built around what young people actually want to do.</h2>
      <p>Project H.O.O.D.'s Youth Programming is a dynamic, community-centered initiative aimed at empowering young people in Woodlawn and the broader South Side. We break the cycle of poverty and limited opportunity by creating an environment where young people can discover their potential, develop real skills, and build a path forward.</p>
      <ul>
        <li>After-school tutoring and homework assistance</li>
        <li>Esports tournaments, leagues, and competitive teams</li>
        <li>Skills training and enrichment programs</li>
        <li>College and career readiness coaching</li>
        <li>Mentorship from community role models</li>
        <li>Summer internship placement</li>
      </ul>
    </div>
    <div class="img-ph" style="min-height:380px;background-image:url('img/programs-youth.jpg');background-size:cover;background-position:center top;">PHOTO · esports arena / youth programming<br><span style="font-size:11px;opacity:.5;">→ img/programs-youth.jpg</span></div>
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
        <li style="padding:8px 0;border-bottom:1px solid var(--line);">Local esports partners and leagues</li>
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
      <div class="stat"><div class="v">LEO</div><div class="l">400-seat esports arena coming</div></div>
    </div>
  </div>
</section>

<section class="cta-strip">
  <div class="wrap">
    <h2>Ready to take the first step?</h2>
    <div class="btn-group">
      <a class="btn btn-yellow" href="https://projecthood.socialsolutionsportal.com/apricot-intake/0eb461e5-38a9-4ad1-9a4e-02bb3ee1414d" target="_blank" rel="noopener">Apply as participant</a>
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
    <div class="img-ph" style="min-height:380px;background-image:url('img/programs-reentry.jpg');background-size:cover;background-position:center top;">PHOTO · re-entry services / staff<br><span style="font-size:11px;opacity:.5;">→ img/programs-reentry.jpg</span></div>
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
    <div class="eyebrow" style="color:var(--yellow);">Impact</div>
    <h1>What <span class="hl-yellow">shows up</span> on the block.</h1>
    <p class="lead">Every number here is what happened in 2025 in Woodlawn and the surrounding South Side — served, placed, trained, fed, funded.</p>
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
      <div class="stat accent-red"><div class="v">1,048</div><div class="l">job placements</div></div>
      <div class="stat"><div class="v">70%</div><div class="l">LEO Center capital campaign funded</div></div>
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
        <h3>1,048 placements · 72% retained at 6 months</h3>
        <p>Construction trades, tech, and logistics. $19/hr average starting wage. 72% still employed with the same employer six months out.</p>
      </div>
      <div class="prog-card pg-blue">
        <span class="tag tag-blue">Youth Programming</span>
        <h3>380 youth · 94% attendance rate</h3>
        <p>Esports league, tutoring, and mentorship. 94% weekly attendance. 42 youth placed in summer internships.</p>
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
        <div class="progress-fill" style="width:70%;font-size:18px;">$24.5M raised · 70% of $35M</div>
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

<section class="cta-strip">
  <div class="wrap">
    <h2>Help us make 2026 bigger.</h2>
    <div class="btn-group">
      <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/">Donate</a>
      <a class="btn btn-outline-light" href="get-involved.html">Volunteer</a>
      <a class="btn btn-outline-light" href="#">Download 2025 report (PDF)</a>
    </div>
  </div>
</section>
"""

# -------- LEO CENTER --------
leo_body = f"""
<section class="hero bg-black">
  <div class="wrap">
    <div class="hero-split">
      <div>
        <div class="eyebrow" style="color:var(--yellow);">LEO Center</div>
        <h1>The Leadership &amp; <span class="hl-yellow">Economic</span> Opportunity Center.</h1>
        <p class="lead">A 90,000 sq ft community hub on S. King Drive — the physical home of every Project H.O.O.D. program and a signal to Woodlawn that investment belongs here too.</p>
        <div style="margin-top:22px;display:flex;gap:12px;flex-wrap:wrap;">
          <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/">Fund the build</a>
          <a class="btn btn-outline-light" href="campaigns.html">Walk Across America</a>
        </div>
      </div>
      <div class="img-ph dark" style="min-height:340px;background-image:url('img/leo-center-rendering.jpg');background-size:cover;background-position:center top;">LEO CENTER RENDERING / SITE PHOTO<br><span style="font-size:11px;opacity:.5;">→ img/leo-center-rendering.jpg</span></div>
    </div>
  </div>
</section>

<section class="section bg-yellow">
  <div class="wrap" style="text-align:center;">
    <div class="eyebrow">Capital campaign · 2022–2027</div>
    <h2>70% funded. <span style="background:var(--black);color:var(--yellow);padding:2px 12px;">$10.5M to go.</span></h2>
    <div style="max-width:720px;margin:var(--sp-3) auto 0;">
      <div class="progress" style="height:54px;">
        <div class="progress-fill" style="width:70%;font-size:18px;">$24.5M raised · 70% of $35M</div>
      </div>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap" style="max-width:900px;">
    <div class="eyebrow" style="text-align:center;">The vision</div>
    <h2 style="text-align:center;margin-bottom:var(--sp-3);">See what we're building.</h2>
    <div style="position:relative;width:100%;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:8px;box-shadow:0 8px 32px rgba(0,0,0,.18);">
      <iframe
        src="https://www.youtube.com/embed/NHNPy5tFCiw"
        title="LEO Center — Leadership &amp; Economic Opportunity Center"
        frameborder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen
        style="position:absolute;top:0;left:0;width:100%;height:100%;">
      </iframe>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">What it is</div>
      <h2>One building, five pillars, one neighborhood.</h2>
      <p>The LEO Center brings every Project H.O.O.D. pillar under one roof: workforce training classrooms, health &amp; wellness counseling suites, esports arena, re-entry services hub, outreach team offices, community kitchen, and a 400-seat multipurpose hall.</p>
      <p>It's being built on land owned by Project H.O.O.D., directly on S. King Drive — a deliberate statement that serious investment belongs on the South Side.</p>
    </div>
    <div class="img-ph" style="min-height:360px;background-image:url('img/leo-center-floorplan.jpg');background-size:cover;background-position:center top;">FLOOR PLAN OR RENDERING<br><span style="font-size:11px;opacity:.5;">→ img/leo-center-floorplan.jpg</span></div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--green);">Inside the LEO</div>
    <h2>What fits inside 90,000 sq ft.</h2>
    <div class="grid-3" style="margin-top:var(--sp-3);">
      <div class="card card-accent"><h3>Training wing</h3><p>Construction trades, tech bootcamp, OSHA classroom, direct-hire employer partners on-site.</p></div>
      <div class="card card-accent" style="border-top-color:var(--blue);"><h3>Youth + Esports</h3><p>400-seat arena, tournament stage, tutoring rooms, after-school program base.</p></div>
      <div class="card card-accent" style="border-top-color:var(--purple);"><h3>Counseling suites</h3><p>Private offices for therapists, group rooms, play-therapy space, crisis intake.</p></div>
      <div class="card card-accent" style="border-top-color:#8a6d00;"><h3>Business incubator</h3><p>Co-working floor for Woodlawn entrepreneurs, grant desk, legal/financial clinic.</p></div>
      <div class="card card-accent" style="border-top-color:var(--green);"><h3>Community kitchen</h3><p>Food distribution, community dinners, culinary training program, event catering.</p></div>
      <div class="card card-accent" style="border-top-color:var(--black);"><h3>Outreach HQ</h3><p>24/7 response team base, de-escalation rooms, family-support space.</p></div>
    </div>
  </div>
</section>

<section class="section bg-black">
  <div class="wrap">
    <div class="testimonial" style="border-left-color:var(--yellow);">
      <blockquote>"The LEO Center isn't a building. It's a proof that investment belongs here too. When it opens, we stop having to ask for permission."</blockquote>
      <cite>— Pastor Corey B. Brooks</cite>
    </div>
  </div>
</section>

<section class="cta-strip">
  <div class="wrap">
    <h2>Help us close the last <span class="hl-yellow">$10.5M.</span></h2>
    <div class="btn-group">
      <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/">Give to the build</a>
      <a class="btn btn-outline-light" href="campaigns.html">Walk Across America</a>
      <a class="btn btn-outline-light" href="contact.html">Name a space</a>
    </div>
  </div>
</section>
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
    <div class="eyebrow" style="color:var(--yellow);">Get Involved</div>
    <h1>Three ways to <span class="hl-yellow">move the work forward.</span></h1>
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
<section class="hero bg-red">
  <div class="wrap hero-split">
    <div>
      <div class="eyebrow" style="color:var(--yellow);">Donate</div>
      <h1>Your gift <span class="hl-yellow">stays</span> in Woodlawn.</h1>
      <p class="lead">Every dollar funds programs on the block. No national overhead, no middle layer. Give securely through NetworkForGood — our partner platform since day one.</p>
      <div style="margin-top:22px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
        <a class="btn btn-yellow" style="font-size:16px;padding:16px 28px;" href="https://projecthood.networkforgood.com/">Give now →</a>
        <span style="font-family:var(--font-serif);font-style:italic;font-size:13px;opacity:.85;">opens projecthood.networkforgood.com in a new tab</span>
      </div>
      <p style="font-size:12px;opacity:.8;margin-top:12px;">Tax-deductible · EIN 45-3964886 · takes under 2 minutes</p>
    </div>
    <div style="background:rgba(255,255,255,.12);padding:22px;border-left:4px solid var(--yellow);">
      <div class="eyebrow" style="color:var(--yellow);margin-bottom:8px;">How your gift is used</div>
      <ul style="list-style:none;padding:0;margin:0;font-family:var(--font-serif);font-size:15px;line-height:1.85;">
        <li><strong>$50</strong> · feeds a family for a week</li>
        <li><strong>$250</strong> · sponsors a training cohort seat</li>
        <li><strong>$1,000</strong> · funds an outreach worker's week</li>
        <li><strong>$5,000+</strong> · names a LEO Center space</li>
      </ul>
    </div>
  </div>
</section>

<section class="section bg-blue">
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

<section class="section">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--green);">Other ways to give</div>
    <div class="grid-4" style="margin-top:var(--sp-3);">
      <div class="card"><h4>Stock &amp; Securities</h4><p style="font-size:13.5px;">Donate appreciated stock directly — avoid capital gains, maximize your impact.</p><a href="ways-to-give.html#stock" style="font-size:13px;color:var(--green);font-weight:600;">How it works →</a></div>
      <div class="card"><h4>Donor-Advised Fund</h4><p style="font-size:13.5px;">Grant from your Fidelity Charitable, Schwab, or Vanguard DAF using EIN 45-3964886.</p><a href="ways-to-give.html#daf" style="font-size:13px;color:var(--green);font-weight:600;">DAF details →</a></div>
      <div class="card"><h4>Check by mail</h4><p style="font-size:13.5px;">Project H.O.O.D.<br>6620 S. King Drive<br>Chicago IL 60637</p></div>
      <div class="card"><h4>Planned &amp; corporate</h4><p style="font-size:13.5px;">Bequests, beneficiary designations, or employer matching.</p><a href="ways-to-give.html" style="font-size:13px;color:var(--green);font-weight:600;">All options →</a></div>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap grid-2" style="align-items:center;">
    <div>
      <div class="eyebrow" style="color:var(--red);">Stay connected</div>
      <h2>Get updates once a month. No spam.</h2>
      <p>LEO Center progress, program milestones, upcoming events — delivered via NetworkForGood.</p>
    </div>
    <div style="background:var(--white);padding:20px;border:1px solid var(--line);">
      <div class="eyebrow" style="color:var(--muted);margin-bottom:10px;font-size:10.5px;">NFG Newsletter embed</div>
      <input type="email" placeholder="you@email.com" style="width:100%;padding:12px;border:1px solid var(--line);font-family:var(--font-serif);font-size:14px;margin-bottom:8px;">
      <button class="btn btn-primary" style="width:100%;padding:12px;">Subscribe</button>
    </div>
  </div>
</section>
"""

# -------- WAYS TO GIVE --------
ways_to_give_body = f"""
<section class="hero bg-green">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">Ways to Give</div>
    <h1>Every dollar <span class="hl-yellow">stays</span> in Woodlawn.</h1>
    <p class="lead">Give online, by stock, through your donor-advised fund, or by mail. Every method is tax-deductible. EIN 45-3964886.</p>
  </div>
</section>

<!-- NAV ANCHORS -->
<section class="section-sm" style="border-bottom:1px solid var(--line);background:var(--white);">
  <div class="wrap" style="display:flex;gap:24px;font-family:var(--font-display);text-transform:uppercase;font-size:12px;letter-spacing:.12em;flex-wrap:wrap;">
    <a href="#online" style="color:var(--ink);text-decoration:none;">Online</a>
    <a href="#stock" style="color:var(--ink);text-decoration:none;">Stock &amp; Securities</a>
    <a href="#daf" style="color:var(--ink);text-decoration:none;">Donor-Advised Fund</a>
    <a href="#check" style="color:var(--ink);text-decoration:none;">Check / Mail</a>
    <a href="#match" style="color:var(--ink);text-decoration:none;">Corporate Match</a>
    <a href="#planned" style="color:var(--ink);text-decoration:none;">Planned Giving</a>
  </div>
</section>

<!-- ONLINE -->
<section class="section" id="online">
  <div class="wrap grid-2" style="align-items:center;gap:var(--sp-6);">
    <div>
      <div class="eyebrow" style="color:var(--green);">Fastest · Most flexible</div>
      <h2>Give online</h2>
      <p>Credit card, debit, or bank transfer via NetworkForGood — our secure partner platform. Choose a one-time or recurring gift and designate your fund.</p>
      <ul style="margin:12px 0 20px;padding-left:18px;font-size:14.5px;line-height:2;">
        <li>One-time or monthly recurring</li>
        <li>Designate to a specific program</li>
        <li>Receipt emailed instantly</li>
        <li>Processing fee optional to cover</li>
      </ul>
      <a class="btn btn-primary" style="font-size:15px;padding:14px 26px;" href="https://projecthood.networkforgood.com/" target="_blank" rel="noopener">Donate now →</a>
      <p style="font-size:11.5px;color:var(--muted);margin-top:8px;">Opens projecthood.networkforgood.com</p>
    </div>
    <div style="background:var(--offwhite);padding:24px;border-left:4px solid var(--green);">
      <div class="eyebrow" style="color:var(--muted);margin-bottom:10px;">What your gift funds</div>
      <ul style="list-style:none;padding:0;margin:0;font-family:var(--font-serif);font-size:15px;line-height:2.1;">
        <li><strong>$50</strong> · feeds a family for a week</li>
        <li><strong>$250</strong> · sponsors a training cohort seat</li>
        <li><strong>$1,000</strong> · funds an outreach worker's week</li>
        <li><strong>$5,000+</strong> · names a LEO Center space</li>
      </ul>
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
        <!-- DonateStock embed — register free at donatestock.com → add Project H.O.O.D. → copy your widget code here -->
        <div style="background:var(--offwhite);border:2px dashed var(--line);padding:18px;text-align:center;border-radius:8px;margin-bottom:4px;">
          <p style="font-size:12px;color:var(--muted);margin:0 0 10px;font-family:var(--font-display);text-transform:uppercase;letter-spacing:.08em;">DonateStock widget · activate at donatestock.com</p>
          <a class="btn btn-primary" href="https://www.donatestock.com" target="_blank" rel="noopener" style="font-size:14px;">Donate Stock →</a>
        </div>
        <p style="font-size:11.5px;color:var(--muted);font-style:italic;">Once your DonateStock account is set up, replace the button above with your personalized widget code.</p>
      </div>
      <div class="card" style="border-top:4px solid var(--blue);">
        <h4 style="margin-top:0;">Option B — Direct broker transfer</h4>
        <p style="font-size:13.5px;">Contact your broker and instruct them to transfer shares directly. You will need the following information:</p>
        <table style="font-size:13.5px;width:100%;border-collapse:collapse;margin:8px 0 16px;">
          <tr style="border-bottom:1px solid var(--line);"><td style="padding:7px 4px;font-weight:700;width:38%;color:var(--muted);">Brokerage</td><td style="padding:7px 4px;">[Add brokerage name]</td></tr>
          <tr style="border-bottom:1px solid var(--line);"><td style="padding:7px 4px;font-weight:700;color:var(--muted);">DTC number</td><td style="padding:7px 4px;">[Add DTC #]</td></tr>
          <tr style="border-bottom:1px solid var(--line);"><td style="padding:7px 4px;font-weight:700;color:var(--muted);">Account #</td><td style="padding:7px 4px;">[Add account #]</td></tr>
          <tr style="border-bottom:1px solid var(--line);"><td style="padding:7px 4px;font-weight:700;color:var(--muted);">Account name</td><td style="padding:7px 4px;">Project H.O.O.D.</td></tr>
          <tr><td style="padding:7px 4px;font-weight:700;color:var(--muted);">For credit to</td><td style="padding:7px 4px;">Project H.O.O.D. — EIN 45-3964886</td></tr>
        </table>
        <p style="font-size:13px;padding:10px 12px;background:var(--offwhite);border-left:3px solid var(--blue);margin:0;"><strong>Important:</strong> Please notify us when you initiate the transfer so we can credit your gift. Email <a href="mailto:development@projecthood.org">development@projecthood.org</a> with your name, stock name, and share count.</p>
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
          <tr style="border-bottom:1px solid var(--line);"><td style="padding:8px 4px;font-weight:700;color:var(--muted);">Address</td><td style="padding:8px 4px;">6620 S. King Drive<br>Chicago, IL 60637</td></tr>
          <tr><td style="padding:8px 4px;font-weight:700;color:var(--muted);">Contact</td><td style="padding:8px 4px;"><a href="mailto:development@projecthood.org">development@projecthood.org</a></td></tr>
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
        <p style="font-size:13.5px;">Search by EIN <strong>45-3964886</strong> or email <a href="mailto:development@projecthood.org">development@projecthood.org</a> — we can provide any additional documentation your sponsor needs.</p>
      </div>
    </div>
  </div>
</section>

<!-- CHECK + MATCH + PLANNED -->
<section class="section bg-offwhite" id="check">
  <div class="wrap">
    <div class="grid-3" style="gap:var(--sp-4);">

      <div class="card card-accent" style="border-top-color:var(--green);">
        <h4>Check or money order</h4>
        <p style="font-size:13.5px;">Make checks payable to <strong>Project H.O.O.D.</strong> and mail to:</p>
        <address style="font-style:normal;font-size:14px;line-height:1.85;padding:12px;background:var(--offwhite);margin:12px 0;">
          Project H.O.O.D.<br>
          6620 S. King Drive<br>
          Chicago, IL 60637
        </address>
        <p style="font-size:12.5px;color:var(--muted);">Include your name and email address on the memo line to receive a tax receipt.</p>
      </div>

      <div class="card card-accent" id="match" style="border-top-color:var(--blue);">
        <h4>Corporate matching</h4>
        <p style="font-size:13.5px;">Many employers match charitable gifts dollar-for-dollar — doubling or tripling your impact at no extra cost to you.</p>
        <ol style="font-size:13.5px;padding-left:18px;line-height:1.85;margin-bottom:12px;">
          <li>Check with your HR or benefits team</li>
          <li>Submit your donation receipt through your company's matching portal</li>
          <li>Your employer sends a matching gift to Project H.O.O.D.</li>
        </ol>
        <p style="font-size:12.5px;color:var(--muted);">Need our EIN or W-9? Email <a href="mailto:development@projecthood.org">development@projecthood.org</a></p>
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
        <p style="font-size:12.5px;color:var(--muted);">To discuss planned giving options, contact <a href="mailto:development@projecthood.org">development@projecthood.org</a> — we're honored to talk through your legacy goals.</p>
      </div>

    </div>
  </div>
</section>

<!-- BOTTOM CTA -->
<section class="section bg-red" style="text-align:center;">
  <div class="wrap" style="max-width:600px;margin:0 auto;">
    <h2 style="color:var(--white);">Questions about giving?</h2>
    <p style="color:var(--white);opacity:.95;font-size:15.5px;">Our development team is here to help. Whether you're planning a major gift, want to visit in person, or need a W-9 or 990 — reach out.</p>
    <a class="btn btn-yellow" style="margin-top:10px;font-size:15px;padding:14px 26px;" href="mailto:development@projecthood.org">development@projecthood.org</a>
    <p style="color:var(--white);font-size:12px;opacity:.75;margin-top:14px;">Project H.O.O.D. is a 501(c)(3) nonprofit · EIN 45-3964886 · All gifts are tax-deductible to the extent allowed by law.</p>
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
        <li><strong>Youth programs:</strong> tutoring, esports coaching, field trips</li>
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
        <a class="btn btn-primary" href="https://docs.google.com/forms/d/e/1FAIpQLSfulIcBaCRzjDaNXuMuV-fgo_LxqOoXNQG8FU7ibIOuI_6-FA/viewform" style="margin-top:12px;">Volunteer signup form →</a>
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
# Hardcoded event cards — used when EVENTBRITE_TOKEN is not set
_hardcoded_cards = """
      <div class="card" style="padding:0;overflow:hidden;">
        <div class="img-ph" style="min-height:220px;background:var(--green);">FLYER · save to img/events/</div>
        <div style="padding:16px 18px 18px;">
          <div style="font-size:12px;font-weight:700;color:var(--green);text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;">Thu, Jun 25 · 10:00 AM – 1:00 PM</div>
          <h4 style="margin:0 0 6px;">Community Job Fair &amp; Resource Fair</h4>
          <p style="font-size:13.5px;margin:0 0 12px;color:var(--muted);">Woodlawn · Free</p>
          <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
            <a class="btn btn-primary" href="https://www.eventbrite.com/o/project-hood-41178041593" target="_blank" rel="noopener" style="font-size:13px;padding:8px 16px;">RSVP →</a>
            <button class="ph-share-btn" data-title="Community Job Fair &amp; Resource Fair" data-url="https://www.eventbrite.com/o/project-hood-41178041593" style="background:transparent;border:1px solid var(--line);border-radius:6px;padding:7px 14px;font-size:13px;cursor:pointer;font-family:var(--font-body);color:var(--ink);">Share</button>
          </div>
        </div>
      </div>

      <div class="card" style="padding:0;overflow:hidden;">
        <div class="img-ph" style="min-height:220px;background:var(--blue);">FLYER · save to img/events/</div>
        <div style="padding:16px 18px 18px;">
          <div style="font-size:12px;font-weight:700;color:var(--green);text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;">Sun, Jun 28 · 10:00 AM – 3:00 PM</div>
          <h4 style="margin:0 0 6px;">Community Day 2026</h4>
          <p style="font-size:13.5px;margin:0 0 12px;color:var(--muted);">6620 S King Dr · Free</p>
          <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
            <a class="btn btn-primary" href="https://www.eventbrite.com/e/community-day-2026-tickets-1992501020188" target="_blank" rel="noopener" style="font-size:13px;padding:8px 16px;">RSVP →</a>
            <button class="ph-share-btn" data-title="Community Day 2026" data-url="https://www.eventbrite.com/e/community-day-2026-tickets-1992501020188" style="background:transparent;border:1px solid var(--line);border-radius:6px;padding:7px 14px;font-size:13px;cursor:pointer;font-family:var(--font-body);color:var(--ink);">Share</button>
          </div>
        </div>
      </div>

      <div class="card" style="padding:0;overflow:hidden;">
        <div class="img-ph" style="min-height:220px;background:var(--red);">FLYER · save to img/events/</div>
        <div style="padding:16px 18px 18px;">
          <div style="font-size:12px;font-weight:700;color:var(--green);text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;">Wed, Jul 1 · 4:00 PM – 7:00 PM</div>
          <h4 style="margin:0 0 6px;">Christmas in July</h4>
          <p style="font-size:13.5px;margin:0 0 12px;color:var(--muted);">West 66th Street · Free</p>
          <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
            <a class="btn btn-primary" href="https://www.eventbrite.com/e/christmas-in-july-tickets-1992501767423" target="_blank" rel="noopener" style="font-size:13px;padding:8px 16px;">RSVP →</a>
            <button class="ph-share-btn" data-title="Christmas in July" data-url="https://www.eventbrite.com/e/christmas-in-july-tickets-1992501767423" style="background:transparent;border:1px solid var(--line);border-radius:6px;padding:7px 14px;font-size:13px;cursor:pointer;font-family:var(--font-body);color:var(--ink);">Share</button>
          </div>
        </div>
      </div>

      <div class="card" style="padding:0;overflow:hidden;">
        <div class="img-ph" style="min-height:220px;background:var(--purple);">FLYER · save to img/events/</div>
        <div style="padding:16px 18px 18px;">
          <div style="font-size:12px;font-weight:700;color:var(--green);text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;">Fri, Aug 7 · 4:00 PM</div>
          <h4 style="margin:0 0 6px;">Trunk Party 2026</h4>
          <p style="font-size:13.5px;margin:0 0 12px;color:var(--muted);">6620 S King Dr · Free</p>
          <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
            <a class="btn btn-primary" href="https://www.eventbrite.com/e/trunk-party-2026-tickets-1992502132515" target="_blank" rel="noopener" style="font-size:13px;padding:8px 16px;">RSVP →</a>
            <button class="ph-share-btn" data-title="Trunk Party 2026" data-url="https://www.eventbrite.com/e/trunk-party-2026-tickets-1992502132515" style="background:transparent;border:1px solid var(--line);border-radius:6px;padding:7px 14px;font-size:13px;cursor:pointer;font-family:var(--font-body);color:var(--ink);">Share</button>
          </div>
        </div>
      </div>
"""

# Pick live API cards if available, otherwise hardcoded fallback
_eb_cards = _event_cards_html if _event_cards_html else _hardcoded_cards

events_body = f"""
<section class="hero bg-yellow" style="color:var(--black);">
  <div class="wrap">
    <div class="eyebrow">Community Calendar</div>
    <h1>On the <span style="background:var(--red);color:var(--white);padding:2px 10px;transform:rotate(-1.5deg);display:inline-block;">calendar.</span></h1>
    <p class="lead" style="opacity:1;color:var(--ink);">Programming, workshops, health fairs, and community gatherings across Woodlawn. Staff adds an event to Eventbrite — it shows here automatically. No code needed.</p>
  </div>
</section>

<!-- TAB BAR -->
<section class="section-sm" style="border-bottom:1px solid var(--line);background:var(--white);">
  <div class="wrap" style="display:flex;gap:24px;font-family:var(--font-display);text-transform:uppercase;font-size:12.5px;letter-spacing:.14em;align-items:center;flex-wrap:wrap;">
    <span style="color:var(--red);border-bottom:2px solid var(--red);padding-bottom:4px;">Upcoming</span>
    <span style="color:var(--muted);">Past events</span>
    <div style="margin-left:auto;">
      <a href="https://www.eventbrite.com/o/project-hood-41178041593" target="_blank" rel="noopener" style="font-family:var(--font-serif);text-transform:none;letter-spacing:0;font-size:12.5px;color:var(--muted);font-style:italic;">View all on Eventbrite →</a>
    </div>
  </div>
</section>

<!-- EVENT CARDS — auto-populated from Eventbrite API when EVENTBRITE_TOKEN is set;
     otherwise uses the hardcoded cards below. See _build.py header for setup. -->
<section class="section">
  <div class="wrap">

    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:20px;">
{_eb_cards}
    </div>
    <!-- ═══ END EVENT CARDS ═══ -->

    <!-- ═══ EVENTBRITE WIDGET — when your org is set up on Eventbrite,
         replace the card grid above with the embed snippet from:
         eventbrite.com → Manage → Widgets → Collection Widget
         It will look like:
           <div id="ph-eb-widget"></div>
           <script src="https://www.eventbrite.com/static/widgets/eb_widgets.js"></script>
           <script>
             window.EBWidgets.createWidget({{
               widgetType: 'collection',
               collectionId: 'YOUR_COLLECTION_ID',
               iframeContainerDiv: 'ph-eb-widget'
             }});
           </script>
         ═══ -->

  </div>
</section>

<!-- STAFF HOW-TO -->
<section class="section bg-offwhite">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--muted);">Staff: how to post an event</div>
    <div class="grid-4" style="margin-top:12px;">
      <div class="card card-accent" style="border-top-color:var(--green);"><h4>1 · Sign in</h4><p style="font-size:13px;">Go to eventbrite.com and sign into the Project H.O.O.D. organization. Ask Brian to add you if you don't have access yet.</p></div>
      <div class="card card-accent" style="border-top-color:var(--blue);"><h4>2 · Create</h4><p style="font-size:13px;">Click <strong>Create event</strong>. Upload your flyer as the event image — it becomes the card banner on this page.</p></div>
      <div class="card card-accent" style="border-top-color:var(--red);"><h4>3 · Publish</h4><p style="font-size:13px;">Fill in date, time, location, and set ticket type to <strong>Free</strong>. Hit Publish — it appears on this page automatically.</p></div>
      <div class="card card-accent" style="border-top-color:var(--yellow);"><h4>4 · Share</h4><p style="font-size:13px;">Copy the event URL from Eventbrite and share it — or use the Share button on this page. Eventbrite emails confirmations to all registrants.</p></div>
    </div>
    <p style="font-size:12px;color:var(--muted);margin-top:12px;font-style:italic;">Need access? Email brian@projecthood.org — Eventbrite lets you assign Admin or Manager roles per team member.</p>
  </div>
</section>

<script>
(function() {{
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
      <div style="background:var(--offwhite);padding:var(--sp-4);border:2px dashed var(--line);">
        <p style="font-family:var(--font-display);text-transform:uppercase;letter-spacing:.1em;font-size:12px;color:var(--muted);">Google Form embed · on real site</p>
        <h3 style="margin:10px 0;">Partner Inquiry Form</h3>
        <p style="font-size:14px;">Org name, contact, type of partnership, what you bring, what you need. Routes to our development team.</p>
        <a class="btn btn-primary" href="https://docs.google.com/forms/d/e/1FAIpQLSeSqdS_4Cyd4gdWyvAuJEGF3zR4MFqKsiOPDDRUKUsBMEDNKQ/viewform" style="margin-top:12px;">Partner inquiry form →</a>
      </div>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap">
    <div class="eyebrow">Current partners</div>
    <h2>Who we work with.</h2>
    <div class="grid-4" style="margin-top:var(--sp-3);">
      <div class="card" style="text-align:center;">[Logo]</div>
      <div class="card" style="text-align:center;">[Logo]</div>
      <div class="card" style="text-align:center;">[Logo]</div>
      <div class="card" style="text-align:center;">[Logo]</div>
      <div class="card" style="text-align:center;">[Logo]</div>
      <div class="card" style="text-align:center;">[Logo]</div>
      <div class="card" style="text-align:center;">[Logo]</div>
      <div class="card" style="text-align:center;">[Logo]</div>
    </div>
    <p style="font-size:13px;color:var(--muted);margin-top:12px;font-style:italic;">Logo wall populated in next build round from the partner list you approve.</p>
  </div>
</section>
"""

# -------- NEWS --------
news_body = f"""
<section class="hero bg-black">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">News &amp; updates</div>
    <h1>What we're <span class="hl-yellow">writing about.</span></h1>
    <p class="lead">Program milestones, LEO Center progress, stories from the block, press mentions.</p>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="grid-2">
      <div class="card card-accent" style="border-top-color:var(--green);">
        <div class="eyebrow">Feb 28, 2026 · Workforce</div>
        <h3>1,048 placements: what the 2025 cohort taught us.</h3>
        <p>What worked, what didn't, and what we're changing for the 2026 cohort. A candid look at retention, wages, and employer relationships.</p>
        <a href="#" style="margin-top:auto;">Read →</a>
      </div>
      <div class="card card-accent" style="border-top-color:var(--red);">
        <div class="eyebrow">Feb 12, 2026 · LEO Center</div>
        <h3>70% funded. Here's the plan for the final $10.5M.</h3>
        <p>Board update on the capital campaign — named-gift opportunities, foundation matches, and what the completed building unlocks.</p>
        <a href="#" style="margin-top:auto;">Read →</a>
      </div>
      <div class="card card-accent" style="border-top-color:var(--blue);">
        <div class="eyebrow">Jan 20, 2026 · Violence Prevention</div>
        <h3>How we mediated 140+ incidents in 2025.</h3>
        <p>Inside the outreach team — who they are, how the hospital-based intervention partnership works, and why the approach keeps spreading.</p>
        <a href="#" style="margin-top:auto;">Read →</a>
      </div>
      <div class="card card-accent" style="border-top-color:var(--purple);">
        <div class="eyebrow">Dec 18, 2025 · Health &amp; Wellness</div>
        <h3>Free counseling, no waitlist: the 2025 clinical report.</h3>
        <p>520 sessions delivered, 0 cost to participants. How we funded it, what we're expanding for 2026.</p>
        <a href="#" style="margin-top:auto;">Read →</a>
      </div>
      <div class="card card-accent" style="border-top-color:#8a6d00;">
        <div class="eyebrow">Nov 30, 2025 · WAA</div>
        <h3>Pastor Brooks finishes the walk. The work doesn't stop.</h3>
        <p>900+ miles, $8M raised on the route. What's next for Walk Across America 2026.</p>
        <a href="#" style="margin-top:auto;">Read →</a>
      </div>
      <div class="card card-accent">
        <div class="eyebrow">Nov 6, 2025 · Press</div>
        <h3>Chicago Tribune: "The block that refuses to be overlooked."</h3>
        <p>Front-page feature on Project H.O.O.D.'s decade of work. Link to the full piece.</p>
        <a href="#" style="margin-top:auto;">Read →</a>
      </div>
    </div>
    <p style="margin-top:var(--sp-4);font-size:13px;color:var(--muted);font-style:italic;">All posts are placeholder content for the preview. Real posts get added via the <code>/admin</code> panel once the site is live.</p>
  </div>
</section>
"""

# -------- CONTACT --------
contact_body = f"""
<section class="hero bg-green">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">Contact</div>
    <h1>Talk to us.</h1>
    <p class="lead">Press, partnership, participant inquiry, or general question — we answer every message.</p>
  </div>
</section>

<section class="section">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">Direct lines</div>
      <h2>By topic.</h2>
      <ul style="list-style:none;padding:0;font-family:var(--font-serif);">
        <li style="padding:12px 0;border-bottom:1px solid var(--line);"><strong>General:</strong> info@projecthood.org</li>
        <li style="padding:12px 0;border-bottom:1px solid var(--line);"><strong>Development / donations:</strong> development@projecthood.org</li>
        <li style="padding:12px 0;border-bottom:1px solid var(--line);"><strong>Volunteer coordinator:</strong> volunteer@projecthood.org</li>
        <li style="padding:12px 0;border-bottom:1px solid var(--line);"><strong>Press / media:</strong> press@projecthood.org</li>
        <li style="padding:12px 0;border-bottom:1px solid var(--line);"><strong>Events:</strong> events@projecthood.org</li>
        <li style="padding:12px 0;"><strong>Participant intake:</strong> intake@projecthood.org</li>
      </ul>
      <div style="margin-top:var(--sp-3);">
        <strong>Office:</strong><br>
        Project H.O.O.D.<br>
        6620 S. King Drive<br>
        Chicago, IL 60637<br>
        <br>
        <strong>Phone:</strong> (773) XXX-XXXX
      </div>
    </div>
    <div>
      <div class="eyebrow" style="color:var(--red);">Send a message</div>
      <div style="background:var(--offwhite);padding:var(--sp-4);border:2px dashed var(--line);">
        <p style="font-family:var(--font-display);text-transform:uppercase;letter-spacing:.1em;font-size:12px;color:var(--muted);">Google Form embed · on real site</p>
        <h3 style="margin:10px 0;">Contact form</h3>
        <p style="font-size:14px;">Name, email, topic dropdown, message. Routes to the right inbox based on topic.</p>
        <a class="btn btn-primary" href="https://docs.google.com/forms/d/e/1FAIpQLSezt7dj_hycF7Y45m-Dcls6-52SCGS2sd-NkMDogWDhh_dIkQ/viewform" style="margin-top:12px;">Contact form →</a>
      </div>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap">
    <div class="img-ph" style="min-height:320px;">MAP · 6620 S. King Drive, Chicago</div>
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
        <div class="img-ph" style="min-height:480px;font-size:13px;line-height:1.6;background-image:url('img/desmond-marshall.jpg');background-size:cover;background-position:center top;">
          PHOTO · Desmond "Dez" Marshall<br>
          <span style="font-size:11px;opacity:.5;">→ img/desmond-marshall.jpg</span>
        </div>
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

# ---------------------------------------------------------------------------
# Registry — (filename, title, meta, active key, body)
# ---------------------------------------------------------------------------
pages = [
    ("index.html",       "Home",                         "Project H.O.O.D. — a community-rooted nonprofit investing in Chicago's South Side through violence prevention, workforce development, health & wellness, youth programming, and re-entry services.", None,            home_body),
    ("about.html",       "About",                        "Project H.O.O.D. was founded by Pastor Corey B. Brooks in 2012. A decade of showing up in Woodlawn.",                                   "a_about",        about_body),
    ("exec-director.html", "Executive Director",         "Meet Desmond 'Dez' Marshall — Executive Director of Project H.O.O.D. Led the team from 3 to 83 staff, raised $44M+, serves 15,000+ annually.", "a_about",    exec_director_body),
    ("programs.html",    "Programs",                     "Five Pillars, one neighborhood. Violence prevention, workforce development, health & wellness, youth programming, and re-entry services.",         "a_programs",     programs_body),
    ("violence-prevention.html",   "Violence Prevention",    "Creating safer communities in Woodlawn — credible messengers, conflict mediation, and hospital-based intervention.",           "a_programs",     violence_prevention_body),
    ("workforce-development.html", "Workforce Development",  "Job training, placement, and career development on Chicago's South Side. 1,048 placements in 2025. $19/hr average wage.",          "a_programs",     workforce_development_body),
    ("health-wellness.html",       "Health & Wellness",      "Free medical care, counseling, and wellness programs for South Side residents — including the Southside Free Clinic (SSFC).",     "a_programs",     health_wellness_body),
    ("youth-programming.html",     "Youth Programming",      "After-school programs, esports, mentorship, and enrichment — 380 youth enrolled, 94% attendance, 42 summer internships in 2025.", "a_programs",     youth_programming_body),
    ("reentry-services.html",      "Re-Entry Services",      "Second chances, real support — job readiness, housing, counseling, and mentorship for individuals returning from incarceration.",  "a_programs",     reentry_services_body),
    ("impact.html",      "Impact",                       "2025 impact — 15,000+ served, 1,048 job placements, 2M+ lbs of food distributed, 70% LEO Center funded.",                             "a_impact",       impact_body),
    ("leo-center.html",  "LEO Center",                   "The Leadership and Economic Opportunity Center — 70% funded, a 90,000 sq ft community hub on S. King Drive.",                        "a_leo",          leo_body),
    ("campaigns.html",   "Walk With Us!",                "Walk With Us! — a nationwide movement to raise $25M for youth, families, and the LEO Center. Give, walk, or start a team on Tiltify.",  "a_campaigns",    campaigns_body),
    ("get-involved.html","Get Involved",                 "Three ways to move the work forward — give, volunteer, or partner.",                                                                   "a_gi",           gi_body),
    ("donate.html",      "Donate",                       "Donate securely through NetworkForGood. Your gift stays in Woodlawn.",                                                                 "a_gi",           donate_body),
    ("ways-to-give.html","Ways to Give",                 "Every way to give to Project H.O.O.D. — online, stock, DAF, check, corporate match, and planned giving. EIN 45-3964886.",              "a_gi",           ways_to_give_body),
    ("volunteer.html",   "Volunteer",                    "Volunteer with Project H.O.O.D. — sign up and we'll match you to an opportunity.",                                                      "a_gi",           volunteer_body),
    ("events.html",      "Events",                       "Upcoming events in Woodlawn — workshops, health fairs, youth programs, and community gatherings. RSVP powered by Eventbrite.",        "a_gi",           events_body),
    ("partner.html",     "Partner with us",              "Partner with Project H.O.O.D. — corporate, employer, foundation, church partnerships.",                                                 "a_gi",           partner_body),
    ("news.html",        "News",                         "Program milestones, LEO Center progress, stories from the block, press mentions.",                                                    "a_news",         news_body),
    ("contact.html",     "Contact",                      "Talk to us — press, partnership, participant, or general inquiry.",                                                                    None,             contact_body),
    ("privacy.html",     "Privacy Policy",               "Project H.O.O.D. privacy policy — what we collect, how we use it, and your rights.",                                               None,             privacy_body),
    ("404.html",         "Page not found",               "This page moved or never existed — here's where to go next.",                                                                          None,             notfound_body),
]

if __name__ == "__main__":
    for fname, title, meta, active, body in pages:
        p = write_page(fname, title, meta, active, body)
        print(f"  wrote {p.name}")
    print(f"\n{len(pages)} pages built at {SITE_DIR}")
