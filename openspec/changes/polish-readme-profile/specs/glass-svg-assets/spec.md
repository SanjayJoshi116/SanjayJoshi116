## ADDED Requirements

### Requirement: Activity alt text states the figures
The stats image's alt text SHALL state each figure shown on the card with its label, and the languages image's alt text SHALL list each language shown with its percentage share.

#### Scenario: Screen reader on stats
- **WHEN** a screen reader reaches the stats image
- **THEN** it announces the same numbers the card shows, e.g. "564 contributions in the past year, 398 public commits, 7 pull requests, 12 stars earned, 8 public repos"

#### Scenario: Screen reader on languages
- **WHEN** a screen reader reaches the languages image
- **THEN** it announces each shown language with the same percentage the card shows
