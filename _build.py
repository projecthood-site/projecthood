#!/usr/bin/env python3
"""
Project H.O.O.D. site prototype generator.

Renders a clickable local HTML prototype the team can review before we
commit to the GitHub Pages + Decap CMS + Google Calendar implementation.

To rebuild after tweaks, run: python3 _build.py
Output: all .html pages at the site/ root.
"""
from pathlib import Path
import re

SITE_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# Shared template pieces
# ---------------------------------------------------------------------------

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
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
</head>
<body>

<a class="skip-link" href="#main">Skip to main content</a>

<div class="preview-banner">
  <strong>PREVIEW BUILD</strong> &nbsp;·&nbsp; clickable prototype · brand + IA · content placeholders pending review
</div>

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
        <p style="font-size:13.5px;opacity:.9;">A community-rooted nonprofit investing in Woodlawn &amp; Chicago's South Side — through workforce development, violence prevention, education, mental health, and economic growth.</p>
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
        © 2026 Project H.O.O.D. · 6620 S. King Drive, Chicago IL 60637 · EIN 46-1449998<br>
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
<!-- HERO -->
<section class="hero">
  <div class="wrap">
    <div class="hero-split">
      <div>
        <div class="eyebrow" style="color:var(--yellow);">Woodlawn, Chicago</div>
        <h1>Five programs. <span class="hl-yellow">One neighborhood.</span><br>A decade of showing up.</h1>
        <p class="lead">Project H.O.O.D. invests directly on the block — in workforce training, violence prevention, mental health, education, and economic growth. No national overhead, no middle layer.</p>
        <div style="margin-top:28px;display:flex;gap:12px;flex-wrap:wrap;">
          <a class="btn btn-primary" href="impact.html">See our impact</a>
          <a class="btn btn-outline-light" href="https://projecthood.networkforgood.com/">Donate</a>
        </div>
      </div>
      <div style="position:relative;">
        <div class="img-ph dark" style="min-height:360px;">HERO PHOTO · neighborhood / staff / programs</div>
        <div class="stamp-corner stamp"><img src="img/logo-knockout-offwhite.png" alt=""></div>
      </div>
    </div>
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
    <h2>Five programs, one strategy.</h2>
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
        <span class="tag tag-blue">Education</span>
        <h3 style="margin-top:10px;">Esports &amp; youth enrichment.</h3>
        <p style="font-family:var(--font-serif);">After-school programs, tournaments, and mentorship — meeting kids where they already are.</p>
        <a href="programs.html" style="margin-top:auto;">Read more →</a>
      </div>
      <div class="prog-card pg-purple">
        <span class="tag tag-purple">Mental Health</span>
        <h3 style="margin-top:10px;">Trauma-informed care.</h3>
        <p style="font-family:var(--font-serif);">Free counseling, group sessions, and crisis response — run by licensed clinicians and peer specialists.</p>
        <a href="programs.html" style="margin-top:auto;">Read more →</a>
      </div>
      <div class="prog-card pg-yellow">
        <span class="tag tag-yellow">Economic Growth</span>
        <h3 style="margin-top:10px;">Small-business support.</h3>
        <p style="font-family:var(--font-serif);">Technical assistance, micro-grants, and mentorship for Woodlawn entrepreneurs.</p>
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
      <div class="img-ph dark" style="min-height:300px;">LEO CENTER RENDERING</div>
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

<!-- WALK ACROSS AMERICA -->
<section class="section bg-blue">
  <div class="wrap">
    <div class="grid-2" style="align-items:center;">
      <div>
        <div class="eyebrow" style="color:var(--yellow);">Nationwide Campaign</div>
        <h2>Walk With Us!</h2>
        <p style="font-size:var(--fs-lead);opacity:.95;">What started as Pastor Brooks' 900-mile walk from Chicago to New York has grown into a nationwide movement. Give, organize a walk, or start a team — and help raise $25M for youth, families, and the LEO Center.</p>
        <div style="margin-top:24px;display:flex;gap:12px;flex-wrap:wrap;">
          <a class="btn btn-yellow" href="https://tiltify.com/project-hood/walk-across-america-2025">Give to the movement</a>
          <a class="btn btn-outline-light" href="campaigns.html">Learn more</a>
        </div>
      </div>
      <div class="img-ph dark" style="min-height:260px;">WAA photo · on the route</div>
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
      <p>Project H.O.O.D. (Helping Others Obtain Destiny) exists to create sustainable change in Woodlawn and the broader South Side of Chicago. We operate five interlocking programs — violence prevention, workforce development, education, mental health, and economic growth — because no one of these alone is enough.</p>
      <p>We believe that the people closest to the problems are closest to the solutions. Everything we do is built with the neighborhood, not for it.</p>
    </div>
    <div class="img-ph" style="min-height:340px;">MISSION PHOTO · community or founder</div>
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
    <div class="img-ph dark" style="min-height:320px;">FOUNDER PORTRAIT · Pastor Brooks</div>
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

