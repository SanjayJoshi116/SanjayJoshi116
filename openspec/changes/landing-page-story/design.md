## Context

`render_site()` in `scripts/render_profile.py` currently builds one `index.html` that copies the README's SVG cards into `site/assets/` and places them in the README's order. It reuses the shared README models (`featured_cards`, `private_entry`, `public_cells`, `asset_alts`). `main()` loads a `pulse.svg` kept from a no-token run into `out` only so the site can copy it. `og.png` is drawn with Pillow and measured with the real font. Motivation: see proposal.md (Why). Requirements: see `specs/profile-landing-page/spec.md`.

## Goals / Non-Goals

**Goals:**
- The site reads from the same `data` dict as the README, so projects and counts still match by construction, but has its own markup, layout and theme.
- Multiple pages from one builder, each with its own preview tags and image, and all within the existing all-or-nothing pass.
- Keep every guarantee: no scripts, nothing remote, contrast ≥ 4.5:1, private-name check, no silent overflow.

**Non-Goals:**
- Changing the README, `assets/` or the workflow.
- A theme toggle, client-side behaviour or analytics.
- Guaranteeing the print layout fits one page for arbitrary future content.

## Decisions

**D1. One page shell, many pages.** A `site_page(cfg, url, path, title, desc, body)` helper builds the `<head>` (title, canonical, Open Graph and Twitter tags, inline CSS) for any page. `path` is the page's address relative to `site.url` (`""` for home, `projects/<slug>/`), which gives the absolute canonical and `og:image` URLs and the relative prefix (`""` or `../../`) for links back. Home and case-study pages differ only in `body`. The private-name check runs on each page's content (`page_content`) before it joins `out`.
*Alternative:* a template engine. Rejected: a dependency for two page types.

**D2. Contribution chart drawn inline, coloured by the theme.** The chart is an inline `<svg>` in the HTML (same weekly series and price-line shape as `hero.svg`), using `stroke="var(--accent)"` and a CSS-variable gradient fill, with `role="img"` and `aria-label` from `chart_alt()`. It scales with `viewBox`, follows the theme, and needs no file or request. The name and intro beside it are real `<h1>`/`<p>` text, so the hero no longer needs screen-reader-only copies.
*Alternatives:* reuse `hero.svg` as an `<img>` (stays dark, text not selectable, the current problem); CSS-only bars (loses the price-line identity); a PNG (not theme-aware).

**D3. Theme tokens per theme, accents included.** `PAGE` grows from page colours to a full token set per theme: `bg`, `panel` (card surface), `text`, `muted`, `link`, `accent`, `leaf` (Now ages), `amber` (private badge), `line`. The light theme uses darker accents (the dark theme's `#58A6FF` blue is about 2.4:1 on white), for example `#0969DA` link, `#1A7F37` leaf and `#9A6700` amber. `check_contrast()` checks every text token against both `bg` and `panel` of its theme. Language-bar segment colours are decorative (never text) and stay `LANG_COLORS`.
*Alternative:* keep cards dark in light mode. Rejected: that is exactly the README look the change moves away from.

**D4. Cards keep the flat style, rebuilt in HTML.** A card is a bordered panel with a 3 px top accent line (blue public, amber private), the title, a two-line clamped summary and tag pills, so the site reads as the same identity as the README without the images. Stats are a row of number and label pairs; languages are a CSS flex bar (`width:%` per segment from `lang_shares()`) plus a text legend; stack rows are a label and inline tags; connect links are text buttons. No text sits on a decorative colour.

**D5. `case` blocks validated on every run, used only by the site.** `gather()` already walks the featured candidates; it now also keeps every public candidate with its repo URL (`public_all`, before the top-2 cut) and every private card project (`private_cards`). A new `case_studies(cfg, data)` validates `case` blocks (fields, approach list, diagram fallback, allowed projects, unique slugs) and returns page models. It runs on every render, not only with `--site`, so a bad block fails a local README run too; it writes nothing for the README. The slug comes from `slug(title)` unless `case.slug` is set.
*Alternative:* validate only with `--site`. Rejected: CI always runs `--site`, but local runs would let typos through until CI.

**D6. Featured cards point to case pages.** `featured_cards()` returns the entries (not SVG file names) with their default href. The README keeps its SVG `<img>` per card; the site renders the text card and swaps the href to `projects/<slug>/` when that project has a page. Matching is by the project title, which is unique within each side.

**D7. One preview image renderer, many images.** `render_og()` becomes `render_og(lines)` with a title line, wrapped body copy and a footer line, and loads the fonts once per run. Home: name / intro / host. Case study: project title / summary / `name · host`. The title line must fit (fails otherwise), the body ends with "…" when too long, and every drawn string goes through the private-name check. Images are written next to their page (`site/og.png`, `site/projects/<slug>/og.png`).

**D8. Now section from pulse rows.** It uses `data["pulse"]` (already newest first) and `pulse_age()`'s long form ("3 days ago"), with the render date in IST written as "14 Nov 2026". `data["pulse"] is None` (no token) leaves the section out. Since the site no longer copies `pulse.svg`, the kept-`pulse.svg` load in `main()` is removed; the README's untouched pulse region needs no file in `out`.

**D9. Print styles plus a print-only contact line.** `@media print` sets white background and dark text, hides the chart, Now section, activity, connect buttons and footer, and tightens type. A `print-only` line under the intro lists each connect link's address as text (more reliable across browsers than `a::after{content:attr(href)}`). Case-study links in cards print as plain titles. If the current content does not fit one page in the branch review, the public table is hidden in print and its count stays in the heading; the decision is recorded in tasks.

**D10. Site stops copying SVGs.** The site output no longer includes `site/assets/`; the existing stale-file sweep removes it on the first run. `asset_alts()` is used only by the README again, and the site's alt-from-`<desc>` path goes away with it.

## Risks / Trade-offs

- [Light-theme accent colours drift from the README palette] → they are darker variants of the same hues, checked by `check_contrast()`; the dark theme keeps the README colours.
- [Case copy is new writing to maintain] → `case` is optional; a candidate without it simply has no page and its card links where it does today.
- [Ages on a static page go stale between renders] → the Now section shows the render date; the fingerprint gate re-renders at least daily.
- [Print layout overflows as content grows] → manual print check in every branch review; D9 fallback hides the public table in print.
- [A case page is shared, then its `case` block is removed] → the page disappears (404). Accepted: removal is a deliberate content change; renaming a project changes its slug unless `case.slug` pins it.
- [Delta spec depends on an unarchived change] → archive `profile-landing-page` before applying or archiving this change.

## Migration Plan

1. Merge and archive `profile-landing-page`, so its spec is in `openspec/specs/`.
2. Implement on a branch; write `case` copy for at least one public and one private candidate.
3. Dispatch the workflow on the branch; review `site-preview` in desktop light and dark, at mobile width, and in the browser's print preview (A4 and Letter).
4. Merge; the next render on `main` deploys the new site. The first run removes `site/assets/` through the stale-file sweep.

Rollback: revert the merge commit; the next render redeploys the previous site. The README is unaffected either way.

## Open Questions

- The copy of each `case` block (problem, approach, outcome) and which candidates get one first. This is content, written during implementation, and doesn't change the design.
