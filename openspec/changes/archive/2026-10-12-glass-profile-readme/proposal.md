## Why

The profile README is dense (18 project rows with paragraph-length cells, ~50 tech badges) and visually generic. It also depends on third-party image services of the kind that already broke: two Vercel cards returned 402 DEPLOYMENT_DISABLED and were removed on 2026-10-04, and the header, footer, typing line and stats still load from capsule-render, demolab, github-readme-stats (Vercel) and a Heroku streak service.

## What Changes

- Replace the capsule-render header/footer and demolab typing line with a self-hosted, animated **hero SVG** in `assets/`.
- Adopt the **"Aurora on Ink"** visual language: flat dark cards with gradient accent lines, with motion only in the hero. (Glassmorphism was tried and dropped on 2026-10-12: the scrim needed for readable text left the glass looking muddy. Neumorphism was rejected because it needs a page background GitHub doesn't let us control.)
- Replace both project tables with **4 featured cards**: the 2 most recent public repos and the 2 most recent private repos. Everything else moves to a collapsed `<details>` section.
- Cut the tech stack from ~50 badges to a **20-tool stack card** in 4 groups.
- Replace the Vercel/Heroku stats cards with **self-generated stats cards**.
- Phase 2: a **GitHub Action** regenerates all SVGs from `data/profile.yml` daily and on push.
- **Removed**: capsule-render, readme-typing-svg, github-readme-stats, streak-stats dependencies; ~30 tech badges; project-table paragraphs from the top of the page.

## Capabilities

### New Capabilities
- `profile-readme-layout`: page structure, section order, the featured-vs-collapsed rule, and the trimmed stack
- `glass-svg-assets`: self-hosted SVG hero/cards/grid/stats in the Aurora on Ink flat-card style, including motion and accessibility rules
- `profile-asset-generator`: GitHub Action plus script that renders the assets from `data/profile.yml` and the GitHub API, with allowlist-based recency rotation

### Modified Capabilities
<!-- none: no existing specs -->

## Impact

- `README.md` rewritten; new `assets/`, `data/profile.yml`, `.github/workflows/`, and a render script (Python).
- Needs a fine-grained PAT stored as a repo secret, for private contribution counts and private repo `pushed_at`.
- shields.io Connect badges stay; no other external image hosts remain.
