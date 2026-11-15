#!/usr/bin/env python3
"""Traitement de l'audit du 15/11/2026 : constats, vérification, corrections de la v2, livrables touchés.

Usage : python3 architecture/audit/traitement_audit.py
        (après architecture/reseau/build.py, energie/energie.py et chiffrage/estimation.py : les chiffres sont relus)
Entrées : rapport d'audit (ce dossier), livrables v2, archives v1 (livrables/archives/v1_2026-11-15/)
Sorties : livrables/audit/traitement_audit.html (+ .pdf), README.md, copie du rapport d'audit
"""
import datetime
import html
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ICI = Path(__file__).resolve().parent
ROOT = ICI.parent.parent
sys.path.insert(0, str(ROOT / "architecture" / "reseau"))
import donnees as D  # noqa: E402

OUT = ROOT / "livrables" / "audit"
V1 = ROOT / "livrables" / "archives" / "v1_2026-11-15"
CSS = (ROOT / "cablage" / "document.py").read_text(encoding="utf-8").split('CSS = """', 1)[1].split('"""', 1)[0] + """
.badge { display: inline-block; padding: 0 1.5mm; border-radius: 1mm; color: #fff; font-size: 7.2pt; font-weight: bold; white-space: nowrap; }
.crit { background: #B3261E; } .maj { background: #A85A07; } .min { background: #6C6861; } .q { background: #1F4E8C; }
.fonde { color: #1D7A4E; font-weight: bold; } .partiel { color: #A85A07; font-weight: bold; } .rejet { color: #B3261E; font-weight: bold; }
.fiche { border: 1px solid #DEDAD1; border-radius: 2mm; padding: 2.5mm 3.5mm; margin: 3mm 0; page-break-inside: avoid; }
.fiche h3 { margin: 0 0 1.5mm; }
.fiche dl { display: grid; grid-template-columns: 30mm 1fr; gap: 1mm 3mm; margin: 0; }
.fiche dt { font-weight: bold; color: #3A3833; } .fiche dd { margin: 0; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 7.6pt; }
"""
e = html.escape
eur = lambda v: f"{v:,.0f} €".replace(",", " ")
num = lambda v: f"{v:,.0f}".replace(",", " ")
SEV = {"Critique": "crit", "Majeur": "maj", "Mineur": "min", "Question": "q"}
VERDICT = {"Fondé": "fonde", "Partiellement fondé": "partiel", "Fondé, déjà justifié en v1": "partiel", "Non retenu": "rejet"}

ADR, L2, L3 = "plan_adressage", "architecture_l2", "architecture_l3"
EN, CH, SCH = "energie_refroidissement", "chiffrage", "schéma principal"

