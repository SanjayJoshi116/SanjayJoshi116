## 1. Prerequisites

- [ ] 1.1 Merge `feat/generate-readme-sections` into main (or base this work on that branch)
- [ ] 1.2 Archive `generate-readme-sections` so its delta specs are in the main specs before this change's deltas apply

## 2. Data

- [ ] 2.1 Set `projects.public.hide` to `[ImageResize, Extra-Curricular-Activity-Management]` in `data/profile.yml`
- [ ] 2.2 Add the `connect` list (label, url, color) for LinkedIn, Instagram and YouTube with the current URLs

## 3. Renderer

- [ ] 3.1 Set `stats["repos"]` to the number of public table rows (D1); keep the stars total over all own non-fork repos
- [ ] 3.2 Move the language share calculation into one helper used by `render_langs()` and the alt text (D2)
- [ ] 3.3 Add `activity_block(data)` with the stats and languages alt text per D2
- [ ] 3.4 Add `render_connect_button(entry)` producing `assets/connect-{slug}.svg` in the flat card style, with no external resources (D3)
- [ ] 3.5 Add `connect_block(cfg)` and include the button SVGs in the in-memory output map, so they are written only when every step succeeds
- [ ] 3.6 Wire the `activity` and `connect` regions into `render_readme()`

## 4. README and docs

- [ ] 4.1 Add `activity` and `connect` marker pairs around the existing blocks in `README.md`
- [ ] 4.2 Link Agrileaf in About: `[Agrileaf](https://agrileaf.in)`
- [ ] 4.3 Update `CLAUDE.md`: images only from `assets/` (no shields.io), and the list of generated regions

## 5. Verification

- [ ] 5.1 Render and review the diff: the 2 hidden rows are gone, the summary and stats card both show 8 public, the alt texts state the figures, Connect is SVG buttons, and the Agrileaf link is present
- [ ] 5.2 Audit the README: every image URL is a relative `assets/` path
- [ ] 5.3 Open each `connect-*.svg` with the network blocked: it renders fully, with no `<script>` and no external references
- [ ] 5.4 Change a connect URL: only that link changes; revert it
- [ ] 5.5 Push on a branch, run the workflow, and review in light and dark themes and on mobile before merging
