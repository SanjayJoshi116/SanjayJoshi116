## Context

Builds on `generate-readme-sections`: README regions between `<!-- NAME:start … -->` / `<!-- NAME:end -->` markers are replaced by `replace_region()`, then checked by the private-name leak check, all in memory before any write. `gather()` already computes the public table rows and the stats figures. `render_stats()` and `render_langs()` own the figures and percentages that the alt text must repeat. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- Alt text and figures come from the same values the SVGs draw, so they cannot disagree.
- No external images left in the README.

**Non-Goals:**
- Screenshots of private apps. The owner has not decided on them.
- Generating About. Only the Agrileaf link is added, by hand.
- Brand logos on the Connect buttons (see D3).
- The GitHub profile sidebar (bio, website), which is not in this repo.

## Decisions

### D1. One repo set for the table and the stat
`gather()` computes the public table rows first, then sets `stats["repos"] = len(rows)`. The stars total keeps using all own non-fork repos. Stars on a hidden repo were still earned.

*Alternative:* keep the stat as the full public count and relabel the table summary as "listed". Rejected: two different numbers next to each other still look like an error.

### D2. Activity region with computed alt text
New `activity` region rendering the existing `<p align="center">` with both `<img>` tags. Alt text:
- Stats: `"GitHub activity: {contributions} contributions in the past year, {commits} public commits, {prs} pull requests, {stars} stars earned, {repos} public repos."`, with numbers formatted by the same `fmt()` the card uses.
- Languages: `"Top languages by code size: Python 41%, TypeScript 30%, …, Other 6%."`. Shares are computed once in a helper used by both `render_langs()` and the alt text, rounded the way the card rounds them.

The README now changes whenever the figures change. That adds no extra commits, because `stats.svg` changes on those same runs.

### D3. Connect buttons: text buttons in `assets/`, no logos
```yaml
connect:
  - label: LinkedIn
    url: https://linkedin.com/in/sanjayjoshi116
    color: "#58A6FF"      # accent dot / underline only, never text
  - label: Instagram
    url: https://instagram.com/s_a_n_j_a_y_j_o_s_h_i_
    color: "#F472B6"
  - label: YouTube
    url: https://youtube.com/@SJThinks
    color: "#F5B544"
```
Each entry renders `assets/connect-{slug}.svg`: a 180×44 flat card (same `surface()` style), a small accent dot in `color`, and the label plus " ↗" in `TEXT`. The `connect` region emits one `<a href=url><img … height="44" alt="{label}"></a>` per entry on one centred line.

The accent colour is used only for a mark, never for text, so the contrast check needs no change. Add the accent colours to `check_contrast()` only if one is later used for text.

The YAML colours above are from the existing palette. They are only meant to tell the buttons apart, not to copy each brand's colours.

*Alternative:* inline brand logos (simple-icons path data). Rejected for now: it adds brand-usage questions and path data to maintain. It can be added later with no layout change.

### D4. Agrileaf link by hand
About stays outside any generated region, as the previous change decided. `**Software Developer @ [Agrileaf](https://agrileaf.in)**`. The URL was checked: it returns 200.

## Risks / Trade-offs

- [Text buttons are less recognisable than brand badges] → The label is the network name and the colours are distinct. Logos can come later (D3).
- [Hiding repos lowers the visible repo count] → Intended. The count now matches what is shown. The repos stay public on GitHub.
- [Language percentages that round to the same value disagree with the card by 1%] → Both use one helper (D2).
- [This branch stacks on an unmerged one] → Merge `generate-readme-sections` first, or base this branch on it and merge the two in order.

## Migration Plan

1. Merge (or base on) `feat/generate-readme-sections`.
2. Add `hide` entries and the `connect` list to `profile.yml`. Add `activity` and `connect` markers around the existing blocks. Add the Agrileaf link.
3. Render locally and review the diff: expect the table rows removed, the new alt texts, the Connect block replaced, the new `connect-*.svg` files, and `stats.svg` showing 8 repos.
4. Push on a branch, run the workflow there, and review in light and dark themes and on mobile before merging.

Rollback: revert the commit. Shields badges come back from the reverted README.

### D5. Hero: contribution chart instead of a typed tagline
The typed tagline only ever showed its first line on static renderers, and the centred layout said little. The hero now pairs the name and a plain `intro` with the past year's contributions summed per week, drawn like a price line (the owner works on NSE trading systems, so the form is native to the subject). One motion: the line draws in once, then the area and end dot fade in. Base styles are the final frame. Daily counts come from GraphQL with a token, or from the public contributions page's tooltips without one; the total is their sum, so the chart and figure cannot disagree.

*Alternative:* a photography viewfinder frame. Rejected by the owner in favour of the chart.

### D6. Sentence-case labels, plain headings
Tracked all-caps labels and emoji headings read as template chrome next to the flat cards. Labels become sentence case; headings become plain words.

### D7. Languages skip hidden repos
Hidden repos are hidden because they don't represent current work; counting their bytes put PHP and HTML on the card. They are skipped in language totals too.
