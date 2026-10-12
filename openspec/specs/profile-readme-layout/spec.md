# profile-readme-layout Specification

## Purpose

Defines the structure of the GitHub profile README: section order, which projects are featured versus collapsed, and the trimmed tech stack, so the page reads well on a 10-second skim.

## Requirements

### Requirement: Fixed section order
The README SHALL present sections in this order: hero, About, Featured projects, All projects (collapsed), Stack, Stats, Connect.

#### Scenario: Visitor skims the profile
- **WHEN** a visitor opens the profile page
- **THEN** the hero image appears first, followed by About, Featured projects, a collapsed All projects section, the stack grid, stats, and Connect badges, in that order

### Requirement: About stays as text
The About section SHALL be plain markdown of at most 4 lines and SHALL mention photography as a hobby, including editing in Lightroom.

#### Scenario: About is selectable text
- **WHEN** a visitor selects or searches for text in the About section
- **THEN** the text is selectable and findable, because it is not rendered as an image

#### Scenario: Photography framed as a hobby
- **WHEN** the About section mentions photography
- **THEN** it frames photography as a hobby (e.g. "shoots & edits in Lightroom"), not as a profession

### Requirement: Four featured project cards
The Featured section SHALL show exactly 4 project cards: 2 public projects in the top row and 2 private projects in the bottom row. Forked repositories MUST NOT be featured.

#### Scenario: Initial featured set
- **WHEN** the phase 1 README is published
- **THEN** the public cards are `movie-app-v2` and `movie-dash-v2`, and the private cards are SwingTrade AI and Expense Tracker

#### Scenario: Forks excluded
- **WHEN** a forked repository (e.g. `conjecscore`, `quant_backtesting`) is the most recently pushed public repo
- **THEN** it does not appear as a featured card

### Requirement: Card link targets
A public project card SHALL link to its GitHub repository. A private project card MUST NOT link to its repository; it SHALL link to the All projects section on the same page.

#### Scenario: Visitor clicks a private card
- **WHEN** a visitor clicks a private project card
- **THEN** the page scrolls to the All projects section instead of opening a 404 repository page

#### Scenario: Visitor clicks a public card
- **WHEN** a visitor clicks a public project card
- **THEN** the corresponding public GitHub repository opens

### Requirement: Collapsed All projects section
Every non-featured project SHALL be listed inside a `<details>` element that is collapsed by default. Private projects SHALL appear as one-line entries, and public projects SHALL appear in a table. Paragraph-length descriptions MUST NOT appear above the fold.

#### Scenario: Default collapsed
- **WHEN** a visitor loads the profile
- **THEN** the All projects section is collapsed and expands only when clicked

#### Scenario: No project lost
- **WHEN** the All projects section is expanded
- **THEN** every project from the previous README that is not featured is listed

### Requirement: Trimmed stack of 20 tools
The Stack section SHALL show exactly 20 tools in 4 groups: BUILD (Python, TypeScript, React, Vite, Ant Design, Django, Node.js), DATA & ML (PostgreSQL, Redis, Celery, Pandas, scikit-learn, LightGBM, PyTorch), VISION (YOLO11, OpenCV, Raspberry Pi), and SHIP (Docker, GitHub Actions, Playwright).

#### Scenario: Dropped tools absent
- **WHEN** the Stack section renders
- **THEN** none of the dropped tools (e.g. Java, PHP, Bootstrap, MySQL, Streamlit, Canva) appear in it

### Requirement: No fragile third-party image hosts
The README MUST NOT load images from capsule-render, readme-typing-svg, github-readme-stats, streak-stats, or any other third-party card service. The Connect section SHALL keep the existing shields.io badges, which are the only externally hosted images allowed.

#### Scenario: External image audit
- **WHEN** all `<img src>` URLs in the README are listed
- **THEN** every URL is either a relative path into `assets/` or a `img.shields.io` URL

