# Updating the Project H.O.O.D. website with Claude

This guide is for staff who will keep projecthood.org up to date using **Claude**
(in Cowork mode on the Claude desktop app) as the person actually making the
edits. You describe the change in plain English; Claude edits the files, shows
you the result, and — with your OK — pushes it to GitHub.

> You do **not** need to know HTML. You do need to do a one-time setup, and you
> need to understand the review-and-publish steps so nothing goes live by
> accident.

---

## How the collaboration model works (read this first)

Claude Cowork runs **locally on one computer** and conversations **cannot be
shared** with other people or synced between machines. So there is no single
"team thread" everyone joins. Instead:

- The **GitHub repo `projecthood-site/projecthood` is the shared source of truth.**
- **Each maintainer runs their own Claude** on their own computer, pointed at
  their own copy of the repo.
- Everyone's changes meet in GitHub. As long as each person edits on the
  `staging` branch and pushes there, the work stays coordinated.

So adding people "to this thread" isn't the setup — **adding people to the
GitHub repo is.** Steps for that are below.

---

## One-time setup (per maintainer)

Do this once on each person's computer.

### 1. Get access to the repo
The repo owner adds each maintainer as a **collaborator**:
GitHub → `projecthood-site/projecthood` → **Settings → Collaborators → Add people**.
Each maintainer accepts the email invite and creates a free GitHub account if
they don't have one.

### 2. Get the files onto the computer
Pick one:
- **Simplest (recommended for non-developers):** keep the repo folder in the
  shared **Dropbox** location everyone already uses, and let Claude read/write
  there. (This is how the current setup works — the site lives under
  `…/PH Website Update/site/projecthood`.)
- **Standard developer way:** install GitHub Desktop (desktop.github.com), sign
  in, and **Clone** `projecthood-site/projecthood` to the computer.

### 3. Install Claude desktop + open Cowork
Download the Claude desktop app, sign in, and open **Cowork mode**.
Help article: https://support.claude.com/en/articles/13345190-get-started-with-claude-cowork

### 4. Point Claude at the site folder
In Cowork, **connect the folder** that contains the site (the `projecthood`
folder, or its parent). Claude can now read and edit the site files.

### 5. Connect GitHub (so Claude can push for you)
In the Claude app, open **`/mcp`** and connect the **GitHub** connector, then
authorize it in the browser. This is what lets Claude commit and push without
you touching the terminal.

> If the GitHub connector won't authorize, you can still publish manually with
> three Terminal commands — see "If the GitHub connector isn't working" at the
> bottom.

### 6. Confirm it's working
Start a Cowork conversation and say: *"Open CLAUDE.md and tell me how this site
is structured."* If Claude can read it and summarize, you're set.

---

## Making a change

Just describe what you want in plain English. Helpful prompts:

- *"On the Health & Wellness page, change the clinic hours to Tuesdays 9–1."*
- *"Add this YouTube video to the Youth Programming page: <paste the embed code>."*
- *"Update the 2025 impact numbers on the Workforce page: 1,200 placements, $21/hr average."*
- *"Swap the donate button link to this new NetworkForGood URL: <paste>."*
- *"The construction cohort Google Form is ready — here's the link, wire it into the application button."*

Claude will make the edit and show you what changed. You can ask it to tweak
wording, undo, or try again before anything is saved.

### A few things to tell Claude (or it already knows from CLAUDE.md)
- Edits happen on the **`staging`** branch.
- It should **show you the change and ask before pushing** to GitHub.
- It uses the **brand colors and fonts** automatically — don't paste in custom
  hex colors.
- Nav/footer changes go through `_build.py`; page content is edited directly.

---

## Review → publish (how things actually go live)

There are two gates on purpose, so nothing ships by accident:

1. **Save to `staging`** — Claude commits and pushes your change to GitHub's
   `staging` branch. This does **not** make it live. Preview it at
   https://projecthood-site.github.io/projecthood/ once `staging` is merged for preview,
   or review the diff Claude shows you.
2. **Publish** — to actually update the live site, `staging` is merged into the
   **`main`** branch. GitHub Pages rebuilds from `main`. Ask Claude to *"open a
   pull request from staging to main"* and have the repo owner approve the merge.

> Note: until the DNS cutover described in `LAUNCH_RUNBOOK.md`, the public
> projecthood.org is still served by Squarespace. The GitHub build goes live at
> the address above first.

---

## Where to find more

- **CLAUDE.md** — the rules Claude follows (branch model, brand tokens, build).
- **SITEMAP.md** — what each page is for and who owns its content.
- **CONTENT_UPDATES.md** — plain-English notes on updating content.
- **LAUNCH_RUNBOOK.md** — the go-live / DNS cutover procedure.

---

## If the GitHub connector isn't working

You can publish without it. Open **Terminal** and run (adjust the path if your
copy lives elsewhere):

```
cd "~/Documents/Claude/Projects/PH Website Update/site/projecthood"
git add -A
git commit -m "Describe your change"
git push origin staging
```

If git complains about a `.git/...lock` file, delete the lock and retry:

```
rm -f .git/HEAD.lock .git/index.lock .git/objects/maintenance.lock
git push origin staging
```
