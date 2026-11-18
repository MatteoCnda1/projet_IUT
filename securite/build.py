#!/usr/bin/env python3
"""Point 09 · Sécurité des réseaux : produit livrables/securite/.

Usage : python3 securite/build.py   (après architecture/reseau/build.py)
Entrées : securite/flux.py (matrice), securite/ebios.py (analyse de risque), securite/pssi.py (politique)
Sorties : livrables/securite/matrice_flux.pdf, analyse_risque.pdf, pssi.pdf (+ .html), matrice_flux.csv, README.md
"""
import csv
import datetime
import html
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ICI = Path(__file__).resolve().parent
ROOT = ICI.parent
sys.path.insert(0, str(ICI))
import flux as F  # noqa: E402
import ebios as EB  # noqa: E402
import pssi as PP  # noqa: E402

OUT = ROOT / "livrables" / "securite"
e = html.escape
DATE = datetime.date.today().strftime("%d/%m/%Y")
CSS = (ROOT / "cablage" / "document.py").read_text(encoding="utf-8").split('CSS = """', 1)[1].split('"""', 1)[0] + """
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 7.4pt; }
td.m { font-family: 'DejaVu Sans Mono', monospace; font-size: 7pt; }
.z { display: inline-block; padding: 0 1.3mm; border-radius: 1mm; color: #fff; font-size: 7pt; font-weight: bold; white-space: nowrap; }
.ok { color: #05893e; font-weight: bold; } .ko { color: #c13c3b; font-weight: bold; }
.st { display: inline-block; padding: 0 1.2mm; border-radius: 1mm; font-size: 6.8pt; font-weight: bold; white-space: nowrap; }
.st-ecart { background: #FBE9E7; color: #B3261E; } .st-conf { background: #FBF4EA; color: #8C4A06; }
table.grille td, table.grille th { text-align: center; font-size: 7pt; padding: 1mm; }
table.grille td.vide { background: #F6F4EF; color: #B9B4AA; }
table.grille td.diag { background: #EEF0F3; }
table.regles { font-size: 7.3pt; } table.regles td { padding: 1mm 1.4mm; }
.pourquoi { color: #3A3833; } .ref { color: #6C6861; font-size: 6.8pt; }
@page paysage { size: A4 landscape; margin: 10mm 11mm 12mm; }
.paysage { page: paysage; page-break-before: always; page-break-after: always; }
h2, h3 { page-break-after: avoid; }
.fiche { border: 1px solid #DEDAD1; border-radius: 2mm; padding: 2.5mm 3.5mm; margin: 3mm 0; page-break-inside: avoid; }
.fiche h3 { margin: 0 0 1.5mm; }
"""


def pdf(page, sortie):
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:
        print("  (pas de Chrome : PDF non produit)")
        return
    with tempfile.TemporaryDirectory() as prof:
        subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", f"--user-data-dir={prof}", "--no-pdf-header-footer",
                        f"--print-to-pdf={sortie}", page.as_uri()], check=True, capture_output=True, timeout=180)


def tableau(entetes, lignes, cls="", mono=()):
    H = [f"<table class='{cls}'><tr>" + "".join(f"<th>{x}</th>" for x in entetes) + "</tr>"]
    for l in lignes:
        H.append("<tr>" + "".join(f"<td class='m'>{x}</td>" if i in mono else f"<td>{x}</td>" for i, x in enumerate(l)) + "</tr>")
    return "".join(H) + "</table>"


def z(code):
    if code is None:
        return "<span class='z' style='background:#3A3833'>tout</span>"
    return f"<span class='z' style='background:{F.ZONES[code][2]}'>{code}</span>"


def objets(liste):
    return "<br>".join(e(o) if o == "tout" else f"{z(F.zone(o))} {e(o)}" for o in liste)


def statut(st):
    if not st:
        return ""
    c = "st-ecart" if st.startswith("écart") else "st-conf"
    return f" <span class='st {c}'>{e(st)}</span>"


def action(a):
    return "<span class='ok'>autoriser</span>" if a == "autoriser" else "<span class='ko'>refuser</span>"


