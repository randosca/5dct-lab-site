#!/usr/bin/env python3
"""Build the 5DCT Lab website from the JSON files in data/.

    python build.py

Output goes to _site/: index.html for the home page, one folder per section
(method/, research/, history/, people/, publications/, presentations/, contact/)
each holding its own index.html, plus a copy of assets/. Only the Python
standard library is used, so this runs wherever Python 3 is installed.
"""
import datetime
import html
import json
import math
import random
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA, TPL, ASSETS, OUT = ROOT / "data", ROOT / "templates", ROOT / "assets", ROOT / "_site"

# Current lab members as PubMed writes them (surname + initials prefix). Shown in bold in author lists.
LAB_MEMBERS = ("Low D", "Moghanaki D", "Miller C", "Lauria M", "Andosca R")
TAG_LABELS = {
    "foundations": "Foundations",
    "method": "Acquisition and modeling",
    "clinical": "Clinical",
    "cbct": "Motion-compensated CBCT",
    "lungfunction": "Ventilation and lung function",
    "registration": "Image registration",
    "review": "Review",
}
FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,600;12..96,700'
    '&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400'
    '&family=IBM+Plex+Mono:wght@400;500&display=swap">'
)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def e(text):
    return html.escape(str(text), quote=True)


def fill(text, extra=None):
    for key, val in (extra or {}).items():
        text = text.replace("{" + key + "}", str(val))
    return text


def section_head(cfg, level="h2", extra=None):
    intro = fill(cfg.get("intro", ""), extra)
    intro_html = f'<p class="intro">{e(intro)}</p>' if intro else ""
    return (f'<div class="section-head"><p class="eyebrow">{e(cfg["eyebrow"])}</p>'
            f'<{level}>{e(cfg["heading"])}</{level}>{intro_html}</div>')


def figure(fig, prefix, cls="ct", lazy=True):
    cap = ""
    if fig.get("caption"):
        label = f'<span class="lab">{e(fig["label"])}</span>' if fig.get("label") else ""
        cap = f'<figcaption>{label}{e(fig["caption"])}</figcaption>'
    loading = ' loading="lazy"' if lazy else ""
    return (f'<figure><div class="{cls}"><img src="{e(prefix + fig["src"])}" alt="{e(fig["alt"])}"{loading}></div>'
            f'{cap}</figure>')


def breathing_trace(width=1120, height=84, points=640, seed=5):
    """A deterministic free-breathing trace: fast inhale, slower exhale, varying period, slow drift."""
    rng = random.Random(seed)
    cycles = []
    while sum(c[0] for c in cycles) < 64:
        cycles.append((rng.uniform(3.2, 4.8), rng.uniform(0.7, 1.0)))
    total = sum(c[0] for c in cycles)
    pts = []
    for i in range(points):
        x = i * total / (points - 1)
        start = 0.0
        for period, amp in cycles:
            if x < start + period:
                break
            start += period
        phase = (x - start) / period
        if phase < 0.4:
            b = 0.5 * (1 - math.cos(math.pi * phase / 0.4))
        else:
            b = 0.5 * (1 + math.cos(math.pi * (phase - 0.4) / 0.6))
        drift = 0.05 * math.sin(2 * math.pi * x / total * 1.3)
        y = height * 0.84 - b * amp * height * 0.62 + drift * height
        pts.append(f"{x / total * width:.1f},{y:.1f}")
    return (f'<svg class="wave" viewBox="0 0 {width} {height}" preserveAspectRatio="none" aria-hidden="true">'
            f'<polyline vector-effect="non-scaling-stroke" points="{" ".join(pts)}"/></svg>')


# ---------------------------------------------------------------------------
# Shared chrome
# ---------------------------------------------------------------------------

def nav(site, prefix, current):
    items = []
    for slug, label in site["nav"]:
        cur = ' aria-current="page"' if slug == current else ""
        items.append(f'<li><a href="{e(prefix + slug + "/")}"{cur}>{e(label)}</a></li>')
    home = prefix if prefix else "./"
    return (f'<header class="nav"><div class="wrap"><a class="brand" href="{e(home)}">5DCT Lab'
            f'<small>UCLA Radiation Oncology</small></a><nav aria-label="Sections"><ul>{"".join(items)}</ul></nav></div></header>')


