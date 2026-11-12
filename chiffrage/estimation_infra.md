# Estimation budgétaire – Site de Marseille

Source : `architecture/Projet_Marseille_site.drawio`. Prix HT, prix revendeur constatés (neuf), novembre 2026. À confirmer par devis : ces montants servent à cadrer le budget.

## Synthèse

| Poste | Montant HT |
|---|---:|
| Egress / WAN | 23 400 € |
| Sécurité interne | 14 000 € |
| DMZ | 22 000 € |
| Cœur | 19 000 € |
| Distribution | 38 000 € |
| Accès | 107 900 € |
| Net Management | 33 100 € |
| Datacenter | 61 000 € |
| Énergie / locaux | 57 000 € |
| Câblage | 118 805 € |
| Prestations | 35 750 € |
| **Sous-total** | **529 955 €** |
| Aléas (10%) | 52 996 € |
| **CAPEX total** | **582 951 €** |
| OPEX annuel (années 1 à 3) | 44 081 € |
| Renouvellements annuels (dès l'année 4) | 27 857 € |
| **Coût total sur 5 ans (TCO)** | **859 070 €** |

## Détail CAPEX

| Catégorie | Éléments du schéma | Solution proposée | Qté | PU HT | Total HT | Note |
|---|---|---|---:|---:|---:|---|
| Egress / WAN | EL-RTR1, EL-RTR2 | Cisco Catalyst C8200L-1N-4T + DNA Essentials 3 ans | 2 | 2 200 € | 4 400 € | Routeurs de bordure, 1 par FAI |
| Egress / WAN | EL-FGT1, EL-FGT2 | FortiGate 120G + bundle UTP / FortiCare Premium 3 ans | 2 | 7 200 € | 14 400 € | Cluster HA actif/passif, pare-feu externe |
| Egress / WAN | EL-SW1, EL-SW2 | Cisco Catalyst C9200L-24T-4X-E + DNA-E 3 ans | 2 | 2 300 € | 4 600 € |  |
| Sécurité interne | EL-SNS1, EL-SNS2 | Stormshield SN710 + Premium UTM Security Pack 3 ans | 2 | 7 000 € | 14 000 € | Pare-feu interne HA. Prix à confirmer par devis revendeur |
| DMZ | DM-SW1, DM-SW2 | Cisco Catalyst C9200L-24T-4X-E + DNA-E 3 ans | 2 | 2 300 € | 4 600 € |  |
| DMZ | DM-RP1/2 (Caddy), DM-DNS1, DM-WEB1, DM-MAIL1, DM-SRV1 | Dell PowerEdge R260 (Xeon E-2434, 32 Go, 2x960 Go SSD RAID1, double alim) | 6 | 2 900 € | 17 400 € | 6 serveurs physiques comme sur le schéma |
| Cœur | CL-SW1, CL-SW2 | Cisco Catalyst C9500-16X-E + DNA-E 3 ans + modules 40G SVL | 2 | 9 500 € | 19 000 € | StackWise Virtual |
| Distribution | DL-SW1 à DL-SW4 | Cisco Catalyst C9500-16X-E + DNA-E 3 ans | 4 | 9 500 € | 38 000 € | 2 blocs StackWise Virtual (le SVL impose la gamme 9500) |
| Accès | AL-SW1 à AL-SW4 | Cisco Catalyst C9200L-48P-4X-E PoE+ + DNA-E 3 ans | 15 | 3 900 € | 58 500 € | Le schéma en montre 4. Plan de câblage : 15 switchs pour 484 prises (+10 % de ports libres) et le budget PoE, répartis dans les 6 L.TECH |
| Accès | AL-AP1 | Borne Wi-Fi 6E Cisco CW9164I + licence DNA AP 3 ans | 38 | 1 300 € | 49 400 € | Nombre fixé par l'étude RSSI prédictive (≥ −67 dBm à 5 GHz, livrables/plan_cablage/wifi). Contrôleur 9800-CL en VM |
| Net Management | NM-SW1, NM-SW2 | Cisco Catalyst C9200L-24T-4X-E + DNA-E 3 ans | 2 | 2 300 € | 4 600 € |  |
| Net Management | NM-PVE1 à NM-PVE3 | Dell PowerEdge R660xs (2x Xeon Silver 4510, 256 Go, 4x1,92 To SSD Ceph, 2x25 GbE) | 3 | 9 500 € | 28 500 € | Cluster Proxmox HA : LXC Kea/chrony/DNS, VM Docker (LibreNMS, Grafana, syslog, snmptrapd), Teleport |
| Net Management | Services NM (LXC + Docker) | Kea, chrony, Bind/Unbound, LibreNMS, Grafana, rsyslog, snmptrapd, Teleport Community | 1 | 0 € | 0 € | Logiciels libres, 0 € de licence |
| Datacenter | DT-SW1, DT-SW2 | Cisco Catalyst C9300X-12Y-E (10/25G) + DNA-E 3 ans | 2 | 8 000 € | 16 000 € |  |
| Datacenter | DT-AD1/2, DT-RAD1/2, DT-DHCP1/2 | Dell PowerEdge R360 (Xeon E-2400, 64 Go, 2x960 Go SSD RAID1) | 6 | 3 400 € | 20 400 € | 6 serveurs physiques comme sur le schéma |
| Datacenter | Licences serveurs Windows | Windows Server 2025 Standard 16 cœurs (AD, DHCP, NPS/RADIUS) | 6 | 1 100 € | 6 600 € | Tarif public. Le tarif Éducation est nettement plus bas |
| Datacenter | Licences d'accès | CAL utilisateur Windows Server (tarif Éducation) | 600 | 10 € | 6 000 € | ~100 personnels + ~500 étudiants |
| Datacenter | DT-BKP1 | Serveur de sauvegarde Proxmox Backup Server (Dell R760xd2, ~100 To bruts) | 1 | 12 000 € | 12 000 € | Règle 3-2-1 avec copie externalisée (voir OPEX) |
| Énergie / locaux | Salle serveur | Baie 42U 800x1000 avec portes ventilées | 2 | 1 500 € | 3 000 € |  |
| Énergie / locaux | Locaux techniques (6 L.TECH) | Baie 24U murale/sol | 5 | 700 € | 3 500 € | 2 L.TECH par niveau d'après les plans |
| Énergie / locaux | Locaux techniques | Baie 42U 600x800 au sol | 1 | 1 200 € | 1 200 € | L.TECH dont la baie dépasse 22U (plan de câblage) |
| Énergie / locaux | Salle serveur | Onduleur APC Smart-UPS SRT 6 kVA (en ligne) | 2 | 4 800 € | 9 600 € | Alimentation A/B |
| Énergie / locaux | Locaux techniques | Onduleur 1,5 kVA rackable | 6 | 900 € | 5 400 € |  |
| Énergie / locaux | Salle serveur | PDU managées et métrées | 4 | 700 € | 2 800 € | Mesure de consommation (Green IT) |
| Énergie / locaux | Salle serveur | Climatisation de précision ~7 kW, redondance N+1 | 1 | 12 000 € | 12 000 € |  |
| Énergie / locaux | Salle serveur + L.TECH | Contrôle d'accès par badge | 1 | 5 000 € | 5 000 € |  |
| Énergie / locaux | Salle serveur | Pack batterie externe APC SRT192RMBP (1 par onduleur) | 2 | 1 400 € | 2 800 € | Autonomie si un onduleur tombe : 7.9 min sans pack, 24 min avec (point 14) |
| Énergie / locaux | Salle serveur + L.TECH | Tableau électrique informatique (TD-INFO) et circuits dédiés | 1 | 6 000 € | 6 000 € | 2 départs 32 A onduleurs, 2 départs clim, 6 départs 16 A L.TECH, protections différentielles (point 14) |
| Énergie / locaux | Salle serveur | Confinement d'allée froide (obturateurs, rideaux) | 1 | 1 200 € | 1 200 € | Green IT : -10 % sur la clim (point 14) |
| Énergie / locaux | Salle serveur + L.TECH | Sondes température/humidité et détection de fuite d'eau | 1 | 1 200 € | 1 200 € | Remontées dans LibreNMS ; fuite : salle au sous-sol (point 14) |
| Énergie / locaux | Salle serveur | Détection incendie raccordée au SSI + extincteurs CO2 | 1 | 1 500 € | 1 500 € | Sécurité minimale, sans extinction automatique (point 14) |
| Énergie / locaux | Locaux techniques | Extracteur d'air avec thermostat | 4 | 450 € | 1 800 € | Locaux les plus chargés ou les plus petits (point 14) |
| Câblage | Prises | Prise RJ45 Cat6A fournie, posée et recettée | 484 | 140 € | 67 760 € | 10 Gb/s, durée de vie 15 ans (CdC). Usagers + bornes + caméras + badgeuses (plan de câblage) |
| Câblage | Rocades | Fibre OM4 12 brins L.TECH vers salle serveur | 12 | 1 500 € | 18 000 € | 2 câbles par local, par deux chemins disjoints (colonnes Nord et Sud) |
| Câblage | Chemins de câbles | Chemin de câbles fil 100×50 mm, posé | 636 | 35 € | 22 260 € | Métré du plan de câblage (circulations et locaux) |
| Câblage | Chemins de câbles | Chemin de câbles fil 200×60 mm, posé | 17 | 45 € | 765 € | Métré du plan de câblage (circulations et locaux) |
| Câblage | Chemins de câbles | Chemin de câbles fil 300×100 mm, posé | 7 | 60 € | 420 € | Métré du plan de câblage (circulations et locaux) |
| Câblage | Optiques | Modules SFP+/SFP28/QSFP compatibles | 80 | 70 € | 5 600 € | Optiques Cisco d'origine : x4 environ |
| Câblage | Brassage | Panneaux, cordons, passe-câbles | 1 | 4 000 € | 4 000 € | Forfait |
| Prestations | Intégration | Ingénierie, intégration et configuration (jours) | 45 | 650 € | 29 250 € |  |
| Prestations | Recette | Recette, documentation et formation (jours) | 10 | 650 € | 6 500 € |  |

## OPEX annuel

| Poste | Détail | Montant/an |
|---|---|---:|
| Accès Internet FAI 1 | Fibre dédiée FTTO 1 Gb/s symétrique, GTR 4 h | 10 800 € |
| Accès Internet FAI 2 | Fibre dédiée 500 Mb/s, autre opérateur | 5 400 € |
| Interconnexion WAN | VPN MPLS vers le site jumeau (Digne/Gap) | 8 400 € |
| Proxmox VE | Souscription Standard, 3 nœuds x 2 sockets x 550 € | 3 300 € |
| Sauvegarde externalisée | Stockage objet ~20 To hors site | 1 440 € |
| Électricité du réseau | 61 557 kWh/an × 0.20 € (salle serveur, PUE 1.34, 6 locaux techniques) | 12 311 € |
| Maintenance de la climatisation | Contrat d'entretien, 2 unités | 900 € |
| Provision batteries d'onduleurs | Remplacement tous les 5 ans, lissé par an | 1 500 € |
| Nom de domaine | Domaine + DNS secondaire | 30 € |

## Renouvellements (à partir de l'année 4)

| Poste | Détail | Montant/an |
|---|---|---:|
| FortiGuard UTP + FortiCare | 2 FortiGate 120G | 4 200 € |
| Stormshield Premium UTM | 2 SN710 | 3 000 € |
| Cisco DNA Essentials / AP | ~29 switchs + 38 bornes | 14 357 € |
| Support matériel serveurs | Extension garantie 18 serveurs | 6 300 € |

## Pistes d'optimisation

| Piste | Détail | Économie CAPEX |
|---|---|---:|
| Cœur replié (collapsed core) | Un seul bâtiment : fusionner distribution et cœur dans le bloc CL-SW (SVL). Suppression de DL-SW1 à DL-SW4. | 38 000 € |
| Virtualiser DMZ et datacenter | Héberger DM-* et DT-* (hors sauvegarde) en VM sur 2 clusters Proxmox (un pour la DMZ, isolé). 12 serveurs remplacés par 3 nœuds supplémentaires. | 9 300 € |
| Tarifs Éducation | Remises éditeur Microsoft/Cisco/Fortinet pour l'enseignement supérieur (souvent -30 à -50 %). | variable |

## Hypothèses de dimensionnement

- Bâtiment IUT Génie Télécom (Luminy) : sous-sol, RDC, étage 1, 6 locaux techniques (plans `docs/plans_batiment/`).
- 484 prises d'après le plan de câblage (`livrables/plan_cablage/`) : bureaux 2 par poste, salles de TP 1 par poste + 2, salles de TD/cours/réunion 3, 38 bornes Wi-Fi (étude RSSI), 15 caméras IP, 11 badgeuses.
- Postes clients, imprimantes, téléphones IP et caméras exclus (budget poste de travail à part).
- La `cisco-price-list.pdf` du Drive date du début des années 2000 (gammes Aironet 340/350, VPN 3000) : elle n'est pas utilisable pour des prix actuels.
- Électricité, onduleurs, climatisation : bilan du point 14 (`livrables/energie_refroidissement/`), PUE 1.34, 61557 kWh/an, 0.20 €/kWh HT.