<section class="section">
  <div class="wrap">
    <div class="eyebrow">Team</div>
    <h2>The people behind the programs.</h2>
    <p style="max-width:var(--w-read);">A staff of outreach workers, clinicians, educators, trainers, and operators — most from the neighborhood, all in it for the long haul.</p>
    <div class="grid-4" style="margin-top:var(--sp-3);">
      <div class="card"><div class="img-ph" style="min-height:180px;margin-bottom:12px;">Photo</div><h4>[Staff name]</h4><p style="font-size:13px;color:var(--muted);margin:0;">Role · Department</p></div>
      <div class="card"><div class="img-ph" style="min-height:180px;margin-bottom:12px;">Photo</div><h4>[Staff name]</h4><p style="font-size:13px;color:var(--muted);margin:0;">Role · Department</p></div>
      <div class="card"><div class="img-ph" style="min-height:180px;margin-bottom:12px;">Photo</div><h4>[Staff name]</h4><p style="font-size:13px;color:var(--muted);margin:0;">Role · Department</p></div>
      <div class="card"><div class="img-ph" style="min-height:180px;margin-bottom:12px;">Photo</div><h4>[Staff name]</h4><p style="font-size:13px;color:var(--muted);margin:0;">Role · Department</p></div>
    </div>
    <p style="margin-top:var(--sp-3);font-size:13px;color:var(--muted);font-style:italic;">— Full team + board + advisors added in next build round —</p>
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
    <h1>Five programs. One <span class="hl-yellow">strategy.</span></h1>
    <p class="lead">Violence prevention, workforce development, education, mental health, and economic growth — interlocking, not siloed. You can't fix one without touching the others.</p>
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
        <a href="program.html" class="btn btn-outline" style="align-self:flex-start;margin-top:auto;">About Violence Prevention</a>
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
        <a href="program.html" class="btn btn-outline" style="align-self:flex-start;margin-top:auto;">About Workforce</a>
      </div>
      <div class="prog-card pg-blue">
        <span class="tag tag-blue">03 · Education</span>
        <h3 style="margin-top:12px;">Esports &amp; youth enrichment.</h3>
        <p>After-school programs, academic support, and youth mentorship — built around what kids actually want to do.</p>
        <ul style="font-size:14px;color:var(--muted);margin:var(--sp-2) 0;">
          <li>Esports tournaments + leagues</li>
          <li>Homework + tutoring</li>
          <li>College/career readiness</li>
        </ul>
        <a href="program.html" class="btn btn-outline" style="align-self:flex-start;margin-top:auto;">About Education</a>
      </div>
      <div class="prog-card pg-purple">
        <span class="tag tag-purple">04 · Mental Health</span>
        <h3 style="margin-top:12px;">Trauma-informed care.</h3>
        <p>Free counseling, group work, and crisis response — delivered by licensed clinicians and peer specialists.</p>
        <ul style="font-size:14px;color:var(--muted);margin:var(--sp-2) 0;">
          <li>Individual therapy</li>
          <li>Group support circles</li>
          <li>Crisis + post-incident response</li>
        </ul>
        <a href="program.html" class="btn btn-outline" style="align-self:flex-start;margin-top:auto;">About Mental Health</a>
      </div>
      <div class="prog-card pg-yellow">
        <span class="tag tag-yellow">05 · Economic Growth</span>
        <h3 style="margin-top:12px;">Small-business support.</h3>
        <p>Technical assistance, micro-grants, and mentorship for Woodlawn entrepreneurs — so dollars that come into the neighborhood stay in the neighborhood.</p>
        <ul style="font-size:14px;color:var(--muted);margin:var(--sp-2) 0;">
          <li>Business plan coaching</li>
          <li>Grant + capital access</li>
          <li>Local-vendor procurement</li>
        </ul>
        <a href="program.html" class="btn btn-outline" style="align-self:flex-start;margin-top:auto;">About Economic Growth</a>
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

