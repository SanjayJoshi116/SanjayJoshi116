## Context

`scripts/render_profile.py` gathers everything once (`gather()`), renders every SVG and the README in memory into an `out` dict of path → text, runs the contrast and private-name checks, and only then writes. The workflow renders on push, daily and on polls the push-fingerprint gate lets through, then commits `assets/` and `README.md` if they changed. Motivation: see proposal.md (Why). Requirements: see `specs/profile-landing-page/spec.md`.

## Goals / Non-Goals

**Goals:**
- One more output of the same render pass, so the site can never disagree with the README written by the same run.
- No new runtime dependency for the default (README-only) run.
- Keep every existing guarantee: all-or-nothing writes, private-name checks, nothing remote, contrast ≥ 4.5:1, nothing private in logs.

**Non-Goals:**
- Root URL or custom domain (later: change `site.url`, add `CNAME` or move the build).
- Templating, a static site generator, client-side JavaScript or analytics.
- Making the SVG cards themselves theme-aware. They stay flat dark cards, as on GitHub.

## Decisions

**D1. Opt-in `--site` flag.** The site is built only with `--site`; CI always passes it. A plain local run keeps today's behaviour and needs only PyYAML.
*Alternative:* always build the site. Rejected: every local run would need Pillow and a font, for output that is not committed.

**D2. `og.png` drawn with Pillow from a system TrueType font.** The image is a simple flat dark card: name, intro, accent bar. Pillow ships wheels for every platform with no system libraries, and `ImageFont.getlength` measures with the real font, so the overflow rule is exact instead of the width estimate the SVGs use. Font lookup tries, in order, DejaVu Sans (Ubuntu runner), Segoe UI (Windows) and Helvetica/Arial (macOS), bold and regular; none found → `RenderError`. The PNG differs slightly by machine, which is fine because it is never committed.
*Alternatives:* cairosvg rendering `hero.svg` (needs the system cairo library, awkward on Windows, and the hero isn't 1200×630); resvg (same font-resolution issue, less common); a committed static PNG (drifts from `profile.yml`); headless Chrome screenshot (heavy, slow, flaky in CI). Pillow is pinned to an exact version and installed only in CI and for local `--site` runs.

**D3. Page built as a string in the renderer, from the same data.** New `site_*` builders mirror the README blocks (`hero_block`, `featured_block`, `projects_block`, …) and emit HTML with `html.escape` on every value. They take the same `data` dict, so content and counts match the README by construction. No Jinja or Markdown library.
*Alternative:* convert the rendered README Markdown to HTML. Rejected: needs a Markdown dependency and GitHub-specific `<picture>`/`<details>` handling, and the table would still need restyling.

**D4. Base URL from `site.url` in `profile.yml`.** v1 value `https://sanjayjoshi116.github.io/SanjayJoshi116/`. Used only for absolute URLs in meta tags; all links between site files are relative.
*Alternative:* take `base_url` from `actions/configure-pages`. Rejected: local runs couldn't produce valid tags, and a custom domain later is a one-line data change either way. As a result `configure-pages` is not needed.

**D5. Page theme.** Page background and text colours are new constants with a light set (white background, near-black and grey text, GitHub-blue links) and a dark set (GitHub dark background, the existing `TEXT`/`MUTED`/`BLUE`). They switch with `@media (prefers-color-scheme: dark)`. `check_contrast()` gains these pairs (each text colour against its own background, both themes) plus the `og.png` pairs. Cards are `<img>` of the dark SVGs in both themes; on the light page they read as dark tiles, as they do on GitHub light.

**D6. Site files come from the in-memory `out` dict.** SVGs placed in `site/assets/` are copied from this run's rendered content, not from disk, so the site always matches the README of the same run. Exception: without a token the pulse is left untouched, so the existing `assets/pulse.svg` on disk is copied if the README still shows it. CI always has the token, so this matters only for local runs.

**D7. Writer handles bytes and syncs `site/`.** `out` values may be `bytes` (PNG). After the in-memory render and all checks pass, the writer writes changed files as today, then deletes any file under `site/` that is not in this run's output. `site/` is in `.gitignore`.

**D8. Workflow shape.** The render job installs Pillow, runs `render_profile.py --require-token --site`, and, if the gate rendered:
- on `main`: `actions/upload-pages-artifact` with `path: site`, then a separate `deploy` job (`needs: render`, `environment: github-pages`, `permissions: pages: write, id-token: write`) runs `actions/deploy-pages`. The job runs only when the render job's gate output says it rendered and `github.ref_name == 'main'`;
- on any other branch: `actions/upload-artifact` with `site/` for download and review.
A failed render stops the job before the upload, so nothing deploys. The `github-pages` environment's default rule allows deploys only from the default branch, which backs up the `main` check. Action majors are pinned like the existing steps; check the current majors when implementing.
*Alternative:* deploy on every run, skipped polls included. Rejected: nothing changed, and it adds Pages builds and log lines for no gain.

## Risks / Trade-offs

- [Deploy fails after the assets commit] → the render job only stages its fingerprint (`staged-fp-<run>` cache); a `remember` job promotes it to `push-fp-<run>` after `deploy` succeeds (or after the render, on branches). A failed deploy leaves the old fingerprint, so the next poll renders and redeploys. A failed `deploy` job shows red in Actions.
- [Link previewers cache `og.png` for days] → expected; use LinkedIn Post Inspector / the X card validator to refresh after a visible change.
- [Font differs between local and CI] → measurement uses the actual font, so overflow is caught wherever the run happens; CI is the reference.
- [New dependency surface (Pillow)] → exact pin, CI-only; no image input is ever parsed, Pillow only draws.
- [Private card titles become indexable on a public site] → no new exposure: the same titles are already public in the README; repo names stay guarded.
- [Branch review needs a download] → the artifact zip opens directly from disk, since all site links are relative.

## Migration Plan

1. Merge only after reviewing a branch run's site artifact (desktop light and dark, plus mobile), as for the README.
2. Before or right after merging: Settings → Pages → Source = GitHub Actions.
3. Run the workflow with `workflow_dispatch` on `main` for the first deploy; confirm `site.url` serves the page and a preview tool shows `og.png`.
4. Rollback: set Pages source to none (or unpublish) and revert the change; the README and `assets/` are unaffected throughout.
