"""Charte commune des livrables techniques de RudyLink Infrastructure (v2.1).

Une seule source pour tout ce qui doit être identique d'un livrable à l'autre :
  - la version du dossier et sa date (jamais la date du jour de génération) ;
  - la feuille de style des documents techniques (charte « Console » : Space Grotesk,
    IBM Plex Mono, encre #101217, émeraude #05893E, angles droits, filets de 1 px),
    reprise de livrables/communication/modeles/rudylink-document.css ;
  - l'en-tête avec logo, le cartouche sous le titre, le pied de page numéroté ;
  - le bloc « Suivi des versions » ;
  - la typographie française (espaces insécables) ;
  - l'impression en PDF par Chrome sans interface.

Usage dans un générateur (le dossier racine du dépôt doit être dans sys.path) :

    import sys
    sys.path.insert(0, str(ROOT))
    from commun import charte as CH

    html = CH.page(titre="Plan d'adressage IP et VLAN", titre_court="Plan d'adressage",
                   ref="RLI-ETU-003", points="05", dossier=OUT,
                   chapo="Une phrase qui dit ce que contient le document.",
                   corps="<h2>1. …</h2>…", css_extra=CSS_PROPRE_AU_DOCUMENT)
    CH.ecrire_et_imprimer(html, OUT / "plan_adressage.html", OUT / "plan_adressage.pdf")

Repères de version dans le texte : CH.badge("v2.1") ou CH.badge("v2") (classes .v21 et .v2).
Figures matplotlib autonomes : CH.mention_figure("14") pour la ligne de cartouche.
"""
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Version du dossier : les deux seules constantes à changer à la prochaine version
# ---------------------------------------------------------------------------
VERSION = "v2.1"
DATE_VERSION = "20/11/2026"
DATE_ISO = "2026-11-20"
MENTION = f"{VERSION} — {DATE_VERSION}"
ARCHIVE_PRECEDENTE = "livrables/archives/v2_2026-11-20/"

HISTORIQUE = [
    ("v1", "13/11/2026", "Première version de l'infrastructure (points 03, 04, 05, 14)."),
    ("v2", "15/11/2026", "Traitement des 9 constats de l'audit du 15/11/2026 (16,9/20)."),
    ("v2.1", "20/11/2026", "Audit v2.1 de tous les livrables : coquilles et incohérences corrigées, "
                           "BET thermique et électrique des locaux techniques, groupe électrogène ajouté, "
                           "charte commune, intégration continue."),
]

SOCIETE = "RudyLink Infrastructure"
SITE = "Site de Marseille"
BATIMENT = "IUT Génie Télécom, Luminy"
EQUIPE = "Mattéo Canada (chef de projet), Rafael Maunier, Solal Kruczinsky, Raphael Hovsepian"

FONTS = RACINE / "livrables" / "communication" / "fonts"
LOGO = RACINE / "livrables" / "communication" / "logo" / "rudylink-infrastructure-couleur.svg"

# Couleurs de la charte, pour matplotlib et les SVG
ENCRE = "#101217"
EMERAUDE = "#05893E"
EMERAUDE_FONCE = "#006925"
EMERAUDE_CLAIR = "#B9EEC2"
CORPS = "#2B2F36"
SECONDAIRE = "#4D525B"
DISCRET = "#6D727B"
TRAIT = "#CFD2D8"
REMPLISSAGE = "#ECEEF1"
ALERTE = "#AB7400"
ROUGE = "#C13C3B"


def rel(cible, dossier):
    """Chemin relatif POSIX de `cible` vu depuis `dossier` (pages portables, pas de chemin absolu)."""
    return Path(os.path.relpath(Path(cible).resolve(), Path(dossier).resolve())).as_posix()


def _polices(dossier):
    faces = [("Space Grotesk", "space-grotesk", w) for w in (400, 500, 600, 700)] + \
            [("IBM Plex Mono", "ibm-plex-mono", w) for w in (400, 500, 600)]
    base = rel(FONTS, dossier)
    return "\n".join(
        f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:normal;font-display:swap;"
        f"src:url('{base}/{fic}-latin-{w}-normal.woff2') format('woff2'),url('{base}/{fic}-latin-{w}-normal.woff') format('woff')}}"
        for fam, fic, w in faces)


