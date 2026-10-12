## 1. Prerequisites

- [x] 1.1 Archive `glass-profile-readme` (or confirm with the owner that its 2 open tasks can be closed) so this change's delta specs land on existing main specs *(archived 2026-10-12 with 1.3 open, by owner choice)*
- [x] 1.2 Get the owner's wording for Swing-Trade Research *(title: "Swing-Trade Research"; LightGBM wording keeps the card's "cost-aware" unless the owner changes it)*

## 2. Data migration

- [x] 2.1 Add `projects.private` to `data/profile.yml` with all 8 private projects copied from the README list as is (title, version, summary, stack, `with` for the NSE Signal Bot)
- [x] 2.2 Move each `featured.private` entry's `repo`, `summary` and `tags` into a `card:` block on the matching project, and delete `featured.private`
- [x] 2.3 Add `projects.public.repos` with the 10 current table rows as is (label, stack, about), and an empty `hide` list
- [x] 2.4 Update the comments at the top of `profile.yml` to describe the new sections and the private-name rule

## 3. Renderer

- [x] 3.1 Replace `update_readme()` with `replace_region(text, name, block)` that raises `RenderError` naming the missing marker, and use it for `featured`
- [x] 3.2 In `gather()`, build private card candidates from `projects.private` entries that have `card`, merging `title` and `version`; keep the rotation and the allowlist token checks unchanged
- [x] 3.3 In `gather()`, build public table rows per design D3 (curated rows in file order, then the API fallback newest-first, skipping forks, hidden repos and the profile repo)
- [x] 3.4 Add `hero_block(cfg)` and `stack_block(cfg)` that emit the `<p align="center">` image markup with alt text per D4
- [x] 3.5 Add `projects_block(data)` that emits the `<a name="all-projects">` anchor, `<details>` with computed counts, the private list and the public table, with escaping per D6
- [x] 3.6 Add the leak check from D5 on the final README string, with an error message that does not include the repo value
- [x] 3.7 Wire the new regions into `main()` so all of them are rendered before anything is written

## 4. README and docs

- [x] 4.1 Add `hero`, `projects` and `stack` marker pairs around the existing blocks in `README.md`
- [x] 4.2 Update `CLAUDE.md` Layout and Rules so they list every generated region, not just the featured block

## 5. Verification

- [x] 5.1 Render locally and review the README diff: only the Swing-Trade Research copy fix and any intended alt or table text changes
- [x] 5.2 Tagline edit: the hero SVG and the hero alt text both change; revert it
- [x] 5.3 Delete one end marker: the run fails naming it and writes nothing; restore it
- [x] 5.4 Put a private `card.repo` value into a summary: the run fails without printing the value; revert it
- [x] 5.5 Hide a public repo, and remove one `repos` entry: the counts and rows update, and the uncurated repo shows its API language and description; revert both *(run offline with a stubbed API: the live API returned 403 for unauthenticated calls)*
- [ ] 5.6 Run with an unchanged config twice: the second run writes nothing *(blocked locally by the unauthenticated rate limit; check it in Actions, see 5.7)*
- [ ] 5.7 Push on a branch, run the workflow, and review the profile in desktop light and dark and on mobile before merging
