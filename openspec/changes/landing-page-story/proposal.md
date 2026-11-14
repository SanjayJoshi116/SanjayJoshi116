## Why

The landing page repeats the README section by section, as the same dark SVG images in the same order. Those images are a workaround for GitHub stripping CSS from Markdown; the site has no such limit, yet it inherits the workaround, so it adds a URL and link previews but nothing a visitor couldn't get on the profile. Visitors from LinkedIn, a CV or a shared link are often not developers and won't open a repo: they need a page that tells what the work is, what's happening now, and that can be handed over as a CV.

The README stays the dashboard for people already on GitHub. The site becomes the story.

## What Changes

- **Native page instead of images.** The hero (name, intro), stats, languages, stack, featured cards and connect links become real HTML text and CSS that follow the visitor's light or dark theme. The contribution chart is the only graphic, drawn inline and coloured by the theme. The site no longer copies `assets/*.svg`. **BREAKING** for the site only: `site/assets/` goes away, and the "cards stay dark in both themes" rule is dropped for the site.
- **Case-study pages.** A featured candidate (a `featured.public` entry, or a private project with a card) that has a new `case` block in `data/profile.yml` gets its own page at `projects/<slug>/`: problem, approach, stack, outcome. Private projects can use their diagram stages as the approach. Private pages never link to or name the repo. Each page has its own preview tags and its own generated `og.png`. Pages exist for every candidate with a case, independent of which ones the README currently features, so shared links stay stable.
- **"Now" section.** The pulse data (private card projects by last push) becomes a short "Now" list on the home page, with plain ages ("active 2 days ago") and the date of the render. Without a token there is no pulse data, so the section is left out. The system diagram moves from the home page to its project's case study.
- **Prints as a one-page CV.** A print stylesheet turns the home page into a black-on-white résumé: name, intro, contact URLs, featured work, stack and a compact project list, with the chart, Now section and navigation hidden.
- **Home page order:** hero (name, intro, chart), Now, featured work, stack, all projects, activity (numbers and languages), connect, footer with the render date.
- The privacy check, the all-or-nothing build, the self-contained rule (no scripts, nothing remote) and the overflow rules cover every page and every preview image.
- The README, `assets/` and runs without `--site` are unchanged.
- Out of scope: a theme toggle (it needs a script), a command palette, the "Work with me", `/uses`, timeline and SEO ideas.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `profile-landing-page`: page content and order, native HTML rendering, theme and contrast (accent colours now sit on both page themes), preview images per page, privacy and all-or-nothing rules over several pages, plus new requirements for case-study pages, the Now section and print-as-CV. This capability is introduced by the in-flight change `profile-landing-page`, which must be archived first.

## Impact

- `scripts/render_profile.py`: site builder rewritten as native HTML (inline chart, stat and language blocks, cards, case-study pages, Now list, print CSS); per-page `og.png`; `case` validation; contrast check covers the light and dark accent colours; private-name check over every page; drops copying SVGs and the kept-`pulse.svg` load that only the site used.
- `data/profile.yml`: optional `case` blocks on featured candidates (copy to write for the current ones).
- `CLAUDE.md`: site layout, `case` key, the rules that now cover several pages.
- No workflow, dependency or README change. Branch review of the `site-preview` artifact still applies (desktop light and dark, mobile, plus a print preview).
- Depends on `profile-landing-page` being merged and archived, so its spec is the base for this delta.
