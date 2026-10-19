## ADDED Requirements

### Requirement: Pipeline diagram asset
`pipeline.svg` SHALL be a static flat dark card showing the diagram stages from `data/profile.yml` as boxes in one left-to-right row, joined by arrows, in file order. Each box SHALL show the stage title in body text colour and its detail line in muted text colour. Boxes and arrows SHALL use the Aurora on Ink accents (never Amber for boxes or arrows, never Violet for text), and the card SHALL carry the amber private edge because it describes private work. It MUST NOT contain any repository name, URL, threshold or other value not written in the stage copy.

#### Scenario: Five stages
- **WHEN** the diagram has 5 stages
- **THEN** `pipeline.svg` shows 5 boxes in one row with 4 arrows between them, in the order listed

#### Scenario: Readable on both themes
- **WHEN** the diagram is viewed on GitHub's light and dark themes
- **THEN** it appears as a dark panel and every text colour meets 4.5:1 contrast against the card surface
