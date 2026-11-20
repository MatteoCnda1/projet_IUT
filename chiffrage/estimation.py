#!/usr/bin/env python3
"""Estimation budgétaire de l'infra du site de Marseille (point 18 ; schéma Projet_Marseille_site.drawio).

Prix en euros HT, prix revendeur constatés (neuf), novembre 2026.
Les licences sur 3 ans sont incluses dans le CAPEX quand l'éditeur les vend en bundle.
Lancer : python3 chiffrage/estimation.py  -> régénère estimation_infra.csv, estimation_infra.md, estimation.json
Ordre : cablage/plan_cablage.py (quantités), energie/energie.py (lot énergie), puis ce script.

Version 2 (après l'audit du 15/11/2026) : chiffrage aligné sur l'architecture réelle (SYS-01 : 2 nœuds NM + témoin, sans Ceph),
virtualisation de la DMZ et du datacenter (SYS-02), contrôleurs Wi-Fi physiques (NET-01), modules 10G du Stormshield (SEC-01),
sauvegarde hors ligne et immuable (SEC-03). v1 : livrables/archives/v1_2026-11-15/chiffrage/.

Version 2.1 (20/11/2026) :
  - lot énergie repris de l'étude BET (energie/bet.py, via livrables/energie_refroidissement/resume.json) : groupe électrogène et
    inverseur de source (catégorie « Énergie / secours »), ventilation des L.TECH, coffrets électriques, OPEX du groupe ;
  - lot 4 chiffré (catégorie « Sûreté », hors lot énergie) : caméras, licences VMS, enregistreur VS-NVR1, lecteurs de badge + UTL,
    logiciel de contrôle d'accès, à la place du forfait de 5 000 € ;
  - 2 climatiseurs techniques (et non une « climatisation de précision »), optiques et DAC décomptés, R360 à 4 ports 10G, module
    40G SVL des DL-SW nommé, repères AL-SW / AP corrects ;
  - support 24 h/24 7 j/7 avec rétablissement en 4 h pour les équipements critiques (OPEX explicite), J+1 ouvré pour le reste ;
  - renouvellement DNA par prix unitaires explicites, souscription Proxmox Backup Server.
"""
import csv
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from commun import charte as CH  # noqa: E402

# Quantités issues du plan de câblage (cablage/plan_cablage.py) et de l'étude Wi-Fi (cablage/etude_rssi.py)
_PLAN = HERE.parent / "livrables" / "plan_cablage" / "resume.json"
_BORNES = HERE.parent / "livrables" / "plan_cablage" / "wifi" / "bornes.json"
PLAN = json.loads(_PLAN.read_text(encoding="utf-8")) if _PLAN.exists() else None
BORNES = json.loads(_BORNES.read_text(encoding="utf-8"))["bornes"] if _BORNES.exists() else []
if PLAN:
    NB_PRISES = PLAN["prises"]
    NB_BORNES = PLAN["par_type"]["wifi"]
    NB_CAMERAS = PLAN["par_type"]["camera"]
    NB_BADGES = PLAN["par_type"]["badge"]
    NB_AL_SW = sum(b["switchs_48p"] for b in PLAN["baies"])
    NB_ROCADES = len(PLAN["rocades"])
    BAIES_42 = sum(b["baie"].startswith("42U") for b in PLAN["baies"])
    CHEMINS = {}
    for niv in PLAN["chemins_de_cables_m"].values():
        for dim, m in niv.items():
            CHEMINS[dim] = CHEMINS.get(dim, 0) + m
else:
    NB_PRISES, NB_BORNES, NB_CAMERAS, NB_BADGES, NB_AL_SW, NB_ROCADES, BAIES_42, CHEMINS = 400, 30, 14, 11, 8, 6, 0, {}
REP_BORNES = f"{BORNES[0]['id']} à {BORNES[-1]['id']}" if BORNES else "AP"
# Point 14 (energie/energie.py) : électricité, éléments ajoutés au lot énergie, entretien
_ENERGIE = HERE.parent / "livrables" / "energie_refroidissement" / "resume.json"
ENERGIE = json.loads(_ENERGIE.read_text(encoding="utf-8")) if _ENERGIE.exists() else None
CLIM_KW = ENERGIE["clim"]["unite_kw"] if ENERGIE else 7.1
PRIX_CHEMIN = {"100×50": 35, "200×60": 45, "300×100": 60}  # €/m posé, avec supports
# Chiffres publiés en v2 (15/11/2026, commit 7e1db0b), pour mesurer les changements de la v2.1
REF_V2 = {"capex": 606403, "opex_total": 44892, "renouvellement_total": 25157, "tco5": 881177, "Énergie / locaux": 71900,
          "controle_acces_forfait": 5000, "cameras": 15, "prises": 484}

