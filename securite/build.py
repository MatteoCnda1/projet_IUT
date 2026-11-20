#!/usr/bin/env python3
"""Point 09 · Sécurité des réseaux : produit livrables/securite/.

Usage : python3 securite/build.py   (après architecture/reseau/build.py)
Entrées : securite/flux.py (matrice), securite/ebios.py (analyse de risque), securite/pssi.py (politique)
Sorties (noms et dossier des dépôts GesTT du point 09, PR #12) : livrables/securite/RLI-P09-matrice-flux.pdf et .csv,
  RLI-P09-analyse-risque-ebios.pdf, RLI-P09-pssi.pdf, RLI-P09-sources.zip, README.md ; pages HTML intermédiaires dans securite/build/
Mise en page : charte commune (commun/charte.py) ; références RLI-ETU-006 (matrice), RLI-ETU-007 (analyse), RLI-ETU-008 (PSSI).
"""
import csv
import html
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
ROOT = ICI.parent
sys.path.insert(0, str(ICI))
sys.path.insert(1, str(ROOT))
import flux as F  # noqa: E402
import ebios as EB  # noqa: E402
import pssi as PP  # noqa: E402
from commun import charte as CH  # noqa: E402

OUT = ROOT / "livrables" / "securite"   # dossier du repo de la tâche P09 dans GesTT
BUILD = ICI / "build"                    # pages HTML intermédiaires (non suivies par git)
# Noms des fichiers déposés depuis GesTT (règle RLI-Pxx-<sujet>.<ext>)
NOMS = {"matrice_flux": "RLI-P09-matrice-flux", "analyse_risque": "RLI-P09-analyse-risque-ebios", "pssi": "RLI-P09-pssi"}
CSV_MATRICE = "RLI-P09-matrice-flux.csv"
SOURCES_ZIP = "RLI-P09-sources.zip"
e = html.escape
V21 = CH.badge("v2.1")
# Classes propres à ces documents (repris aussi par juridique/build.py) ; le reste vient de la charte. Les couleurs des zones
# servent de code et ne changent pas.
CSS = """
td.m { font-family: var(--mono); font-size: 7pt; }
.z { display: inline-block; padding: 0 1.3mm; color: #fff; font: 600 6.8pt var(--mono); white-space: nowrap; }
.st { display: inline-block; padding: 0 1.2mm; font: 600 6.4pt var(--mono); white-space: nowrap; border: 1px solid currentColor; }
.st-ecart { color: var(--rouge); } .st-conf { color: var(--alerte); }
table.grille td, table.grille th { text-align: center; font-size: 7pt; padding: 1mm; }
table.grille td.vide { background: var(--remplissage); color: var(--discret); }
table.grille td.diag { background: var(--trait-doux); }
table.regles { font-size: 7.1pt; } table.regles td { padding: .9mm 1.3mm; }
.pourquoi { color: var(--corps); } .ref { color: var(--discret); font-size: 6.8pt; }
@page paysage { size: A4 landscape; margin: 10mm 11mm 14mm; }
.paysage { page: paysage; break-before: page; break-after: page; }
h2, h3 { break-after: avoid; }
.fiche { border: 1px solid var(--trait); border-left: 3px solid var(--emeraude); padding: 2.5mm 3.5mm; margin: 3mm 0; break-inside: avoid; }
.fiche h3 { margin: 0 0 1.5mm; }
.obj { white-space: nowrap; }
.version { border: 1px solid var(--trait); border-left: 3px solid var(--emeraude); background: var(--surface); padding: 2mm 3mm; margin: 2mm 0 4mm; }
"""


def pdf(page, sortie):
    """Impression PDF par la charte commune (gardée sous ce nom pour juridique/build.py)."""
    CH.imprimer_pdf(page, sortie)


def encadre(changements):
    return (f"<div class='version'><b>Version {CH.VERSION[1:]} — {CH.DATE_VERSION}.</b> La version 2 est archivée dans "
            f"<code>{CH.ARCHIVE_PRECEDENTE}</code>. Changements de la v2.1 (repérés {V21}) :<ul>"
            + "".join(f"<li>{c}</li>" for c in changements) + "</ul></div>")


def tableau(entetes, lignes, cls="", mono=()):
    H = [f"<table class='{cls}'><thead><tr>" + "".join(f"<th>{x}</th>" for x in entetes) + "</tr></thead>"]
    for l in lignes:
        H.append("<tr>" + "".join(f"<td class='m'>{x}</td>" if i in mono else f"<td>{x}</td>" for i, x in enumerate(l)) + "</tr>")
    return "".join(H) + "</table>"