# (réf, domaine, sévérité, constat de l'audit, verdict, vérification, correction v2, livrables)
CONSTATS = [
    ("NET-01", "Wi-Fi et mobilité", "Critique",
     "Coupure des sessions lors de l'itinérance Wi-Fi entre étages : FlexConnect en commutation locale, VLAN 115 au RDC et 215 au 1er étage.",
     "Fondé",
     "Exact. La v1 l'assumait (« revers assumé », architecture L2 §1) mais sans le résoudre. Le même document montrait en rouge "
     "le pool WIFI-ETU-B1 à 94 % (960 clients pour 1 022 adresses).",
     "Bornes en mode local : le trafic remonte à deux contrôleurs physiques Catalyst 9800-L-F en HA SSO, raccordés au cœur en 2×10G. "
     "Trois VLAN Wi-Fi pour tout le bâtiment, avec passerelle sur le cœur : 514 WIFI-PERS (/22), 515 WIFI-ETU (/20, 37 % d'occupation, "
     "bail 2 h) et 530 WIFI-INVITES (/22, bail 1 h). Un client garde son adresse partout ; itinérance 802.11r/OKC. La VM 9800-CL est retirée.",
     [ADR, L2, L3, SCH, CH, EN]),
    ("SEC-01", "Pare-feu et débit", "Critique",
     "Goulet d'étranglement du Stormshield SN710 (inspection applicative) face aux flux inter-VRF à 10/40G ; transit par la pile C9200L EL-SW.",
     "Partiellement fondé",
     "Le chemin par EL-SW (petits tampons) était réel. Le chiffre de 2,5 Gb/s avancé par l'audit n'est pas sourcé. Surtout, le plus gros "
     "flux inter-VRF de la v1 était la sauvegarde (hyperviseurs NM en VRF ADM vers DT-BKP1 en VRF SRV), que l'audit n'identifie pas.",
     "Stormshield raccordé directement au cœur (Po2/Po3, 2×10G MEC par nœud, module 10G chiffré). EL-SW ne porte plus que la gestion. "
     "PBS déplacé dans la VRF ADM (VLAN 909) : les sauvegardes NM et DT ne traversent plus le pare-feu. Politique d'inspection par flux "
     "(IPS complet vers l'AD, filtrage à états seul pour les flux chiffrés de sauvegarde de la DMZ). Seuil de supervision à 60 %, "
     "évolution possible vers un SN910.",
     [L2, L3, ADR, SCH, CH]),
    ("SYS-01", "Cohérence documentaire", "Majeur",
     "Le chiffrage prévoit 3 nœuds Proxmox avec Ceph, l'architecture L2 2 nœuds en ZFS répliqué + QDevice ; témoin non chiffré.",
     "Fondé",
     "Exact. La v1 le signalait elle-même dans une note de l'architecture L2, sans reporter la correction dans le chiffrage. "
     "Il manquait aussi la carte 4×1G par nœud et les kits de pile C9200L.",
     "Chiffrage aligné : 2 nœuds R660xs (ZFS, carte 4×1G), NM-WITNESS chiffré, 3 kits de pile, souscription Proxmox recalculée par socket.",
     [CH, L2]),
    ("SYS-02", "Dimensionnement", "Majeur",
     "16 serveurs physiques dont 12 serveurs 1U mono-rôle en DMZ et au datacenter (37,8 k€ de serveurs).",
     "Fondé",
     "Exact (6 Dell R260 + 6 Dell R360). L'audit parle de « 16 serveurs Windows » dans la question Q13 : seuls 6 étaient sous Windows. "
     "Le gain réel sur les serveurs est de 18,1 k€, pas de 20 k€.",
     "Deux clusters Proxmox séparés. Cluster DT (DT-PVE1/2, tier 0) : VM AD, NPS, DHCP. Cluster DMZ (DM-PVE1/2 + DM-WITNESS) : VM Caddy ×2, "
     "DNS public ×2 (le DNS public devient redondant), web, messagerie, applicatif. Une VM de la DMZ ne partage jamais un hyperviseur "
     "avec l'AD. On passe de 16 à 9 serveurs physiques.",
     [L2, ADR, SCH, CH, EN]),
    ("SEC-02", "Active Directory", "Majeur",
     "Contrôleurs de domaine (tier 0) dans le même VLAN 300 que les serveurs DHCP et NPS (tier 1) : non conforme au guide ANSSI PA-099.",
     "Fondé",
     "Exact : DT-AD1/2 en 10.13.48.11-12, VLAN 300, passerelle sur le cœur. Le routage entre serveurs ne passait par aucun filtrage.",
     "VLAN 310 SRV-T0 (10.13.52.0/27, 2001:660:5402:4310::/64). Sa passerelle est le Stormshield, pas le cœur : tout flux vers un "
     "contrôleur de domaine est filtré, même depuis le VLAN 300. Pas d'accès Internet pour les DC. Hyperviseurs DT, PBS et iDRAC "
     "associés traités comme tier 0 : hors domaine, rôle Teleport dédié.",
     [ADR, L2, L3, SCH]),
    ("SEC-03", "Sauvegarde et rançongiciel", "Majeur",
     "Pas d'immuabilité (S3 Object Lock en mode conformité) ni de copie hors ligne des sauvegardes PBS.",
     "Fondé",
     "Exact. Le référentiel ANSSI du projet (BP-100) le notait déjà comme manque.",
     "Règle 3-2-1-1-0 : PBS hors domaine avec comptes locaux et MFA ; jetons API des hyperviseurs limités à l'écriture (pas de suppression) ; "
     "datastore amovible sur 3 disques en rotation hebdomadaire (un hors site, coffre ignifuge) ; copie externalisée en mode S3 Object Lock "
     "conformité chez un hébergeur SecNumCloud ; tests de restauration.",
     [ADR, L2, L3, CH]),
    ("SYS-03", "Salle en sous-sol", "Majeur",
     "Salle serveur au sous-sol sans plancher surélevé, batardeau, extinction automatique ni groupe électrogène.",
     "Fondé",
     "Exact. Ces protections avaient été chiffrées en option et écartées en v1. Décision de l'équipe (15/11/2026) : intégrer la protection "
     "contre l'eau et l'extinction ; le groupe électrogène reste une option à valider avec le campus.",
     "Plancher technique surélevé de 30 cm, batardeau à la porte, clapet anti-retour, câble de détection de fuite ; détection VESDA et extinction "
     "automatique au gaz inerte IG-541 ; arrêt ordonné sur batterie par NUT (serveur sur NM-WITNESS), autonomie portée à 33 min avec un seul "
     "onduleur (pack batterie).",
     [EN, CH]),
    ("NET-02", "Cœur et distribution", "Mineur",
     "4 commutateurs C9500 de distribution dans la même baie que le cœur au lieu d'un cœur replié (38 k€, 640 W).",
     "Fondé, déjà justifié en v1",
     "La v1 étudiait déjà cette variante (architecture L2 §1, chiffrage, énergie) et l'écartait : le cahier des charges impose trois couches. "
     "L'audit recommande lui-même de « l'assumer ».",
     "Pas de changement d'architecture. La variante cœur replié est présentée comme étudiée et chiffrée (sur 2 × C9500-48Y4C) dans le chiffrage et "
     "dans le document énergie.",
     [L2, CH, EN]),
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
    ("RTO de plus de 44 h depuis le cloud", "Fondé", "La copie hors ligne (disque amovible) permet une restauration locale à la vitesse d'un disque. Le cloud devient le dernier recours. Un PBS croisé avec le site jumeau est une piste du point 15.", [L3, CH]),
    ("Inspection TLS absente (Q7)", "Fondé", "Inspection sur le FortiGate pour les postes gérés uniquement, avec liste d'exclusion (banque, santé, administrations) et cadre légal (charte, DPIA). Pas de déchiffrement sur les appareils personnels.", [L3]),
    ("Asymétrie BGP (Q4)", "Fondé", "Annonce conditionnelle du /24 vers le FAI 2 (seulement si la route du FAI 1 disparaît), iBGP entre les routeurs, BFD vers les opérateurs. "
     "La solution proposée par l'audit (« set asymroute enable ») est écartée : elle désactive le contrôle d'état du FortiGate.", [L3, ADR, SCH]),
    ("PMTUD et MTU (plan d'actions)", "Partiellement fondé", "Les grandes trames ne servaient déjà que sur les liens d'infrastructure. Ajouts : ICMPv4 3/4 et ICMPv6 type 2 autorisés explicitement, MSS ajusté sur les tunnels.", [L3]),
    ("MAB des caméras et badgeuses (Q10)", "Fondé", "802.1X EAP-TLS quand l'équipement le permet ; sinon MAB avec ACL téléchargée par RADIUS (seul le serveur métier est joignable) ; coupure du port à la première violation.", [L2, L3]),
    ("Extinction ordonnée (Q13)", "Fondé", "Séquence NUT décrite et chiffrée dans le document énergie ; l'autonomie visée passe de 10 à 20 min pour la couvrir.", [EN]),
    ("Pool Wi-Fi étudiants à 94 %", "Fondé", "Voir NET-01 : /20 à 37 % et bail de 2 h.", [ADR]),
    ("Fuite de routes entre VRF sur le cœur (proposée en Q3)", "Non retenu", "Faire des fuites de routes entre VRF sur le cœur supprimerait le principe « aucune route entre VRF » : on règle le débit par le raccordement direct du pare-feu et le déplacement des sauvegardes.", []),
]

