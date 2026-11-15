#!/usr/bin/env python3
"""Estimation budgétaire de l'infra du site de Marseille (schéma Projet_Marseille_site.drawio).

Prix en euros HT, prix revendeur constatés (neuf), novembre 2026.
Les licences sur 3 ans sont incluses dans le CAPEX quand l'éditeur les vend en bundle.
Lancer: python3 estimation.py  -> régénère estimation_infra.csv, estimation_infra.md, estimation.json

Version 2 (après l'audit du 15/11/2026) : chiffrage aligné sur l'architecture réelle (SYS-01 : 2 nœuds NM + témoin, sans Ceph),
virtualisation de la DMZ et du datacenter (SYS-02), contrôleurs Wi-Fi physiques (NET-01), modules 10G du Stormshield (SEC-01),
sauvegarde hors ligne et immuable (SEC-03). v1 : livrables/archives/v1_2026-11-15/chiffrage/.
"""
import csv, json, pathlib

HERE = pathlib.Path(__file__).parent

# Quantités issues du plan de câblage (cablage/plan_cablage.py) et de l'étude Wi-Fi (cablage/etude_rssi.py)
_PLAN = HERE.parent / "livrables" / "plan_cablage" / "resume.json"
PLAN = json.loads(_PLAN.read_text(encoding="utf-8")) if _PLAN.exists() else None
if PLAN:
    NB_PRISES = PLAN["prises"]
    NB_BORNES = PLAN["par_type"]["wifi"]
    NB_AL_SW = sum(b["switchs_48p"] for b in PLAN["baies"])
    NB_ROCADES = len(PLAN["rocades"])
    BAIES_42 = sum(b["baie"].startswith("42U") for b in PLAN["baies"])
    CHEMINS = {}
    for niv in PLAN["chemins_de_cables_m"].values():
        for dim, m in niv.items():
            CHEMINS[dim] = CHEMINS.get(dim, 0) + m
else:
    NB_PRISES, NB_BORNES, NB_AL_SW, NB_ROCADES, BAIES_42, CHEMINS = 400, 30, 8, 6, 0, {}
# Point 14 (energie/energie.py) : électricité, éléments ajoutés au lot énergie, entretien
_ENERGIE = HERE.parent / "livrables" / "energie_refroidissement" / "resume.json"
ENERGIE = json.loads(_ENERGIE.read_text(encoding="utf-8")) if _ENERGIE.exists() else None
PRIX_CHEMIN = {"100×50": 35, "200×60": 45, "300×100": 60}  # €/m posé, avec supports

