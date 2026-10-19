# profile-asset-generator Specification

## Purpose

Automatically regenerates the profile SVG assets from one data file and the GitHub API, so stars, stats, and featured projects stay current without hand edits and without exposing non-allowlisted private repositories.

## Requirements

### Requirement: Single data source
All human-authored profile content used by the assets (the intro, featured allowlists, private card copy and version labels, the stack and the connect list) SHALL come from `data/profile.yml`.

#### Scenario: Intro edit
- **WHEN** the owner edits `intro` in `data/profile.yml` and pushes
- **THEN** the regenerated `hero.svg` and the hero alt text show the new intro, with no manual edit
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
API access beyond public data SHALL use a fine-grained, read-only token stored as a repository secret, scoped to metadata of the allowlisted repositories. The token MUST NOT appear in logs or generated files. The pulse strip SHALL be built from repository metadata (`pushed_at`) only, and MUST NOT require any permission beyond metadata.

#### Scenario: Missing token
- **WHEN** the secret is absent or invalid
- **THEN** the run fails without overwriting existing assets and reports the error

#### Scenario: Metadata-only pulse
- **WHEN** the token has Metadata: read and no other permission on the allowlisted repositories
- **THEN** the run succeeds and renders the pulse strip

### Requirement: Failure leaves existing assets intact
If any API call or render step fails, the workflow SHALL keep the previously committed assets unchanged.

#### Scenario: API outage
- **WHEN** the GitHub API returns errors during a run
- **THEN** no assets are modified or committed, and the run is marked failed

### Requirement: Generated README regions
The generator SHALL regenerate these README regions from `data/profile.yml` and the public repository list, alongside the featured block: the hero image with its alt text, the All projects section, and the stack image with its alt text. Content outside the marked regions MUST NOT change.

#### Scenario: Intro edit reaches the alt text
- **WHEN** the owner edits `intro` in `data/profile.yml` and the generator runs
- **THEN** both `hero.svg` and the hero image's alt text in the README show the new intro

#### Scenario: Stack edit reaches the alt text
- **WHEN** the owner adds a tool to a `stack` group and the generator runs
- **THEN** the stack image's alt text lists the new tool under its group

#### Scenario: Hand-written text untouched
- **WHEN** the generator runs
- **THEN** the About section is byte-identical to its previous content

### Requirement: Missing region markers fail the run
If any generated region's start or end marker is missing from the README, the generator SHALL fail and write nothing.

#### Scenario: Marker deleted
- **WHEN** the All projects end marker has been removed from the README
- **THEN** the run fails with an error naming the missing marker, and no asset or README change is written

### Requirement: Private project defined once
Each private project's title and version label SHALL be defined once in `data/profile.yml` and used by both its featured card (if featured) and its All projects entry.

#### Scenario: Title edit
- **WHEN** the owner renames a featured private project in `data/profile.yml`
- **THEN** the card SVG, the card's alt text and the All projects entry all show the new title

### Requirement: Private repo names never written to the README
Generated README content and `pulse.svg` MUST NOT contain any private repository `owner/name` value from `data/profile.yml`. The generator SHALL check the rendered README and the rendered pulse strip for these values before writing and fail if any is found.

#### Scenario: Leak check
- **WHEN** a private project's copy contains its own `owner/name` repository value
- **THEN** the run fails without writing, and the error does not print the repository value

#### Scenario: Leak check on the pulse strip
- **WHEN** a private project's title contains its own `owner/name` repository value
- **THEN** the run fails before writing `pulse.svg`, and the error does not print the repository value

### Requirement: Unlisted public repos still appear
A public, non-fork repository other than the profile repository that has no entry in `data/profile.yml` (neither under `repos` nor in a group) and is not hidden SHALL still be listed in All projects, using its API language and description. A missing entry MUST NOT fail the run.

#### Scenario: New public repo
- **WHEN** the owner creates a new public repository and the daily run fires
- **THEN** the run succeeds and the repository appears in the public table with its GitHub language and description, and the public count includes it

#### Scenario: Hidden repo
- **WHEN** a public repository is listed under `hide`
- **THEN** it is absent from the public table and not counted

#### Scenario: Grouped repo not repeated
- **WHEN** a public repository is a member of a group
- **THEN** it appears only inside the group's row, not as a separate row

### Requirement: Repo count matches the public table
The "public repos" figure on the stats card SHALL count exactly the repositories listed in the All projects public table, counting each member of a group: public, non-fork, not the profile repository, and not hidden.

#### Scenario: Profile repo and hidden repos excluded
- **WHEN** the owner has 13 public repositories, of which 2 are forks, 1 is the profile repository and 2 are hidden
- **THEN** the stats card shows 8 public repos and the All projects summary shows 8 public