# Optiques et DAC (v2.1, QTE-12) : Po1 de chaque switch d'accès vers les deux DL (2 liens fibre, 2 optiques par lien),
# plus les câbles DAC et QSFP de la salle serveur d'après le tableau des agrégats de l'architecture L2 : Po101/102 (8), Po2/3 (4),
# Po4 (2), maillage FGT-SNS (4), Po30/31 (4), Po10 (4), Po20 (4), Po21/22 (4), Po23 (2), Po1 FGT-DM (2), Po11/12 (4), DAD (3),
# SVL en QSFP (6), réplications (3).
DAC_SALLE = 54
NB_OPTIQUES = 4 * NB_AL_SW + DAC_SALLE

# Sûreté (lot 4, v2.1) : enregistrement continu, conservation 30 jours au plus (volet juridique)
VIDEO = dict(jours=30, debits_mbps=(4, 8), disques=8, disque_to=8, utile_to=43)
VIDEO["besoin_to"] = [round(NB_CAMERAS * d * 1e6 * VIDEO["jours"] * 86400 / 8 / 1e12, 1) for d in VIDEO["debits_mbps"]]


def fr(x, d=0):
    """Nombre pour le Markdown et les libellés : virgule décimale, espace ordinaire pour les milliers."""
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",")


# (catégorie, éléments du schéma, solution proposée, quantité, prix unitaire HT, note)
CAPEX = [
    ("Egress / WAN", "EL-RTR1, EL-RTR2", "Cisco Catalyst C8200L-1N-4T + DNA Essentials 3 ans", 2, 2200, "Routeurs de bordure, 1 par FAI"),
    ("Egress / WAN", "EL-FGT1, EL-FGT2", "FortiGate 120G + bundle UTP / FortiCare Premium 3 ans", 2, 7200, "Cluster HA actif/passif, pare-feu externe. Inspection TLS incluse dans le bundle"),
    ("Egress / WAN", "EL-SW1, EL-SW2", "Cisco Catalyst C9200L-24T-4X-E + DNA-E 3 ans", 2, 2300, ""),
    ("Sécurité interne", "EL-SNS1, EL-SNS2", "Stormshield SN710 + Premium UTM Security Pack 3 ans", 2, 7000, "Pare-feu interne HA. Prix à confirmer par devis revendeur"),
    ("Sécurité interne", "EL-SNS1, EL-SNS2", "Module d'extension 10G SFP+ pour SN710", 2, 1200, "v2 (SEC-01) : raccordement direct au cœur en 2×10G. Prix à confirmer"),
    ("DMZ", "DM-SW1, DM-SW2", "Cisco Catalyst C9200L-24T-4X-E + DNA-E 3 ans", 2, 2300, ""),
    ("DMZ", "DM-PVE1, DM-PVE2", "Dell PowerEdge R360 (Xeon E-2488 8 cœurs, 64 Go, 4 × 960 Go SSD ZFS, 4 × 10 GbE SFP+, double alim)", 2, 4450,
     "v2 (SYS-02) : cluster Proxmox de la DMZ (VM Caddy ×2, DNS ×2, web, mail, applicatif) au lieu de 6 serveurs physiques. "
     "v2.1 : 4 ports 10G (bond1 2×10G, réplication 10G DAC, 1 libre), carte 2 × 10G ajoutée (+250 €)"),
    ("DMZ", "DM-WITNESS", "Dell PowerEdge R260 entrée de gamme (Xeon E-2414, 16 Go, 2 × 480 Go SSD)", 1, 1600, "v2 : QDevice propre à la DMZ (flux vers l'administration limités à la sauvegarde, aux journaux, à l'heure et à NUT)"),
    ("Cœur", "CL-SW1, CL-SW2", "Cisco Catalyst C9500-16X-E + DNA-E 3 ans + modules 40G SVL", 2, 9500, "StackWise Virtual"),
    ("Distribution", "DL-SW1 à DL-SW4", "Cisco Catalyst C9500-16X-E + DNA-E 3 ans + module 40G SVL (C9500-NM-2Q)", 4, 9500,
     "2 blocs StackWise Virtual (gamme 9500 : la moins chère des gammes compatibles SVL, avec 9400 et 9600). v2.1 : module 40G nommé, "
     "compris dans le prix comme pour le cœur"),
    ("Accès", f"AL-SW1 à AL-SW{NB_AL_SW}", "Cisco Catalyst C9200L-48P-4X-E PoE+ + DNA-E 3 ans", NB_AL_SW, 3900,
     f"Plan de câblage : {NB_AL_SW} switchs pour {NB_PRISES} prises (+10 % de ports libres) et le budget PoE, répartis dans les 6 L.TECH "
     "(le schéma de site n'en montre que 4, à titre de principe)"),
    ("Accès", REP_BORNES, "Borne Wi-Fi 6E Cisco CW9164I + licence DNA AP 3 ans", NB_BORNES, 1300,
     "Nombre fixé par l'étude RSSI prédictive (≥ −67 dBm à 5 GHz, livrables/plan_cablage/wifi/bornes.csv)"),
    ("Accès", "WLC1, WLC2", "Contrôleur Wi-Fi Cisco Catalyst 9800-L-F (4 × 10G SFP+), HA SSO", 2, 6000,
     "v2 (NET-01) : bornes en mode local, itinérance sans coupure dans tout le bâtiment. Remplace la VM 9800-CL"),
    ("Net Management", "NM-SW1, NM-SW2", "Cisco Catalyst C9200L-24T-4X-E + DNA-E 3 ans", 2, 2300, ""),
    ("Net Management", "NM-PVE1, NM-PVE2", "Dell PowerEdge R660xs (2 × Xeon Silver 4510, 256 Go, 4 × 1,92 To SSD ZFS miroir, 2 × 25 GbE + carte 4 × 1G)", 2, 9800,
     "v2 (SYS-01) : 2 nœuds + témoin, ZFS répliqué en câble direct 25G (v1 : 3 nœuds Ceph). LXC Kea/chrony/DNS/Teleport/journaux, VM supervision"),
    ("Net Management", "NM-WITNESS", "Dell PowerEdge R260 entrée de gamme (Xeon E-2414, 16 Go, 2 × 480 Go SSD)", 1, 1600,
     "v2 (SYS-01) : QDevice des clusters NM et DT, serveur NUT (arrêt ordonné)"),
    ("Net Management", "EL-SW, NM-SW, DM-SW", "Kit de pile StackWise-80 C9200L (2 modules + câbles)", 3, 1100, "v2 : oubli de la v1 (piles prévues dans l'architecture L2)"),
    ("Net Management", "Services NM (LXC + Docker)", "Kea, chrony, Unbound, LibreNMS, Grafana, Loki, rsyslog, snmptrapd, Teleport Community, NUT", 1, 0, "Logiciels libres, 0 € de licence"),
    ("Datacenter", "DT-SW1, DT-SW2", "Cisco Catalyst C9300X-12Y-E (10/25G) + DNA-E 3 ans", 2, 8000, ""),
    ("Datacenter", "DT-PVE1, DT-PVE2", "Dell PowerEdge R660xs (1 × Xeon Silver 4514Y 16 cœurs, 128 Go, 4 × 1,92 To SSD ZFS, 4 × 25 GbE)", 2, 8500,
     "v2 (SYS-02) : cluster Proxmox tier 0 (VM AD ×2, NPS ×2, DHCP ×2) au lieu de 6 serveurs physiques"),
    ("Datacenter", "Licences serveurs Windows", "Windows Server 2025 Standard 16 cœurs (AD, DHCP, NPS/RADIUS)", 6, 1100,
     "6 VM Windows ; 1 licence = 2 VM, 3 par nœud pour pouvoir tout porter sur un seul nœud. Tarif public (Éducation nettement plus bas)"),
    ("Datacenter", "Licences d'accès", "CAL utilisateur Windows Server (tarif Éducation)", 600, 10, "~100 personnels + ~500 étudiants"),
    ("Datacenter", "DT-BKP1", "Serveur de sauvegarde Proxmox Backup Server (Dell R760xd2, ~100 To bruts)", 1, 12000, "Règle 3-2-1-1-0 : copie hors ligne et copie immuable externalisée (voir OPEX)"),
    ("Datacenter", "DT-BKP1", "Disque externe 24 To pour datastore amovible PBS", 3, 550,
     "v2 (SEC-03) : copie hors ligne. Rotation hebdomadaire : 1 branché, 1 au coffre sur place, 1 hors site"),
    ("Datacenter", "DT-BKP1", "Coffre ignifuge pour supports de sauvegarde", 1, 800, "v2 (SEC-03) : hors de la salle serveur"),
    ("Énergie / locaux", "Salle serveur", "Baie 42U 800 × 1000 avec portes ventilées", 2, 1500, ""),
    ("Énergie / locaux", f"Locaux techniques ({6 - BAIES_42} L.TECH)", "Baie 24U murale/sol", 6 - BAIES_42, 700, "2 L.TECH par niveau d'après les plans"),
    ("Énergie / locaux", "Locaux techniques", "Baie 42U 600 × 800 au sol", BAIES_42, 1200, "L.TECH dont la baie dépasse 22U (plan de câblage)"),
    ("Énergie / locaux", "Salle serveur", "Onduleur APC Smart-UPS SRT 6 kVA (en ligne)", 2, 4800, "Alimentation A/B"),
    ("Énergie / locaux", "Locaux techniques", "Onduleur 1,5 kVA rackable", 6, 900, ""),
    ("Énergie / locaux", "Salle serveur", "PDU managées et métrées", 4, 700, "Mesure de consommation (Green IT)"),
    ("Énergie / locaux", "Salle serveur", f"Climatiseur technique {fr(CLIM_KW, 1)} kW (fonctionnement 24 h/24), 1 en marche + 1 en secours (N+1)", 2, 6000,
     "v2.1 : 2 unités, comme au point 14 (v2 : « climatisation de précision » forfaitaire, 1 × 12 000 €) ; les armoires de précision y sont "
     "une option écartée"),
] + [
    (l["categorie"], l["schema"], l["solution"], l["quantite"], l["pu_ht"], l["note"] + " (point 14)") for l in (ENERGIE or {}).get("capex_nouveaux", [])
] + [
    # Lot 4, sûreté (v2.1) : ordres de grandeur, à confirmer par devis. Hors du lot énergie.
    ("Sûreté", f"Caméras {NB_CAMERAS} (plan de câblage)", "Caméra IP fixe PoE 802.3af, ONVIF profils S et T, 802.1X, posée, raccordée et réglée "
     "(masquage des zones privatives), panneaux d'information compris", NB_CAMERAS, 550,
     "v2.1 : lot 4 chiffré ; ordre de grandeur 400 à 700 € posée, à confirmer par devis. Aucune caméra au foyer des étudiants"),
    ("Sûreté", "VS-NVR1", "Licence VMS par caméra (perpétuelle, 3 ans de mises à jour)", NB_CAMERAS, 150,
     "v2.1 : ordre de grandeur 100 à 200 € par caméra, à confirmer par devis"),
    ("Sûreté", "VS-NVR1", f"Enregistreur vidéo 2U, {VIDEO['disques']} × {VIDEO['disque_to']} To en RAID 6 (≈ {VIDEO['utile_to']} To utiles), "
     "logiciel VMS, 2 alimentations", 1, 7500,
     f"v2.1 : baie 2 de la salle serveur. {VIDEO['jours']} jours d'images : {NB_CAMERAS} caméras × {VIDEO['debits_mbps'][0]} Mb/s ≈ "
     f"{fr(VIDEO['besoin_to'][0])} To ({fr(VIDEO['besoin_to'][1])} To à {VIDEO['debits_mbps'][1]} Mb/s). À confirmer par devis"),
    ("Sûreté", f"Badgeuses {NB_BADGES} (plan de câblage)", "Lecteur sans contact DESFire EV3 + UTL OSDP v2 (canal sécurisé), gâche ou ventouse, "
     "posés et raccordés", NB_BADGES, 1200,
     "v2.1 : remplace le forfait v2 de 5 000 € (7 portes) ; ordre de grandeur 800 à 1 500 € par porte, à confirmer par devis"),
    ("Sûreté", "Contrôle d'accès", "Logiciel de contrôle d'accès (licence serveur, VM du datacenter)", 1, 1500, "v2.1 : à confirmer par devis"),
] + [
    ("Câblage", "Prises", "Prise RJ45 Cat6A fournie, posée et recettée", NB_PRISES, 140,
     "10 Gb/s, durée de vie 15 ans (CdC). Usagers + bornes + caméras + badgeuses (plan de câblage)"),
    ("Câblage", "Rocades", "Fibre OM4 12 brins L.TECH vers salle serveur", NB_ROCADES, 1500,
     "2 câbles par local, par deux chemins distincts (colonnes Nord et Sud ; au sous-sol, deux circulations différentes)"),
] + [
    ("Câblage", "Chemins de câbles", f"Chemin de câbles fil {dim} mm, posé", round(m), PRIX_CHEMIN.get(dim.split()[0], 60),
     "Métré du plan de câblage (circulations et locaux)") for dim, m in sorted(CHEMINS.items())
] + [
    ("Câblage", "Optiques", "Modules SFP+/SFP28/QSFP compatibles et câbles DAC", NB_OPTIQUES, 70,
     f"v2.1 : décompte ({4 * NB_AL_SW} optiques pour les Po1 des {NB_AL_SW} switchs d'accès + {DAC_SALLE} DAC et QSFP dans la salle serveur, "
     "v2 : 96 forfaitaires), à valider par l'équipe réseau. Optiques Cisco d'origine : environ ×4"),
    ("Câblage", "Brassage", "Panneaux, cordons, passe-câbles", 1, 4000, "Forfait"),
    ("Prestations", "Intégration", "Ingénierie, intégration et configuration (jours)", 50, 650, "v2 : +5 j (3 clusters Proxmox, WLC, chaîne de journalisation)"),
    ("Prestations", "Recette", "Recette, documentation et formation (jours)", 10, 650, ""),
]
ALEAS = 0.10  # provision pour aléas
CAT_ENERGIE = ("Énergie / locaux", "Énergie / secours")
CAT_SURETE = "Sûreté"

