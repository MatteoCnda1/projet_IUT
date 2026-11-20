#!/usr/bin/env python3
"""Traitement des audits de l'infrastructure (RLI-AUD-001).

Partie A : audit du 15/11/2026 (version 1 -> version 2), 9 constats vérifiés puis corrigés.
Partie B : audit v2.1 du 20/11/2026 (version 2 -> version 2.1) : quatre audits en parallèle, BET, groupe électrogène,
intégration continue, décisions D1 à D6, points ouverts.

Usage : python3 architecture/audit/traitement_audit.py
        (dernière étape de la chaîne, après l'énergie et le chiffrage : bash outils/ci/generer_tout.sh)
Entrées : constats_v21.json (ce dossier : constats v2.1, statuts, décisions, points ouverts, à tenir à jour),
          rapport d'audit du 15/11/2026 (ce dossier, texte figé), archives v1 et v2 (livrables/archives/),
          chiffrage/estimation.json, livrables/energie_refroidissement/resume.json, livrables/plan_adressage/vlans.csv,
          outils/ci/ (liste des contrôles et des étapes de la chaîne)
Sorties : livrables/audit/traitement_audit.html (+ .pdf), README.md, copie du rapport d'audit
Aucun montant ni aucune valeur de l'énergie n'est écrit ici : tout est relu dans les JSON.
"""
import csv
import html
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

ICI = Path(__file__).resolve().parent
ROOT = ICI.parent.parent
sys.path.insert(0, str(ROOT))
from commun import charte as CH  # noqa: E402

OUT = ROOT / "livrables" / "audit"
ARCH = ROOT / "livrables" / "archives"
V1, V2 = ARCH / "v1_2026-11-15", ARCH / "v2_2026-11-20"
EN = "energie_refroidissement"
REF = "RLI-AUD-001"
POINTS = ["03", "04", "05", "09", "14", "18", "19"]
DATE_AUDIT_1 = "15/11/2026"  # audit de la v1 (date historique, ne change plus)

e = html.escape
N = CH.nombre
NBSP = CH.NBSP


def lire(chemin):
    return json.loads(Path(chemin).read_text(encoding="utf-8"))


def eur_md(v):
    """Montant pour un README Markdown : espaces ordinaires (règle de la charte pour le Markdown)."""
    return f"{v:,.0f} €".replace(",", " ")


def dec_md(v, n):
    return f"{v:.{n}f}".replace(".", ",")


CSS_PROPRE = """
.sev { display: inline-block; font: 600 6.2pt/1.2 var(--mono); letter-spacing: .04em; text-transform: uppercase; padding: .2mm 1.1mm;
  border: 1px solid currentColor; white-space: nowrap; }
.sev.critique, .sev.bloquant { color: var(--rouge); } .sev.majeur { color: var(--alerte); }
.sev.mineur, .sev.coquille { color: var(--discret); } .sev.question { color: var(--secondaire); }
.fonde { color: var(--emeraude-fonce); font-weight: 600; } .partiel { color: var(--alerte); font-weight: 600; } .rejet { color: var(--rouge); font-weight: 600; }
.st-traite { color: var(--emeraude-fonce); font-weight: 600; } .st-partiel, .st-ouvert { color: var(--alerte); font-weight: 600; }
.st-hors, .st-sans { color: var(--discret); font-weight: 600; }
.st-traite, .st-partiel, .st-ouvert, .st-hors, .st-sans { white-space: nowrap; }
.fiche { border: 1px solid var(--trait); background: var(--surface); padding: 2.5mm 3.5mm; margin: 3mm 0; break-inside: avoid; }
.fiche h3 { margin: 0 0 1.5mm; }
.fiche dl { display: grid; grid-template-columns: 30mm 1fr; gap: 1mm 3mm; margin: 0; }
.fiche dt { font: 500 6.8pt/1.6 var(--mono); letter-spacing: .05em; text-transform: uppercase; color: var(--secondaire); } .fiche dd { margin: 0; }
.partie { font: 600 7.4pt/1.3 var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--emeraude-fonce);
  border-top: 2px solid var(--encre); padding-top: 2mm; margin: 8mm 0 0; }
.serre td, .serre th { padding: .8mm 1.5mm; } .serre { font-size: 7.4pt; }
.id { font-family: var(--mono); font-weight: 600; white-space: nowrap; color: var(--encre); }
"""

# ======================================================================================
# Partie A : audit du 15/11/2026 (v1 -> v2). Texte de la v2, complété en v2.1 (SYS-03, renvois, vocabulaire).
# ======================================================================================
SEV = {"Critique": "critique", "Majeur": "majeur", "Mineur": "mineur", "Question": "question"}
VERDICT = {"Fondé": "fonde", "Partiellement fondé": "partiel", "Fondé, déjà justifié en v1": "partiel", "Non retenu": "rejet"}

ADR, L2, L3 = "plan_adressage", "architecture_l2", "architecture_l3"
CHF, SCH = "chiffrage", "schéma principal"

