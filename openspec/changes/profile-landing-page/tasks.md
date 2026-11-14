## 1. Setup

- [x] 1.1 Add `site:` with `url: https://sanjayjoshi116.github.io/SanjayJoshi116/` to `data/profile.yml`
- [x] 1.2 Add `site/` to `.gitignore`
- [x] 1.3 Pick the current Pillow release and the current majors of `actions/upload-pages-artifact`, `actions/deploy-pages` and `actions/upload-artifact`; note the exact versions for 1.4 and section 5
- [x] 1.4 Add `--site` to the renderer's argument parser; import Pillow only when it is set, failing with a clear `RenderError` if it is missing

## 2. Page

- [x] 2.1 Validate `site.url` on `--site` runs (`https://`, ends in `/`); fail naming `site.url` otherwise
- [x] 2.2 Add light and dark page colour constants and extend `check_contrast()` with each page text colour against its theme background (D5)
- [x] 2.3 Build the page sections from `data` with `html.escape` on every value, in spec order: hero + intro, featured cards (public link to repo, private link to `#projects`), pulse, diagram in `<details>`, All projects table with the same counts as the README, stack, activity, connect
- [x] 2.4 Write the `<head>`: title, meta description from the intro, canonical, Open Graph and Twitter card tags with absolute URLs from `site.url`, inline CSS with `prefers-color-scheme`, system font stack, no remote resources
- [x] 2.5 Responsive CSS: featured cards two-up on desktop and stacked under ~700 px, table and diagram scroll inside their own box, no page scroll sideways at 320 px
- [x] 2.6 Run `check_no_private_names` over the page HTML (target `site/index.html`)

## 3. Preview image

- [x] 3.1 Font lookup: DejaVu Sans, Segoe UI, Helvetica/Arial (bold + regular); fail if none is found
- [x] 3.2 Draw `og.png` (1200×630, flat dark card, accent bar, name, wrapped intro) with measured text; fail if the name doesn't fit one line, end an overlong intro with "…"
- [x] 3.3 Add the `og.png` text colours to `check_contrast()`, and run `check_no_private_names` over every string drawn into the image before drawing

## 4. Writing

- [x] 4.1 Put `site/index.html`, `site/og.png` and `site/assets/*.svg` into `out`, built only from the in-memory `out` (main loads a `pulse.svg` left untouched into `out`)
- [x] 4.2 Let the writer handle `bytes` values, and after writing remove any file under `site/` that is not in this run's output
- [x] 4.3 Confirm a failure anywhere in a `--site` run writes nothing to `assets/`, `README.md` or `site/` (e.g. force a bad `site.url` and an unreachable API)

## 5. Workflow

- [x] 5.1 Install the pinned Pillow next to PyYAML and run the render step with `--require-token --site`
- [x] 5.2 Expose the gate result as a job output; on `main` after a successful render, upload `site/` with `actions/upload-pages-artifact`
- [x] 5.3 Add a `deploy` job: `needs: render`, runs only when it rendered on `main`, `environment: github-pages`, `permissions: pages: write, id-token: write`, `actions/deploy-pages`
- [x] 5.4 On branches other than `main`, upload `site/` with `actions/upload-artifact` instead of deploying
- [x] 5.5 Check that `git add assets README.md` still never picks up `site/` and that no new step prints repo names, push times or the token
- [x] 5.6 Save the poll fingerprint only after the deploy succeeds (staged cache + `remember` job), so a failed deploy is retried

## 6. Docs

- [x] 6.1 `CLAUDE.md`: add the site to Layout (`site/`, `site.url`, `--site`, deploy rules), the `--site` command with `pip install pillow==<pin>`, and the site to the private-name, no-remote and contrast rules

## 7. Verify

- [x] 7.1 Local `--site` run: open `site/index.html` from disk in light and dark, and at 360 px; check every section, link and image
- [x] 7.2 Local default run: `assets/` and `README.md` identical to a run before this change, and `site/` untouched
- [ ] 7.3 Branch: Settings → Pages → Source = GitHub Actions; dispatch the workflow on the branch, download the site artifact and review desktop light, desktop dark and mobile; confirm nothing was deployed
- [ ] 7.4 After merge: dispatch on `main`, confirm `site.url` serves the page, and check the preview in a link preview tool