# Support 24 h/24 7 j/7 avec rétablissement en 4 h (v2.1, décision D4) : équipements critiques. Le reste (accès AL-SW, bornes, DMZ,
# objets) : J+1 ouvré, couvert par les garanties constructeur et l'extension de garantie des serveurs (renouvellements).
# Onduleurs et climatiseurs de la salle : contrats du lot énergie (point 14, repris dans l'OPEX ci-dessous).
SUPPORT_4H = [
    ("Support Cisco 24 h/24 7 j/7, remplacement sous 4 h", [("EL-RTR1/2", 2, 350), ("CL-SW1/2, DL-SW1 à 4", 6, 1200), ("WLC1/2", 2, 600)]),
    ("Fortinet : remplacement matériel sous 4 h, 24 h/24 7 j/7", [("EL-FGT1/2 (en plus de FortiCare Premium)", 2, 700)]),
    ("Stormshield : échange sur site sous 4 h, 24 h/24 7 j/7", [("EL-SNS1/2", 2, 600)]),
    ("Dell : ProSupport Plus Mission Critical, intervention sous 4 h, 24 h/24 7 j/7", [("DT-PVE1/2, NM-PVE1/2, DT-BKP1 : supplément sur la garantie de base", 5, 750)]),
]

# OPEX annuel, années 1 à 5 (licences sécurité/réseau incluses dans le CAPEX les 3 premières années)
IT_KW, PUE, KWH = 3.5, 1.6, 0.20
OPEX = [
    ("Accès Internet FAI 1", "Fibre dédiée FTTO 1 Gb/s symétrique, GTR 4 h", 12 * 900),
    ("Accès Internet FAI 2", "Fibre dédiée 500 Mb/s, autre opérateur", 12 * 450),
    ("Interconnexion WAN", "VPN MPLS vers le site jumeau (Digne)", 12 * 700),
    ("Proxmox VE", "Souscription Standard : NM 2 nœuds × 2 sockets, DT et DMZ 4 nœuds × 1 socket, 550 €/socket", (2 * 2 + 4 * 1) * 550),
    ("Proxmox Backup Server", "v2.1 : souscription Basic de DT-BKP1 (1 socket), à confirmer", 550),
    ("Sauvegarde externalisée", "Stockage objet ~20 To hors site, verrouillage S3 Object Lock en mode conformité (hébergeur qualifié SecNumCloud, données dans l'UE)", 12 * 180),
] + [
    (poste + " (v2.1)", " ; ".join(f"{rep} : {n} × {fr(pu)} €" for rep, n, pu in eq), sum(n * pu for _r, n, pu in eq)) for poste, eq in SUPPORT_4H
] + ([
    ("Électricité", f"{fr(IT_KW, 1)} kW IT × PUE {fr(PUE, 1)} × 8 760 h × {fr(KWH, 2)} €/kWh", round(IT_KW * PUE * 8760 * KWH)),
] if not ENERGIE else [(o["poste"], o["detail"], o["montant"]) for o in ENERGIE["opex"]]) + [
    ("Nom de domaine", "Domaine + DNS secondaire", 30),
]

