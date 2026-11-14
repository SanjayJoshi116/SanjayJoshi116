"""Render the profile README's card SVGs from data/profile.yml and the GitHub API.

Usage:
    python scripts/render_profile.py [--require-token] [--site]
    python scripts/render_profile.py --fingerprint PATH

--site also builds the GitHub Pages landing site in site/ (needs Pillow).

Env:
    PROFILE_TOKEN  optional fine-grained read-only PAT. Enables private-repo
                   rotation and private language bytes for allowlisted repos.

Everything is fetched and rendered in memory first; files are written only if
every step succeeds, so a failed run never leaves assets half-updated.
"""

import argparse
import hashlib
import html
import http.client
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from xml.sax.saxutils import escape

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "data" / "profile.yml"
ASSETS = ROOT / "assets"
README = ROOT / "README.md"
SITE = ROOT / "site"
PILLOW_PIN = "pillow==13.0.0"
API = "https://api.github.com"
# Pulse ages count calendar days here, matching the IST schedule in render-profile.yml (no DST).
IST = timezone(timedelta(hours=5, minutes=30))

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

# Landing page themes (--site). Cards stay dark SVGs in both; these colour the page around them.
PAGE = {
    "light": {"bg": "#FFFFFF", "text": "#1F2328", "muted": "#59636E", "link": "#0969DA", "line": "#D1D9E0"},
    "dark": {"bg": "#0D1117", "text": TEXT, "muted": MUTED, "link": BLUE, "line": "#30363D"},
}

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
        except (OSError, http.client.HTTPException) as e:
            # Read timeouts and dropped connections surface outside URLError.
            raise RenderError(f"network error: {type(e).__name__}") from None

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


def card_repos(cfg):
    """Private card repos in file order; empty unless every card names one, since rotation needs them all."""
    repos = [(p["card"] or {}).get("repo") for p in cfg["projects"]["private"] if "card" in p]
    return repos if repos and all(repos) else []


def watched_public(cfg, repos):
    """Public repos whose pushes can change the render: not forks, not hidden (unless featured),
    and not the profile repo, whose own asset commits would otherwise re-trigger every poll."""
    user = cfg["user"].lower()
    hidden = set(cfg["projects"]["public"].get("hide") or []) - {e["repo"] for e in cfg["featured"]["public"]}
    return [r for r in repos if not r["fork"] and r["name"] not in hidden and r["name"].lower() != user]


PUBLIC_REPOS_QUERY = """{ user(login: %s) { repositories(first: 100, after: %s, privacy: PUBLIC,
  ownerAffiliations: [OWNER]) { pageInfo { hasNextPage endCursor } nodes { name isFork isPrivate
  stargazerCount pushedAt createdAt url description primaryLanguage { name } } } } }"""


def public_repos(gh, user):
    """Every public repo the user owns, in the REST repo shape gather() reads.

    With a token: GraphQL with privacy: PUBLIC, so GitHub filters server side and no
    private repo is ever returned (never enumerate them), while the calls count against
    the token's limit instead of the shared runner IP's 60/hr. Without a token, or if
    GitHub rejects it (HTTP 401), the unauthenticated REST listing, which only ever
    returns public repos. Both paths page through everything; the isPrivate/private
    check is a second guard, not the filter.
    """
    if gh.token:
        try:
            repos, cursor = [], None
            while True:
                q = PUBLIC_REPOS_QUERY % (json.dumps(user), json.dumps(cursor))
                page = gh.graphql(q)["user"]["repositories"]
                for n in page["nodes"]:
                    if n["isPrivate"]:
                        continue
                    repos.append({"name": n["name"], "fork": n["isFork"], "private": False,
                                  "stargazers_count": n["stargazerCount"],
                                  "pushed_at": n["pushedAt"] or n["createdAt"], "html_url": n["url"],
                                  "description": n["description"],
                                  "language": (n["primaryLanguage"] or {}).get("name")})
                if not page["pageInfo"]["hasNextPage"]:
                    return repos
                cursor = page["pageInfo"]["endCursor"]
        except RenderError as e:
            if not str(e).startswith("HTTP 401"):
                raise
    repos, n = [], 1
    while True:
        batch = gh.get(f"/users/{user}/repos?per_page=100&type=owner&page={n}", auth=False)
        repos += [r for r in batch if not r.get("private", True)]
        if len(batch) < 100:
            return repos
        n += 1


