"""Bouwt de losse websites (GitHub Pages) uit één bron, bron/dagscore.html.

  index.html          Dagscore     (iPhone) -> Scores.csv
  werk/index.html     Werkscore    (Mac)    -> WorkScores.csv
  ochtend/index.html  Ochtendscore (iPhone) -> MorningScores.csv

Per app verschillen alleen de instellingen in <script id="app-config">, de
titel en het icoon. Gebruik (vanuit de hoofdmap): python3 bron/build_site.py
"""
import hashlib
import json
import math
import re
from pathlib import Path

try:  # Pillow is alleen nodig om de iconen opnieuw te tekenen
    from PIL import Image, ImageDraw
except ImportError:
    Image = None

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "dagscore.html"
OUT = ROOT.parent  # de gebouwde site staat in de hoofdmap van de repository

SCALE_10 = {"type": "scale", "min": 1, "max": 10, "low": "laag", "high": "hoog"}

# App key van de Dropbox-app (niet geheim; inloggen gaat met PKCE)
DROPBOX_KEY = "erjo5qemoyi1iu4"

APPS = [
    {
        "dir": "",
        "icon": "dag",
        "config": None,  # de instellingen die al in dagscore.html staan
    },
    {
        "dir": "werk",
        "icon": "werk",
        "config": {
            "name": "Werkscore",
            "file": "WorkScores.csv",
            "storeKey": "werkscore.verstuurd.v1",
            "dayStartsAt": 7,
            # eenmalig: oude Stress-waarden 1–10 omzetten naar 0–5 (zie runMigration in dagscore.html)
            # en eenmalig: kolom Happyness hernoemen naar Happiness, en kolom Workload verwijderen
            "migrations": [{"id": "werkstress-0-5", "col": "Stress"},
                           {"id": "werk-happiness-naam", "rename": ["Happyness", "Happiness"]},
                           {"id": "workload-verwijderen", "drop": "Workload"}],
            "questions": [
                {"id": "happiness", "label": "Happiness?", "short": "Happy", **SCALE_10},
                {"id": "stress", "label": "Stress?", "short": "Stress", "type": "scale", "min": 0, "max": 5, "low": "geen", "high": "veel"},
                {"id": "unclenched", "label": "Unclenched?", "short": "Unclenched", **SCALE_10},
                {"id": "comment", "label": "Comment", "short": "Comment", "type": "text"},
            ],
        },
    },
    {
        "dir": "ochtend",
        "icon": "ochtend",
        "config": {
            "name": "Ochtendscore",
            "file": "MorningScores.csv",
            "storeKey": "ochtendscore.verstuurd.v1",
            "dayStartsAt": 0,  # 's ochtends invullen hoort bij vandaag
            # Slaap (uren) rekent de app uit: opgestaan − naar bed − wakker gelegen. De kolommen Slaap en
            # Wakker houden hun naam, zodat de geschiedenis en het dashboard blijven kloppen.
            "order": ["bed", "op", "wakker", "slaap", "gevoel"],
            "questions": [
                {"id": "slaap", "label": "Geslapen", "col": "Slaap", "short": "Slaap", "type": "calc", "unit": "uur",
                 "calc": {"from": "bed", "to": "op", "minus": "wakker"}},
                {"id": "wakker", "label": "Uren wakker gelegen?", "col": "Wakker", "short": "Wakker", "type": "slider", "min": 0, "max": 4, "step": 0.5, "default": 0.5},
                {"id": "gevoel", "label": "Gevoel?", "short": "Gevoel", "type": "scale", "min": 1, "max": 10, "low": "slecht", "high": "goed"},
                {"id": "bed", "label": "Naar bed?", "short": "Bed", "type": "slider", "time": True, "min": 20, "max": 27, "step": 0.5},
                {"id": "op", "label": "Opgestaan?", "short": "Op", "type": "slider", "time": True, "min": 4, "max": 12, "step": 0.5},
            ],
        },
    },
]

HEAD = """<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="{name}">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="theme-color" content="#EBF0F2" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0E151B" media="(prefers-color-scheme: dark)">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="icon" type="image/png" href="apple-touch-icon.png">
<style>
:root {{ color-scheme: light; padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }}
body {{ margin: 0; }}
img {{ max-width: 100%; }}
[hidden] {{ display: none !important; }}
</style>
"""

CONFIG_RE = re.compile(r'(<script id="app-config" type="application/json">)(.*?)(</script>)', re.S)


def variant(src: str, config: dict | None) -> tuple[str, str]:
    """Geeft (broncode voor deze app, app-naam)."""
    if config is None:
        config = json.loads(CONFIG_RE.search(src).group(2))
    config = {**config, "dropboxKey": DROPBOX_KEY}
    body ="\n" + json.dumps(config, ensure_ascii=False, indent=2) + "\n"
    src = CONFIG_RE.sub(lambda m: m.group(1) + body + m.group(3), src, count=1)
    src = src.replace("<title>Dagscore</title>", f"<title>{config['name']}</title>", 1)
    return src, config["name"]


