"""Render the profile README's card SVGs from data/profile.yml and the GitHub API.

Usage:
    python scripts/render_profile.py [--require-token]

Env:
    PROFILE_TOKEN  optional fine-grained read-only PAT. Enables private-repo
                   rotation and private language bytes for allowlisted repos.

Everything is fetched and rendered in memory first; files are written only if
every step succeeds, so a failed run never leaves assets half-updated.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "data" / "profile.yml"
ASSETS = ROOT / "assets"
README = ROOT / "README.md"
API = "https://api.github.com"

# Aurora on Ink
BLUE = "#58A6FF"
LEAF = "#34D399"
VIOLET = "#8B5CF6"
AMBER = "#F5B544"
CYAN = "#22D3EE"
TEXT = "#F0F6FC"
MUTED = "#9DA7B3"
LANG_COLORS = [BLUE, LEAF, VIOLET, CYAN, "#F472B6", "#C9D1D9"]

# Card surface; check_contrast() proves every text colour stays AA on it.
SURFACE = "#0F1424"

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Consolas,Menlo,monospace"


class RenderError(Exception):
    pass


# ---------------------------------------------------------------- GitHub API

class GitHub:
    def __init__(self, token):
        self.token = token

    def _request(self, url, data=None, auth=True, accept="application/vnd.github+json"):
        headers = {"Accept": accept, "User-Agent": "profile-renderer"}
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            raise RenderError(f"HTTP {e.code} from {url.split('?')[0]}") from None
        except urllib.error.URLError as e:
            raise RenderError(f"network error: {e.reason}") from None

    def get(self, path, auth=True):
        return json.loads(self._request(API + path, auth=auth))

    def graphql(self, query):
        body = json.dumps({"query": query}).encode()
        out = json.loads(self._request(API + "/graphql", data=body))
        if out.get("errors"):
            raise RenderError("GraphQL error")
        return out["data"]

    def html(self, url):
        return self._request(url, auth=False, accept="text/html")


def gather(cfg, gh):
    user = cfg["user"]
    # Public endpoint without auth: never returns private repos, even with a token.
    repos = {r["name"]: r for r in gh.get(f"/users/{user}/repos?per_page=100&type=owner", auth=False)}
    own = [r for r in repos.values() if not r["fork"]]

    public = []
    for entry in cfg["featured"]["public"]:
        r = repos.get(entry["repo"])
        if r and not r["fork"]:
            public.append({**entry, "stars": r["stargazers_count"], "pushed": r["pushed_at"],
                           "url": r["html_url"]})
    public.sort(key=lambda e: e["pushed"], reverse=True)
    if len(public) < 2:
        raise RenderError("fewer than 2 public allowlist repos found")

    # Featured private candidates: projects with a card, title/version defined once on the project.
    private_cfg = []
    for p in cfg["projects"]["private"]:
        if "card" in p:
            if not p.get("version"):
                raise RenderError(f"private project {p['title']!r} has a card but no version")
            private_cfg.append({**p["card"], "title": p["title"], "version": p["version"]})
    if len(private_cfg) < 2:
        raise RenderError("fewer than 2 private projects have a card")
    private = [dict(e) for e in private_cfg]
    private_repos = []
    if gh.token and all(e.get("repo") for e in private_cfg):
        for i, e in enumerate(private):
            try:
                r = gh.get(f"/repos/{e['repo']}")
            except RenderError:
                raise RenderError(f"private allowlist entry #{i + 1} is not readable with the token") from None
            e["pushed"] = r["pushed_at"]
            private_repos.append(e["repo"])
        private.sort(key=lambda e: e["pushed"], reverse=True)

    # Stats
    if gh.token:
        q = '{ user(login: "%s") { contributionsCollection { contributionCalendar { totalContributions } } } }' % user
        contributions = gh.graphql(q)["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    else:
        page = gh.html(f"https://github.com/users/{user}/contributions")
        m = re.search(r"([\d,]+)\s+contributions?\s+in the last year", page)
        if not m:
            raise RenderError("could not read contribution count")
        contributions = int(m.group(1).replace(",", ""))
    stats = {
        "contributions": contributions,
        "commits": gh.get(f"/search/commits?q=author:{user}&per_page=1")["total_count"],
        "prs": gh.get(f"/search/issues?q=author:{user}+type:pr&per_page=1")["total_count"],
        "stars": sum(r["stargazers_count"] for r in own),
        "repos": len(own),
    }

    # Languages: public own repos plus allowlisted private repos (aggregate only).
    exclude = set(cfg["languages"].get("exclude", []))
    totals = {}
    sources = [f"/repos/{user}/{r['name']}/languages" for r in own] + [f"/repos/{p}/languages" for p in private_repos]
    for src in sources:
        for lang, n in gh.get(src).items():
            if lang not in exclude:
                totals[lang] = totals.get(lang, 0) + n
    if not totals:
        raise RenderError("no language data")

    # All projects table: curated rows in file order, then any other public repo from the API.
    pub_cfg = cfg["projects"]["public"]
    hidden = set(pub_cfg.get("hide") or [])
    rows, seen = [], set()
    for entry in pub_cfg.get("repos") or []:
        r = repos.get(entry["repo"])
        if r and not r["fork"] and entry["repo"] not in hidden:
            rows.append({**entry, "url": r["html_url"]})
            seen.add(entry["repo"])
    extra = [r for r in own if r["name"] not in seen | hidden and r["name"].lower() != user.lower()]
    for r in sorted(extra, key=lambda r: r["pushed_at"], reverse=True):
        about = (r["description"] or "").split(". ")[0].strip().rstrip(".")
        rows.append({"repo": r["name"], "url": r["html_url"], "stack": [r["language"]] if r["language"] else [],
                     "about": about if len(about) <= 100 else about[:99].rstrip() + "…"})

    return {"public": public[:2], "private": private[:2], "stats": stats, "langs": totals,
            "rows": rows, "private_all": cfg["projects"]["private"],
            "private_repos": [e["repo"] for e in private_cfg if e.get("repo")]}


# ---------------------------------------------------------------- contrast

def _lum(hex_or_rgb):
    rgb = hex_or_rgb if isinstance(hex_or_rgb, tuple) else tuple(int(hex_or_rgb[i:i + 2], 16) for i in (1, 3, 5))
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def check_contrast():
    """Every text colour against the flat card surface."""
    worst = {}
    for fg in (TEXT, MUTED, BLUE, LEAF, AMBER, CYAN):
        l1, l2 = sorted((_lum(fg), _lum(SURFACE)), reverse=True)
        worst[fg] = (l1 + 0.05) / (l2 + 0.05)
    # Violet is decorative only (accent lines, language bar); it's not used for text.
    failing = {k: round(v, 2) for k, v in worst.items() if v < 4.5}
    if failing:
        raise RenderError(f"text contrast below 4.5:1: {failing}")
    return worst


# ---------------------------------------------------------------- SVG helpers

def text_w(s, size, bold=False, avg=0.56):
    # avg is a deliberately wide per-char estimate so overflow checks hold across system fonts
    return len(s) * size * (0.6 if bold else avg)


def wrap(s, size, max_w, max_lines):
    words, lines, cur = s.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if text_w(trial, size, avg=0.52) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(" ,.;") + "…"
    return lines


def fmt(n):
    return f"{n:,}"


def svg_open(w, h, title, desc, extra_css=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-labelledby="t d">'
        f'<title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>'
        f"<style>text{{font-family:{SANS}}}.m{{font-family:{MONO}}}{extra_css}</style>"
    )


def surface(w, h, rx, accent=(BLUE, VIOLET), edge=None, grid=False):
    """Flat dark card: solid surface, top accent line, hairline border. Returns defs+background."""
    a1, a2 = accent
    edge_svg = ""
    if edge:
        edge_svg = (
            f'<rect x="1.5" y="1.5" width="{w - 3}" height="{h - 3}" rx="{rx - 1}" fill="none" stroke="{edge}" '
            f'stroke-width="3" stroke-opacity=".35" filter="url(#glow)"/>'
            f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="none" '
            f'stroke="{edge}" stroke-opacity=".6"/>'
        )
    grid_def = grid_svg = ""
    if grid:
        grid_def = ('<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
                    '<circle cx="1.5" cy="1.5" r="1" fill="#fff" fill-opacity=".06"/></pattern>')
        grid_svg = f'<rect width="{w}" height="{h}" fill="url(#dots)"/>'
    return (
        "<defs>"
        f'<clipPath id="frame"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath>'
        '<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="4"/></filter>'
        '<linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{a1}" stop-opacity="0"/><stop offset=".25" stop-color="{a1}"/>'
        f'<stop offset=".75" stop-color="{a2}"/><stop offset="1" stop-color="{a2}" stop-opacity="0"/>'
        "</linearGradient>"
        + grid_def
        + "</defs>"
        + '<g clip-path="url(#frame)">'
        + f'<rect width="{w}" height="{h}" fill="{SURFACE}"/>'
        + grid_svg
        + f'<rect width="{w}" height="2" fill="url(#accent)"/>'
        + "</g>"
        + f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="none" stroke="#fff" stroke-opacity=".1"/>'
        + edge_svg
    )


def badge(label, color, x=36, y=44):
    """Section label with a coloured status dot."""
    return (
        f'<circle cx="{x + 3.5}" cy="{y - 4}" r="3.5" fill="{color}"/>'
        f'<text x="{x + 14}" y="{y}" font-size="11" font-weight="600" fill="{color}" letter-spacing="1.6">{label}</text>'
    )


def pills(tags, x, y, max_x, size=11.5):
    out = []
    for tag in tags:
        w = text_w(tag, size) + 18
        if x + w > max_x:
            print(f"warning: dropped tag {tag!r} (no room)", file=sys.stderr)
            break
        out.append(
            f'<rect x="{x}" y="{y}" width="{w:.0f}" height="22" rx="11" fill="#fff" fill-opacity=".08" '
            f'stroke="#fff" stroke-opacity=".18"/>'
            f'<text x="{x + w / 2:.1f}" y="{y + 15}" font-size="{size}" fill="{TEXT}" text-anchor="middle">{escape(tag)}</text>'
        )
        x += w + 8
    return "".join(out)


# ---------------------------------------------------------------- assets

def render_hero(cfg):
    w, h = 840, 240
    lines = cfg["tagline"]
    n = len(lines)
    cycle = 4 * n
    pct = lambda s: f"{s / cycle * 100:.2f}%"
    css = (
        # Each line owns a 4s slot. Line 0 starts visible (complete first frame) with no
        # negative delay; the others fade in 0.5s before their slot.
        f".l{{opacity:0;animation:tl {cycle}s linear infinite}}"
        f".l0{{opacity:1;animation-name:tl0}}"
        f"@keyframes tl0{{0%,{pct(3)}{{opacity:1;transform:none}}{pct(3.5)}{{opacity:0;transform:translateY(-6px)}}"
        f"{pct(cycle - .5)}{{opacity:0;transform:translateY(6px)}}100%{{opacity:1;transform:none}}}}"
        f"@keyframes tl{{0%{{opacity:0;transform:translateY(6px)}}{pct(.5)},{pct(3.5)}{{opacity:1;transform:none}}"
        f"{pct(4)},100%{{opacity:0;transform:translateY(-6px)}}}}"
        + "".join(f".l{i}{{animation-delay:{4 * i - .5}s}}" for i in range(1, n))
        + ".cur{animation:bl 1.1s steps(1) infinite}@keyframes bl{50%{opacity:0}}"
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
    )
    tag_svg = "".join(
        f'<text class="m l l{i}" x="{w / 2}" y="190" font-size="17" fill="{BLUE}" text-anchor="middle">'
        f'{escape(line)}<tspan class="cur" fill-opacity=".8"> ▌</tspan></text>'
        for i, line in enumerate(lines)
    )
    return (
        svg_open(w, h, f"{cfg['name']} — {cfg['roles']}", " / ".join(lines), css)
        + surface(w, h, 20, accent=(BLUE, LEAF), grid=True)
        + f'<text x="{w / 2}" y="98" font-size="48" font-weight="800" fill="{TEXT}" text-anchor="middle" '
          f'letter-spacing="-1">{escape(cfg["name"])}</text>'
        + f'<rect x="{w / 2 - 28}" y="116" width="56" height="3" rx="1.5" fill="url(#accent)"/>'
        + f'<text x="{w / 2}" y="146" font-size="13" font-weight="600" fill="{MUTED}" text-anchor="middle" '
          f'letter-spacing="3">{escape(cfg["roles"].upper())}</text>'
        + tag_svg
        + "</svg>"
    )


def render_card(entry, private):
    w, h = 420, 200
    if private:
        label, color, accent = "PRIVATE · IN DEVELOPMENT", AMBER, (AMBER, VIOLET)
        corner = entry["version"]
    else:
        label, color, accent = "PUBLIC REPO", BLUE, (BLUE, VIOLET)
        corner = f"★ {entry['stars']}"
    summary = wrap(entry["summary"], 13.5, w - 72, 2)
    kind = "Private project" if private else "Public repo"
    body = (
        badge(label, color)
        + f'<rect x="{w - 36 - text_w(corner, 12, True) - 16:.0f}" y="28" width="{text_w(corner, 12, True) + 16:.0f}" '
          f'height="22" rx="11" fill="#fff" fill-opacity=".08" stroke="#fff" stroke-opacity=".16"/>'
        + f'<text x="{w - 36 - (text_w(corner, 12, True) + 16) / 2:.1f}" y="43" font-size="12" font-weight="600" '
          f'fill="{TEXT}" text-anchor="middle">{escape(corner)}</text>'
        + f'<text x="36" y="84" font-size="25" font-weight="800" fill="{TEXT}" letter-spacing="-.4">{escape(entry["title"])}</text>'
        + "".join(
            f'<text x="36" y="{108 + i * 19}" font-size="13.5" fill="{MUTED}">{escape(line)}</text>'
            for i, line in enumerate(summary)
        )
        + pills(entry["tags"], 36, 148, w - 36)
    )
    return (
        svg_open(w, h, f"{entry['title']} ({kind})", entry["summary"])
        + surface(w, h, 16, accent=accent, edge=AMBER if private else None)
        + body
        + "</svg>"
    )


def render_stack(cfg):
    groups = cfg["stack"]
    colors = [BLUE, LEAF, CYAN, TEXT]
    w, row_h, pad = 840, 54, 10
    h = pad * 2 + len(groups) * row_h
    rows_svg = []
    for i, (label, tools) in enumerate(groups.items()):
        y = pad + i * row_h
        if i:
            rows_svg.append(f'<line x1="24" y1="{y}" x2="{w - 24}" y2="{y}" stroke="#fff" stroke-opacity=".08"/>')
        rows_svg.append(badge(escape(label), colors[i % len(colors)], x=28, y=y + 31))
        x, max_x = 168, w - 24
        for tool in tools:
            tw = text_w(tool, 13) + 24
            if x + tw > max_x:
                raise RenderError(f"stack row {label!r} overflows; shorten it")
            rows_svg.append(
                f'<rect x="{x}" y="{y + 13}" width="{tw:.0f}" height="28" rx="14" fill="#fff" fill-opacity=".07" '
                f'stroke="#fff" stroke-opacity=".16"/>'
                f'<text x="{x + tw / 2:.1f}" y="{y + 31.5}" font-size="13" fill="{TEXT}" text-anchor="middle">{escape(tool)}</text>'
            )
            x += tw + 8
    desc = "; ".join(f"{k}: {', '.join(v)}" for k, v in groups.items())
    return (
        svg_open(w, h, "Tech stack", desc)
        + surface(w, h, 16, accent=(BLUE, VIOLET))
        + "".join(rows_svg)
        + "</svg>"
    )


def render_stats(stats):
    w, h = 420, 200
    tiles = [("commits", "public commits"), ("prs", "pull requests"), ("stars", "stars earned"), ("repos", "public repos")]
    tile_svg = ""
    for i, (key, label) in enumerate(tiles):
        x = 210 + (i % 2) * 96
        y = 92 + (i // 2) * 56
        tile_svg += (
            f'<text x="{x}" y="{y}" font-size="22" font-weight="700" fill="{TEXT}">{fmt(stats[key])}</text>'
            f'<text x="{x}" y="{y + 18}" font-size="11.5" fill="{MUTED}">{label}</text>'
        )
    desc = (f"{fmt(stats['contributions'])} contributions in the past year; {fmt(stats['commits'])} public commits, "
            f"{stats['prs']} pull requests, {stats['stars']} stars earned, {stats['repos']} public repos")
    return (
        svg_open(w, h, "GitHub activity", desc)
        + surface(w, h, 16, accent=(LEAF, BLUE))
        + badge("GITHUB ACTIVITY", LEAF)
        + f'<text x="36" y="118" font-size="50" font-weight="800" fill="{TEXT}" letter-spacing="-1">{fmt(stats["contributions"])}</text>'
        + f'<text x="36" y="142" font-size="12.5" fill="{MUTED}">contributions</text>'
        + f'<text x="36" y="159" font-size="12.5" fill="{MUTED}">in the past year</text>'
        + f'<line x1="186" y1="70" x2="186" y2="160" stroke="#fff" stroke-opacity=".15"/>'
        + tile_svg
        + "</svg>"
    )


def render_langs(langs, top):
    w, h = 420, 200
    total = sum(langs.values())
    ranked = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)
    shown = ranked[:top]
    other = total - sum(n for _, n in shown)
    parts = [(name, n / total, LANG_COLORS[i % len(LANG_COLORS)]) for i, (name, n) in enumerate(shown)]
    if other:
        parts.append(("Other", other / total, "#4B5563"))
    bar_x, bar_w, x = 36, w - 72, 36.0
    seg = ""
    for _, frac, color in parts:
        sw = frac * bar_w
        seg += f'<rect x="{x:.2f}" y="66" width="{sw:.2f}" height="10" fill="{color}"/>'
        x += sw
    legend = ""
    for i, (name, frac, color) in enumerate(parts[:top]):
        lx = 36 + (i % 2) * 176
        ly = 108 + (i // 2) * 24
        legend += (
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{color}"/>'
            f'<text x="{lx + 16}" y="{ly}" font-size="13" fill="{TEXT}">{escape(name)}</text>'
            f'<text x="{lx + 160}" y="{ly}" font-size="12.5" fill="{MUTED}" text-anchor="end">{frac * 100:.1f}%</text>'
        )
    desc = "Top languages by code size: " + ", ".join(f"{n} {f * 100:.1f}%" for n, f, _ in parts)
    return (
        svg_open(w, h, "Top languages", desc)
        + surface(w, h, 16, accent=(BLUE, CYAN))
        + badge("TOP LANGUAGES", BLUE)
        + f'<clipPath id="bar"><rect x="{bar_x}" y="66" width="{bar_w}" height="10" rx="5"/></clipPath>'
        + f'<g clip-path="url(#bar)">{seg}</g>'
        + legend
        + "</svg>"
    )


# ---------------------------------------------------------------- README blocks

def attr(s):
    return escape(s, {'"': "&quot;"})


def featured_block(data):
    def cell(entry, i, private):
        src = f"assets/card-{'private' if private else 'public'}-{i}.svg"
        href = "#all-projects" if private else entry["url"]
        alt = f"{entry['title']} — {entry['summary']}"
        return f'<a href="{href}"><img src="{src}" width="49%" alt="{attr(alt)}"></a>'

    pub = "\n".join(cell(e, i + 1, False) for i, e in enumerate(data["public"]))
    pri = "\n".join(cell(e, i + 1, True) for i, e in enumerate(data["private"]))
    return (
        "**🎬 Shipped in public**\n\n"
        f'<p align="center">\n{pub}\n</p>\n\n'
        "**🔒 Building in private**\n\n"
        f'<p align="center">\n{pri}\n</p>'
    )


def hero_block(cfg):
    alt = f"{cfg['name']} — {cfg['roles']}. " + ". ".join(l.rstrip(".") for l in cfg["tagline"]) + "."
    return (
        '<p align="center">\n'
        f'  <a href="https://github.com/{cfg["user"]}"><img src="assets/hero.svg" width="100%" alt="{attr(alt)}"></a>\n'
        "</p>"
    )


def stack_block(cfg):
    def label(k):
        # "DATA & ML" -> "Data and ML": keep 2-letter acronyms, sentence-case the rest.
        words = k.replace("&", "and").split()
        return " ".join(w if len(w) <= 2 or w == "and" else w.capitalize() for w in words)

    alt = "Tech stack. " + " ".join(f"{label(k)}: {', '.join(v)}." for k, v in cfg["stack"].items())
    return (
        '<p align="center">\n'
        f'  <img src="assets/stack.svg" width="100%" alt="{attr(alt)}">\n'
        "</p>"
    )


def projects_block(data):
    def private_line(p):
        head = f"**{p['title']}**"
        if p.get("version"):
            head += f" ({p['version']})"
        if p.get("with"):
            head += f" (w/ [@{p['with']}](https://github.com/{p['with']}))"
        return f"- {head}: {p['summary'].rstrip('.')}. *{' · '.join(p['stack'])}*"

    def cell(s):
        return s.replace("|", "\\|")

    def row(r):
        name = f"[{r['repo']}]({r['url']})" + (f" ({r['label']})" if r.get("label") else "")
        return f"| {cell(name)} | {cell(' · '.join(r['stack']))} | {cell(r['about'])} |"

    private, rows = data["private_all"], data["rows"]
    return (
        '<a name="all-projects"></a>\n'
        "<details>\n"
        f"<summary><b>All projects</b> ({len(private)} private · {len(rows)} public)</summary>\n\n"
        "#### 🔒 Private / in development\n\n"
        + "\n".join(private_line(p) for p in private)
        + "\n\n#### 🌐 Public repos\n\n"
        "| Project | Stack | What it is |\n"
        "|---------|-------|------------|\n"
        + "\n".join(row(r) for r in rows)
        + "\n\n</details>"
    )


def replace_region(text, name, block):
    pattern = re.compile(rf"<!-- {name}:start.*?<!-- {name}:end -->", re.S)
    if not pattern.search(text):
        raise RenderError(f"README is missing the {name}:start/{name}:end markers")
    marked = (f"<!-- {name}:start (generated by scripts/render_profile.py; edit data/profile.yml) -->\n"
              f"{block}\n<!-- {name}:end -->")
    return pattern.sub(lambda _: marked, text)


def check_no_private_names(text, private_repos):
    # Match "owner/name" anywhere, and a bare name of 5+ chars as a whole word, so short
    # common words in project copy don't trip it. Never print the value.
    low = text.lower()
    for repo in private_repos:
        name = repo.split("/")[-1].lower()
        if repo.lower() in low or (len(name) >= 5 and re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", low)):
            raise RenderError("a private repo name would be written to README.md")


def render_readme(text, cfg, data):
    for name, block in (("hero", hero_block(cfg)), ("featured", featured_block(data)),
                        ("projects", projects_block(data)), ("stack", stack_block(cfg))):
        text = replace_region(text, name, block)
    check_no_private_names(text, data["private_repos"])
    return text


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--require-token", action="store_true",
                    help="fail unless PROFILE_TOKEN is set and valid (used in CI)")
    args = ap.parse_args()

    token = os.environ.get("PROFILE_TOKEN") or None
    gh = GitHub(token)
    try:
        if args.require_token:
            if not token:
                raise RenderError("PROFILE_TOKEN is not set")
            try:
                gh.get("/rate_limit")
            except RenderError:
                raise RenderError("PROFILE_TOKEN was rejected") from None

        check_contrast()
        try:
            cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            raise RenderError(f"data/profile.yml is not valid YAML: {e}") from None
        data = gather(cfg, gh)

        out = {
            ASSETS / "hero.svg": render_hero(cfg),
            ASSETS / "stack.svg": render_stack(cfg),
            ASSETS / "stats.svg": render_stats(data["stats"]),
            ASSETS / "langs.svg": render_langs(data["langs"], cfg["languages"].get("top", 6)),
        }
        for i, e in enumerate(data["public"], 1):
            out[ASSETS / f"card-public-{i}.svg"] = render_card(e, private=False)
        for i, e in enumerate(data["private"], 1):
            out[ASSETS / f"card-private-{i}.svg"] = render_card(e, private=True)
        out[README] = render_readme(README.read_text(encoding="utf-8"), cfg, data)
    except RenderError as e:
        print(f"render failed, nothing written: {e}", file=sys.stderr)
        return 1

    ASSETS.mkdir(exist_ok=True)
    changed = 0
    for path, content in out.items():
        content = content if content.endswith("\n") else content + "\n"
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8", newline="\n")
            changed += 1
            print(f"wrote {path.relative_to(ROOT)}")
    titles = ", ".join(e["title"] for e in data["public"] + data["private"])
    print(f"featured: {titles}; {changed} file(s) changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
