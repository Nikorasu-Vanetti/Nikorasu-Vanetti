#!/usr/bin/env python3
"""
Generador del perfil de GitHub de Nikorasu-Vanetti.

Lee los repositorios vía la API de GitHub y regenera, a partir de datos reales:
  - assets/header.svg        Banner PCB/blueprint animado (identidad).
  - assets/languages.svg     Distribucion de lenguajes (barra + leyenda) animada.
  - assets/stats.svg         Tarjetas de metricas (repos, estrellas, lenguajes...).
  - Seccion PROJECTS del README.md (entre marcadores).

Sin dependencias externas: solo la libreria estandar.
Token: variable de entorno METRICS_TOKEN (preferida) o GITHUB_TOKEN.
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

USERNAME = "Nikorasu-Vanetti"
API = "https://api.github.com"
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
README = os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md")

# Identidad (lo unico curado a mano; el resto es 100% derivado de datos).
FULL_NAME = "Jose Nicolas Sanchez Zorrilla"
ALIAS = "NIKO . VANETTI"
ROLE = "Software Engineer  //  Developer tools, AI agents & embedded systems"

# Colores oficiales de GitHub Linguist (los que falten caen a un gris).
LINGUIST = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572A5",
    "C": "#555555", "C++": "#f34b7d", "HTML": "#e34c26", "CSS": "#563d7c",
    "Swift": "#F05138", "Java": "#b07219", "Kotlin": "#A97BFF",
    "Verilog": "#848bf3", "Ruby": "#701516", "Batchfile": "#C1F12E",
    "Shell": "#89e051", "Go": "#00ADD8", "Rust": "#dea584", "Dart": "#00B4AB",
    "Vue": "#41b883", "PHP": "#4F5D95", "C#": "#178600",
}
DEFAULT_COLOR = "#6b7280"


# --------------------------------------------------------------------------- #
#  Capa de datos                                                              #
# --------------------------------------------------------------------------- #
def token():
    tk = os.environ.get("METRICS_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    return tk.strip().lstrip("﻿")  # tolera BOM/espacios de un secret mal codificado


def api_get(path):
    url = path if path.startswith("http") else API + path
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", USERNAME + "-profile-generator")
    tk = token()
    if tk:
        req.add_header("Authorization", "Bearer " + tk)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_repos():
    """Repos propios (publicos + privados si el token lo permite), sin forks."""
    repos = []
    # Con token de usuario: /user/repos ve privados. Si falla, fallback publico.
    endpoints = [
        "/user/repos?affiliation=owner&per_page=100&sort=updated",
        "/users/" + USERNAME + "/repos?per_page=100&sort=updated",
    ]
    for ep in endpoints:
        try:
            data = api_get(ep)
            if isinstance(data, list) and data:
                repos = data
                break
        except urllib.error.HTTPError:
            continue
    out = []
    for r in repos:
        if r.get("fork"):
            continue
        if r.get("name", "").lower() == USERNAME.lower():
            continue  # el propio repo de perfil
        out.append(r)
    return out


def fetch_languages(repo):
    try:
        return api_get("/repos/" + USERNAME + "/" + repo["name"] + "/languages")
    except Exception:
        return {}


def fetch_profile():
    try:
        return api_get("/users/" + USERNAME)
    except Exception:
        return {}


def aggregate_languages(repos):
    totals = {}
    for r in repos:
        for lang, b in fetch_languages(r).items():
            totals[lang] = totals.get(lang, 0) + b
    grand = sum(totals.values()) or 1
    rows = []
    for lang, b in sorted(totals.items(), key=lambda kv: kv[1], reverse=True):
        rows.append({
            "name": lang,
            "bytes": b,
            "pct": round(b / grand * 100, 1),
            "color": LINGUIST.get(lang, DEFAULT_COLOR),
        })
    return rows


# --------------------------------------------------------------------------- #
#  Utilidades                                                                  #
# --------------------------------------------------------------------------- #
def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def write(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("wrote", os.path.relpath(path))


# --------------------------------------------------------------------------- #
#  SVG: cabecera PCB animada                                                   #
# --------------------------------------------------------------------------- #
def header_svg(top_lang):
    W, H = 1000, 320
    accent = "#2dd4bf"   # teal traza
    accent2 = "#38bdf8"  # sky traza
    gold = "#fbbf24"     # cobre / vias
    silk = "#e2f1f8"     # serigrafia

    # Trazos PCB (ruteo a 45 grados). Cada uno se "dibuja" y lleva corriente.
    traces = [
        "M40,60 L160,60 L210,110 L210,210 L150,270",
        "M40,150 L120,150 L150,180 L300,180",
        "M40,250 L100,250 L140,210 L260,210",
        "M960,70 L840,70 L800,110 L800,250 L860,300",
        "M960,160 L880,160 L850,190 L700,190",
        "M960,260 L900,260 L860,220 L740,220",
        "M500,300 L500,250 L470,220 L470,170",
        "M620,300 L620,260 L650,230 L650,180",
    ]
    # Vias / pads que pulsan.
    vias = [
        (160, 60), (210, 210), (300, 180), (260, 210),
        (840, 70), (700, 190), (740, 220), (470, 170), (650, 180),
        (120, 150), (880, 160), (900, 260),
    ]

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
                 f'width="{W}" height="{H}" role="img" '
                 f'aria-label="{esc(FULL_NAME)} - {esc(ROLE)}">')

    # ---- defs ----
    parts.append('<defs>')
    parts.append('<radialGradient id="bg" cx="50%" cy="40%" r="80%">'
                 '<stop offset="0%" stop-color="#0a1f33"/>'
                 '<stop offset="60%" stop-color="#071524"/>'
                 '<stop offset="100%" stop-color="#040d18"/></radialGradient>')
    parts.append(f'<linearGradient id="trace" x1="0" y1="0" x2="1" y2="0">'
                 f'<stop offset="0%" stop-color="{accent}"/>'
                 f'<stop offset="100%" stop-color="{accent2}"/></linearGradient>')
    parts.append('<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">'
                 '<feGaussianBlur stdDeviation="2.2" result="b"/>'
                 '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    parts.append('<pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse">'
                 '<path d="M28 0H0V28" fill="none" stroke="#0e2a45" stroke-width="1"/></pattern>')
    parts.append('</defs>')

    # ---- styles (CSS animations, sin JS, funcionan via <img>) ----
    css = """
    <style>
      .draw{stroke-dasharray:1400;stroke-dashoffset:1400;animation:draw 2.6s ease forwards;}
      .flow{stroke-dasharray:6 22;stroke-dashoffset:0;animation:flow 1.4s linear infinite;}
      @keyframes draw{to{stroke-dashoffset:0;}}
      @keyframes flow{to{stroke-dashoffset:-280;}}
      .via{animation:pulse 2.8s ease-in-out infinite;transform-origin:center;}
      @keyframes pulse{0%,100%{opacity:.45;r:3;}50%{opacity:1;r:5;}}
      .led{animation:blink 1.6s steps(1) infinite;}
      @keyframes blink{0%,49%{opacity:1;}50%,100%{opacity:.15;}}
      .pin{animation:sweep 3.2s ease-in-out infinite;}
      @keyframes sweep{0%,100%{opacity:.25;}50%{opacity:1;}}
      .fade{opacity:0;animation:fade 1s ease forwards;}
      .fade2{opacity:0;animation:fade 1s ease .5s forwards;}
      .fade3{opacity:0;animation:fade 1s ease 1s forwards;}
      @keyframes fade{to{opacity:1;}}
      .cur{animation:cur 1.1s steps(1) infinite;}
      @keyframes cur{0%,49%{opacity:1;}50%,100%{opacity:0;}}
      text{font-family:'Segoe UI',Helvetica,Arial,sans-serif;}
      .mono{font-family:'Cascadia Code','Consolas',ui-monospace,monospace;}
    </style>
    """
    parts.append(css)

    # ---- background ----
    parts.append(f'<rect width="{W}" height="{H}" rx="16" fill="url(#bg)"/>')
    parts.append(f'<rect width="{W}" height="{H}" rx="16" fill="url(#grid)" opacity="0.6"/>')
    parts.append(f'<rect x="3" y="3" width="{W - 6}" height="{H - 6}" rx="14" fill="none" '
                 f'stroke="{accent}" stroke-width="1.5" opacity="0.5"/>')

    # ---- traces (capa base dibujandose + capa de corriente) ----
    for d in traces:
        parts.append(f'<path d="{d}" fill="none" stroke="url(#trace)" stroke-width="2.4" '
                     f'stroke-linecap="round" stroke-linejoin="round" opacity="0.55" class="draw"/>')
    for d in traces:
        parts.append(f'<path d="{d}" fill="none" stroke="#bdf6ff" stroke-width="2.4" '
                     f'stroke-linecap="round" filter="url(#glow)" class="flow"/>')

    # ---- vias ----
    for (x, y) in vias:
        parts.append(f'<circle cx="{x}" cy="{y}" r="3" fill="{gold}" class="via" filter="url(#glow)"/>')

    # ---- chip / IC a la derecha ----
    cx, cy, cw, ch = 740, 70, 150, 96
    parts.append('<g class="fade2">')
    parts.append(f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="8" fill="#0c2236" '
                 f'stroke="{accent}" stroke-width="1.5"/>')
    # pines laterales
    for i in range(6):
        py = cy + 14 + i * 13
        parts.append(f'<rect x="{cx - 10}" y="{py}" width="10" height="6" fill="{gold}" '
                     f'class="pin" style="animation-delay:{i * 0.18:.2f}s"/>')
        parts.append(f'<rect x="{cx + cw}" y="{py}" width="10" height="6" fill="{gold}" '
                     f'class="pin" style="animation-delay:{i * 0.18 + 0.4:.2f}s"/>')
    parts.append(f'<circle cx="{cx + 16}" cy="{cy + 16}" r="5" fill="none" '
                 f'stroke="{accent2}" stroke-width="1.5"/>')
    parts.append(f'<text x="{cx + 34}" y="{cy + 22}" fill="{silk}" class="mono" font-size="13" '
                 f'letter-spacing="1">JNSZ-01</text>')
    parts.append(f'<text x="{cx + 18}" y="{cy + 64}" fill="{accent}" class="mono" font-size="10" '
                 f'opacity="0.7">core: {esc(top_lang)}</text>')
    parts.append('</g>')

    # ---- LED de estado ----
    parts.append('<circle cx="58" cy="36" r="5" fill="#22c55e" class="led" filter="url(#glow)"/>')
    parts.append(f'<text x="72" y="40" fill="{silk}" class="mono" font-size="12" '
                 f'opacity="0.8">online</text>')

    # ---- texto heroe (identidad) ----
    parts.append(f'<text x="60" y="148" fill="{silk}" font-size="40" font-weight="700" '
                 f'letter-spacing="0.5" class="fade">{esc(FULL_NAME)}</text>')
    parts.append(f'<text x="62" y="184" fill="{gold}" class="mono fade2" font-size="20" '
                 f'font-weight="600" letter-spacing="3">aka {esc(ALIAS)}</text>')
    parts.append('<g class="fade3">')
    parts.append(f'<text x="62" y="224" fill="{accent}" class="mono" font-size="14" '
                 f'opacity="0.85">{esc(ROLE)}</text>')
    parts.append(f'<text x="62" y="258" fill="{silk}" class="mono" font-size="14" '
                 f'opacity="0.9">&gt; building<tspan fill="{silk}"> _</tspan>'
                 f'<tspan class="cur" fill="{gold}">|</tspan></text>')
    parts.append('</g>')

    parts.append('</svg>')
    return "".join(parts)


# --------------------------------------------------------------------------- #
#  SVG: distribucion de lenguajes                                             #
# --------------------------------------------------------------------------- #
def languages_svg(rows):
    rows = rows[:8]
    W = 1000
    pad = 28
    barx, barw, bary, barh = pad, W - 2 * pad, 88, 26
    legcols = 4
    legrows = (len(rows) + legcols - 1) // legcols
    H = bary + barh + 56 + legrows * 30

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
                 f'width="{W}" height="{H}" role="img" aria-label="Language distribution">')
    css = """
    <style>
      @keyframes grow{from{width:0;}}
      @keyframes fin{from{opacity:0;transform:translateY(6px);}to{opacity:1;transform:translateY(0);}}
      .seg{animation:grow 1.4s cubic-bezier(.2,.7,.2,1) forwards;}
      .lg{opacity:0;animation:fin .6s ease forwards;}
      .via{animation:vp 2.6s ease-in-out infinite;transform-origin:center;}
      @keyframes vp{0%,100%{opacity:.4;}50%{opacity:1;}}
      text{font-family:'Cascadia Code','Consolas',ui-monospace,monospace;}
    </style>
    """
    parts.append(css)
    parts.append(f'<rect width="{W}" height="{H}" rx="16" fill="#071524"/>')
    parts.append(f'<rect x="2" y="2" width="{W - 4}" height="{H - 4}" rx="15" fill="none" '
                 f'stroke="#0e2a45" stroke-width="1.5"/>')
    # vias decorativas en esquinas
    for (vx, vy, dly) in [(18, 18, 0), (W - 18, 18, .6), (18, H - 18, 1.2), (W - 18, H - 18, .3)]:
        parts.append(f'<circle cx="{vx}" cy="{vy}" r="3.5" fill="#2dd4bf" class="via" '
                     f'style="animation-delay:{dly}s"/>')

    parts.append(f'<text x="{pad}" y="44" fill="#e2f1f8" font-size="18" font-weight="700" '
                 f'letter-spacing="2">LANGUAGE DISTRIBUTION</text>')
    parts.append(f'<text x="{W - pad}" y="44" fill="#2dd4bf" font-size="12" text-anchor="end" '
                 f'opacity="0.8">// computed from all owned repos</text>')

    # barra base
    parts.append(f'<rect x="{barx}" y="{bary}" width="{barw}" height="{barh}" rx="13" fill="#0b2236"/>')
    # segmentos
    x = barx
    delay = 0.0
    parts.append(f'<clipPath id="barclip"><rect x="{barx}" y="{bary}" width="{barw}" '
                 f'height="{barh}" rx="13"/></clipPath>')
    parts.append('<g clip-path="url(#barclip)">')
    for r in rows:
        w = max(2, barw * r["pct"] / 100.0)
        parts.append(f'<rect x="{x:.1f}" y="{bary}" width="{w:.1f}" height="{barh}" '
                     f'fill="{r["color"]}" class="seg" style="animation-delay:{delay:.2f}s">'
                     f'<title>{esc(r["name"])} {r["pct"]:.1f}%</title></rect>')
        x += w
        delay += 0.12
    parts.append('</g>')

    # leyenda en grid
    coli = 0
    rowi = 0
    cellw = barw / legcols
    ly0 = bary + barh + 40
    for i, r in enumerate(rows):
        lx = barx + coli * cellw
        ly = ly0 + rowi * 30
        d = 0.4 + i * 0.08
        parts.append(f'<g class="lg" style="animation-delay:{d:.2f}s">')
        parts.append(f'<rect x="{lx:.1f}" y="{ly - 11}" width="12" height="12" rx="3" '
                     f'fill="{r["color"]}"/>')
        parts.append(f'<text x="{lx + 20:.1f}" y="{ly}" fill="#cfe3f0" font-size="13">'
                     f'{esc(r["name"])}</text>')
        parts.append(f'<text x="{lx + cellw - 14:.1f}" y="{ly}" fill="#7aa0b8" font-size="13" '
                     f'text-anchor="end">{r["pct"]:.1f}%</text>')
        parts.append('</g>')
        coli += 1
        if coli >= legcols:
            coli = 0
            rowi += 1
    parts.append('</svg>')
    return "".join(parts)


# --------------------------------------------------------------------------- #
#  SVG: tarjetas de metricas                                                   #
# --------------------------------------------------------------------------- #
def stats_svg(metrics):
    W, H = 1000, 132
    n = len(metrics)
    pad = 28
    gap = 16
    cw = (W - 2 * pad - gap * (n - 1)) / n
    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
                 f'width="{W}" height="{H}" role="img" aria-label="Profile metrics">')
    css = """
    <style>
      .card{opacity:0;animation:up .7s ease forwards;}
      @keyframes up{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}
      .scan{animation:scan 3s linear infinite;}
      @keyframes scan{0%{opacity:0;}10%{opacity:.8;}100%{opacity:0;transform:translateX(140px);}}
      text{font-family:'Cascadia Code','Consolas',ui-monospace,monospace;}
    </style>
    """
    parts.append(css)
    parts.append(f'<rect width="{W}" height="{H}" fill="#040d18"/>')
    for i, (label, value) in enumerate(metrics):
        x = pad + i * (cw + gap)
        parts.append(f'<g class="card" style="animation-delay:{i * 0.15:.2f}s">')
        parts.append(f'<rect x="{x:.1f}" y="20" width="{cw:.1f}" height="92" rx="12" fill="#081a2c" '
                     f'stroke="#123a55" stroke-width="1.3"/>')
        parts.append(f'<rect x="{x:.1f}" y="20" width="4" height="92" rx="2" fill="#2dd4bf"/>')
        parts.append(f'<text x="{x + 22:.1f}" y="74" fill="#e2f1f8" font-size="34" '
                     f'font-weight="700">{esc(value)}</text>')
        parts.append(f'<text x="{x + 22:.1f}" y="98" fill="#6f97b0" font-size="12" '
                     f'letter-spacing="1.5">{esc(label.upper())}</text>')
        # linea de escaneo
        parts.append(f'<rect x="{x + 6:.1f}" y="22" width="2" height="88" fill="#2dd4bf" '
                     f'class="scan" style="animation-delay:{i * 0.4:.2f}s"/>')
        parts.append('</g>')
    parts.append('</svg>')
    return "".join(parts)


# --------------------------------------------------------------------------- #
#  README: seccion de proyectos                                               #
# --------------------------------------------------------------------------- #
def projects_md(repos):
    rows = sorted(repos, key=lambda r: r.get("updated_at", ""), reverse=True)
    lines = []
    lines.append("| Project | Stack | What it is | Status |")
    lines.append("| --- | --- | --- | --- |")
    for r in rows:
        name = r.get("name", "")
        lang = (r.get("language") or "-")
        desc = (r.get("description") or "").strip() or "-"
        priv = r.get("private", False)
        url = r.get("html_url", "")
        if priv:
            title = "**" + esc(name) + "**"
            status = "private"
        else:
            title = "**[" + esc(name) + "](" + url + ")**"
            stars = r.get("stargazers_count", 0)
            status = ("public . " + str(stars) + " stars") if stars else "public"
        lines.append("| %s | `%s` | %s | %s |" % (title, esc(lang), esc(desc), status))
    return "\n".join(lines)


def inject(readme_text, marker, content):
    start = "<!-- %s:START -->" % marker
    end = "<!-- %s:END -->" % marker
    pattern = re.compile(re.escape(start) + ".*?" + re.escape(end), re.DOTALL)
    repl = start + "\n" + content + "\n" + end
    if pattern.search(readme_text):
        return pattern.sub(lambda m: repl, readme_text)
    return readme_text  # marcador ausente: no toca nada


# --------------------------------------------------------------------------- #
#  Main                                                                        #
# --------------------------------------------------------------------------- #
def main():
    print("fetching data for", USERNAME, "...")
    repos = fetch_repos()
    profile = fetch_profile()
    langs = aggregate_languages(repos)
    top_lang = langs[0]["name"] if langs else "code"

    os.makedirs(ASSETS, exist_ok=True)
    write(os.path.join(ASSETS, "header.svg"), header_svg(top_lang))
    write(os.path.join(ASSETS, "languages.svg"), languages_svg(langs))

    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    created = profile.get("created_at", "2023-01-01T00:00:00Z")[:4]
    metrics = [
        ("Repositories", str(len(repos))),
        ("Total stars", str(total_stars)),
        ("Languages", str(len(langs))),
        ("Since", created),
    ]
    write(os.path.join(ASSETS, "stats.svg"), stats_svg(metrics))

    if os.path.exists(README):
        txt = open(README, encoding="utf-8").read()
        txt = inject(txt, "PROJECTS", projects_md(repos))
        txt = inject(txt, "UPDATED",
                     "_Last refreshed: " +
                     datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC") + "_")
        write(README, txt)

    print("done. repos:", len(repos), "languages:", len(langs), "stars:", total_stars)


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as e:
        print("HTTP error:", e.code, e.reason, file=sys.stderr)
        sys.exit(1)