# (réf, domaine, sévérité, constat de l'audit, verdict, vérification, correction v2, livrables)
CONSTATS = [
    ("NET-01", "Wi-Fi et mobilité", "Critique",
     "Coupure des sessions lors de l'itinérance Wi-Fi entre étages : FlexConnect en commutation locale, VLAN 115 au RDC et 215 à l'étage 1.",
     "Fondé",
     "Exact. La v1 l'assumait (« revers assumé », architecture L2, section 1) mais sans le résoudre. Le même document montrait en rouge "
     "le pool WIFI-ETU-B1 à 94 % (960 clients pour 1 022 adresses).",
     "Bornes en mode local : le trafic remonte à deux contrôleurs physiques Catalyst 9800-L-F en HA SSO, raccordés au cœur en 2×10G. "
     "Trois VLAN Wi-Fi pour tout le bâtiment, avec passerelle sur le cœur : 514 WIFI-PERS (/22), 515 WIFI-ETU (/20, 37 % d'occupation, "
     "bail 2 h) et 530 WIFI-INVITES (/22, bail 1 h). Un client garde son adresse partout ; itinérance 802.11r/OKC. La VM 9800-CL est retirée.",
     [ADR, L2, L3, SCH, CHF, EN]),
    ("SEC-01", "Pare-feu et débit", "Critique",
     "Goulet d'étranglement du Stormshield SN710 (inspection applicative) face aux flux inter-VRF à 10/40G ; transit par la pile C9200L EL-SW.",
     "Partiellement fondé",
     "Le chemin par EL-SW (petits tampons) était réel. Le chiffre de 2,5 Gb/s avancé par l'audit n'est pas sourcé. Surtout, le plus gros "
     "flux inter-VRF de la v1 était la sauvegarde (hyperviseurs NM en VRF ADM vers DT-BKP1 en VRF SRV), que l'audit n'identifie pas.",
     "Stormshield raccordé directement au cœur (Po2/Po3, 2×10G MEC par nœud, module 10G chiffré). EL-SW ne porte plus que la gestion. "
     "PBS déplacé dans la VRF ADM (VLAN 909) : les sauvegardes NM et DT ne traversent plus le pare-feu. Politique d'inspection par flux "
     "(IPS complet vers l'AD, filtrage à états seul pour les flux chiffrés de sauvegarde de la DMZ). Seuil de supervision à 60 %, "
     "évolution possible vers un SN910.",
     [L2, L3, ADR, SCH, CHF]),
    ("SYS-01", "Cohérence documentaire", "Majeur",
     "Le chiffrage prévoit 3 nœuds Proxmox avec Ceph, l'architecture L2 2 nœuds en ZFS répliqué + QDevice ; témoin non chiffré.",
     "Fondé",
     "Exact. La v1 le signalait elle-même dans une note de l'architecture L2, sans reporter la correction dans le chiffrage. "
     "Il manquait aussi la carte 4×1G par nœud et les kits de pile C9200L.",
     "Chiffrage aligné : 2 nœuds R660xs (ZFS, carte 4×1G), NM-WITNESS chiffré, 3 kits de pile, souscription Proxmox recalculée par socket.",
     [CHF, L2]),
    ("SYS-02", "Dimensionnement", "Majeur",
     "16 serveurs physiques dont 12 serveurs 1U mono-rôle en DMZ et au datacenter (37,8 k€ de serveurs).",
     "Fondé",
     "Exact (6 Dell R260 + 6 Dell R360). L'audit parle de « 16 serveurs Windows » dans la question Q13 : seuls 6 étaient sous Windows. "
     "Le gain réel sur les serveurs est de 18,1 k€, pas de 20 k€.",
     "Deux clusters Proxmox séparés. Cluster DT (DT-PVE1/2, tier 0) : VM AD, NPS, DHCP. Cluster DMZ (DM-PVE1/2 + DM-WITNESS) : VM Caddy ×2, "
     "DNS public ×2 (le DNS public devient redondant), web, messagerie, applicatif. Une VM de la DMZ ne partage jamais un hyperviseur "
     "avec l'AD. On passe de 16 à 9 serveurs physiques.",
     [L2, ADR, SCH, CHF, EN]),
    ("SEC-02", "Active Directory", "Majeur",
     "Contrôleurs de domaine (tier 0) dans le même VLAN 300 que les serveurs DHCP et NPS (tier 1) : non conforme au guide ANSSI PA-099.",
     "Fondé",
     "Exact : DT-AD1/2 en 10.13.48.11-12, VLAN 300, passerelle sur le cœur. Le routage entre serveurs ne passait par aucun filtrage.",
     "VLAN 310 SRV-T0 (10.13.52.0/27, 2001:660:5402:4310::/64). Sa passerelle est le Stormshield, pas le cœur : tout flux vers un "
     "contrôleur de domaine est filtré, même depuis le VLAN 300. Pas d'accès Internet pour les contrôleurs de domaine. Hyperviseurs DT, "
     "PBS et iDRAC associés traités comme tier 0 : hors domaine, rôle Teleport dédié.",
     [ADR, L2, L3, SCH]),
    ("SEC-03", "Sauvegarde et rançongiciel", "Majeur",
     "Pas d'immuabilité (S3 Object Lock en mode conformité) ni de copie hors ligne des sauvegardes PBS.",
     "Fondé",
     "Exact. Le référentiel ANSSI du projet (BP-100) le notait déjà comme manque.",
     "Règle 3-2-1-1-0 : PBS hors domaine avec comptes locaux et MFA ; jetons API des hyperviseurs limités à l'écriture (pas de suppression) ; "
     "datastore amovible sur 3 disques en rotation hebdomadaire (un hors site, coffre ignifuge) ; copie externalisée en mode S3 Object Lock "
     "conformité chez un hébergeur SecNumCloud ; tests de restauration.",
     [ADR, L2, L3, CHF]),
    ("SYS-03", "Salle en sous-sol", "Majeur",
     "Salle serveur au sous-sol sans plancher surélevé, batardeau, extinction automatique ni groupe électrogène.",
     "Fondé",
     "Exact. Ces protections avaient été chiffrées en option et écartées en v1. Décision de l'équipe (15/11/2026) : intégrer la protection "
     "contre l'eau et l'extinction. Le groupe électrogène, laissé de côté en v2, est intégré en v2.1 : le client a confirmé le 20/11/2026 "
     "que le site n'en a pas (partie B, section 12).",
     "Plancher technique surélevé de 30 cm, batardeau à la porte, clapet anti-retour, câble de détection de fuite ; détection VESDA et extinction "
     "automatique au gaz inerte IG-541 ; arrêt ordonné sur batterie par NUT (serveur sur NM-WITNESS), autonomie portée à 33 min avec un seul "
     "onduleur (pack batterie). __V21__ Groupe électrogène dédié et inverseur de source automatique ; l'arrêt ordonné ne se déclenche plus "
     "que si le groupe n'a pas repris.",
     [EN, CHF]),
    ("NET-02", "Cœur et distribution", "Mineur",
     "4 commutateurs C9500 de distribution dans la même baie que le cœur au lieu d'un cœur replié (38 k€, 640 W).",
     "Fondé, déjà justifié en v1",
     "La v1 étudiait déjà cette variante (architecture L2, section 1, chiffrage, énergie) et l'écartait : le cahier des charges impose trois couches. "
     "L'audit recommande lui-même de « l'assumer ».",
     "Pas de changement d'architecture. La variante cœur replié est présentée comme étudiée et chiffrée (sur 2 × C9500-48Y4C) dans le chiffrage et "
     "dans le document énergie.",
     [L2, CHF, EN]),
    ("SEC-04", "Traçabilité légale", "Mineur",
     "Conservation légale d'un an des journaux (NAT, DHCP) reposant sur une seule VM Docker.",
     "Fondé",
     "Exact : un conteneur syslog dans la VM de supervision.",
     "Chaîne dédiée, conforme au guide ANSSI sur la journalisation : 2 collecteurs rsyslog en LXC (un par nœud, VIP 10.13.59.55, TCP + TLS) ; "
     "archives brutes quotidiennes avec empreinte SHA-256 horodatée (RFC 3161) ; conservation d'un an ; copies par PBS (hors ligne et immuable) ; "
     "Loki pour la recherche. Volume estimé : environ 60 Go compressés par an.",
     [L3, L2, ADR, SCH]),
]

# Autres faiblesses du rapport (sections détaillées et questions du jury)
AUTRES = [
    ("RPO de 5 min", "Partiellement fondé", "Le contrôleur Wi-Fi n'est plus une VM ; la supervision est répliquée toutes les minutes ; les journaux ne dépendent plus d'elle.", [L2, SCH]),
    ("RTO de plus de 44 h depuis le cloud", "Fondé", "La copie hors ligne (disque amovible) permet une restauration locale à la vitesse d'un disque. Le cloud devient le dernier recours. Un PBS croisé avec le site jumeau est une piste du point 15.", [L3, CHF]),
    ("Inspection TLS absente (Q7)", "Fondé", "Inspection sur le FortiGate pour les postes gérés uniquement, avec liste d'exclusion (banque, santé, administrations) et cadre légal (charte, AIPD). Pas de déchiffrement sur les appareils personnels.", [L3]),
    ("Asymétrie BGP (Q4)", "Fondé", "Annonce conditionnelle du /24 vers le FAI 2 (seulement si la route du FAI 1 disparaît), iBGP entre les routeurs, BFD vers les opérateurs. "
     "La solution proposée par l'audit (« set asymroute enable ») est écartée : elle désactive le contrôle d'état du FortiGate.", [L3, ADR, SCH]),
    ("PMTUD et MTU (plan d'actions)", "Partiellement fondé", "Les grandes trames ne servaient déjà que sur les liens d'infrastructure. Ajouts : ICMPv4 3/4 et ICMPv6 type 2 autorisés explicitement, MSS ajusté sur les tunnels.", [L3]),
    ("MAB des caméras et badgeuses (Q10)", "Fondé", "802.1X EAP-TLS quand l'équipement le permet ; sinon MAB avec ACL téléchargée par RADIUS (seul le serveur métier est joignable) ; coupure du port à la première violation.", [L2, L3]),
    ("Extinction ordonnée (Q13)", "Fondé", "Séquence NUT décrite et chiffrée dans le document énergie ; l'autonomie visée passe de 10 à 20 min pour la couvrir.", [EN]),
    ("Pool Wi-Fi étudiants à 94 %", "Fondé", "Voir NET-01 : /20 à 37 % et bail de 2 h.", [ADR]),
    ("Fuite de routes entre VRF sur le cœur (proposée en Q3)", "Non retenu", "Faire des fuites de routes entre VRF sur le cœur supprimerait le principe « aucune route entre VRF » : on règle le débit par le raccordement direct du pare-feu et le déplacement des sauvegardes.", []),
]