# Constats trouvés pendant la correction (absents du rapport)
TROUVES = [
    ("Adresses fixes des VLAN 401 et 402 hors de leur sous-réseau",
     "La v1 ajoutait la terminaison à l'adresse du réseau : le FortiGate du VLAN 401 (172.16.13.32/27) était noté 172.16.13.65, "
     "les iDRAC du VLAN 402 en 172.16.13.135-140. Corrigé dans donnees.py (terminaison absolue dans le /24)."),
    ("Kits de pile et cartes 4×1G absents du chiffrage", "Prévus par l'architecture L2, jamais chiffrés. Ajoutés (3 kits, une carte par nœud NM)."),
    ("Enregistreur vidéo et serveur de contrôle d'accès sans adresse", "Destinataires des flux IOT de la matrice, mais absents du plan. Ajoutés en 10.13.48.60 et .61."),
]

QUESTIONS = [
    ("1", "Itinérance Wi-Fi et rupture de session", "Architecture L2 §1 et §9 (mode local, WLC HA SSO)"),
    ("2", "4 C9500 de distribution contre cœur replié", "Architecture L2 §1, chiffrage (pistes d'optimisation)"),
    ("3", "Chemin d'une trame inter-VRF", "Architecture L3 §4 (politique d'inspection), L2 §4 (Po2/Po3 sur le cœur)"),
    ("4", "Asymétrie BGP", "Architecture L3 §6 (annonce conditionnelle, extrait EL-RTR2)"),
    ("5", "NPTv6 contre NAT44", "Architecture L3 §6 (inchangé)"),
    ("6", "Débit UTM du SN710", "Architecture L3 §4"),
    ("7", "Angle mort TLS", "Architecture L3 §4 (inspection TLS)"),
    ("8", "Tiering AD et VLAN 300", "Architecture L3 §2, plan d'adressage (VLAN 310)"),
    ("9", "Rançongiciel et immuabilité", "Ce document, SEC-03 ; chiffrage (disques, OPEX)"),
    ("10", "MAB des caméras", "Architecture L2 §7-8 (EAP-TLS, ACL téléchargée)"),
    ("11", "Quorum et QDevice", "Architecture L2 §10-11 (deux témoins, NM-WITNESS sert NM et DT)"),
    ("12", "RPO ZFS contre Ceph", "Architecture L2 §10 (réplication 1 min pour la supervision)"),
    ("13", "Arrêt électrique en cascade", "Énergie §3 (séquence NUT)"),
    ("14", "Consigne à 27 °C et humidité", "Énergie §4 (40-60 % d'humidité relative)"),
]

