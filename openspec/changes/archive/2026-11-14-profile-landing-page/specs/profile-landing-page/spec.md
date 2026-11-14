## Purpose

A GitHub Pages landing page generated from `data/profile.yml` and the profile's SVG cards, so the profile has a shareable link with previews and no second copy of its content.

## ADDED Requirements

### Requirement: Site built from the profile data
When run with `--site`, the generator SHALL build a static site in `site/` from `data/profile.yml`, the same GitHub API data as the README and the same generated SVG cards. The page SHALL show, in this order: the hero with the intro, the featured cards, the pulse strip (when the README shows one), the system diagram in a collapsed section (when one is defined), the All projects table, the stack, the activity cards and the connect links. Public featured cards SHALL link to their repositories; private cards SHALL link to the All projects section on the same page. The hand-written About section is not part of the site.

#### Scenario: Site run
- **WHEN** the generator runs with `--site` and every API call succeeds
- **THEN** `site/index.html`, `site/og.png` and every SVG the page uses are written, and the page shows the sections above in order

#### Scenario: Default run
- **WHEN** the generator runs without `--site`
- **THEN** `site/` is neither read nor written, and `assets/` and `README.md` are rendered exactly as before

#### Scenario: Same featured projects as the README
- **WHEN** a site run completes
- **THEN** the featured cards, pulse rows and All projects entries on the page are the same as in the README written by that run

### Requirement: Site content matches the README counts
The All projects section on the site SHALL show the same private and public counts as the README summary line, and the counts MUST equal the entries listed on the page, counting each member of a public group as one repository.

#### Scenario: Group members counted
- **WHEN** the public table has a group with three listed members
- **THEN** the page's public count includes all three and matches the README's

### Requirement: Self-contained page
The page MUST NOT load any remote resource: no remote fonts, scripts, stylesheets or images. CSS SHALL be inline, text SHALL use the system font stack, and images SHALL be local files in `site/`. Every link and image reference between site files SHALL be relative, so the page works from any base path and when opened from disk.

#### Scenario: Opened from disk
- **WHEN** `site/index.html` is opened directly from the file system after a site run
- **THEN** every image renders and no request leaves the machine

### Requirement: Light and dark theme with readable contrast
The page SHALL follow the visitor's `prefers-color-scheme` with a light and a dark theme, in the flat dark card style (cards stay dark in both themes). Every page text colour SHALL have contrast of at least 4.5:1 against the page background it sits on, in both themes. The generator SHALL check this before writing and fail if any pair is below 4.5:1.

#### Scenario: Low-contrast colour
- **WHEN** a page text colour has contrast below 4.5:1 against either theme's background
- **THEN** the run fails naming the colour and writes nothing

### Requirement: Responsive layout
The page SHALL work from 320 px wide up to desktop with no horizontal page scroll. Cards that sit side by side on desktop SHALL stack on narrow screens, and wide content (the projects table, the diagram) SHALL scroll inside its own box rather than widen the page.

#### Scenario: Phone width
- **WHEN** the page is shown 360 px wide
- **THEN** the featured cards stack in one column and the page does not scroll sideways

### Requirement: Link preview metadata
The page SHALL carry a `<title>`, a meta description built from the intro, a canonical link, Open Graph tags (`og:title`, `og:description`, `og:url`, `og:image`, `og:image:width`, `og:image:height`, `og:type`) and Twitter card tags (`twitter:card` = `summary_large_image`). Every URL in these tags SHALL be absolute, built from `site.url` in `data/profile.yml`. A site run without a valid `site.url` (an `https://` URL ending in `/`) SHALL fail and write nothing.

#### Scenario: Shared link
- **WHEN** the site URL is pasted into a link previewer
- **THEN** the preview shows the profile name, the intro and the `og.png` image

#### Scenario: Missing base URL
- **WHEN** `site.url` is missing or not an `https://` URL ending in `/`
- **THEN** a `--site` run fails naming `site.url` and writes nothing

### Requirement: Preview image
The generator SHALL produce `site/og.png`, a 1200×630 PNG in the flat dark card style showing the profile name and the intro. Text in the image SHALL be measured with the font actually used; the name MUST fit on one line or the run fails, and an intro too long for its lines SHALL end with "…". Text colours in the image SHALL meet 4.5:1 against the image background. If the font cannot be found, the run fails and writes nothing.

#### Scenario: Long intro
- **WHEN** the intro needs more lines than the image allows
- **THEN** the last line ends with "…" and the run succeeds

#### Scenario: Name too wide
- **WHEN** the profile name is wider than the image's text area
- **THEN** the run fails naming the name line and writes nothing

### Requirement: Private repo names never written to the site
The site's HTML and every text drawn into `og.png` MUST NOT contain any private repository `owner/name` value or bare name from `data/profile.yml`, with the same matching rules as the README check. The generator SHALL check before writing and fail if any is found. The error MUST NOT print the value. Copied SVGs are the same files the README uses and are covered by their existing checks.

#### Scenario: Private name in the intro
- **WHEN** the intro contains a private card repository's bare name as a whole word
- **THEN** a `--site` run fails without printing the name and writes nothing

### Requirement: All-or-nothing site build
A `--site` run SHALL render `assets/`, `README.md` and `site/` in memory and write nothing if any step fails. When it succeeds, `site/` SHALL contain exactly the files of this run: files left from earlier runs are removed.

#### Scenario: API failure during a site run
- **WHEN** any API call fails during a `--site` run
- **THEN** `assets/`, `README.md` and `site/` are left exactly as they were

#### Scenario: Stale file
- **WHEN** a card that existed in the last site run is no longer rendered (e.g. the diagram is removed)
- **THEN** its file is no longer in `site/` after the next successful site run

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
