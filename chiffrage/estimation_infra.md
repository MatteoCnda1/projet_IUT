# Estimation budgétaire – Site de Marseille (version 2)

Source : `architecture/Projet_Marseille_site.drawio`. Prix HT, prix revendeur constatés (neuf), novembre 2026. À confirmer par devis : ces montants servent à cadrer le budget.

## Synthèse

| Poste | Montant HT |
|---|---:|
| Egress / WAN | 23 400 € |
| Sécurité interne | 16 400 € |
| DMZ | 14 600 € |
| Cœur | 19 000 € |
| Distribution | 38 000 € |
| Accès | 119 900 € |
| Net Management | 29 100 € |
| Datacenter | 60 050 € |
| Énergie / locaux | 71 900 € |
| Câblage | 119 925 € |
| Prestations | 39 000 € |
| **Sous-total** | **551 275 €** |
| Aléas (10%) | 55 128 € |
| **CAPEX total** | **606 403 €** |
| OPEX annuel (années 1 à 3) | 44 892 € |
| Renouvellements annuels (dès l'année 4) | 25 157 € |
| **Coût total sur 5 ans (TCO)** | **881 177 €** |

## Détail CAPEX

| Catégorie | Éléments du schéma | Solution proposée | Qté | PU HT | Total HT | Note |
|---|---|---|---:|---:|---:|---|
| Egress / WAN | EL-RTR1, EL-RTR2 | Cisco Catalyst C8200L-1N-4T + DNA Essentials 3 ans | 2 | 2 200 € | 4 400 € | Routeurs de bordure, 1 par FAI |
| Egress / WAN | EL-FGT1, EL-FGT2 | FortiGate 120G + bundle UTP / FortiCare Premium 3 ans | 2 | 7 200 € | 14 400 € | Cluster HA actif/passif, pare-feu externe. Inspection TLS incluse dans le bundle |
| Egress / WAN | EL-SW1, EL-SW2 | Cisco Catalyst C9200L-24T-4X-E + DNA-E 3 ans | 2 | 2 300 € | 4 600 € |  |
| Sécurité interne | EL-SNS1, EL-SNS2 | Stormshield SN710 + Premium UTM Security Pack 3 ans | 2 | 7 000 € | 14 000 € | Pare-feu interne HA. Prix à confirmer par devis revendeur |
| Sécurité interne | EL-SNS1, EL-SNS2 | Module d'extension 10G SFP+ pour SN710 | 2 | 1 200 € | 2 400 € | v2 (SEC-01) : raccordement direct au cœur en 2×10G. Prix à confirmer |
| DMZ | DM-SW1, DM-SW2 | Cisco Catalyst C9200L-24T-4X-E + DNA-E 3 ans | 2 | 2 300 € | 4 600 € |  |
| DMZ | DM-PVE1, DM-PVE2 | Dell PowerEdge R360 (Xeon E-2488 8 cœurs, 64 Go, 4x960 Go SSD ZFS, 2x10 GbE, double alim) | 2 | 4 200 € | 8 400 € | v2 (SYS-02) : cluster Proxmox de la DMZ (VM Caddy x2, DNS x2, web, mail, applicatif) au lieu de 6 serveurs physiques |
| DMZ | DM-WITNESS | Dell PowerEdge R260 entrée de gamme (Xeon E-2414, 16 Go, 2x480 Go SSD) | 1 | 1 600 € | 1 600 € | v2 : QDevice propre à la DMZ (aucun flux vers l'administration) |
| Cœur | CL-SW1, CL-SW2 | Cisco Catalyst C9500-16X-E + DNA-E 3 ans + modules 40G SVL | 2 | 9 500 € | 19 000 € | StackWise Virtual |
| Distribution | DL-SW1 à DL-SW4 | Cisco Catalyst C9500-16X-E + DNA-E 3 ans | 4 | 9 500 € | 38 000 € | 2 blocs StackWise Virtual (le SVL impose la gamme 9500) |
| Accès | AL-SW1 à AL-SW4 | Cisco Catalyst C9200L-48P-4X-E PoE+ + DNA-E 3 ans | 15 | 3 900 € | 58 500 € | Le schéma en montre 4. Plan de câblage : 15 switchs pour 484 prises (+10 % de ports libres) et le budget PoE, répartis dans les 6 L.TECH |
| Accès | AL-AP1 | Borne Wi-Fi 6E Cisco CW9164I + licence DNA AP 3 ans | 38 | 1 300 € | 49 400 € | Nombre fixé par l'étude RSSI prédictive (≥ −67 dBm à 5 GHz, livrables/plan_cablage/wifi) |
| Accès | WLC1, WLC2 | Contrôleur Wi-Fi Cisco Catalyst 9800-L-F (4x10G SFP+), HA SSO | 2 | 6 000 € | 12 000 € | v2 (NET-01) : bornes en mode local, itinérance sans coupure dans tout le bâtiment. Remplace la VM 9800-CL |
| Net Management | NM-SW1, NM-SW2 | Cisco Catalyst C9200L-24T-4X-E + DNA-E 3 ans | 2 | 2 300 € | 4 600 € |  |
| Net Management | NM-PVE1, NM-PVE2 | Dell PowerEdge R660xs (2x Xeon Silver 4510, 256 Go, 4x1,92 To SSD ZFS miroir, 2x25 GbE + carte 4x1G) | 2 | 9 800 € | 19 600 € | v2 (SYS-01) : 2 nœuds + témoin, ZFS répliqué en câble direct 25G (v1 : 3 nœuds Ceph). LXC Kea/chrony/DNS/Teleport/journaux, VM supervision |
| Net Management | NM-WITNESS | Dell PowerEdge R260 entrée de gamme (Xeon E-2414, 16 Go, 2x480 Go SSD) | 1 | 1 600 € | 1 600 € | v2 (SYS-01) : QDevice des clusters NM et DT, serveur NUT (arrêt ordonné) |
| Net Management | EL-SW, NM-SW, DM-SW | Kit de pile StackWise-80 C9200L (2 modules + câbles) | 3 | 1 100 € | 3 300 € | v2 : oubli de la v1 (piles prévues dans l'architecture L2) |
| Net Management | Services NM (LXC + Docker) | Kea, chrony, Unbound, LibreNMS, Grafana, Loki, rsyslog, snmptrapd, Teleport Community, NUT | 1 | 0 € | 0 € | Logiciels libres, 0 € de licence |
| Datacenter | DT-SW1, DT-SW2 | Cisco Catalyst C9300X-12Y-E (10/25G) + DNA-E 3 ans | 2 | 8 000 € | 16 000 € |  |
| Datacenter | DT-PVE1, DT-PVE2 | Dell PowerEdge R660xs (1x Xeon Silver 4514Y 16 cœurs, 128 Go, 4x1,92 To SSD ZFS, 4x25 GbE) | 2 | 8 500 € | 17 000 € | v2 (SYS-02) : cluster Proxmox tier 0 (VM AD x2, NPS x2, DHCP x2) au lieu de 6 serveurs physiques |
| Datacenter | Licences serveurs Windows | Windows Server 2025 Standard 16 cœurs (AD, DHCP, NPS/RADIUS) | 6 | 1 100 € | 6 600 € | 6 VM Windows ; 1 licence = 2 VM, 3 par nœud pour pouvoir tout porter sur un seul nœud. Tarif public (Éducation nettement plus bas) |
| Datacenter | Licences d'accès | CAL utilisateur Windows Server (tarif Éducation) | 600 | 10 € | 6 000 € | ~100 personnels + ~500 étudiants |
| Datacenter | DT-BKP1 | Serveur de sauvegarde Proxmox Backup Server (Dell R760xd2, ~100 To bruts) | 1 | 12 000 € | 12 000 € | Règle 3-2-1-1-0 : copie hors ligne et copie immuable externalisée (voir OPEX) |
| Datacenter | DT-BKP1 | Disque externe 24 To pour datastore amovible PBS | 3 | 550 € | 1 650 € | v2 (SEC-03) : copie hors ligne. Rotation hebdomadaire : 1 branché, 1 au coffre sur place, 1 hors site |
| Datacenter | DT-BKP1 | Coffre ignifuge pour supports de sauvegarde | 1 | 800 € | 800 € | v2 (SEC-03) : hors de la salle serveur |
| Énergie / locaux | Salle serveur | Baie 42U 800x1000 avec portes ventilées | 2 | 1 500 € | 3 000 € |  |
| Énergie / locaux | Locaux techniques (6 L.TECH) | Baie 24U murale/sol | 5 | 700 € | 3 500 € | 2 L.TECH par niveau d'après les plans |
| Énergie / locaux | Locaux techniques | Baie 42U 600x800 au sol | 1 | 1 200 € | 1 200 € | L.TECH dont la baie dépasse 22U (plan de câblage) |
| Énergie / locaux | Salle serveur | Onduleur APC Smart-UPS SRT 6 kVA (en ligne) | 2 | 4 800 € | 9 600 € | Alimentation A/B |
| Énergie / locaux | Locaux techniques | Onduleur 1,5 kVA rackable | 6 | 900 € | 5 400 € |  |
| Énergie / locaux | Salle serveur | PDU managées et métrées | 4 | 700 € | 2 800 € | Mesure de consommation (Green IT) |
| Énergie / locaux | Salle serveur | Climatisation de précision ~7 kW, redondance N+1 | 1 | 12 000 € | 12 000 € |  |
| Énergie / locaux | Salle serveur + L.TECH | Contrôle d'accès par badge | 1 | 5 000 € | 5 000 € |  |
| Énergie / locaux | Salle serveur | Pack batterie externe APC SRT192RMBP (1 par onduleur) | 2 | 1 400 € | 2 800 € | Autonomie si un onduleur tombe : 11.2 min sans pack, 33 min avec (point 14) |
| Énergie / locaux | Salle serveur + L.TECH | Tableau électrique informatique (TD-INFO) et circuits dédiés | 1 | 6 000 € | 6 000 € | 2 départs 32 A onduleurs, 2 départs clim, 6 départs 16 A L.TECH, protections différentielles (point 14) |
| Énergie / locaux | Salle serveur | Confinement d'allée froide (obturateurs, rideaux) | 1 | 1 200 € | 1 200 € | Green IT : -10 % sur la clim (point 14) |
| Énergie / locaux | Salle serveur + L.TECH | Sondes température/humidité et détection de fuite d'eau | 1 | 1 200 € | 1 200 € | Remontées dans LibreNMS ; fuite : salle au sous-sol (point 14) |
| Énergie / locaux | Salle serveur | Détection incendie raccordée au SSI + extincteurs CO2 | 1 | 1 500 € | 1 500 € | Report d'alarme au SSI du bâtiment (point 14) |
| Énergie / locaux | Salle serveur | Extinction automatique par gaz inerte (IG-541) + détection précoce par aspiration (VESDA) | 1 | 8 500 € | 8 500 € | v2 (audit SYS-03) : un incendie la nuit ne détruit plus la salle. Gaz inerte : sans danger pour le matériel (point 14) |
| Énergie / locaux | Salle serveur | Plancher technique surélevé 30 cm, baies et onduleurs sur socles | 25 | 160 € | 4 000 € | v2 (SYS-03) : matériel hors d'eau en cas d'inondation du sous-sol (prix au m²) (point 14) |
| Énergie / locaux | Salle serveur | Batardeau amovible à la porte (60 cm) + clapet anti-retour sur l'évacuation des condensats | 1 | 1 500 € | 1 500 € | v2 (SYS-03) : retarde l'entrée de l'eau par la circulation (point 14) |
| Énergie / locaux | Salle serveur | Câble de détection de fuite sous le plancher (centrale + 20 m) | 1 | 900 € | 900 € | v2 (SYS-03) : alerte dès les premiers centimètres, avant que l'eau n'atteigne le matériel (point 14) |
| Énergie / locaux | Locaux techniques | Extracteur d'air avec thermostat | 4 | 450 € | 1 800 € | Locaux les plus chargés ou les plus petits (point 14) |
| Câblage | Prises | Prise RJ45 Cat6A fournie, posée et recettée | 484 | 140 € | 67 760 € | 10 Gb/s, durée de vie 15 ans (CdC). Usagers + bornes + caméras + badgeuses (plan de câblage) |
| Câblage | Rocades | Fibre OM4 12 brins L.TECH vers salle serveur | 12 | 1 500 € | 18 000 € | 2 câbles par local, par deux chemins disjoints (colonnes Nord et Sud) |
| Câblage | Chemins de câbles | Chemin de câbles fil 100×50 mm, posé | 636 | 35 € | 22 260 € | Métré du plan de câblage (circulations et locaux) |
| Câblage | Chemins de câbles | Chemin de câbles fil 200×60 mm, posé | 17 | 45 € | 765 € | Métré du plan de câblage (circulations et locaux) |
| Câblage | Chemins de câbles | Chemin de câbles fil 300×100 mm, posé | 7 | 60 € | 420 € | Métré du plan de câblage (circulations et locaux) |
| Câblage | Optiques | Modules SFP+/SFP28/QSFP compatibles et câbles DAC | 96 | 70 € | 6 720 € | Optiques Cisco d'origine : x4 environ. v2 : +16 (Stormshield, WLC, DAC de réplication) |
| Câblage | Brassage | Panneaux, cordons, passe-câbles | 1 | 4 000 € | 4 000 € | Forfait |
| Prestations | Intégration | Ingénierie, intégration et configuration (jours) | 50 | 650 € | 32 500 € | v2 : +5 j (3 clusters Proxmox, WLC, chaîne de journalisation) |
| Prestations | Recette | Recette, documentation et formation (jours) | 10 | 650 € | 6 500 € |  |

## OPEX annuel

| Poste | Détail | Montant/an |
|---|---|---:|
| Accès Internet FAI 1 | Fibre dédiée FTTO 1 Gb/s symétrique, GTR 4 h | 10 800 € |
| Accès Internet FAI 2 | Fibre dédiée 500 Mb/s, autre opérateur | 5 400 € |
| Interconnexion WAN | VPN MPLS vers le site jumeau (Digne/Gap) | 8 400 € |
| Proxmox VE | Souscription Standard : NM 2 nœuds x 2 sockets, DT et DMZ 4 nœuds x 1 socket, 550 €/socket | 4 400 € |
| Sauvegarde externalisée | Stockage objet ~20 To hors site, verrouillage S3 Object Lock en mode conformité (hébergeur SecNumCloud) | 2 160 € |
| Électricité du réseau | 53 510 kWh/an × 0.20 € (salle serveur, PUE 1.34, 6 locaux techniques) | 10 702 € |
| Maintenance de la climatisation | Contrat d'entretien, 2 unités | 900 € |
| Provision batteries d'onduleurs | Remplacement tous les 5 ans, lissé par an | 1 500 € |
| Maintenance de l'extinction automatique | Visite annuelle obligatoire (APSAD R13), contrôle des bouteilles | 600 € |
| Nom de domaine | Domaine + DNS secondaire | 30 € |

## Renouvellements (à partir de l'année 4)

| Poste | Détail | Montant/an |
|---|---|---:|
| FortiGuard UTP + FortiCare | 2 FortiGate 120G | 4 200 € |
| Stormshield Premium UTM | 2 SN710 | 3 000 € |
| Cisco DNA Essentials / AP | ~29 switchs + 38 bornes | 14 357 € |
| Support matériel serveurs | Extension garantie 9 serveurs (v1 : 16) | 3 600 € |

## Pistes d'optimisation

| Piste | Détail | Économie CAPEX |
|---|---|---:|
| Cœur replié (collapsed core) | Un seul bâtiment : fusionner distribution et cœur sur 2 C9500-48Y4C (SVL). Suppression de DL-SW1 à DL-SW4. Étudiée, non retenue : le cahier des charges demande 3 couches (audit NET-02). | 38 000 € |
| Services libres pour NPS et DHCP | Remplacer NPS et le DHCP Windows par FreeRADIUS et Kea (déjà utilisés pour les autres VRF) : seules les 2 VM AD restent sous Windows, soit 1 licence par nœud au lieu de 3. | 4 400 € |
| Tarifs Éducation | Remises éditeur Microsoft/Cisco/Fortinet pour l'enseignement supérieur (souvent -30 à -50 %). | variable |

## Écarts avec la version 1 (audit du 15/11/2026)

Détail par constat : `livrables/audit/traitement_audit.pdf`. Version 1 : `livrables/archives/v1_2026-11-15/chiffrage/`.

| | v1 | v2 | Écart |
|---|---:|---:|---:|
| CAPEX total | 582 951 € | 606 403 € | +23 452 € |
| OPEX annuel | 44 081 € | 44 892 € | +811 € |
| Renouvellements annuels | 27 857 € | 25 157 € | −2 700 € |
| TCO 5 ans | 859 070 € | 881 177 € | +22 107 € |

Principales causes : 12 serveurs physiques et 3 nœuds Ceph remplacés par 6 hyperviseurs et 2 témoins (−) ; contrôleurs Wi-Fi physiques, modules 10G du Stormshield, kits de pile, sauvegarde hors ligne (+) ; extinction automatique, plancher surélevé et batardeau (lot énergie, +).

## Hypothèses de dimensionnement

- Bâtiment IUT Génie Télécom (Luminy) : sous-sol, RDC, étage 1, 6 locaux techniques (plans `docs/plans_batiment/`).
- 484 prises d'après le plan de câblage (`livrables/plan_cablage/`) : bureaux 2 par poste, salles de TP 1 par poste + 2, salles de TD/cours/réunion 3, 38 bornes Wi-Fi (étude RSSI), 15 caméras IP, 11 badgeuses.
- Postes clients, imprimantes, téléphones IP et caméras exclus (budget poste de travail à part).
- La `cisco-price-list.pdf` du Drive date du début des années 2000 (gammes Aironet 340/350, VPN 3000) : elle n'est pas utilisable pour des prix actuels.
- Électricité, onduleurs, climatisation : bilan du point 14 (`livrables/energie_refroidissement/`), PUE 1.34, 53510 kWh/an, 0.20 €/kWh HT.
