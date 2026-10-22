## 1. Renderer fingerprint mode

- [x] 1.1 Add `--fingerprint PATH` to `scripts/render_profile.py`: load config, build the `GitHub` client, collect sorted `(name, pushed_at)` for non-fork repos from the unauthenticated `/users/{user}/repos` call and `pushed_at` for each `projects.private[].card.repo` via the token, write the SHA-256 hex digest to PATH, print nothing, exit 0
- [x] 1.2 On any error in fingerprint mode, write `error` to PATH with no output and exit 0
- [x] 1.3 Run locally with and without a token: confirm a stable digest across two runs, no stdout/stderr, and no README/asset changes

## 2. Workflow

- [x] 2.1 Add cron `47 0-17 * * *` (06:17–23:17 IST) next to `17 2 * * *`, with comments giving the IST times
- [x] 2.2 Add `actions/cache/restore` (path `.push-fp/last`, key `push-fp-${{ github.run_id }}`, restore-keys `push-fp-`) and the fingerprint step writing `.push-fp/now` with `PROFILE_TOKEN`
- [x] 2.3 Add a gate step (`id: gate`) that sets `render=true` unless the event is the hourly schedule and `.push-fp/last` exists and equals `.push-fp/now`, and echoes only `changed` or `unchanged`
- [x] 2.4 Make the render and commit steps conditional on `steps.gate.outputs.render == 'true'`
- [x] 2.5 After a successful commit step, copy `now` to `last` and run `actions/cache/save` with key `push-fp-${{ github.run_id }}`
- [x] 2.6 Add `.push-fp/` to `.gitignore`

## 3. Docs

- [x] 3.1 Update the workflow line in `CLAUDE.md`: hourly 06:17–23:17 IST poll gated by the push-time fingerprint, daily forced render at 07:47 IST, and no names or fingerprint in logs

## 4. Verify

- [ ] 4.1 `workflow_dispatch` on the branch: it renders, saves the cache, and logs contain no repo names, push times or digest
- [ ] 4.2 After merge, check the first hourly runs: the first renders (cache miss) and later ones log `unchanged` and skip the render; a test push to a watched repo renders on the next poll
