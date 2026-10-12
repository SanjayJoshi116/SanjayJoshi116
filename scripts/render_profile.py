"""Render the profile README's glass SVGs from data/profile.yml and the GitHub API.

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
INK = "#0B1020"
BLUE = "#58A6FF"
LEAF = "#34D399"
VIOLET = "#8B5CF6"
AMBER = "#F5B544"
CYAN = "#22D3EE"
TEXT = "#F0F6FC"
MUTED = "#9DA7B3"
LANG_COLORS = [BLUE, LEAF, VIOLET, CYAN, "#F472B6", "#C9D1D9"]

# Glass recipe; check_contrast() proves text stays AA over the brightest blob.
BLOB_A = 0.6
SCRIM_A = 0.74
FROST_A = 0.06

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

    private_cfg = cfg["featured"]["private"]
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

    return {"public": public[:2], "private": private[:2], "stats": stats, "langs": totals}


# ---------------------------------------------------------------- contrast

def _lum(hex_or_rgb):
    rgb = hex_or_rgb if isinstance(hex_or_rgb, tuple) else tuple(int(hex_or_rgb[i:i + 2], 16) for i in (1, 3, 5))
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _over(top, a, bottom):
    t = tuple(int(top[i:i + 2], 16) for i in (1, 3, 5)) if isinstance(top, str) else top
    b = tuple(int(bottom[i:i + 2], 16) for i in (1, 3, 5)) if isinstance(bottom, str) else bottom
    return tuple(tc * a + bc * (1 - a) for tc, bc in zip(t, b))


def check_contrast():
    """Worst case: text over the un-blurred peak of the brightest blob, through the glass."""
    worst = {}
    for blob in (BLUE, LEAF, VIOLET, AMBER, CYAN):
        bg = _over(blob, BLOB_A, INK)
        bg = _over(INK, SCRIM_A, bg)
        bg = _over("#FFFFFF", FROST_A, bg)
        for fg in (TEXT, MUTED, BLUE, LEAF, VIOLET, AMBER, CYAN):
            l1, l2 = sorted((_lum(fg), _lum(bg)), reverse=True)
            ratio = (l1 + 0.05) / (l2 + 0.05)
            worst[fg] = min(worst.get(fg, 99), ratio)
    # Violet is decorative only (blobs, chips); it's not used for text.
    failing = {k: round(v, 2) for k, v in worst.items() if v < 4.5 and k != VIOLET}
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


def blobs(spec, filt, classes=None):
    out = []
    for i, (cx, cy, r, color) in enumerate(spec):
        cls = f' class="{classes[i]}"' if classes else ""
        out.append(f'<g{cls}><circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" fill-opacity="{BLOB_A}"/></g>')
    return f'<g filter="url(#{filt})">{"".join(out)}</g>'


def glass(w, h, rx, blob_spec, classes=None, accent=(BLUE, VIOLET), edge=None, grid=False):
    """One frosted surface: ink, blurred aurora blobs, scrim, top accent line. Returns defs+background."""
    a1, a2 = accent
    edge_svg = ""
    if edge:
        edge_svg = (
            f'<rect x="1.5" y="1.5" width="{w - 3}" height="{h - 3}" rx="{rx - 1}" fill="none" stroke="{edge}" '
            f'stroke-width="3" stroke-opacity=".45" filter="url(#glow)"/>'
            f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="none" '
            f'stroke="{edge}" stroke-opacity=".7"/>'
        )
    grid_def = grid_svg = ""
    if grid:
        grid_def = ('<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
                    '<circle cx="1.5" cy="1.5" r="1" fill="#fff" fill-opacity=".07"/></pattern>')
        grid_svg = f'<rect width="{w}" height="{h}" fill="url(#dots)"/>'
    return (
        "<defs>"
        f'<clipPath id="frame"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath>'
        '<filter id="frost" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="40"/></filter>'
        '<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="4"/></filter>'
        '<linearGradient id="shine" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#fff" stop-opacity=".07"/><stop offset=".5" stop-color="#fff" stop-opacity="0"/>'
        "</linearGradient>"
        '<linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{a1}" stop-opacity="0"/><stop offset=".25" stop-color="{a1}"/>'
        f'<stop offset=".75" stop-color="{a2}"/><stop offset="1" stop-color="{a2}" stop-opacity="0"/>'
        "</linearGradient>"
        + grid_def
        + "</defs>"
        + '<g clip-path="url(#frame)">'
        + f'<rect width="{w}" height="{h}" fill="{INK}"/>'
        + blobs(blob_spec, "frost", classes)
        + f'<rect width="{w}" height="{h}" fill="{INK}" fill-opacity="{SCRIM_A}"/>'
        + f'<rect width="{w}" height="{h}" fill="#fff" fill-opacity="{FROST_A}"/>'
        + grid_svg
        + f'<rect width="{w}" height="{h}" fill="url(#shine)"/>'
        + f'<rect width="{w}" height="2" fill="url(#accent)"/>'
        + "</g>"
        + f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="none" stroke="#fff" stroke-opacity=".14"/>'
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
        ".d1{animation:d1 19s ease-in-out infinite alternate}"
        ".d2{animation:d2 23s ease-in-out infinite alternate}"
        ".d3{animation:d3 29s ease-in-out infinite alternate}"
        "@keyframes d1{to{transform:translate(90px,26px)}}"
        "@keyframes d2{to{transform:translate(-110px,-18px)}}"
        "@keyframes d3{to{transform:translate(60px,-30px)}}"
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
    spec = [(130, 40, 170, BLUE), (720, 210, 180, VIOLET), (470, -10, 120, LEAF)]
    tag_svg = "".join(
        f'<text class="m l l{i}" x="{w / 2}" y="190" font-size="17" fill="{BLUE}" text-anchor="middle">'
        f'{escape(line)}<tspan class="cur" fill-opacity=".8"> ▌</tspan></text>'
        for i, line in enumerate(lines)
    )
    return (
        svg_open(w, h, f"{cfg['name']} — {cfg['roles']}", " / ".join(lines), css)
        + glass(w, h, 20, spec, classes=["d1", "d2", "d3"], accent=(BLUE, LEAF), grid=True)
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
        spec = [(40, 200, 120, VIOLET), (400, 20, 110, BLUE), (330, 210, 90, AMBER)]
        label, color, accent = "PRIVATE · IN DEVELOPMENT", AMBER, (AMBER, VIOLET)
        corner = entry["version"]
    else:
        spec = [(50, 10, 120, BLUE), (390, 200, 130, VIOLET), (260, -10, 80, LEAF)]
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
        + glass(w, h, 16, spec, accent=accent, edge=AMBER if private else None)
        + body
        + "</svg>"
    )


def render_stack(cfg):
    groups = cfg["stack"]
    colors = [BLUE, LEAF, CYAN, TEXT]
    w, row_h, pad = 840, 54, 10
    h = pad * 2 + len(groups) * row_h
    spec = [(100, 20, 170, BLUE), (740, h, 180, VIOLET), (430, h / 2, 120, LEAF)]
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
        + glass(w, h, 16, spec, accent=(BLUE, VIOLET))
        + "".join(rows_svg)
        + "</svg>"
    )


def render_stats(stats):
    w, h = 420, 200
    spec = [(40, 20, 120, BLUE), (400, 200, 120, LEAF), (250, 220, 70, VIOLET)]
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
        + glass(w, h, 16, spec, accent=(LEAF, BLUE))
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
    spec = [(400, 10, 120, VIOLET), (40, 210, 120, BLUE), (220, -20, 70, LEAF)]
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
        + glass(w, h, 16, spec, accent=(BLUE, CYAN))
        + badge("TOP LANGUAGES", BLUE)
        + f'<clipPath id="bar"><rect x="{bar_x}" y="66" width="{bar_w}" height="10" rx="5"/></clipPath>'
        + f'<g clip-path="url(#bar)">{seg}</g>'
        + legend
        + "</svg>"
    )


# ---------------------------------------------------------------- README block

def featured_block(data):
    def cell(entry, i, private):
        src = f"assets/card-{'private' if private else 'public'}-{i}.svg"
        href = "#all-projects" if private else entry["url"]
        alt = f"{entry['title']} — {entry['summary']}"
        return f'<a href="{href}"><img src="{src}" width="49%" alt="{escape(alt, {chr(34): "&quot;"})}"></a>'

    pub = "\n".join(cell(e, i + 1, False) for i, e in enumerate(data["public"]))
    pri = "\n".join(cell(e, i + 1, True) for i, e in enumerate(data["private"]))
    return (
        "<!-- featured:start (generated by scripts/render_profile.py; edit data/profile.yml) -->\n"
        "**🎬 Shipped in public**\n\n"
        f'<p align="center">\n{pub}\n</p>\n\n'
        "**🔒 Building in private**\n\n"
        f'<p align="center">\n{pri}\n</p>\n'
        "<!-- featured:end -->"
    )


def update_readme(text, block):
    pattern = re.compile(r"<!-- featured:start.*?<!-- featured:end -->", re.S)
    if not pattern.search(text):
        raise RenderError("README is missing the featured:start/featured:end markers")
    return pattern.sub(lambda _: block, text)


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
        out[README] = update_readme(README.read_text(encoding="utf-8"), featured_block(data))
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
