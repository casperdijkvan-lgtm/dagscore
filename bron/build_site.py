"""Bouwt de losse websites (GitHub Pages) uit één bron, bron/dagscore.html.

  index.html          Dagscore     (iPhone) -> Scores.csv
  werk/index.html     Werkscore    (Mac)    -> WorkScores.csv
  ochtend/index.html  Ochtendscore (iPhone) -> MorningScores.csv

Per app verschillen alleen de instellingen in <script id="app-config">, de
titel en het icoon. Gebruik (vanuit de hoofdmap): python3 bron/build_site.py
"""
import hashlib
import json
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
        "icon_bg": (27, 90, 134),
        "bars": [0.55, 0.30, 0.68, 0.80],
        "config": None,  # de instellingen die al in dagscore.html staan
    },
    {
        "dir": "werk",
        "icon_bg": (32, 104, 88),
        "bars": [0.72, 0.38],
        "config": {
            "name": "Werkscore",
            "file": "WorkScores.csv",
            "storeKey": "werkscore.verstuurd.v1",
            "dayStartsAt": 7,
            # eenmalig: oude Stress-waarden 1–10 omzetten naar 0–5 (zie runMigration in dagscore.html)
            # en eenmalig: kolom Happyness hernoemen naar Happiness
            "migrations": [{"id": "werkstress-0-5", "col": "Stress"},
                           {"id": "werk-happiness-naam", "rename": ["Happyness", "Happiness"]}],
            "questions": [
                {"id": "happiness", "label": "Happiness?", "short": "Happy", **SCALE_10},
                {"id": "stress", "label": "Stress?", "short": "Stress", "type": "scale", "min": 0, "max": 5, "low": "geen", "high": "veel"},
                {"id": "unclenched", "label": "Unclenched?", "short": "Unclenched", **SCALE_10},
                {"id": "workload", "label": "Workload?", "short": "Workload", **SCALE_10},
                {"id": "comment", "label": "Comment", "short": "Comment", "type": "text"},
            ],
        },
    },
    {
        "dir": "ochtend",
        "icon_bg": (176, 98, 18),
        "bars": [0.40, 0.62, 0.80],
        "config": {
            "name": "Ochtendscore",
            "file": "MorningScores.csv",
            "storeKey": "ochtendscore.verstuurd.v1",
            "dayStartsAt": 0,  # 's ochtends invullen hoort bij vandaag
            "questions": [
                {"id": "slaap", "label": "Slaap?", "short": "Slaap", "type": "slider", "min": 1, "max": 10, "step": 0.5},
                {"id": "wakker", "label": "Wakker?", "short": "Wakker", "type": "slider", "min": 0, "max": 4, "step": 0.5, "default": 0.5},
                {"id": "gevoel", "label": "Gevoel?", "short": "Gevoel", "type": "scale", "min": 1, "max": 10, "low": "slecht", "high": "goed"},
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


def build_icon(out_dir: Path, bg, heights, size: int = 180) -> None:
    if Image is None:
        print("  (Pillow ontbreekt: bestaand icoon blijft staan)")
        return
    # Staafjes als niveaumeter, net als de schalen in de app
    fg = (250, 252, 253)
    img = Image.new("RGB", (size, size), bg)
    d = ImageDraw.Draw(img)
    n = len(heights)
    bar_w, gap = size * (0.13 if n > 2 else 0.17), size * 0.07
    total = n * bar_w + (n - 1) * gap
    x0, base = (size - total) / 2, size * 0.78
    for i, h in enumerate(heights):
        x = x0 + i * (bar_w + gap)
        top = base - h * size * 0.56
        d.rounded_rectangle([x, top, x + bar_w, base], radius=bar_w * 0.32, fill=fg)
    img.save(out_dir / "apple-touch-icon.png")


if __name__ == "__main__":
    src = SRC.read_text(encoding="utf-8")
    for app in APPS:
        out_dir = OUT / app["dir"] if app["dir"] else OUT
        out_dir.mkdir(parents=True, exist_ok=True)
        app_src, name = variant(src, app["config"])
        build_html(app_src, name, out_dir)
        build_icon(out_dir, app["icon_bg"], app["bars"])
        print(f"Klaar: {name} -> {out_dir / 'index.html'}")
