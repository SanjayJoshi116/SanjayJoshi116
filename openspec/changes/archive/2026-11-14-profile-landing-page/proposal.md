## Why

The profile README only exists inside GitHub. Its links show no preview when shared (LinkedIn, Slack, WhatsApp), the layout is fixed by GitHub's renderer, and there is no page to put on a CV or in an email signature. A GitHub Pages site built from the same `data/profile.yml` gives a shareable landing page without a second copy of the content to keep in sync.

## What Changes

- The renderer gets a `--site` mode that also builds a static site in `site/` from `data/profile.yml`, the same API data and the same SVG cards as the README: intro, featured cards, pulse strip, system diagram, All projects table, stack, activity and connect links.
- The page has its own light and dark theme (`prefers-color-scheme`), works at phone width, and loads nothing remote: inline CSS, system font stack, local SVGs only.
- The page carries title, description, canonical and Open Graph / Twitter card tags with absolute URLs, plus a generated 1200×630 PNG preview image (`og.png`), because link previewers don't show SVG.
- The site's base URL comes from a new `site.url` key in `data/profile.yml` (v1: `https://sanjayjoshi116.github.io/SanjayJoshi116/`).
- The private-repo name check covers every text output of the site, including the text drawn into `og.png`. The renderer stays all-or-nothing: on any error neither `assets/`, `README.md` nor `site/` is written.
- `site/` is build output: gitignored, never committed, and rebuilt in full on every site run.
- The render workflow runs the renderer with `--site` and, on `main`, publishes `site/` to GitHub Pages through `actions/upload-pages-artifact` and `actions/deploy-pages`, only when the render ran (not on polls the gate skips). On other branches it uploads the site as a downloadable workflow artifact for review instead of deploying.
- Repo setting: Settings → Pages → Source = GitHub Actions (one-time, manual).
- `CLAUDE.md` gets the site in its layout, commands and rules.
- Out of scope for v1: a root URL (`SanjayJoshi116.github.io` repo), a custom domain, and the hand-written About section.

## Capabilities

### New Capabilities

- `profile-landing-page`: the generated GitHub Pages site: its content, theme, preview metadata and image, privacy guard, all-or-nothing build and deploy rules.

### Modified Capabilities

None. Default runs (no `--site`) keep their current behaviour and outputs.

## Impact

- `scripts/render_profile.py`: `--site` flag, HTML page builder, `og.png` drawing, site contrast check, private-name check over site output, writer handles binary files and clears stale files in `site/`.
- `data/profile.yml`: new `site.url` key.
- `.github/workflows/render-profile.yml`: `--site` on the render step, Pillow install, Pages permissions (`pages: write`, `id-token: write`) and a deploy job; branch runs upload a review artifact.
- New Python dependency: Pillow (pinned), only needed with `--site`. A TrueType font is read from the runner (DejaVu Sans on Ubuntu).
- `.gitignore`: `site/`.
- `CLAUDE.md`: layout, commands, rules.
- GitHub: one-time Pages source setting; a `github-pages` environment is created on first deploy.