def z(code):
    if code is None:
        return "<span class='z' style='background:#3A3833'>tout</span>"
    return f"<span class='z' style='background:{F.ZONES[code][2]}'>{code}</span>"


def objets(liste):
    return "<br>".join(e(o) if o == "tout" else f"<span class='obj'>{z(F.zone(o))} {e(o)}</span>" for o in liste)


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


NOUVELLES_V21 = {f"F{k}" for k in range(56, 71)}
MODIFIEES_V21 = {"F04", "F05", "F09", "F14", "F16", "F23", "F24", "F27", "F29", "F35", "F36", "F38", "F39", "F40", "F41", "F42",
                 "F43", "F44", "F46"}


def contenu_objet(k):
    a4 = [a for a, _ in F.adresses(k)]
    txt = ", ".join(a4[:3]) + (f" … ({len(a4)})" if len(a4) > 3 else "")
    sauf = [x for x, _ in F.exclusions(k)]
    return txt + (" sauf " + ", ".join(sauf) if sauf else "")


def doc_matrice():
    n_ok = sum(r["action"] == "autoriser" for r in F.R)
    tests = [(r["id"], p, c, svc, r["action"]) for r in F.R for p, c, svc in r["tests"]]
    n_masques = len({m[0] for m in F.masques(sorted(F.R, key=lambda r: int(r["id"][1:])))})
    H = [encadre([
        "<b>Règles ajoutées</b> (F56 à F70) : résolution DNS des résolveurs internes vers Internet et de la DMZ par le FortiGate, relais "
        "DHCP des objets et de l'administration, CAPWAP des bornes, NUT (onduleurs, clients internes et de la DMZ), sources de temps NTP "
        "et NTS, sauvegarde et administration de DT-BKP1, administration des serveurs et des objets par le bastion, alertes par courriel, "
        "supervision du groupe électrogène en lecture seule (F70).",
        "<b>Ordre de déploiement</b> fixé (section 1) et objet INTERNET défini par négation des préfixes du site ; le pool du VPN "
        "d'administration remplace « NOMADES » comme source vers le bastion (F38).",
        "<b>Écarts E2, E3 et E4 intégrés</b> à l'architecture : VPN IPsec IKEv2, VS-NVR1 → caméras, DNS des postes par les résolveurs "
        "internes (section 6).",
        "<b>Journaux</b> : données de connexion 1 an, URL complètes 6 mois (F16, F29) ; DT-BKP1, les PAW, les boucles et les VM de la DMZ "
        "envoient leurs journaux et reçoivent l'heure ; eduroam en RADIUS sur UDP (NPS ne parle pas RadSec)."]),
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
         "<li><b>Le pare-feu se déduit du chemin</b> : Internet, la DMZ et le VPN d'administration passent par le FortiGate, tout changement "
         "de zone interne par le Stormshield, et ce qui va de la DMZ vers l'intérieur traverse les deux (deux marques en cascade, guide "
         "ANSSI PA-044). À l'intérieur d'une même zone, ce sont des ACL sur les passerelles (distribution ou cœur). La liaison avec le site jumeau "
         "passe par un tunnel IPsec du FortiGate, puis par le Stormshield.</li>",
         f"<li>{V21} <b>Ordre de déploiement</b> : les règles sont présentées par thème, mais déployées dans cet ordre : sessions établies, "
         "puis toutes les autorisations (dans l'ordre des numéros), puis les refus explicites, puis le refus par défaut. Les pare-feu "
         "appliquent la première règle qui correspond : déployées dans l'ordre des numéros, "
         f"{n_masques} autorisations seraient en partie masquées par un refus placé avant elles (par exemple F42, journaux de la DMZ, "
         "derrière F12). Le script de la matrice contrôle qu'aucune autorisation n'est masquée dans l'ordre de déploiement. Les refus "
         "explicites servent à compter et à lever une alerte sur les tentatives qui comptent (une caméra qui cherche à joindre un poste, "
         "un poste d'administration qui veut sortir sur Internet).</li>",
         f"<li>{V21} <b>Internet</b> : l'objet INTERNET (et NOMADES) vaut toute adresse <b>hors</b> des préfixes du site (objet par "
         "négation sur le Stormshield, interface externe sur le FortiGate) : une autorisation depuis ou vers Internet n'ouvre donc jamais "
         "une zone interne.</li>",
         "<li><b>IPv4 et IPv6</b> : chaque règle vaut pour les deux familles (mêmes terminaisons d'adresse, voir le plan d'adressage).</li>",
         f"<li>{V21} <b>Plan de contrôle hors matrice</b> : eBGP, iBGP par câble direct, BFD, OSPF et liens de haute disponibilité des "
         "grappes ne traversent aucun pare-feu ; ils sont protégés par des ACL et la protection du plan de contrôle (CoPP) des "
         "équipements (CCTP lots 1 et 2).</li>",
         "<li><b>Statuts</b> : " + statut("à confirmer (Pxx)") + " = dépend d'un choix d'un autre point du cahier des charges ; "
         + statut("écart Ex") + " = règle de l'architecture que l'analyse de sécurité propose de faire évoluer (section 6) ; "
         + V21 + " = règle ajoutée ou modifiée en v2.1.</li></ul>",
         "<h2>2. Zones</h2>",
         tableau(["Zone", "Contenu", "Confiance"], [[z(k), e(v[0]), e(v[1])] for k, v in F.ZONES.items()]),
         "<h2 class='saut'>3. Vue d'ensemble : quelles zones se parlent</h2>",
         "<p>Chaque case donne les règles qui concernent ce couple de zones (en rouge : refus explicites). Une case grise vide = aucun flux, "
         "refus par défaut. La diagonale correspond aux flux internes à une zone (ACL).</p>",
         grille(),
         "<h2>4. Objets d'adresses</h2>",
         tableau(["Objet", "Zone", "Contenu", "IPv4"], [[f"<b>{e(k)}</b>", z(v[0]), e(v[1]), contenu_objet(k)] for k, v in F.OBJETS.items()],
                 mono=(3,)),
         "<div class='paysage'><h2>5. Règles</h2>"]
    section = None
    lignes = []
    entetes = ["Id", "Source", "Destination", "Services", "Action", "Appliquée par", "Inspection", "Journal", "Pourquoi"]
    for r in F.R:
        if r["section"] != section:
            if lignes:
                H.append(tableau(entetes, lignes, cls="regles"))
            section, lignes = r["section"], []
            H.append(f"<h3>{e(section)}</h3>")
        marque = f" {V21}" if r["id"] in NOUVELLES_V21 | MODIFIEES_V21 else ""
        lignes.append([f"<b>{r['id']}</b>{marque}{statut(r['statut'])}", objets(r["src"]), objets(r["dst"]),
                       "<code>" + services(r["svc"]) + "</code>", action(r["action"]), appliquee(r),
                       e(r["profil"]), e(r["journal"]),
                       f"<span class='pourquoi'>{e(r['pourquoi'])}</span>" + (f"<br><span class='ref'>{e(r['ref'])}</span>" if r["ref"] else "")])
    H.append(tableau(entetes, lignes, cls="regles"))
    H.append("</div>")
    integres = ", ".join(F.INTEGRES_V21)
    proposes = ", ".join(k for k in F.ECARTS if k not in F.INTEGRES_V21)
    H.append("<h2 class='saut'>6. Écarts relevés en v2 et leur traitement</h2>"
             "<p>En détaillant chaque flux jusqu'au port, quatre règles de l'architecture v2 sont apparues à améliorer, et la zone de l'IA "
             f"locale (note du point 11) devait trouver sa place. {V21} Les écarts {integres} sont intégrés à l'architecture v2.1 "
             f"(architecture L3, matrice résumée). Les écarts {proposes} restent des propositions pour une version ultérieure : ils "
             "dépendent de choix des points 13 (messagerie) et 11 (plateforme d'IA).</p>")
    for k, (titre, constat, proposition, points) in F.ECARTS.items():
        regles = ", ".join(r["id"] for r in F.R if r["statut"] == f"écart {k}")
        etat = "intégré en v2.1 " + V21 if k in F.INTEGRES_V21 else "proposé (version ultérieure)"
        H.append(f"<div class='fiche'><h3>{k} · {e(titre)}</h3><p><b>Constat.</b> {e(constat)}</p><p><b>Proposition.</b> {e(proposition)}</p>"
                 f"<p class='sous'>État : {etat} · points concernés : {e(points)}{' · règles ' + regles if regles else ''}</p></div>")
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
             "le mentionnent, ce qui relie une alerte à sa justification.</li></ul>")
    H.append("<div class='garde'>" + CH.bloc_suivi("RLI-ETU-006", changements="règles F56 à F70 (DNS, DHCP, CAPWAP, NUT, NTP, sauvegarde, bastion, alertes, groupe "
                                                      "électrogène), ordre de déploiement contrôlé, objet INTERNET par négation, "
                                                      "écarts E2 à E4 intégrés, journaux en deux durées") + "</div>")
    return CH.page(titre="Matrice des flux entre zones", titre_court="Matrice des flux", ref="RLI-ETU-006", points="09", dossier=BUILD,
                   chapo="Qui parle à qui, sur quels ports, par quel pare-feu, avec quelle inspection, et pourquoi. Source unique : "
                         "<code>securite/flux.py</code> ; tableur : <code>RLI-P09-matrice-flux.csv</code>.",
                   corps="\n".join(H), css_extra=CSS)


