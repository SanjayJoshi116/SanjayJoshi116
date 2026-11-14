# profile-landing-page Specification

## Purpose

A GitHub Pages landing page generated from `data/profile.yml` and the profile's SVG cards, so the profile has a shareable link with previews and no second copy of its content.

## Requirements

### Requirement: Site built from the profile data
When run with `--site`, the generator SHALL build a static site in `site/` from `data/profile.yml` and the same GitHub API data as the README. The site is written as native page content (text, CSS and one inline chart), not as copies of the README's SVG cards, and `site/` SHALL contain no copy of `assets/*.svg`. The home page SHALL show, in this order: the hero (profile name and intro as text, and the contribution chart), the Now section (when there is pulse data), the featured work, the stack, the All projects section, the activity numbers and languages, the connect links, and a footer with the render date. The featured work SHALL be the same projects the README features in that run, each shown as a text card with its title, summary and tags. A featured card SHALL link to its case-study page when the project has one; otherwise a public card SHALL link to its repository and a private card to the All projects section. The hand-written About section is not part of the site.

#### Scenario: Site run
- **WHEN** the generator runs with `--site` and every API call succeeds
- **THEN** `site/index.html`, `site/og.png` and every case-study page with its preview image are written, the home page shows the sections above in order, and `site/` holds no SVG card file

#### Scenario: Default run
- **WHEN** the generator runs without `--site`
- **THEN** `site/` is neither read nor written, and `assets/` and `README.md` are rendered exactly as before

#### Scenario: Same featured projects as the README
- **WHEN** a site run completes
- **THEN** the featured cards and All projects entries on the home page are the same projects as in the README written by that run

#### Scenario: Text, not images
- **WHEN** the home page is shown
- **THEN** the name, intro, stats, languages, stack, featured cards and connect links are selectable text, and the contribution chart is the only graphic

### Requirement: Site content matches the README counts
The All projects section on the site SHALL show the same private and public counts as the README summary line, and the counts MUST equal the entries listed on the page, counting each member of a public group as one repository.

#### Scenario: Group members counted
- **WHEN** the public table has a group with three listed members
- **THEN** the page's public count includes all three and matches the README's

### Requirement: Self-contained page
No site page MAY load any remote resource: no remote fonts, scripts, stylesheets or images. Pages MUST NOT contain scripts. CSS SHALL be inline, text SHALL use the system font stack, and the contribution chart SHALL be drawn inline in the page. Every link between site pages and every reference to a site file SHALL be relative, so the site works from any base path and when opened from disk.

#### Scenario: Opened from disk
- **WHEN** `site/index.html` or a case-study page is opened directly from the file system after a site run
- **THEN** the page renders fully, links between pages work, and no request leaves the machine

### Requirement: Light and dark theme with readable contrast
Every site page SHALL follow the visitor's `prefers-color-scheme` with a light and a dark theme, and all page content, cards and the chart included, SHALL take its colours from the active theme. Every text colour used on a page, accent colours included, SHALL have contrast of at least 4.5:1 against the background it sits on, in both themes. The generator SHALL check this before writing and fail if any pair is below 4.5:1.

#### Scenario: Low-contrast colour
- **WHEN** a page text colour has contrast below 4.5:1 against either theme's background
- **THEN** the run fails naming the colour and writes nothing

#### Scenario: Light theme
- **WHEN** a visitor with a light system theme opens the home page
- **THEN** the cards, stats and chart are drawn on the light background, not as dark panels

### Requirement: Responsive layout
Every site page SHALL work from 320 px wide up to desktop with no horizontal page scroll. Cards and stats that sit side by side on desktop SHALL stack on narrow screens, and wide content (the projects table) SHALL scroll inside its own box rather than widen the page.

#### Scenario: Phone width
- **WHEN** the home page or a case-study page is shown 360 px wide
- **THEN** cards stack in one column and the page does not scroll sideways