# (catégorie, éléments du schéma, solution proposée, quantité, prix unitaire HT, note)
CAPEX = [
    ("Egress / WAN", "EL-RTR1, EL-RTR2", "Cisco Catalyst C8200L-1N-4T + DNA Essentials 3 ans", 2, 2200, "Routeurs de bordure, 1 par FAI"),
    ("Egress / WAN", "EL-FGT1, EL-FGT2", "FortiGate 120G + bundle UTP / FortiCare Premium 3 ans", 2, 7200, "Cluster HA actif/passif, pare-feu externe. Inspection TLS incluse dans le bundle"),
    ("Egress / WAN", "EL-SW1, EL-SW2", "Cisco Catalyst C9200L-24T-4X-E + DNA-E 3 ans", 2, 2300, ""),
    ("Sécurité interne", "EL-SNS1, EL-SNS2", "Stormshield SN710 + Premium UTM Security Pack 3 ans", 2, 7000, "Pare-feu interne HA. Prix à confirmer par devis revendeur"),
    ("Sécurité interne", "EL-SNS1, EL-SNS2", "Module d'extension 10G SFP+ pour SN710", 2, 1200, "v2 (SEC-01) : raccordement direct au cœur en 2×10G. Prix à confirmer"),
    ("DMZ", "DM-SW1, DM-SW2", "Cisco Catalyst C9200L-24T-4X-E + DNA-E 3 ans", 2, 2300, ""),
    ("DMZ", "DM-PVE1, DM-PVE2", "Dell PowerEdge R360 (Xeon E-2488 8 cœurs, 64 Go, 4x960 Go SSD ZFS, 2x10 GbE, double alim)", 2, 4200,
     "v2 (SYS-02) : cluster Proxmox de la DMZ (VM Caddy x2, DNS x2, web, mail, applicatif) au lieu de 6 serveurs physiques"),
    ("DMZ", "DM-WITNESS", "Dell PowerEdge R260 entrée de gamme (Xeon E-2414, 16 Go, 2x480 Go SSD)", 1, 1600, "v2 : QDevice propre à la DMZ (aucun flux vers l'administration)"),
    ("Cœur", "CL-SW1, CL-SW2", "Cisco Catalyst C9500-16X-E + DNA-E 3 ans + modules 40G SVL", 2, 9500, "StackWise Virtual"),
    ("Distribution", "DL-SW1 à DL-SW4", "Cisco Catalyst C9500-16X-E + DNA-E 3 ans", 4, 9500, "2 blocs StackWise Virtual (le SVL impose la gamme 9500)"),
    ("Accès", "AL-SW1 à AL-SW4", "Cisco Catalyst C9200L-48P-4X-E PoE+ + DNA-E 3 ans", NB_AL_SW, 3900,
     f"Le schéma en montre 4. Plan de câblage : {NB_AL_SW} switchs pour {NB_PRISES} prises (+10 % de ports libres) et le budget PoE, répartis dans les 6 L.TECH"),
    ("Accès", "AL-AP1", "Borne Wi-Fi 6E Cisco CW9164I + licence DNA AP 3 ans", NB_BORNES, 1300,
     "Nombre fixé par l'étude RSSI prédictive (≥ −67 dBm à 5 GHz, livrables/plan_cablage/wifi)"),
    ("Accès", "WLC1, WLC2", "Contrôleur Wi-Fi Cisco Catalyst 9800-L-F (4x10G SFP+), HA SSO", 2, 6000,
     "v2 (NET-01) : bornes en mode local, itinérance sans coupure dans tout le bâtiment. Remplace la VM 9800-CL"),
    ("Net Management", "NM-SW1, NM-SW2", "Cisco Catalyst C9200L-24T-4X-E + DNA-E 3 ans", 2, 2300, ""),
    ("Net Management", "NM-PVE1, NM-PVE2", "Dell PowerEdge R660xs (2x Xeon Silver 4510, 256 Go, 4x1,92 To SSD ZFS miroir, 2x25 GbE + carte 4x1G)", 2, 9800,
     "v2 (SYS-01) : 2 nœuds + témoin, ZFS répliqué en câble direct 25G (v1 : 3 nœuds Ceph). LXC Kea/chrony/DNS/Teleport/journaux, VM supervision"),
    ("Net Management", "NM-WITNESS", "Dell PowerEdge R260 entrée de gamme (Xeon E-2414, 16 Go, 2x480 Go SSD)", 1, 1600,
     "v2 (SYS-01) : QDevice des clusters NM et DT, serveur NUT (arrêt ordonné)"),
    ("Net Management", "EL-SW, NM-SW, DM-SW", "Kit de pile StackWise-80 C9200L (2 modules + câbles)", 3, 1100, "v2 : oubli de la v1 (piles prévues dans l'architecture L2)"),
    ("Net Management", "Services NM (LXC + Docker)", "Kea, chrony, Unbound, LibreNMS, Grafana, Loki, rsyslog, snmptrapd, Teleport Community, NUT", 1, 0, "Logiciels libres, 0 € de licence"),
    ("Datacenter", "DT-SW1, DT-SW2", "Cisco Catalyst C9300X-12Y-E (10/25G) + DNA-E 3 ans", 2, 8000, ""),
    ("Datacenter", "DT-PVE1, DT-PVE2", "Dell PowerEdge R660xs (1x Xeon Silver 4514Y 16 cœurs, 128 Go, 4x1,92 To SSD ZFS, 4x25 GbE)", 2, 8500,
     "v2 (SYS-02) : cluster Proxmox tier 0 (VM AD x2, NPS x2, DHCP x2) au lieu de 6 serveurs physiques"),
    ("Datacenter", "Licences serveurs Windows", "Windows Server 2025 Standard 16 cœurs (AD, DHCP, NPS/RADIUS)", 6, 1100,
     "6 VM Windows ; 1 licence = 2 VM, 3 par nœud pour pouvoir tout porter sur un seul nœud. Tarif public (Éducation nettement plus bas)"),
    ("Datacenter", "Licences d'accès", "CAL utilisateur Windows Server (tarif Éducation)", 600, 10, "~100 personnels + ~500 étudiants"),
    ("Datacenter", "DT-BKP1", "Serveur de sauvegarde Proxmox Backup Server (Dell R760xd2, ~100 To bruts)", 1, 12000, "Règle 3-2-1-1-0 : copie hors ligne et copie immuable externalisée (voir OPEX)"),
    ("Datacenter", "DT-BKP1", "Disque externe 24 To pour datastore amovible PBS", 3, 550,
     "v2 (SEC-03) : copie hors ligne. Rotation hebdomadaire : 1 branché, 1 au coffre sur place, 1 hors site"),
    ("Datacenter", "DT-BKP1", "Coffre ignifuge pour supports de sauvegarde", 1, 800, "v2 (SEC-03) : hors de la salle serveur"),
    ("Énergie / locaux", "Salle serveur", "Baie 42U 800x1000 avec portes ventilées", 2, 1500, ""),
    ("Énergie / locaux", "Locaux techniques (6 L.TECH)", "Baie 24U murale/sol", 6 - BAIES_42, 700, "2 L.TECH par niveau d'après les plans"),
    ("Énergie / locaux", "Locaux techniques", "Baie 42U 600x800 au sol", BAIES_42, 1200, "L.TECH dont la baie dépasse 22U (plan de câblage)"),
    ("Énergie / locaux", "Salle serveur", "Onduleur APC Smart-UPS SRT 6 kVA (en ligne)", 2, 4800, "Alimentation A/B"),
    ("Énergie / locaux", "Locaux techniques", "Onduleur 1,5 kVA rackable", 6, 900, ""),
    ("Énergie / locaux", "Salle serveur", "PDU managées et métrées", 4, 700, "Mesure de consommation (Green IT)"),
    ("Énergie / locaux", "Salle serveur", "Climatisation de précision ~7 kW, redondance N+1", 1, 12000, ""),
    ("Énergie / locaux", "Salle serveur + L.TECH", "Contrôle d'accès par badge", 1, 5000, ""),
] + [
    (l["categorie"], l["schema"], l["solution"], l["quantite"], l["pu_ht"], l["note"] + " (point 14)") for l in (ENERGIE or {}).get("capex_nouveaux", [])
] + [
    ("Câblage", "Prises", "Prise RJ45 Cat6A fournie, posée et recettée", NB_PRISES, 140,
     "10 Gb/s, durée de vie 15 ans (CdC). Usagers + bornes + caméras + badgeuses (plan de câblage)"),
    ("Câblage", "Rocades", "Fibre OM4 12 brins L.TECH vers salle serveur", NB_ROCADES, 1500,
     "2 câbles par local, par deux chemins disjoints (colonnes Nord et Sud)"),
] + [
    ("Câblage", "Chemins de câbles", f"Chemin de câbles fil {dim} mm, posé", round(m), PRIX_CHEMIN.get(dim.split()[0], 60),
     "Métré du plan de câblage (circulations et locaux)") for dim, m in sorted(CHEMINS.items())
] + [
    ("Câblage", "Optiques", "Modules SFP+/SFP28/QSFP compatibles et câbles DAC", 96, 70, "Optiques Cisco d'origine : x4 environ. v2 : +16 (Stormshield, WLC, DAC de réplication)"),
    ("Câblage", "Brassage", "Panneaux, cordons, passe-câbles", 1, 4000, "Forfait"),
    ("Prestations", "Intégration", "Ingénierie, intégration et configuration (jours)", 50, 650, "v2 : +5 j (3 clusters Proxmox, WLC, chaîne de journalisation)"),
    ("Prestations", "Recette", "Recette, documentation et formation (jours)", 10, 650, ""),
]
ALEAS = 0.10  # provision pour aléas