def footer(site):
    today = datetime.date.today().strftime("%B %Y")
    return (f'<footer class="footer"><div class="wrap"><span>5DCT Lab &#183; {e(site["affiliation"])}</span>'
            f'<span>{e(site["footer_note"])} Last built {today}.</span></div></footer>')


def page(site, prefix, current, title, description, body):
    notice = (f'<div class="notice"><div class="wrap">{e(site["mockup_notice"])}</div></div>'
              if site.get("mockup_notice") else "")
    if current:
        body = f'<section class="page"><div class="wrap">{body}</div></section>'
    html_body = "".join(['<a class="skip" href="#main">Skip to content</a>', notice, nav(site, prefix, current),
                         f'<main id="main">{body}</main>', footer(site)])
    doc = (TPL / "base.html").read_text(encoding="utf-8")
    for key, val in {"title": e(title), "description": e(description), "fonts": FONTS,
                     "css": (TPL / "site.css").read_text(encoding="utf-8"), "body": html_body}.items():
        doc = doc.replace("{{" + key + "}}", val)
    return doc


# ---------------------------------------------------------------------------
# Home page
# ---------------------------------------------------------------------------

def hero(site, prefix):
    h = site["hero"]
    dims = "".join(
        f'<span class="{"breath" if sym in ("v", "f") else ""}"><b>{e(sym)}</b><small>{e(label)}</small></span>'
        for sym, label in h["dims"])
    stats = "".join(f'<div class="stat"><div class="n">{e(s["n"])}</div><div class="l">{e(s["l"])}</div></div>'
                    for s in site["stats"])
    return (
        f'<section class="hero"><div class="wrap">'
        f'<div><div class="dims" aria-label="The five dimensions">{dims}</div>'
        f'<h1>{e(h["headline"])}</h1>'
        f'<p class="lede"><strong>{e(h["lede_strong"])}</strong>{e(h["lede"])}</p>'
        f'<div class="cta"><a class="btn primary" href="{e(prefix + h["primary"][0] + "/")}">{e(h["primary"][1])}</a>'
        f'<a class="btn" href="{e(prefix + h["secondary"][0] + "/")}">{e(h["secondary"][1])}</a></div></div>'
        f'{figure(h["figure"], prefix, lazy=False)}'
        f'</div><div class="wrap">{breathing_trace()}<div class="stats">{stats}</div></div></section>'
    )


def contents(site, prefix, pub_count):
    """Index of the section pages, built from each section's own heading and intro."""
    entries = [("method", site["method"]), ("research", site["research"]), ("history", site["milestones"]),
               ("people", site["people"]), ("publications", site["publications"]),
               ("presentations", site["presentations"]), ("contact", site["contact"])]
    items = []
    for slug, cfg in entries:
        intro = fill(cfg.get("intro", ""), {"count": pub_count})
        items.append(f'<a class="item" href="{e(prefix + slug + "/")}"><p class="eyebrow">{e(cfg["eyebrow"])}</p>'
                     f'<h3>{e(cfg["heading"])}</h3><p>{e(intro)}</p></a>')
    return (f'<section class="section"><div class="wrap">{section_head(site["contents"])}'
            f'<div class="index">{"".join(items)}</div></div></section>')


# ---------------------------------------------------------------------------
# Section pages
# ---------------------------------------------------------------------------

def method(site, prefix):
    m = site["method"]
    paras = "".join(f"<p>{e(p)}</p>" for p in m["paragraphs"])
    steps = "".join(f'<li><div><h3>{e(s["title"])}</h3><p>{e(s["text"])}</p></div></li>' for s in m["steps"])
    equation = ('<div class="eq"><div class="f">X(<b>v</b>, <b>f</b>) = X&#8320; + &#945;&#183;<b>v</b> + &#946;&#183;<b>f</b></div>'
                f'<p class="legend">{e(m["equation_legend"])}</p></div>')
    return (f'{section_head(m, "h1")}'
            f'<div class="two"><div class="text flow">{paras}{equation}</div>'
            f'<div><ol class="steps">{steps}</ol><div style="margin-top:28px">{figure(m["figure"], prefix)}</div></div>'
            f'</div>')