### Requirement: Link preview metadata
Every site page SHALL carry a `<title>`, a meta description, a canonical link, Open Graph tags (`og:title`, `og:description`, `og:url`, `og:image`, `og:image:width`, `og:image:height`, `og:type`) and Twitter card tags (`twitter:card` = `summary_large_image`). For the home page the title is the profile name and the description is the intro; for a case-study page they are the project title and its summary, and only the page's `<title>` (the browser tab) adds the profile name after the project title. Every URL in these tags SHALL be absolute, built from `site.url` in `data/profile.yml`, and each page's `og:image` SHALL be that page's own preview image. A site run without a valid `site.url` (an `https://` URL ending in `/`) SHALL fail and write nothing.

#### Scenario: Shared link
- **WHEN** the site URL is pasted into a link previewer
- **THEN** the preview shows the profile name, the intro and the home page's `og.png`

#### Scenario: Shared case-study link
- **WHEN** a case-study page's URL is pasted into a link previewer
- **THEN** the preview shows the project title, its summary and that page's own preview image

#### Scenario: Missing base URL
- **WHEN** `site.url` is missing or not an `https://` URL ending in `/`
- **THEN** a `--site` run fails naming `site.url` and writes nothing

### Requirement: Preview image
The generator SHALL produce a 1200×630 PNG preview image for every site page: `site/og.png` showing the profile name and intro, and one per case-study page showing the project title, its summary and the profile name. Text in the images SHALL be measured with the font actually used; a title line (profile name or project title) MUST fit on one line or the run fails, and copy too long for its lines SHALL end with "…". Text colours in the images SHALL meet 4.5:1 against the image background. If the font cannot be found, the run fails and writes nothing.

#### Scenario: Long intro
- **WHEN** the intro or a project summary needs more lines than its image allows
- **THEN** the last line ends with "…" and the run succeeds

#### Scenario: Title too wide
- **WHEN** the profile name or a project title is wider than the image's text area
- **THEN** the run fails naming the line and writes nothing

### Requirement: Private repo names never written to the site
No site page and no text drawn into any preview image MAY contain any private repository `owner/name` value or bare name from `data/profile.yml`, with the same matching rules as the README check. The check SHALL cover what each page says (its text, link and preview-tag values, and page addresses such as case-study slugs), not its fixed markup or CSS. The generator SHALL check before writing and fail if any is found. The error MUST NOT print the value.

#### Scenario: Private name in the intro
- **WHEN** the intro contains a private card repository's bare name as a whole word
- **THEN** a `--site` run fails without printing the name and writes nothing

#### Scenario: Private name in a case study
- **WHEN** a case-study block or its slug contains a private card repository's bare name as a whole word
- **THEN** a `--site` run fails without printing the name or the slug and writes nothing

### Requirement: All-or-nothing site build
A `--site` run SHALL render `assets/`, `README.md` and every site file in memory and write nothing if any step fails. When it succeeds, `site/` SHALL contain exactly the files of this run: files and folders left from earlier runs are removed.

#### Scenario: API failure during a site run
- **WHEN** any API call fails during a `--site` run
- **THEN** `assets/`, `README.md` and `site/` are left exactly as they were

#### Scenario: Stale page
- **WHEN** a project that had a case-study page in the last site run no longer has one (its `case` block is removed)
- **THEN** its page and preview image are no longer in `site/` after the next successful site run

### Requirement: Site is build output
`site/` SHALL be ignored by git and MUST NOT be committed by the workflow.

#### Scenario: Workflow commit
- **WHEN** the workflow commits refreshed assets
- **THEN** the commit contains no file under `site/`

### Requirement: Deploy on render, from main only
The render workflow SHALL run the generator with `--site` whenever it renders. On `main`, after a successful render, it SHALL publish `site/` to GitHub Pages. It SHALL NOT deploy when the change gate skips the render or when the render fails, leaving the last published site in place. The poll's saved push fingerprint SHALL change only after the deploy succeeds (on `main`) or the render succeeds (elsewhere), so a failed deploy is retried by the next poll. On any other branch it SHALL NOT deploy; it SHALL upload `site/` as a workflow artifact for review instead. Pages logs follow the same rule as the rest of the workflow: no private repo names, push times or the token.

#### Scenario: Unchanged poll
- **WHEN** an hourly poll finds the push fingerprint unchanged
- **THEN** nothing is rendered and nothing is deployed

#### Scenario: Render on main
- **WHEN** a render on `main` succeeds
- **THEN** the new `site/` is published to `site.url`

