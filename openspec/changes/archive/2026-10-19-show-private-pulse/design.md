## Context

`gather()` already reads `/repos/{card.repo}` for every private project with a card, but only when a token is set and every card has a `repo`. It uses `pushed_at` to rotate the 2 featured private cards, then drops the other 2. The token is fine-grained with Metadata: read only, and the user chose to keep it that way (see proposal.md). The public table rows come from `projects.public.repos`, then any other unhidden public repos from the API. `stats["repos"]` is `len(rows)`, and the summary uses the same number.

## Goals / Non-Goals

**Goals:**
- Reuse the `pushed_at` values that rotation already fetches; add no new API calls.
- Keep the renderer all-or-nothing and the leak check strict.
- Keep group configuration declarative in `profile.yml`.

**Non-Goals:**
- Commit counts, sparklines, or anything else that needs Contents: read.
- Private projects without a `card.repo` (they have no readable metadata).
- Pulse rows for public repos (their cards already show activity through stars and links).

## Decisions

**D1. Pulse data comes from the sorted private list before it is trimmed to 2.** `gather` returns `pulse` as all card projects sorted by `pushed`, each with `title`, `version` and `pushed`. Rotation keeps `private[:2]`. Alternative: a second fetch per repo. Rejected: it duplicates calls and could disagree within one run.

**D2. No token → the pulse is preserved, not rendered.** `main` adds `pulse.svg` to the write set only when `data["pulse"]` is present. `render_readme` copies the existing `pulse` region text through unchanged; the marker is still required, so a missing marker still fails. Alternative: render an empty or "unavailable" strip. Rejected: a local unauthenticated run would then churn the README and assets. The existing no-token rotation fallback already differs from CI, but only in order, never in content shape.

**D3. Ages are bucketed and computed against an injectable `now`.** Buckets: "today" (0 days), `Nd` (1–13 days), `Nw` (14–62 days, days // 7), `Nmo` (63+ days, days // 30). The SVG uses the short form; the alt text uses words ("2 days ago"). `render_pulse(rows, now)` takes `now` so tests are deterministic; `main` passes `datetime.now(timezone.utc)`. Alternative: exact dates. Rejected: dates read as stale and invite the question "why not today?".

**D4. Recency colours reuse the palette.** Leaf ≤ 7 days, Cyan ≤ 30 days, Muted otherwise. The dot is decoration; the age text is always `TEXT` or `MUTED`, both already contrast-checked on `SURFACE`. Amber appears only as the private edge, as on the private cards.

**D5. Layout.** The viewBox is 860 wide, matching two 420-wide cards plus a gap. It has a 44px header ("Private work, last active") and then 30px per row: dot, title, version in mono, and the age right-aligned. It is rendered at `width="100%"` in its own `<p align="center">`, with no link, because a private repo has nowhere to go.

**D6. The leak check runs on pulse output too.** `check_no_private_names` is generalised to take a label for its error, and it is called on the rendered `pulse.svg` string as well as the README. The error names the file, never the value.

**D7. Groups are rows with a `members` list.** `projects.public.groups[]` has `title`, `stack`, `about` and `repos`. `gather` validates that no repo appears twice across `repos` and all groups, and adds every group member to `seen` so the API fallback never repeats it. Each group becomes a row `{title, members: [{repo, url}], stack, about}` appended after the individual rows. `stats["repos"]` becomes the number of repositories across rows (1 per plain row, `len(members)` per group). The row's name cell is `**Early ML coursework**<br>[A](…) · [B](…) · …`. Alternative: a nested `<details>` per group. Rejected: nested disclosure inside a table renders badly on mobile.

## Risks / Trade-offs

- [`pushed_at` counts any push, including a branch push or force-push] → Acceptable: it signals activity, not shipped work, and the copy says "active", not "released".
- [Ages change daily, so the cron commits most days] → Already true because of the contribution figures; no new churn source.
- [A token that loses access to one card repo fails the whole run] → Existing behaviour for rotation; unchanged.
- [Groups hide the notebook repos one click deeper] → Intended; every member is still linked in the table.

## Migration Plan

1. Add `<!-- pulse:start -->` / `<!-- pulse:end -->` below the private card row in `README.md`, outside the featured markers (a one-time marker edit).
2. Move the 5 notebook entries from `projects.public.repos` into one group in `profile.yml`.
3. Run with `PROFILE_TOKEN` on a branch, then review light, dark and mobile.

Rollback: revert the commit. `pulse.svg` becomes unreferenced and harmless until it is deleted.
