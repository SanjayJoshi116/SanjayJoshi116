## 1. Data and markers

- [x] 1.1 Add `diagram.stages` to SwingTrade AI in `data/profile.yml`: NSE data / 752 stocks, daily; Indicators / EMA, RSI, ATR, market regime; 23 detectors / breakouts, pullbacks, reversals; Scan + score / weighted score, veto layer; Alerts / email, Telegram
- [x] 1.2 Add `<!-- diagram:start -->` / `<!-- diagram:end -->` markers to `README.md` after the pulse markers

## 2. Generator

- [x] 2.1 In `gather`, collect the one private project with a `diagram`; fail on two, or on fewer than 3 or more than 6 stages
- [x] 2.2 Add `render_diagram(project)` per design D2: header, boxes, Blue arrows, amber private edge, fail-on-overflow wrapping (D3)
- [x] 2.3 Add `diagram_block` (collapsed `<details>`, "How <title> works", full-width image, stage-by-stage alt text) and wire the `diagram` region into `render_readme`; empty region and no asset when no diagram
- [x] 2.4 Leak-check the rendered `pipeline.svg` (target `assets/pipeline.svg`), reusing or adding the generalised `check_no_private_names`

## 3. Verification

- [x] 3.1 Render: `pipeline.svg` has 5 boxes and 4 arrows in order, no `<script>`, no external references, no repo names; the README region is collapsed with the expected alt text
- [x] 3.2 Add a 7th stage: the run fails naming the limit; revert
- [x] 3.3 Lengthen one title past one line: the run fails naming the stage; revert
- [x] 3.4 Put the bare word "trade" in a detail: the run fails naming `assets/pipeline.svg` without printing the name; revert
- [x] 3.5 Remove the `diagram` end marker: the run fails naming it; restore
- [x] 3.6 Run without a token: the diagram output is identical to a run with a token
- [ ] 3.7 Update CLAUDE.md (diagram region and asset) and review on a branch in light, dark and mobile, with the details expanded