def gather(cfg, gh):
    user = cfg["user"]
    repos = {r["name"]: r for r in public_repos(gh, user)}
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
    if gh.token and card_repos(cfg):
        for i, e in enumerate(private):
            try:
                r = gh.get(f"/repos/{e['repo']}")
            except RenderError:
                raise RenderError(f"private allowlist entry #{i + 1} is not readable with the token") from None
            e["pushed"] = r["pushed_at"]
            private_repos.append(e["repo"])
        private.sort(key=lambda e: e["pushed"], reverse=True)
    # System diagram: at most one private project carries one; copy only, no API data.
    with_diagram = [p for p in cfg["projects"]["private"] if p.get("diagram")]
    if len(with_diagram) > 1:
        raise RenderError("only one private project may have a diagram")
    diagram = None
    if with_diagram:
        stages = with_diagram[0]["diagram"].get("stages") or []
        if not 3 <= len(stages) <= 6:
            raise RenderError(f"a diagram needs 3 to 6 stages, found {len(stages)}")
        for i, s in enumerate(stages):
            if not (isinstance(s, dict) and s.get("title") and s.get("detail")):
                raise RenderError(f"diagram stage {i + 1} needs a title and a detail")
        diagram = {"title": with_diagram[0]["title"], "stages": stages}

    # Pulse rows: every card project, newest push first. None without a token (left untouched);
    # empty with a token but no card repos (region and pulse.svg removed).
    if private_repos:
        pulse = [{k: e[k] for k in ("title", "version", "pushed")} for e in private]
    else:
        pulse = [] if gh.token else None

    # All projects table: curated rows in file order, then any other public repo from the API.
    pub_cfg = cfg["projects"]["public"]
    hidden = set(pub_cfg.get("hide") or [])
    groups = pub_cfg.get("groups") or []
    for i, g in enumerate(groups):
        missing = [k for k in ("title", "stack", "about", "repos") if not g.get(k)]
        if missing:
            raise RenderError(f"public group #{i + 1} is missing {', '.join(missing)}")
    listed = [e["repo"] for e in pub_cfg.get("repos") or []] + [n for g in groups for n in g["repos"]]
    dup = sorted(n for n, c in Counter(listed).items() if c > 1)
    if dup:
        raise RenderError(f"public repo listed more than once in data/profile.yml: {', '.join(dup)}")
    rows, seen = [], set()
    for entry in pub_cfg.get("repos") or []:
        r = repos.get(entry["repo"])
        if r and not r["fork"] and entry["repo"] not in hidden:
            rows.append({**entry, "url": r["html_url"]})
            seen.add(entry["repo"])
    seen.update(n for g in groups for n in g["repos"])
    # Same filter the poll watches, so a repo shown here is one whose pushes trigger a render.
    extra = [r for r in watched_public(cfg, own) if r["name"] not in seen | hidden]
    for r in sorted(extra, key=lambda r: r["pushed_at"], reverse=True):
        about = (r["description"] or "").split(". ")[0].strip().rstrip(".")
        rows.append({"repo": r["name"], "url": r["html_url"], "stack": [r["language"]] if r["language"] else [],
                     "about": about if len(about) <= 100 else about[:99].rstrip() + "…"})
    # Groups: one row each, after every individual row; missing or hidden members are skipped.
    for g in groups:
        members = [{"repo": n, "url": repos[n]["html_url"]} for n in g["repos"]
                   if n in repos and not repos[n]["fork"] and n not in hidden]
        if members:
            rows.append({"title": g["title"], "members": members, "stack": g["stack"], "about": g["about"]})

    # Stats. Daily contribution counts feed the hero chart; the total is their sum.
    if gh.token:
        q = ('{ user(login: "%s") { contributionsCollection { contributionCalendar '
             '{ weeks { contributionDays { date contributionCount } } } } } }' % user)
        cal = gh.graphql(q)["user"]["contributionsCollection"]["contributionCalendar"]
        days = sorted((d["date"], d["contributionCount"]) for w in cal["weeks"] for d in w["contributionDays"])
    else:
        page = gh.html(f"https://github.com/users/{user}/contributions")
        ids = re.findall(r'data-date="([\d-]+)" id="(contribution-day-component-[\d-]+)"', page)
        tips = dict(re.findall(r'for="(contribution-day-component-[\d-]+)"[^>]*>([^<]*)', page))
        days = []
        for date, cid in ids:
            tip = tips.get(cid, "")
            m = re.match(r"(\d+) contributions?", tip)
            if not m and not tip.startswith("No contributions"):
                raise RenderError("could not read contribution calendar")
            days.append((date, int(m.group(1)) if m else 0))
        days.sort()
    if len(days) < 14:
        raise RenderError("could not read contribution calendar")
    stats = {
        "contributions": sum(n for _, n in days),
        "commits": gh.get(f"/search/commits?q=author:{user}&per_page=1")["total_count"],
        "prs": gh.get(f"/search/issues?q=author:{user}+type:pr&per_page=1")["total_count"],
        "stars": sum(r["stargazers_count"] for r in own),
        "repos": sum(len(r.get("members", [r])) for r in rows),
    }

    # Languages: listed public repos plus allowlisted private repos (aggregate only).
    exclude = set(cfg["languages"].get("exclude", []))
    totals = {}
    sources = ([f"/repos/{user}/{r['name']}/languages" for r in own if r["name"] not in hidden]
               + [f"/repos/{p}/languages" for p in private_repos])
    for src in sources:
        for lang, n in gh.get(src).items():
            if lang not in exclude:
                totals[lang] = totals.get(lang, 0) + n
    if not totals:
        raise RenderError("no language data")

    return {"public": public[:2], "private": private[:2], "stats": stats, "langs": totals, "days": days,
            "rows": rows, "private_all": cfg["projects"]["private"], "pulse": pulse, "diagram": diagram,
            "private_repos": [e["repo"] for e in private_cfg if e.get("repo")]}


# ---------------------------------------------------------------- contrast

def _rgb(hex_color):
    return tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))