# Renouvellements à partir de l'année 4 (fin des licences et garanties de 3 ans)
DNA = dict(acces=220, salle=500, ap=90, routeur=300)   # € HT/an : C9200L-48P ; switchs de la salle (C9200L-24T, C9500, C9300X) ; borne ; C8200L
NB_SW_SALLE = 2 + 2 + 2 + 2 + 4 + 2                     # EL-SW, DM-SW, NM-SW, CL-SW, DL-SW, DT-SW
RENOUV = [
    ("FortiGuard UTP + FortiCare", "2 FortiGate 120G", 2 * 2100),
    ("Stormshield Premium UTM", "2 SN710", 2 * 1500),
    ("Cisco DNA Essentials / AP", f"v2.1 : {NB_AL_SW} switchs d'accès × {DNA['acces']} € + {NB_SW_SALLE} switchs de la salle × {DNA['salle']} € + "
     f"{NB_BORNES} bornes × {DNA['ap']} € + 2 routeurs × {DNA['routeur']} € (v2 : 12 000 € × switchs et bornes / 56, base non documentée)",
     NB_AL_SW * DNA["acces"] + NB_SW_SALLE * DNA["salle"] + NB_BORNES * DNA["ap"] + 2 * DNA["routeur"]),
    ("Support matériel serveurs", "Extension de garantie J+1 de 9 serveurs × 400 € (v1 : 16 serveurs, comptés 18 × 350 €)", 9 * 400),
    ("Sûreté (lot 4)", f"v2.1 : mises à jour du VMS ({NB_CAMERAS} caméras × 30 €), du logiciel de contrôle d'accès (400 €), extension de garantie "
     "du VS-NVR1 (300 €)", NB_CAMERAS * 30 + 400 + 300),
]