_CSS = """
:root { --encre:#101217; --papier:#f3f4f6; --surface:#fbfbfc; --remplissage:#eceef1; --trait:#cfd2d8; --trait-doux:#e3e5e9;
  --corps:#2b2f36; --secondaire:#4d525b; --discret:#6d727b; --emeraude:#05893e; --emeraude-fonce:#006925; --emeraude-clair:#b9eec2;
  --alerte:#ab7400; --rouge:#c13c3b;
  --sans:'Space Grotesk','Arial',sans-serif; --mono:'IBM Plex Mono','Consolas','Courier New',monospace; }
@page { size: A4; margin: 14mm 13mm 16mm;
  @bottom-left { content: "RUDYLINK INFRASTRUCTURE · __TITRE_COURT__"; font: 500 6.8pt 'IBM Plex Mono','Consolas',monospace; color: #6d727b; letter-spacing: .06em; }
  @bottom-right { content: counter(page) " / " counter(pages); font: 500 6.8pt 'IBM Plex Mono','Consolas',monospace; color: #6d727b; } }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { margin: 0; font: 400 9.2pt/1.45 var(--sans); color: var(--corps); background: #fff; font-variant-numeric: tabular-nums; }
h1, h2, h3, h4 { color: var(--encre); font-weight: 600; text-wrap: balance; }
h1 { font-size: 22pt; line-height: 1.1; letter-spacing: -.02em; margin: 0 0 2mm; }
h2 { font-size: 14pt; line-height: 1.25; letter-spacing: -.01em; margin: 7mm 0 2.5mm; padding-bottom: 1.5mm; border-bottom: 1px solid var(--trait); }
h3 { font-size: 10.5pt; margin: 4.5mm 0 1.5mm; }
h4 { font-size: 9.5pt; margin: 3mm 0 1mm; }
p { margin: 1.5mm 0; }
ul, ol { margin: 1mm 0 2mm 5mm; padding: 0; } li { margin: .6mm 0; }
b, strong { color: var(--encre); font-weight: 600; }
a { color: var(--emeraude-fonce); }
code, .mono, pre { font-family: var(--mono); font-size: .92em; }
code { background: var(--remplissage); padding: 0 1mm; }
pre { background: var(--remplissage); padding: 2mm 3mm; white-space: pre-wrap; }
.entete { display: flex; justify-content: space-between; align-items: center; padding-bottom: 3mm; border-bottom: 1px solid var(--trait); margin-bottom: 5mm; }
.entete img { height: 10mm; }
.entete .label { text-align: right; }
.label { font: 500 6.8pt/1.3 var(--mono); letter-spacing: .07em; text-transform: uppercase; color: var(--discret); }
.sous { color: var(--secondaire); font-size: 8.6pt; }
.cartouche-ligne { font: 500 7.2pt/1.4 var(--mono); letter-spacing: .03em; color: var(--discret); margin: 0 0 1.5mm; }
.chapo { font-size: 10.5pt; line-height: 1.45; color: var(--secondaire); margin: 1mm 0 4mm; }
.cles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 3mm; margin: 4mm 0; }
.cle { border: 1px solid var(--trait); padding: 2.5mm 3mm; background: var(--surface); }
.cle b { display: block; font-size: 15pt; letter-spacing: -.02em; color: var(--encre); }
table { width: 100%; border-collapse: collapse; margin: 2mm 0 3mm; font-size: 8.2pt; }
th { text-align: left; font: 500 6.8pt var(--mono); letter-spacing: .05em; text-transform: uppercase; color: var(--secondaire);
  background: var(--remplissage); border-top: 1px solid var(--trait); border-bottom: 1px solid var(--trait); padding: 1.4mm 1.8mm; }
td { padding: 1.2mm 1.8mm; border-bottom: 1px solid var(--trait-doux); vertical-align: top; }
tr { break-inside: avoid; }
td.n, th.n { text-align: right; white-space: nowrap; } td.c, th.c { text-align: center; }
.chemin { color: var(--secondaire); font-size: 7.6pt; }
.lt01 { color: var(--emeraude-fonce); font-weight: 600; } .lt02 { color: var(--alerte); font-weight: 600; }
img { max-width: 100%; border: 1px solid var(--trait); margin: 2mm 0; }
.entete img { border: 0; margin: 0; }
.saut { break-before: page; }
.garde { break-inside: avoid; }
.note { border: 1px solid var(--trait); border-left: 3px solid var(--emeraude); background: var(--surface); padding: 2mm 3mm; margin: 3mm 0; break-inside: avoid; }
.note.alerte { border-left-color: var(--alerte); }
.ok { color: var(--emeraude-fonce); font-weight: 600; } .ko { color: var(--rouge); font-weight: 600; }
.v2, .v21 { display: inline-block; font: 600 6.4pt/1.2 var(--mono); letter-spacing: .04em; padding: .2mm 1.2mm; margin: 0 .8mm;
  vertical-align: .3mm; border: 1px solid currentColor; }
.v2 { color: var(--secondaire); }
.v21 { color: #fff; background: var(--emeraude); border-color: var(--emeraude); }
.suivi td:first-child { white-space: nowrap; font-family: var(--mono); }
"""