QUESTIONS = [
    ("1", "Itinérance Wi-Fi et rupture de session", "Architecture L2, sections 1 et 9 (mode local, WLC HA SSO)"),
    ("2", "4 C9500 de distribution contre cœur replié", "Architecture L2, section 1 ; chiffrage (pistes d'optimisation)"),
    ("3", "Chemin d'une trame inter-VRF", "Architecture L3, section 4 (politique d'inspection) ; L2, section 4 (Po2/Po3 sur le cœur)"),
    ("4", "Asymétrie BGP", "Architecture L3, section 6 (annonce conditionnelle, extrait EL-RTR2)"),
    ("5", "NPTv6 contre NAT44", "Architecture L3, section 6 (inchangé)"),
    ("6", "Débit UTM du SN710", "Architecture L3, section 4"),
    ("7", "Angle mort TLS", "Architecture L3, section 4 (inspection TLS) ; charte informatique (point 19)"),
    ("8", "Tiering AD et VLAN 300", "Architecture L3, section 2 ; plan d'adressage (VLAN 310)"),
    ("9", "Rançongiciel et immuabilité", "Ce document, SEC-03 ; chiffrage (disques, OPEX)"),
    ("10", "MAB des caméras", "Architecture L2, sections 7 et 8 (EAP-TLS, ACL téléchargée)"),
    ("11", "Quorum et QDevice", "Architecture L2, sections 10 et 11 (deux témoins, NM-WITNESS sert NM et DT)"),
    ("12", "RPO ZFS contre Ceph", "Architecture L2, section 10 (réplication 1 min pour la supervision)"),
    ("13", "Arrêt électrique en cascade", "Énergie, section 3 (séquence NUT) ; BET, groupe électrogène (v2.1)"),
    ("14", "Consigne à 27 °C et humidité", "Énergie, section 4 (40 à 60 % d'humidité relative)"),
]

COURT = {
    "NET-01": "Bornes en mode local, 2 contrôleurs physiques HA sur le cœur, VLAN Wi-Fi uniques (pool /20, bail 2 h)",
    "SEC-01": "Stormshield en direct sur le cœur, sauvegardes hors du pare-feu, inspection par flux",
    "SYS-01": "Chiffrage aligné : 2 nœuds + témoin, sans Ceph",
    "SYS-02": "12 serveurs physiques → 2 clusters Proxmox (DT tier 0, DMZ isolée)",
    "SEC-02": "VLAN 310 tier 0, passerelle sur le Stormshield, pas d'Internet",
    "SEC-03": "PBS hors domaine, disques hors ligne en rotation, S3 Object Lock",
    "SYS-03": "Plancher surélevé, batardeau, détection de fuite, extinction au gaz, arrêt NUT ; groupe électrogène __V21__",
    "NET-02": "Variante étudiée et chiffrée, 3 couches imposées par le CdC",
    "SEC-04": "2 collecteurs dédiés, archives scellées conservées 1 an",
}

LIBELLE = {ADR: "Plan d'adressage", L2: "Architecture L2", L3: "Architecture L3", EN: "Énergie", CHF: "Chiffrage", SCH: "Schéma principal"}

# Ce qui restait à faire le 15/11/2026, et ce que c'est devenu au 20/11/2026
RESTE_V2 = [
    ("Faire auditer la v2 (même méthode, rapport comparable) pour mesurer l'effet des corrections.",
     "Fait le 20/11/2026 : audit v2.1 (partie B), sous une autre forme (quatre audits spécialisés, constats ligne à ligne)."),
    ("Confirmer par devis : module 10G du SN710, Catalyst 9800-L-F, extinction automatique (étude par un installateur APSAD), plancher technique.",
     "Toujours ouvert (partie B, section 16)."),
    ("Valider avec le campus : cote de crue du sous-sol, annonce du /24 par l'AMU, BFD chez les opérateurs.",
     "Toujours ouvert (partie B, section 16). Le groupe électrogène n'est plus une question : le client a confirmé que le site n'en a pas."),
    ("AIPD de l'inspection TLS avec le DPO de l'AMU ; charte informatique à mettre à jour.",
     "Charte informatique rédigée au point 19 (RLI-ETU-009) ; l'AIPD de l'inspection TLS reste à faire avec le DPO."),
    ("Reporter les changements dans la maquette (point 06) : VLAN Wi-Fi sur le cœur, VLAN 310 derrière le pare-feu.",
     "Toujours ouvert : la maquette n'est pas encore versionnée (constats MAQ-01 à MAQ-08)."),
]


# ======================================================================================
# Données lues
# ======================================================================================
def nb_vlans(dossier):
    with open(dossier / "plan_adressage" / "vlans.csv", encoding="utf-8") as f:
        return sum(1 for r in csv.DictReader(f) if int(r["vlan"]) < 1000)


def serveurs(ch):
    """Serveurs physiques du chiffrage (lignes Dell), hors enregistreur vidéo."""
    return sum(lg["quantite"] for lg in ch["capex_lignes"] if "Dell" in lg["solution"] and not lg["schema"].startswith("VS-"))


def versions():
    """Chiffrage, énergie et adressage des trois versions : v1 et v2 depuis les archives, v2.1 depuis les livrables en vigueur."""
    vs = []
    for nom, date, ch, en, adr in (
            ("v1", "13/11/2026", V1 / "chiffrage" / "estimation.json", V1 / EN / "resume.json", V1),
            ("v2", "15/11/2026", V2 / "chiffrage" / "estimation.json", V2 / EN / "resume.json", V2),
            (CH.VERSION, CH.DATE_VERSION, ROOT / "chiffrage" / "estimation.json", ROOT / "livrables" / EN / "resume.json", ROOT / "livrables")):
        vs.append({"nom": nom, "date": date, "ch": lire(ch), "en": lire(en), "vlans": nb_vlans(adr)})
    return vs


def lignes_versions(vs, md=False):
    """(libellé, valeur v1, v2, v2.1) ; md=True : format Markdown (espaces ordinaires)."""
    eur = eur_md if md else CH.euros
    num = (lambda v, n=0: dec_md(v, n) if n else f"{v:,.0f}".replace(",", " ")) if md else N
    sp = " " if md else NBSP

    def secours(en):
        ge = en.get("bet", {}).get("groupe_electrogene")
        if not ge:
            return "aucun"
        return f"groupe {ge['esp_kva']}{sp}kVA, {ge['autonomie_h']}{sp}h"

    def tout(f):
        return [f(v) for v in vs]
    return [
        ("Serveurs physiques", *tout(lambda v: str(serveurs(v["ch"])))),
        ("VLAN (hors transits)", *tout(lambda v: str(v["vlans"]))),
        ("Puissance IT de la salle serveur", *tout(lambda v: f"{num(v['en']['salle']['it_typ'] / 1000, 2)}{sp}kW")),
        ("PUE de la salle serveur", *tout(lambda v: num(v["en"]["energie"]["pue"], 2))),
        ("Électricité par an", *tout(lambda v: f"{num(v['en']['energie']['kwh'])}{sp}kWh")),
        ("Autonomie avec un seul onduleur", *tout(lambda v: f"{v['en']['onduleurs']['autonomie_degrade']}{sp}min")),
        ("Secours long", *tout(lambda v: secours(v["en"]))),
        ("Lot énergie (investissement)", *tout(lambda v: eur(v["en"]["capex_lot"]))),
        ("CAPEX (aléas compris)", *tout(lambda v: eur(v["ch"]["capex"]))),
        ("OPEX annuel", *tout(lambda v: eur(v["ch"]["opex_total"]))),
        ("Coût sur 5 ans", *tout(lambda v: eur(v["ch"]["tco5"]))),
    ]


