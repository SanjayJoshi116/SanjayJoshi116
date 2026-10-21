# README improvement ideas

Brainstorm from 2026-10-18. Nothing here is decided or started.

## The gap

Visitors see 8 public repos (2 movie apps, 5 old ML notebooks) and 12 stars. The real work (SwingTrade AI, Contribution Finder, Expense Tracker, FitTrack, Agrileaf apps) is private. Most ideas below try to close that gap without writing a private repo name anywhere.

Open question that reorders everything: is the README mainly for recruiters (favour A3, D2) or for developer and trading peers (favour B1, B2)?

## A. Proof that private work is alive

- **A1. Pulse strip.** The token already reads allowlisted repos. Render a weekly commit sparkline per private project, labelled by title only (e.g. `SwingTrade AI ▁▃▅█▆▇▅ 42 commits / 30d v0.41`). Risk: a quiet week shows; a 90-day window softens that.
- **A2. Auto version labels.** Read the latest tag or release from each private repo instead of hand-typing `version:` in `profile.yml`.
- **A3. Screenshots of private apps.** One UI shot per card. Highest value for recruiters. Cost: manual capture and image size. Use demo data, especially for the finance app.

## B. Show thinking, not just output

- **B1. Mermaid architecture diagram** for SwingTrade AI (NSE EOD → 750 stocks → 21 detectors → regime filter → sizing → alerts, plus the 22-strategy backtester). GitHub renders Mermaid natively, with no external host, and it adapts to light and dark themes.
- **B2. Daily market regime line.** Show today's Nifty regime (e.g. "risk-on") from your own detector logic, run by the existing daily cron. High novelty. Risks: NSE data in CI is flaky or blocked; show only the label so no strategy leaks.

## C. The person behind the code

- **C1. Photo of the week.** Rotate your own photos from `assets/photos/`. Strip EXIF and GPS data, and compress the files.
- **C2. Latest YouTube video.** @SJThinks has a public RSS feed with no API key. Render the title as an SVG card, so no external thumbnail is loaded.
- **C3. Work account.** Plot SanjayJoshi116 and AgrileafSanjay as two lines in the hero chart. This only counts if private contributions are visible on the work account.

## D. Subtract

- **D1. Demote the old ML notebooks.** Collapse the 5 regression and clustering repos into one row ("Early ML coursework (5 repos)"), or archive them on GitHub.
- **D2. Persona doors.** Two `<details>` blocks near the top: "Hiring? 30-second version" and "Developer? How things are built".

## E. Open source

- **E1. Merged PRs to other repos.** Auto-list them with the search API (`author:SanjayJoshi116 is:merged -user:SanjayJoshi116`). Hide the section until at least one exists.
- **E2. Dogfood Contribution Finder.** Once it is public, show "issues my tool picked for me this week".

## Challenge to the current design

The spec keeps dark panels on both GitHub themes. Alternative: `<picture>` with `prefers-color-scheme` sources gives light-theme variants that look native rather than a dark box on white. Cost: twice the assets and twice the contrast checks.

## Ranking (value against effort)

| Idea | Value | Effort | Risk |
|---|---|---|---|
| A1 pulse strip | high | low (token exists) | quiet weeks show |
| D1 demote notebooks | medium | trivial | none |
| B1 Mermaid diagram | high | low | none |
| E1 merged PRs | medium, grows | low | empty until the first PR |
| A3 screenshots | high | medium, manual | data visible in shots |
| B2 daily regime | high novelty | high | flaky data source |
| C1 photo of the week | medium, human | medium | EXIF and GPS |

## Constraints any idea must respect

- No private repo name or token in assets, the README, logs or commits.
- No external images or fonts; everything comes from `assets/`.
- Text contrast of at least 4.5:1 on GitHub light and dark.
- Content changes go through `data/profile.yml` and the renderer, which stays all-or-nothing.