def _lum(hex_or_rgb):
    rgb = hex_or_rgb if isinstance(hex_or_rgb, tuple) else _rgb(hex_or_rgb)
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _ratio(fg, bg):
    l1, l2 = sorted((_lum(fg), _lum(bg)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def check_contrast():
    """Every text colour against the background it sits on: the flat card surface (SVGs and
    og.png) and each landing-page theme."""
    # Violet is decorative only (accent lines, language bar); it's not used for text.
    surfaces = [("card", SURFACE, (TEXT, MUTED, BLUE, LEAF, AMBER, CYAN))]
    surfaces += [(f"page {t}", c["bg"], (c["text"], c["muted"], c["link"])) for t, c in PAGE.items()]
    worst = {f"{name} {fg}": _ratio(fg, bg) for name, bg, fgs in surfaces for fg in fgs}
    failing = {k: round(v, 2) for k, v in worst.items() if v < 4.5}
    if failing:
        raise RenderError(f"text contrast below 4.5:1: {failing}")
    return worst


# ---------------------------------------------------------------- SVG helpers

def text_w(s, size, bold=False, avg=0.56):
    # avg is a deliberately wide per-char estimate so overflow checks hold across system fonts
    return len(s) * size * (0.6 if bold else avg)


def svg_measure(size):
    """Estimated width of SVG copy at `size`, for wrap()."""
    return lambda s: text_w(s, size, avg=0.52)


def wrap(s, measure, max_w, max_lines, box="its text box"):
    """Wrap by `measure(text) -> width`. A single word wider than the box fails; too many
    lines end with '…', dropping words until the last line still fits."""
    words, lines, cur = s.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if measure(trial) <= max_w:
            cur = trial
        elif measure(w) > max_w:
            raise RenderError(f"the word {w!r} is too wide for {box}; shorten it")
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1].split()
        while True:
            line = " ".join(last).rstrip(" ,.;") + "…"
            if not last or measure(line) <= max_w:
                break
            last.pop()
        lines[-1] = line
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
        f'<text x="{x + 14}" y="{y}" font-size="12.5" font-weight="600" fill="{color}">{label}</text>'
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

MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def weekly(days):
    """Daily (date, count) pairs, oldest first, summed into weeks; the last week may be partial."""
    return [(days[i][0], sum(n for _, n in days[i:i + 7])) for i in range(0, len(days), 7)]


def render_hero(cfg, stats, days):
    w, h = 840, 260
    intro = wrap(cfg["intro"], svg_measure(17), 360, 4)

    # Contribution chart: weekly totals drawn like a price line.
    weeks = weekly(days)
    x0, x1, top, base = 470, 800, 92, 196
    peak = max(n for _, n in weeks) or 1
    step = (x1 - x0) / (len(weeks) - 1)
    pts = [(x0 + i * step, base - n / peak * (base - top)) for i, (_, n) in enumerate(weeks)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{x0},{base} {line} {x1},{base}"
    lx, ly = pts[-1]
    start_label = f"{MONTHS[int(weeks[0][0][5:7]) - 1]} {weeks[0][0][:4]}"

    # The base styles are the final frame, so renderers that skip animation still show the full chart.
    css = (
        ".ln{stroke-dasharray:1;animation:draw 1.8s cubic-bezier(.3,.7,.2,1) both}"
        "@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}"
        ".fd{animation:fade .6s 1.4s ease-out both}@keyframes fade{from{opacity:0}}"
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
    )
    desc = f"{cfg['intro']} {fmt(stats['contributions'])} contributions in the past year, peaking at {peak} in one week."
    return (
        svg_open(w, h, cfg["name"], desc, css)
        + surface(w, h, 20, accent=(BLUE, LEAF))
        + f'<text x="40" y="96" font-size="44" font-weight="800" fill="{TEXT}" letter-spacing="-1.2">'
          f'{escape(cfg["name"])}</text>'
        + "".join(
            f'<text x="40" y="{138 + i * 26}" font-size="17" fill="{MUTED}">{escape(l)}</text>'
            for i, l in enumerate(intro)
        )
        + f'<text x="{x0}" y="56" font-size="14" fill="{MUTED}">'
          f'<tspan font-weight="700" fill="{TEXT}">{fmt(stats["contributions"])}</tspan> contributions in the past year</text>'
        + f'<line x1="{x0}" y1="{top}" x2="{x1}" y2="{top}" stroke="#fff" stroke-opacity=".14" stroke-dasharray="3 4"/>'
        + f'<text x="{x1}" y="{top - 8}" font-size="11.5" fill="{MUTED}" text-anchor="end">peak {peak} a week</text>'
        + f'<line x1="{x0}" y1="{base}" x2="{x1}" y2="{base}" stroke="#fff" stroke-opacity=".2"/>'
        + f'<polygon class="fd" points="{area}" fill="{LEAF}" fill-opacity=".09"/>'
        + f'<polyline class="ln" pathLength="1" points="{line}" fill="none" stroke="{LEAF}" stroke-width="2" '
          f'stroke-linejoin="round" stroke-linecap="round"/>'
        + f'<g class="fd"><circle cx="{lx:.1f}" cy="{ly:.1f}" r="7" fill="{LEAF}" fill-opacity=".2"/>'
          f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="3.5" fill="{LEAF}"/></g>'
        + f'<text x="{x0}" y="218" font-size="11.5" fill="{MUTED}">{start_label}</text>'
        + f'<text x="{x1}" y="218" font-size="11.5" fill="{MUTED}" text-anchor="end">This week</text>'
        + "</svg>"
    )


def render_card(entry, private):
    w, h = 420, 200
    if private:
        label, color, accent = "Private, in development", AMBER, (AMBER, VIOLET)
        corner = entry["version"]
    else:
        label, color, accent = "Public repo", BLUE, (BLUE, VIOLET)
        corner = f"★ {entry['stars']}"
    summary = wrap(entry["summary"], svg_measure(13.5), w - 72, 2)
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
        x = 36 + (i % 2) * 176
        y = 100 + (i // 2) * 58
        tile_svg += (
            f'<text x="{x}" y="{y}" font-size="30" font-weight="800" fill="{TEXT}" letter-spacing="-.6">{fmt(stats[key])}</text>'
            f'<text x="{x}" y="{y + 20}" font-size="12.5" fill="{MUTED}">{label}</text>'
        )
    return (
        svg_open(w, h, "GitHub activity", stats_alt(stats))
        + surface(w, h, 16, accent=(LEAF, BLUE))
        + badge("GitHub activity", LEAF)
        + tile_svg
        + "</svg>"
    )


def stats_alt(stats):
    return (f"GitHub activity: {fmt(stats['commits'])} public commits, {fmt(stats['prs'])} pull requests, "
            f"{fmt(stats['stars'])} stars earned, {fmt(stats['repos'])} public repos.")


def lang_shares(langs, top):
    """(name, share, colour) for the top languages plus Other; one source for the card and its alt text."""
    total = sum(langs.values())
    ranked = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)
    shown = ranked[:top]
    other = total - sum(n for _, n in shown)
    parts = [(name, n / total, LANG_COLORS[i % len(LANG_COLORS)]) for i, (name, n) in enumerate(shown)]
    if other:
        parts.append(("Other", other / total, "#4B5563"))
    return parts


def langs_alt(langs, top):
    return "Top languages by code size: " + ", ".join(f"{n} {f * 100:.1f}%" for n, f, _ in lang_shares(langs, top)) + "."


def render_langs(langs, top):
    w, h = 420, 200
    parts = lang_shares(langs, top)
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
    return (
        svg_open(w, h, "Top languages", langs_alt(langs, top))
        + surface(w, h, 16, accent=(BLUE, CYAN))
        + badge("Top languages", BLUE)
        + f'<clipPath id="bar"><rect x="{bar_x}" y="66" width="{bar_w}" height="10" rx="5"/></clipPath>'
        + f'<g clip-path="url(#bar)">{seg}</g>'
        + legend
        + "</svg>"
    )


def pulse_age(pushed, now):
    """(days, short, long) for a pushed_at timestamp, bucketed so the strip never shows a raw date."""
    # Python < 3.11 can't parse a trailing "Z"; `now` is IST, so days are IST calendar days.
    pushed_at = datetime.fromisoformat(pushed.replace("Z", "+00:00")).astimezone(now.tzinfo)
    days = max(0, (now.date() - pushed_at.date()).days)
    if days == 0:
        return days, "today", "today"
    for limit, unit, size in ((14, "d", 1), (63, "w", 7), (None, "mo", 30)):
        if limit is None or days < limit:
            n = days // size
            word = {"d": "day", "w": "week", "mo": "month"}[unit]
            return days, f"{n}{unit} ago", f"{n} {word}{'s' if n != 1 else ''} ago"


def pulse_alt(rows, now):
    return "Private work, last active: " + ", ".join(f"{r['title']} {pulse_age(r['pushed'], now)[2]}" for r in rows)


def render_pulse(rows, now):
    """One row per private card project: recency dot, title, version, relative age. No repo data."""
    w, top, row_h = 860, 60, 30
    h = top + row_h * len(rows) + 6
    body = f'<text x="36" y="38" font-size="13" font-weight="600" fill="{MUTED}">Private work, last active</text>'
    # Reserve room for the widest age label, so copy that fits today can't start overlapping as ages grow.
    age_left = w - 36 - text_w("active 99mo ago", 13)
    for i, r in enumerate(rows):
        y = top + i * row_h
        days, short, _ = pulse_age(r["pushed"], now)
        dot = LEAF if days <= 7 else CYAN if days <= 30 else MUTED
        version_x = 56 + text_w(r["title"], 14, True) + 10
        if version_x + text_w(r["version"], 12, avg=0.6) + 16 > age_left:
            raise RenderError(f"pulse row {i + 1} title and version are too long; shorten them")
        body += (
            f'<circle cx="40.5" cy="{y - 4.5}" r="4.5" fill="{dot}"/>'
            f'<text x="56" y="{y}" font-size="14" font-weight="600" fill="{TEXT}">{escape(r["title"])}</text>'
            f'<text x="{version_x:.0f}" y="{y}" class="m" font-size="12" fill="{MUTED}">{escape(r["version"])}</text>'
            f'<text x="{w - 36}" y="{y}" font-size="13" fill="{TEXT}" text-anchor="end">active {short}</text>'
        )
    return (
        svg_open(w, h, "Private work, last active", pulse_alt(rows, now))
        + surface(w, h, 16, accent=(AMBER, VIOLET), edge=AMBER)
        + body
        + "</svg>"
    )


def diagram_alt(diagram):
    steps = ", then ".join(f"{s['title']} ({s['detail']})" for s in diagram["stages"])
    return f"{diagram['title']} daily flow: {steps}"


def render_diagram(diagram):
    """Stage boxes in one row joined by arrows. Text that doesn't fit fails the run, never truncates."""
    stages = diagram["stages"]
    w, h, m, gap, top, box_h = 860, 148, 36, 24, 52, 76
    n = len(stages)
    bw = (w - 2 * m - gap * (n - 1)) / n
    inner = bw - 16
    body = f'<text x="{m}" y="34" font-size="13" font-weight="600" fill="{MUTED}">How {escape(diagram["title"])} works</text>'
    for i, s in enumerate(stages):
        if text_w(s["title"], 13, True) > inner:
            raise RenderError(f"diagram stage {i + 1} title does not fit on one line")
        detail = wrap(s["detail"], svg_measure(11.5), inner, 9)
        if len(detail) > 2:
            raise RenderError(f"diagram stage {i + 1} detail does not fit on two lines")
        x = m + i * (bw + gap)
        body += (
            f'<rect x="{x:.1f}" y="{top}" width="{bw:.1f}" height="{box_h}" rx="10" fill="#fff" fill-opacity=".04" '
            f'stroke="#fff" stroke-opacity=".16"/>'
            f'<text x="{x + 8:.1f}" y="{top + 24}" font-size="13" font-weight="600" fill="{TEXT}">{escape(s["title"])}</text>'
            + "".join(f'<text x="{x + 8:.1f}" y="{top + 44 + j * 15}" font-size="11.5" fill="{MUTED}">{escape(line)}</text>'
                      for j, line in enumerate(detail))
        )
        if i < n - 1:
            ax, ay = x + bw + 4, top + box_h / 2
            body += (f'<path d="M{ax:.1f} {ay}h{gap - 8}" stroke="{BLUE}" stroke-width="2"/>'
                     f'<path d="M{ax + gap - 13:.1f} {ay - 4}l5 4l-5 4" fill="none" stroke="{BLUE}" stroke-width="2"/>')
    return (
        svg_open(w, h, f"How {diagram['title']} works", diagram_alt(diagram))
        + surface(w, h, 16, accent=(AMBER, VIOLET), edge=AMBER)
        + body
        + "</svg>"
    )


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def render_connect_button(entry):
    """Flat text button; the accent colour marks the dot and top line only, never text."""
    w, h = 180, 44
    label = entry["label"]
    # Amber marks private work only; off-palette colours break the card style.
    if entry["color"].upper() not in (BLUE, LEAF, VIOLET, CYAN):
        raise RenderError(f"connect colour for {label!r} must be Blue, Leaf, Violet or Cyan")
    if text_w(label, 14, True) > w - 56:
        raise RenderError(f"connect label {label!r} is too long")
    return (
        svg_open(w, h, label, f"{label}: {entry['url']}")
        + surface(w, h, 12, accent=(entry["color"], entry["color"]))
        + f'<circle cx="24" cy="22" r="4.5" fill="{entry["color"]}"/>'
        + f'<text x="38" y="27" font-size="14" font-weight="600" fill="{TEXT}">{escape(label)}</text>'
        + "</svg>"
    )


# ---------------------------------------------------------------- README blocks

def attr(s):
    """Escape for HTML text and double-quoted attributes, in the README and the site."""
    return escape(str(s), {'"': "&quot;"})


PROJECTS_ID = "all-projects"  # anchor of the All projects section, README and site


def card_name(i, private):
    return f"card-{'private' if private else 'public'}-{i}.svg"


def featured_cards(data):
    """Featured sections as (heading, [(href, asset name)]), shared by the README and the site.
    Private cards never link to their repo, only to the All projects section."""
    return [
        ("Shipped in public", [(e["url"], card_name(i, False)) for i, e in enumerate(data["public"], 1)]),
        ("Building in private", [(f"#{PROJECTS_ID}", card_name(i, True)) for i, e in enumerate(data["private"], 1)]),
    ]


def chart_alt(data):
    peak = max(n for _, n in weekly(data["days"]))
    return (f"Chart: {fmt(data['stats']['contributions'])} contributions in the past year, "
            f"peaking at {peak} in one week.")


def stack_alt(cfg):
    def label(k):
        # "DATA & ML" -> "Data and ML": keep 2-letter acronyms, sentence-case the rest.
        words = k.replace("&", "and").split()
        return " ".join(w if len(w) <= 2 or w == "and" else w.capitalize() for w in words)

    return "Tech stack. " + " ".join(f"{label(k)}: {', '.join(v)}." for k, v in cfg["stack"].items())


def asset_alts(cfg, data, now):
    """Alt text for every asset this run renders, keyed by file name; the README and the site
    both use it. A pulse.svg left untouched (no token) is not here: the site reads its <desc>."""
    alts = {
        "hero.svg": f"{cfg['name']}. {cfg['intro']} {chart_alt(data)}",
        "stack.svg": stack_alt(cfg),
        "stats.svg": stats_alt(data["stats"]),
        "langs.svg": langs_alt(data["langs"], cfg["languages"].get("top", 6)),
    }
    for private in (False, True):
        for i, e in enumerate(data["private" if private else "public"], 1):
            alts[card_name(i, private)] = f"{e['title']} — {e['summary']}"
    for e in cfg["connect"]:
        alts[f"connect-{slug(e['label'])}.svg"] = e["label"]
    if data["pulse"]:
        alts["pulse.svg"] = pulse_alt(data["pulse"], now)
    if data["diagram"]:
        alts["pipeline.svg"] = diagram_alt(data["diagram"])
    return alts


def project_counts(data):
    # Public count is per repository, so a group adds one per member.
    return f"{len(data['private_all'])} private · {data['stats']['repos']} public"


# Inline markup for the All projects entries: one row model, written as Markdown for the
# README and as HTML for the site, so the two can't drift apart.
MARKDOWN = {
    "text": lambda s: s,
    "bold": lambda s: f"**{s}**",
    "em": lambda s: f"*{s}*",
    "link": lambda text, href: f"[{text}]({href})",
}
HTML = {
    "text": attr,
    "bold": lambda s: f"<strong>{attr(s)}</strong>",
    "em": lambda s: f'<em class="muted">{attr(s)}</em>',
    "link": lambda text, href: f'<a href="{attr(href)}">{attr(text)}</a>',
}


def private_entry(p, m):
    head = m["bold"](p["title"])
    if p.get("version"):
        head += f" ({m['text'](p['version'])})"
    if p.get("with"):
        head += f" (w/ {m['link']('@' + p['with'], 'https://github.com/' + p['with'])})"
    return f"{head}: {m['text'](p['summary'].rstrip('.'))}. {m['em'](' · '.join(p['stack']))}"


def public_cells(r, m):
    """(project, stack, about) cells of one public row: a repo, or a group of repos."""
    if "members" in r:
        name = m["bold"](r["title"]) + "<br>" + " · ".join(m["link"](x["repo"], x["url"]) for x in r["members"])
    else:
        name = m["link"](r["repo"], r["url"]) + (f" ({m['text'](r['label'])})" if r.get("label") else "")
    return name, m["text"](" · ".join(r["stack"])), m["text"](r["about"])


def featured_block(data, alts):
    def cell(href, name):
        return f'<a href="{attr(href)}"><img src="assets/{name}" width="49%" alt="{attr(alts[name])}"></a>'

    return "\n\n".join(
        f"**{heading}**\n\n" + '<p align="center">\n' + "\n".join(cell(*c) for c in cards) + "\n</p>"
        for heading, cards in featured_cards(data)
    )


def hero_block(cfg, alts):
    return (
        '<p align="center">\n'
        f'  <a href="https://github.com/{cfg["user"]}"><img src="assets/hero.svg" width="100%" '
        f'alt="{attr(alts["hero.svg"])}"></a>\n'
        "</p>"
    )


def stack_block(alts):
    return (
        '<p align="center">\n'
        f'  <img src="assets/stack.svg" width="100%" alt="{attr(alts["stack.svg"])}">\n'
        "</p>"
    )


def projects_block(data):
    def row(r):
        return "| " + " | ".join(c.replace("|", "\\|") for c in public_cells(r, MARKDOWN)) + " |"

    return (
        f'<a name="{PROJECTS_ID}"></a>\n'
        "<details>\n"
        f"<summary><b>All projects</b> ({project_counts(data)})</summary>\n\n"
        "#### Private, in development\n\n"
        + "\n".join("- " + private_entry(p, MARKDOWN) for p in data["private_all"])
        + "\n\n#### Public repos\n\n"
        "| Project | Stack | What it is |\n"
        "|---------|-------|------------|\n"
        + "\n".join(row(r) for r in data["rows"])
        + "\n\n</details>"
    )


def activity_block(alts):
    return (
        '<p align="center">\n'
        f'  <img src="assets/stats.svg" width="49%" alt="{attr(alts["stats.svg"])}">\n'
        f'  <img src="assets/langs.svg" width="49%" alt="{attr(alts["langs.svg"])}">\n'
        "</p>"
    )


def pulse_block(data, alts):
    if not data["pulse"]:
        return ""
    return f'<p align="center">\n  <img src="assets/pulse.svg" width="100%" alt="{attr(alts["pulse.svg"])}">\n</p>'


def diagram_block(data, alts):
    d = data["diagram"]
    if not d:
        return ""
    return (
        f"<details>\n<summary><b>How {attr(d['title'])} works</b></summary>\n\n"
        f'<p align="center">\n  <img src="assets/pipeline.svg" width="100%" alt="{attr(alts["pipeline.svg"])}">\n</p>\n\n'
        "</details>"
    )


def connect_block(cfg, alts):
    links = []
    for e in cfg["connect"]:
        name = f"connect-{slug(e['label'])}.svg"
        links.append(f'  <a href="{attr(e["url"])}"><img src="assets/{name}" height="44" alt="{attr(alts[name])}"></a>')
    return '<p align="center">\n' + "\n".join(links) + "\n</p>"


def replace_region(text, name, block):
    pattern = re.compile(rf"<!-- {name}:start.*?<!-- {name}:end -->", re.S)
    if not pattern.search(text):
        raise RenderError(f"README is missing the {name}:start/{name}:end markers")
    if block is None:  # keep the region as it is; the markers are still required
        return text
    marked = (f"<!-- {name}:start (generated by scripts/render_profile.py; edit data/profile.yml) -->\n"
              f"{block}\n<!-- {name}:end -->")
    return pattern.sub(lambda _: marked, text)


def check_no_private_names(text, private_repos, target="README.md"):
    # Match "owner/name" anywhere, and a bare name of 5+ chars as a whole word, so short
    # common words in project copy don't trip it. Never print the value.
    low = text.lower()
    for repo in private_repos:
        name = repo.split("/")[-1].lower()
        if repo.lower() in low or (len(name) >= 5 and re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", low)):
            raise RenderError(f"a private repo name would be written to {target}")


def render_readme(text, cfg, data, alts):
    pulse = None if data["pulse"] is None else pulse_block(data, alts)
    for name, block in (("hero", hero_block(cfg, alts)), ("featured", featured_block(data, alts)), ("pulse", pulse),
                        ("diagram", diagram_block(data, alts)),
                        ("projects", projects_block(data)), ("stack", stack_block(alts)),
                        ("activity", activity_block(alts)), ("connect", connect_block(cfg, alts))):
        text = replace_region(text, name, block)
    check_no_private_names(text, data["private_repos"])
    return text


# ---------------------------------------------------------------- landing site (--site)

def site_url(cfg):
    url = (cfg.get("site") or {}).get("url")
    if not (isinstance(url, str) and url.startswith("https://") and url.endswith("/") and " " not in url):
        raise RenderError("site.url in data/profile.yml must be an https:// URL ending in /")
    return url


def load_pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise RenderError(f"--site needs Pillow: pip install {PILLOW_PIN}") from None
    return Image, ImageDraw, ImageFont


# Regular + bold pairs, first match wins: Ubuntu runner, Windows, macOS.
OG_FONTS = [
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/segoeuib.ttf"),
    ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
    ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf"),
]


def og_fonts():
    """(regular, bold) font paths for og.png."""
    pair = next((p for p in OG_FONTS if all(Path(f).exists() for f in p)), None)
    if not pair:
        raise RenderError("no font found for og.png (on Ubuntu: apt-get install fonts-dejavu-core)")
    return pair


def render_og(cfg, url, private_repos):
    """1200x630 link-preview PNG: flat dark card with the name, intro and site address."""
    Image, ImageDraw, ImageFont = load_pillow()
    regular, bold = og_fonts()
    w, h, x, max_w = 1200, 630, 80, 1040
    f_name = ImageFont.truetype(bold, 76)
    f_intro = ImageFont.truetype(regular, 36)
    f_url = ImageFont.truetype(regular, 28)
    name, host = cfg["name"], url.split("://", 1)[1].rstrip("/")
    if f_name.getlength(name) > max_w:
        raise RenderError("the name line is too wide for og.png; shorten name in data/profile.yml")
    if f_url.getlength(host) > max_w:
        raise RenderError("the site.url line is too wide for og.png")
    intro = wrap(cfg["intro"], f_intro.getlength, max_w, 4, box="the og.png intro")
    for t in [name, host, *intro]:
        check_no_private_names(t, private_repos, "site/og.png")

    img = Image.new("RGB", (w, h), SURFACE)
    d = ImageDraw.Draw(img)
    # Top accent line, blue to leaf, as on the hero card.
    c1, c2 = _rgb(BLUE), _rgb(LEAF)
    for i in range(w):
        t = i / (w - 1)
        d.line([(i, 0), (i, 5)], fill=tuple(round(a + (b - a) * t) for a, b in zip(c1, c2)))
    d.rectangle([0, 0, w - 1, h - 1], outline=(40, 46, 62))
    d.text((x, 150), name, font=f_name, fill=TEXT)
    for i, line in enumerate(intro):
        d.text((x, 270 + i * 52), line, font=f_intro, fill=MUTED)
    d.text((x, h - 80), host, font=f_url, fill=BLUE)
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def svg_desc(content, name):
    """The alt text an SVG carries as <desc id="d">."""
    m = re.search(r'<desc id="d">(.*?)</desc>', content, re.S)
    if not m:
        raise RenderError(f"assets/{name} has no <desc>; re-render it with a token")
    return html.unescape(m.group(1))


def css_vars(theme):
    return ";".join(f"--{k}:{v}" for k, v in PAGE[theme].items())


SITE_CSS = (
    f":root{{color-scheme:light dark;{css_vars('light')}}}\n"
    f"@media (prefers-color-scheme:dark){{:root{{{css_vars('dark')}}}}}\n"
    f"body{{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 {SANS}}}\n"
) + """
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
main{max-width:880px;margin:0 auto;padding:24px 16px 48px}
a{color:var(--link)}
img{display:block;max-width:100%;height:auto}
h2{font-size:1.15rem;margin:40px 0 12px}
h3{font-size:1rem;margin:24px 0 8px}
.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.grid>a,.grid>img{min-width:0}
.below{margin-top:12px}
.muted{color:var(--muted)}
details{margin-top:24px}
summary{cursor:pointer;font-weight:600}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
.scroll>img{min-width:640px}
ul.private{padding-left:20px}
ul.private li{margin:6px 0}
table{border-collapse:collapse;width:100%;min-width:560px;font-size:.95rem}
th,td{text-align:left;vertical-align:top;padding:8px 10px;border-bottom:1px solid var(--line)}
th{font-weight:600}
.connect{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-top:40px}
.connect img{height:44px;width:auto}
footer{margin-top:40px;font-size:.85rem;text-align:center}
@media (max-width:700px){.grid{grid-template-columns:1fr}}
"""

# Meta tags with fixed values, which carry no profile content and so skip the private-name check.
FIXED_META = [("name", "viewport", "width=device-width,initial-scale=1"), ("name", "color-scheme", "light dark"),
              ("property", "og:type", "website"), ("property", "og:image:width", "1200"),
              ("property", "og:image:height", "630"), ("name", "twitter:card", "summary_large_image")]


class _PageContent(HTMLParser):
    """Collects what a page says, not how it is built: text outside <style> and the href, src,
    alt and content values, minus FIXED_META. Tag names, classes and CSS are skipped, so a
    private repo with a generic name (connect, scroll) only matches real content."""

    FIXED = {n for _, n, _ in FIXED_META}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.in_style = [], False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.in_style = tag == "style"
        if tag == "meta" and (a.get("name") or a.get("property")) in self.FIXED:
            return
        self.parts += [a[k] for k in ("href", "src", "alt", "content") if a.get(k)]

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False

    def handle_data(self, data):
        if not self.in_style:
            self.parts.append(data)


def page_content(page):
    p = _PageContent()
    p.feed(page)
    p.close()
    return "\n".join(p.parts)


def render_site(cfg, data, out, alts):
    """Landing page, preview image and the SVGs it uses, as {path: content}. Writes nothing.
    Assets come only from `out`, this run's render (plus a pulse.svg kept as it was)."""
    url = site_url(cfg)
    files = {}

    def img(name, alt=None):
        content = out.get(ASSETS / name)
        if content is None:
            raise RenderError(f"the site needs assets/{name}, which this run did not render")
        files[SITE / "assets" / name] = content
        alt = alt or alts.get(name) or svg_desc(content, name)
        return f'<img src="assets/{name}" alt="{attr(alt)}">'

    user = attr(cfg["user"])
    # The name and intro are real text here, so the hero's alt only describes the chart.
    parts = [
        f'<header><h1 class="sr-only">{attr(cfg["name"])}</h1><p class="sr-only">{attr(cfg["intro"])}</p>'
        f'<a href="https://github.com/{user}">{img("hero.svg", chart_alt(data))}</a></header>'
    ]

    featured = [f'<h2>{attr(heading)}</h2><div class="grid">'
                + "".join(f'<a href="{attr(href)}">{img(name)}</a>' for href, name in cards) + "</div>"
                for heading, cards in featured_cards(data)]
    if out.get(ASSETS / "pulse.svg"):
        featured.append(f'<div class="below">{img("pulse.svg")}</div>')
    if data["diagram"]:
        featured.append(f"<details><summary>How {attr(data['diagram']['title'])} works</summary>"
                        f'<div class="scroll below">{img("pipeline.svg")}</div></details>')
    parts.append("<section>" + "".join(featured) + "</section>")

    parts.append(
        f'<section><h2 id="{PROJECTS_ID}">All projects <span class="muted">({project_counts(data)})</span></h2>'
        "<h3>Private, in development</h3>"
        '<ul class="private">' + "".join(f"<li>{private_entry(p, HTML)}</li>" for p in data["private_all"]) + "</ul>"
        "<h3>Public repos</h3>"
        '<div class="scroll"><table><thead><tr><th>Project</th><th>Stack</th><th>What it is</th></tr></thead><tbody>'
        + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in public_cells(r, HTML)) + "</tr>" for r in data["rows"])
        + "</tbody></table></div></section>"
    )

    parts.append(f"<section><h2>Stack</h2>{img('stack.svg')}</section>")
    parts.append(f'<section><h2>Activity</h2><div class="grid">{img("stats.svg")}{img("langs.svg")}</div></section>')
    parts.append('<nav class="connect" aria-label="Connect">'
                 + "".join(f'<a href="{attr(e["url"])}">{img("connect-" + slug(e["label"]) + ".svg")}</a>'
                           for e in cfg["connect"])
                 + "</nav>")
    parts.append(f'<footer class="muted">Generated from <a href="https://github.com/{user}/{user}">'
                 f"{user}/{user}</a></footer>")

    title, desc, image = cfg["name"], cfg["intro"], url + "og.png"
    meta = FIXED_META + [
        ("name", "description", desc), ("property", "og:title", title), ("property", "og:description", desc),
        ("property", "og:url", url), ("property", "og:image", image), ("property", "og:image:alt", f"{title}. {desc}"),
        ("name", "twitter:title", title), ("name", "twitter:description", desc), ("name", "twitter:image", image)]
    page = (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        f"<title>{attr(title)}</title>\n"
        f'<link rel="canonical" href="{attr(url)}">\n'
        + "".join(f'<meta {k}="{n}" content="{attr(v)}">\n' for k, n, v in meta)
        + f"<style>{SITE_CSS}</style>\n</head>\n<body>\n<main>\n"
        + "\n".join(parts)
        + "\n</main>\n</body>\n</html>\n"
    )
    check_no_private_names(page_content(page), data["private_repos"], "site/index.html")
    files[SITE / "index.html"] = page
    files[SITE / "og.png"] = render_og(cfg, url, data["private_repos"])
    return files


# ---------------------------------------------------------------- push fingerprint

def fingerprint(path, token):
    """Write a digest of push times for watched repos, plus today's IST date, to `path`.

    The date makes the first poll of each day re-render, so pulse ages move on daily
    even when GitHub delays the daily cron. CI logs are public, so this prints
    nothing: no names, times or digest. Any failure writes "error", which never
    matches a saved digest, so the render runs and reports the problem itself.
    """
    try:
        cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        gh = GitHub(token)
        repos = public_repos(gh, cfg["user"])
        items = sorted(f"{r['name']}\t{r['pushed_at']}" for r in watched_public(cfg, repos))
        items.append(datetime.now(IST).date().isoformat())
        if token:
            # Private repos in file order, by push time only.
            for repo in card_repos(cfg):
                items.append(gh.get(f"/repos/{repo}")["pushed_at"])
        digest = hashlib.sha256("\n".join(items).encode()).hexdigest()
    except Exception:
        digest = "error"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(digest + "\n", encoding="utf-8")
    return 0


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--require-token", action="store_true",
                    help="fail unless PROFILE_TOKEN is set and valid (used in CI)")
    ap.add_argument("--site", action="store_true",
                    help="also build the GitHub Pages landing site in site/ (needs Pillow)")
    ap.add_argument("--fingerprint", type=Path, metavar="PATH",
                    help="write a push-time digest to PATH and exit; renders nothing")
    args = ap.parse_args()

    token = os.environ.get("PROFILE_TOKEN") or None
    if args.fingerprint:
        return fingerprint(args.fingerprint, token)
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
        if args.site:  # fail fast, before any API call
            site_url(cfg)
            load_pillow()
            og_fonts()
        data = gather(cfg, gh)

        out = {
            ASSETS / "hero.svg": render_hero(cfg, data["stats"], data["days"]),
            ASSETS / "stack.svg": render_stack(cfg),
            ASSETS / "stats.svg": render_stats(data["stats"]),
            ASSETS / "langs.svg": render_langs(data["langs"], cfg["languages"].get("top", 6)),
        }
        for i, e in enumerate(data["public"], 1):
            out[ASSETS / f"card-public-{i}.svg"] = render_card(e, private=False)
        for i, e in enumerate(data["private"], 1):
            out[ASSETS / f"card-private-{i}.svg"] = render_card(e, private=True)
        for e in cfg["connect"]:
            out[ASSETS / f"connect-{slug(e['label'])}.svg"] = render_connect_button(e)
        now = datetime.now(IST)
        if data["pulse"]:
            pulse_svg = render_pulse(data["pulse"], now)
            check_no_private_names(pulse_svg, data["private_repos"], "assets/pulse.svg")
            out[ASSETS / "pulse.svg"] = pulse_svg
        elif data["pulse"] is not None:
            out[ASSETS / "pulse.svg"] = None  # None means delete: its README region is now empty
        elif (ASSETS / "pulse.svg").exists():
            # No token: pulse.svg and its README region stay as they are. Rewriting the same
            # content changes nothing, and the site can then mirror it from `out` alone.
            kept = (ASSETS / "pulse.svg").read_text(encoding="utf-8")
            check_no_private_names(kept, data["private_repos"], "assets/pulse.svg")
            out[ASSETS / "pulse.svg"] = kept
        if data["diagram"]:
            diagram_svg = render_diagram(data["diagram"])
            check_no_private_names(diagram_svg, data["private_repos"], "assets/pipeline.svg")
            out[ASSETS / "pipeline.svg"] = diagram_svg
        else:
            out[ASSETS / "pipeline.svg"] = None
        alts = asset_alts(cfg, data, now)
        out[README] = render_readme(README.read_text(encoding="utf-8"), cfg, data, alts)
        if args.site:
            out.update(render_site(cfg, data, out, alts))
    except RenderError as e:
        print(f"render failed, nothing written: {e}", file=sys.stderr)
        return 1

    if args.site:
        # site/ holds exactly this run's files: anything else there is deleted like a removed asset.
        for path in SITE.rglob("*"):
            if path.is_file():
                out.setdefault(path, None)

    ASSETS.mkdir(exist_ok=True)
    changed = 0
    for path, content in out.items():
        if content is None:
            if path.exists():
                path.unlink()
                changed += 1
                print(f"removed {path.relative_to(ROOT)}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            if not path.exists() or path.read_bytes() != content:
                path.write_bytes(content)
                changed += 1
                print(f"wrote {path.relative_to(ROOT)}")
            continue
        content = content if content.endswith("\n") else content + "\n"
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8", newline="\n")
            changed += 1
            print(f"wrote {path.relative_to(ROOT)}")
    if args.site:
        for path in sorted(SITE.rglob("*"), reverse=True):
            if path.is_dir() and not any(path.iterdir()):
                path.rmdir()
    titles = ", ".join(e["title"] for e in data["public"] + data["private"])
    print(f"featured: {titles}; {changed} file(s) changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