def ci():
    """Contrôles de verifier_coherence.py et étapes de generer_tout.sh, relus dans leur source."""
    src = (ROOT / "outils" / "ci" / "verifier_coherence.py").read_text(encoding="utf-8")
    controles = re.findall(r'^@controle\("(\w+)", "([^"]+)"\)', src, re.M)
    sh = (ROOT / "outils" / "ci" / "generer_tout.sh").read_text(encoding="utf-8")
    bloc = re.search(r"ETAPES=\((.*?)\)", sh, re.S)
    etapes = bloc.group(1).split() if bloc else []
    return controles, etapes


# ======================================================================================
# HTML
# ======================================================================================
def sev(g):
    return f"<span class='sev {g.lower()}'>{e(g)}</span>"


def statut_html(s):
    cls = {"traité": "st-traite", "partiel": "st-partiel", "ouvert": "st-ouvert", "hors dépôt": "st-hors", "sans objet": "st-sans"}.get(s, "st-ouvert")
    return f"<span class='{cls}'>{e(s)}</span>"


def v21(texte):
    return texte.replace("__V21__", CH.badge("v2.1"))


def partie_a(vs):
    v1, v2 = vs[0], vs[1]
    H = ["<p class='partie'>Partie A · audit du 15/11/2026 · version 1 → version 2</p>",
         "<h2 style='margin-top:2mm'>1. L'audit du 15/11/2026</h2>",
         f"<p>Le {DATE_AUDIT_1}, l'équipe a soumis l'ensemble du dossier à un <b>audit indépendant en lecture seule</b>, réalisé avec l'assistant Gemini. "
         "Trois rôles d'auditeur ont été simulés : architecture réseau L2/L3 et Wi-Fi, cybersécurité et conformité ANSSI, infrastructure physique et "
         "virtualisation. Le dossier audité comprenait les schémas, le plan d'adressage, les architectures L2 et L3, le chiffrage et le lot énergie. "
         "Les référentiels appliqués étaient les guides ANSSI (PA-022, PA-043, PA-044, PA-099, BP-031, BP-100, PA-105), NIS 2, ASHRAE A1, "
         "la NF C 15-100 et l'ISO 11801.</p>",
         "<p>Résultat : <b>16,9 / 20</b> (réseau 18,0, sécurité 17,0, systèmes et datacenter 15,8), avec 9 constats (2 critiques, 5 majeurs, "
         "2 mineurs), un plan d'actions et 14 questions pièges pour la soutenance. Le rapport complet est joint, inchangé : "
         "<code>rapport_audit_2026-11-15.pdf</code>.</p>",
         "<h3>Méthode de traitement</h3><ol>",
         "<li><b>Vérifier chaque constat</b> dans les sources du projet (<code>donnees.py</code>, scripts de chiffrage et d'énergie, schémas) avant "
         "de corriger. Un audit fait par une IA peut se tromper : chaque affirmation est classée <span class='fonde'>fondée</span>, "
         "<span class='partiel'>partiellement fondée</span> ou <span class='rejet'>non retenue</span>.</li>",
         "<li><b>Figer la version 1</b> telle qu'auditée : <code>livrables/archives/v1_2026-11-15/</code> (documents) et "
         "<code>architecture/archives/v1_2026-11-15/</code> (schémas et sources).</li>",
         "<li><b>Corriger les sources</b> puis régénérer tous les livrables : ils sont produits par script à partir d'une source unique, ce qui "
         "garde la cohérence entre plan d'adressage, schémas, chiffrage et énergie (c'est justement une incohérence entre documents qui a "
         "produit le constat SYS-01).</li>",
         f"<li><b>Tracer</b> : chaque modification porte la référence du constat (repère {CH.badge('v2')} dans les documents, référence dans les scripts).</li></ol>",
         "<h2>2. Synthèse</h2>",
         "<table><tr><th>Réf.</th><th>Sévérité</th><th>Domaine</th><th>Verdict</th><th>Correction v2</th><th>Statut</th></tr>"]
    for ref, dom, s, _c, verdict, _v, _corr, _l in CONSTATS:
        statut = "Justifié" if verdict.startswith("Fondé, déjà") else "Corrigé"
        H.append(f"<tr><td class='id'>{ref}</td><td>{sev(s)}</td><td>{e(dom)}</td>"
                 f"<td class='{VERDICT[verdict]}'>{e(verdict)}</td><td>{v21(e(COURT[ref]))}</td><td><b>{statut}</b></td></tr>")
    H.append("</table>")
    H.append("<h2 class='saut'>3. Détail des constats</h2>")
    for ref, dom, s, constat, verdict, verif, corr, livs in CONSTATS:
        H.append(f"<div class='fiche'><h3>{ref} · {e(dom)} {sev(s)}</h3><dl>"
                 f"<dt>Constat</dt><dd>{e(constat)}</dd>"
                 f"<dt>Vérification</dt><dd><span class='{VERDICT[verdict]}'>{e(verdict)}.</span> {e(verif)}</dd>"
                 f"<dt>Correction</dt><dd>{v21(e(corr))}</dd>"
                 f"<dt>Livrables</dt><dd>{', '.join(LIBELLE[x] for x in livs)}</dd></dl></div>")
    H.append("<h2>4. Autres points du rapport</h2><table><tr><th>Point</th><th>Verdict</th><th>Traitement</th><th>Livrables</th></tr>")
    for pt, verdict, trait, livs in AUTRES:
        H.append(f"<tr><td><b>{e(pt)}</b></td><td class='{VERDICT[verdict]}'>{e(verdict)}</td><td>{e(trait)}</td>"
                 f"<td class='chemin'>{', '.join(LIBELLE[x] for x in livs) or '—'}</td></tr>")
    H.append("</table>")
    H.append("<h2>5. Écarts trouvés pendant la correction</h2><p>Absents du rapport d'audit, découverts en reprenant les sources :</p><ul>")
    H += [f"<li><b>{e(t)}</b> : {d}</li>" for t, d in trouves()]
    H.append("</ul>")
    H.append("<h2 class='saut'>6. Version 1 et version 2</h2>"
             "<p>Chiffres relus dans les archives des deux versions (<code>livrables/archives/</code>) ; la v2.1 est comparée aux deux "
             "en partie B, section 15.</p>"
             "<table><tr><th></th><th class='n'>v1 (auditée)</th><th class='n'>v2</th></tr>")
    H += [f"<tr><td>{a}</td><td class='n'>{b}</td><td class='n'><b>{c}</b></td></tr>"
          for a, b, c, _d in lignes_versions(vs) if a != "Secours long"]
    H.append("</table>")
    d = v2["ch"]["capex"] - v1["ch"]["capex"]
    kwh = 100 * (v2["en"]["energie"]["kwh"] - v1["en"]["energie"]["kwh"]) / v1["en"]["energie"]["kwh"]
    H.append(f"<p>Le CAPEX augmente de <b>{CH.euros(d)}</b> (+{N(100 * d / v1['ch']['capex'], 1)} %). La virtualisation et la correction du cluster NM "
             "économisent environ 18 k€ HT de serveurs, ce qui finance une partie des ajouts de sécurité : extinction automatique et protection "
             "contre l'eau (≈ 15 k€ HT), contrôleurs Wi-Fi physiques (12 k€ HT), modules 10G du Stormshield, sauvegarde hors ligne, kits de pile "
             f"oubliés en v1. La consommation électrique varie de {N(kwh, 0)} %. Le détail ligne à ligne est dans "
             "<code>livrables/archives/v2_2026-11-20/chiffrage/estimation_infra.md</code> (section « Écarts avec la version 1 »).</p>")
    H.append("<h3>Livrables mis à jour</h3><table><tr><th>Livrable</th><th>En vigueur (v2.1)</th><th>v2 archivée</th><th>v1 archivée</th></tr>")
    for lib, vig, arch in (("Plan d'adressage (point 05)", "livrables/plan_adressage/", "plan_adressage/"),
                           ("Architecture L2 (points 03, 06)", "livrables/architecture_l2/", "architecture_l2/"),
                           ("Architecture L3 (points 03, 05, 07)", "livrables/architecture_l3/", "architecture_l3/"),
                           ("Énergie et refroidissement (point 14)", f"livrables/{EN}/", f"{EN}/"),
                           ("Chiffrage (point 18)", "chiffrage/", "chiffrage/")):
        H.append(f"<tr><td>{lib}</td><td><code>{vig}</code></td><td><code>…/v2_2026-11-20/{arch}</code></td><td><code>…/v1_2026-11-15/{arch}</code></td></tr>")
    H.append("<tr><td>Schéma principal et sources du réseau</td><td><code>architecture/</code></td>"
             "<td><code>architecture/archives/v2_2026-11-20/</code></td><td><code>architecture/archives/v1_2026-11-15/</code></td></tr></table>")
    H.append("<h2>7. Préparation de la soutenance</h2><p>Les 14 questions pièges du rapport ont une réponse dans les documents en vigueur :</p>"
             "<table><tr><th>Q</th><th>Sujet</th><th>Où se trouve la réponse</th></tr>")
    H += [f"<tr><td>{q}</td><td>{e(s)}</td><td>{e(o)}</td></tr>" for q, s, o in QUESTIONS]
    H.append("</table>")
    H.append(f"<h2>8. Ce qui restait à faire le {DATE_AUDIT_1}</h2><table><tr><th>Reste à faire (v2)</th><th>Au {CH.DATE_VERSION} {CH.badge('v2.1')}</th></tr>")
    H += [f"<tr><td>{e(a)}</td><td>{e(b)}</td></tr>" for a, b in RESTE_V2]
    H.append("</table>")
    return H


