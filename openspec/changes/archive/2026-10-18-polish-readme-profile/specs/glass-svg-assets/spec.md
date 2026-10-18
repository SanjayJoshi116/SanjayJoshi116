## ADDED Requirements

### Requirement: Activity alt text states the figures
The stats image's alt text SHALL state each figure shown on the card with its label, and the languages image's alt text SHALL list each language shown with its percentage share.

#### Scenario: Screen reader on stats
- **WHEN** a screen reader reaches the stats image
- **THEN** it announces the same numbers the card shows, e.g. "564 contributions in the past year, 398 public commits, 7 pull requests, 12 stars earned, 8 public repos"

#### Scenario: Screen reader on languages
- **WHEN** a screen reader reaches the languages image
- **THEN** it announces each shown language with the same percentage the card shows

## MODIFIED Requirements

### Requirement: Motion limited to the hero
Only `hero.svg` SHALL animate: its contribution line draws in once on load, then the area and end marker fade in. All other assets MUST be static. Each animated asset SHALL honour `prefers-reduced-motion: reduce` by stopping its animation. The base styles SHALL be the final frame, so a renderer that skips animation shows the complete chart.

#### Scenario: Reduced motion
- **WHEN** the viewer's OS has reduced motion enabled
- **THEN** the hero shows a static, complete frame

#### Scenario: First frame complete
- **WHEN** a renderer shows the hero without running its animation (e.g. the GitHub mobile app)
- **THEN** the name, the intro and the full contribution chart are visible

## ADDED Requirements

### Requirement: Hero contribution chart
The hero SHALL show the owner's name and the `intro` from `data/profile.yml` on the left, and on the right the past year's contributions summed per week, drawn as a line with its total, its weekly peak, and start and end labels. The figures SHALL come from the same daily counts the run reads.

#### Scenario: Chart matches the calendar
- **WHEN** the contribution calendar sums to 592 with a busiest week of 36
- **THEN** the hero reads "592 contributions in the past year" and "peak 36 a week"

### Requirement: Sentence-case labels
Card and section labels inside the assets SHALL be sentence case with no letter-spacing (e.g. "Public repo", "Private, in development", "Data & ML").
