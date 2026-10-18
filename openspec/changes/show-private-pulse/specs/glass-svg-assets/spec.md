## MODIFIED Requirements

### Requirement: Required asset set
The repository SHALL contain these assets: `hero.svg`, one card per featured project, `pulse.svg`, `stack.svg`, `stats.svg`, `langs.svg`, and one `connect-*.svg` button per entry in the `connect` list.

#### Scenario: README references resolve
- **WHEN** every relative `assets/` path in the README is checked
- **THEN** each one points to an existing file

## ADDED Requirements

### Requirement: Private pulse strip
`pulse.svg` SHALL be a static flat dark card with one row per private project that has a `card.repo`, ordered by most recent push first. Each row SHALL show the project title, its version label and a relative age of its last push ("active today", "active 3d ago", "active 2w ago", "active 4mo ago"). A recency dot SHALL show freshness: Leaf when the last push is at most 7 days old, Cyan when at most 30 days, muted text colour otherwise. The card SHALL carry the amber private edge. It MUST NOT contain any repository name, URL, commit count or other repository content.

#### Scenario: Fresh and stale projects
- **WHEN** SwingTrade AI was last pushed 2 days ago and FitTrack 45 days ago
- **THEN** SwingTrade AI is listed first with a Leaf dot and "active 2d ago", and FitTrack shows a muted dot and "active 6w ago"

#### Scenario: No repo name in the strip
- **WHEN** `pulse.svg` is inspected
- **THEN** it contains project titles and ages only, and no `owner/name` value from `data/profile.yml`

### Requirement: Pulse alt text states the ages
The pulse image's alt text SHALL list each row's title and relative age in the same order as the strip.

#### Scenario: Screen reader on the pulse strip
- **WHEN** a screen reader reaches the pulse image
- **THEN** it announces e.g. "Private work, last active: SwingTrade AI 2 days ago, Expense Tracker 3 weeks ago"