def appliquee(r):
    eqs = {F.filtre(F.zone(s) if s != "tout" else None, F.zone(d) if d != "tout" else None) for s in r["src"] for d in r["dst"]}
    return "<br>".join(sorted(eqs))


def services(svc):
    """tcp/88 tcp/389 udp/88 -> « tcp 88, 389 » / « udp 88 » : une ligne par protocole."""
    par = {}
    for x in svc:
        p, _, port = x.partition("/")
        par.setdefault(p, []).append(port)
    return "<br>".join(e(p if not ports[0] else f"{p} {', '.join(ports)}") for p, ports in par.items())


def grille():
    """Tableau zone source × zone destination : identifiants des règles d'autorisation (en rouge : refus explicites)."""
    ordre = list(F.ZONES)
    cel = {(a, b): [] for a in ordre for b in ordre}
    for r in F.R:
        for s in r["src"]:
            for d in r["dst"]:
                if "tout" in (s, d):
                    continue
                k = (F.zone(s), F.zone(d))
                lab = r["id"] if r["action"] == "autoriser" else f"<span class='ko'>{r['id']}</span>"
                if lab not in cel[k]:
                    cel[k].append(lab)
    H = ["<table class='grille'><tr><th>source ↓ / destination →</th>" + "".join(f"<th>{z(b)}</th>" for b in ordre) + "</tr>"]
    for a in ordre:
        H.append(f"<tr><th>{z(a)}</th>")
        for b in ordre:
            v = cel[(a, b)]
            cls = "diag" if a == b else ("" if v else "vide")
            H.append(f"<td class='{cls}'>{' '.join(v) if v else '·'}</td>")
        H.append("</tr>")
    return "".join(H) + "</table>"


