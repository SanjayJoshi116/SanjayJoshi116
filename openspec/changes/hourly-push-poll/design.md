## Context

`render-profile.yml` runs once a day, on pushes to `main` that touch `data/profile.yml` or the renderer, and on `workflow_dispatch`. A render makes several API calls (including the contribution GraphQL query) and commits only when output differs. Repos are public, so Actions logs are public. `PROFILE_TOKEN` is read-only metadata on the allowlisted repos. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- Pushes to watched repos appear on the profile within about an hour during 06:00–23:00 IST.
- Polls that find nothing cost a few API calls and no render.

**Non-Goals:**
- Real-time updates (`repository_dispatch`, webhooks, GitHub App).
- Re-rendering for contribution-count changes in unwatched repos between daily runs.
- Changing what the renderer outputs.

## Decisions

### Cron in UTC, two lines
`47 0-17 * * *` = :17 IST, 06:17–23:17. `17 2 * * *` keeps the daily 07:47 IST run. The steps tell them apart with `github.event.schedule == '17 2 * * *'`. IST has no DST, so the window never shifts. Polls at :17 IST place the last run after the 23:00 cutoff.

Alternative: one hourly cron with a forced render at a chosen hour. Rejected: two lines say the intent directly.

### Fingerprint mode in the renderer
`render_profile.py --fingerprint PATH` loads `profile.yml`, uses the existing `GitHub` client, and writes a SHA-256 hex digest to `PATH`. It prints nothing and exits 0. Input, sorted:
- `(name, pushed_at)` for each non-fork repo from the unauthenticated `/users/{user}/repos` call `gather` already makes. That includes repos not yet in `profile.yml`, so a new public repo triggers a render.
- `pushed_at` for each `projects.private[].card.repo`, via `/repos/{repo}` with the token. These are the same calls `gather` already makes.

Any error writes the digest `error`. That never matches a saved digest, so the render runs and reports failures with its own existing messages.

Alternatives:
- Separate script: rejected because it would duplicate the client and config loading.
- One GraphQL query with aliases: rejected because GraphQL errors can echo repo names, and REST matches calls already proven with this token.
- Hashing the whole `gather()` output: rejected because it costs as much as a full render.

### State in `actions/cache`
`actions/cache/restore` with `restore-keys: push-fp-` restores the newest saved digest to `.push-fp/last`. After a successful render and commit, `actions/cache/save` writes key `push-fp-${{ github.run_id }}`. Saving only after success gives the retry-on-failure behavior. An `error` digest is never saved, and the gate always treats it as changed. A cache miss (evicted after 7 days unused, or first run) counts as changed.

Alternative: commit the digest to the repo. Rejected because it adds a commit on every change and puts a value derived from private push times in public git history.

### Gate step
Bash compares `.push-fp/now` with `.push-fp/last` and sets `outputs.render`. It is true when the run is not an hourly poll, or the files differ, or `last` is missing. It echoes only `changed`/`unchanged`. The render, commit and cache-save steps run on `if: steps.gate.outputs.render == 'true'`. `.push-fp/` is in `.gitignore` and outside `git add assets README.md`, so it is never committed.

### Fingerprint on every trigger
Every run computes the fingerprint so that daily, manual and push renders also save fresh state. Otherwise the next hourly poll would re-render what was just rendered.

## Risks / Trade-offs

- **Cron starts late (often 5–15 min):** harmless, because each poll compares current state rather than a time window.
- **Rendered output is not committed by the run that saved the fingerprint, then a push races in:** the commit loop already rebases. The next poll sees any later push time.
- **The cache is readable by any workflow in the repo:** it holds only a digest. It is not logged, and recovering names from it would require guessing both names and exact timestamps.
- **Concurrency:** the `render-profile` group serializes runs and keeps one pending. Bursts collapse, which is fine.
- **Scheduled workflows are disabled after 60 days without repo activity:** bot commits from daily renders keep the repo active, the same as today.
- **Pulse buckets and contributions change between daily runs without a push:** accepted. A daily refresh is enough for those.

## Migration Plan

Merge to `main` after a `workflow_dispatch` run on the branch. Watch the first few hourly runs: the first is a cache miss and renders, later ones should report `unchanged`. To roll back, remove the hourly cron line. The gate then always renders, the same as today.
