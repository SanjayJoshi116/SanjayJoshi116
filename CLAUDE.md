# CLAUDE.md

GitHub profile README repo for SanjayJoshi116. `README.md` renders on the profile page.

## Layout

- `README.md`: profile page. Images come only from `assets/…` or `img.shields.io`.
- `assets/*.svg`: glass SVG cards (hero, featured cards, stack, stats, langs). **Generated; don't hand-edit.**
- `data/profile.yml`: source of truth for tagline, featured allowlists, private card copy, stack, languages.
- `scripts/render_profile.py`: reads `profile.yml` + GitHub API, renders `assets/` and the featured block in `README.md`.
- `.github/workflows/render-profile.yml`: runs the renderer daily (02:17 UTC), on push to `main` touching `data/profile.yml` or the script, and on `workflow_dispatch`. Commits only when output differs.
- `openspec/changes/glass-profile-readme/`: proposal, design, specs and `tasks.md` for this redesign.

## Commands

```sh
pip install pyyaml==6.0.2
python scripts/render_profile.py                   # local; unauthenticated API, may hit rate limit
PROFILE_TOKEN=... python scripts/render_profile.py --require-token   # as CI runs it
```

## Rules

- To change content, edit `data/profile.yml`, then re-render. Never edit `assets/*.svg` or the README block between `<!-- featured:start` and `<!-- featured:end -->` by hand.
- Renderer is all-or-nothing: it renders in memory and writes nothing on any error. Keep it that way.
- Private repos: never enumerate them, and never write a private repo name or the token to assets, logs or commits. Only `featured.private` entries in `profile.yml` are considered.
- SVGs load no external resources (system font stack, no remote fonts or images) and must keep text contrast ≥ 4.5:1 on GitHub light and dark.
- `PROFILE_TOKEN` repo secret: fine-grained, read-only, metadata for allowlisted repos only.
- Review the rendered profile on a branch (desktop light and dark, plus mobile) before merging to `main`.
