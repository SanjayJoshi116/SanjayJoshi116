# profile-readme-layout Specification

## Purpose

Defines the structure of the GitHub profile README: section order, which projects are featured versus collapsed, and the trimmed tech stack, so the page reads well on a 10-second skim.

## Requirements

### Requirement: Fixed section order
The README SHALL present sections in this order: hero, About, Featured projects, All projects (collapsed), Stack, Activity, Connect.

#### Scenario: Visitor skims the profile
- **WHEN** a visitor opens the profile page
- **THEN** the hero image appears first, followed by About, Featured projects, a collapsed All projects section, the stack grid, the Activity cards, and the Connect buttons, in that order

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
The README MUST NOT load images from capsule-render, readme-typing-svg, github-readme-stats, streak-stats, shields.io, or any other third-party host. Every image, including the Connect buttons, SHALL come from `assets/`.

#### Scenario: External image audit
- **WHEN** all `<img src>` URLs and markdown image URLs in the README are listed
- **THEN** every URL is a relative path into `assets/`
### Requirement: Accurate All projects counts
The All projects summary SHALL show the number of private projects and public repositories listed inside it, and the numbers MUST equal the entries actually listed, counting each member of a public group as one repository.

#### Scenario: Count matches list
- **WHEN** a visitor expands All projects
- **THEN** the number of private entries and the number of public repositories linked in the table (group members included) equal the counts shown in the summary line

#### Scenario: Forks and profile repo not counted
- **WHEN** the owner has forked public repositories and the profile repository
- **THEN** none of them are listed or counted

### Requirement: Alt text matches the images
The hero and stack images SHALL have alt text that states the same name, intro, contribution figures and tools that the images show.

#### Scenario: Screen reader on the hero
- **WHEN** a screen reader announces the hero image
- **THEN** it reads the name, the intro, the yearly contribution total and the weekly peak currently in the hero SVG

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

### Requirement: Pulse strip under the private cards
The Featured section SHALL show the pulse strip directly below the private cards row, at full width, without a link.

#### Scenario: Visitor skims Featured
- **WHEN** a visitor reaches the Featured section
- **THEN** they see the public cards, the private cards, then the pulse strip, in that order

### Requirement: Grouped repos shown as one row
Each public repo group SHALL appear as a single row in the All projects public table, after the individually listed repos. The row SHALL show the group title, its stack and its one-line description, and SHALL link every member repository. Initially the group "Early ML coursework" holds StartupSuccessPrediction, HousePricePrediction, CricketScore, CustomerSegmentation and MachineLearningPrograms.

#### Scenario: Initial group
- **WHEN** a visitor expands All projects
- **THEN** the public table has 4 rows (movie-app-v2, movie-dash-v2, tv-dash, Early ML coursework), and the last row links all 5 notebook repos

#### Scenario: Member still reachable
- **WHEN** a visitor clicks `CricketScore` in the Early ML coursework row
- **THEN** the CricketScore repository opens

### Requirement: Collapsed system diagram
The Featured section SHALL include, after the private cards and after the pulse strip when it is present, a `<details>` element collapsed by default whose summary reads "How <project title> works". Expanded, it SHALL show the pipeline diagram at full width, with alt text that names the project and lists every stage title and detail in order.

#### Scenario: Default collapsed
- **WHEN** a visitor loads the profile
- **THEN** the "How SwingTrade AI works" summary is visible and the diagram is hidden until it is clicked

#### Scenario: Screen reader on the diagram
- **WHEN** a screen reader reaches the expanded diagram
- **THEN** it announces e.g. "SwingTrade AI daily flow: NSE data (752 stocks, daily), then Indicators (EMA, RSI, ATR, market regime), then 23 detectors (breakouts, pullbacks, reversals), then Scan + score (weighted score, veto layer), then Alerts (email, Telegram)"
