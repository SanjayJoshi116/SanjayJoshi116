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
The repository SHALL contain these assets: `hero.svg`, one card per featured project, `stack.svg`, `stats.svg`, and `langs.svg`.

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
Only `hero.svg` SHALL animate, with a typing tagline. All other assets MUST be static. Each animated asset SHALL honour `prefers-reduced-motion: reduce` by stopping its animation.

#### Scenario: Reduced motion
- **WHEN** the viewer's OS has reduced motion enabled
- **THEN** the hero shows a static, complete frame

#### Scenario: First frame complete
- **WHEN** a renderer shows only the first frame of the hero (e.g. the GitHub mobile app)
- **THEN** the name and at least one full tagline line are visible and legible

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
