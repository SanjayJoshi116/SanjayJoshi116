## ADDED Requirements

### Requirement: Accurate All projects counts
The All projects summary SHALL show the number of private and public projects listed inside it, and the numbers MUST equal the entries actually listed.

#### Scenario: Count matches list
- **WHEN** a visitor expands All projects
- **THEN** the number of private entries and public table rows equal the counts shown in the summary line

#### Scenario: Forks and profile repo not counted
- **WHEN** the owner has forked public repositories and the profile repository
- **THEN** none of them are listed or counted

### Requirement: Alt text matches the images
The hero and stack images SHALL have alt text that states the same name, roles, tagline lines and tools that the images show.

#### Scenario: Screen reader on the hero
- **WHEN** a screen reader announces the hero image
- **THEN** it reads the name, roles and every tagline line currently in the hero SVG

