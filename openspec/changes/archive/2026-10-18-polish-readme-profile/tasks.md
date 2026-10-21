## 1. Prerequisites

- [x] 1.1 Merge `feat/generate-readme-sections` into main (or base this work on that branch)
- [x] 1.2 Archive `generate-readme-sections` so its delta specs are in the main specs before this change's deltas apply

## 2. Data

- [x] 2.1 Set `projects.public.hide` to `[ImageResize, Extra-Curricular-Activity-Management]` in `data/profile.yml`
- [x] 2.2 Add the `connect` list (label, url, color) for LinkedIn, Instagram and YouTube with the current URLs

## 3. Renderer

- [x] 3.1 Set `stats["repos"]` to the number of public table rows (D1); keep the stars total over all own non-fork repos
- [x] 3.2 Move the language share calculation into one helper used by `render_langs()` and the alt text (D2)
- [x] 3.3 Add `activity_block(data)` with the stats and languages alt text per D2
- [x] 3.4 Add `render_connect_button(entry)` producing `assets/connect-{slug}.svg` in the flat card style, with no external resources (D3)
- [x] 3.5 Add `connect_block(cfg)` and include the button SVGs in the in-memory output map, so they are written only when every step succeeds
- [x] 3.6 Wire the `activity` and `connect` regions into `render_readme()`

## 4. README and docs

- [x] 4.1 Add `activity` and `connect` marker pairs around the existing blocks in `README.md`
- [x] 4.2 Link Agrileaf in About: `[Agrileaf](https://agrileaf.in)`
- [x] 4.3 Update `CLAUDE.md`: images only from `assets/` (no shields.io), and the list of generated regions

## 4b. Redesign (D5–D7)

- [x] 4b.1 Replace `roles`/`tagline` with `intro`; hero renders name, intro and weekly contribution chart
- [x] 4b.2 Read daily contribution counts (GraphQL with token, contributions page without)
- [x] 4b.3 Stats card drops the contributions figure
- [x] 4b.4 Sentence-case asset labels; plain README headings; rewrite About
- [x] 4b.5 Skip hidden repos in language totals

## 5. Verification

- [x] 5.1 Render and review the diff: the 2 hidden rows are gone, the summary and stats card both show 8 public, the alt texts state the figures, Connect is SVG buttons, and the Agrileaf link is present
- [x] 5.2 Audit the README: every image URL is a relative `assets/` path
- [x] 5.3 Open each `connect-*.svg` with the network blocked: it renders fully, with no `<script>` and no external references
- [x] 5.4 Change a connect URL: only that link changes; revert it
- [x] 5.5 Push on a branch, run the workflow, and review in light and dark themes and on mobile before merging
- [x] 5.6 Fix verification findings: connect accents limited to Blue, Leaf, Violet and Cyan (renderer rejects others); network timeouts fail as a render error
