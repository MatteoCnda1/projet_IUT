#!/usr/bin/env python3
"""Identité de RudyLink Infrastructure : couleurs, polices, logo vectoriel.

La société fictive du projet reprend le nom et la charte « Console » de RudyLink
(micro-entreprise réelle de Mattéo Canada, rudylink.eu) : angles droits, traits de 1 px,
Space Grotesk + IBM Plex Mono, accent émeraude. Les textes du logo sont vectorisés
(fontTools), donc les SVG s'affichent à l'identique sans police installée.
"""
import pathlib
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

ICI = pathlib.Path(__file__).parent
POLICES = ICI / "fonts"

NOM = "RudyLink Infrastructure"
SIGNATURE = "Conseil et ingénierie des réseaux"
DOMAINE = "infra.rudylink.eu"          # sous-domaine proposé pour le site vitrine
CONTACT = "infra@rudylink.eu"          # alias à créer dans Cloudflare Email Routing

# Palette (charte « Console » de RudyLink Knowledge, OKLCH converti en sRGB)
C = {
    "encre": "#101217",       # texte principal, fond du symbole
    "papier": "#f3f4f6",      # fond clair
    "surface": "#fbfbfc",     # cartes, tableaux
    "remplissage": "#eceef1",
    "trait": "#cfd2d8",
    "trait_doux": "#e3e5e9",
    "corps": "#2b2f36",
    "secondaire": "#4d525b",
    "discret": "#6d727b",
    "emeraude": "#05893e",    # oklch(0.55 0.15 150) : accent unique
    "emeraude_fonce": "#006925",
    "emeraude_clair": "#b9eec2",
    "emeraude_nuit": "#53be70",
    "constellation": "#052216",  # vert profond du portail RudyLink (rudylink.eu)
    "nuit": "#0f1115", "nuit_surface": "#16181d", "nuit_trait": "#353941", "nuit_texte": "#eceef1",
    "danger": "#c13c3b", "alerte": "#ab7400", "info": "#0079b5",
}

# Une teinte par axe du cahier des charges (espacées de ~40° en OKLCH, L 0.55 C 0.13)
AXES = {
    "A": ("Architecture physique", "#a75c00"),
    "B": ("Architecture réseaux", "#0079b5"),
    "C": ("Architecture système", "#6466bb"),
    "D": ("WAN et interconnexion", "#008889"),
    "E": ("Sécurité et juridique", "#b14e49"),
    "F": ("Coûts", "#8a6f00"),
    "G": ("Gestion de projet", "#97549b"),
    "I": ("Innovation", "#298646"),
    "L": ("Livrables", "#4d525b"),
}

_cache = {}


def police(nom):
    if nom not in _cache:
        _cache[nom] = TTFont(POLICES / f"{nom}.woff")
    return _cache[nom]


SG = "space-grotesk-latin-600-normal"
SG5 = "space-grotesk-latin-500-normal"
MONO = "ibm-plex-mono-latin-500-normal"


def texte(chaine, nom_police, taille, x, y, interlettre=0.0):
    """Chemin SVG du texte (ligne de base en y) et sa largeur, en unités SVG."""
    f = police(nom_police)
    gs, cmap = f.getGlyphSet(), f.getBestCmap()
    upm = f["head"].unitsPerEm
    k = taille / upm
    d, cx = [], x
    for i, ch in enumerate(chaine):
        g = cmap.get(ord(ch))
        if g is None:
            raise ValueError(f"glyphe absent : {ch!r} dans {nom_police}")
        pen = SVGPathPen(gs)
        gs[g].draw(TransformPen(pen, (k, 0, 0, -k, cx, y)))
        d.append(pen.getCommands())
        cx += gs[g].width * k + (interlettre * taille if i < len(chaine) - 1 else 0)
    return " ".join(p for p in d if p), cx - x


# Symbole : la hiérarchie trois couches (1 cœur, 2 distributions, 3 accès), maillée et redondée.
NOEUDS = {"c": (48, 22), "d1": (30, 48), "d2": (66, 48), "a1": (18, 74), "a2": (48, 74), "a3": (78, 74)}
LIENS = [("c", "d1"), ("c", "d2"), ("d1", "d2"), ("d1", "a1"), ("d1", "a2"), ("d2", "a2"), ("d2", "a3")]