# -------- SINGLE PROGRAM PAGE (template) --------
program_body = f"""
<section class="hero bg-green">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--yellow);">Programs · Violence Prevention</div>
    <h1>Outreach <span class="hl-yellow">on the block.</span></h1>
    <p class="lead">Credible messengers and conflict mediators embedded in the neighborhood, defusing violence before it escalates and mentoring young people out of the life.</p>
  </div>
</section>

<section class="section">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">How it works</div>
      <h2>Tangible activities.</h2>
      <p>Outreach workers are out on the block nightly — mediating beefs, riding to the hospital with shooting victims, pulling young men aside before a retaliation escalates. Every worker carries a caseload of participants they mentor long-term.</p>
      <ul>
        <li>24/7 community response team covering Woodlawn + Washington Park</li>
        <li>Hospital-based intervention partnering with University of Chicago Medicine</li>
        <li>Embedded mediators in local schools</li>
        <li>Weekly peace circles for young men 16–24</li>
      </ul>
    </div>
    <div class="img-ph" style="min-height:380px;">PROGRAM PHOTO · staff or outreach scene</div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">Who runs it</div>
      <h2>Led by people from the block.</h2>
      <p>Our outreach team is led by [Director name], a former participant who rose through the program. The team is 12 strong — all credible messengers with lived experience and specialized training.</p>
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
    <div class="eyebrow" style="color:var(--yellow);">Proof</div>
    <h2 style="color:var(--white);">What the work is producing.</h2>
    <div class="stat-grid" style="margin-top:var(--sp-3);">
      <div class="stat"><div class="v">140+</div><div class="l">incidents mediated in 2025</div></div>
      <div class="stat"><div class="v">22</div><div class="l">hospital-bedside interventions</div></div>
      <div class="stat"><div class="v">85</div><div class="l">young men in peace circles</div></div>
      <div class="stat"><div class="v">31%</div><div class="l">reduction in 60637 gun homicides (2024→2025)</div></div>
    </div>
    <div class="testimonial" style="margin-top:var(--sp-4);background:var(--black);">
      <blockquote>"They showed up when nobody else did. When my brother got shot, outreach was at the hospital before my mother got there."</blockquote>
      <cite>— Program participant, 23</cite>
    </div>
  </div>
</section>

<section class="cta-strip">
  <div class="wrap">
    <h2>Support the outreach team.</h2>
    <div class="btn-group">
      <a class="btn btn-yellow" href="https://projecthood.networkforgood.com/">Fund this program</a>
      <a class="btn btn-outline-light" href="get-involved.html">Volunteer</a>
      <a class="btn btn-outline-light" href="https://projecthood.socialsolutionsportal.com/apricot-intake/0eb461e5-38a9-4ad1-9a4e-02bb3ee1414d" target="_blank" rel="noopener">Apply as participant</a>
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
        <span class="tag tag-blue">Education</span>
        <h3>380 youth · 94% attendance rate</h3>
        <p>Esports league, tutoring, and mentorship. 94% weekly attendance. 42 youth placed in summer internships.</p>
      </div>
      <div class="prog-card pg-purple">
        <span class="tag tag-purple">Mental Health</span>
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
      <div class="img-ph dark" style="min-height:340px;">LEO CENTER RENDERING / SITE PHOTO</div>
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

<section class="section">
  <div class="wrap grid-2">
    <div>
      <div class="eyebrow">What it is</div>
      <h2>One building, five programs, one neighborhood.</h2>
      <p>The LEO Center brings every Project H.O.O.D. program under one roof: workforce training classrooms, mental health counseling suites, esports arena, economic growth incubator, outreach team offices, community kitchen, and a 400-seat multipurpose hall.</p>
      <p>It's being built on land owned by Project H.O.O.D., directly on S. King Drive — a deliberate statement that serious investment belongs on the South Side.</p>
    </div>
    <div class="img-ph" style="min-height:360px;">FLOOR PLAN OR RENDERING</div>
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
<section class="hero bg-blue">
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
      <div class="img-ph dark" style="min-height:340px;">WAA PHOTO · on the route</div>
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
    <div class="img-ph" style="min-height:340px;">ROUTE MAP · Chicago → NYC</div>
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
      <p style="font-size:12px;opacity:.8;margin-top:12px;">Tax-deductible · EIN 46-1449998 · takes under 2 minutes</p>
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
      <div class="card"><h4>Stock &amp; DAF</h4><p style="font-size:13.5px;">Donor-advised funds, appreciated securities. Contact development@projecthood.org.</p></div>
      <div class="card"><h4>Planned giving</h4><p style="font-size:13.5px;">Bequests, beneficiary designations. Let's schedule a call.</p></div>
      <div class="card"><h4>Check by mail</h4><p style="font-size:13.5px;">Project H.O.O.D.<br>6620 S. King Drive<br>Chicago IL 60637</p></div>
      <div class="card"><h4>Corporate match</h4><p style="font-size:13.5px;">Ask your HR team — or submit via our Google Form lookup.</p></div>
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
events_body = f"""
<section class="hero bg-yellow" style="color:var(--black);">
  <div class="wrap">
    <div class="eyebrow">Events</div>
    <h1>On the <span style="background:var(--red);color:var(--white);padding:2px 10px;transform:rotate(-1.5deg);display:inline-block;">calendar.</span></h1>
    <p class="lead" style="opacity:1;color:var(--ink);">Community dinners, fundraisers, workshops, and LEO Center milestones. Live from the Project H.O.O.D. Google Calendar — when staff adds or updates an event, it appears here automatically.</p>
  </div>