def build_html(src: str, name: str, out_dir: Path) -> None:
    # Versiestempel: de app vergelijkt dit met de site en laadt opnieuw als het anders is
    version = hashlib.sha1(src.encode("utf-8")).hexdigest()[:10]
    split = src.index("<main")
    head_part, body_part = src[:split], src[split:]
    meta = f'<meta name="dagscore-versie" content="{version}">\n'
    html = (HEAD.format(name=name) + meta + head_part.rstrip() + "\n</head>\n<body>\n"
            + body_part.rstrip() + "\n</body>\n</html>\n")
    (out_dir / "index.html").write_text(html, encoding="utf-8")


# ---------- Iconen: kleurverloop met één duidelijk symbool per app ----------
def _stroke(d, a, b, w) -> None:
    """Lijn met ronde uiteinden."""
    d.line([a, b], fill=255, width=round(w))
    for x, y in (a, b):
        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=255)


def _rays(d, s, cx, cy, r0, r1, w, degrees) -> None:
    for deg in degrees:
        c, n = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        _stroke(d, (s * (cx + r0 * c), s * (cy + r0 * n)), (s * (cx + r1 * c), s * (cy + r1 * n)), s * w)


def _star(d, s, cx, cy, r) -> None:
    """Vierpuntige ster."""
    points = []
    for i in range(8):
        radius = r if i % 2 == 0 else r * 0.3
        angle = math.radians(i * 45 - 90)
        points.append((s * (cx + radius * math.cos(angle)), s * (cy + radius * math.sin(angle))))
    d.polygon(points, fill=255)


def _icon_dag(d, s) -> None:
    """Maansikkel met sterren: het einde van de dag."""
    cx, cy, r = 0.45, 0.53, 0.275
    d.ellipse([s * (cx - r), s * (cy - r), s * (cx + r), s * (cy + r)], fill=255)
    cx, cy, r = 0.575, 0.445, 0.24
    d.ellipse([s * (cx - r), s * (cy - r), s * (cx + r), s * (cy + r)], fill=0)
    _star(d, s, 0.665, 0.335, 0.105)
    _star(d, s, 0.785, 0.525, 0.06)


def _icon_ochtend(d, s) -> None:
    """Zon die opkomt boven de horizon."""
    cx, cy, r = 0.5, 0.60, 0.175
    d.pieslice([s * (cx - r), s * (cy - r), s * (cx + r), s * (cy + r)], 180, 360, fill=255)
    _rays(d, s, cx, cy, 0.265, 0.345, 0.052, range(210, 331, 30))
    _stroke(d, (s * 0.19, s * 0.675), (s * 0.81, s * 0.675), s * 0.052)
    _stroke(d, (s * 0.35, s * 0.775), (s * 0.65, s * 0.775), s * 0.052)


def _icon_werk(d, s) -> None:
    """Aktetas."""
    d.rounded_rectangle([s * 0.375, s * 0.235, s * 0.625, s * 0.42], radius=s * 0.055, outline=255, width=round(s * 0.05))
    d.rounded_rectangle([s * 0.185, s * 0.335, s * 0.815, s * 0.765], radius=s * 0.075, fill=255)
    d.rectangle([s * 0.185, s * 0.525, s * 0.815, s * 0.555], fill=0)  # naad
    d.rounded_rectangle([s * 0.425, s * 0.475, s * 0.575, s * 0.605], radius=s * 0.03, fill=0)  # ruimte om het slot
    d.rounded_rectangle([s * 0.452, s * 0.502, s * 0.548, s * 0.578], radius=s * 0.018, fill=255)  # slot


# kleur boven, kleur onder, kleur van het symbool, tekening
ICONS = {
    "dag": ((58, 56, 138), (15, 18, 56), (255, 224, 130), _icon_dag),
    "werk": ((46, 170, 134), (15, 82, 68), (255, 255, 255), _icon_werk),
    "ochtend": ((247, 150, 54), (186, 58, 44), (255, 243, 218), _icon_ochtend),
}


def build_icon(out_dir: Path, kind: str, size: int = 180) -> None:
    if Image is None:
        print("  (Pillow ontbreekt: bestaand icoon blijft staan)")
        return
    top, bottom, color, draw = ICONS[kind]
    s = size * 8  # groot tekenen en verkleinen geeft gladde randen
    fade = Image.linear_gradient("L").resize((s, s))
    img = Image.composite(Image.new("RGB", (s, s), bottom), Image.new("RGB", (s, s), top), fade)
    mask = Image.new("L", (s, s), 0)
    draw(ImageDraw.Draw(mask), s)
    img.paste(color, (0, 0), mask)
    img.resize((size, size), Image.LANCZOS).save(out_dir / "apple-touch-icon.png", optimize=True)


if __name__ == "__main__":
    src = SRC.read_text(encoding="utf-8")
    for app in APPS:
        out_dir = OUT / app["dir"] if app["dir"] else OUT
        out_dir.mkdir(parents=True, exist_ok=True)
        app_src, name = variant(src, app["config"])
        build_html(app_src, name, out_dir)
        build_icon(out_dir, app["icon"])
        print(f"Klaar: {name} -> {out_dir / 'index.html'}")
