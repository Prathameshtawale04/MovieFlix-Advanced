"""Generates a distinct placeholder poster (as an inline SVG data URI) for movies that have
no real image — used by demo mode, and as a nicer fallback than a single generic box."""
import base64

# same palette as the hero's .tone-N gradients, so demo posters and the hero feel consistent
_PALETTE = ["#c0293a", "#2f7fb0", "#c98a2e", "#6a3fc9", "#2f9e63", "#c93fa8"]


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def _wrap(title, width=13, max_lines=4):
    words = _esc(title).split()
    lines, cur = [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if len(trial) <= width or not cur:
            cur = trial
        else:
            lines.append(cur); cur = w
        if len(lines) == max_lines:
            return lines
    if cur:
        lines.append(cur)
    return lines[:max_lines]


def poster_svg(title, seed=0, year=""):
    accent = _PALETTE[int(seed) % len(_PALETTE)]
    lines = _wrap(title)
    title_bottom = 640  # last title line always ends here, regardless of line count
    ty = title_bottom - (len(lines) - 1) * 38
    tspans = "".join(f'<tspan x="36" dy="{0 if i == 0 else 38}">{ln}</tspan>' for i, ln in enumerate(lines))
    year_tag = f'<text x="36" y="682" fill="#ffffffaa" font-family="Arial,sans-serif" font-size="20">{_esc(year)}</text>' if year else ""
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 750">
<defs>
  <linearGradient id="g" x1="0" y1="0" x2="0.9" y2="1">
    <stop offset="0" stop-color="{accent}" stop-opacity="0.55"/>
    <stop offset="0.55" stop-color="#0e0e0e"/>
  </linearGradient>
</defs>
<rect width="500" height="750" fill="#111"/>
<rect width="500" height="750" fill="url(#g)"/>
<circle cx="430" cy="90" r="120" fill="{accent}" opacity="0.18"/>
<rect x="36" y="36" width="46" height="6" rx="3" fill="{accent}"/>
<text x="36" y="{ty}" fill="#fff" font-family="Arial,sans-serif" font-size="34" font-weight="700">{tspans}</text>
{year_tag}
<text x="36" y="720" fill="#ffffff66" font-family="Arial,sans-serif" font-size="15" letter-spacing="2">MOVIEFLIX</text>
</svg>'''
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")