def research(site, prefix):
    r = site["research"]
    cards = []
    for c in r["cards"]:
        if c.get("figure"):
            fig = (f'<div class="fig"><img src="{e(prefix + c["figure"]["src"])}" alt="{e(c["figure"]["alt"])}"'
                   f' loading="lazy"></div>')
        else:
            fig = f'<div class="fig pending">{e(c.get("pending", "Figure pending"))}</div>'
        cards.append(f'<article class="card">{fig}<div class="body"><h3>{e(c["title"])}</h3>'
                     f'<p>{e(c["text"])}</p><div class="who">{e(c["people"])}</div></div></article>')
    return f'{section_head(r, "h1")}<div class="cards">{"".join(cards)}</div>'


def milestones(site, items):
    rows = []
    for t in items:
        link = f' <a href="{e(t["link"])}">source</a>' if t.get("link") else ""
        rows.append(f'<li><div class="y">{e(t["year"])}</div><div><h3>{e(t["title"])}</h3>'
                    f'<p>{e(t["text"])}{link}</p></div></li>')
    return f'{section_head(site["milestones"], "h1")}<ol class="timeline">{"".join(rows)}</ol>'


def people(site, data):
    groups = []
    for g in data["groups"]:
        cards = []
        for p in g["people"]:
            links = "".join(f'<a href="{e(url)}">{e(label)}</a>' for label, url in p.get("links", []))
            links_html = f'<div class="links">{links}</div>' if links else ""
            cards.append(
                f'<div class="person"><div class="avatar" aria-hidden="true">{e(p["initials"])}</div>'
                f'<h4>{e(p["name"])}<small>{e(p["credentials"])}</small></h4>'
                f'<div class="role">{e(p["role"])}</div><p class="title">{e(p["title"])}</p>'
                f'<p class="bio">{e(p["bio"])}</p>{links_html}</div>')
        groups.append(f'<div class="group"><h3>{e(g["title"])}</h3><div class="people">{"".join(cards)}</div></div>')
    lineage = []
    for item in data["lineage"]:
        link = f' <a href="{e(item["link"])}">dissertation</a>' if item.get("link") else ""
        lineage.append(f'<li class="{"open" if item.get("open") else ""}"><div class="y">{e(item["year"])}</div>'
                       f'<h4>{e(item["name"])}</h4><p>{e(item["thesis"])}{link}</p><p>{e(item["now"])}</p></li>')
    return (f'{section_head(site["people"], "h1")}{"".join(groups)}'
            f'<div class="group"><h3>{e(data["lineage_heading"])}</h3><ol class="lineage">{"".join(lineage)}</ol>'
            f'<p class="note">{e(data["alumni_note"])}</p><p class="note">{e(data["collaborators"])}</p></div>')


def author_list(authors):
    out = []
    for a in authors:
        name = e(a)
        out.append(f"<strong>{name}</strong>" if a.startswith(LAB_MEMBERS) else name)
    return ", ".join(out)


