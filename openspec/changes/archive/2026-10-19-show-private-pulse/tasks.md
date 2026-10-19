## 1. Data and markers

- [x] 1.1 Add `projects.public.groups` to `data/profile.yml` with one "Early ML coursework" group (title, stack, about, repos) and remove its 5 repos from `projects.public.repos`
- [x] 1.2 Add `<!-- pulse:start -->` / `<!-- pulse:end -->` markers to `README.md` directly below the private card row, outside the featured markers

## 2. Public repo groups

- [x] 2.1 In `gather`, read groups, fail on a repo listed twice (across `repos` and groups), skip missing or hidden members, omit empty groups, and add members to `seen`
- [x] 2.2 Count `stats["repos"]` per repository (group members included)
- [x] 2.3 Render group rows in `projects_block` after the plain rows (bold title, then linked members), and use the per-repository count in the summary

## 3. Pulse strip

- [x] 3.1 Return `pulse` from `gather`: every card project sorted by `pushed`, only when the token path fetched `pushed_at`
- [x] 3.2 Add the age-bucket helper (today / Nd / Nw / Nmo, plus a long form for alt text) with an injectable `now`
- [x] 3.3 Add `render_pulse(rows, now)`: 860-wide flat card with the amber edge, a header, one row per project with a recency dot (Leaf / Cyan / Muted), title, mono version and right-aligned age
- [x] 3.4 Add `pulse_block` with alt text "Private work, last active: …" and wire the `pulse` region into `render_readme`
- [x] 3.5 Without a token, skip writing `pulse.svg` and pass the existing `pulse` region through unchanged (the marker is still required)
- [x] 3.6 Generalise `check_no_private_names` to take a target label and run it on the rendered `pulse.svg`

## 4. Verification

- [x] 4.1 Run with a fixed `now` and fake `pushed` values: the order, buckets (0d, 2d, 13d, 14d, 45d, 63d) and dot colours match the spec
- [x] 4.2 Put a card's `owner/name` into its title: the run fails, writes nothing and the error does not print the value
- [x] 4.3 Run without a token: `pulse.svg` and the `pulse` region are byte-identical before and after
- [x] 4.4 Duplicate `CricketScore` under `repos` and in the group: the run fails naming it; revert
- [x] 4.5 Full render: the table has 4 rows, the summary and stats card still show 8 public, all 5 notebook repos are linked, and `pulse.svg` has no `<script>`, no external references and no repo names
- [x] 4.6 Remove the `pulse` end marker: the run fails naming it and writes nothing; restore it
- [x] 4.7 Update CLAUDE.md (pulse region, groups) and review on a branch in light, dark and mobile before merging