def trouves():
    """Écarts trouvés pendant la correction de la v2 ; le premier renvoie au constat RES-01 de l'audit v2.1 et à son statut."""
    c = {x["id"]: x for x in lire(ICI / "constats_v21.json")["constats"]}
    res01 = c.get("RES-01", {}).get("statut", "ouvert")
    suite = ("corrigées en v2.1, et <code>verifier()</code> contrôle désormais chaque adresse d'hôte et de transit"
             if res01 == "traité" else "à corriger (statut du constat : " + e(res01) + ")")
    return [
        ("Adresses fixes des VLAN 401, 402 et des transits 1020 à 1090 hors de leur sous-réseau",
         "La v1 ajoutait la terminaison à l'adresse du réseau : le FortiGate du VLAN 401 (172.16.13.32/27) était noté 172.16.13.65, "
         "les iDRAC du VLAN 402 en 172.16.13.135-140. Corrigé en v2 dans <code>donnees.py</code> (terminaison absolue dans le /24). "
         f"La même erreur touchait les adresses des transits 1020 à 1090, vues par l'audit v2.1 (RES-01) : {suite}."),
        ("Kits de pile et cartes 4×1G absents du chiffrage", "Prévus par l'architecture L2, jamais chiffrés. Ajoutés (3 kits, une carte par nœud NM)."),
        ("Enregistreur vidéo et serveur de contrôle d'accès sans adresse", "Destinataires des flux IOT de la matrice, mais absents du plan. Ajoutés en 10.13.48.60 et .61."),
    ]


