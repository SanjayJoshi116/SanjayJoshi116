## Context

The renderer builds every asset from `data/profile.yml` and the GitHub API in memory, then writes all or nothing. Private card copy lives on `projects.private[]`. `check_no_private_names` already blocks `owner/name` values and bare names of 5+ characters as whole words; the bare names include `trade`. `show-private-pulse` (not yet archived) adds a `pulse` region directly after `featured` and generalises the leak check to take a target label.

## Goals / Non-Goals

**Goals:**
- A diagram that matches the flat card system and renders identically on desktop, mobile and the GitHub app.
- Stage copy editable in `profile.yml` only.
- No API calls, so the diagram is deterministic and identical with or without a token.

**Non-Goals:**
- Branches, loops or multiple rows (the backtester and outcome-ledger loop were deliberately left out).
- Mermaid or any other rendering GitHub would do client-side.
- Diagrams for more than one project.

## Decisions

**D1. Generated SVG, not Mermaid.** A Mermaid block would take GitHub's diagram style, not the Ink card style; its rendering in the GitHub mobile app is unverified, and it is not an `assets/` image, so the image-host rule would need a carve-out. The cost is one renderer function.

**D2. Fixed single-row layout.** viewBox 860 wide, the same as the pulse strip. Margins 36, arrow gaps 24, so box width = (860 − 72 − 24·(n−1)) / n (138px at n = 5). Boxes are 76px tall, with rx 10, a translucent white fill (`.04`) and a hairline stroke. Inside each box: the title (13px, 600 weight, `TEXT`) on 1 line, and the detail (11.5px, `MUTED`) on up to 2 lines, both wrapped with the existing `wrap` at box width minus 16. Arrows are a 2px line plus a chevron in Blue. A 44px header carries "How <title> works" in `MUTED`. The 3–6 stage bound keeps boxes at least 99px wide, so wrapping stays legible.

**D3. Overflow fails rather than truncates.** `wrap` truncates with "…". For the diagram, the renderer instead fails when the title needs more than 1 line or the detail more than 2, naming the stage. A cut-off architecture label reads as a bug; a failed run is caught at review.

**D4. The diagram lives on the project.** It is `projects.private[i].diagram.stages`, so the summary title comes from that project's `title`; renaming the project renames the block. gather collects at most one such project, and two fail.

**D5. Its own region, after `pulse`.** Markers `<!-- diagram:start -->` / `<!-- diagram:end -->` sit after the pulse markers, or after `featured:end` if the pulse change has not landed. The block is `<details>\n<summary><b>How … works</b></summary>\n\n<p align="center"><img src="assets/pipeline.svg" width="100%" alt="…"></p>\n\n</details>`. With no diagram configured, the region is empty and the asset is not written.

**D6. The leak check reuses the README matcher.** If `show-private-pulse` has landed, call the generalised `check_no_private_names(text, repos, "assets/pipeline.svg")`; otherwise add the same `target` parameter here. Whichever change is applied second keeps the single generalised version. The README's own check already covers the region.

## Risks / Trade-offs

- [A stage label uses the bare word "trade" and fails the leak check] → Intended: the stage copy avoids it, and the error names the file so the cause is clear.
- [The diagram drifts from the real system] → The stages are copy in `profile.yml`, reviewed like the card summaries; the 23-detector count matches the SwingTrade AI README as of 2026-10-18.
- [Both open changes edit `render_readme` and README marker order] → Small and mechanical; whichever lands second rebases its region tuple and marker position.

## Migration Plan

1. Add the `diagram` markers to `README.md`.
2. Add `diagram.stages` to SwingTrade AI in `profile.yml`.
3. Render, then review on a branch in light, dark and mobile (expand the details on mobile).

Rollback: remove the `diagram` block from `profile.yml`. The region renders empty and the asset is left unreferenced.
