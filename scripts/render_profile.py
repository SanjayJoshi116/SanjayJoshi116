"""Render the profile README's card SVGs from data/profile.yml and the GitHub API.

Usage:
    python scripts/render_profile.py [--require-token]
    python scripts/render_profile.py --fingerprint PATH

Env:
    PROFILE_TOKEN  optional fine-grained read-only PAT. Enables private-repo
                   rotation and private language bytes for allowlisted repos.

Everything is fetched and rendered in memory first; files are written only if
every step succeeds, so a failed run never leaves assets half-updated.
"""

import argparse
import hashlib
import http.client
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "data" / "profile.yml"
ASSETS = ROOT / "assets"
README = ROOT / "README.md"
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
        elif text_w(w, size, avg=0.52) > max_w:
            raise RenderError(f"the word {w!r} is too wide for its text box; shorten it")
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
    intro = wrap(cfg["intro"], 17, 360, 4)

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
        detail = wrap(s["detail"], 11.5, inner, 9)
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
        "**Shipped in public**\n\n"
        f'<p align="center">\n{pub}\n</p>\n\n'
        "**Building in private**\n\n"
        f'<p align="center">\n{pri}\n</p>'
    )


def hero_block(cfg, data):
    peak = max(n for _, n in weekly(data["days"]))
    alt = (f"{cfg['name']}. {cfg['intro']} Chart: {fmt(data['stats']['contributions'])} contributions "
           f"in the past year, peaking at {peak} in one week.")
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
        if "members" in r:
            name = f"**{r['title']}**<br>" + " · ".join(f"[{m['repo']}]({m['url']})" for m in r["members"])
        else:
            name = f"[{r['repo']}]({r['url']})" + (f" ({r['label']})" if r.get("label") else "")
        return f"| {cell(name)} | {cell(' · '.join(r['stack']))} | {cell(r['about'])} |"

    # Public count is per repository, so a group adds one per member.
    private, rows = data["private_all"], data["rows"]
    return (
        '<a name="all-projects"></a>\n'
        "<details>\n"
        f"<summary><b>All projects</b> ({len(private)} private · {data['stats']['repos']} public)</summary>\n\n"
        "#### Private, in development\n\n"
        + "\n".join(private_line(p) for p in private)
        + "\n\n#### Public repos\n\n"
        "| Project | Stack | What it is |\n"
        "|---------|-------|------------|\n"
        + "\n".join(row(r) for r in rows)
        + "\n\n</details>"
    )


def activity_block(cfg, data):
    alt_l = langs_alt(data["langs"], cfg["languages"].get("top", 6))
    return (
        '<p align="center">\n'
        f'  <img src="assets/stats.svg" width="49%" alt="{attr(stats_alt(data["stats"]))}">\n'
        f'  <img src="assets/langs.svg" width="49%" alt="{attr(alt_l)}">\n'
        "</p>"
    )


def pulse_block(data, now):
    if not data["pulse"]:
        return ""
    alt = pulse_alt(data["pulse"], now)
    return f'<p align="center">\n  <img src="assets/pulse.svg" width="100%" alt="{attr(alt)}">\n</p>'


def diagram_block(data):
    d = data["diagram"]
    if not d:
        return ""
    return (
        f"<details>\n<summary><b>How {escape(d['title'])} works</b></summary>\n\n"
        f'<p align="center">\n  <img src="assets/pipeline.svg" width="100%" alt="{attr(diagram_alt(d))}">\n</p>\n\n'
        "</details>"
    )


def connect_block(cfg):
    links = "\n".join(
        f'  <a href="{attr(e["url"])}"><img src="assets/connect-{slug(e["label"])}.svg" height="44" '
        f'alt="{attr(e["label"])}"></a>'
        for e in cfg["connect"]
    )
    return f'<p align="center">\n{links}\n</p>'


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


def render_readme(text, cfg, data, now):
    pulse = None if data["pulse"] is None else pulse_block(data, now)
    for name, block in (("hero", hero_block(cfg, data)), ("featured", featured_block(data)), ("pulse", pulse),
                        ("diagram", diagram_block(data)),
                        ("projects", projects_block(data)), ("stack", stack_block(cfg)),
                        ("activity", activity_block(cfg, data)), ("connect", connect_block(cfg))):
        text = replace_region(text, name, block)
    check_no_private_names(text, data["private_repos"])
    return text


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
        repos = gh.get(f"/users/{cfg['user']}/repos?per_page=100&type=owner", auth=False)
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
        if data["diagram"]:
            diagram_svg = render_diagram(data["diagram"])
            check_no_private_names(diagram_svg, data["private_repos"], "assets/pipeline.svg")
            out[ASSETS / "pipeline.svg"] = diagram_svg
        else:
            out[ASSETS / "pipeline.svg"] = None
        out[README] = render_readme(README.read_text(encoding="utf-8"), cfg, data, now)
    except RenderError as e:
        print(f"render failed, nothing written: {e}", file=sys.stderr)
        return 1

    ASSETS.mkdir(exist_ok=True)
    changed = 0
    for path, content in out.items():
        if content is None:
            if path.exists():
                path.unlink()
                changed += 1
                print(f"removed {path.relative_to(ROOT)}")
            continue
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