# OPEX annuel années 1 à 3 (licences sécurité/réseau incluses dans le CAPEX)
IT_KW, PUE, KWH = 3.5, 1.6, 0.20
OPEX = [
    ("Accès Internet FAI 1", "Fibre dédiée FTTO 1 Gb/s symétrique, GTR 4 h", 12 * 900),
    ("Accès Internet FAI 2", "Fibre dédiée 500 Mb/s, autre opérateur", 12 * 450),
    ("Interconnexion WAN", "VPN MPLS vers le site jumeau (Digne/Gap)", 12 * 700),
    ("Proxmox VE", "Souscription Standard : NM 2 nœuds x 2 sockets, DT et DMZ 4 nœuds x 1 socket, 550 €/socket", (2 * 2 + 4 * 1) * 550),
    ("Sauvegarde externalisée", "Stockage objet ~20 To hors site, verrouillage S3 Object Lock en mode conformité (hébergeur SecNumCloud)", 12 * 180),
] + ([
    ("Électricité", f"{IT_KW} kW IT x PUE {PUE} x 8 760 h x {KWH:.2f} €/kWh", round(IT_KW * PUE * 8760 * KWH)),
] if not ENERGIE else [(o["poste"], o["detail"], o["montant"]) for o in ENERGIE["opex"]]) + [
    ("Nom de domaine", "Domaine + DNS secondaire", 30),
]
# Renouvellements à partir de l'année 4
RENOUV = [
    ("FortiGuard UTP + FortiCare", "2 FortiGate 120G", 2 * 2100),
    ("Stormshield Premium UTM", "2 SN710", 2 * 1500),
    ("Cisco DNA Essentials / AP", f"~{NB_AL_SW + 14} switchs + {NB_BORNES} bornes", round(12000 * (NB_AL_SW + 14 + NB_BORNES) / 56)),
    ("Support matériel serveurs", "Extension garantie 9 serveurs (v1 : 16)", 9 * 400),
]