#### Scenario: Grouped repos counted individually
- **WHEN** 5 of the 8 listed public repositories are in one group, so the table has 4 rows
- **THEN** the stats card and the All projects summary both show 8 public

### Requirement: Generated Activity and Connect regions
The generator SHALL regenerate the README's Activity region (stats and languages images with their alt text) and Connect region (one button per entry in the `connect` list of `data/profile.yml`). The same marker and failure rules as the other generated regions SHALL apply.

#### Scenario: Connect link edit
- **WHEN** the owner changes the YouTube URL in `data/profile.yml` and the generator runs
- **THEN** the YouTube button links to the new URL, with no hand edit to the README

#### Scenario: Missing marker
- **WHEN** the `connect` end marker is missing from the README
- **THEN** the run fails naming the marker and writes nothing

### Requirement: Languages follow the public table
Language totals SHALL skip hidden repos, so the languages card reflects the repos the README lists plus allowlisted private repos.

#### Scenario: Hidden repo's language drops out
- **WHEN** a PHP-only repo is in `projects.public.hide`
- **THEN** its PHP bytes are not counted on the languages card

### Requirement: Generated pulse region
The generator SHALL regenerate `pulse.svg` and the README's `pulse` region (the pulse image with its alt text) from the private projects with a `card.repo` and their `pushed_at` values. Relative ages SHALL be computed against the run's current UTC date. The same marker and failure rules as the other generated regions SHALL apply.

#### Scenario: Push moves a project up
- **WHEN** Expense Tracker is pushed and the next run fires
- **THEN** Expense Tracker moves to the top row with "active today"

#### Scenario: Missing pulse marker
- **WHEN** the `pulse` end marker is missing from the README
- **THEN** the run fails naming the marker and writes nothing

### Requirement: Pulse left untouched without a token
When the run has no token, the generator SHALL leave `pulse.svg` and the README's `pulse` region byte-identical to their current content, and render everything else as usual.

#### Scenario: Local run without a token
- **WHEN** the owner runs the generator locally with no `PROFILE_TOKEN`
- **THEN** `pulse.svg` and the `pulse` region are unchanged, and no private project is named in output, logs or errors

### Requirement: Public repo groups
`data/profile.yml` SHALL support `projects.public.groups`, each with a title, a stack, a one-line description and a list of member repositories. Members missing from the API or hidden SHALL be skipped; a group with no remaining members SHALL be omitted. A repository listed both under `repos` and in a group, or in two groups, SHALL fail the run.

#### Scenario: Missing member
- **WHEN** a group member repository has been deleted
- **THEN** the run succeeds and the group row links only the remaining members

#### Scenario: Duplicate entry
- **WHEN** `CricketScore` appears under `repos` and in a group
- **THEN** the run fails naming `CricketScore` and writes nothing

### Requirement: Diagram defined in the data file
A private project in `data/profile.yml` MAY carry a `diagram` with 3 to 6 `stages`, each with a `title` and a `detail`. At most one project SHALL carry a diagram. The generator SHALL fail and write nothing when a diagram has fewer than 3 or more than 6 stages, when a second project carries one, or when a title or detail does not fit its box on the allowed number of lines.

#### Scenario: Stage edit
- **WHEN** the owner changes a stage's detail in `data/profile.yml` and the generator runs
- **THEN** `pipeline.svg` and the diagram alt text show the new detail, with no manual edit

#### Scenario: Too many stages
- **WHEN** a diagram lists 7 stages
- **THEN** the run fails naming the limit and writes nothing

#### Scenario: Text too long
- **WHEN** a stage title does not fit on one line of its box
- **THEN** the run fails naming the stage and writes nothing

### Requirement: Generated diagram region
The generator SHALL regenerate `pipeline.svg` and the README's `diagram` region from the diagram in `data/profile.yml`, with or without a token. The region SHALL be empty when no project carries a diagram, and `pipeline.svg` SHALL then not be written. The same marker and failure rules as the other generated regions SHALL apply.

#### Scenario: Missing diagram marker
- **WHEN** the `diagram` end marker is missing from the README
- **THEN** the run fails naming the marker and writes nothing

#### Scenario: No token
- **WHEN** the generator runs without `PROFILE_TOKEN`
- **THEN** `pipeline.svg` and the `diagram` region are rendered exactly as they would be with a token

### Requirement: Diagram leak check
The generator SHALL check the rendered `pipeline.svg` and the rendered `diagram` region for every private repository `owner/name` value and bare name from `data/profile.yml`, with the same matching rules as the README check, and fail before writing if any is found. The error MUST NOT print the value.

#### Scenario: Bare repo name in a stage
- **WHEN** a stage detail contains a private repository's bare name as a whole word
- **THEN** the run fails before writing, naming `assets/pipeline.svg`, and the error does not print the name