def doc_matrice():
    n_ok = sum(r["action"] == "autoriser" for r in F.R)
    tests = [(r["id"], p, c, svc, r["action"]) for r in F.R for p, c, svc in r["tests"]]
    H = [f"<!doctype html><html lang='fr'><head><meta charset='utf-8'><title>Matrice des flux</title><style>{CSS}</style></head><body>",
         "<h1>Matrice des flux entre zones</h1>",
         f"<p class='sous'>Site de Marseille · IUT Génie Télécom, Luminy · RudyLink Infrastructure · point 09 du cahier des charges · "
         f"matrice v{F.VERSION} sur l'infrastructure v2 · {DATE}<br>Qui parle à qui, sur quels ports, par quel pare-feu, avec quelle "
         "inspection, et pourquoi. Source unique : <code>securite/flux.py</code> ; tableur : <code>matrice_flux.csv</code>.</p>",
         "<div class='cles'>",
         f"<div class='cle'><b>{len(F.R)}</b>règles ({n_ok} autorisations)</div>",
         f"<div class='cle'><b>{len(F.ZONES)}</b>zones de confiance</div>",
         f"<div class='cle'><b>{len(F.OBJETS)}</b>objets d'adresses</div>",
         f"<div class='cle'><b>{len(tests)}</b>tests de recette proposés</div></div>",
         "<h2>1. Principes</h2><ul>",
         "<li><b>Refus par défaut</b> (F99) : tout ce qui n'est pas écrit ici est refusé et journalisé. Chaque autorisation a un propriétaire, "
         "une justification et une référence (note technique ANSSI sur la politique de filtrage : liste blanche, règles commentées, revue).</li>",
         "<li><b>Une zone = un niveau de confiance.</b> Les zones internes sont des VRF du cœur (ou des VLAN dont la passerelle est sur le "
         "Stormshield, comme le tier 0) : entre deux zones, il n'existe <b>aucune route</b> qui ne traverse un pare-feu.</li>",
         "<li><b>Le pare-feu se déduit du chemin</b> : Internet et la DMZ passent par le FortiGate, tout changement de zone interne par le "
         "Stormshield, et ce qui va de la DMZ vers l'intérieur traverse les deux (deux marques en cascade, guide ANSSI PA-044). À l'intérieur "
         "d'une même zone, ce sont des ACL sur les passerelles (distribution ou cœur).</li>",
         "<li><b>Ordre d'évaluation</b> : sessions établies, puis autorisations, puis refus explicites, puis refus par défaut. Les refus "
         "explicites ne changent rien au résultat : ils servent à compter et à lever une alerte sur les tentatives qui comptent "
         "(une caméra qui cherche à joindre un poste, un poste d'administration qui veut sortir sur Internet).</li>",
         "<li><b>IPv4 et IPv6</b> : chaque règle vaut pour les deux familles (mêmes terminaisons d'adresse, voir le plan d'adressage).</li>",
         "<li><b>Statuts</b> : " + statut("à confirmer (Pxx)") + " = dépend d'un choix d'un autre point du cahier des charges ; "
         + statut("écart Ex") + " = règle de l'architecture v2 que l'analyse de sécurité propose de faire évoluer (section 5).</li></ul>",
         "<h2>2. Zones</h2>",
         tableau(["Zone", "Contenu", "Confiance"], [[z(k), e(v[0]), e(v[1])] for k, v in F.ZONES.items()]),
         "<h2 class='saut'>3. Vue d'ensemble : quelles zones se parlent</h2>",
         "<p>Chaque case donne les règles qui concernent ce couple de zones (en rouge : refus explicites). Une case grise vide = aucun flux, "
         "refus par défaut. La diagonale correspond aux flux internes à une zone (ACL).</p>",
         grille(),
         "<h2>4. Objets d'adresses</h2>",
         tableau(["Objet", "Zone", "Contenu", "IPv4"],
                 [[f"<b>{e(k)}</b>", z(v[0]), e(v[1]), ", ".join(a for a, _ in F.adresses(k)[:3]) + (f" … ({len(F.adresses(k))})" if len(F.adresses(k)) > 3 else "")]
                  for k, v in F.OBJETS.items()], mono=(3,)),
         "<div class='paysage'><h2>5. Règles</h2>"]
    section = None
    lignes = []
    for r in F.R:
        if r["section"] != section:
            if lignes:
                H.append(tableau(["Id", "Source", "Destination", "Services", "Action", "Appliquée par", "Inspection", "Journal", "Pourquoi"],
                                 lignes, cls="regles"))
            section, lignes = r["section"], []
            H.append(f"<h3>{e(section)}</h3>")
        lignes.append([f"<b>{r['id']}</b>{statut(r['statut'])}", objets(r["src"]), objets(r["dst"]),
                       "<code>" + services(r["svc"]) + "</code>", action(r["action"]), appliquee(r),
                       e(r["profil"]), e(r["journal"]),
                       f"<span class='pourquoi'>{e(r['pourquoi'])}</span>" + (f"<br><span class='ref'>{e(r['ref'])}</span>" if r["ref"] else "")])
    H.append(tableau(["Id", "Source", "Destination", "Services", "Action", "Appliquée par", "Inspection", "Journal", "Pourquoi"], lignes, cls="regles"))
    H.append("</div>")
    H.append("<h2 class='saut'>6. Écarts avec l'architecture v2 (propositions pour la v3)</h2>"
             "<p>En détaillant chaque flux jusqu'au port, quatre règles de l'architecture v2 apparaissent comme à améliorer, et la zone de l'IA "
             "locale (note du point 11) doit trouver sa place. Rien n'est changé dans les livrables v2 : ces propositions seront traitées "
             "comme une revue, avec une v3 (archivage de la v2, puis corrections).</p>")
    for k, (titre, constat, proposition, points) in F.ECARTS.items():
        regles = ", ".join(r["id"] for r in F.R if r["statut"] == f"écart {k}")
        H.append(f"<div class='fiche'><h3>{k} · {e(titre)}</h3><p><b>Constat.</b> {e(constat)}</p><p><b>Proposition.</b> {e(proposition)}</p>"
                 f"<p class='sous'>Points concernés : {e(points)}{' · règles ' + regles if regles else ''}</p></div>")
    H.append("<h3>Zone de l'IA locale (E5) : adresses proposées</h3>")
    H.append(tableau(["VLAN", "Nom", "IPv4", "IPv6", "Usage"],
                     [[str(vid), e(p["nom"]), p["v4"], p["v6"], e(p["usage"])] for vid, p in F.PROPOSITIONS.items()], mono=(2, 3)))
    H.append("<h2>7. Tests de recette proposés</h2>"
             "<p>La configuration des pare-feu (Stormshield, FortiGate, et le pare-feu de la maquette) revient à l'équipe d'intégration. Pour "
             "la recette, chaque règle importante est accompagnée de cas de test : un flux qui doit passer, ou un flux qui doit être refusé. "
             "Pour qu'un refus prouve quelque chose, un service doit écouter sur la cible : l'échec ne peut alors venir que du pare-feu. "
             "Les postes cités sont ceux de la maquette du point 06. Dans la maquette, l'AD est encore en VLAN 300 (10.13.48.11), "
             "comme le note le TP.</p>")
    H.append(tableau(["Règle", "Depuis", "Vers", "Service", "Attendu"],
                     [[f"<b>{rid}</b>", f"<code>{e(p)}</code> ({F.MAQUETTE_POSTES[p]})", f"{e(c)} ({F.CIBLES_MAQUETTE[c]})", f"<code>{e(svc)}</code>",
                       "<span class='ok'>passe</span>" if a == "autoriser" else "<span class='ko'>refusé</span>"] for rid, p, c, svc, a in tests]))
    H.append("<h2>8. Exploitation de la matrice</h2><ul>"
             "<li><b>Revue</b> semestrielle par le RSSI et l'administrateur réseau : chaque règle est justifiée ou supprimée ; les compteurs à zéro "
             "depuis six mois sont des candidates à la suppression.</li>"
             "<li><b>Changement</b> : toute demande d'ouverture passe par une demande écrite (besoin, source, destination, port, durée), "
             "l'avis du RSSI, puis une modification de <code>flux.py</code>, relue par un second administrateur (revue de code).</li>"
             "<li><b>Traçabilité</b> : l'identifiant Fxx est repris dans le nom de la règle sur le Stormshield et le FortiGate ; les journaux "
             "le mentionnent, ce qui relie une alerte à sa justification.</li></ul></body></html>")
    return "\n".join(H)


