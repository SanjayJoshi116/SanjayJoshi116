## ADDED Requirements

### Requirement: Repo count matches the public table
The "public repos" figure on the stats card SHALL count exactly the repositories listed in the All projects public table: public, non-fork, not the profile repository, and not hidden.

#### Scenario: Profile repo and hidden repos excluded
- **WHEN** the owner has 13 public repositories, of which 2 are forks, 1 is the profile repository and 2 are hidden
- **THEN** the stats card shows 8 public repos and the All projects summary shows 8 public

### Requirement: Generated Activity and Connect regions
The generator SHALL regenerate the README's Activity region (stats and languages images with their alt text) and Connect region (one button per entry in the `connect` list of `data/profile.yml`). The same marker and failure rules as the other generated regions SHALL apply.

#### Scenario: Connect link edit
- **WHEN** the owner changes the YouTube URL in `data/profile.yml` and the generator runs
- **THEN** the YouTube button links to the new URL, with no hand edit to the README

#### Scenario: Missing marker
- **WHEN** the `connect` end marker is missing from the README
- **THEN** the run fails naming the marker and writes nothing

## MODIFIED Requirements

### Requirement: Single data source
All human-authored profile content used by the assets (the intro, featured allowlists, private card copy and version labels, the stack and the connect list) SHALL come from `data/profile.yml`.

#### Scenario: Intro edit
- **WHEN** the owner edits `intro` in `data/profile.yml` and pushes
- **THEN** the regenerated `hero.svg` and the hero alt text show the new intro, with no manual edit

### Requirement: Languages follow the public table
Language totals SHALL skip hidden repos, so the languages card reflects the repos the README lists plus allowlisted private repos.

#### Scenario: Hidden repo's language drops out
- **WHEN** a PHP-only repo is in `projects.public.hide`
- **THEN** its PHP bytes are not counted on the languages card
