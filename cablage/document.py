"""Document « Implantation de l'infrastructure » : où est chaque élément, quelle salle est
desservie par quel local, par où passent les câbles et les fibres.
Écrit livrables/plan_cablage/implantation.html et implantation.pdf (Chrome sans interface)."""
import datetime
import html
import json
import math
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "livrables" / "plan_cablage"
CHIFFRAGE = HERE.parent / "chiffrage" / "estimation.json"
NOMS = {"N-1": "Sous-sol", "N0": "Rez-de-chaussée", "N1": "Étage 1"}
TYPES_SALLE = {"tp": "salle de TP", "projet": "salle de projet", "cours": "salle de cours/TD", "accueil": "accueil",
               "bureau": "bureau", "atelier": "atelier", "prepa": "préparation", "vie": "vie étudiante", "amphi": "amphithéâtre",
               "circulation": "circulation", "parking": "parking", "salle_serveur": "salle serveur", "technique": "local technique"}
e = html.escape

CSS = """
@page { size: A4; margin: 14mm 13mm 16mm; }
* { box-sizing: border-box; }
body { font-family: 'DejaVu Sans', 'Liberation Sans', sans-serif; font-size: 9.2pt; color: #211F1C; line-height: 1.45; margin: 0; }
h1 { font-family: 'DejaVu Serif', serif; font-size: 22pt; margin: 0 0 2mm; }
h2 { font-family: 'DejaVu Serif', serif; font-size: 14pt; margin: 8mm 0 2.5mm; padding-bottom: 1.5mm; border-bottom: 1.5px solid #1F4E8C; color: #1F4E8C; }
h3 { font-size: 10.5pt; margin: 5mm 0 2mm; }
p { margin: 1.5mm 0; }
.sous { color: #6C6861; font-size: 9pt; }
.cles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 3mm; margin: 4mm 0; }
.cle { border: 1px solid #DEDAD1; border-radius: 2mm; padding: 2.5mm 3mm; background: #F6F4EF; }
.cle b { display: block; font-size: 15pt; color: #1F4E8C; }
table { width: 100%; border-collapse: collapse; margin: 2mm 0 3mm; font-size: 8.2pt; }
th { text-align: left; background: #EAF0F8; color: #0E2240; font-weight: bold; padding: 1.4mm 1.8mm; border-bottom: 1px solid #C9D8EC; }
td { padding: 1.2mm 1.8mm; border-bottom: 1px solid #E8E5DE; vertical-align: top; }
tr { page-break-inside: avoid; }
td.n, th.n { text-align: right; white-space: nowrap; }
.chemin { color: #3A3833; font-size: 7.6pt; }
.lt01 { color: #2C6E8C; font-weight: bold; } .lt02 { color: #8C682C; font-weight: bold; }
img { width: 100%; border: 1px solid #DEDAD1; margin: 2mm 0; }
.saut { page-break-before: always; }
.note { border-left: 3px solid #A85A07; background: #FBF4EA; padding: 2mm 3mm; margin: 3mm 0; }
ul { margin: 1mm 0 2mm 5mm; padding: 0; } li { margin: 0.6mm 0; }
"""


def classe_lt(code):
    return "lt01" if code.endswith("LT01") else "lt02"


def voisins(niv, x, y, n=2):
    cand = [s for s in niv["salles"] if s.get("surface") and s["type"] in TYPES_SALLE and s["type"] not in ("technique",)]
    cand.sort(key=lambda s: math.hypot(s["x"] - x, s["y"] - y))
    return [s["nom"] for s in cand[:n]]


def court(passage, code):
    return passage.replace(f" → {code}", "") if passage else "—"