#### Scenario: Branch review run
- **WHEN** the workflow is dispatched on a branch other than `main`
- **THEN** `site/` is uploaded as a workflow artifact and the published site is unchanged

#### Scenario: Failed render
- **WHEN** a render on `main` fails
- **THEN** no deploy runs and the published site stays as it was

#### Scenario: Failed deploy
- **WHEN** a render on `main` succeeds but the Pages deploy fails
- **THEN** the saved push fingerprint stays as it was, so the next poll renders and deploys again

### Requirement: Case-study content in the profile data
A featured candidate in `data/profile.yml` (an entry of `featured.public`, or a private project with a `card`) MAY carry a `case` block with a `problem` (text), an `approach` (a list of steps), and an `outcome` (text). A private project with a diagram MAY leave out `approach`; its diagram stages are then used. The page address SHALL be derived from the project title unless the block sets its own `slug`. A `case` block anywhere else in the file (on another project, or nested under a card, a diagram or a group), a missing field, an empty approach, or two pages with the same address SHALL fail the run naming the project, and write nothing. The README SHALL NOT change because of `case` blocks.

#### Scenario: Missing outcome
- **WHEN** a `case` block has no `outcome`
- **THEN** a `--site` run fails naming the project and writes nothing

#### Scenario: Private project with a diagram
- **WHEN** a private project with a diagram has a `case` block without `approach`
- **THEN** its case-study page lists the diagram stages, each with its title and detail, as the approach

#### Scenario: Duplicate address
- **WHEN** two projects' case-study pages would have the same address
- **THEN** a `--site` run fails naming both projects and writes nothing

### Requirement: Case-study pages
The site SHALL have one page at `projects/<slug>/` for every featured candidate with a `case` block, whether or not the README features that project in the current run; a public candidate whose repository is missing or a fork gets no page. Each page SHALL show the project title, its summary, its tags as the stack, then the problem, the approach as an ordered list and the outcome, and a link back to the home page. Every case-study page SHALL be linked from its project's entry in the All projects section, so it can be reached even when its project is not featured; the link is left off the printout. A public project's page SHALL link to its repository. A private project's page SHALL show it as private and in development with its version, and MUST NOT link to or name its repository; a collaborator link (`with`) MAY be shown.

#### Scenario: Public case study
- **WHEN** a public featured candidate has a `case` block and its repository exists
- **THEN** its page shows the problem, approach, stack and outcome and links to the repository

#### Scenario: Private case study
- **WHEN** a private project with a card has a `case` block
- **THEN** its page shows "Private, in development" and the version, with no link to and no name of its repository

#### Scenario: Not featured this run
- **WHEN** a candidate with a `case` block is not among the projects the README features this run
- **THEN** its case-study page is still built, so links to it keep working, and its All projects entry links to it

### Requirement: Now section
When the run has pulse data (a token and at least one private card repository), the home page SHALL show a Now section listing every private card project by title and version, most recently active first, each with its age in words ("active today", "active 3 days ago", "active 2 weeks ago"), counted in IST calendar days as in the pulse strip, and the date the page was rendered. It SHALL show no repository names and no push times. When there is no pulse data the section SHALL be left out.

#### Scenario: Run with a token
- **WHEN** a site run has pulse data for three private card projects
- **THEN** the Now section lists all three, newest activity first, each with its age in words, and shows the render date

#### Scenario: Run without a token
- **WHEN** a site run has no token
- **THEN** the home page has no Now section and the run succeeds

### Requirement: Print as a one-page CV
Printing the home page SHALL produce a résumé layout: dark text on a white background regardless of theme, showing the name, intro, connect links with their addresses written out, featured work, stack and a compact project list, and hiding the chart, the Now section and on-screen navigation. With the current `data/profile.yml` the printout SHALL fit one A4 or US Letter page; this is checked by hand in the branch review, not by the generator.

#### Scenario: Print preview
- **WHEN** the home page is printed from a browser in dark mode
- **THEN** the printout is dark text on white, shows the contact addresses and featured work, and contains no chart or Now section

#### Scenario: Links on paper
- **WHEN** the home page is printed
- **THEN** each connect link shows its address as text, so the paper copy is usable without clicking