def entete(titre, sous):
    return [f"<!doctype html><html lang='fr'><head><meta charset='utf-8'><title>{e(titre)}</title><style>{CSS}{CSS_RISQUE}</style></head><body>",
            f"<h1>{e(titre)}</h1>",
            f"<p class='sous'>Site de Marseille · IUT Génie Télécom, Luminy · RudyLink Infrastructure · point 09 du cahier des charges · "
            f"version 1 sur l'infrastructure v2 · {DATE}<br>{sous}</p>"]


CSS_RISQUE = """
table.carte { width: auto; margin: 3mm auto; page-break-inside: avoid; }
.bloc { page-break-inside: avoid; }
td:first-child b { white-space: nowrap; } table.carte td, table.carte th { width: 30mm; height: 15mm; text-align: center; vertical-align: middle; font-size: 8pt; border: 1px solid #fff; }
.r1 { background: #DCEFE3; } .r2 { background: #FBF0C9; } .r3 { background: #F7D2B5; } .r4 { background: #F2B8B0; }
.ini { font-weight: bold; color: #3A3833; } .res { font-weight: bold; color: #05893e; }
.etat { display: inline-block; padding: 0 1.2mm; border-radius: 1mm; font-size: 6.8pt; font-weight: bold; white-space: nowrap; }
.e-place { background: #DCEFE3; color: #1D5E3A; } .e-prop { background: #E5EDF8; color: #1F4E8C; } .e-org { background: #F1EEE8; color: #5C574F; }
.n-couverte { color: #05893e; font-weight: bold; } .n-partielle { color: #A85A07; font-weight: bold; } .n-client { color: #6C6861; font-weight: bold; }
ol.chemin { margin: 0; padding-left: 4mm; } ol.chemin li { margin: 0; }
"""


def niveau_risque(g, v):
    p = g * v
    return 4 if p >= 12 else 3 if p >= 8 else 2 if p >= 4 else 1


