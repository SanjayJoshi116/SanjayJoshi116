# glass-svg-assets Specification

## Purpose

Self-hosted SVG images (hero, project cards, stack grid, stats) in the "Aurora on Ink" flat dark card style, so the profile renders consistently under GitHub's HTML sanitizer without third-party image hosts.

## Requirements

### Requirement: Self-contained SVG files
Every visual asset SHALL be an SVG file in `assets/` that loads no external resources: no remote fonts, images, or scripts. Any font or icon data MUST be inlined.

#### Scenario: Offline render
- **WHEN** an asset SVG is opened in a browser with network access blocked
- **THEN** it renders completely, with no missing glyphs or images

#### Scenario: No script
- **WHEN** an asset SVG is inspected
- **THEN** it contains no `<script>` elements, no event-handler attributes, and no `<foreignObject>`

### Requirement: Required asset set
The repository SHALL contain these assets: `hero.svg`, one card per featured project, `pulse.svg`, `stack.svg`, `stats.svg`, `langs.svg`, and one `connect-*.svg` button per entry in the `connect` list.

#### Scenario: README references resolve
- **WHEN** every relative `assets/` path in the README is checked
- **THEN** each one points to an existing file

### Requirement: Aurora on Ink palette
Assets SHALL use the palette Ink `#0F1424` (card surface), Signal Blue `#58A6FF`, Leaf `#34D399`, Violet `#8B5CF6` and Cyan `#22D3EE` (accents; Violet is never used for text), Amber `#F5B544` (reserved for private work), and text `#F0F6FC` / `#9DA7B3`.

#### Scenario: Private cards marked with amber
- **WHEN** a private project card renders
- **THEN** it has an amber edge glow, and public cards do not use amber

### Requirement: Flat card surface
Each asset SHALL be a flat dark card: a solid Ink surface clipped to a rounded rectangle, a gradient accent line along the top edge, and a thin translucent white border. Assets MUST NOT use blurred background blobs or CSS `backdrop-filter`.

#### Scenario: Cross-browser appearance
- **WHEN** a card is viewed via `<img>` in Chrome, Firefox, and Safari
- **THEN** the card appearance is visually equivalent in all three

### Requirement: Motion limited to the hero
Only `hero.svg` SHALL animate: its contribution line draws in once on load, then the area and end marker fade in. All other assets MUST be static. Each animated asset SHALL honour `prefers-reduced-motion: reduce` by stopping its animation. The base styles SHALL be the final frame, so a renderer that skips animation shows the complete chart.

#### Scenario: Reduced motion
- **WHEN** the viewer's OS has reduced motion enabled
- **THEN** the hero shows a static, complete frame

#### Scenario: First frame complete
- **WHEN** a renderer shows the hero without running its animation (e.g. the GitHub mobile app)
- **THEN** the name, the intro and the full contribution chart are visible
### Requirement: Accessible image text
Every asset `<img>` in the README SHALL have descriptive `alt` text that conveys its content, such as the project name and one-line description for cards, or the tool list for the stack grid.

#### Scenario: Screen reader
- **WHEN** a screen reader reaches a featured card
- **THEN** it announces the project name and its one-line summary

### Requirement: Readable on light and dark GitHub themes
Assets SHALL be dark panels with their own background, legible on both GitHub's light and dark themes. Text contrast against the panel MUST meet WCAG AA (4.5:1 for body text).

#### Scenario: Light theme
- **WHEN** the profile is viewed with GitHub's light theme
- **THEN** each asset appears as an intentional dark panel with no transparent edges bleeding into the page

### Requirement: Stats without streak
`stats.svg` SHALL show aggregate contribution figures (total commits, PRs, stars earned, public repos) and MUST NOT show a contribution streak.

#### Scenario: Stats content
- **WHEN** `stats.svg` renders
- **THEN** it shows the aggregate figures and no current or longest streak

### Requirement: Activity alt text states the figures
The stats image's alt text SHALL state each figure shown on the card with its label, and the languages image's alt text SHALL list each language shown with its percentage share.

#### Scenario: Screen reader on stats
- **WHEN** a screen reader reaches the stats image
- **THEN** it announces the same numbers the card shows, e.g. "564 contributions in the past year, 398 public commits, 7 pull requests, 12 stars earned, 8 public repos"

#### Scenario: Screen reader on languages
- **WHEN** a screen reader reaches the languages image
- **THEN** it announces each shown language with the same percentage the card shows

### Requirement: Hero contribution chart
The hero SHALL show the owner's name and the `intro` from `data/profile.yml` on the left, and on the right the past year's contributions summed per week, drawn as a line with its total, its weekly peak, and start and end labels. The figures SHALL come from the same daily counts the run reads.

#### Scenario: Chart matches the calendar
- **WHEN** the contribution calendar sums to 592 with a busiest week of 36
- **THEN** the hero reads "592 contributions in the past year" and "peak 36 a week"

### Requirement: Sentence-case labels
Card and section labels inside the assets SHALL be sentence case with no letter-spacing (e.g. "Public repo", "Private, in development", "Data & ML").

#### Scenario: Card labels
- **WHEN** a card or section label renders in an asset
- **THEN** it is sentence case with no letter-spacing, e.g. "Public repo" rather than "PUBLIC REPO"

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

### Requirement: Pipeline diagram asset
`pipeline.svg` SHALL be a static flat dark card showing the diagram stages from `data/profile.yml` as boxes in one left-to-right row, joined by arrows, in file order. Each box SHALL show the stage title in body text colour and its detail line in muted text colour. Boxes and arrows SHALL use the Aurora on Ink accents (never Amber for boxes or arrows, never Violet for text), and the card SHALL carry the amber private edge because it describes private work. It MUST NOT contain any repository name, URL, threshold or other value not written in the stage copy.

#### Scenario: Five stages
- **WHEN** the diagram has 5 stages
- **THEN** `pipeline.svg` shows 5 boxes in one row with 4 arrows between them, in the order listed

#### Scenario: Readable on both themes
- **WHEN** the diagram is viewed on GitHub's light and dark themes
- **THEN** it appears as a dark panel and every text colour meets 4.5:1 contrast against the card surface
