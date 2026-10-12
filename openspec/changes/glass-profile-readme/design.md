## Context

GitHub sanitizes README HTML: no `<style>`, no `style=""`, no classes, no JS, no `backdrop-filter`, no `:hover`. Allowed: `<p/div align>`, `<img>`, `<picture>`, `<details>`, `<table>`. An SVG loaded through `<img>` keeps its own `<style>`, `@keyframes`, filters and gradients, so every visual effect has to live inside SVG images. Limits inside those SVGs: no JS, no external fonts or images (inline them as base64), no interactivity, and the whole image is a single link.

Current README audit (2026-10-10): 8 private + 10 public project rows, ~50 badges in 10 groups, and 5 external image hosts (shields.io is stable; the other four are fragile).

## Goals / Non-Goals

**Goals:** look polished on a 10-second skim; no fragile third-party image hosts; low-effort updates through one data file.

**Non-Goals:** neumorphism; animation on every element; a light-theme variant in v1; converting About/Connect text into images.

## Decisions

### D1: Glassmorphism, faked without `backdrop-filter`
Each asset is one frosted surface that fills the whole image (no inner panel inside an outer frame). Layer stack, all clipped to the rounded image shape:
1. Ink background
2. colour blobs with `feGaussianBlur` (stdDeviation 40)
3. Ink scrim at 74% (see Risks: the WCAG AA floor)
4. white frost fill at 6%
5. vertical highlight gradient over the top half (white 7% → 0)
6. 2px gradient accent line along the top edge, fading out at both ends; its colours mark the asset (blue→violet public cards, amber→violet private cards, leaf→blue stats, blue→cyan languages, blue→leaf hero)
7. 1px white stroke at 14%; private cards add a soft amber edge glow
8. text and icons

The hero also gets a faint dot grid (white 7%, 22px pitch). The stack is a single surface whose rows are split by 8% white divider lines, not four separate panels. Section labels carry a coloured status dot, and corner values (★ stars, version) sit in pill chips.

*Changed 2026-10-12:* the first version layered a frosted inner panel over sharp blobs inside an outer frame. The blobs clipped hard at the frame edge and read as muddy coloured borders, and the box-inside-a-box framing looked busy. The 74% scrim keeps colour muted. Dropping it to 68% would push muted and blue text below 4.5:1, so muted colour is the accepted cost of AA.