COURT = {
    "NET-01": "Bornes en mode local, 2 contrôleurs physiques HA sur le cœur, VLAN Wi-Fi uniques (pool /20, bail 2 h)",
    "SEC-01": "Stormshield en direct sur le cœur, sauvegardes hors du pare-feu, inspection par flux",
    "SYS-01": "Chiffrage aligné : 2 nœuds + témoin, sans Ceph",
    "SYS-02": "12 serveurs physiques → 2 clusters Proxmox (DT tier 0, DMZ isolée)",
    "SEC-02": "VLAN 310 tier 0, passerelle sur le Stormshield, pas d'Internet",
    "SEC-03": "PBS hors domaine, disques hors ligne en rotation, S3 Object Lock",
    "SYS-03": "Plancher surélevé, batardeau, détection de fuite, extinction au gaz, arrêt NUT",
    "NET-02": "Variante étudiée et chiffrée, 3 couches imposées par le CdC",
    "SEC-04": "2 collecteurs dédiés, archives scellées conservées 1 an",
}

LIBELLE = {ADR: "Plan d'adressage", L2: "Architecture L2", L3: "Architecture L3", EN: "Énergie", CH: "Chiffrage", SCH: "Schéma principal"}


def chiffres():
    ch2 = json.loads((ROOT / "chiffrage" / "estimation.json").read_text(encoding="utf-8"))
    ch1 = json.loads((V1 / "chiffrage" / "estimation.json").read_text(encoding="utf-8"))
    en2 = json.loads((ROOT / "livrables" / EN / "resume.json").read_text(encoding="utf-8"))
    en1 = json.loads((V1 / EN / "resume.json").read_text(encoding="utf-8"))
    nb_vlan2 = len([v for v in D.VLANS if v < 1000])
    return [
        ("Serveurs physiques", "16", "9"),
        ("VLAN (hors transits)", "37", str(nb_vlan2)),
        ("Pool Wi-Fi étudiants", "/22 par bloc, 94 % (bloc 1)", "/20 pour le bâtiment, 37 %"),
        ("Puissance de la salle serveur", f"{en1['salle']['it_typ'] / 1000:.2f} kW", f"{en2['salle']['it_typ'] / 1000:.2f} kW"),
        ("Électricité par an", f"{num(en1['energie']['kwh'])} kWh", f"{num(en2['energie']['kwh'])} kWh"),
        ("Autonomie avec un seul onduleur", f"{en1['onduleurs']['autonomie_degrade']} min", f"{en2['onduleurs']['autonomie_degrade']} min"),
        ("CAPEX (aléas compris)", eur(ch1["capex"]), eur(ch2["capex"])),
        ("OPEX annuel", eur(ch1["opex_total"]), eur(ch2["opex_total"])),
        ("Coût sur 5 ans", eur(ch1["tco5"]), eur(ch2["tco5"])),
    ], ch1, ch2


