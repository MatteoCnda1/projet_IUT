"""Document « Implantation de l'infrastructure réseau » (RLI-ETU-001, point 04) : où est chaque élément, quelle salle est
desservie par quel local, par où passent les câbles et les fibres.
Écrit livrables/plan_cablage/implantation.html et implantation.pdf (Chrome sans interface), à la charte commune (commun/charte.py).

v2.1 : charte commune ; liste des équipements de la salle serveur lue directement dans chiffrage/estimation.py (plus de boucle
avec estimation.json), contrôleurs Wi-Fi et enregistreur vidéo VS-NVR1 inclus ; aménagement de la salle repris du point 14 ;
voies B du sous-sol et adduction FAI 2 distinctes (points communs restants listés)."""
import html
import importlib.util
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from commun import charte as CH  # noqa: E402

OUT = ROOT / "livrables" / "plan_cablage"
ESTIMATION = ROOT / "chiffrage" / "estimation.py"
ENERGIE = ROOT / "livrables" / "energie_refroidissement" / "resume.json"
REF = "RLI-ETU-001"
NOMS = {"N-1": "Sous-sol", "N0": "Rez-de-chaussée", "N1": "Étage 1"}
TYPES_SALLE = {"tp": "salle de TP", "projet": "salle de projet", "cours": "salle de cours/TD", "accueil": "accueil",
               "bureau": "bureau", "atelier": "atelier", "prepa": "préparation", "vie": "vie étudiante", "amphi": "amphithéâtre",
               "circulation": "circulation", "parking": "parking", "salle_serveur": "salle serveur", "technique": "local technique"}
ZONES_SALLE = ("Egress / WAN", "Sécurité interne", "DMZ", "Cœur", "Distribution", "Net Management", "Datacenter")
V21 = CH.badge("v2.1")
CSS_IMPLANTATION = "td.lt01, td.lt02 { white-space: nowrap; }"   # seule règle propre à ce document (le reste : charte commune)
e = html.escape


def classe_lt(code):
    return "lt01" if code.endswith("LT01") else "lt02"


def voisins(niv, x, y, n=2):
    cand = [s for s in niv["salles"] if s.get("surface") and s["type"] in TYPES_SALLE and s["type"] not in ("technique",)]
    cand.sort(key=lambda s: math.hypot(s["x"] - x, s["y"] - y))
    return [s["nom"] for s in cand[:n]]


def court(passage, code):
    return passage.replace(f" → {code}", "") if passage else "—"


def designation(sol):
    """Désignation sans les options après « + », sans couper une parenthèse (« Kit de pile … (2 modules + câbles) »)."""
    return re.split(r" \+ (?![^()]*\))", sol)[0]


def lignes_chiffrage():
    """Lignes CAPEX du chiffrage, lues dans chiffrage/estimation.py (et non dans estimation.json, qui est écrit après ce
    document dans la chaîne de génération) : la liste de la salle serveur est donc toujours celle du plan de câblage du jour."""
    try:
        spec = importlib.util.spec_from_file_location("estimation_chiffrage", ESTIMATION)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return [dict(categorie=c, schema=s, solution=so, quantite=q) for c, s, so, q, _pu, _n in mod.CAPEX]
    except (OSError, KeyError, ValueError, ImportError, AttributeError):
        return []


