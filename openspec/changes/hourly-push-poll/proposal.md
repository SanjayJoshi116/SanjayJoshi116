## Why

The profile only re-renders once a day (07:47 IST), so a push to a featured or pulse-tracked repo can take up to 24 hours to show. Push-triggered updates from each source repo would need a write-capable token stored in every watched repo; polling from the profile repo gets close enough with the existing read-only token and nothing added to the source repos.

## What Changes

- The render workflow polls hourly at :17 IST from 06:17 to 23:17 IST (cron `47 0-17 * * *` UTC). Nothing runs 23:18–06:16 IST.
- Each poll first computes a fingerprint of last-push times for the owner's public repos and the private card repos (`projects.private[].card.repo`), using the existing `PROFILE_TOKEN`. If the fingerprint equals the one saved by the last successful render, the run stops without rendering.
- The daily run (`17 2 * * *`, 07:47 IST), `workflow_dispatch` and the existing `push` trigger always render, ignoring the fingerprint. The daily run keeps the contribution chart and pulse age buckets current.
- The fingerprint is never printed. Logs show only whether it changed, so no private repo name or push time reaches the public Actions logs.
- The fingerprint is saved only after a successful render, so a failed render is retried on the next poll.
- `CLAUDE.md` workflow description updated.
- No `repository_dispatch`, no new token, no change in any source repo. Renderer stays all-or-nothing; commits stay only-on-diff.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `profile-asset-generator`: "Scheduled and push-triggered regeneration" gains the hourly daytime poll with a change gate, and a requirement that the gate leaks nothing to logs.

## Impact

- `.github/workflows/render-profile.yml`: second cron, fingerprint step, cache restore/save, conditional render.
- `scripts/render_profile.py`: new `--fingerprint` mode that reuses the existing GitHub client and writes the digest to a file.
- `CLAUDE.md`: workflow line.
- Actions usage: up to 18 extra short runs a day on a public repo (free). API: about 2 + N private card calls per poll, well under the token's rate limit.