</section>

<section class="section-sm" style="border-bottom:1px solid var(--line);background:var(--white);">
  <div class="wrap" style="display:flex;gap:24px;font-family:var(--font-display);text-transform:uppercase;font-size:12.5px;letter-spacing:.14em;align-items:center;flex-wrap:wrap;">
    <span style="color:var(--red);border-bottom:2px solid var(--red);padding-bottom:4px;">Upcoming</span>
    <span style="color:var(--muted);">Recurring</span>
    <span style="color:var(--muted);">Past events</span>
    <div style="margin-left:auto;display:flex;gap:16px;flex-wrap:wrap;align-items:center;">
      <a href="https://calendar.google.com/calendar/ical/c_aaab49ab274191a67fd34d3ec23430823e39f8a684eb5358c53ccfc765269ec6%40group.calendar.google.com/public/basic.ics" style="font-family:var(--font-serif);text-transform:none;letter-spacing:0;font-size:12.5px;color:var(--muted);font-style:italic;">🗓 Subscribe (.ics / Apple)</a>
      <a href="https://calendar.google.com/calendar/r?cid=c_aaab49ab274191a67fd34d3ec23430823e39f8a684eb5358c53ccfc765269ec6@group.calendar.google.com" style="font-family:var(--font-serif);text-transform:none;letter-spacing:0;font-size:12.5px;color:var(--muted);font-style:italic;">+ Add to Google Calendar</a>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <!-- Featured -->
    <div class="bg-black" style="padding:var(--sp-4);display:grid;grid-template-columns:.4fr .6fr;gap:24px;align-items:center;color:var(--white);">
      <div class="img-ph dark" style="min-height:240px;">FEATURED EVENT PHOTO</div>
      <div>
        <div class="eyebrow" style="color:var(--yellow);">Featured · Aug 22, 2026</div>
        <h2 style="color:var(--white);">Back to School Giveaway</h2>
        <p style="opacity:.88;">Free backpacks, school supplies, haircuts, and family meals for 500+ Woodlawn families.</p>
        <div style="margin-top:14px;display:flex;gap:10px;flex-wrap:wrap;">
          <a class="btn btn-yellow" href="https://docs.google.com/forms/d/e/1FAIpQLSfulIcBaCRzjDaNXuMuV-fgo_LxqOoXNQG8FU7ibIOuI_6-FA/viewform">RSVP</a>
          <a class="btn btn-outline-light" href="volunteer.html">Volunteer for this</a>
        </div>
      </div>
    </div>

    <!-- Live Google Calendar embed -->
    <div style="margin-top:var(--sp-4);border:1px solid var(--line);overflow:hidden;">
      <iframe
        src="https://calendar.google.com/calendar/embed?src=c_aaab49ab274191a67fd34d3ec23430823e39f8a684eb5358c53ccfc765269ec6%40group.calendar.google.com&ctz=America%2FChicago&showTitle=0&showNav=1&showPrint=0&showTabs=0&showCalendars=0&mode=AGENDA"
        style="border:0;width:100%;min-height:520px;display:block;"
        frameborder="0"
        scrolling="no"
        title="Project H.O.O.D. upcoming events">
      </iframe>
    </div>
  </div>
