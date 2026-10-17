## Why

After `generate-readme-sections`, the README is accurate but has a few rough edges for a visitor who skims it. The stats card says 11 public repos while All projects lists 10. The stats and languages images have alt text with no numbers in it. The Connect section uses bright shields.io badges that clash with the flat dark cards and are the last third-party images on the page. Two weak public repos sit in the table next to the strongest work. The page is for every kind of visitor, so the fixes stay neutral: no recruiter-specific "open to" line.

## What Changes

- Hide `ImageResize` and `Extra-Curricular-Activity-Management` from the public table, using the existing `hide` list.
- The stats card's "public repos" figure counts the same repos the public table lists (non-fork, not the profile repo, not hidden), so both numbers match.
- The renderer generates the Activity section between `activity` markers, with alt text that states the real figures (contributions, commits, PRs, stars, repos) and the top languages with their shares.
- The Connect section becomes generated SVG buttons in `assets/` (LinkedIn, Instagram, YouTube), defined in a new `connect` list in `data/profile.yml`. **BREAKING** (layout spec): the README then loads no external images at all, and shields.io is no longer used.
- The Agrileaf employer name in About links to `https://agrileaf.in`. About stays hand-written, rewritten to lead with current builds.
- Hero redesign: the centred name and typed rotating tagline become a left-aligned name and one-sentence `intro`, beside a chart of the past year's weekly contributions. `roles` and `tagline` leave `profile.yml`. The stats card drops its duplicate contributions figure.
- Hidden repos also drop out of language totals.
- Asset labels move to sentence case; README section headings drop emojis.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `profile-readme-layout`: Connect no longer uses shields.io badges, so all README images come from `assets/`. Hidden repos are absent from the public table, and the repo count matches it.
- `profile-asset-generator`: generates the Activity and Connect regions and the connect button SVGs, and uses the table's repo set for the stats count.
- `glass-svg-assets`: the stats and languages alt text must state their figures.

## Impact

- Depends on `generate-readme-sections` (region markers, `hide` list), which is on branch `feat/generate-readme-sections` and not merged yet. Build this on top of that branch, or after it merges.
- `scripts/render_profile.py`: stats repo count, two new regions, a connect button renderer, and contrast checks for the button colours.
- `data/profile.yml`: `hide` entries and a new `connect` list.
- `README.md`: `activity` and `connect` markers; the Agrileaf link in About.
- `assets/`: new `connect-*.svg` files. `stats.svg` changes, because its repo figure changes.
- Profile sidebar (bio, website) is outside this repo; noted for the owner, not part of the tasks.
