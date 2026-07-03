#!/usr/bin/env python3
"""
sync_eventbrite.py

Pulls live/upcoming events from the Project H.O.O.D. Eventbrite organization
and regenerates the auto-generated event cards block in events.html.

Requires the EVENTBRITE_TOKEN environment variable (an Eventbrite Private
Token — see Eventbrite > Account Settings > Developer Links > API Keys).
Never hardcode the token here; it is injected via a GitHub Actions secret.

Usage:
    EVENTBRITE_TOKEN=xxxx python3 scripts/sync_eventbrite.py

Exit codes:
    0 — success (file updated or already up to date)
    1 — missing token / fatal config error
    2 — Eventbrite API request failed
"""
import html
import os
import re
import sys
import urllib.error
import urllib.request
import json
from datetime import datetime

ORG_ID = "41178041593"  # Project H.O.O.D. — eventbrite.com/o/project-hood-41178041593
API_BASE = "https://www.eventbriteapi.com/v3"
EVENTS_HTML_PATH = os.path.join(os.path.dirname(__file__), "..", "events.html")

START_MARKER = "<!-- EVENTBRITE:CARDS:START -->"
END_MARKER = "<!-- EVENTBRITE:CARDS:END -->"

FALLBACK_CARD_HTML = """
      <div class="card" style="padding:32px;text-align:center;grid-column:1/-1;">
        <p style="font-family:var(--font-serif);color:var(--muted);font-size:15px;margin:0;">
          No upcoming events posted right now — check
          <a href="https://www.eventbrite.com/o/project-hood-41178041593" target="_blank" rel="noopener">our Eventbrite page</a>
          or check back soon.
        </p>
      </div>
"""


def fetch_events(token: str) -> list:
    """Fetch all live, upcoming events for the PH Eventbrite org (handles pagination)."""
    events = []
    page = 1
    while True:
        url = (
            f"{API_BASE}/organizations/{ORG_ID}/events/"
            f"?status=live&order_by=start_asc&expand=venue&page={page}"
        )
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            print(f"Eventbrite API error {e.code}: {body}", file=sys.stderr)
            raise
        events.extend(data.get("events", []))
        pagination = data.get("pagination", {})
        if page >= pagination.get("page_count", 1):
            break
        page += 1
    # Only future events (Eventbrite's "live" status can include events that
    # already started but haven't been marked ended/completed).
    now = datetime.utcnow()
    future = []
    for ev in events:
        start_utc = ev.get("start", {}).get("utc")
        if not start_utc:
            continue
        try:
            start_dt = datetime.strptime(start_utc, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
        if start_dt >= now:
            future.append(ev)
    return future


def format_date_range(start_local: str, end_local: str) -> str:
    """'2026-08-29T10:00:00' + end -> 'Sat, Aug 29 · 10 AM – 3 PM'"""
    def parse(dt_str):
        return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")

    start_dt = parse(start_local)
    day = f"{start_dt.strftime('%a')}, {start_dt.strftime('%b')} {start_dt.day}"

    def fmt_time(dt):
        s = dt.strftime("%I:%M %p").lstrip("0")
        return s.replace(":00 ", " ")

    start_time = fmt_time(start_dt)
    if end_local:
        end_dt = parse(end_local)
        end_time = fmt_time(end_dt)
        return f"{day} · {start_time} – {end_time}"
    return f"{day} · {start_time}"


def venue_line(ev: dict) -> str:
    if ev.get("online_event"):
        return "Online event"
    venue = ev.get("venue")
    if not venue:
        return "Location TBA"
    name = venue.get("name") or ""
    addr = (venue.get("address") or {}).get("localized_address_display") or ""
    if name and addr:
        return f"{html.escape(name)} · {html.escape(addr)}"
    return html.escape(name or addr or "Location TBA")


def card_html(ev: dict) -> str:
    name = html.escape(ev.get("name", {}).get("text", "Untitled Event"))
    url = html.escape(ev.get("url", "https://www.eventbrite.com/o/project-hood-41178041593"))
    logo = ev.get("logo")
    img_url = html.escape(logo["url"]) if logo and logo.get("url") else "img/social-icon.jpg"
    start_local = ev.get("start", {}).get("local", "")
    end_local = ev.get("end", {}).get("local", "")
    date_str = format_date_range(start_local, end_local) if start_local else "Date TBA"
    venue = venue_line(ev)

    return f"""
      <div class="card" style="padding:0;overflow:hidden;">
        <img src="{img_url}" alt="{name} flyer"
             style="width:100%;height:240px;object-fit:cover;display:block;">
        <div style="padding:14px 18px 16px;">
          <div style="font-size:11px;font-weight:700;color:var(--red);text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px;">{date_str}</div>
          <div style="font-size:17px;font-weight:800;color:var(--dark);font-family:var(--font-display);line-height:1.2;margin-bottom:3px;">{name}</div>
          <div style="font-size:13px;color:var(--muted);margin-bottom:12px;">{venue}</div>
          <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
            <a class="btn btn-primary" href="{url}" target="_blank" rel="noopener" style="font-size:13px;padding:8px 16px;">RSVP &rarr;</a>
            <button class="ph-share-btn" data-title="{name}" data-url="{url}" style="background:transparent;border:1px solid var(--line);border-radius:6px;padding:7px 14px;font-size:13px;cursor:pointer;font-family:var(--font-body);color:var(--ink);">Share</button>
          </div>
        </div>
      </div>"""


def build_cards_block(events: list) -> str:
    if not events:
        inner = FALLBACK_CARD_HTML
    else:
        inner = "".join(card_html(ev) for ev in events)
    return (
        f'{START_MARKER}\n'
        f'    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:20px;">\n'
        f'{inner}\n'
        f'    </div>\n'
        f'    {END_MARKER}'
    )


def update_events_html(cards_block: str) -> bool:
    """Returns True if the file changed."""
    with open(EVENTS_HTML_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL
    )
    if not pattern.search(content):
        print(
            f"ERROR: markers {START_MARKER!r} / {END_MARKER!r} not found in "
            f"{EVENTS_HTML_PATH}. Did the page template change?",
            file=sys.stderr,
        )
        sys.exit(1)

    new_content = pattern.sub(cards_block, content, count=1)
    if new_content == content:
        return False

    with open(EVENTS_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    return True


def main():
    token = os.environ.get("EVENTBRITE_TOKEN")
    if not token:
        print("ERROR: EVENTBRITE_TOKEN environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    try:
        events = fetch_events(token)
    except Exception:
        sys.exit(2)

    print(f"Fetched {len(events)} upcoming live event(s) from Eventbrite.")
    cards_block = build_cards_block(events)
    changed = update_events_html(cards_block)
    print("events.html updated." if changed else "events.html already up to date.")


if __name__ == "__main__":
    main()