def symbole(x=0, y=0, taille=96, fond=C["encre"], noeud=C["papier"], coeur=C["emeraude"], lien=None):
    k = taille / 96
    lien = lien or noeud
    out = [f'<rect x="{x}" y="{y}" width="{taille}" height="{taille}" fill="{fond}"/>']
    for a, b in LIENS:
        (x1, y1), (x2, y2) = NOEUDS[a], NOEUDS[b]
        out.append(f'<line x1="{x + x1 * k:.2f}" y1="{y + y1 * k:.2f}" x2="{x + x2 * k:.2f}" y2="{y + y2 * k:.2f}" '
                   f'stroke="{lien}" stroke-opacity="0.6" stroke-width="{3 * k:.2f}"/>')
    for n, (cx, cy) in NOEUDS.items():
        s = 12 * k
        out.append(f'<rect x="{x + cx * k - s / 2:.2f}" y="{y + cy * k - s / 2:.2f}" width="{s:.2f}" height="{s:.2f}" '
                   f'fill="{coeur if n == "c" else noeud}"/>')
    return "\n".join(out)


VARIANTES = {
    # nom : (fond de page, fond du symbole, nœuds, cœur, texte, sous-titre)
    "couleur": (None, C["encre"], C["papier"], C["emeraude"], C["encre"], C["secondaire"]),
    "inverse": (C["encre"], C["papier"], C["encre"], C["emeraude"], C["papier"], "#a4a9b1"),
    "constellation": (C["constellation"], C["papier"], C["constellation"], C["emeraude"], "#f2f5ef", "#9fc7ad"),
    "mono": (None, C["encre"], "#ffffff", "#ffffff", C["encre"], C["encre"]),
}


def _svg(w, h, corps, fond, titre):
    bg = f'<rect width="{w}" height="{h}" fill="{fond}"/>' if fond else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}" '
            f'role="img" aria-label="{titre}"><title>{titre}</title>{bg}{corps}</svg>\n')


def logo_horizontal(variante="couleur", marge=0):
    fond, sf, sn, sc, tx, st = VARIANTES[variante]
    m = marge
    p1, w1 = texte("RudyLink", SG, 56, m + 96 + 26, m + 50, -0.02)
    p2, w2 = texte("INFRASTRUCTURE", MONO, 15.5, m + 96 + 28, m + 86, 0.16)
    w = m + 96 + 26 + max(w1, w2) + 4 + m
    corps = symbole(m, m, 96, sf, sn, sc) + f'<path d="{p1}" fill="{tx}"/><path d="{p2}" fill="{st}"/>'
    return _svg(w, 96 + 2 * m, corps, fond, NOM)


def logo_vertical(variante="couleur", marge=0):
    fond, sf, sn, sc, tx, st = VARIANTES[variante]
    m = marge
    _, w1 = texte("RudyLink", SG, 60, 0, 0, -0.02)
    _, w2 = texte("INFRASTRUCTURE", MONO, 20, 0, 0, 0.12)
    w = max(w1, w2, 120) + 2 * m
    p1, _ = texte("RudyLink", SG, 60, (w - w1) / 2, m + 120 + 30 + 46, -0.02)
    p2, _ = texte("INFRASTRUCTURE", MONO, 20, (w - w2) / 2, m + 120 + 30 + 86, 0.12)
    corps = symbole((w - 120) / 2, m, 120, sf, sn, sc) + f'<path d="{p1}" fill="{tx}"/><path d="{p2}" fill="{st}"/>'
    return _svg(w, m + 120 + 30 + 94 + m, corps, fond, NOM)


def logo_symbole(variante="couleur", taille=96):
    fond, sf, sn, sc, *_ = VARIANTES[variante]
    return _svg(taille, taille, symbole(0, 0, taille, sf, sn, sc), None, NOM)


def css_polices(chemin="fonts"):
    """@font-face communs (polices servies à côté des pages)."""
    faces = [("Space Grotesk", "space-grotesk", w) for w in (400, 500, 600, 700)] + \
            [("IBM Plex Mono", "ibm-plex-mono", w) for w in (400, 500, 600)]
    return "\n".join(
        f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:normal;font-display:swap;"
        f"src:url('{chemin}/{fic}-latin-{w}-normal.woff2') format('woff2'),url('{chemin}/{fic}-latin-{w}-normal.woff') format('woff')}}"
        for fam, fic, w in faces)


def ecrire_logos(dossier):
    dossier = pathlib.Path(dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    fichiers = {}
    for v in ("couleur", "inverse", "constellation", "mono"):
        fichiers[f"rudylink-infrastructure-{v}.svg"] = logo_horizontal(v, marge=24 if VARIANTES[v][0] else 0)
        fichiers[f"rudylink-infrastructure-vertical-{v}.svg"] = logo_vertical(v, marge=32 if VARIANTES[v][0] else 0)
    fichiers["symbole.svg"] = logo_symbole("couleur")
    fichiers["symbole-inverse.svg"] = logo_symbole("inverse")
    fichiers["favicon.svg"] = logo_symbole("couleur", 32)
    for nom, svg in fichiers.items():
        (dossier / nom).write_text(svg, encoding="utf-8")
    return list(fichiers)


if __name__ == "__main__":
    print(ecrire_logos(ICI.parent / "livrables" / "communication" / "logo"))