def carte(points):
    """Carte des risques gravité × vraisemblance. points : {(g, v): [libellés]}."""
    H = ["<table class='carte'><tr><th></th>" + "".join(f"<th>V{v}<br><span class='sous'>{e(EB.VRAISEMBLANCE[v][0])}</span></th>" for v in range(1, 5)) + "</tr>"]
    for g in range(4, 0, -1):
        H.append(f"<tr><th>G{g}<br><span class='sous'>{e(EB.GRAVITE[g][0])}</span></th>")
        for v in range(1, 5):
            H.append(f"<td class='r{niveau_risque(g, v)}'>{' '.join(points.get((g, v), []))}</td>")
        H.append("</tr>")
    return "".join(H) + "</table>"


def doc_ebios():
    PP.verifier()
    EB.verifier(PP.CODES)
    mes = {m[0]: m for m in PP.MESURES}
    H = entete("Analyse de risque EBIOS RM", "Méthode EBIOS Risk Manager (ANSSI, v1.5), version allégée : ateliers 1 à 3 détaillés, "
               "vraisemblance des scénarios estimée directement, puis plan de traitement relié à la PSSI et à la matrice de flux.")
    H += ["<div class='cles'>", f"<div class='cle'><b>{len(EB.VALEURS)}</b>valeurs métier</div>",
          f"<div class='cle'><b>{len(EB.EVENEMENTS)}</b>événements redoutés</div>",
          f"<div class='cle'><b>{sum(s[5] for s in EB.SOURCES)}</b>sources de risque retenues</div>",
          f"<div class='cle'><b>{len(EB.SCENARIOS)}</b>scénarios stratégiques</div></div>",
          "<h2>1. Atelier 1 : cadrage et socle de sécurité</h2>",
          f"<p><b>Mission.</b> {e(EB.MISSION)}</p><p><b>Périmètre.</b> Le SI du bâtiment conçu dans ce projet (réseau, datacenter, DMZ, "
          "administration, sûreté) et son lien avec le site jumeau. Hors périmètre : les applications nationales de l'AMU (scolarité, RH), "
          "qui ont leur propre homologation.</p><h3>Valeurs métier et biens supports</h3>",
          tableau(["", "Valeur métier", "Responsable", "Biens supports"], [[f"<b>{c}</b>", e(v), e(r), e(b)] for c, v, r, b in EB.VALEURS]),
          "<h3>Échelle de gravité</h3>",
          tableau(["", "Niveau", "Signification"], [[f"G{k}", e(v[0]), e(v[1])] for k, v in EB.GRAVITE.items()]),
          "<h3>Événements redoutés</h3>",
          tableau(["", "Valeur", "Événement redouté", "Impacts", "Gravité"],
                  [[f"<b>{c}</b>", v, e(t), e(i), f"<b>G{g}</b> {e(EB.GRAVITE[g][0])}"] for c, v, t, i, g in EB.EVENEMENTS]),
          "<h3>Socle de sécurité</h3>",
          tableau(["Référentiel", "Statut", "État dans le projet"], [[e(a), e(b), e(c)] for a, b, c in EB.SOCLE]),
          "<h2 class='saut'>2. Atelier 2 : sources de risque et objectifs visés</h2>",
          "<p>Motivation et ressources notées de 1 à 3. Un couple est retenu si sa pertinence (motivation × ressources) atteint 4, "
          "ou s'il est fréquent dans le secteur (SR5).</p>",
          tableau(["", "Source de risque", "Objectif visé", "Motivation", "Ressources", "Pertinence", "Retenu", "Commentaire"],
                  [[f"<b>{c}</b>", e(s), e(o), str(m), str(r), f"<b>{m * r}</b>", "oui" if ok else "non", e(com)]
                   for c, s, o, m, r, ok, com in EB.SOURCES]),
          "<h2>3. Atelier 3 : écosystème et scénarios stratégiques</h2><h3>Parties prenantes</h3>",
          "<p>Notées de 1 à 4. Niveau de menace = (dépendance × pénétration) / (maturité cyber × confiance). Au-dessus de "
          f"{EB.SEUIL_MENACE}, la partie prenante est critique et reçoit des mesures propres.</p>",
          tableau(["", "Partie prenante", "Dépendance", "Pénétration", "Maturité", "Confiance", "Menace"],
                  [[f"<b>{p[0]}</b>", e(p[1]), *map(str, p[2:]),
                    f"<b class='{'ko' if EB.menace(p) > EB.SEUIL_MENACE else ''}'>{EB.menace(p)}</b>"] for p in EB.PARTIES]),
          "<p>Parties critiques : " + ", ".join(f"{p[0]} ({e(p[1].split(' (')[0])})" for p in EB.PARTIES if EB.menace(p) > EB.SEUIL_MENACE) +
          ". Mesures propres : accès des prestataires par le bastion uniquement (M-ADM-2), clauses des CCTP (M-FOU-1), modèles d'IA vérifiés "
          "(M-IA-2), appareils personnels jamais admis dans les zones de confiance (M-RES-2, M-RES-4).</p>",
          "<h3>Échelle de vraisemblance</h3>",
          tableau(["", "Niveau", "Signification"], [[f"V{k}", e(v[0]), e(v[1])] for k, v in EB.VRAISEMBLANCE.items()]),
          "<h3>Scénarios stratégiques</h3>",
          tableau(["", "Source", "Événements", "Chemin d'attaque", "Gravité", "Vraisemblance"],
                  [[f"<b>{c}</b>", sr, ", ".join(ers), "<ol class='chemin'>" + "".join(f"<li>{e(x)}</li>" for x in et) + "</ol>",
                    f"G{g}", f"V{v}"] for c, sr, ers, et, g, v in EB.SCENARIOS]),
          "<h2 class='saut'>4. Plan de traitement</h2>",
          "<p>Pour chaque scénario : les mesures de la PSSI et les règles de la matrice de flux qui cassent le chemin d'attaque, la "
          "vraisemblance qui reste une fois ces mesures appliquées, et qui accepte le risque résiduel.</p>"]
    lignes = []
    for c, sr, ers, et, g, v in EB.SCENARIOS:
        m, regles, vr, qui = EB.TRAITEMENT[c]
        lignes.append([f"<b>{c}</b>", "<br>".join(f"<b>{x}</b> {e(mes[x][2])}" for x in m), ", ".join(regles),
                       f"G{g} V{v} → <b>G{g} V{vr}</b>", e(qui)])
    H.append(tableau(["", "Mesures (PSSI)", "Règles de flux", "Risque initial → résiduel", "Accepté par"], lignes))
    ini, res = {}, {}
    for c, sr, ers, et, g, v in EB.SCENARIOS:
        ini.setdefault((g, v), []).append(f"<span class='ini'>{c}</span>")
        res.setdefault((g, EB.TRAITEMENT[c][2]), []).append(f"<span class='res'>{c}</span>")
    resid = sorted(((g * EB.TRAITEMENT[c][2], c, g, EB.TRAITEMENT[c][2]) for c, _, _, _, g, _ in EB.SCENARIOS), reverse=True)
    rouges = [c for _, c, g, v in resid if niveau_risque(g, v) >= 3]
    jaunes = [f"{c} (G{g} V{v})" for _, c, g, v in resid if niveau_risque(g, v) == 2]
    H += ["<div class='bloc'><h3>Carte des risques avant traitement</h3>", carte(ini), "</div>",
          "<div class='bloc'><h3>Carte des risques après traitement</h3>", carte(res), "</div>",
          f"<p>{'Aucun risque ne reste en orange ou en rouge.' if not rouges else 'Risques encore élevés : ' + ', '.join(rouges) + '.'} "
          f"Restent en zone jaune, sous surveillance : {', '.join(jaunes)}. SS1 et SS4 gardent une gravité critique : les mesures "
          "réduisent leur vraisemblance, pas leurs conséquences, d'où l'importance des sauvegardes hors ligne et du plan de crise (point 19). "
          "SS6 (détournement de l'IA) porte sur une technologie récente dont les attaques évoluent vite, et SS5 dépend aussi des "
          "opérateurs (déni de service). Ces quatre scénarios justifient la revue annuelle de l'analyse.</p>",
          "<h2>5. Limites de l'analyse</h2><ul>"
          "<li>Analyse faite par le concepteur, sans atelier avec les métiers de l'IUT : les valeurs métier et la gravité sont à valider par "
          "la direction et les laboratoires avant l'homologation.</li>"
          "<li>L'atelier 4 (scénarios opérationnels) n'est pas détaillé : la vraisemblance repose sur l'architecture v2 et sur la menace "
          "décrite par le CERT-FR. Un test d'intrusion (M-GOU-3) la confirmera.</li>"
          "<li>Les services de l'AMU (applications nationales, messagerie fédérée) sont hors périmètre et relèvent de leur propre analyse.</li></ul>",
          "</body></html>"]
    return "\n".join(H)