def implantation(data, prises, locaux, srv, baies, rocades, adductions, resume, wifi):
    niveaux = {n["code"]: n for n in data["niveaux"]}
    date = datetime.date.today().strftime("%d/%m/%Y")
    t = resume["par_type"]
    H = [f"<!doctype html><html lang='fr'><head><meta charset='utf-8'><title>Implantation de l'infrastructure</title><style>{CSS}</style></head><body>",
         "<h1>Implantation de l'infrastructure réseau</h1>",
         f"<p class='sous'>Site de Marseille · IUT Génie Télécom, Luminy · point 04 du cahier des charges · {date}<br>"
         "Où se trouve chaque élément, quelle salle est desservie par quel local technique, et par où passent les câbles et les fibres. "
         "Plans à l'échelle et repères dans <code>plans/</code> et <code>prises.csv</code>.</p>",
         "<div class='cles'>",
         f"<div class='cle'><b>{resume['prises']}</b>prises RJ45 Cat6A</div>",
         f"<div class='cle'><b>{t['wifi']}</b>bornes Wi-Fi</div>",
         f"<div class='cle'><b>6 + 1</b>locaux techniques + salle serveur</div>",
         f"<div class='cle'><b>{resume['lien_max_m']:.0f} m</b>câble le plus long (max. 90 m)</div>",
         "</div>",
         "<h2>1. Principe</h2>",
         "<ul><li><b>Salle serveur</b> au centre du sous-sol : cœur du réseau, distribution, accès Internet, DMZ, serveurs, administration.</li>",
         "<li><b>6 locaux techniques</b> (2 par niveau) : chacun reçoit une baie avec les switchs d'accès et les panneaux de brassage des salles voisines.</li>",
         "<li><b>Câble cuivre Cat6A</b> de chaque prise jusqu'au local technique de son niveau : goulotte dans la salle, puis chemin de câbles en faux plafond dans les couloirs.</li>",
         "<li><b>Fibre optique OM4</b> entre chaque local technique et la salle serveur, deux câbles par deux chemins différents (voies A et B), par deux colonnes montantes.</li>",
         "<li><b>Deux arrivées opérateur</b> séparées (façades ouest et est) : une coupure de tranchée ne prive pas le bâtiment d'Internet.</li></ul>",
         "<h2>2. Salle serveur</h2>",
         f"<p><b>Où :</b> sous-sol, partie sud de la <b>SALLE J05</b>, cloisonnée sur environ {srv['surface']:.0f} m², contre le local technique N-1-LT01 "
         "et le couloir CIRC 03. C'est le point le plus central du bâtiment : les fibres vers les étages y sont les plus courtes.</p>"]
    try:
        ch = json.loads(CHIFFRAGE.read_text(encoding="utf-8"))
        zones = {}
        for l in ch["capex_lignes"]:
            if l["categorie"] in ("Egress / WAN", "Sécurité interne", "DMZ", "Cœur", "Distribution", "Net Management", "Datacenter") and l["quantite"]:
                zones.setdefault(l["categorie"], []).append(f"{l['schema']} ({l['solution'].split(' + ')[0]})")
        H.append("<table><tr><th>Zone</th><th>Équipements installés dans la salle serveur</th></tr>")
        for z, items in zones.items():
            H.append(f"<tr><td><b>{e(z)}</b></td><td>{e(' · '.join(items))}</td></tr>")
        H.append("</table>")
    except (OSError, KeyError, ValueError):
        pass
    H.append("<p><b>Aménagement :</b> 2 baies 42U, onduleurs en double alimentation A/B, climatisation de précision N+1, contrôle d'accès par badge (B), "
             "caméra (C). Sous-sol : plancher technique et détection de fuite d'eau à prévoir, cloison coupe-feu.</p>")

    # Locaux techniques
    H.append("<h2>3. Locaux techniques</h2><table><tr><th>Local</th><th>Où</th><th class='n'>Surface</th><th>Baie</th><th class='n'>Switchs</th>"
             "<th class='n'>Prises</th><th>Salles desservies</th></tr>")
    bb = {b["local"]: b for b in baies}
    for code, lt in locaux.items():
        b = bb[code]
        niv = niveaux[lt["niveau"]]
        salles = sorted({p["salle"] for p in prises if p["local"] == code and p["type"] == "usager"})
        H.append(f"<tr><td class='{classe_lt(code)}'>{code}</td><td>{NOMS[lt['niveau']]}, salle « {e(lt['nom'])} » du plan, "
                 f"à côté de {e(' et '.join(voisins(niv, lt['x'], lt['y'])))}</td><td class='n'>{lt['surface']:.0f} m²</td>"
                 f"<td>{b['baie']} ({b['hauteur_U']}U)</td><td class='n'>{b['switchs_48p']}</td><td class='n'>{b['prises']}</td>"
                 f"<td class='chemin'>{e(', '.join(salles))}</td></tr>")
    H.append("</table><p class='note'>Le local N0-LT01 (RDC nord) est un placard d'environ 2 m² : baie murale, porte ventilée. "
             "Le local N1-LT02 dessert toute l'aile sud de l'étage (salles de TP) : baie au sol 42U.</p>")

    # Colonnes, fibres, adductions
    H.append("<h2>4. Colonnes montantes, fibres et arrivées opérateur</h2>"
             "<p><b>Colonne Nord :</b> part du vide sanitaire du sous-sol, monte à l'aplomb du local N0-LT01 (RDC, aile nord) puis jusqu'à l'étage. "
             "<b>Colonne Sud :</b> part du plafond du parking, monte à l'aplomb des locaux N0-LT02 et N1-LT02 (aile sud). "
             "Chaque local a sa voie A par la colonne la plus proche et sa voie B par l'autre : une colonne coupée n'isole aucun local.</p>"
             "<table><tr><th>Local</th><th>Voie</th><th>Chemin de la fibre (depuis la salle serveur)</th><th class='n'>Longueur</th></tr>")
    for r in rocades:
        H.append(f"<tr><td class='{classe_lt(r['local'])}'>{r['local']}</td><td>{r['voie']}</td><td class='chemin'>{e(r.get('chemin', r['par']))}</td>"
                 f"<td class='n'>{r['longueur']:.0f} m</td></tr>")
    H.append("</table><table><tr><th>Opérateur</th><th>Entrée dans le bâtiment</th><th>Chemin jusqu'à la salle serveur</th><th class='n'>Longueur</th></tr>")
    for a in adductions:
        H.append(f"<tr><td><b>{a['operateur']}</b></td><td>{e(a['entree'])}</td><td class='chemin'>{e(a.get('chemin', ''))}</td>"
                 f"<td class='n'>{a['longueur_interne']:.0f} m</td></tr>")
    H.append("</table><img src='synoptique.png' alt='Synoptique des fibres'>")

    # Par niveau
    for k, code in enumerate(("N-1", "N0", "N1")):
        niv = niveaux[code]
        mes = [p for p in prises if p["niveau"] == code]
        H.append(f"<h2 class='saut'>{5 + k}. {NOMS[code]}</h2><img src='plans/{code}_cablage.png' alt='Plan de câblage {NOMS[code]}'>")
        H.append("<table><tr><th>Salle</th><th>Usage</th><th class='n'>Prises</th><th>Équipements</th><th>Local</th>"
                 "<th>Les câbles passent par</th><th class='n'>Plus long</th></tr>")
        par_salle = {}
        for p in mes:
            par_salle.setdefault(p["salle"], []).append(p)
        typ = {s["nom"]: s["type"] for s in niv["salles"]}
        for nom in sorted(par_salle, key=lambda n: (typ.get(n, "") in ("circulation", "parking", "technique"), n)):
            ps = par_salle[nom]
            nu = sum(p["type"] == "usager" for p in ps)
            eq = [p.get("repere", p["type"]) for p in ps if p["type"] != "usager"]
            loc = Counter(p["local"] for p in ps).most_common(1)[0][0]
            pas = Counter(court(p.get("passage", ""), loc) for p in ps).most_common(1)[0][0]
            tel = " · 1 tél. IP" if any(p["poe"] == "telephone" for p in ps) else ""
            H.append(f"<tr><td><b>{e(nom)}</b></td><td>{e(TYPES_SALLE.get(typ.get(nom, ''), ''))}</td><td class='n'>{nu or '—'}</td>"
                     f"<td>{e(', '.join(eq))}{tel}</td><td class='{classe_lt(loc)}'>{loc}</td><td class='chemin'>{e(pas or 'directement')}</td>"
                     f"<td class='n'>{max(p['longueur'] for p in ps):.0f} m</td></tr>")
        H.append("</table>")
        rem = [p for p in mes if p.get("remarque")]
        if rem:
            H.append(f"<p class='note'>{e(rem[0]['remarque'])} : {e(', '.join(sorted({p['salle'] for p in rem})))}.</p>")

    # Équipements
    H.append("<h2 class='saut'>8. Bornes Wi-Fi, caméras et badgeuses</h2>"
             "<p>Bornes placées d'après l'étude Wi-Fi prédictive (<code>wifi/</code>) : au plafond, alimentées par leur câble (PoE+). "
             "Caméras et badgeuses sur des réseaux séparés (VLAN vidéo et contrôle d'accès).</p>"
             "<table><tr><th>Repère</th><th>Niveau</th><th>Salle</th><th>Détail</th><th>Local</th><th class='n'>Câble</th></tr>")
    ordre = {"wifi": 0, "camera": 1, "badge": 2}
    for p in sorted((p for p in prises if p["type"] != "usager"), key=lambda p: (ordre[p["type"]], p["niveau"], p.get("repere", ""))):
        det = p["usage"].split(",")[0] if p["type"] != "wifi" else p["usage"].replace("borne ", "").replace(", au plafond", "")
        H.append(f"<tr><td><b>{e(p.get('repere', ''))}</b></td><td>{NOMS[p['niveau']]}</td><td>{e(p['salle'])}</td><td>{e(det)}</td>"
                 f"<td class='{classe_lt(p['local'])}'>{p['local']}</td><td class='n'>{p['longueur']:.0f} m</td></tr>")
    H.append("</table>")
    H.append("<h2>9. Repérage et règles de pose</h2><ul>"
             "<li>Chaque prise porte un repère <b>&lt;local&gt;-P&lt;numéro&gt;</b> (ex. N0-LT02-P017), identique sur la prise et au panneau de brassage (TIA-606). La liste complète est dans <code>prises.csv</code>.</li>"
             "<li>Câble Cat6A U/FTP, Euroclasse Cca-s1b,d1,a1 ; lien permanent ≤ 90 m (ISO/IEC 11801-1, EN 50173-1).</li>"
             "<li>Chemins de câbles en faux plafond des couloirs, séparés des courants forts (EN 50174-2) ; traversées de murs rebouchées coupe-feu.</li>"
             "<li>Longueurs estimées : 1,10 × cheminement sur plan + 3 m de descentes + 2 m de réserve ; échelle des plans ±2 %.</li>"
             "</ul><p class='note'>À valider avec le client : emplacement des chambres de tirage des opérateurs, passage en vide sanitaire et au plafond du parking, "
             "salle serveur dans J05, mesure Wi-Fi sur site.</p></body></html>")
    page = OUT / "implantation.html"
    page.write_text("\n".join(H), encoding="utf-8")
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if chrome:
        with tempfile.TemporaryDirectory() as prof:
            subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", f"--user-data-dir={prof}", "--no-pdf-header-footer",
                            f"--print-to-pdf={OUT / 'implantation.pdf'}", page.as_uri()], check=True, capture_output=True, timeout=180)
