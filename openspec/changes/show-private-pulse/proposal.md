## Why

Visitors see a thin public profile: 2 movie apps, 5 old ML notebooks and 12 stars. The real, ongoing work sits in private repos, and the private cards give no sign that it is alive. This change shows how recently each private project was worked on, and moves the old notebooks out of the way, without widening the token or naming a private repo.

## What Changes

- Add a **pulse strip** (`assets/pulse.svg`) under the private cards in Featured. It has one row per private project with a `card.repo`: the title, its version and how long ago it was last pushed (e.g. "active 2d ago"). The data comes from `pushed_at`, which the metadata-only token already reads.
- Rows are ordered newest first. A recency dot shows freshness: Leaf for 7 days or less, Cyan for 30 days or less, muted for anything older.
- The pulse image gets alt text with the same titles and ages. A new `pulse` README region holds it.
- When no token is set, the renderer leaves `pulse.svg` and the `pulse` region as they were, rather than rendering an empty strip.
- Extend the private-name leak check from the README to `pulse.svg`.
- Add **public repo groups** to `data/profile.yml` (`projects.public.groups`). A group renders as one All projects row (title, stack, one line, plus links to each member repo). Initially one group, "Early ML coursework", holds StartupSuccessPrediction, HousePricePrediction, CricketScore, CustomerSegmentation and MachineLearningPrograms.
- **BREAKING (spec):** All projects and stats counts now count repositories, not table rows. The summary still reads 8 public while the table shows 4 rows.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `glass-svg-assets`: `pulse.svg` joins the required asset set; new requirement for the pulse strip's content, recency colours and alt text.
- `profile-asset-generator`: generates the `pulse` region and asset from `pushed_at`; keeps the token metadata-only; leaves the pulse untouched without a token; runs the leak check on `pulse.svg`; supports public repo groups.
- `profile-readme-layout`: pulse strip placed below the private cards; grouped repos shown as one row; counts are per repository.

## Impact

- `scripts/render_profile.py`: new `render_pulse`, `pulse_block` and pulse alt text; group handling in `gather` and `projects_block`; leak check extended to `pulse.svg`.
- `data/profile.yml`: new `projects.public.groups`; the 5 notebook repos move from `repos` into the group.
- `README.md`: new `<!-- pulse:start -->` / `<!-- pulse:end -->` markers inside Featured (one-time hand edit to add the markers).
- `assets/pulse.svg`: new generated file.
- `PROFILE_TOKEN`: no change (stays Metadata: read).
- The relative ages change daily, so the daily run commits most days. The contribution figures already cause this.