</section>

<section class="section bg-offwhite">
  <div class="wrap">
    <div class="eyebrow" style="color:var(--muted);">Staff: how to post an event</div>
    <div class="grid-4" style="margin-top:12px;">
      <div class="card card-accent" style="border-top-color:var(--green);"><h4>1 · Create</h4><p style="font-size:13px;">Add to the "Project H.O.O.D. Events" Google Calendar.</p></div>
      <div class="card card-accent" style="border-top-color:var(--blue);"><h4>2 · Tag</h4><p style="font-size:13px;">Use <code>[FEATURED]</code> in the title to pin to hero.</p></div>
      <div class="card card-accent" style="border-top-color:var(--red);"><h4>3 · Link</h4><p style="font-size:13px;">Paste a Google Form RSVP URL in the description.</p></div>
      <div class="card card-accent" style="border-top-color:var(--yellow);"><h4>4 · Done</h4><p style="font-size:13px;">Live on site within ~60 seconds.</p></div>
    </div>
    <p style="font-size:12px;color:var(--muted);margin-top:12px;font-style:italic;">This helper block is visible in the preview for team review only. It comes off before launch.</p>
  </div>
</section>
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
        <div class="eyebrow">Dec 18, 2025 · Mental Health</div>
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
    <p>Project H.O.O.D. (Helping Others Obtain Destiny) is a 501(c)(3) nonprofit organization located at 6620 S. King Drive, Chicago, IL 60637. EIN 46-1449998. You can reach us at <a href="mailto:info@projecthood.org">info@projecthood.org</a>.</p>

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

# -------- 404 --------
notfound_body = f"""
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
    ("index.html",       "Home",                         "Project H.O.O.D. — a community-rooted nonprofit investing in Chicago's South Side through violence prevention, workforce development, mental health, education, and economic growth.", None,            home_body),
    ("about.html",       "About",                        "Project H.O.O.D. was founded by Pastor Corey B. Brooks in 2012. A decade of showing up in Woodlawn.",                                   "a_about",        about_body),
    ("programs.html",    "Programs",                     "Five programs, one neighborhood. Violence prevention, workforce development, education, mental health, and economic growth.",         "a_programs",     programs_body),
    ("program.html",     "Violence Prevention",          "Violence Prevention at Project H.O.O.D. — credible messengers and conflict mediators embedded in Woodlawn.",                          "a_programs",     program_body),
    ("impact.html",      "Impact",                       "2025 impact — 15,000+ served, 1,048 job placements, 2M+ lbs of food distributed, 70% LEO Center funded.",                             "a_impact",       impact_body),
    ("leo-center.html",  "LEO Center",                   "The Leadership and Economic Opportunity Center — 70% funded, a 90,000 sq ft community hub on S. King Drive.",                        "a_leo",          leo_body),
    ("campaigns.html",   "Walk With Us!",                "Walk With Us! — a nationwide movement to raise $25M for youth, families, and the LEO Center. Give, walk, or start a team on Tiltify.",  "a_campaigns",    campaigns_body),
    ("get-involved.html","Get Involved",                 "Three ways to move the work forward — give, volunteer, or partner.",                                                                   "a_gi",           gi_body),
    ("donate.html",      "Donate",                       "Donate securely through NetworkForGood. Your gift stays in Woodlawn.",                                                                 "a_gi",           donate_body),
    ("volunteer.html",   "Volunteer",                    "Volunteer with Project H.O.O.D. — sign up and we'll match you to an opportunity.",                                                      "a_gi",           volunteer_body),
    ("events.html",      "Events",                       "Community dinners, fundraisers, workshops, LEO Center milestones — live-synced from our Google Calendar.",                            "a_gi",           events_body),
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