# Pistes d'optimisation (force de proposition)
OPTIM = [
    ("Cœur replié (collapsed core)", "Un seul bâtiment : fusionner distribution et cœur sur 2 C9500-48Y4C (SVL). Suppression de DL-SW1 à DL-SW4. "
     "Étudiée, non retenue : le cahier des charges demande 3 couches (audit NET-02). Économie brute : le surcoût des deux C9500-48Y4C par rapport "
     "aux C9500-16X du cœur est à déduire (non chiffré).", 4 * 9500),
    ("Services libres pour NPS et DHCP", "Remplacer NPS et le DHCP Windows par FreeRADIUS et Kea (déjà utilisés pour les autres VRF) : seules les 2 VM AD "
     "restent sous Windows, soit 1 licence par nœud au lieu de 3.", 4 * 1100),
    ("Tarifs Éducation", "Remises éditeur Microsoft/Cisco/Fortinet pour l'enseignement supérieur (souvent −30 à −50 %).", None),
]
OPTIM_BRUT = {"Cœur replié (collapsed core)"}


def main():
    rows = []
    for cat, schema, sol, q, pu, note in CAPEX:
        rows.append(dict(categorie=cat, schema=schema, solution=sol, quantite=q, pu_ht=pu, total_ht=q * pu, note=note))
    sous_total = sum(r["total_ht"] for r in rows)
    aleas = round(sous_total * ALEAS)
    capex = sous_total + aleas
    opex = sum(x[2] for x in OPEX)
    renouv = sum(x[2] for x in RENOUV)
    tco5 = capex + 5 * opex + 2 * renouv
    cats = {}
    for r in rows:
        cats[r["categorie"]] = cats.get(r["categorie"], 0) + r["total_ht"]
    lot_energie = sum(cats.get(c, 0) for c in CAT_ENERGIE)
    lot_surete = cats.get(CAT_SURETE, 0)
    support = sum(x[2] for x in OPEX if x[0].endswith("(v2.1)") and "4 h" in x[0])
    support_nrj = sum(o["montant"] for o in (ENERGIE or {}).get("opex", []) if "4 h" in o["detail"])

    with open(HERE / "estimation_infra.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter=";")
        w.writeheader()
        w.writerows(rows)

    data = dict(version=CH.VERSION, date=CH.DATE_VERSION,
                capex_lignes=rows, par_categorie=cats, sous_total=sous_total, aleas=aleas, capex=capex,
                opex=[dict(poste=a, detail=b, montant=c) for a, b, c in OPEX], opex_total=opex,
                renouvellement=[dict(poste=a, detail=b, montant=c) for a, b, c in RENOUV], renouvellement_total=renouv,
                tco5=tco5, optimisations=[dict(piste=a, detail=b, economie=c, brute=a in OPTIM_BRUT) for a, b, c in OPTIM],
                lots=dict(energie=lot_energie, surete=lot_surete),
                quantites=dict(prises=NB_PRISES, bornes=NB_BORNES, cameras=NB_CAMERAS, badges=NB_BADGES, switchs_acces=NB_AL_SW,
                               rocades=NB_ROCADES, optiques=NB_OPTIQUES),
                stockage_video=dict(VIDEO, cameras=NB_CAMERAS),
                support_4h=dict(opex_reseau_serveurs=support, opex_energie=support_nrj,
                                equipements="EL-RTR, EL-FGT, EL-SNS, CL-SW, DL-SW, WLC, DT-PVE, NM-PVE, DT-BKP1, onduleurs et climatiseurs de la salle",
                                reste="J+1 ouvré (AL-SW, bornes, DMZ, objets)"),
                v2=REF_V2)
    (HERE / "estimation.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    e = lambda n: f"{fr(n)} €"  # noqa: E731
    sg = lambda d: "+" if d >= 0 else "−"  # noqa: E731
    md = ["# Estimation budgétaire de l'infrastructure (point 18)", "",
          f"{CH.SITE} · {CH.BATIMENT} · {CH.SOCIETE} · **{CH.MENTION}**", "",
          "Source : `architecture/Projet_Marseille_site.drawio`, plan de câblage (point 04), énergie et refroidissement (point 14). Prix HT, prix "
          "revendeur constatés (neuf), novembre 2026. À confirmer par devis : ces montants servent à cadrer le budget.", "",
          "## Synthèse", "", "| Poste | Montant HT |", "|---|---:|"]
    md += [f"| {c} | {e(v)} |" for c, v in cats.items()]
    md += [f"| **Sous-total** | **{e(sous_total)}** |", f"| Aléas ({ALEAS * 100:.0f} %) | {e(aleas)} |",
           f"| **CAPEX total** | **{e(capex)}** |", f"| OPEX annuel (années 1 à 5, hors renouvellements) | {e(opex)} |",
           f"| Renouvellements annuels (dès l'année 4) | {e(renouv)} |", f"| **Coût total sur 5 ans (TCO)** | **{e(tco5)}** |", "",
           f"Coût sur 5 ans = CAPEX + 5 × OPEX + 2 × renouvellements. Lot énergie (Énergie / locaux + Énergie / secours) : {e(lot_energie)} HT ; "
           f"lot sûreté : {e(lot_surete)} HT (hors aléas).", "",
           "## Détail CAPEX", "", "| Catégorie | Éléments du schéma | Solution proposée | Qté | PU HT | Total HT | Note |", "|---|---|---|---:|---:|---:|---|"]
    md += [f"| {r['categorie']} | {r['schema']} | {r['solution']} | {r['quantite']} | {e(r['pu_ht'])} | {e(r['total_ht'])} | {r['note']} |" for r in rows]
    md += ["", "## OPEX annuel (années 1 à 5)", "", "| Poste | Détail | Montant/an |", "|---|---|---:|"]
    md += [f"| {a} | {b} | {e(c)} |" for a, b, c in OPEX]
    md += ["", f"Support des équipements critiques (v2.1) : rétablissement en 4 h, 24 h/24 7 j/7, pour les routeurs EL-RTR, les pare-feu EL-FGT et "
           "EL-SNS, le cœur CL-SW, la distribution DL-SW, les WLC, les hyperviseurs DT-PVE et NM-PVE, DT-BKP1, les onduleurs et les climatiseurs "
           f"de la salle : {e(support)} HT/an (réseau et serveurs) + {e(support_nrj)} HT/an (lot énergie). Le reste (accès AL-SW, bornes, DMZ, "
           "objets) : J+1 ouvré, garanties constructeur. Prix des contrats en ordre de grandeur, à confirmer par devis."]
    md += ["", "## Renouvellements (à partir de l'année 4)", "", "| Poste | Détail | Montant/an |", "|---|---|---:|"]
    md += [f"| {a} | {b} | {e(c)} |" for a, b, c in RENOUV]
    md += ["", "## Pistes d'optimisation", "", "| Piste | Détail | Économie CAPEX |", "|---|---|---:|"]
    def economie(piste, montant):
        if not montant:
            return "variable"
        return "jusqu'à " + e(montant) + " (brut)" if piste in OPTIM_BRUT else e(montant)
    md += [f"| {a} | {b} | {economie(a, c)} |" for a, b, c in OPTIM]
    v1 = HERE.parent / "livrables" / "archives" / "v1_2026-11-15" / "chiffrage" / "estimation.json"
    if v1.exists():
        a = json.loads(v1.read_text(encoding="utf-8"))
        md += ["", "## Écarts avec la version 1 (audit du 15/11/2026)", "",
               "Détail par constat : `livrables/audit/traitement_audit.pdf`. Version 1 : `livrables/archives/v1_2026-11-15/chiffrage/`.", "",
               f"| | v1 | {CH.VERSION} | Écart |", "|---|---:|---:|---:|"]
        for nom, k in (("CAPEX total", "capex"), ("OPEX annuel", "opex_total"), ("Renouvellements annuels", "renouvellement_total"), ("TCO 5 ans", "tco5")):
            md.append(f"| {nom} | {e(a[k])} | {e(data[k])} | {sg(data[k] - a[k])}{e(abs(data[k] - a[k]))} |")
        md += ["", "Principales causes (v2) : 12 serveurs physiques et 3 nœuds Ceph remplacés par 6 hyperviseurs et 2 témoins (−) ; contrôleurs Wi-Fi "
               "physiques, modules 10G du Stormshield, kits de pile, sauvegarde hors ligne (+) ; extinction automatique, plancher surélevé et batardeau "
               "(lot énergie, +). Puis v2.1 : voir ci-dessous."]
    md += ["", "## Écarts avec la version 2 (15/11/2026)", "",
           f"Version 2 : `{CH.ARCHIVE_PRECEDENTE}`. Étude BET et groupe électrogène : `livrables/energie_refroidissement/bet_locaux_techniques.pdf`.", "",
           "| | v2 | v2.1 | Écart |", "|---|---:|---:|---:|",
           f"| Lot énergie (Énergie / locaux + Énergie / secours) | {e(REF_V2['Énergie / locaux'])} (dont {e(REF_V2['controle_acces_forfait'])} de "
           f"contrôle d'accès) | {e(lot_energie)} | "
           f"{sg(lot_energie - REF_V2['Énergie / locaux'])}{e(abs(lot_energie - REF_V2['Énergie / locaux']))} |",
           f"| Lot sûreté (caméras, VMS, enregistreur, badgeuses) | {e(REF_V2['controle_acces_forfait'])} (forfait, dans le lot énergie) | {e(lot_surete)} | "
           f"+{e(lot_surete - REF_V2['controle_acces_forfait'])} |"]
    for nom, k in (("CAPEX total (aléas compris)", "capex"), ("OPEX annuel", "opex_total"), ("Renouvellements annuels", "renouvellement_total"),
                   ("TCO 5 ans", "tco5")):
        md.append(f"| {nom} | {e(REF_V2[k])} | {e(data[k])} | {sg(data[k] - REF_V2[k])}{e(abs(data[k] - REF_V2[k]))} |")
    causes = []
    if ENERGIE and "bet" in ENERGIE:
        causes.append(f"groupe électrogène {ENERGIE['bet']['groupe_electrogene']['esp_kva']} kVA ESP, inverseur de source, génie civil et raccordement "
                      f"({e(ENERGIE.get('capex_groupe_electrogene', 0))} HT) ; ventilation renforcée de trois L.TECH (mini-split, extracteurs 300 m³/h) et "
                      "coffrets électriques ; OPEX : maintenance, essai sur banc et gazole du groupe, électricité recalculée (pertes réelles des onduleurs, "
                      "auxiliaires, enregistreur vidéo)")
    causes += [f"lot 4 chiffré : {NB_CAMERAS} caméras et leurs licences VMS, enregistreur VS-NVR1, {NB_BADGES} lecteurs de badge et UTL, logiciel "
               "de contrôle d'accès, au lieu du forfait de 5 000 € classé dans le lot énergie",
               f"caméra du foyer retirée ({REF_V2['cameras']} → {NB_CAMERAS} caméras, {REF_V2['prises']} → {NB_PRISES} prises)",
               f"optiques et DAC décomptés (96 → {NB_OPTIQUES}), carte 2 × 10G des DM-PVE",
               f"support 24 h/24 7 j/7 en 4 h des équipements critiques ({e(support + support_nrj)} HT/an), souscription Proxmox Backup Server",
               "renouvellement DNA par prix unitaires, mises à jour du lot sûreté"]
    md += ["", "Causes : " + " ; ".join(causes) + "."]
    md += ["", "## Hypothèses de dimensionnement", "",
           "- Bâtiment IUT Génie Télécom (Luminy) : sous-sol, RDC, étage 1, 6 locaux techniques (plans `docs/plans_batiment/`).",
           (f"- {NB_PRISES} prises d'après le plan de câblage (`livrables/plan_cablage/`) : bureaux 2 par poste, salles de TP 1 par poste + 2, "
            f"salles de TD/cours/réunion 3, {NB_BORNES} bornes Wi-Fi (étude RSSI), {NB_CAMERAS} caméras IP, {NB_BADGES} badgeuses." if PLAN else
            "- ~400 prises : ~17 bureaux × 2, ~10 salles info/TP/réseaux × 24, ~12 salles TD/cours/réunion × 3, 30 bornes, ~14 caméras IP, ~11 badgeuses."),
           "- Postes clients, imprimantes et téléphones IP exclus (budget poste de travail à part).",
           f"- Sûreté (lot 4, v2.1) : enregistrement continu, {VIDEO['jours']} jours au plus ; {NB_CAMERAS} caméras × {VIDEO['debits_mbps'][0]} à "
           f"{VIDEO['debits_mbps'][1]} Mb/s = {fr(VIDEO['besoin_to'][0])} à {fr(VIDEO['besoin_to'][1])} To, couverts par les {VIDEO['utile_to']} To utiles "
           "de VS-NVR1. Prix en ordre de grandeur, à confirmer par devis. Le VMS n'est plus une VM du datacenter.",
           "- La `cisco-price-list.pdf` (`docs/references_prix/`) date du début des années 2000 (gammes Aironet 340/350, VPN 3000) : elle n'est pas "
           "utilisable pour des prix actuels.",
           (f"- Électricité, onduleurs, climatisation : bilan du point 14 (`livrables/energie_refroidissement/`), PUE {fr(ENERGIE['energie']['pue'], 2)}, "
            f"{fr(ENERGIE['energie']['kwh'])} kWh/an, {fr(KWH, 2)} €/kWh HT." if ENERGIE else
            f"- Électricité : {fr(IT_KW, 1)} kW de charge IT moyenne, PUE {fr(PUE, 1)}, {fr(KWH, 2)} €/kWh HT."),
           (f"- Groupe électrogène (v2.1) : le site n'en a pas (confirmé par le client). Groupe diesel {ENERGIE['bet']['groupe_electrogene']['esp_kva']} kVA ESP / "
            f"{ENERGIE['bet']['groupe_electrogene']['prp_kva']} kVA PRP et inverseur automatique en tête du tableau informatique, prix en ordre de grandeur "
            "(distributeurs, installateurs), à confirmer par devis." if ENERGIE and "bet" in ENERGIE else ""), ""]
    (HERE / "estimation_infra.md").write_text("\n".join(md), encoding="utf-8")
    print(f"sous-total {sous_total}  aleas {aleas}  CAPEX {capex}  OPEX/an {opex}  renouv/an {renouv}  TCO5 {tco5}")
    print(f"  lot énergie {lot_energie}  lot sûreté {lot_surete}  support 4 h {support} + {support_nrj} (énergie)")
    for c, v in cats.items():
        print(f"  {c:20s} {v}")


if __name__ == "__main__":
    main()
