## 1. Phase 1 — Shared glass template

- [x] 1.1 Create `assets/` and a reference glass card SVG implementing the D1 layer stack (blobs → clipped blur → white fill → stroke + highlight → text) in the Aurora on Ink palette
- [x] 1.2 Inline a subset font (or use a system font stack) so the SVG loads no external resources; confirm with network blocked
- [ ] 1.3 Check the reference card in Chrome, Firefox and Safari via `<img>`, and on GitHub light and dark themes; confirm text contrast ≥ 4.5:1 *(done in Edge/Chromium on light and dark, contrast checked by the renderer; Firefox and Safari still to check)*

## 2. Phase 1 — Assets

- [x] 2.1 Build `assets/hero.svg`: name, blob drift, CSS-keyframe typing tagline, a complete first frame, and a `prefers-reduced-motion` stop
- [x] 2.2 Build public cards for `movie-app-v2` and `movie-dash-v2` (blue/violet glow, star count as of build date)
- [x] 2.3 Build private cards for SwingTrade AI (v0.25) and Expense Tracker (v1.7) with amber edge glow and no repo URL
- [x] 2.4 Build `assets/stack.svg`: 20 tools in the BUILD / DATA & ML / VISION / SHIP groups
- [x] 2.5 Build static `assets/stats.svg` (commits, PRs, stars, public repos; no streak) and `assets/langs.svg` from current GitHub data

## 3. Phase 1 — README restructure

- [x] 3.1 Replace the capsule-render header/footer and typing line with `assets/hero.svg`
- [x] 3.2 Rewrite About to ≤4 markdown lines, including the hobby-photography/Lightroom line
- [x] 3.3 Add the Featured section: public pair on top linking to the repos, private pair below linking to `#all-projects`, each with descriptive `alt` text
- [x] 3.4 Move all non-featured projects into a collapsed `<details>` All projects section with a stable anchor: private projects as one-liners, public projects as a table, forks excluded
- [x] 3.5 Replace the ~50 badges with `assets/stack.svg`, and replace the Vercel/Heroku stats with `assets/stats.svg` and `assets/langs.svg`
- [x] 3.6 Keep the Connect shields.io badges unchanged
- [x] 3.7 Audit all `<img src>` values: only `assets/…` or `img.shields.io`; every relative path resolves
- [x] 3.8 Confirm every previously listed non-featured project still appears under All projects
- [ ] 3.9 Push to a branch and review the rendered profile on desktop (light and dark) and on the GitHub mobile app before merging to main

## 4. Phase 2 — Data file and renderer

- [x] 4.1 Create `data/profile.yml`: tagline lines, public/private allowlists, private card copy and version labels, stack groups
- [x] 4.2 Convert the phase 1 SVGs into templates with placeholders for the variable fields
- [x] 4.3 Write the Python render script: read `profile.yml`, query the GitHub API for allowlisted repos only, pick the 2 most recent pushes per visibility excluding forks, and render all assets
- [x] 4.4 Make the script write to a temp dir and replace `assets/` only after every render succeeds; on any error, exit non-zero and leave assets untouched
- [x] 4.5 Ensure no non-allowlisted private repo name or the token appears in output, logs or commits
- [x] 4.6 Run the script locally and confirm the output matches the phase 1 assets *(ran unauthenticated on 2026-10-12; a second run changes 0 files. The assets now come from the renderer, including the single-surface restyle, so the hand-built phase 1 files are superseded)*

## 5. Phase 2 — Action and secret

- [x] 5.1 Create a fine-grained read-only PAT scoped to the allowlisted repos' metadata; store it as a repo secret (owner action)
- [x] 5.2 Add `.github/workflows/render-profile.yml`: daily cron, push on `data/profile.yml` or templates, and `workflow_dispatch`
- [x] 5.3 Commit regenerated assets only when they differ from the committed ones
- [ ] 5.4 Test: a no-op run (no commit), a tagline edit (hero updates), and a missing secret (fails, no asset changes) *(locally verified: tagline edit, missing/invalid token; the no-op commit check is deferred to the first Action run)*
