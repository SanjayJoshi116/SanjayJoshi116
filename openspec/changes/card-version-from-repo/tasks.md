## 1. Token

- [x] 1.1 Edit the `PROFILE_TOKEN` fine-grained token (GitHub → Settings → Developer settings): add Contents: Read-only on the same allowlisted card repositories, nothing else; keep Metadata: read

## 2. Reading versions

- [x] 2.1 Add `GitHub.raw(path)`: contents API with the raw media type; text on 200, `None` on 404, a "can't read file contents" error on 403, the usual error otherwise
- [x] 2.2 Add version parsing for `VERSION`, `pyproject.toml` (`[project]`, then `[tool.poetry]`) and `package.json`, the version pattern check and the `v<major>.<minor>` label; never include the value in an error
- [x] 2.3 In `gather()`'s per-card loop, resolve each card's version: `version_from: manual` → profile.yml; `version_from: <path>` → that file only; otherwise the first existing of `VERSION`, `pyproject.toml`, `package.json`; errors name the card by number only
- [x] 2.4 Apply the resolved labels once: card entries (and so pulse rows) and copies in `data["private_all"]`; no token → profile.yml versions, no file requests

## 3. Config and docs

- [x] 3.1 `data/profile.yml`: document `card.version_from` (path or `manual`) and that `version` is the no-token / manual fallback; add `version_from` only where auto-detection would pick the wrong file
- [x] 3.2 `CLAUDE.md`: token rule (Metadata + Contents read on card repos), the version source and `version_from`

## 4. Verification

- [x] 4.1 Harness with stubbed contents responses: auto-detect order, explicit path, `manual`, missing file, 403, invalid value (not printed), no token (no requests); README, pulse and site show the same label
- [x] 4.2 Check that no error message or log line contains a repo name or file content, including for the 403 and invalid-value cases
- [ ] 4.3 Branch dispatch with the updated token: cards, pulse strip, All projects and `site-preview` show the repos' versions; then merge