def document():
    date = datetime.date.today().strftime("%d/%m/%Y")
    lignes, ch1, ch2 = chiffres()
    H = [f"<!doctype html><html lang='fr'><head><meta charset='utf-8'><title>Traitement de l'audit</title><style>{CSS}</style></head><body>",
         "<h1>Traitement de l'audit d'infrastructure</h1>",
         f"<p class='sous'>Site de Marseille · IUT Génie Télécom, Luminy · RudyLink Infrastructure · RLI-AUD-001 · {date}<br>"
         f"Audit du {D.DATE_AUDIT} : constats, vérification, corrections apportées dans la version 2 de l'infrastructure.</p>",
         "<div class='cles'>",
         f"<div class='cle'><b>{len(CONSTATS)} constats</b>du tableau de synthèse, tous traités</div>",
         f"<div class='cle'><b>{len(AUTRES)} points</b>complémentaires (détail et questions du jury)</div>",
         f"<div class='cle'><b>{len(TROUVES)} écarts</b>trouvés en plus pendant la correction</div>",
         "<div class='cle'><b>v1 → v2</b>v1 archivée, v2 livrée</div></div>",
         "<h2>1. L'audit</h2>",
         "<p>Le 15/11/2026, l'équipe a soumis l'ensemble du dossier à un <b>audit indépendant en lecture seule</b>, réalisé avec l'assistant Gemini. "
         "Trois rôles d'auditeur ont été simulés : architecture réseau L2/L3 et Wi-Fi, cybersécurité et conformité ANSSI, infrastructure physique et "
         "virtualisation. Le dossier audité comprenait les schémas, le plan d'adressage, les architectures L2 et L3, le chiffrage et le lot énergie. "
         "Les référentiels appliqués étaient les guides ANSSI (PA-022, PA-043, PA-044, PA-099, BP-031, BP-100, PA-105), NIS 2, ASHRAE A1, "
         "la NF C 15-100 et l'ISO 11801.</p>",
         "<p>Résultat : <b>16,9 / 20</b> (réseau 18,0, sécurité 17,0, systèmes et datacenter 15,8), avec 9 constats (2 critiques, 5 majeurs, "
         "2 mineurs), un plan d'actions et 14 questions pièges pour la soutenance. Le rapport complet est joint : "
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
         "<li><b>Tracer</b> : chaque modification porte la référence du constat (repère <b>v2</b> dans les documents, référence dans les scripts).</li></ol>",
         "<h2>2. Synthèse</h2>",
         "<table><tr><th>Réf.</th><th>Sévérité</th><th>Domaine</th><th>Verdict</th><th>Correction v2</th><th>Statut</th></tr>"]
    for ref, dom, sev, constat, verdict, verif, corr, livs in CONSTATS:
        statut = "Justifié" if verdict.startswith("Fondé, déjà") else "Corrigé"
        H.append(f"<tr><td style='white-space:nowrap'><b>{ref}</b></td><td><span class='badge {SEV[sev]}'>{sev}</span></td><td>{e(dom)}</td>"
                 f"<td class='{VERDICT[verdict]}'>{e(verdict)}</td><td>{e(COURT[ref])}</td><td><b>{statut}</b></td></tr>")
    H.append("</table>")
    H.append("<h2 class='saut'>3. Détail des constats</h2>")
    for ref, dom, sev, constat, verdict, verif, corr, livs in CONSTATS:
        H.append(f"<div class='fiche'><h3>{ref} · {e(dom)} <span class='badge {SEV[sev]}'>{sev}</span></h3><dl>"
                 f"<dt>Constat</dt><dd>{e(constat)}</dd>"
                 f"<dt>Vérification</dt><dd><span class='{VERDICT[verdict]}'>{e(verdict)}.</span> {e(verif)}</dd>"
                 f"<dt>Correction v2</dt><dd>{e(corr)}</dd>"
                 f"<dt>Livrables</dt><dd>{', '.join(LIBELLE[l] for l in livs)}</dd></dl></div>")
    H.append("<h2>4. Autres points du rapport</h2><table><tr><th>Point</th><th>Verdict</th><th>Traitement</th><th>Livrables</th></tr>")
    for pt, verdict, trait, livs in AUTRES:
        H.append(f"<tr><td><b>{e(pt)}</b></td><td class='{VERDICT[verdict]}'>{e(verdict)}</td><td>{e(trait)}</td>"
                 f"<td class='chemin'>{', '.join(LIBELLE[l] for l in livs) or '—'}</td></tr>")
    H.append("</table>")
    H.append("<h2>5. Écarts trouvés pendant la correction</h2><p>Absents du rapport d'audit, découverts en reprenant les sources :</p><ul>")
    H += [f"<li><b>{e(t)}</b> : {e(d)}</li>" for t, d in TROUVES]
    H.append("</ul>")
    H.append("<h2 class='saut'>6. Version 1 et version 2</h2><table><tr><th></th><th class='n'>v1 (auditée)</th><th class='n'>v2</th></tr>")
    H += [f"<tr><td>{a}</td><td class='n'>{b}</td><td class='n'><b>{c}</b></td></tr>" for a, b, c in lignes]
    H.append("</table>")
    d = ch2["capex"] - ch1["capex"]
    H.append(f"<p>Le CAPEX augmente de <b>{eur(d)}</b> ({100 * d / ch1['capex']:+.1f} %). La virtualisation et la correction du cluster NM "
             "économisent environ 18 k€ de serveurs, ce qui finance une partie des ajouts de sécurité : extinction automatique et protection "
             "contre l'eau (≈ 15 k€), contrôleurs Wi-Fi physiques (12 k€), modules 10G du Stormshield, sauvegarde hors ligne, kits de pile "
             "oubliés en v1. La consommation électrique baisse d'environ 13 %. Le détail ligne à ligne est dans "
             "<code>chiffrage/estimation_infra.md</code> (section « Écarts avec la version 1 »).</p>")
    H.append("<h3>Livrables mis à jour</h3><table><tr><th>Livrable</th><th>Version 2</th><th>Version 1 archivée</th></tr>"
             "<tr><td>Plan d'adressage (point 05)</td><td><code>livrables/plan_adressage/</code></td><td><code>…/v1_2026-11-15/plan_adressage/</code></td></tr>"
             "<tr><td>Architecture L2 (points 03, 06)</td><td><code>livrables/architecture_l2/</code></td><td><code>…/v1_2026-11-15/architecture_l2/</code></td></tr>"
             "<tr><td>Architecture L3 (points 03, 05, 07)</td><td><code>livrables/architecture_l3/</code></td><td><code>…/v1_2026-11-15/architecture_l3/</code></td></tr>"
             "<tr><td>Énergie et refroidissement (point 14)</td><td><code>livrables/energie_refroidissement/</code></td><td><code>…/v1_2026-11-15/energie_refroidissement/</code></td></tr>"
             "<tr><td>Chiffrage</td><td><code>chiffrage/estimation_infra.md</code></td><td><code>…/v1_2026-11-15/chiffrage/</code></td></tr>"
             "<tr><td>Schéma principal</td><td><code>architecture/Projet_Marseille_site.drawio</code> (.png)</td>"
             "<td><code>architecture/archives/v1_2026-11-15/</code></td></tr></table>")
    H.append("<h2>7. Préparation de la soutenance</h2><p>Les 14 questions pièges du rapport ont maintenant une réponse dans les documents v2 :</p>"
             "<table><tr><th>Q</th><th>Sujet</th><th>Où se trouve la réponse</th></tr>")
    H += [f"<tr><td>{q}</td><td>{e(s)}</td><td>{e(o)}</td></tr>" for q, s, o in QUESTIONS]
    H.append("</table>")
    H.append("<h2>8. Reste à faire</h2><ul>"
             "<li>Faire auditer la v2 (même méthode, rapport comparable) pour mesurer l'effet des corrections.</li>"
             "<li>Confirmer par devis : module 10G du SN710, Catalyst 9800-L-F, extinction automatique (étude par un installateur APSAD), plancher technique.</li>"
             "<li>Valider avec le campus : groupe électrogène existant, cote de crue du sous-sol, annonce du /24 par l'AMU, BFD chez les opérateurs.</li>"
             "<li>DPIA de l'inspection TLS avec le DPO de l'AMU ; charte informatique à mettre à jour.</li>"
             "<li>Reporter les changements dans la maquette (point 06) : VLAN Wi-Fi sur le cœur, VLAN 310 derrière le pare-feu.</li></ul></body></html>")
    return "\n".join(H)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "html"):
        src = ICI / f"Rapport_Audit_Infrastructure_Marseille.{ext}"
        if src.exists():
            shutil.copyfile(src, OUT / f"rapport_audit_2026-11-15.{ext}")
    page = OUT / "traitement_audit.html"
    page.write_text(document(), encoding="utf-8")
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if chrome:
        with tempfile.TemporaryDirectory() as prof:
            subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", f"--user-data-dir={prof}", "--no-pdf-header-footer",
                            f"--print-to-pdf={OUT / 'traitement_audit.pdf'}", page.as_uri()], check=True, capture_output=True, timeout=180)
    lignes, _, _ = chiffres()
    (OUT / "README.md").write_text("\n".join([
        "# Audit de l'infrastructure (15/11/2026)", "<!-- onglet: Audit -->", "",
        "Audit indépendant en lecture seule de tout le dossier (schémas, adressage, L2/L3, chiffrage, énergie), réalisé avec Gemini "
        "(trois rôles : réseau, sécurité/ANSSI, systèmes/datacenter). Note : **16,9 / 20**, 9 constats (2 critiques, 5 majeurs, 2 mineurs).", "",
        "| Fichier | Contenu |", "|---|---|",
        "| [`traitement_audit.pdf`](traitement_audit.pdf) | RLI-AUD-001 : vérification de chaque constat, corrections de la v2, livrables touchés, réponses aux 14 questions du jury |",
        "| [`rapport_audit_2026-11-15.pdf`](rapport_audit_2026-11-15.pdf) | Rapport d'audit d'origine (aussi en `.html`) |", "",
        "## Versions de l'infrastructure", "",
        "- **v1** (auditée) : figée dans `livrables/archives/v1_2026-11-15/` et `architecture/archives/v1_2026-11-15/`.",
        "- **v2** (actuelle) : tous les livrables régénérés ; les changements sont repérés **v2** dans les documents.", "",
        "| | v1 | v2 |", "|---|---:|---:|", *[f"| {a} | {b} | {c} |" for a, b, c in lignes], "",
        "Régénérer : `python3 architecture/reseau/build.py && python3 energie/energie.py && python3 chiffrage/estimation.py && "
        "python3 architecture/audit/traitement_audit.py`. Le rapport d'audit et le script qui l'a produit (`generer_rapport_audit.py`) sont dans "
        "`architecture/audit/`.", ""]), encoding="utf-8")
    print(f"  {page.relative_to(ROOT)} -> .pdf")


if __name__ == "__main__":
    main()
