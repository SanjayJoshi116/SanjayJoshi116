## 1. Prerequisites

- [x] 1.1 Merge the `profile-landing-page` PR and archive that change, so `openspec/specs/profile-landing-page/spec.md` exists as the base for this delta
- [x] 1.2 Start a branch from the updated `main`

## 2. Data and validation

- [x] 2.1 Keep every public featured candidate with its repo URL (`public_all`) and every private card project (`private_cards`) in `gather()`'s result, without changing what the README features
- [x] 2.2 Add `case_studies(cfg, data)`: validate `case` blocks (allowed projects, `problem`/`approach`/`outcome`, non-empty approach, diagram fallback for private projects, slug from title or `case.slug`, unique slugs), skip public candidates whose repo is missing or a fork, and return page models; run it on every render
- [x] 2.3 Check that a run with no `case` blocks renders README and `assets/` byte-identical to before

## 3. Theme and contrast

- [x] 3.1 Extend `PAGE` to the per-theme token set (`bg`, `panel`, `text`, `muted`, `link`, `accent`, `leaf`, `amber`, `line`) with darker light-theme accents
- [x] 3.2 Make `check_contrast()` check every page text token against both `bg` and `panel` of its theme; confirm a deliberately low-contrast token fails and writes nothing

## 4. Home page

- [x] 4.1 Add the page shell `site_page()` (per-page title, description, canonical, Open Graph and Twitter tags from `site.url` and the page path, inline CSS, relative link prefix)
- [x] 4.2 Hero: name and intro as text, inline theme-coloured contribution chart with `aria-label` from `chart_alt()`
- [x] 4.3 Now section from pulse rows: title, version, age in words, newest first, render date in IST; left out when `data["pulse"]` is None
- [x] 4.4 Featured work as HTML cards (flat panel, accent line, title, summary, tags), same projects as the README, linking to the case page when there is one, else repo (public) or All projects (private); make `featured_cards()` return entries
- [x] 4.5 Stack rows, activity numbers, languages bar plus legend (from `lang_shares()`), connect text buttons, footer with render date
- [x] 4.6 Keep the All projects section on the shared `private_entry`/`public_cells` models with matching counts
- [x] 4.7 Stop copying SVGs into `site/` and remove the kept-`pulse.svg` load from `main()`; confirm the first run sweeps `site/assets/`

## 5. Case-study pages

- [x] 5.1 Render `projects/<slug>/index.html`: title, summary, stack, problem, approach (ordered list; diagram stages with title and detail for private fallback), outcome, back link; public pages link the repo, private pages show "Private, in development" and the version with no repo link or name
- [x] 5.2 Generalise `render_og()` to a title, wrapped body and footer, fonts loaded once; draw `site/og.png` and one `og.png` per case page; title lines must fit, body ends with "…"
- [x] 5.3 Run the private-name check over every page's content (slugs included) and every string drawn into each preview image

## 6. Print

- [x] 6.1 Add `@media print` styles (white background, dark text, hidden chart, Now, activity, connect buttons and footer, tighter type) and the print-only contact line with addresses as text
- [x] 6.2 Print-preview the home page in A4 and Letter with the current content; if it overflows, hide the public table in print (keep its count) and note it here. Overflowed onto a second page (the public table); the table is now hidden in print, and Letter and A4 both print on one page

## 7. Content

- [x] 7.1 Write `case` blocks in `data/profile.yml` for at least one public candidate and one private card project (use the diagram for the private one), keeping private repo names out of the copy

## 8. Verification

- [x] 8.1 Harness run with and without a token: home page sections in order, Now present only with a token, case pages and their `og.png` written, no SVG files in `site/`, README and `assets/` unchanged
- [x] 8.2 Failure cases write nothing: bad `case` block, duplicate slug, too-wide project title in a preview image, private name in a case block
- [x] 8.3 Open `site/index.html` and a case page from disk: links between pages work, no request leaves the machine, no horizontal scroll at 360 px
- [ ] 8.4 Branch run: review the `site-preview` artifact in desktop light, desktop dark, mobile and print preview; check a case-study link in a link previewer after merge

## 9. Docs

- [x] 9.1 `CLAUDE.md`: site layout (pages, no copied SVGs, per-page `og.png`), the `case` key, Now and print, and the rules that now cover every page and preview image