def doc_pssi():
    PP.verifier()
    H = entete("Politique de sécurité du SI", "PSSI du bâtiment IUT Génie Télécom : déclinaison locale de la PSSI de l'AMU. Elle s'appuie sur "
               "l'analyse de risque (<code>analyse_risque.pdf</code>) et la matrice des flux (<code>matrice_flux.pdf</code>).")
    etats = {"en place": "e-place", "proposé": "e-prop", "organisationnel": "e-org"}
    nb = {k: sum(m[4] == k for m in PP.MESURES) for k in etats}
    H += ["<div class='cles'>", f"<div class='cle'><b>{len(PP.MESURES)}</b>mesures</div>",
          f"<div class='cle'><b>{nb['en place']}</b>déjà dans l'architecture v2</div>",
          f"<div class='cle'><b>{nb['proposé']}</b>proposées (v3)</div>",
          f"<div class='cle'><b>{nb['organisationnel']}</b>organisationnelles (client)</div></div>",
          "<h2>1. Objet et périmètre</h2>",
          "<p>Le cahier des charges demande de « mettre l'accent sur la sécurité en général : des biens, des personnes, des réseaux ». Cette "
          "politique fixe les règles qui s'appliquent au SI du bâtiment (réseau, datacenter, DMZ, administration, systèmes de sûreté, "
          "plateforme d'IA) et à ceux qui l'utilisent ou l'administrent. Elle s'applique aussi au site jumeau de Digne pour ce qui est "
          "partagé (annuaire, liaison).</p>",
          "<p><b>Cadre.</b> PSSI de l'AMU ; RGPD ; conservation des données de connexion (CPCE L34-1) ; directive NIS 2, que la loi "
          "Résilience doit transposer : on retient l'hypothèse que l'établissement sera une entité concernée, et l'on anticipe ses "
          "obligations (gouvernance, gestion des risques, notification des incidents). Recommandations de l'ANSSI listées dans "
          "<code>docs/anssi/referentiel_anssi.md</code>.</p>",
          "<h2>2. Organisation</h2>",
          tableau(["Rôle", "Qui", "Responsabilités"], [[f"<b>{e(a)}</b>", e(b), e(c)] for a, b, c in PP.ROLES]),
          "<div class='bloc'><h2>3. Principes</h2>",
          tableau(["Principe", "Traduction dans l'architecture"], [[f"<b>{e(a)}</b>", e(b)] for a, b in PP.PRINCIPES]), "</div>",
          "<h2 class='saut'>4. Mesures</h2>",
          "<p>État : <span class='etat e-place'>en place</span> = déjà dans l'architecture v2 ; <span class='etat e-prop'>proposé</span> = "
          "ajouté par ce dossier, à intégrer en v3 ; <span class='etat e-org'>organisationnel</span> = relève de l'exploitation par le client.</p>"]
    dom = None
    lignes = []
    for code, d, titre, exig, etat, ref in PP.MESURES:
        if d != dom:
            if lignes:
                H.append(tableau(["", "Mesure", "Exigence", "État", "Références"], lignes))
            dom, lignes = d, []
            H.append(f"<h3>{e(d)}</h3>")
        lignes.append([f"<b>{code}</b>", f"<b>{e(titre)}</b>", e(exig), f"<span class='etat {etats[etat]}'>{etat}</span>", f"<span class='ref'>{e(ref)}</span>"])
    H.append(tableau(["", "Mesure", "Exigence", "État", "Références"], lignes))
    H.append("<h2 class='saut'>5. Conformité au guide d'hygiène informatique (42 mesures)</h2>"
             "<p>Intitulés du guide de l'ANSSI (v2, 2017, outil de suivi). « À la charge du client » : la conception peut le prévoir, mais "
             "seule l'exploitation peut le faire vivre (formation, procédures RH, gestion du parc).</p>")
    cls = {"couverte": "n-couverte", "partielle": "n-partielle", "à la charge du client": "n-client"}
    total = {k: 0 for k in cls}
    for chap, titre, liste in PP.HYGIENE:
        H.append(f"<h3>{chap}. {e(titre)}</h3>")
        H.append(tableau(["N°", "Mesure du guide", "Couverte par", "Niveau"],
                         [[str(n), e(t), ", ".join(m), f"<span class='{cls[niv]}'>{niv}</span>"] for n, t, m, niv in liste]))
        for *_, niv in liste:
            total[niv] += 1
    H.append(f"<p><b>Bilan</b> : {total['couverte']} mesures couvertes, {total['partielle']} partielles, {total['à la charge du client']} "
             "à la charge du client. Les mesures partielles deviennent couvertes avec les propositions v3 (messagerie en relais E1, "
             "inventaire des comptes privilégiés, revue des produits qualifiés).</p>")
    H.append("<h2>6. Application, dérogations, revue</h2><ul>"
             "<li>Une dérogation à cette politique est demandée par écrit au RSSI, limitée dans le temps, et accompagnée d'une mesure compensatoire.</li>"
             "<li>La politique est revue chaque année et après tout incident majeur ou changement d'architecture (nouvelle version de l'infrastructure).</li>"
             "<li>Le non-respect par un utilisateur relève de la charte informatique et du règlement intérieur (point 19).</li></ul></body></html>")
    return "\n".join(H)


