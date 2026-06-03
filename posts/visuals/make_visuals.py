"""Générateur de visuels « Le Terminal » (cartes-citation + schémas pédago).

100 % local, gratuit. Produit des PNG 1080x1350 (format LinkedIn portrait 4:5)
dans posts/visuals/out/.

  python posts/visuals/make_visuals.py

DIRECTION ARTISTIQUE (d'après le logo officiel) :
  - ambiance cinématique, sombre, luxe / aviation
  - fond noir profond avec dégradé + halo BLEU électrique (lueur des réacteurs)
  - typographie chrome/métal, argentée, en capitales pour le wordmark
  - accent BLEU (pas vert)

⚠️ Conformité : aucun visuel ne montre de montants/gains réels. Les schémas sont
illustratifs. Les cartes ne contiennent jamais de promesse de gain.
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# --- Charte (DA Le Terminal) ----------------------------------------------
GRAD_TOP = (16, 19, 24)     # haut du dégradé
GRAD_BOT = (6, 7, 10)       # bas du dégradé (presque noir)
FG = (245, 247, 250)        # texte principal (blanc cassé)
SILVER = (202, 208, 214)    # chrome du logo
MUTED = (140, 148, 160)     # texte secondaire
ACCENT = (61, 124, 255)     # bleu électrique (lueur réacteur)
RED = (235, 87, 87)         # rouge (schéma risque)

W, H = 1080, 1350
MARGIN = 96

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
REG = os.path.join(FONT_DIR, "DejaVuSans.ttf")

OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)


def _f(path, size):
    return ImageFont.truetype(path, size)


def _canvas():
    """Fond cinématique : dégradé vertical + halo bleu diffus en bas."""
    grad = Image.new("RGB", (1, H))
    for y in range(H):
        t = y / H
        grad.putpixel((0, y), tuple(
            int(GRAD_TOP[i] + (GRAD_BOT[i] - GRAD_TOP[i]) * t) for i in range(3)))
    img = grad.resize((W, H)).convert("RGBA")

    # halo bleu (réacteur) diffus, en bas à droite
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W * 0.50, H * 0.62, W * 1.08, H * 1.12], fill=(40, 90, 255, 110))
    gd.ellipse([W * -0.15, H * 0.70, W * 0.30, H * 1.05], fill=(40, 90, 255, 55))
    glow = glow.filter(ImageFilter.GaussianBlur(130))
    return Image.alpha_composite(img, glow).convert("RGB")


def _wordmark(d, x, y):
    """Carré accent bleu + « LE TERMINAL » en argent, lettres espacées."""
    d.rectangle([x, y, x + 24, y + 24], fill=ACCENT)
    f = _f(BOLD, 26)
    cx = x + 40
    for ch in "LE TERMINAL":
        d.text((cx, y - 2), ch, font=f, fill=SILVER)
        cx += d.textlength(ch, font=f) + 5


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
    for size in range(hi, lo - 1, -2):
        font = _f(BOLD, size)
        lines = _wrap(d, text, font, max_w)
        lh = int(size * 1.28)
        if len(lines) * lh <= max_h:
            return font, lines, lh
    font = _f(BOLD, lo)
    return font, _wrap(d, text, font, max_w), int(lo * 1.28)


def carte_citation(texte, nom_fichier, handle="@LeTerminalFx"):
    img = _canvas()
    d = ImageDraw.Draw(img)
    _wordmark(d, MARGIN, MARGIN)

    top = 360
    d.rectangle([MARGIN, top, MARGIN + 90, top + 8], fill=ACCENT)

    font, lines, lh = _fit(d, texte, W - 2 * MARGIN, 620)
    y = top + 60
    for ln in lines:
        d.text((MARGIN, y), ln, font=font, fill=FG)
        y += lh

    d.line([MARGIN, H - 150, W - MARGIN, H - 150], fill=(38, 44, 52), width=2)
    d.text((MARGIN, H - 120), handle, font=_f(REG, 30), fill=MUTED)
    img.save(os.path.join(OUT, nom_fichier))
    return nom_fichier


def schema_risque_recompense(nom_fichier="schema_risque_recompense.png"):
    img = _canvas()
    d = ImageDraw.Draw(img)
    _wordmark(d, MARGIN, MARGIN)

    d.text((MARGIN, 320), "Risque / Récompense", font=_f(BOLD, 64), fill=FG)
    d.text((MARGIN, 410), "Pas besoin d'avoir raison souvent.",
           font=_f(REG, 36), fill=MUTED)

    base_y, bar_w = 1050, 220
    d.rectangle([200, base_y - 220, 200 + bar_w, base_y], fill=RED)
    d.text((230, base_y + 24), "Risque : 1", font=_f(BOLD, 36), fill=FG)
    d.rectangle([660, base_y - 440, 660 + bar_w, base_y], fill=ACCENT)
    d.text((660, base_y + 24), "Objectif : 2", font=_f(BOLD, 36), fill=FG)

    d.text((MARGIN, H - 150), "Illustratif — aucun montant ni gain réel.",
           font=_f(REG, 28), fill=MUTED)
    img.save(os.path.join(OUT, nom_fichier))
    return nom_fichier


def schema_interets_composes(nom_fichier="schema_interets_composes.png"):
    img = _canvas()
    d = ImageDraw.Draw(img)
    _wordmark(d, MARGIN, MARGIN)

    d.text((MARGIN, 320), "Les intérêts composés", font=_f(BOLD, 60), fill=FG)
    d.text((MARGIN, 400), "Le temps fait le travail.", font=_f(REG, 36), fill=MUTED)

    ox, oy = MARGIN, 1050
    ax_w, ax_h = W - 2 * MARGIN, 520
    d.line([ox, oy, ox + ax_w, oy], fill=(60, 68, 76), width=3)
    d.line([ox, oy, ox, oy - ax_h], fill=(60, 68, 76), width=3)

    pts = []
    for i in range(0, 101):
        t = i / 100
        pts.append((ox + t * ax_w, oy - (t ** 2.6) * ax_h))
    d.line(pts, fill=ACCENT, width=8, joint="curve")

    d.text((ox, oy + 20), "Temps", font=_f(REG, 30), fill=MUTED)
    d.text((MARGIN, H - 150), "Illustratif — courbe de principe, sans montants.",
           font=_f(REG, 28), fill=MUTED)
    img.save(os.path.join(OUT, nom_fichier))
    return nom_fichier


def schema_deux_traders(nom_fichier="schema_deux_traders.png"):
    """2 courbes : discipline (bleu, tient) vs sans gestion du risque (rouge, s'effondre)."""
    img = _canvas()
    d = ImageDraw.Draw(img)
    _wordmark(d, MARGIN, MARGIN)

    d.text((MARGIN, 320), "2 traders, même départ", font=_f(BOLD, 58), fill=FG)
    d.text((MARGIN, 398), "La gestion du risque fait la différence.",
           font=_f(REG, 34), fill=MUTED)

    ox, oy = MARGIN, 1050
    ax_w, ax_h = W - 2 * MARGIN, 540
    d.line([ox, oy, ox + ax_w, oy], fill=(60, 68, 76), width=3)
    d.line([ox, oy, ox, oy - ax_h], fill=(60, 68, 76), width=3)

    disc, risky = [], []
    for i in range(0, 101):
        t = i / 100
        disc.append((ox + t * ax_w, oy - (0.10 + 0.72 * t) * ax_h))
        y = (0.10 + 1.6 * t) if t < 0.5 else (0.90 - 1.7 * (t - 0.5))
        risky.append((ox + t * ax_w, oy - max(y, 0.03) * ax_h))
    d.line(risky, fill=RED, width=7, joint="curve")
    d.line(disc, fill=ACCENT, width=8, joint="curve")

    # légende
    ly = oy + 24
    d.rectangle([ox, ly + 6, ox + 26, ly + 26], fill=ACCENT)
    d.text((ox + 38, ly), "Discipline / risque maîtrisé", font=_f(REG, 30), fill=FG)
    d.rectangle([ox, ly + 50, ox + 26, ly + 70], fill=RED)
    d.text((ox + 38, ly + 44), "Sans gestion du risque", font=_f(REG, 30), fill=FG)

    d.text((MARGIN, H - 120), "Illustratif — courbes de principe, sans montants.",
           font=_f(REG, 28), fill=MUTED)
    img.save(os.path.join(OUT, nom_fichier))
    return nom_fichier


def schema_levier(nom_fichier="schema_levier.png"):
    """Effet de levier : amplifie gains (bleu, haut) ET pertes (rouge, bas)."""
    img = _canvas()
    d = ImageDraw.Draw(img)
    _wordmark(d, MARGIN, MARGIN)

    d.text((MARGIN, 320), "L'effet de levier", font=_f(BOLD, 60), fill=FG)
    d.text((MARGIN, 400), "Il amplifie tout — gains ET pertes.",
           font=_f(REG, 34), fill=MUTED)

    base, bw = 820, 150
    d.line([MARGIN, base, W - MARGIN, base], fill=(60, 68, 76), width=3)
    # marché (petit, gris)
    d.rectangle([180, base - 90, 180 + bw, base], fill=(120, 128, 140))
    d.text((176, base + 20), "Marché : +1 %", font=_f(REG, 28), fill=MUTED)
    # gain amplifié (bleu, vers le haut)
    d.rectangle([500, base - 300, 500 + bw, base], fill=ACCENT)
    d.text((500, base + 20), "Gain ×levier", font=_f(BOLD, 28), fill=FG)
    # perte amplifiée (rouge, vers le bas)
    d.rectangle([820, base, 820 + bw, base + 300], fill=RED)
    d.text((820, base + 320), "Perte ×levier", font=_f(BOLD, 28), fill=FG)

    d.text((MARGIN, H - 120), "Illustratif — le levier amplifie dans les deux sens.",
           font=_f(REG, 28), fill=MUTED)
    img.save(os.path.join(OUT, nom_fichier))
    return nom_fichier


# Visuel à générer pour chacun des posts LinkedIn (dans l'ordre du calendrier).
LINKEDIN = [
    ("01_vie-dun-autre.png",     "carte", "Tu n'es pas en retard. Tu vis juste la vie d'un autre."),
    ("02_declic.png",            "carte", "2 ans de pertes. Puis le déclic."),
    ("03_2traders.png",          "deux_traders", None),
    ("04_zone-confort.png",      "carte", "Ta zone de confort est l'endroit le plus dangereux pour tes rêves."),
    ("05_routine.png",           "carte", "La motivation te lance. La routine te fait tenir."),
    ("06_arreter-copier.png",    "carte", "Le jour où j'ai arrêté de copier, tout a changé."),
    ("07_interets-composes.png", "interets", None),
    ("08_comparaison.png",       "carte", "Tu compares ton chapitre 1 au chapitre 20 d'un autre."),
    ("09_personne-te-sauver.png","carte", "Personne ne viendra te sauver. Et c'est une bonne nouvelle."),
    ("10_pire-perte.png",        "carte", "Ma pire perte ne m'a pas ruiné. Elle m'a réveillé."),
    ("11_pire-ennemi.png",       "carte", "Ton pire ennemi n'est pas le marché. C'est toi."),
    ("12_regularite.png",        "carte", "La régularité bat l'intensité. À chaque fois."),
    ("13_dire-non.png",          "carte", "Chaque « oui » est un « non » à autre chose."),
    ("14_failli-arreter.png",    "carte", "Après 18 mois de pertes, j'ai failli tout arrêter."),
    ("15_risque-recompense.png", "risque", None),
    # --- Semaine 3 ---
    ("16_cout-inaction.png",     "carte", "Ne rien faire est aussi un choix. Avec un prix."),
    ("17_famille.png",           "carte", "« Trouve un vrai métier. » J'ai quand même continué."),
    ("18_journal.png",           "carte", "Ton journal de trading vaut plus que ton prochain indicateur."),
    ("19_environnement.png",     "carte", "Tu deviens la moyenne de ce qui t'entoure."),
    ("20_energie.png",           "carte", "Ton énergie passe avant ta productivité."),
    ("21_couper-perte.png",      "carte", "Un bon trader perd petit. Et respecte son plan."),
    ("22_levier.png",            "levier", None),
]


def generer_linkedin():
    faits = []
    for nom, typ, texte in LINKEDIN:
        if typ == "carte":
            faits.append(carte_citation(texte, nom))
        elif typ == "deux_traders":
            faits.append(schema_deux_traders(nom))
        elif typ == "interets":
            faits.append(schema_interets_composes(nom))
        elif typ == "risque":
            faits.append(schema_risque_recompense(nom))
        elif typ == "levier":
            faits.append(schema_levier(nom))
    return faits


if __name__ == "__main__":
    faits = generer_linkedin()
    print(f"{len(faits)} visuels LinkedIn générés dans posts/visuals/out/ :")
    for f in faits:
        print("  -", f)
