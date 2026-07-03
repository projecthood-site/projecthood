# Content Updates — Team Guide

A plain-English guide for updating the projecthood.org website after launch. **No coding background required.** You'll use GitHub's website to make changes — no software to install.

---

## Before you start

### One-time setup
1. Make sure you have a GitHub account (free — sign up at https://github.com)
2. Send Brian your GitHub username so he can add you as a collaborator on the `projecthood-site/projecthood` repo
3. Accept the collaborator invite email
4. You're in. You can now edit from any browser.

### Two rules
1. **Every change is visible to everyone immediately** — there's no "save draft and preview." When you save, it goes live within ~60 seconds. So read carefully before you save.
2. **If you mess up, you can't break it permanently.** Brian can roll back any change. Don't panic. But do tell him in Slack if you think something broke.

---

## Editing text on a page

**Use case:** you want to change a headline, fix a typo, update a paragraph.

1. Go to https://github.com/projecthood-site/projecthood
2. Click the file that matches the page you want to edit (e.g., `about.html` for the About page — see [SITEMAP.md](SITEMAP.md) for the full list)
3. Click the ✏️ pencil icon in the top-right of the file view
4. The file opens in an editor. Use Ctrl+F (Windows) or Cmd+F (Mac) to find the text you want to change.
5. Edit it directly. **Only change the text itself** — don't touch anything inside `< >` angle brackets unless you know what you're doing.
6. Scroll to the bottom. Under "Commit changes":
   - Title: write a short description (e.g., "Fix typo in About mission statement")
   - Click the green **Commit changes** button
7. Wait ~60 seconds, then refresh https://projecthood.org to see your change

### What NOT to touch
Anything that looks like this:
```
<h2 class="section-title">Our Mission</h2>
```
The words "Our Mission" are safe to change. Everything inside the `< >` is code — leave it alone.

---

## Adding a news post

**Use case:** a new press hit, blog update, or announcement.

1. Open `news.html` on GitHub (same steps as above — go to the repo, click the file, click the pencil)
2. Find the first `<article class="news-card">` block — it's the most recent post
3. **Copy the entire block** (from `<article ...>` down to `</article>`)
4. **Paste it directly above** the existing first post, so the new one appears at the top
5. In your pasted copy, replace:
   - The date
   - The headline
   - The summary paragraph
   - The image `src="..."` filename (see "Adding a photo" below)
   - The link (if any)
6. Commit with a title like "Add news: [headline]"

If that feels complicated, just write the post in a Google Doc, send it to Brian, and he'll add it in under 2 minutes.

---

## Updating events

**Events are managed on Eventbrite — you don't need to touch the website at all.**

### One-time setup (Brian does this once)
1. Create a free organization account at [eventbrite.com](https://www.eventbrite.com)
2. Set up the **Project H.O.O.D.** organization profile
3. Invite team members: go to **Manage organization → Team** and add people by email
4. Assign roles: Owner (Brian), Admin (comms lead), or Manager (program coordinators)

### Posting an event (any team member with access)
1. Go to [eventbrite.com](https://www.eventbrite.com) and sign in under Project H.O.O.D.
2. Click **Create event**
3. Upload your event flyer as the **Event image** — this becomes the card photo on the website
4. Fill in: title, date, time, location, description
5. Set ticket type to **Free** (or paid if applicable)
6. Click **Publish** — the event appears on projecthood.org automatically

That's it. No GitHub, no code, no Brian needed.

### Sharing an event
- Copy the event URL from Eventbrite and paste it anywhere (texts, Instagram, GroupMe, email)
- Or use the **Share** button on the events page — it copies the link to your clipboard
- Eventbrite automatically emails confirmation and reminders to everyone who RSVPs

### Downloading / sharing a flyer
- Upload the flyer PDF to `docs/events/` in the GitHub repo (same way you upload photos — see "Adding a photo" above)
- Brian can add a "Download flyer" link to the event card on the site

### Adding an event card to the website (if not using Eventbrite widget yet)
Until the Eventbrite collection widget is embedded, event cards are managed directly in `events.html`:
1. Open `events.html` on GitHub
2. Find the comment `═══ EVENT CARD — copy this entire block`
3. Copy one of the existing `<div class="card"...>` blocks
4. Paste it above the existing cards (so the newest appears first)
5. Update: date text, title, location, the `href` in the RSVP button (your Eventbrite event URL), and the `data-url` in the Share button (same URL)
6. For the flyer image: upload it to `img/events/` in the GitHub repo, then replace `<div class="img-ph"...>` with `<img src="img/events/YOUR-FILENAME.jpg" alt="[Event name] flyer" style="width:100%;display:block;">`
7. Commit with a title like "Add event: [Event name]"

**Who owns this:** Comms/events lead. Make sure you have Eventbrite access — ask Brian at brian@projecthood.org.

---

## Swapping or adding a photo

**Use case:** you have a new photo for the home page hero, or you want to replace an outdated team photo.

### Step 1 — Get the photo ready
- Photo should be at least 1600 pixels on the longest side
- JPG or PNG format
- Name it clearly: `home-hero-youth-group.jpg`, not `IMG_2839.jpg`
- If your photo is huge (like 15MB from a DSLR), use https://tinypng.com to shrink it — free, takes 5 seconds

### Step 2 — Upload to the repo
1. Go to https://github.com/projecthood-site/projecthood
2. Click into the **img** folder
3. Click **Add file** → **Upload files**
4. Drag your photo in
5. Scroll down, commit with title like "Add home hero photo"

### Step 3 — Put the photo on the page
1. Open the `.html` page where you want the photo (e.g., `index.html` for home)
2. Find the spot where you want it — look for existing `<img src="img/...">` lines or dashed-box placeholders marked `photo-placeholder`
3. Either replace the existing `src="img/OLDFILENAME.jpg"` with your new filename, **or** if it's a placeholder, ask Brian to wire it up (easier than doing this yourself)
4. Always include `alt="..."` with a short description of what's in the photo (accessibility + SEO)
5. Commit

**Honest recommendation:** for photo swaps, it's usually faster to just drop the photo in Slack and tell Brian where it goes. The upload-then-wire-it-up flow has a couple of gotchas.

---

## Updating the team page

Open `about.html`. Find the `<section id="team">` block. Each team member is a `<div class="team-card">` — follow the existing pattern for name, title, photo, and bio. Same copy/paste-the-block approach as news posts.

---

## Updating program info

Open `programs.html` for the overview, or `program.html` for the Violence Prevention detail page. Over time we'll add more program detail pages (workforce, mental health, etc.) — when that happens Brian will let you know which file is which.

---

## Posting a job opening

**Use case:** a new role opens up and you want it visible on the website.

1. Open `jobs.html` on GitHub (same steps as text editing above)
2. Find this comment block near the top of the `<main>` section:
   ```
   <!-- ═══ OPEN POSITION CARD — copy/paste this block to add a role ═══
   ```
3. Copy the entire template block (from the opening comment down to `═══ END OPEN POSITION CARD ═══`)
4. **Paste it directly above** the `<!-- NO OPENINGS STATE -->` block
5. Fill in: department, full-time/part-time, posted date, job title, description, key responsibilities, compensation, start date, and the Google Form application URL
6. Delete the `<!-- NO OPENINGS STATE -->` block (the "No open positions right now" box) — it should only show when there are no openings
7. Commit with a title like "Add job: [Job Title]"

**When a position is filled or closed:**
1. Open `jobs.html`, find the job card you want to remove
2. Delete the entire card (from `<div class="card card-accent"` through the closing `</div>`)
3. If no other openings remain, un-delete the "NO OPENINGS STATE" block (or paste it back in from this guide — it's also in a comment above the jobs section)
4. Commit with a title like "Remove job: [Job Title] — filled"

**Application form:** Each job listing links to a Google Form for applications. Create a new Google Form per role (or reuse a general one). The form should collect: name, email, phone, resume (file upload or link), and why they're applying.

---

## Updating impact numbers

Open `impact.html`. The numbers (15,000+ community members served, 2M+ lbs food, 1,048 job placements, 70% LEO Center funded) appear in two places:
- The `<section class="stats">` block on `impact.html` itself
- The home page `index.html` — the four colored stat tiles in the middle of the page

Update both files when numbers change. Do this after each program cycle ends or at the start of each calendar year. **Who owns this:** Development or evaluation lead.

---

## Updating program application status (open / closed)

When a program opens or closes enrollment, the relevant program detail page needs a status update. In `program.html` (and any future program detail pages):
- Find the Apply/CTA section near the top of the page
- Update the button text and link to reflect whether applications are open, closed, or waitlisted
- If Apricot has a direct intake URL, paste it as the button href

**Who owns this:** The program director for each program.

---

## Updating board / leadership

Board of directors and senior leadership live in `about.html`. Find the `<section id="team">` block — board members and staff follow the same card pattern. Add or remove cards as people join or depart.

**Tip:** Don't remove someone's card on the day they leave — coordinate with Brian so it comes off at a quiet moment, not during a fundraising push or press cycle.

---

## Updating donate / volunteer / event RSVPs

These are **not** edited on the website. They live in external tools:

| What you're updating | Where |
|---|---|
| Donation page look / donor amounts | NetworkForGood admin |
| Walk Across America campaign | Tiltify admin |
| Volunteer form questions | Google Forms |
| Events — post, edit, cancel | Eventbrite admin |
| Event RSVPs + confirmations | Eventbrite (automatic) |
| Program intake forms | Apricot |
| Re-Entry intake form | Google Forms |

The website just links to these — so changes you make in those tools show up automatically.

---

## "Help, I think I broke it"

1. Don't panic
2. Post in `#proj_website-update-2026` with: which page, what you were trying to do, what it looks like now
3. Brian can roll back your commit in about 30 seconds

The worst case is about 60 seconds of weirdness on the site. Low stakes.

---

## Cheat sheet — which file for what?

| I want to update... | File to edit |
|---|---|
| Home page hero, top features | `index.html` |
| Mission, history, team | `about.html` |
| Program overview | `programs.html` |
| Violence Prevention details | `program.html` |
| Impact numbers, stories | `impact.html` |
| LEO Center campaign | `leo-center.html` |
| Walk Across America | `campaigns.html` |
| Donate / Volunteer / Partner hub | `get-involved.html` |
| Events (card text, RSVP links) | `events.html` — or just use Eventbrite |
| News / press | `news.html` |
| Job openings | `jobs.html` |
| Contact info, office address | `contact.html` |
| Impact numbers | `impact.html` + `index.html` (update both) |
| Board / leadership | `about.html` — team section |
| Site-wide nav, footer, colors, fonts | Ask Brian — these are in `_build.py` and `css/styles.css` |

---

## Questions?

`#proj_website-update-2026` in Slack, or DM Brian.
