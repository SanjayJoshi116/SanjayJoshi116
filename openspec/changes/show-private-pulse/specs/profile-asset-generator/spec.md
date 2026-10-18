## MODIFIED Requirements

### Requirement: Least-privilege token
API access beyond public data SHALL use a fine-grained, read-only token stored as a repository secret, scoped to metadata of the allowlisted repositories. The token MUST NOT appear in logs or generated files. The pulse strip SHALL be built from repository metadata (`pushed_at`) only, and MUST NOT require any permission beyond metadata.

#### Scenario: Missing token
- **WHEN** the secret is absent or invalid
- **THEN** the run fails without overwriting existing assets and reports the error

#### Scenario: Metadata-only pulse
- **WHEN** the token has Metadata: read and no other permission on the allowlisted repositories
- **THEN** the run succeeds and renders the pulse strip

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

## ADDED Requirements

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