# Carte des risques : vert, jaune, orange, rouge (code de lecture usuel des cartes de risques, inchangé) ; le reste à la charte.
CSS_RISQUE = """
table.carte { width: auto; margin: 3mm auto; break-inside: avoid; }
.bloc { break-inside: avoid; }
td:first-child b { white-space: nowrap; } table.carte td, table.carte th { width: 30mm; height: 15mm; text-align: center; vertical-align: middle; font-size: 8pt; border: 1px solid #fff; }
.r1 { background: #DCEFE3; } .r2 { background: #FBF0C9; } .r3 { background: #F7D2B5; } .r4 { background: #F2B8B0; }
.ini { font-weight: 600; color: var(--encre); } .res { font-weight: 600; color: var(--emeraude-fonce); } .acc { font-style: italic; }
.etat { display: inline-block; padding: 0 1.2mm; font: 600 6.4pt var(--mono); white-space: nowrap; border: 1px solid currentColor; }
.e-place { color: var(--emeraude-fonce); } .e-prop { color: var(--alerte); } .e-org { color: var(--secondaire); }
.n-couverte { color: var(--emeraude-fonce); font-weight: 600; } .n-partielle { color: var(--alerte); font-weight: 600; } .n-client { color: var(--discret); font-weight: 600; }
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
    regles = {r["id"]: r for r in F.R}
    H = [encadre([
        "<b>Coupure électrique prolongée</b> : événement redouté ER8, risque non intentionnel RA1 (section 5) placé sur les cartes des "
        "risques ; groupe électrogène et inverseur de source au socle ; mainteneur du groupe en partie prenante (PP8).",
        "<b>Plan de traitement</b> : la colonne « dont non déployées » sépare les mesures en place de celles qui restent à faire ; le "
        "risque résiduel affiché suppose ces propositions appliquées.",
        "<b>Cohérence</b> : règle de sélection des sources de risque précisée (SR6), mesures propres au site jumeau, revue annuelle du cycle "
        "opérationnel et cycle stratégique de 3 ans (M-GOU-1)."]),
         "<div class='cles'>", f"<div class='cle'><b>{len(EB.VALEURS)}</b>valeurs métier</div>",
         f"<div class='cle'><b>{len(EB.EVENEMENTS)}</b>événements redoutés</div>",
         f"<div class='cle'><b>{sum(s[5] for s in EB.SOURCES)}</b>sources de risque retenues</div>",
         f"<div class='cle'><b>{len(EB.SCENARIOS)}</b>scénarios stratégiques</div></div>",
         "<h2>1. Atelier 1 : cadrage et socle de sécurité</h2>",
         f"<p><b>Mission.</b> {e(EB.MISSION)}</p><p><b>Périmètre.</b> Le SI du bâtiment conçu dans ce projet (réseau, datacenter, DMZ, "
         "administration, sûreté, énergie) et son lien avec le site jumeau (Digne ou Gap). Hors périmètre : les applications nationales de "
         "l'AMU (scolarité, RH), qui ont leur propre homologation.</p><h3>Valeurs métier et biens supports</h3>",
         tableau(["", "Valeur métier", "Responsable", "Biens supports"], [[f"<b>{c}</b>", e(v), e(r), e(b)] for c, v, r, b in EB.VALEURS]),
         "<h3>Échelle de gravité</h3>",
         tableau(["", "Niveau", "Signification"], [[f"G{k}", e(v[0]), e(v[1])] for k, v in EB.GRAVITE.items()]),
         "<h3>Événements redoutés</h3>",
         tableau(["", "Valeur", "Événement redouté", "Impacts", "Gravité"],
                 [[f"<b>{c}</b>" + (f" {V21}" if c == "ER8" else ""), v, e(t), e(i), f"<b>G{g}</b> {e(EB.GRAVITE[g][0])}"]
                  for c, v, t, i, g in EB.EVENEMENTS]),
         "<h3>Socle de sécurité</h3>",
         tableau(["Référentiel", "Statut", "État dans le projet"], [[e(a), e(b), e(c)] for a, b, c in EB.SOCLE]),
         "<h2 class='saut'>2. Atelier 2 : sources de risque et objectifs visés</h2>",
         "<p>Motivation et ressources notées de 1 à 3. Un couple est retenu si sa pertinence (motivation × ressources) atteint 4, "
         "ou s'il est fréquent dans le secteur (SR5), sauf s'il est traité entièrement par un autre point du cahier des charges "
         "(SR6 : point 12).</p>",
         tableau(["", "Source de risque", "Objectif visé", "Motivation", "Ressources", "Pertinence", "Retenu", "Commentaire"],
                 [[f"<b>{c}</b>", e(s), e(o), str(m), str(r), f"<b>{m * r}</b>", "oui" if ok else "non", e(com)]
                  for c, s, o, m, r, ok, com in EB.SOURCES]),
         "<h2>3. Atelier 3 : écosystème et scénarios stratégiques</h2><h3>Parties prenantes</h3>",
         "<p>Notées de 1 à 4. Niveau de menace = (dépendance × pénétration) / (maturité cyber × confiance). Au-dessus de "
         f"{CH.nombre(EB.SEUIL_MENACE, 1)}, la partie prenante est critique et reçoit des mesures propres.</p>",
         tableau(["", "Partie prenante", "Dépendance", "Pénétration", "Maturité", "Confiance", "Menace"],
                 [[f"<b>{p[0]}</b>" + (f" {V21}" if p[0] == "PP8" else ""), e(p[1]), *map(str, p[2:]),
                   f"<b class='{'ko' if EB.menace(p) > EB.SEUIL_MENACE else ''}'>{CH.nombre(EB.menace(p), 2)}</b>"] for p in EB.PARTIES]),
         "<p>Parties critiques : " + ", ".join(f"{p[0]} ({e(p[1].split(' (')[0])})" for p in EB.PARTIES if EB.menace(p) > EB.SEUIL_MENACE) +
         ". Mesures propres : accès des prestataires par le bastion uniquement (M-ADM-2), clauses des CCTP (M-FOU-1), modèles d'IA vérifiés "
         "(M-IA-2), appareils personnels jamais admis dans les zones de confiance (M-RES-2, M-RES-4), liaison avec le site jumeau limitée à la "
         "réplication entre contrôleurs de domaine, chiffrée et inspectée (F53, F54), " + V21 + " groupe électrogène supervisé en lecture "
         "seule, sans modem du mainteneur (M-PHY-5).</p>",
         "<h3>Échelle de vraisemblance</h3>",
         tableau(["", "Niveau", "Signification"], [[f"V{k}", e(v[0]), e(v[1])] for k, v in EB.VRAISEMBLANCE.items()]),
         "<h3>Scénarios stratégiques</h3>",
         tableau(["", "Source", "Événements", "Chemin d'attaque", "Gravité", "Vraisemblance"],
                 [[f"<b>{c}</b>", sr, ", ".join(ers), "<ol class='chemin'>" + "".join(f"<li>{e(x)}</li>" for x in et) + "</ol>",
                   f"G{g}", f"V{v}"] for c, sr, ers, et, g, v in EB.SCENARIOS]),
         "<h2 class='saut'>4. Plan de traitement</h2>",
         "<p>Pour chaque scénario : les mesures de la PSSI et les règles de la matrice de flux qui coupent ou restreignent le chemin "
         "d'attaque, la vraisemblance qui reste une fois ces mesures appliquées, et qui accepte le risque résiduel. " + V21 + " La "
         "colonne « dont non déployées » liste les mesures proposées ou organisationnelles et les règles encore à confirmer : le "
         "risque résiduel affiché est celui de l'infrastructure une fois ces propositions appliquées.</p>"]
    lignes = []
    for c, sr, ers, et, g, v in EB.SCENARIOS:
        m, rgl, vr, qui = EB.TRAITEMENT[c]
        non = [x for x in m if mes[x][4] != "en place"] + [x for x in rgl if regles[x]["statut"]]
        lignes.append([f"<b>{c}</b>", "<br>".join(f"<b>{x}</b> {e(mes[x][2])}" for x in m), ", ".join(rgl),
                       ", ".join(non) or "—", f"G{g} V{v} → <b>G{g} V{vr}</b>", e(qui)])
    H.append(tableau(["", "Mesures (PSSI)", "Règles de flux (qui coupent ou restreignent le chemin)", "dont non déployées",
                      "Risque initial → résiduel (après les propositions)", "Accepté par"], lignes))
    ini, res = {}, {}
    for c, sr, ers, et, g, v in EB.SCENARIOS:
        ini.setdefault((g, v), []).append(f"<span class='ini'>{c}</span>")
        res.setdefault((g, EB.TRAITEMENT[c][2]), []).append(f"<span class='res'>{c}</span>")
    for c, _, _, g, v, _, vr, _, _ in EB.ACCIDENTELS:
        ini.setdefault((g, v), []).append(f"<span class='ini acc'>{c}</span>")
        res.setdefault((g, vr), []).append(f"<span class='res acc'>{c}</span>")
    resid = sorted([(g * EB.TRAITEMENT[c][2], c, g, EB.TRAITEMENT[c][2]) for c, _, _, _, g, _ in EB.SCENARIOS] +
                   [(g * vr, c, g, vr) for c, _, _, g, _, _, vr, _, _ in EB.ACCIDENTELS], reverse=True)
    rouges = [c for _, c, g, v in resid if niveau_risque(g, v) >= 3]
    jaunes = [f"{c} (G{g} V{v})" for _, c, g, v in resid if niveau_risque(g, v) == 2]
    H += ["<div class='bloc'><h3>Carte des risques avant traitement</h3>", carte(ini), "</div>",
          "<div class='bloc'><h3>Carte des risques après traitement</h3>", carte(res), "</div>",
          "<p class='sous'>En italique : risque non intentionnel (section 5), noté avec les mêmes échelles.</p>",
          f"<p>{'Aucun risque ne reste en orange ou en rouge.' if not rouges else 'Risques encore élevés : ' + ', '.join(rouges) + '.'} "
          f"Restent en zone jaune, sous surveillance : {', '.join(jaunes)}. SS1 et SS4 gardent une gravité critique : les mesures "
          "réduisent leur vraisemblance, pas leurs conséquences, d'où l'importance des sauvegardes hors ligne et du plan de crise (point 19). "
          "SS6 (détournement de l'IA) porte sur une technologie récente dont les attaques évoluent vite, et SS5 dépend aussi des "
          "opérateurs (déni de service). Ces quatre scénarios justifient une revue annuelle du cycle opérationnel (scénarios et "
          "vraisemblances) ; le cycle stratégique reste de 3 ans (M-GOU-1).</p>",
          "<h2>5. Risques non intentionnels (socle) " + V21 + "</h2>",
          "<p>EBIOS RM traite les sources de risque intentionnelles ; les événements accidentels relèvent du socle (atelier 1). Ils sont "
          "notés ici avec les mêmes échelles pour figurer sur les cartes des risques.</p>",
          tableau(["", "Événement", "ER", "Risque v2 → v2.1", "Mesures (PSSI)", "Accepté par", "Commentaire"],
                  [[f"<b>{c}</b>", e(ev), er, f"G{g} V{v} → <b>G{g} V{vr}</b>", "<br>".join(f"<b>{x}</b> {e(mes[x][2])}" for x in m),
                    e(qui), e(com)] for c, ev, er, g, v, m, vr, qui, com in EB.ACCIDENTELS]),
          "<h2>6. Limites de l'analyse</h2><ul>"
          "<li>Analyse faite par le concepteur, sans atelier avec les métiers de l'IUT : les valeurs métier et la gravité sont à valider par "
          "la direction et les laboratoires avant l'homologation.</li>"
          "<li>L'atelier 4 (scénarios opérationnels) n'est pas détaillé : la vraisemblance repose sur l'architecture v2.1 et sur la menace "
          "décrite par le CERT-FR. Un test d'intrusion (M-GOU-3) la confirmera.</li>"
          "<li>Les services de l'AMU (applications nationales, messagerie fédérée) sont hors périmètre et relèvent de leur propre analyse.</li></ul>",
          "<div class='garde'>" + CH.bloc_suivi("RLI-ETU-007", changements="coupure électrique prolongée (ER8, RA1, PP8, socle), colonne des mesures non "
                                                   "déployées, règle de sélection des sources précisée, revue annuelle et cycle de 3 ans") + "</div>"]
    return CH.page(titre="Analyse de risque EBIOS RM", titre_court="Analyse de risque", ref="RLI-ETU-007", points="09", dossier=BUILD,
                   chapo="Méthode EBIOS Risk Manager (ANSSI, v1.5), version allégée : ateliers 1 à 3 détaillés, vraisemblance des "
                         "scénarios estimée directement, puis plan de traitement relié à la PSSI et à la matrice de flux.",
                   corps="\n".join(H), css_extra=CSS + CSS_RISQUE)


def doc_pssi():
    PP.verifier()
    etats = {"en place": "e-place", "proposé": "e-prop", "organisationnel": "e-org"}
    nb = {k: sum(m[4] == k for m in PP.MESURES) for k in etats}
    nouvelles = {"M-PHY-4", "M-PHY-5", "M-PHY-6", "M-PHY-2", "M-PHY-3", "M-ADM-2", "M-DET-1", "M-POS-2", "M-RES-1"}
    H = [encadre([
        "<b>Groupe électrogène</b> : M-PHY-4 réécrite (onduleurs, NUT seulement si le groupe n'a pas repris) et nouvelle mesure M-PHY-5 "
        "(groupe et inverseur, supervision en lecture seule, sans modem).",
        "<b>Mesures mises à jour</b> : extinction au gaz inerte en place (M-PHY-2), travail isolé à part (M-PHY-6), vidéoprotection "
        "autorisée par le préfet et sans caméra au foyer (M-PHY-3), VPN IKEv2 en place (M-ADM-2), journaux en deux durées (M-DET-1), "
        "correctifs des contrôleurs de domaine sans flux sortant (M-POS-2)."]),
         "<div class='cles'>", f"<div class='cle'><b>{len(PP.MESURES)}</b>mesures</div>",
         f"<div class='cle'><b>{nb['en place']}</b>dans l'architecture v2.1</div>",
         f"<div class='cle'><b>{nb['proposé']}</b>proposées (version ultérieure)</div>",
         f"<div class='cle'><b>{nb['organisationnel']}</b>organisationnelles (client)</div></div>",
         "<h2>1. Objet et périmètre</h2>",
         "<p>Le cahier des charges demande de « mettre l'accent sur la sécurité en général : des biens, des personnes, des réseaux ». Cette "
         "politique fixe les règles qui s'appliquent au SI du bâtiment (réseau, datacenter, DMZ, administration, systèmes de sûreté, "
         "énergie, plateforme d'IA) et à ceux qui l'utilisent ou l'administrent. Elle s'applique aussi au site jumeau (Digne ou Gap) pour ce qui "
         "est partagé (annuaire, liaison).</p>",
         "<p><b>Cadre.</b> PSSI de l'AMU ; RGPD ; conservation des données de connexion (CPCE L34-1, décrets n° 2021-1361 et 2021-1362) ; directive "
         "NIS 2, que la loi Résilience doit transposer : nous retenons l'hypothèse que l'établissement sera une entité concernée, et nous "
         "anticipons ses obligations (gouvernance, gestion des risques, notification des incidents). Recommandations de l'ANSSI listées "
         "dans <code>docs/anssi/referentiel_anssi.md</code>.</p>",
         "<h2>2. Organisation</h2>",
         tableau(["Rôle", "Qui", "Responsabilités"], [[f"<b>{e(a)}</b>", e(b), e(c)] for a, b, c in PP.ROLES]),
         "<div class='bloc'><h2>3. Principes</h2>",
         tableau(["Principe", "Traduction dans l'architecture"], [[f"<b>{e(a)}</b>", e(b)] for a, b in PP.PRINCIPES]), "</div>",
         "<h2 class='saut'>4. Mesures</h2>",
         "<p>État : <span class='etat e-place'>en place</span> = dans l'architecture v2.1 ; <span class='etat e-prop'>proposé</span> = "
         "ajouté par ce dossier, à intégrer dans une version ultérieure ; <span class='etat e-org'>organisationnel</span> = relève de "
         "l'exploitation par le client.</p>"]
    dom = None
    lignes = []
    for code, d, titre, exig, etat, ref in PP.MESURES:
        if d != dom:
            if lignes:
                H.append(tableau(["", "Mesure", "Exigence", "État", "Références"], lignes))
            dom, lignes = d, []
            H.append(f"<h3>{e(d)}</h3>")
        lignes.append([f"<b>{code}</b>" + (f" {V21}" if code in nouvelles else ""), f"<b>{e(titre)}</b>", e(exig),
                       f"<span class='etat {etats[etat]}'>{etat}</span>", f"<span class='ref'>{e(ref)}</span>"])
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
             "à la charge du client. Les mesures partielles deviennent couvertes avec les propositions restantes (messagerie en relais E1, "
             "inventaire des comptes privilégiés, revue des produits qualifiés).</p>")
    H.append("<h2>6. Application, dérogations, revue</h2><ul>"
             "<li>Une dérogation à cette politique est demandée par écrit au RSSI, limitée dans le temps, et accompagnée d'une mesure compensatoire.</li>"
             "<li>La politique est revue chaque année et après tout incident majeur ou changement d'architecture (nouvelle version de l'infrastructure).</li>"
             "<li>Le non-respect par un utilisateur relève de la charte informatique et du règlement intérieur (point 19).</li></ul>")
    H.append("<div class='garde'>" + CH.bloc_suivi("RLI-ETU-008", changements="groupe électrogène (M-PHY-4, M-PHY-5), extinction en place, travail isolé, "
                                                      "vidéoprotection, VPN IKEv2, journaux en deux durées, correctifs du tier 0") + "</div>")
    return CH.page(titre="Politique de sécurité du SI", titre_court="PSSI", ref="RLI-ETU-008", points="09", dossier=BUILD,
                   chapo="PSSI du bâtiment IUT Génie Télécom : déclinaison locale de la PSSI de l'AMU. Elle s'appuie sur l'analyse de "
                         "risque (<code>RLI-P09-analyse-risque-ebios.pdf</code>) et la matrice des flux (<code>RLI-P09-matrice-flux.pdf</code>).",
                   corps="\n".join(H), css_extra=CSS + CSS_RISQUE)


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


def ecrire_sources(chemin):
    """Archive des sources du point 09, comme celle du dépôt GesTT (dates fixes : archive reproductible)."""
    import zipfile
    fichiers = ["securite/.gitignore", "securite/build.py", "securite/ebios.py", "securite/flux.py", "securite/pssi.py",
                "commun/charte.py", "livrables/securite/README.md"]
    with zipfile.ZipFile(chemin, "w", zipfile.ZIP_DEFLATED) as z:
        for f in fichiers:
            info = zipfile.ZipInfo(f, date_time=(2026, 11, 20, 0, 0, 0))
            info.external_attr = 0o644 << 16
            z.writestr(info, (ROOT / f).read_bytes())


def main():
    F.verifier()
    print("Matrice de flux : contrôles OK (objets au plan, adresses dans leur sous-réseau, aucune autorisation masquée)")
    OUT.mkdir(parents=True, exist_ok=True)
    BUILD.mkdir(parents=True, exist_ok=True)
    ecrire_csv(OUT / CSV_MATRICE)
    docs = [("matrice_flux", doc_matrice), ("analyse_risque", doc_ebios), ("pssi", doc_pssi)]
    for nom, fonction in docs:
        page = BUILD / f"{NOMS[nom]}.html"
        CH.ecrire_et_imprimer(fonction(), page, OUT / f"{NOMS[nom]}.pdf")
        print(f"  livrables/securite/{NOMS[nom]}.pdf")
    (OUT / "README.md").write_text(
        "# Sécurité des réseaux (point 09)\n<!-- onglet: Sécurité -->\n\n"
        "Politique de sécurité du réseau du bâtiment : flux autorisés entre zones, analyse de risque et PSSI. "
        "Noms et dossier identiques au dépôt GesTT de la tâche P09 (PR #12).\n\n"
        "| Document | Réf. | Contenu |\n|---|---|---|\n"
        f"| **[RLI-P09-matrice-flux.pdf](RLI-P09-matrice-flux.pdf)** | RLI-ETU-006 | Matrice des flux entre zones : {len(F.R)} règles détaillées, pare-feu, "
        "inspection, justification, ordre de déploiement, écarts avec l'architecture, tests de recette proposés. Tableur : `RLI-P09-matrice-flux.csv` |\n"
        "| **[RLI-P09-analyse-risque-ebios.pdf](RLI-P09-analyse-risque-ebios.pdf)** | RLI-ETU-007 | Analyse EBIOS RM allégée : valeurs métier, événements redoutés, "
        "sources de risque, écosystème, scénarios stratégiques, plan de traitement, risques non intentionnels et cartes des risques |\n"
        "| **[RLI-P09-pssi.pdf](RLI-P09-pssi.pdf)** | RLI-ETU-008 | Politique de sécurité du SI du site : organisation, principes, mesures (biens, personnes, "
        "réseaux, énergie, IA), conformité aux 42 mesures du guide d'hygiène |\n"
        "| [RLI-P09-sources.zip](RLI-P09-sources.zip) | — | Sources des trois documents (`securite/`, `commun/charte.py`) |\n\n"
        f"**Version {CH.VERSION[1:]} — {CH.DATE_VERSION}** : règles F56 à F70 (DNS, DHCP, CAPWAP, NUT, NTP, sauvegarde, bastion, alertes, "
        "groupe électrogène), ordre de déploiement contrôlé, écarts E2 à E4 intégrés, coupure électrique prolongée dans l'analyse de "
        "risque, mesures M-PHY-4 à M-PHY-6 dans la PSSI, journaux en deux durées (connexion 1 an, navigation 6 mois), repérés « v2.1 » "
        "dans les documents. Version précédente : le dépôt GesTT du 19/11/2026 (PR #12).\n\n"
        "Régénérer : `python3 securite/build.py` (sources : `securite/flux.py`, `ebios.py`, `pssi.py`).\n",
        encoding="utf-8")
    ecrire_sources(OUT / SOURCES_ZIP)
    print(f"  livrables/securite/README.md, {SOURCES_ZIP}")


if __name__ == "__main__":
    main()
