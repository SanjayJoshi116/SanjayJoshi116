# CLAUDE.md

GitHub profile README repo for SanjayJoshi116. `README.md` renders on the profile page.

## Layout

- `README.md`: profile page. Images come only from `assets/…`.
- `assets/*.svg`: flat dark SVG cards (hero with contribution chart, featured cards, private pulse strip `pulse.svg`, system diagram `pipeline.svg`, stack, stats, langs, connect buttons). **Generated; don't hand-edit.**
- `data/profile.yml`: source of truth for intro, `site.url`, featured allowlist, projects (private list, card copy and diagram stages, public table, `groups` and `hide`), stack, connect links, languages.
  - `projects.private[].diagram.stages`: at most one private project has one, with 3–6 stages, each with a `title` and a `detail`. Each stage title must fit on one line and its detail on two, or the render fails. It renders as `pipeline.svg` inside a collapsed "How <title> works" `<details>`.
  - `projects.public.groups`: rows of related repos (title, stack, about, repos; all required), shown after the plain `repos` rows. A repo listed twice across `repos` and groups fails the render. Missing or hidden members are skipped, and empty groups are omitted. The public count includes group members.
- `scripts/render_profile.py`: reads `profile.yml` + GitHub API, renders `assets/` and the `hero`, `featured`, `pulse`, `diagram`, `projects`, `stack`, `activity` and `connect` marker regions in `README.md`. Every marker pair must exist. Public repos come from `public_repos()`: with a token, GraphQL `repositories(privacy: PUBLIC)` so GitHub filters private repos out server side; without one or on HTTP 401, unauthenticated REST; all pages. Never list repos with the token through an endpoint that can return private ones. `pulse` (private card projects by last push) needs a token, so without one `pulse.svg` and the `pulse` region are left as they are; with a token but no card repos, both are removed. Pulse ages count IST calendar days. The diagram uses no API data, so its output is the same with or without a token; with no diagram, `pipeline.svg` is deleted.
- `site/`: GitHub Pages landing page (`index.html`, `og.png` preview, copies of the SVGs), built by `render_profile.py --site` from the same data in the same all-or-nothing pass. Gitignored, never committed; holds exactly the last site run's files. `site.url` (https, trailing `/`) is used only for absolute preview-tag URLs; links inside the site are relative. Live at `sanjayjoshi116.github.io/SanjayJoshi116/` (Pages source: GitHub Actions).
- `.github/workflows/render-profile.yml`: renders daily (02:17 UTC, 07:47 IST), on push to `main` touching `data/profile.yml` or the script, and on `workflow_dispatch`. It also polls hourly from 06:17 to 23:17 IST (`47 0-17 * * *` UTC). GitHub schedules are best-effort: most polls are dropped and the rest start late (observed ~4 runs/day, forced render included, Oct 2026), so updates are a few times a day, not hourly. Each poll runs `render_profile.py --fingerprint` (a digest of push times for public repos, minus hidden ones and the profile repo itself, and private card repos, plus today's IST date; kept in `actions/cache`) and renders only if the digest changed, so the first poll of each day always renders. The poll logs only `changed`/`unchanged`, never names, times or the digest. Commits only when output differs. Renders always pass `--site`; after a render on `main` a `deploy` job publishes `site/` to Pages (`github-pages` environment, `main` only), skipped polls and failed renders deploy nothing. The render job only stages the new digest; a `remember` job saves it as the poll's digest after `deploy` succeeds (after the render on other branches), so a failed deploy is retried by the next poll. Other branches upload `site/` as the `site-preview` artifact instead.
- `openspec/specs/`: main specs. `openspec/changes/`: active changes; `archive/` holds finished ones (e.g. the glass-profile-readme redesign).

## Commands

```sh
pip install pyyaml==6.0.2
python scripts/render_profile.py                   # local; unauthenticated API, may hit rate limit
PROFILE_TOKEN=... python scripts/render_profile.py --require-token   # README + assets only
pip install pillow==13.0.0
PROFILE_TOKEN=... python scripts/render_profile.py --require-token --site   # as CI runs it; also builds site/
```

## Rules

- To change content, edit `data/profile.yml`, then re-render. Never edit `assets/*.svg` or any README region between `<!-- NAME:start` and `<!-- NAME:end -->` by hand (`hero`, `featured`, `pulse`, `diagram`, `projects`, `stack`, `activity`, `connect`). About is hand-written.
- Renderer is all-or-nothing: it renders in memory and writes nothing on any error. Keep it that way.
- Text never overflows silently. The render fails on a word wider than its text box (any wrapped copy), a stack row or connect label that doesn't fit, a diagram stage over its lines, or a pulse row whose title and version would reach the widest age label (`active 99mo ago`). On the site, the `og.png` name line must fit (measured with the real font) or the render fails. Too many lines in the hero intro, a card summary or the `og.png` intro end with "…" instead.
- Private repos: never enumerate them, and never write a private repo name or the token to assets, the README, logs or commits. Only `projects.private[].card.repo` values in `profile.yml` are considered; the renderer fails if one would appear in the README, `pulse.svg`, `pipeline.svg`, `site/index.html` or the text drawn into `site/og.png`. For `index.html` only what the page says is checked (text, link, image and preview-tag values), not its markup or CSS.
- Style is flat dark cards (`design.md` D1); glassmorphism was tried and dropped.
- SVGs and the site load no external resources (system font stack, inline CSS, no scripts, remote fonts or images) and must keep text contrast ≥ 4.5:1 on GitHub light and dark; the site's own light and dark page colours (`PAGE`) are checked by `check_contrast()`.
- `PROFILE_TOKEN` repo secret: fine-grained, read-only, metadata for allowlisted repos only.
- Review the rendered profile and the `site-preview` artifact on a branch (desktop light and dark, plus mobile) before merging to `main`.
