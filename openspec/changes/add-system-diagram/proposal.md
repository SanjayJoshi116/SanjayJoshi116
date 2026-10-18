## Why

The private cards say what SwingTrade AI does, but not how it is built. A small system diagram shows design thinking on a profile whose best work is private, without exposing code, thresholds or the repository name.

## What Changes

- Add a generated `assets/pipeline.svg`: one flat dark card with 5 stage boxes in a row joined by arrows. Initially: NSE data (752 stocks, daily) → Indicators → 23 detectors → Scan + score → Alerts (email, Telegram).
- Stages are defined in `data/profile.yml` as a `diagram` on the private project, each with a title and a short detail line, so the diagram can be edited without code changes.
- Add a new `diagram` README region: a collapsed `<details>` titled "How SwingTrade AI works", holding the image and one-sentence alt text that walks through the stages in order.
- Place it in Featured, after the private cards (and after the pulse strip once `show-private-pulse` lands).
- Run the private-name leak check on `pipeline.svg` and the diagram region.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `glass-svg-assets`: new requirement for the pipeline diagram asset (layout, palette, static, no repository data).
- `profile-asset-generator`: generates the diagram from `profile.yml`, validates the stage count and length, and leak-checks the diagram.
- `profile-readme-layout`: new collapsed "How … works" block in Featured.

## Impact

- `scripts/render_profile.py`: new `render_diagram`, `diagram_block`, stage validation, and a leak check on the diagram output.
- `data/profile.yml`: a `diagram.stages` list on the SwingTrade AI private project.
- `README.md`: new `<!-- diagram:start -->` / `<!-- diagram:end -->` markers in Featured (a one-time marker edit).
- `assets/pipeline.svg`: new generated file.
- No API calls and no token change; the diagram renders the same with or without a token.
- Overlaps `show-private-pulse` only in README placement; both changes add requirements rather than modifying the same ones, so they archive in any order.
