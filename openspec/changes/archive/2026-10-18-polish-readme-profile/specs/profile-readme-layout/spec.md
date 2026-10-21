## MODIFIED Requirements

### Requirement: No fragile third-party image hosts
The README MUST NOT load images from capsule-render, readme-typing-svg, github-readme-stats, streak-stats, shields.io, or any other third-party host. Every image, including the Connect buttons, SHALL come from `assets/`.

#### Scenario: External image audit
- **WHEN** all `<img src>` URLs and markdown image URLs in the README are listed
- **THEN** every URL is a relative path into `assets/`

## ADDED Requirements

### Requirement: Connect buttons match the cards
The Connect section SHALL show one button per link in the flat dark card style, each linking to its profile URL and each with alt text naming the network.

#### Scenario: Visitor clicks a button
- **WHEN** a visitor clicks the LinkedIn button
- **THEN** the LinkedIn profile opens

#### Scenario: Theme check
- **WHEN** the Connect section is viewed in GitHub's light and dark themes
- **THEN** each button appears as a dark panel with text contrast of at least 4.5:1

#### Scenario: Accent stays on palette
- **WHEN** a `connect` entry in `data/profile.yml` uses Amber or a colour outside Blue, Leaf, Violet and Cyan
- **THEN** the run fails naming the entry and writes nothing

### Requirement: Weak repos hidden from the public table
Repositories listed under `hide` in `data/profile.yml` SHALL NOT appear in the All projects public table. Initially `ImageResize` and `Extra-Curricular-Activity-Management` are hidden.

#### Scenario: Initial hidden set
- **WHEN** a visitor expands All projects
- **THEN** neither `ImageResize` nor `Extra-Curricular-Activity-Management` is listed

### Requirement: Employer is linked
The About section SHALL link the employer name to the employer's website.

#### Scenario: Visitor clicks Agrileaf
- **WHEN** a visitor clicks "Agrileaf" in the About section
- **THEN** `https://agrileaf.in` opens

## MODIFIED Requirements

### Requirement: Alt text matches the images
The hero and stack images SHALL have alt text that states the same name, intro, contribution figures and tools that the images show.

#### Scenario: Screen reader on the hero
- **WHEN** a screen reader announces the hero image
- **THEN** it reads the name, the intro, the yearly contribution total and the weekly peak currently in the hero SVG
