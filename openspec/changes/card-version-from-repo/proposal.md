## Why

The version shown for each private project (README featured cards, pulse strip, All projects list, and the landing page's cards, Now rows and case pages) is typed by hand in `data/profile.yml`, so it falls behind. On 14 Nov 2026 the profile showed SwingTrade AI v0.41 and Expense Tracker v1.7 while the projects were at 0.58.0 and 1.24.0. Every other number on the profile updates itself; the version is the one that silently goes stale.

## What Changes

- With a token, each private card project's version is read from its repository's default branch: an explicit `card.version_from` path, or the first of `VERSION`, `pyproject.toml` and `package.json` that exists. It is shown as `v<major>.<minor>`, as today.
- The read version replaces the hand-typed one everywhere it appears: featured card, pulse strip, All projects entry, and every place on the landing page. Without a token (local runs) the `version` in `data/profile.yml` is used, as today.
- A card can opt out with `version_from: manual`, which keeps its `profile.yml` version even with a token.
- A version that can't be read with a token fails the render (all-or-nothing, nothing written) instead of falling back silently, so drift can't return unnoticed. The error names the card by number, never the repository, and never prints file contents.
- **BREAKING (configuration):** the `PROFILE_TOKEN` secret needs **Contents: read** on the allowlisted card repositories, on top of Metadata: read. Nothing else changes in its scope. Until it's granted, every card must use `version_from: manual` or CI renders fail.
- Projects without a card keep their hand-typed version (they have no repository to read).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `profile-asset-generator`: the token's least-privilege scope gains Contents: read on allowlisted card repositories; the private project's version label is read from its repository when a token is available; a new requirement covers reading, parsing, validating and failing on card versions.

## Impact

- `scripts/render_profile.py`: version reading per card repo in `gather()` (contents API, file detection, parsing with `tomllib`/`json`), validation and formatting, and applying the version to the card, pulse and All projects entries.
- `data/profile.yml`: optional `card.version_from`; `version` stays as the no-token fallback (comment updated).
- GitHub: `PROFILE_TOKEN` fine-grained token edited to add Contents: read on the same repositories (manual, one-time).
- `CLAUDE.md`: token rule and `profile.yml` notes.
- No workflow change. A version bump is a push, so the existing push-time fingerprint already triggers the render. About 1–3 extra API calls per card per render, under the token's limit.
- The landing page needs no change: it shows the same data.