def partie_b(vs, C):
    constats = C["constats"]
    resp = C["responsables"]
    gravites = C["gravites"]
    audits = {a["id"]: a for a in C["audits"]}
    depot = [c for c in constats if not c["hors_depot"]]
    hors = [c for c in constats if c["hors_depot"]]
    st = Counter(c["statut"] for c in depot)
    en, ch = vs[2]["en"], vs[2]["ch"]
    bet = en.get("bet", {})
    ge = bet.get("groupe_electrogene", {})
    H = [f"<p class='partie saut'>Partie B · audit v2.1 du {C['date']} · version 2 → version 2.1 {CH.badge('v2.1')}</p>",
         "<h2 style='margin-top:2mm'>9. Méthode</h2>",
         f"<p>Le {C['date']}, avant de figer la v2.1, le dossier entier (commit <code>{e(C['commit_audite'])}</code> : points 01 à 05, 09, 14, 18 et 19) "
         f"a été relu par <b>{len(C['audits'])} audits menés en parallèle</b>, chacun en lecture seule sur son domaine. Chaque constat donne le fichier "
         "<b>source</b> à corriger et la ligne (les PDF et les HTML sont générés), la preuve, et la correction exacte « avant → après ». "
         "Les audits ont rejoué les scripts dans un dossier à part pour vérifier que les livrables suivis par git correspondent à leurs sources.</p>",
         "<table><tr><th>Audit</th><th>Périmètre</th><th>Méthode</th></tr>"]
    H += [f"<tr><td><b>{e(a['titre'])}</b><br><span class='chemin'>{e(a['prefixe'])}</span></td><td>{e(a['perimetre'])}</td><td>{e(a['methode'])}</td></tr>"
          for a in C["audits"]]
    H.append("</table>")
    H.append(f"<p>Deux travaux complètent ces audits : une <b>étude de bureau d'études</b> (BET) thermique et électrique des locaux techniques "
             f"({e(bet.get('reference', 'BET'))}, section 12) et une <b>intégration continue</b> qui rejoue la chaîne de génération et contrôle la cohérence "
             "du dépôt à chaque envoi (section 13). Les constats ont été corrigés par domaine (réseau et sécurité ; câblage, chiffrage et énergie ; "
             "juridique ; documentation transverse), selon six décisions communes (section 14).</p>")
    # 10. Synthèse chiffrée
    bilan = []
    for aid, a in audits.items():
        cs = [c for c in constats if c["audit"] == aid]
        dd = [c for c in cs if not c["hors_depot"]]
        nh, nb = len(cs) - len(dd), sum(1 for c in dd if c["gravite"] == "bloquant")
        total = len(cs) if a.get("hors_depot_au_total") else len(dd)
        txt = f"{e(a['titre'].lower())} <b>{total}</b> constats"
        txt += f" dont {nb} bloquant{'s' if nb > 1 else ''}" if nb else ""
        txt += (f", dont {nh} hors dépôt" if a.get("hors_depot_au_total") else f" (plus {nh} hors dépôt)") if nh else ""
        bilan.append(txt)
    H.append(f"<h2>10. Synthèse chiffrée</h2><p>Bilan par audit : {' ; '.join(bilan)}.</p>"
             "<table><tr><th>Audit</th><th class='n'>Dans le dépôt</th>"
             + "".join(f"<th class='n'>{g}s</th>" for g in gravites) + "<th class='n'>Hors dépôt</th><th class='n'>Traités</th><th class='n'>Autres</th></tr>")
    for aid, a in audits.items():
        cs = [c for c in constats if c["audit"] == aid]
        dd = [c for c in cs if not c["hors_depot"]]
        g = Counter(c["gravite"] for c in dd)
        tr = sum(1 for c in dd if c["statut"] == "traité")
        H.append(f"<tr><td><b>{e(a['titre'])}</b></td><td class='n'>{len(dd)}</td>"
                 + "".join(f"<td class='n'>{g.get(x, 0) or '—'}</td>" for x in gravites)
                 + f"<td class='n'>{len(cs) - len(dd) or '—'}</td><td class='n'>{tr}</td><td class='n'>{len(dd) - tr or '—'}</td></tr>")
    g = Counter(c["gravite"] for c in depot)
    H.append(f"<tr><td><b>Total</b></td><td class='n'><b>{len(depot)}</b></td>" + "".join(f"<td class='n'><b>{g.get(x, 0)}</b></td>" for x in gravites)
             + f"<td class='n'><b>{len(hors)}</b></td><td class='n'><b>{st.get('traité', 0)}</b></td><td class='n'><b>{len(depot) - st.get('traité', 0)}</b></td></tr></table>")
    H.append("<p class='sous'>Les colonnes de gravité, « Traités » et « Autres » comptent les constats sur les fichiers du dépôt. "
             "Hors dépôt : le travail non versionné du checkout principal (maquette du point 06, document de suivi du 19/11). "
             f"Statuts : {' ; '.join(f'<b>{e(k)}</b> : {e(v)}' for k, v in C['statuts'].items())}.</p>")
    H.append("<h3>Par équipe de correction</h3><table><tr><th>Équipe</th><th class='n'>Constats</th><th class='n'>Traités</th><th>Autres statuts</th></tr>")
    for k, lib in resp.items():
        if k == "hors_depot":
            continue
        cs = [c for c in depot if k in c["responsables"]]
        if not cs:
            continue
        autres = Counter(c["statut"] for c in cs if c["statut"] != "traité")
        H.append(f"<tr><td>{e(lib)}</td><td class='n'>{len(cs)}</td><td class='n'>{sum(1 for c in cs if c['statut'] == 'traité')}</td>"
                 f"<td>{', '.join(f'{n} {e(s)}' for s, n in autres.items()) or '—'}</td></tr>")
    H.append("</table><p class='sous'>Un constat qui touche les fichiers de plusieurs équipes est compté pour chacune.</p>")
    # 11. Bloquants et majeurs
    graves = [c for c in depot if c["gravite"] in ("bloquant", "majeur")]
    graves.sort(key=lambda c: (gravites.index(c["gravite"]), list(audits).index(c["audit"])))
    H.append(f"<h2>11. Constats bloquants et majeurs ({len(graves)})</h2>"
             "<p>Les constats bloquants empêchent un service de fonctionner tel qu'il est décrit ; les majeurs sont visibles du client ou du jury "
             "(incohérence entre documents, état dépassé, outil cassé). Le traitement résume la correction faite dans les sources ; la liste "
             "complète, avec les fichiers visés, est dans <code>architecture/audit/constats_v21.json</code>.</p>"
             "<table class='serre'><tr><th>Constat</th><th>Gravité</th><th style='width:30%'>Ce que l'audit a trouvé</th><th>Traitement v2.1</th><th>Statut</th></tr>")
    for c in graves:
        trait = c["traitement"] or "Correction proposée par l'audit appliquée."
        H.append(f"<tr><td class='id'>{c['id']}</td><td>{sev(c['gravite'])}</td><td>{e(c['titre'])}</td>"
                 f"<td>{e(trait)} <span class='chemin'>({e(', '.join(resp[r] for r in c['responsables']))})</span></td><td>{statut_html(c['statut'])}</td></tr>")
    H.append("</table>")
    hg = [c for c in hors if c["gravite"] in ("bloquant", "majeur")]
    if hg:
        H.append("<p><b>Hors dépôt</b> (à corriger quand ces fichiers entreront dans le dépôt) : "
                 + " ; ".join(f"<span class='id'>{c['id']}</span> {e(c['titre'])}" for c in hg) + ".</p>")
    H += section_bet(en, ch, bet, ge)
    H += section_ci()
    # 14. Décisions
    H.append("<h2>14. Décisions communes D1 à D6</h2><p>Prises par la direction de projet le "
             f"{C['date']} pour trancher les points soulevés par plusieurs audits ; elles s'imposent à tous les documents.</p>"
             "<table><tr><th>Décision</th><th>Contenu</th><th>Constats réglés</th></tr>")
    H += [f"<tr><td class='id'>{d['id']}<br><span style='font-family:var(--sans);font-weight:600'>{e(d['titre'])}</span></td><td>{e(d['resume'])}</td>"
          f"<td class='chemin'>{', '.join(d['constats'])}</td></tr>" for d in C["decisions"]]
    H.append("</table>")
    # 15. Chiffres clés
    H.append("<h2 class='saut'>15. Chiffres clés des trois versions</h2>"
             "<p>v1 et v2 relues dans leurs archives, v2.1 dans <code>chiffrage/estimation.json</code> et "
             f"<code>livrables/{EN}/resume.json</code>.</p>"
             "<table><tr><th></th><th class='n'>v1 (13/11/2026)</th><th class='n'>v2 (15/11/2026)</th>"
             f"<th class='n'>{CH.VERSION} ({CH.DATE_VERSION})</th></tr>")
    H += [f"<tr><td>{a}</td><td class='n'>{b}</td><td class='n'>{c}</td><td class='n'><b>{d}</b></td></tr>" for a, b, c, d in lignes_versions(vs)]
    H.append("</table>")
    v2c, v21c = vs[1]["ch"], vs[2]["ch"]
    dcap = v21c["capex"] - v2c["capex"]
    cats = sorted(((k, v - v2c["par_categorie"].get(k, 0)) for k, v in v21c["par_categorie"].items()), key=lambda x: -abs(x[1]))
    cats = [(k, d) for k, d in cats if d] + [(k, -v) for k, v in v2c["par_categorie"].items() if k not in v21c["par_categorie"]]
    H.append(f"<p>De la v2 à la v2.1, le CAPEX varie de <b>{'+' if dcap >= 0 else ''}{CH.euros(dcap)}</b> "
             f"({'+' if dcap >= 0 else ''}{N(100 * dcap / v2c['capex'], 1)} %), aléas compris. Écarts du sous-total par poste : "
             + ", ".join(f"{e(k)} {'+' if d >= 0 else ''}{CH.euros(d)}" for k, d in cats) + ".</p>")
    # 16. Points ouverts
    types = []
    for p in C["points_ouverts"]:
        if p["type"] not in types:
            types.append(p["type"])
    H.append(f"<h2>16. Points ouverts ({len(C['points_ouverts'])})</h2><p>Ce qui ne dépend pas de l'équipe seule (vérification sur site, réponse du client, "
             "devis) ou qui demande encore un choix. Ils ne bloquent pas la v2.1 : chaque document en vigueur les signale là où ils comptent.</p>"
             "<table><tr><th>Nature</th><th>Point</th><th>Origine</th></tr>")
    for t in types:
        for p in (x for x in C["points_ouverts"] if x["type"] == t):
            H.append(f"<tr><td style='white-space:nowrap'>{e(t)}</td><td>{e(p['sujet'])}</td><td class='chemin'>{e(p['source'])}</td></tr>")
    H.append("</table>")
    # Annexe
    autres = [c for c in constats if c["gravite"] not in ("bloquant", "majeur") or c["hors_depot"]]
    H.append(f"<h2 class='saut'>Annexe · Constats mineurs, coquilles et hors dépôt ({len(autres)})</h2>"
             "<table class='serre'><tr><th>Constat</th><th>Gravité</th><th>Titre</th><th>Équipe</th><th>Statut</th></tr>")
    for c in autres:
        H.append(f"<tr><td class='id'>{c['id']}</td><td>{sev(c['gravite'])}</td><td>{e(c['titre'])}"
                 + (f"<br><span class='chemin'>{e(c['traitement'])}</span>" if c["traitement"] else "")
                 + f"</td><td class='chemin'>{e(', '.join(resp[r] for r in c['responsables']))}</td><td>{statut_html(c['statut'])}</td></tr>")
    H.append("</table>")
    return H