def css(dossier, titre_court):
    """Feuille de style complète, polices référencées depuis le dossier de la page."""
    titre = titre_court.upper().replace('"', "'")
    return _polices(dossier) + _CSS.replace("__TITRE_COURT__", titre)


def badge(version="v2.1"):
    cls = "v21" if version == "v2.1" else "v2"
    return f"<span class='{cls}'>{version}</span>"


def entete(ref, titre_court, dossier):
    return (f"<div class='entete'><img src='{rel(LOGO, dossier)}' alt='{SOCIETE}'>"
            f"<div class='label'>{titre_court}<br>{ref} · {MENTION}</div></div>")


def points_cdc(points):
    """'05' -> 'point 05 du cahier des charges' ; ['03', '06'] -> 'points 03 et 06 du cahier des charges'."""
    if isinstance(points, str):
        points = [points]
    if len(points) == 1:
        return f"point {points[0]} du cahier des charges"
    return "points " + ", ".join(points[:-1]) + " et " + points[-1] + " du cahier des charges"


def cartouche(points, ref):
    """Ligne de cartouche identique dans tous les livrables techniques."""
    return f"{SITE} · {BATIMENT} · {SOCIETE} · {points_cdc(points)} · {ref} · {MENTION}"


def mention_figure(points):
    """Ligne de cartouche pour une figure autonome (plan, synoptique, schéma matplotlib)."""
    p = points_cdc(points).replace(" du cahier des charges", "")
    return f"{SOCIETE} · {BATIMENT} · {p} · {MENTION}"


def bloc_suivi(ref, statut="En relecture", redige_par=EQUIPE, relu_par="toute l'équipe (pull request GitHub)", changements=None):
    """Tableau « Suivi des versions » : historique du dossier + changements propres au document."""
    lignes = []
    for v, d, txt in HISTORIQUE:
        if v == VERSION and changements:
            txt = changements
        lignes.append(f"<tr><td>{v}</td><td>{d}</td><td>{txt}</td></tr>")
    return (f"<h2>Suivi des versions</h2><table class='suivi'><tr><th>Version</th><th>Date</th><th>Changements</th></tr>"
            + "".join(lignes) + "</table>"
            f"<table><tr><th>Référence</th><th>Version</th><th>Statut</th><th>Rédigé par</th><th>Relu par</th></tr>"
            f"<tr><td>{ref}</td><td>{MENTION}</td><td>{statut}</td><td>{redige_par}</td><td>{relu_par}</td></tr></table>")


