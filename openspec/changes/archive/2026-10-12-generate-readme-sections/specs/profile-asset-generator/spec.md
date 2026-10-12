## ADDED Requirements

### Requirement: Generated README regions
The generator SHALL regenerate these README regions from `data/profile.yml` and the public repository list, alongside the featured block: the hero image with its alt text, the All projects section, and the stack image with its alt text. Content outside the marked regions MUST NOT change.

#### Scenario: Tagline edit reaches the alt text
- **WHEN** the owner edits a tagline line in `data/profile.yml` and the generator runs
- **THEN** both `hero.svg` and the hero image's alt text in the README show the new line

#### Scenario: Stack edit reaches the alt text
- **WHEN** the owner adds a tool to a `stack` group and the generator runs
- **THEN** the stack image's alt text lists the new tool under its group

#### Scenario: Hand-written text untouched
- **WHEN** the generator runs
- **THEN** the About and Connect sections are byte-identical to their previous content

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
Generated README content MUST NOT contain any private repository `owner/name` value from `data/profile.yml`. The generator SHALL check the rendered README for these values before writing and fail if any is found.

#### Scenario: Leak check
- **WHEN** a private project's copy contains its own `owner/name` repository value
- **THEN** the run fails without writing, and the error does not print the repository value

### Requirement: Unlisted public repos still appear
A public, non-fork repository other than the profile repository that has no entry in `data/profile.yml` and is not hidden SHALL still be listed in All projects, using its API language and description. A missing entry MUST NOT fail the run.

#### Scenario: New public repo
- **WHEN** the owner creates a new public repository and the daily run fires
- **THEN** the run succeeds and the repository appears in the public table with its GitHub language and description, and the public count includes it

#### Scenario: Hidden repo
- **WHEN** a public repository is listed under `hide`
- **THEN** it is absent from the public table and not counted