def section_bet(en, ch, bet, ge):
    if not bet:
        return ["<h2>12. Bureau d'études et groupe électrogène</h2><p>Étude BET absente de <code>resume.json</code>.</p>"]
    v2 = en.get("v2", {})
    ver = bet.get("verifications", {})
    renf = [x for x in bet.get("locaux", []) if x.get("verdict") != "conforme"]
    lignes_ge = [x for x in en.get("capex_nouveaux", []) if x["categorie"] == "Énergie / secours"]
    opex_ge = [o for o in en.get("opex", []) if "groupe" in o["poste"].lower()]
    s = bet.get("salle", {})
    H = ["<h2 class='saut'>12. Bureau d'études (BET) et groupe électrogène</h2>",
         f"<p>Le BET ({e(bet.get('reference', ''))}, <code>livrables/{EN}/bet_locaux_techniques.pdf</code>) a repris la salle serveur, les "
         f"{len(bet.get('locaux', []))} locaux techniques, le tableau informatique, le TGBT et le secours électrique, à partir de l'inventaire du chiffrage "
         f"et du plan de câblage. Sur {ver.get('total', '?')} vérifications : <b>{ver.get('ok', '?')} conformes</b> (corrections v2.1 comprises), "
         f"{ver.get('a_verifier', '?')} à vérifier sur site, {ver.get('nok', '?')} non conforme.</p>",
         "<div class='note'><b>Verdict : l'infrastructure énergétique tient, après les corrections de la v2.1.</b> Onduleurs, climatisation de la "
         "salle serveur et circuits de la v2 étaient bien dimensionnés. Trois points ne tenaient pas ; ils sont corrigés dans les sources et dans le "
         "chiffrage.</div>", "<table><tr><th>Correction</th><th>v2 (15/11/2026)</th><th>v2.1 (20/11/2026)</th></tr>"]
    H.append("<tr><td><b>1. Ventilation des locaux techniques en été</b></td><td>"
             + "<br>".join(f"{e(x['local'])} : {e(x['solution_v2'])}" for x in renf) + "</td><td>"
             + "<br>".join(f"{e(x['local'])} : <b>{e(x['solution'])}</b>, {N(x['t_ete'], 1)} °C au plus chaud" for x in renf) + "</td></tr>")
    H.append("<tr><td><b>2. Pertes des onduleurs à faible charge et auxiliaires de la salle</b></td>"
             f"<td>rendement fixe, auxiliaires non comptés : PUE {N(v2.get('pue', 0), 2)}, {N(v2.get('kwh', 0))} kWh/an</td>"
             f"<td>pertes réelles en 2N et auxiliaires comptés : PUE {N(en['energie']['pue'], 2)}, {N(en['energie']['kwh'])} kWh/an</td></tr>")
    H.append("<tr><td><b>3. Secours long</b></td><td>aucun : arrêt ordonné de toute la salle après quelques minutes de coupure</td>"
             f"<td>groupe électrogène {ge.get('esp_kva')} kVA ESP et inverseur automatique ; arrêt ordonné seulement si le groupe n'a pas repris "
             f"à T0 + {ge.get('arret_nut_si_ge_absent_min')} min</td></tr></table>")
    if s:
        H.append(f"<p>Sans aucun froid, la salle atteindrait 35 °C en {N(s['t35_min'], 1)} min et 40 °C en {N(s['t40_min'], 1)} min : c'est pourquoi "
                 "les climatiseurs restent secourus par les onduleurs puis par le groupe.</p>")
    H.append(f"<h3>Groupe électrogène {CH.badge('v2.1')}</h3>"
             "<p>Le client a confirmé le 20/11/2026 que le site n'a pas de groupe électrogène : un groupe dédié est donc ajouté au lot énergie.</p><ul>"
             f"<li>Puissance : <b>{ge.get('esp_kva')} kVA en secours (ESP)</b>, {ge.get('prp_kva')} kVA en continu (PRP), pour un besoin de "
             f"{N(ge.get('besoin_kva', 0), 1)} kVA (charge de {ge.get('charge_moy_pct')} % en moyenne, {ge.get('charge_max_pct')} % au plus).</li>"
             f"<li>Autonomie : cuve double paroi de {ge.get('cuve_l')} l, soit <b>{ge.get('autonomie_h')} h</b> à charge moyenne et "
             f"{ge.get('autonomie_75_h')} h à 75 % de la PRP ({N(ge.get('conso_75_lh', 0), 1)} l/h).</li>"
             f"<li>Arrêt ordonné : NUT n'arrête les serveurs que si l'onduleur est encore sur batterie à T0 + {ge.get('arret_nut_si_ge_absent_min')} min "
             f"(groupe absent) ; la séquence se termine à T0 + {ge.get('fin_arret_min')} min, dans l'autonomie de l'onduleur restant "
             f"({en['onduleurs']['autonomie_degrade']} min).</li>"
             f"<li>Puissance à réserver au TGBT : <b>{bet.get('reserve_tgbt_kva')} kVA</b> (pointe du lot : {N(bet.get('puissance_max_kva', 0), 1)} kVA), "
             "à vérifier sur site avec le régime de neutre et l'emplacement exact du groupe.</li></ul>")
    if lignes_ge:
        H.append("<table><tr><th>Investissement</th><th>Où</th><th class='n'>Total HT</th></tr>")
        H += [f"<tr><td>{e(x['solution'])}</td><td>{e(x['schema'])}</td><td class='n'>{CH.euros(x['total_ht'], ht=False)}</td></tr>" for x in lignes_ge]
        H.append(f"<tr><td colspan='2'><b>Total du secours long</b></td><td class='n'><b>{CH.euros(en.get('capex_groupe_electrogene', sum(x['total_ht'] for x in lignes_ge)), ht=False)}</b></td></tr>")
        if opex_ge:
            H += [f"<tr><td>{e(o['poste'])} <span class='chemin'>{e(o['detail'])}</span></td><td>par an</td><td class='n'>{CH.euros(o['montant'], ht=False)}</td></tr>" for o in opex_ge]
        H.append("</table>")
    H.append(f"<p>Le lot énergie passe de {CH.euros(v2.get('capex_lot', 0))} (v2) à <b>{CH.euros(en['capex_lot'])}</b> d'investissement et de "
             f"{CH.euros(v2.get('opex_total', 0))} à <b>{CH.euros(en['opex_total'])}</b> par an ; il est repris tel quel par le chiffrage "
             f"(CAPEX total {CH.euros(ch['capex'])}). Le CCTP lot 5 « Énergie et locaux techniques » (RLI-CCTP-005) le décrit pour la consultation.</p>")
    return H


def section_ci():
    controles, etapes = ci()
    return ["<h2>13. Intégration continue</h2>",
            "<p>L'audit a montré que plusieurs livrables n'étaient plus à jour avec leurs sources (copies du site en v1, modèle de présentation périmé, "
            "chaîne de génération dans le mauvais ordre). La v2.1 ajoute une intégration continue (<code>.github/workflows/ci.yml</code>, "
            "<code>outils/ci/</code>) qui tourne à chaque envoi et à chaque pull request, en trois tâches parallèles :</p><ul>"
            "<li><b>Python</b> : compilation de tous les scripts et <code>ruff</code> (noms indéfinis, imports et variables inutiles, f-strings vides).</li>"
            f"<li><b>Cohérence</b> : <code>verifier_coherence.py</code>, {len(controles)} contrôles : "
            + "; ".join(f"{e(t[0].lower() + t[1:])}" for _n, t in controles) + ".</li>"
            f"<li><b>Génération</b> : la chaîne complète <code>outils/ci/generer_tout.sh</code> ({len(etapes)} scripts dans l'ordre des dépendances, "
            "du plan de câblage à ce document), puis <code>verifier_a_jour.py</code> : chaque livrable texte suivi par git doit être identique à "
            "ce que produisent les sources.</li></ul>"
            "<p>La chaîne <code>bash outils/ci/generer_tout.sh</code> est désormais la seule commande de génération de référence (décision D6).</p>"]