# ---------------------------------------------------------------------------
# Typographie française : espaces insécables (U+00A0), hors code et hors balises
# ---------------------------------------------------------------------------
NBSP = " "
_UNITES = (r"%|€|k€|M€|kW|kVA|kWh|MWh|kWc|W|VA|BTU/h|m²|m³/h|m³|mm|cm|km|m|min|h|°C|K|Go|To|Mo|Ko|Gb/s|Mb/s|"
           r"U|A|mA|V|kV|l/h|L/h|l|L|dB\(A\)|dBA|dBm|dB|MHz|GHz|ms|µs|s|t|kg|ans?|jours?|mois|postes?|ports?")
_RE_UNITE = re.compile(rf"(\d) ({_UNITES})(?![\w/])")
_RE_MILLIERS = re.compile(r"(?<![\d.,:/-])(\d{1,3})((?: \d{3})+)(?![\d])")
_RE_PONCT = re.compile(r" ([:;!?»])")
_RE_GUILL = re.compile(r"« ")
_PROTEGES = re.compile(r"(<(code|pre|script|style|svg)\b.*?</\2>|<[^>]+>)", re.S | re.I)


def _typo_texte(t):
    t = _RE_PONCT.sub(NBSP + r"\1", t)
    t = _RE_GUILL.sub("«" + NBSP, t)
    t = _RE_MILLIERS.sub(lambda m: m.group(1) + m.group(2).replace(" ", NBSP), t)
    t = _RE_UNITE.sub(r"\1" + NBSP + r"\2", t)
    return t


def typo_fr(html):
    """Applique les espaces insécables au texte d'une page HTML, sans toucher aux balises, au code ni aux SVG."""
    morceaux, pos = [], 0
    for m in _PROTEGES.finditer(html):
        morceaux.append(_typo_texte(html[pos:m.start()]))
        morceaux.append(m.group(0))
        pos = m.end()
    morceaux.append(_typo_texte(html[pos:]))
    return "".join(morceaux)


def nombre(x, decimales=0):
    """Nombre au format français : virgule décimale, insécable comme séparateur de milliers (dès 4 chiffres)."""
    s = f"{x:,.{decimales}f}".replace(",", NBSP).replace(".", ",")
    if decimales == 0 and abs(x) < 10000 and abs(x) >= 1000:
        s = s.replace(NBSP, NBSP)
    return s.replace("-", "−")


def euros(x, ht=True):
    return f"{nombre(round(x))}{NBSP}€{' HT' if ht else ''}"


# ---------------------------------------------------------------------------
# Page complète et impression
# ---------------------------------------------------------------------------
def page(titre, corps, dossier, ref, titre_court, points, chapo="", css_extra="", typo=True):
    """Document HTML complet : en-tête logo, titre, cartouche commun, chapô, corps."""
    tete = (f"<!doctype html><html lang='fr'><head><meta charset='utf-8'><title>{titre} · {SOCIETE}</title>"
            f"<style>{css(dossier, titre_court)}{css_extra}</style></head><body>")
    haut = (entete(ref, titre_court, dossier) + f"<h1>{titre}</h1>"
            f"<p class='cartouche-ligne'>{cartouche(points, ref)}</p>" + (f"<p class='chapo'>{chapo}</p>" if chapo else ""))
    html = tete + haut + corps + "</body></html>"
    return typo_fr(html) if typo else html


def chrome():
    return shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")


def imprimer_pdf(page_html, sortie, timeout=180):
    """Imprime une page HTML déjà écrite sur disque en PDF A4 (Chrome sans interface). Renvoie False sans Chrome."""
    exe = chrome()
    if not exe:
        print(f"  (Chrome introuvable : {Path(sortie).name} non régénéré)")
        return False
    with tempfile.TemporaryDirectory() as prof:
        subprocess.run([exe, "--headless=new", "--no-sandbox", "--disable-gpu", f"--user-data-dir={prof}",
                        "--no-pdf-header-footer", "--virtual-time-budget=5000", f"--print-to-pdf={sortie}",
                        Path(page_html).resolve().as_uri()], check=True, capture_output=True, timeout=timeout)
    return True


def ecrire_et_imprimer(html, page_html, sortie_pdf):
    Path(page_html).write_text(html, encoding="utf-8")
    return imprimer_pdf(page_html, sortie_pdf)