def publications(site, pubs):
    years = {}
    for p in pubs:
        years.setdefault(p["year"], []).append(p)
    blocks = []
    for year in sorted(years, reverse=True):
        entries = []
        for p in years[year]:
            cite = f'<em>{e(p["journal"])}</em> {e(p["year"])}'
            if p.get("volume"):
                cite += f';{e(p["volume"])}'
                if p.get("issue"):
                    cite += f'({e(p["issue"])})'
            if p.get("pages"):
                cite += f':{e(p["pages"])}'
            href = f'https://doi.org/{p["doi"]}' if p.get("doi") else f'https://pubmed.ncbi.nlm.nih.gov/{p["pmid"]}/'
            pills = "".join(f'<span class="pill accent">{e(TAG_LABELS.get(t, t))}</span>' for t in p.get("tags", []))
            links = f'<a href="{e(href)}">doi</a>' if p.get("doi") else ""
            if p.get("pmid"):
                links += f' <a href="https://pubmed.ncbi.nlm.nih.gov/{e(p["pmid"])}/">pubmed</a>'
            entries.append(f'<li class="pub"><div class="t"><a href="{e(href)}">{e(p["title"])}</a></div>'
                           f'<div class="a">{author_list(p["authors"])}</div><div class="j">{cite}</div>'
                           f'<div class="meta">{pills}{links}</div></li>')
        blocks.append(f'<div class="pubyear"><div class="y">{year}</div><ol class="pubs">{"".join(entries)}</ol></div>')
    return f'{section_head(site["publications"], "h1", {"count": len(pubs)})}{"".join(blocks)}'


def presentations(site, items, prefix):
    cards = []
    for p in sorted(items, key=lambda x: (-x["year"], x["title"])):
        if p.get("thumb"):
            thumb = (f'<div class="thumb"><img src="{e(prefix + p["thumb"])}" alt="Poster: {e(p["title"])}"'
                     f' loading="lazy"></div>')
        else:
            thumb = '<div class="thumb pending">No image yet</div>'
        cards.append(f'<article class="poster">{thumb}<div class="body">'
                     f'<div class="m"><span class="pill">{e(p["type"])}</span>{e(p["meeting"])}</div>'
                     f'<div class="t">{e(p["title"])}</div><p class="au">{e(p["authors"])}</p></div></article>')
    return f'{section_head(site["presentations"], "h1")}<div class="posters">{"".join(cards)}</div>'


def contact(site):
    c = site["contact"]
    paras = "".join(f"<p>{e(p)}</p>" for p in c["paragraphs"])
    rows = []
    for k, v in c["details"]:
        val = e(v)
        for token in v.split():
            if token.startswith("http"):
                val = val.replace(e(token), f'<a href="{e(token)}">{e(token)}</a>')
            elif "@" in token and "." in token:
                tok = token.rstrip(",.")
                val = val.replace(e(tok), f'<a href="mailto:{e(tok)}">{e(tok)}</a>')
        rows.append(f"<dt>{e(k)}</dt><dd>{val}</dd>")
    return (f'{section_head(c, "h1")}'
            f'<div class="contact"><div class="flow">{paras}</div><dl class="details">{"".join(rows)}</dl></div>')


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build():
    site = load("site.json")
    pubs = load("publications.json")
    name = site["title"]

    def titled(cfg, extra=None):
        return f'{cfg["heading"]} · {name}', fill(cfg.get("intro", ""), extra) or site["description"]

    pages = [("", (name, site["description"]), hero(site, "") + contents(site, "", len(pubs)))]
    sub = "../"
    pages += [
        ("method", titled(site["method"]), method(site, sub)),
        ("research", titled(site["research"]), research(site, sub)),
        ("history", titled(site["milestones"]), milestones(site, load("timeline.json"))),
        ("people", titled(site["people"]), people(site, load("people.json"))),
        ("publications", titled(site["publications"], {"count": len(pubs)}), publications(site, pubs)),
        ("presentations", titled(site["presentations"]), presentations(site, load("presentations.json"), sub)),
        ("contact", titled(site["contact"]), contact(site)),
    ]

    # Empty the output folder rather than deleting it, so a local server pointed at it keeps working.
    OUT.mkdir(exist_ok=True)
    for child in OUT.iterdir():
        shutil.rmtree(child) if child.is_dir() else child.unlink()

    for slug, (title, description), body in pages:
        prefix = sub if slug else ""
        folder = OUT / slug if slug else OUT
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text(page(site, prefix, slug, title, description, body), encoding="utf-8")

    shutil.copytree(ASSETS, OUT / "assets")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    if site.get("domain"):
        (OUT / "CNAME").write_text(site["domain"].strip() + "\n", encoding="utf-8")
    print(f"built {len(pages)} pages into {OUT}")


if __name__ == "__main__":
    build()