def comptes(C):
    """Total annoncé par les audits (l'audit de forme compte ses constats hors dépôt, l'audit réseau non), constats du dépôt, traités."""
    cs = C["constats"]
    depot = [c for c in cs if not c["hors_depot"]]
    au_total = {a["id"] for a in C["audits"] if a.get("hors_depot_au_total")}
    annonces = sum(1 for c in cs if not c["hors_depot"] or c["audit"] in au_total)
    return {"annonces": annonces, "en_plus": len(cs) - annonces, "depot": len(depot),
            "traites": sum(1 for c in depot if c["statut"] == "traité"),
            "gravite": Counter(c["gravite"] for c in depot)}


def total_txt(k):
    return f"{k['annonces']} constats" + (f", plus {k['en_plus']} sur la maquette hors dépôt" if k["en_plus"] else "")


def document(C):
    vs = versions()
    k = comptes(C)
    nb_bloq = k["gravite"].get("bloquant", 0)
    tr, depot = k["traites"], range(k["depot"])
    corps = ["<div class='cles'>",
             f"<div class='cle'><b>9 constats</b>de l'audit du {DATE_AUDIT_1} (16,9 / 20), tous traités en v2</div>",
             f"<div class='cle'><b>{k['annonces']} constats</b>des {len(C['audits'])} audits v2.1, dont {k['depot']} sur les fichiers du dépôt</div>",
             f"<div class='cle'><b>{tr} / {len(depot)}</b>constats v2.1 du dépôt traités ({nb_bloq} bloquants)</div>",
             f"<div class='cle'><b>v1 → v2 → {CH.VERSION}</b>v1 et v2 archivées, {CH.VERSION} en vigueur</div></div>"]
    corps += partie_a(vs)
    corps += partie_b(vs, C)
    corps.append(CH.bloc_suivi(REF, changements="Partie B ajoutée : audit v2.1 du 20/11/2026 (quatre audits, BET, groupe électrogène, CI, "
                                                "décisions D1 à D6, points ouverts) ; partie A complétée (SYS-03, transits, reste à faire) ; charte commune."))
    return CH.page(titre="Traitement des audits de l'infrastructure", titre_court="Traitement des audits", ref=REF, points=POINTS, dossier=OUT,
                   chapo=f"Les deux audits du dossier et ce que nous en avons fait : l'audit du {DATE_AUDIT_1} (version 1, 9 constats), qui a produit "
                         f"la version 2, puis l'audit v2.1 du {C['date']} ({len(C['audits'])} audits en parallèle, {total_txt(k)}), qui a "
                         "produit la version 2.1. Chaque constat est vérifié dans les sources, corrigé ou justifié, et tracé.",
                   corps="\n".join(corps), css_extra=CSS_PROPRE)


def readme(C):
    vs = versions()
    k = comptes(C)
    g = k["gravite"]
    lignes = lignes_versions(vs, md=True)
    return "\n".join([
        "# Audits de l'infrastructure (15/11/2026 et 20/11/2026)", "<!-- onglet: Audit -->", "",
        f"Les deux audits du dossier et leur traitement : l'audit du {DATE_AUDIT_1} (version 1 : 16,9 / 20, 9 constats), qui a produit la version 2, "
        f"puis l'audit v2.1 du {C['date']} ({len(C['audits'])} audits en parallèle, {total_txt(k)}), qui a produit la version 2.1.", "",
        "| Document | Réf. | Contenu |", "|---|---|---|",
        f"| **[traitement_audit.pdf](traitement_audit.pdf)** | {REF} | Partie A : vérification et correction des 9 constats du 15/11/2026, livrables "
        "touchés, réponses aux 14 questions du jury. Partie B : audit v2.1 (méthode, constats par audit, bloquants et majeurs avec leur traitement, "
        "BET et groupe électrogène, intégration continue, décisions D1 à D6, chiffres des trois versions, points ouverts) |",
        "| **[rapport_audit_2026-11-15.pdf](rapport_audit_2026-11-15.pdf)** | — | Rapport d'audit d'origine du 15/11/2026, texte figé (aussi en `.html`) |",
        f"| [`constats_v21.json`](../../architecture/audit/constats_v21.json) | — | Les {len(C['constats'])} constats de l'audit v2.1, hors dépôt compris "
        f"({g.get('bloquant', 0)} bloquants et {g.get('majeur', 0)} majeurs dans le dépôt), leur traitement et leur statut ({k['traites']} traités sur "
        f"{k['depot']} dans le dépôt), les décisions et "
        "les points ouverts : source de la partie B |", "",
        "## Versions de l'infrastructure", "",
        "| Version | Date | Ce qui la définit | Où |", "|---|---|---|---|",
        "| v1 | 13/11/2026 | Première version, auditée le 15/11/2026 | `livrables/archives/v1_2026-11-15/`, `architecture/archives/v1_2026-11-15/` |",
        "| v2 | 15/11/2026 | Les 9 constats de l'audit du 15/11 traités (repères « v2 » dans les documents) | `livrables/archives/v2_2026-11-20/`, "
        "`architecture/archives/v2_2026-11-20/` |",
        f"| **{CH.VERSION}** | {CH.DATE_VERSION} | Audit v2.1 traité, BET des locaux techniques, groupe électrogène, charte commune, intégration continue "
        "(repères « v2.1 ») | livrables en vigueur |", "",
        f"| Indicateur (montants HT) | v1 (13/11/2026) | v2 (15/11/2026) | {CH.VERSION} ({CH.DATE_VERSION}) |", "|---|---:|---:|---:|",
        *[f"| {a} | {b} | {c} | {d} |" for a, b, c, d in lignes], "",
        "v1 et v2 sont relues dans leurs archives (`livrables/archives/`), la v2.1 dans `chiffrage/estimation.json` et "
        "`livrables/energie_refroidissement/resume.json`.", "",
        f"**Version {CH.VERSION[1:]} — {CH.DATE_VERSION}** : partie B (audit v2.1) ajoutée au traitement, constat SYS-03 complété (groupe électrogène "
        "intégré), mise en page de la charte commune. Version précédente du traitement : dans git (tag `v2`).", "",
        "Régénérer : `python3 architecture/audit/traitement_audit.py` (sources : `architecture/audit/constats_v21.json` pour les constats v2.1 et "
        "leur statut, les archives v1 et v2, `chiffrage/estimation.json`, `livrables/energie_refroidissement/resume.json`). Chaîne complète : "
        "`bash outils/ci/generer_tout.sh`. Le rapport d'audit d'origine et le script qui l'a produit (`generer_rapport_audit.py`) sont dans "
        "`architecture/audit/`.", ""])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "html"):
        src = ICI / f"Rapport_Audit_Infrastructure_Marseille.{ext}"
        if src.exists():
            shutil.copyfile(src, OUT / f"rapport_audit_2026-11-15.{ext}")
    C = lire(ICI / "constats_v21.json")
    inconnus = {c["statut"] for c in C["constats"]} - set(C["statuts"])
    assert not inconnus, f"statut(s) inconnu(s) dans constats_v21.json : {inconnus}"
    page = OUT / "traitement_audit.html"
    CH.ecrire_et_imprimer(document(C), page, OUT / "traitement_audit.pdf")
    (OUT / "README.md").write_text(readme(C), encoding="utf-8")
    print(f"  {page.relative_to(ROOT)} -> .pdf, README.md ({len(C['constats'])} constats v2.1)")


if __name__ == "__main__":
    main()