def implantation(data, prises, locaux, srv, baies, rocades, adductions, resume, wifi):
    niveaux = {n["code"]: n for n in data["niveaux"]}
    t = resume["par_type"]
    nrj = json.loads(ENERGIE.read_text(encoding="utf-8")) if ENERGIE.exists() else {}
    clim_kw = CH.nombre(nrj["clim"]["unite_kw"], 1) if nrj.get("clim") else "7,1"
    cam_srv = next((p for p in prises if p["salle"] == "SALLE SERVEUR" and p["type"] == "camera"), {})
    bad_srv = next((p for p in prises if p["salle"] == "SALLE SERVEUR" and p["type"] == "badge"), {})
    porte = (bad_srv.get("passage") or "CIRC 03").split(" → ")[0]
    communs = resume.get("points_communs", {})
    add_commun = communs.get("adductions", [])
    roc_communs = {k: v for k, v in communs.items() if k != "adductions"}
    H = ["<div class='note'><b>Version 2.1 — 20/11/2026.</b> La version 2 est archivée dans "
         f"<code>{CH.ARCHIVE_PRECEDENTE}</code>. Changements dans ce document (repérés {V21}) : caméra du foyer des étudiants retirée "
         f"({t['camera']} caméras, CNIL) ; enregistreur vidéo VS-NVR1 dans la salle serveur ; voies B du sous-sol et arrivée FAI 2 tracées "
         "par d'autres circulations que la voie A ; câbles écartés de la gaine d'ascenseur ; contrôleurs Wi-Fi ajoutés à la liste de la salle "
         "serveur ; aménagement de la salle repris du point 14 ; repères uniques des bornes, caméras et badgeuses.</div>",
         "<div class='cles'>",
         f"<div class='cle'><b>{resume['prises']}</b>prises RJ45 Cat6A</div>",
         f"<div class='cle'><b>{t['wifi']}</b>bornes Wi-Fi</div>",
         "<div class='cle'><b>6 + 1</b>locaux techniques + salle serveur</div>",
         f"<div class='cle'><b>{resume['lien_max_m']:.0f} m</b>câble le plus long (max. 90 m)</div>",
         "</div>",
         "<h2>1. Principe</h2>",
         "<ul><li><b>Salle serveur</b> au centre du sous-sol : cœur du réseau, distribution, accès Internet, DMZ, serveurs, administration.</li>",
         "<li><b>6 locaux techniques</b> (2 par niveau) : chacun reçoit une baie avec les switchs d'accès et les panneaux de brassage des salles voisines.</li>",
         "<li><b>Câble cuivre Cat6A</b> de chaque prise jusqu'au local technique de son niveau : goulotte dans la salle, puis chemin de câbles en faux plafond dans les couloirs.</li>",
         "<li><b>Fibre optique OM4</b> entre chaque local technique et la salle serveur, deux câbles par deux chemins différents (voies A et B) : "
         f"par les deux colonnes montantes pour le RDC et l'étage, par deux circulations différentes au sous-sol {V21}.</li>",
         "<li><b>Deux arrivées opérateur</b> séparées (façades ouest et est) : une coupure de tranchée ne prive pas le bâtiment d'Internet"
         + (f". À l'intérieur, les deux fourreaux traversent tous deux le {e(', '.join(add_commun))}, seul passage du côté est vers la salle serveur "
            f"(section 4) {V21}.</li></ul>" if add_commun else f" ; à l'intérieur, leurs chemins n'ont aucune circulation commune {V21}.</li></ul>"),
         "<h2>2. Salle serveur</h2>",
         f"<p><b>Où :</b> sous-sol, partie sud de la <b>SALLE J05</b>, cloisonnée sur environ {srv['surface']:.0f} m², contre le local technique N-1-LT01 "
         f"et le couloir {e(porte)} (porte, badgeuse). C'est le point le plus central du bâtiment : les fibres vers les étages y sont les plus courtes.</p>"]
    zones = {}
    for lg in lignes_chiffrage():
        dans_salle = (lg["categorie"] in ZONES_SALLE or lg["schema"].startswith("WLC")
                      or (lg["categorie"] == "Sûreté" and lg["schema"].startswith("VS-")))
        if dans_salle and lg["quantite"]:
            z = "Accès (contrôleurs Wi-Fi)" if lg["schema"].startswith("WLC") else ("Sûreté" if lg["categorie"] == "Sûreté" else lg["categorie"])
            zones.setdefault(z, []).append(f"{lg['schema']} ({designation(lg['solution'])})")
    if zones:
        H.append("<table><tr><th>Zone</th><th>Équipements installés dans la salle serveur</th></tr>")
        for z, items in zones.items():
            nv = f" {V21}" if z in ("Accès (contrôleurs Wi-Fi)", "Sûreté") else ""
            H.append(f"<tr><td><b>{e(z)}</b>{nv}</td><td>{e(' · '.join(items))}</td></tr>")
        H.append("</table>")
    H.append(f"<p><b>Aménagement</b> {V21} : 2 baies 42U, onduleurs en double alimentation A/B avec packs batterie, 2 climatiseurs techniques "
             f"{clim_kw} kW (N+1) et allée froide, plancher technique surélevé de 30 cm, batardeau, détection de fuite, extinction automatique "
             "au gaz inerte (IG-541), tableau informatique TD-INFO et inverseur de source vers le groupe électrogène (point 14, "
             f"<code>energie_refroidissement.pdf</code>) ; contrôle d'accès par badge ({e(bad_srv.get('repere', 'B'))}), caméra "
             f"({e(cam_srv.get('repere', 'C'))}), cloison coupe-feu.</p>")

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
             "Chaque local a sa voie A par la colonne la plus proche et sa voie B par l'autre : une colonne coupée n'isole aucun local. "
             f"Au sous-sol, la voie B évite les circulations et les traversées de mur de la voie A {V21} : "
             + ("aucune circulation n'est commune aux deux voies.</p>" if not roc_communs else
                "seul reste commun : " + "; ".join(f"{k} ({', '.join(v)})" for k, v in roc_communs.items()) + ".</p>")
             + "<table><tr><th>Local</th><th>Voie</th><th>Chemin de la fibre (depuis la salle serveur)</th><th class='n'>Longueur</th></tr>")
    for r in rocades:
        nv = f" {V21}" if r["voie"] == "B" and r["local"].startswith("N-1") else ""
        H.append(f"<tr><td class='{classe_lt(r['local'])}'>{r['local']}</td><td>{r['voie']}{nv}</td><td class='chemin'>{e(r.get('chemin', r['par']))}</td>"
                 f"<td class='n'>{r['longueur']:.0f} m</td></tr>")
    H.append("</table><table><tr><th>Opérateur</th><th>Entrée dans le bâtiment</th><th>Chemin jusqu'à la salle serveur</th><th class='n'>Longueur</th></tr>")
    for a in adductions:
        nv = f" {V21}" if a.get("points_communs") is not None and a["operateur"] != "FAI 1" else ""
        H.append(f"<tr><td><b>{a['operateur']}</b>{nv}</td><td>{e(a['entree'])}</td><td class='chemin'>{e(a.get('chemin', ''))}</td>"
                 f"<td class='n'>{a['longueur_interne']:.0f} m</td></tr>")
    H.append("</table>")
    if add_commun:
        ecart = adductions[-1].get("ecart_min_m")
        H.append(f"<p class='note alerte'><b>Point commun des deux arrivées</b> {V21} : le tracé de FAI 2 évite les circulations de FAI 1, sauf le "
                 f"<b>{e(', '.join(add_commun))}</b>, seul passage du côté est vers la salle serveur"
                 + (" (les deux tracés s'y croisent)" if ecart == 0 else f" (écart minimal entre les tracés : {CH.nombre(ecart, 1)} m)" if ecart else "")
                 + ". Les deux fourreaux y sont posés sur des supports distincts, au plafond du parking ; supprimer ce point commun demanderait "
                 "une autre entrée pour FAI 2, à étudier avec l'opérateur.</p>")
    H.append("<img src='synoptique.png' alt='Synoptique des fibres'>")

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
             f"Caméras et badgeuses sur des réseaux séparés (VLAN vidéo et contrôle d'accès). {V21} : {t['camera']} caméras ; celle du foyer "
             "des étudiants (ancienne prise N0-LT01-P050) est retirée, la CNIL excluant la vidéo dans un lieu de pause (AIPD, point 19). "
             "Les images sont enregistrées par VS-NVR1, dans la baie 2 de la salle serveur (30 jours au plus).</p>"
             "<table><tr><th>Repère</th><th>Niveau</th><th>Salle</th><th>Détail</th><th>Local</th><th class='n'>Câble</th></tr>")
    ordre = {"wifi": 0, "camera": 1, "badge": 2}
    for p in sorted((p for p in prises if p["type"] != "usager"), key=lambda p: (ordre[p["type"]], p["niveau"], p.get("repere", ""))):
        det = p["usage"].split(",")[0] if p["type"] != "wifi" else p["usage"].replace("borne ", "").replace(", au plafond", "")
        H.append(f"<tr><td><b>{e(p.get('repere', ''))}</b></td><td>{NOMS[p['niveau']]}</td><td>{e(p['salle'])}</td><td>{e(det)}</td>"
                 f"<td class='{classe_lt(p['local'])}'>{p['local']}</td><td class='n'>{p['longueur']:.0f} m</td></tr>")
    H.append("</table>")
    H.append("<h2>9. Repérage et règles de pose</h2><ul>"
             "<li>Chaque prise porte un repère <b>&lt;local&gt;-P&lt;numéro&gt;</b> (ex. N0-LT02-P017), identique sur la prise et au panneau de brassage (TIA-606). La liste complète est dans <code>prises.csv</code>.</li>"
             f"<li>Équipements raccordés {V21} : borne <b>AP-&lt;niveau&gt;-&lt;nn&gt;</b> (identifiant de l'étude Wi-Fi, ex. AP-N0-03), caméra "
             "<b>&lt;niveau&gt;-C&lt;n&gt;</b>, badgeuse <b>&lt;niveau&gt;-B&lt;n&gt;</b> : un repère unique dans tout le bâtiment.</li>"
             "<li>Câble Cat6A U/FTP, Euroclasse Cca-s1b,d1,a1 ; lien permanent ≤ 90 m (ISO/IEC 11801-1, EN 50173-1).</li>"
             "<li>Chemins de câbles en faux plafond des couloirs, séparés des courants forts (EN 50174-2) ; traversées de murs rebouchées coupe-feu.</li>"
             "<li>Longueurs estimées : 1,10 × cheminement sur plan + 3 m de descentes + 2 m de réserve ; échelle des plans ±2 %.</li>"
             "</ul><p class='note'>À valider avec le client : emplacement des chambres de tirage des opérateurs, passage en vide sanitaire et au plafond du parking, "
             "salle serveur dans J05, mesure Wi-Fi sur site.</p>")
    H.append(CH.bloc_suivi(REF, changements="Charte commune ; caméra du foyer retirée ; VS-NVR1 ; voies B du sous-sol et FAI 2 distinctes ; "
                                            "câbles hors de la gaine d'ascenseur ; contrôleurs Wi-Fi listés ; aménagement de la salle du point 14 ; "
                                            "repères uniques."))
    html_page = CH.page(titre="Implantation de l'infrastructure réseau", titre_court="Implantation", ref=REF, points="04", dossier=OUT,
                        chapo="Où se trouve chaque élément, quelle salle est desservie par quel local technique, et par où passent les câbles "
                              "et les fibres. Plans à l'échelle dans <code>plans/</code>, repères dans <code>prises.csv</code>.",
                        corps="\n".join(H), css_extra=CSS_IMPLANTATION)
    CH.ecrire_et_imprimer(html_page, OUT / "implantation.html", OUT / "implantation.pdf")
