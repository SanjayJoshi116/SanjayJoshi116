## Why

The renderer only generates the README's featured block. The hero alt text, stack alt text, the All projects list and its "(N private · N public)" count are hand-written copies of data that lives in `data/profile.yml` or comes from the GitHub API. The copies have already drifted: the private card says "Swing-Trade Research … cost-aware LightGBM" while the list says "Swing-Trade Research Platform … turnover-aware LightGBM". Any tagline or stack edit leaves stale alt text for screen readers, and any new public repo makes the count wrong.

## What Changes

- `data/profile.yml` gains a `projects` section that holds every private project once (title, version, list summary, stack, optional collaborator, optional card copy). Private featured cards are drawn from the entries that have card copy, so a private project's title and version live in exactly one place.
- `data/profile.yml` gains per-repo copy for the public table (label, stack, one-line description) and a `hide` list. Public repos that have no entry still appear, using the API's language and description, so a new repo never breaks the daily run.
- The renderer generates three more README regions between markers: the hero image (alt from name, roles and tagline), the All projects `<details>` block (private list, public table, computed counts), and the stack image (alt from `stack`).
- Private projects are written to the README by title and copy only. The renderer fails if a private `repo` value would appear in any generated output.
- **BREAKING** (data file only): `featured.private` moves into `projects.private`. The README and assets look the same after migration, apart from the corrected copy.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `profile-asset-generator`: the generator also owns the README hero, All projects and stack regions, and must keep private repo names out of them.
- `profile-readme-layout`: the All projects counts and contents, plus the hero and stack alt text, are derived from data rather than hand-written.

## Impact

- `scripts/render_profile.py`: new README region renderers, a generic marker replace, and a leak check for private repo values. Still all-or-nothing.
- `data/profile.yml`: new `projects` section; `featured.private` migrated into it.
- `README.md`: three new marker pairs; content between them becomes generated.
- `CLAUDE.md`: the "never edit by hand" rule extends to the new regions.
- No workflow, dependency or token-scope change. The public repo list is already fetched without auth.