def ecrire_csv(chemin):
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "section", "source", "zone_source", "destination", "zone_destination", "services", "action",
                    "appliquee_par", "inspection", "journal", "statut", "justification", "reference"])
        for r in F.R:
            for s in r["src"]:
                for d in r["dst"]:
                    zs = F.zone(s) if s != "tout" else None
                    zd = F.zone(d) if d != "tout" else None
                    w.writerow([r["id"], r["section"], s, zs or "tout", d, zd or "tout", " ".join(r["svc"]), r["action"],
                                F.filtre(zs, zd), r["profil"], r["journal"], r["statut"], r["pourquoi"], r["ref"]])


def main():
    F.verifier()
    print("Matrice de flux : contrôles OK")
    OUT.mkdir(parents=True, exist_ok=True)
    ecrire_csv(OUT / "matrice_flux.csv")
    docs = [("matrice_flux", doc_matrice), ("analyse_risque", doc_ebios), ("pssi", doc_pssi)]
    for nom, fonction in docs:
        page = OUT / f"{nom}.html"
        page.write_text(fonction(), encoding="utf-8")
        pdf(page, OUT / f"{nom}.pdf")
        print(f"  {page.relative_to(ROOT)} -> .pdf")
    (OUT / "README.md").write_text(
        "# Sécurité des réseaux (point 09)\n<!-- onglet: Sécurité -->\n\n"
        "| Document | Contenu |\n|---|---|\n"
        "| **[matrice_flux.pdf](matrice_flux.pdf)** | Matrice des flux entre zones : règles détaillées, pare-feu, inspection, justification, "
        "écarts avec la v2, tests de recette proposés. Tableur : `matrice_flux.csv` |\n"
        "| **[analyse_risque.pdf](analyse_risque.pdf)** | Analyse EBIOS RM allégée : valeurs métier, événements redoutés, sources de risque, "
        "écosystème, scénarios stratégiques, plan de traitement et cartes des risques |\n"
        "| **[pssi.pdf](pssi.pdf)** | Politique de sécurité du SI du site : organisation, principes, mesures (biens, personnes, réseaux, IA), "
        "conformité aux 42 mesures du guide d'hygiène |\n\n"
        "Régénérer : `python3 securite/build.py` (sources : `securite/flux.py`, `ebios.py`, `pssi.py`)..\n",
        encoding="utf-8")


if __name__ == "__main__":
    main()
