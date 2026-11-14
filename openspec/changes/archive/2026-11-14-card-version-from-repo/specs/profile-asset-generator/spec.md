## MODIFIED Requirements

### Requirement: Least-privilege token
API access beyond public data SHALL use a fine-grained, read-only token stored as a repository secret, scoped to the allowlisted repositories with Metadata: read and Contents: read and no other permission. Contents access SHALL be used only to read each card repository's version file; file contents MUST NOT be written to any output or log, except the validated version label. The token MUST NOT appear in logs or generated files. The pulse strip SHALL be built from repository metadata (`pushed_at`) only.

#### Scenario: Missing token
- **WHEN** the secret is absent or invalid
- **THEN** the run fails without overwriting existing assets and reports the error

#### Scenario: Metadata-only pulse
- **WHEN** the token has Metadata: read and no other permission on the allowlisted repositories, and every private card sets `version_from: manual`
- **THEN** the run succeeds and renders the pulse strip, with the versions from `data/profile.yml`

#### Scenario: Contents permission missing
- **WHEN** the token lacks Contents: read on a card repository whose version is read from the repository
- **THEN** the run fails naming the card by its number and the missing permission, without naming the repository, and writes nothing

### Requirement: Private project defined once
Each private project's title SHALL be defined once in `data/profile.yml`, and each private project SHALL have one version label that is used by its featured card (if featured), the pulse strip, its All projects entry and every place the landing page shows it. For a private project with a card, the label SHALL come from its repository when a token is available, unless the card sets `version_from: manual`; otherwise it SHALL be the `version` in `data/profile.yml`.

#### Scenario: Title edit
- **WHEN** the owner renames a featured private project in `data/profile.yml`
- **THEN** the card SVG, the card's alt text and the All projects entry all show the new title

#### Scenario: Version bump in the repository
- **WHEN** a card repository's version file changes from 0.41.0 to 0.58.0 on its default branch and the next render runs with a token
- **THEN** the featured card, pulse strip, All projects entry and landing page all show v0.58, while `data/profile.yml` still says v0.41

#### Scenario: Project without a card
- **WHEN** a private project has no card
- **THEN** its All projects entry shows the `version` from `data/profile.yml`

## ADDED Requirements

### Requirement: Card versions read from the repository
For each private card project, when a token is available, the card names a repository (`card.repo`) and does not set `version_from: manual`, the generator SHALL read the version from the repository's default branch: from the file named by `card.version_from` if set, otherwise from the first of `VERSION`, `pyproject.toml` and `package.json` that exists. It SHALL take the version from the whole text of a plain file such as `VERSION`, from `[project].version`, `[tool.poetry].version` or `[package].version` in any `.toml` file, and from the top-level `version` in any `.json` file. Files SHALL be read as UTF-8 (a byte-order mark is ignored) or as UTF-16 when they start with a UTF-16 byte-order mark. The value MUST match a dotted numeric version (`<major>.<minor>` with an optional leading `v`, optional further parts and suffix) and SHALL be shown as `v<major>.<minor>`. `version_from: manual` is matched without regard to case. If the repository itself can't be read with the token, the run SHALL fail saying so, before any file is requested. If no file is found, the file can't be decoded or parsed, the value is invalid, or the request fails, the run SHALL fail and write nothing; a refused request (HTTP 403) SHALL be reported as a missing Contents permission or a rate limit. The error SHALL identify the card by its position in `data/profile.yml` and MUST NOT print the repository name or any file content. Without a token the `version` in `data/profile.yml` SHALL be used and no repository file is read. A `version_from` that is not a repository path or `manual`, or one placed on the project instead of under its `card`, SHALL fail every run, with or without a token. Private project titles MUST be unique.

#### Scenario: Auto-detected file
- **WHEN** a card repository has no `VERSION` file and its `pyproject.toml` has `[project]` `version = "0.58.0"`
- **THEN** the card's version label is v0.58

#### Scenario: Explicit file
- **WHEN** a card sets `version_from: frontend/package.json` and that file's `version` is `1.24.0`
- **THEN** the label is v1.24, and no other file is read for that card

#### Scenario: No version file
- **WHEN** none of `VERSION`, `pyproject.toml` and `package.json` exists in a card repository and the card has no `version_from`
- **THEN** the run fails naming the card number, suggesting `version_from`, and writes nothing

#### Scenario: Invalid value
- **WHEN** the version file holds `latest` or any value that is not a dotted numeric version
- **THEN** the run fails naming the card number, without printing the value, and writes nothing

#### Scenario: Local run without a token
- **WHEN** the generator runs without a token
- **THEN** every card uses its `version` from `data/profile.yml` and no repository file is requested

#### Scenario: Leading v and encodings
- **WHEN** a card repository's `VERSION` file holds `v0.12.63`, saved as UTF-16 with a byte-order mark
- **THEN** the label is v0.12

#### Scenario: Repository outside the token's scope
- **WHEN** a card repository is not among the token's repositories
- **THEN** the run fails saying that card number is not readable with the token, not that its version file is missing

#### Scenario: Misplaced version_from
- **WHEN** `version_from` is written on the private project instead of under its `card`, and the run has no token
- **THEN** the run fails naming the card number and writes nothing
