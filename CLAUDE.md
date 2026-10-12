# CLAUDE.md

GitHub profile README repo for SanjayJoshi116. `README.md` renders on the profile page.

## Layout

- `README.md`: profile page. Images come only from `assets/…` or `img.shields.io`.
- `assets/*.svg`: flat dark SVG cards (hero, featured cards, stack, stats, langs). **Generated; don't hand-edit.**
- `data/profile.yml`: source of truth for tagline, featured allowlist, projects (private list and card copy, public table), stack, languages.
- `scripts/render_profile.py`: reads `profile.yml` + GitHub API, renders `assets/` and the `hero`, `featured`, `projects` and `stack` marker regions in `README.md`.
- `.github/workflows/render-profile.yml`: runs the renderer daily (02:17 UTC), on push to `main` touching `data/profile.yml` or the script, and on `workflow_dispatch`. Commits only when output differs.
- `openspec/specs/`: main specs. `openspec/changes/`: active changes; `archive/` holds finished ones (e.g. the glass-profile-readme redesign).

## Commands

```sh
pip install pyyaml==6.0.2
python scripts/render_profile.py                   # local; unauthenticated API, may hit rate limit
PROFILE_TOKEN=... python scripts/render_profile.py --require-token   # as CI runs it
```

## Rules

- To change content, edit `data/profile.yml`, then re-render. Never edit `assets/*.svg` or any README region between `<!-- NAME:start` and `<!-- NAME:end -->` by hand (`hero`, `featured`, `projects`, `stack`). About and Connect are hand-written.
- Renderer is all-or-nothing: it renders in memory and writes nothing on any error. Keep it that way.
- Private repos: never enumerate them, and never write a private repo name or the token to assets, the README, logs or commits. Only `projects.private[].card.repo` values in `profile.yml` are considered; the renderer fails if one would appear in the README.
- Style is flat dark cards (`design.md` D1); glassmorphism was tried and dropped.
- SVGs load no external resources (system font stack, no remote fonts or images) and must keep text contrast ≥ 4.5:1 on GitHub light and dark.
- `PROFILE_TOKEN` repo secret: fine-grained, read-only, metadata for allowlisted repos only.
- Review the rendered profile on a branch (desktop light and dark, plus mobile) before merging to `main`.
