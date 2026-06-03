"""Générateur de visuels « Le Terminal » (cartes-citation + schémas pédago).

100 % local, gratuit, à la charte. Produit des PNG 1080x1350 (format LinkedIn
portrait 4:5) dans posts/visuals/out/.

  python posts/visuals/make_visuals.py

⚠️ Conformité : aucun visuel ne montre de montants/gains réels. Les schémas sont
illustratifs. Les cartes ne contiennent jamais de promesse de gain.
"""

import os
from PIL import Image, ImageDraw, ImageFont

# --- Charte ----------------------------------------------------------------
BG = (11, 14, 17)        # fond quasi-noir « terminal »
FG = (255, 255, 255)     # texte principal
MUTED = (138, 146, 158)  # texte secondaire
ACCENT = (22, 199, 132)  # vert
RED = (235, 87, 87)      # rouge (schéma risque)

W, H = 1080, 1350
MARGIN = 96

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
REG = os.path.join(FONT_DIR, "DejaVuSans.ttf")

OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)


def _f(path, size):
    return ImageFont.truetype(path, size)


def _wordmark(d, x, y):
    """Petit carré accent + « LE TERMINAL » en lettres espacées."""
    d.rectangle([x, y, x + 24, y + 24], fill=ACCENT)
    f = _f(BOLD, 26)
    cx = x + 40
    for ch in "LE TERMINAL":
        d.text((cx, y - 2), ch, font=f, fill=FG)
        cx += d.textlength(ch, font=f) + 4


def _wrap(d, text, font, max_w):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if d.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _fit(d, text, max_w, max_h, hi=96, lo=40):
    """Trouve la plus grande taille de police qui tient dans la zone."""
    for size in range(hi, lo - 1, -2):
        font = _f(BOLD, size)
        lines = _wrap(d, text, font, max_w)
        lh = int(size * 1.28)
        if len(lines) * lh <= max_h:
            return font, lines, lh
    font = _f(BOLD, lo)
    return font, _wrap(d, text, font, max_w), int(lo * 1.28)


def carte_citation(texte, nom_fichier, handle="@LeTerminalFx"):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    _wordmark(d, MARGIN, MARGIN)

    # barre accent au-dessus de la citation
    top = 360
    d.rectangle([MARGIN, top, MARGIN + 90, top + 8], fill=ACCENT)

    font, lines, lh = _fit(d, texte, W - 2 * MARGIN, 620)
    y = top + 60
    for ln in lines:
        d.text((MARGIN, y), ln, font=font, fill=FG)
        y += lh

    # bas de carte : handle + filet
    d.line([MARGIN, H - 150, W - MARGIN, H - 150], fill=(32, 38, 44), width=2)
    d.text((MARGIN, H - 120), handle, font=_f(REG, 30), fill=MUTED)
    img.save(os.path.join(OUT, nom_fichier))
    return nom_fichier


def schema_risque_recompense(nom_fichier="schema_risque_recompense.png"):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    _wordmark(d, MARGIN, MARGIN)

    d.text((MARGIN, 320), "Risque / Récompense", font=_f(BOLD, 64), fill=FG)
    d.text((MARGIN, 410), "Pas besoin d'avoir raison souvent.",
           font=_f(REG, 36), fill=MUTED)

    base_y = 1050
    bar_w = 220
    # barre risque (rouge, hauteur 1)
    x1 = 200
    h1 = 220
    d.rectangle([x1, base_y - h1, x1 + bar_w, base_y], fill=RED)
    d.text((x1 + 30, base_y + 24), "Risque : 1", font=_f(BOLD, 36), fill=FG)
    # barre récompense (vert, hauteur 2)
    x2 = 660
    h2 = 440
    d.rectangle([x2, base_y - h2, x2 + bar_w, base_y], fill=ACCENT)
    d.text((x2, base_y + 24), "Objectif : 2", font=_f(BOLD, 36), fill=FG)

    d.text((MARGIN, H - 150),
           "Illustratif — aucun montant ni gain réel.",
           font=_f(REG, 28), fill=MUTED)
    img.save(os.path.join(OUT, nom_fichier))
    return nom_fichier


def schema_interets_composes(nom_fichier="schema_interets_composes.png"):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    _wordmark(d, MARGIN, MARGIN)

    d.text((MARGIN, 320), "Les intérêts composés", font=_f(BOLD, 60), fill=FG)
    d.text((MARGIN, 400), "Le temps fait le travail.", font=_f(REG, 36), fill=MUTED)

    # repère
    ox, oy = MARGIN, 1050          # origine
    ax_w, ax_h = W - 2 * MARGIN, 520
    d.line([ox, oy, ox + ax_w, oy], fill=(60, 68, 76), width=3)        # axe X (temps)
    d.line([ox, oy, ox, oy - ax_h], fill=(60, 68, 76), width=3)        # axe Y (valeur)

    # courbe exponentielle : plate au début, qui décolle
    pts = []
    for i in range(0, 101):
        t = i / 100
        val = (t ** 2.6)                 # croissance accélérée
        px = ox + t * ax_w
        py = oy - val * ax_h
        pts.append((px, py))
    d.line(pts, fill=ACCENT, width=8, joint="curve")

    d.text((ox, oy + 20), "Temps", font=_f(REG, 30), fill=MUTED)
    d.text((MARGIN, H - 150), "Illustratif — courbe de principe, sans montants.",
           font=_f(REG, 28), fill=MUTED)
    img.save(os.path.join(OUT, nom_fichier))
    return nom_fichier


if __name__ == "__main__":
    faits = []
    faits.append(carte_citation(
        "Tu n'es pas en retard. Tu vis juste la vie d'un autre.",
        "carte_vie_dun_autre.png"))
    faits.append(carte_citation(
        "La régularité bat l'intensité. À chaque fois.",
        "carte_regularite.png"))
    faits.append(carte_citation(
        "Ton pire ennemi n'est pas le marché. C'est toi.",
        "carte_pire_ennemi.png"))
    faits.append(schema_risque_recompense())
    faits.append(schema_interets_composes())
    print("Visuels générés dans posts/visuals/out/ :")
    for f in faits:
        print("  -", f)