Renders the same in every browser. Avoid `<foreignObject>`, which is unreliable in Safari when SVG is loaded via `<img>`.
*Rejected:* neumorphism (needs to match GitHub's page background, which differs across light, dark, dimmed and high-contrast themes; poor contrast).

### D2: Palette "Aurora on Ink"
| Role | Name | Hex |
|---|---|---|
| Background | Ink | `#0B1020` |
| Blob 1 | Signal Blue (current brand) | `#58A6FF` |
| Blob 2 | Leaf (agriculture/CV) | `#34D399` |
| Blob 3 | Violet (ML/research) | `#8B5CF6` |
| Accent | Amber (used sparingly; marks private work) | `#F5B544` |
| Text | primary / secondary | `#F0F6FC` / `#9DA7B3` |

Cards are dark-only in v1 and read as deliberate dark panels on GitHub's light theme. A light variant via `<picture>` + `prefers-color-scheme` comes later, if wanted.

### D3: Motion budget
- Only the hero animates: slow blob drift plus a CSS-keyframe typing line.
- Cards, grid and stats stay static.
- Every animated SVG includes `@media (prefers-reduced-motion: reduce)`.
- The first frame must look complete on its own, because the GitHub mobile app renders animation inconsistently.

### D4: Page layout (option C: hero + project cards)
1. Glass hero (animated): `assets/hero.svg`
2. About: 4 markdown lines; Lightroom moves here ("shoots & edits in Lightroom")
3. Featured: 4 glass cards, 2 public on top and 2 private below
4. `▸ All projects` (`<details>`): the remaining private projects as one-liners, plus the public table
5. Stack grid: `assets/stack.svg`
6. Stats + top languages: `assets/stats.svg`, `assets/langs.svg` (no streak)
7. Connect: shields.io badges (kept)

### D5: Featured selection = 2 most recent public + 2 most recent private
- Snapshot 2026-10-10:
  - Public (verified via API): `movie-app-v2` (CINE DB, ★2, pushed 10-09) and `movie-dash-v2` (★1, 10-08).
  - Private (confirmed by the owner on 2026-10-11): SwingTrade AI (v0.25) and Expense Tracker (v1.7). In phase 1 these are pinned by hand. In phase 2, rotation takes over within the allowlist (D8).
- Presented as two themed pairs: "🎬 Shipped in public" (blue/violet glow) and "🔒 Building in private" (amber edge glow).
- Public cards link to the repo and show live stars. Private cards have no repo link (it would 404 for visitors); they anchor to the All projects section and show a version number from `profile.yml`.
- Forks (`conjecscore`, `quant_backtesting`) are excluded.

### D6: Stack trimmed to 20 tools in 4 groups
- **BUILD:** Python, TypeScript, React, Vite, Ant Design, Django, Node.js
- **DATA & ML:** PostgreSQL, Redis, Celery, Pandas, scikit-learn, LightGBM, PyTorch
- **VISION:** YOLO11, OpenCV, Raspberry Pi
- **SHIP:** Docker, GitHub Actions, Playwright

Dropped: Java, C, C++, PHP, JavaScript, HTML5, CSS3, Bootstrap, Recharts, Chart.js, React Query, Zustand, DRF, Express, Apache, MySQL, MSSQL, Firebase, SQLite, NumPy, XGBoost, Streamlit, Plotly, Anaconda, PaddleOCR, Flask, Arduino, Vitest, Lightroom (moved to About), Canva.

### D7: Generator Action (phase 2)
`data/profile.yml` (tagline lines, allowlists, private-card copy, stack) plus the GitHub API feed a Python render script that uses the glass SVG templates and writes `assets/*.svg`. Triggers: daily cron and push to `profile.yml`. It commits only when output changed.
*Rejected:* `lowlighter/metrics` (can't match the glass style); hand-only SVGs (stars and stats go stale).

### D8: Recency rotation only within an allowlist
The Action never lists all private repos. It reads `pushed_at` only for repos allowlisted in `profile.yml`, then picks the newest 2 per visibility. This prevents leaking Agrileaf, client or scratch repos onto the public profile.

## Risks / Trade-offs

- **SVG text is not searchable or selectable.** Mitigation: keep About and the All projects section as markdown, and give every image meaningful `alt` text.
- **The PAT is a long-lived secret.** Mitigation: a fine-grained PAT, read-only, scoped to the allowlisted repos and metadata.
- **Three-quarters-themed cards could look repetitive.** Mitigation: the two-pair framing (public/private).
- **Over-animation.** Mitigation: the D3 motion budget.

### D9: Implementation notes (added during apply, 2026-10-11)
- The phase 1 assets come from the phase 2 renderer (`scripts/render_profile.py`), not from hand-built SVGs, so both phases share one set of templates.
- Card file names are stable (`card-public-1.svg` …). The renderer also rewrites the README block between `<!-- featured:start -->` and `<!-- featured:end -->`, so links and alt text follow rotation.
- To meet WCAG AA over the brightest blob, the glass needs an Ink scrim at 74% under the frost layer. The renderer checks this worst case on every run.
- Language stats skip Jupyter Notebook (notebook output swamps real code), plus Hack, SCSS, Dockerfile and Shell.
- Without a token, contributions come from the public contributions page and only public data is used. With a token, contributions come from GraphQL and private language bytes come from allowlisted repos.

## Phasing

- **Phase 1:** hand-built SVGs (hero, 4 cards, stack, static stats), README restructure, all fragile hosts removed.
- **Phase 2:** `profile.yml`, the render script, the Action, the PAT secret, and auto-updated stars, stats and rotation.

## Open Questions

Resolved 2026-10-11:
- Featured private cards are SwingTrade AI and Expense Tracker.
- The streak stat is dropped. The stats card shows totals and top languages only.
- Light-theme variants are deferred and stay out of this change.
