## Context

`gather()` already calls `GET /repos/{repo}` for each private card repo when a token is set (for `pushed_at`, rotation and the pulse strip), and collects `private_repos` for the leak checks. The version label comes from `projects.private[].version` and reaches three places through different paths: the card entries (`private_cfg`, copied from the project), the pulse rows (copied from those entries), and the All projects list (`data["private_all"]`, which is the raw `cfg` list). The landing page reads the same `data`. `PROFILE_TOKEN` is fine-grained with Metadata: read on the card repos. Motivation: see proposal.md. Requirements: see `specs/profile-asset-generator/spec.md`.

## Goals / Non-Goals

**Goals:**
- One resolved version per private project, applied once in `gather()` so every output shows the same label.
- Read as little as possible: at most three small files per card, from the default branch, never logged.
- Keep all-or-nothing behaviour and the no-names-in-errors rule.

**Non-Goals:**
- Versions for projects without a card or a repository (they stay hand-typed).
- Git tags or GitHub releases as a source. The repos record versions in files and changelogs, not consistently in tags, and tags would need the same Contents permission anyway.
- Showing patch versions. The label stays `v<major>.<minor>`.

## Decisions

**D1. Contents API, raw media type.** `GET /repos/{repo}/contents/{path}` with `Accept: application/vnd.github.raw` returns the file body on the default branch with no base64 step. A new `GitHub.raw(path)` returns the text, or `None` on 404 (file missing), and raises on anything else. A 403 is reported as a missing Contents permission.
*Alternative:* the Git trees API to list files first. Rejected: one extra call per card, and the same permission.

**D2. Fixed detection order with an explicit override.** `card.version_from` names one file. Otherwise the order is `VERSION` → `pyproject.toml` → `package.json`, and the first file that exists decides, even if it has no usable version (it then fails rather than skipping on). The order puts the Python projects' own version ahead of a root `package.json` that may only hold tooling (one card repo has `pyproject.toml` 0.58.0 next to a root `package.json` 0.1.0). `version_from: manual` skips reading entirely.
*Alternative:* try every file and take the highest version. Rejected: it hides a wrong file instead of surfacing it.

**D3. Parsing with the standard library.** Bytes are decoded as UTF-16 when they start with a UTF-16 BOM (PowerShell 5.1 writes these), otherwise as `utf-8-sig`. Any `.toml`: `tomllib` (imported lazily, so other modes don't need 3.11), `[project].version`, then `[tool.poetry].version`, then `[package].version` (Cargo). Any `.json`: top-level `version`. Anything else (`VERSION`): the stripped text. The value must match `^[vV]?\d+\.\d+(\.\d+)*([-+.][0-9A-Za-z.-]+)?$`; the label is `v` + the first two numbers. A value that fails the pattern is never printed, so neither file content nor a stray name can reach a log. Since a valid label is only digits and dots, it can't carry a private name into any output.

**D4. Resolve once in `gather()`.** One loop over the private projects builds each card's entry and the All projects copy. With a token and a repo, it first checks that the repo is readable (and takes `pushed_at`), then reads the version, so a repo outside the token's scope gets the right error instead of looking like missing files. Titles must be unique, since case pages find a project's version by title. `version_from` is validated on every run (`version_source`), so mistakes fail locally too. It produces `versions = {title: label}`. The card entries get the resolved label, so pulse rows inherit it. `data["private_all"]` becomes a list of copies with `version` replaced where resolved, so the README list, the site and the case pages need no change. Cards are read whenever the card names a repo and a token is set, independent of whether rotation is possible.

**D5. Errors by card number.** Messages read like `private card #2: no version file found (VERSION, pyproject.toml, package.json); set card.version_from` and `private card #2: the token can't read file contents; grant Contents: read or set version_from: manual`. They never include the repo, the path's file content or the value.

**D6. `version` stays required for card projects.** It is the no-token fallback and the `manual` value, and `gather()` already requires it. The comment in `profile.yml` says it is only shown when no token is available or the card is `manual`.

## Risks / Trade-offs

- [Broader token scope: Contents: read exposes source code if the token leaks] → still read-only, still only the allowlisted repos, still a repository secret never logged. The renderer reads at most three named files per repo. This is the user's explicit trade for automatic versions (proposal).
- [Merging before the token is updated turns every render red] → task order: update the token first, verify with a branch dispatch, then merge. Fallback: `version_from: manual` on every card.
- [The default branch lags a release branch] → acceptable: the profile shows what's on the default branch, and that's what pushes update.
- [Local runs without a token show the hand-typed versions] → only CI output is committed, and CI always has the token. The fallback can be stale, which the `profile.yml` comment states.
- [A file exists but holds a placeholder (e.g. `0.0.0` in a frontend `package.json`)] → D2's order and `version_from` cover it, and the branch review shows the label.

## Migration Plan

1. Edit the `PROFILE_TOKEN` fine-grained token: add Contents: Read-only on the same card repositories.
2. Implement on a branch. Dispatch the workflow there and check that the cards, pulse strip, All projects and `site-preview` show the repo versions.
3. Merge. If a render fails on version reading, set `version_from: manual` on the failing card and push. The error names its number.

Rollback: revert the commit; the hand-typed versions in `profile.yml` are used again. The token's extra permission can be removed afterwards.
