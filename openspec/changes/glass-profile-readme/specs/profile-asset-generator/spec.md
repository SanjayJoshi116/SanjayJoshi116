## Purpose

Automatically regenerates the profile SVG assets from one data file and the GitHub API, so stars, stats, and featured projects stay current without hand edits and without exposing non-allowlisted private repositories.

## ADDED Requirements

### Requirement: Single data source
All human-authored profile content used by the assets (tagline lines, featured allowlists, private card copy and version labels, and the stack) SHALL come from `data/profile.yml`.

#### Scenario: Tagline edit
- **WHEN** the owner edits a tagline line in `data/profile.yml` and pushes
- **THEN** the regenerated `hero.svg` shows the new line, with no manual SVG edit

### Requirement: Scheduled and push-triggered regeneration
A GitHub Actions workflow SHALL regenerate the assets daily and on any push that changes `data/profile.yml` or the asset templates. It SHALL also be manually runnable.

#### Scenario: Daily refresh
- **WHEN** the daily schedule fires
- **THEN** the workflow runs and refreshes stars, stats, and featured selection

### Requirement: Commit only on change
The workflow SHALL commit regenerated assets only when their content differs from what is already committed.

#### Scenario: No-op run
- **WHEN** a run produces assets byte-identical to the committed ones
- **THEN** no commit is created

### Requirement: Allowlist-bounded recency rotation
Featured cards SHALL be the 2 most recently pushed public repositories and the 2 most recently pushed private repositories, chosen only from allowlists in `data/profile.yml`. The generator MUST NOT enumerate or emit names of private repositories outside the allowlist, and forks MUST be excluded.

#### Scenario: Non-allowlisted private repo pushed
- **WHEN** a private repository not on the allowlist is the most recently pushed repo
- **THEN** it is neither featured nor named in any generated asset, log, or commit

#### Scenario: Rotation
- **WHEN** an allowlisted private repo is pushed more recently than one of the currently featured private repos
- **THEN** the next run features it in place of the older one

### Requirement: Private cards carry no repo links
Generated private cards SHALL show copy and a version label from `data/profile.yml` and MUST NOT include the repository URL or any live metrics from it.

#### Scenario: Private card content
- **WHEN** a private card is generated
- **THEN** it contains the curated name, summary, and version label, and no GitHub URL

### Requirement: Least-privilege token
API access beyond public data SHALL use a fine-grained, read-only token stored as a repository secret, scoped to metadata of the allowlisted repositories. The token MUST NOT appear in logs or generated files.

#### Scenario: Missing token
- **WHEN** the secret is absent or invalid
- **THEN** the run fails without overwriting existing assets and reports the error

### Requirement: Failure leaves existing assets intact
If any API call or render step fails, the workflow SHALL keep the previously committed assets unchanged.

#### Scenario: API outage
- **WHEN** the GitHub API returns errors during a run
- **THEN** no assets are modified or committed, and the run is marked failed