# Pistes d'optimisation (force de proposition)
OPTIM = [
    ("Cœur replié (collapsed core)", "Un seul bâtiment : fusionner distribution et cœur sur 2 C9500-48Y4C (SVL). Suppression de DL-SW1 à DL-SW4. "
     "Étudiée, non retenue : le cahier des charges demande 3 couches (audit NET-02).", 4 * 9500),
    ("Services libres pour NPS et DHCP", "Remplacer NPS et le DHCP Windows par FreeRADIUS et Kea (déjà utilisés pour les autres VRF) : seules les 2 VM AD "
     "restent sous Windows, soit 1 licence par nœud au lieu de 3.", 4 * 1100),
    ("Tarifs Éducation", "Remises éditeur Microsoft/Cisco/Fortinet pour l'enseignement supérieur (souvent -30 à -50 %).", None),
]


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

    with open(HERE / "estimation_infra.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter=";")
        w.writeheader(); w.writerows(rows)

    data = dict(capex_lignes=rows, par_categorie=cats, sous_total=sous_total, aleas=aleas, capex=capex,
                opex=[dict(poste=a, detail=b, montant=c) for a, b, c in OPEX], opex_total=opex,
                renouvellement=[dict(poste=a, detail=b, montant=c) for a, b, c in RENOUV], renouvellement_total=renouv,
                tco5=tco5, optimisations=[dict(piste=a, detail=b, economie=c) for a, b, c in OPTIM])
    (HERE / "estimation.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    e = lambda n: f"{n:,.0f} €".replace(",", " ")
    md = ["# Estimation budgétaire – Site de Marseille (version 2)", "",
          "Source : `architecture/Projet_Marseille_site.drawio`. Prix HT, prix revendeur constatés (neuf), novembre 2026. "
          "À confirmer par devis : ces montants servent à cadrer le budget.", "",
          "## Synthèse", "", "| Poste | Montant HT |", "|---|---:|"]
    md += [f"| {c} | {e(v)} |" for c, v in cats.items()]
    md += [f"| **Sous-total** | **{e(sous_total)}** |", f"| Aléas ({ALEAS:.0%}) | {e(aleas)} |",
           f"| **CAPEX total** | **{e(capex)}** |", f"| OPEX annuel (années 1 à 3) | {e(opex)} |",
           f"| Renouvellements annuels (dès l'année 4) | {e(renouv)} |", f"| **Coût total sur 5 ans (TCO)** | **{e(tco5)}** |", "",
           "## Détail CAPEX", "", "| Catégorie | Éléments du schéma | Solution proposée | Qté | PU HT | Total HT | Note |", "|---|---|---|---:|---:|---:|---|"]
    md += [f"| {r['categorie']} | {r['schema']} | {r['solution']} | {r['quantite']} | {e(r['pu_ht'])} | {e(r['total_ht'])} | {r['note']} |" for r in rows]
    md += ["", "## OPEX annuel", "", "| Poste | Détail | Montant/an |", "|---|---|---:|"]
    md += [f"| {a} | {b} | {e(c)} |" for a, b, c in OPEX]
    md += ["", "## Renouvellements (à partir de l'année 4)", "", "| Poste | Détail | Montant/an |", "|---|---|---:|"]
    md += [f"| {a} | {b} | {e(c)} |" for a, b, c in RENOUV]
    md += ["", "## Pistes d'optimisation", "", "| Piste | Détail | Économie CAPEX |", "|---|---|---:|"]
    md += [f"| {a} | {b} | {e(c) if c else 'variable'} |" for a, b, c in OPTIM]
    v1 = HERE.parent / "livrables" / "archives" / "v1_2026-11-15" / "chiffrage" / "estimation.json"
    if v1.exists():
        a = json.loads(v1.read_text(encoding="utf-8"))
        md += ["", "## Écarts avec la version 1 (audit du 15/11/2026)", "",
               "Détail par constat : `livrables/audit/traitement_audit.pdf`. Version 1 : `livrables/archives/v1_2026-11-15/chiffrage/`.", "",
               "| | v1 | v2 | Écart |", "|---|---:|---:|---:|"]
        for nom, k in (("CAPEX total", "capex"), ("OPEX annuel", "opex_total"), ("Renouvellements annuels", "renouvellement_total"), ("TCO 5 ans", "tco5")):
            md.append(f"| {nom} | {e(a[k])} | {e(data[k])} | {'+' if data[k] >= a[k] else '−'}{e(abs(data[k] - a[k]))} |")
        md += ["", "Principales causes : 12 serveurs physiques et 3 nœuds Ceph remplacés par 6 hyperviseurs et 2 témoins (−) ; contrôleurs Wi-Fi physiques, "
               "modules 10G du Stormshield, kits de pile, sauvegarde hors ligne (+) ; extinction automatique, plancher surélevé et batardeau (lot énergie, +)."]
    md += ["", "## Hypothèses de dimensionnement", "",
           "- Bâtiment IUT Génie Télécom (Luminy) : sous-sol, RDC, étage 1, 6 locaux techniques (plans `docs/plans_batiment/`).",
           (f"- {NB_PRISES} prises d'après le plan de câblage (`livrables/plan_cablage/`) : bureaux 2 par poste, salles de TP 1 par poste + 2, "
            f"salles de TD/cours/réunion 3, {NB_BORNES} bornes Wi-Fi (étude RSSI), 15 caméras IP, 11 badgeuses." if PLAN else
            "- ~400 prises : ~17 bureaux x 2, ~10 salles info/TP/réseaux x 24, ~12 salles TD/cours/réunion x 3, 30 bornes, ~15 caméras IP, ~10 badgeuses."),
           "- Postes clients, imprimantes, téléphones IP et caméras exclus (budget poste de travail à part).",
           "- La `cisco-price-list.pdf` du Drive date du début des années 2000 (gammes Aironet 340/350, VPN 3000) : elle n'est pas utilisable pour des prix actuels.",
           (f"- Électricité, onduleurs, climatisation : bilan du point 14 (`livrables/energie_refroidissement/`), PUE {ENERGIE['energie']['pue']}, "
            f"{ENERGIE['energie']['kwh']} kWh/an, {KWH:.2f} €/kWh HT." if ENERGIE else f"- Électricité : {IT_KW} kW de charge IT moyenne, PUE {PUE}, {KWH:.2f} €/kWh HT."), ""]
    (HERE / "estimation_infra.md").write_text("\n".join(md), encoding="utf-8")
    print(f"sous-total {sous_total}  aleas {aleas}  CAPEX {capex}  OPEX/an {opex}  renouv/an {renouv}  TCO5 {tco5}")
    for c, v in cats.items(): print(f"  {c:20s} {v}")


if __name__ == "__main__":
    main()
