# Estimation budgétaire de l'infrastructure (point 18)

Site de Marseille · IUT Génie Télécom, Luminy · RudyLink Infrastructure · **v2.1 — 20/11/2026**

Source : `architecture/Projet_Marseille_site.drawio`, plan de câblage (point 04), énergie et refroidissement (point 14). Prix HT, prix revendeur constatés (neuf), novembre 2026. À confirmer par devis : ces montants servent à cadrer le budget.

## Synthèse

| Poste | Montant HT |
|---|---:|
| Egress / WAN | 23 400 € |
| Sécurité interne | 16 400 € |
| DMZ | 15 100 € |
| Cœur | 19 000 € |
| Distribution | 38 000 € |
| Accès | 119 900 € |
| Net Management | 29 100 € |
| Datacenter | 60 050 € |
| Énergie / locaux | 72 550 € |
| Énergie / secours | 32 000 € |
| Sûreté | 32 000 € |
| Câblage | 120 765 € |
| Prestations | 39 000 € |
| **Sous-total** | **617 265 €** |
| Aléas (10 %) | 61 726 € |
| **CAPEX total** | **678 991 €** |
| OPEX annuel (années 1 à 5, hors renouvellements) | 66 756 € |
| Renouvellements annuels (dès l'année 4) | 26 240 € |
| **Coût total sur 5 ans (TCO)** | **1 065 251 €** |

Coût sur 5 ans = CAPEX + 5 × OPEX + 2 × renouvellements. Lot énergie (Énergie / locaux + Énergie / secours) : 104 550 € HT ; lot sûreté : 32 000 € HT (hors aléas).

## Détail CAPEX

| Catégorie | Éléments du schéma | Solution proposée | Qté | PU HT | Total HT | Note |
|---|---|---|---:|---:|---:|---|
| Egress / WAN | EL-RTR1, EL-RTR2 | Cisco Catalyst C8200L-1N-4T + DNA Essentials 3 ans | 2 | 2 200 € | 4 400 € | Routeurs de bordure, 1 par FAI |
| Egress / WAN | EL-FGT1, EL-FGT2 | FortiGate 120G + bundle UTP / FortiCare Premium 3 ans | 2 | 7 200 € | 14 400 € | Cluster HA actif/passif, pare-feu externe. Inspection TLS incluse dans le bundle |
| Egress / WAN | EL-SW1, EL-SW2 | Cisco Catalyst C9200L-24T-4X-E + DNA-E 3 ans | 2 | 2 300 € | 4 600 € |  |
| Sécurité interne | EL-SNS1, EL-SNS2 | Stormshield SN710 + Premium UTM Security Pack 3 ans | 2 | 7 000 € | 14 000 € | Pare-feu interne HA. Prix à confirmer par devis revendeur |
| Sécurité interne | EL-SNS1, EL-SNS2 | Module d'extension 10G SFP+ pour SN710 | 2 | 1 200 € | 2 400 € | v2 (SEC-01) : raccordement direct au cœur en 2×10G. Prix à confirmer |
| DMZ | DM-SW1, DM-SW2 | Cisco Catalyst C9200L-24T-4X-E + DNA-E 3 ans | 2 | 2 300 € | 4 600 € |  |
| DMZ | DM-PVE1, DM-PVE2 | Dell PowerEdge R360 (Xeon E-2488 8 cœurs, 64 Go, 4 × 960 Go SSD ZFS, 4 × 10 GbE SFP+, double alim) | 2 | 4 450 € | 8 900 € | v2 (SYS-02) : cluster Proxmox de la DMZ (VM Caddy ×2, DNS ×2, web, mail, applicatif) au lieu de 6 serveurs physiques. v2.1 : 4 ports 10G (bond1 2×10G, réplication 10G DAC, 1 libre), carte 2 × 10G ajoutée (+250 €) |
| DMZ | DM-WITNESS | Dell PowerEdge R260 entrée de gamme (Xeon E-2414, 16 Go, 2 × 480 Go SSD) | 1 | 1 600 € | 1 600 € | v2 : QDevice propre à la DMZ (flux vers l'administration limités à la sauvegarde, aux journaux, à l'heure et à NUT) |
| Cœur | CL-SW1, CL-SW2 | Cisco Catalyst C9500-16X-E + DNA-E 3 ans + modules 40G SVL | 2 | 9 500 € | 19 000 € | StackWise Virtual |
| Distribution | DL-SW1 à DL-SW4 | Cisco Catalyst C9500-16X-E + DNA-E 3 ans + module 40G SVL (C9500-NM-2Q) | 4 | 9 500 € | 38 000 € | 2 blocs StackWise Virtual (gamme 9500 : la moins chère des gammes compatibles SVL, avec 9400 et 9600). v2.1 : module 40G nommé, compris dans le prix comme pour le cœur |
| Accès | AL-SW1 à AL-SW15 | Cisco Catalyst C9200L-48P-4X-E PoE+ + DNA-E 3 ans | 15 | 3 900 € | 58 500 € | Plan de câblage : 15 switchs pour 483 prises (+10 % de ports libres) et le budget PoE, répartis dans les 6 L.TECH (le schéma de site n'en montre que 4, à titre de principe) |
| Accès | AP-N-1-01 à AP-N1-16 | Borne Wi-Fi 6E Cisco CW9164I + licence DNA AP 3 ans | 38 | 1 300 € | 49 400 € | Nombre fixé par l'étude RSSI prédictive (≥ −67 dBm à 5 GHz, livrables/plan_cablage/wifi/bornes.csv) |
| Accès | WLC1, WLC2 | Contrôleur Wi-Fi Cisco Catalyst 9800-L-F (4 × 10G SFP+), HA SSO | 2 | 6 000 € | 12 000 € | v2 (NET-01) : bornes en mode local, itinérance sans coupure dans tout le bâtiment. Remplace la VM 9800-CL |
| Net Management | NM-SW1, NM-SW2 | Cisco Catalyst C9200L-24T-4X-E + DNA-E 3 ans | 2 | 2 300 € | 4 600 € |  |
| Net Management | NM-PVE1, NM-PVE2 | Dell PowerEdge R660xs (2 × Xeon Silver 4510, 256 Go, 4 × 1,92 To SSD ZFS miroir, 2 × 25 GbE + carte 4 × 1G) | 2 | 9 800 € | 19 600 € | v2 (SYS-01) : 2 nœuds + témoin, ZFS répliqué en câble direct 25G (v1 : 3 nœuds Ceph). LXC Kea/chrony/DNS/Teleport/journaux, VM supervision |
| Net Management | NM-WITNESS | Dell PowerEdge R260 entrée de gamme (Xeon E-2414, 16 Go, 2 × 480 Go SSD) | 1 | 1 600 € | 1 600 € | v2 (SYS-01) : QDevice des clusters NM et DT, serveur NUT (arrêt ordonné) |
| Net Management | EL-SW, NM-SW, DM-SW | Kit de pile StackWise-80 C9200L (2 modules + câbles) | 3 | 1 100 € | 3 300 € | v2 : oubli de la v1 (piles prévues dans l'architecture L2) |
| Net Management | Services NM (LXC + Docker) | Kea, chrony, Unbound, LibreNMS, Grafana, Loki, rsyslog, snmptrapd, Teleport Community, NUT | 1 | 0 € | 0 € | Logiciels libres, 0 € de licence |
| Datacenter | DT-SW1, DT-SW2 | Cisco Catalyst C9300X-12Y-E (10/25G) + DNA-E 3 ans | 2 | 8 000 € | 16 000 € |  |
| Datacenter | DT-PVE1, DT-PVE2 | Dell PowerEdge R660xs (1 × Xeon Silver 4514Y 16 cœurs, 128 Go, 4 × 1,92 To SSD ZFS, 4 × 25 GbE) | 2 | 8 500 € | 17 000 € | v2 (SYS-02) : cluster Proxmox tier 0 (VM AD ×2, NPS ×2, DHCP ×2) au lieu de 6 serveurs physiques |
| Datacenter | Licences serveurs Windows | Windows Server 2025 Standard 16 cœurs (AD, DHCP, NPS/RADIUS) | 6 | 1 100 € | 6 600 € | 6 VM Windows ; 1 licence = 2 VM, 3 par nœud pour pouvoir tout porter sur un seul nœud. Tarif public (Éducation nettement plus bas) |
| Datacenter | Licences d'accès | CAL utilisateur Windows Server (tarif Éducation) | 600 | 10 € | 6 000 € | ~100 personnels + ~500 étudiants |
| Datacenter | DT-BKP1 | Serveur de sauvegarde Proxmox Backup Server (Dell R760xd2, ~100 To bruts) | 1 | 12 000 € | 12 000 € | Règle 3-2-1-1-0 : copie hors ligne et copie immuable externalisée (voir OPEX) |
| Datacenter | DT-BKP1 | Disque externe 24 To pour datastore amovible PBS | 3 | 550 € | 1 650 € | v2 (SEC-03) : copie hors ligne. Rotation hebdomadaire : 1 branché, 1 au coffre sur place, 1 hors site |
| Datacenter | DT-BKP1 | Coffre ignifuge pour supports de sauvegarde | 1 | 800 € | 800 € | v2 (SEC-03) : hors de la salle serveur |
| Énergie / locaux | Salle serveur | Baie 42U 800 × 1000 avec portes ventilées | 2 | 1 500 € | 3 000 € |  |
| Énergie / locaux | Locaux techniques (5 L.TECH) | Baie 24U murale/sol | 5 | 700 € | 3 500 € | 2 L.TECH par niveau d'après les plans |
| Énergie / locaux | Locaux techniques | Baie 42U 600 × 800 au sol | 1 | 1 200 € | 1 200 € | L.TECH dont la baie dépasse 22U (plan de câblage) |
| Énergie / locaux | Salle serveur | Onduleur APC Smart-UPS SRT 6 kVA (en ligne) | 2 | 4 800 € | 9 600 € | Alimentation A/B |
| Énergie / locaux | Locaux techniques | Onduleur 1,5 kVA rackable | 6 | 900 € | 5 400 € |  |
| Énergie / locaux | Salle serveur | PDU managées et métrées | 4 | 700 € | 2 800 € | Mesure de consommation (Green IT) |
| Énergie / locaux | Salle serveur | Climatiseur technique 7,1 kW (fonctionnement 24 h/24), 1 en marche + 1 en secours (N+1) | 2 | 6 000 € | 12 000 € | v2.1 : 2 unités, comme au point 14 (v2 : « climatisation de précision » forfaitaire, 1 × 12 000 €) ; les armoires de précision y sont une option écartée |
| Énergie / locaux | Salle serveur | Pack batterie externe APC SRT192RMBP (1 par onduleur) | 2 | 1 400 € | 2 800 € | Autonomie si un onduleur tombe : 10,6 min sans pack, 32 min avec (point 14) |
| Énergie / locaux | Salle serveur + L.TECH | Tableau électrique informatique (TD-INFO) et circuits dédiés | 1 | 6 800 € | 6 800 € | 2 départs 32 A onduleurs (différentiel type B), 2 départs 20 A clim (type F), 6 départs 20 A L.TECH, éclairage, prises, auxiliaires. v2.1 : différentiels adaptés (BET) (point 14) |
| Énergie / locaux | Salle serveur | Confinement d'allée froide (obturateurs, rideaux) | 1 | 1 200 € | 1 200 € | Green IT : −10 % sur la clim (point 14) |
| Énergie / locaux | Salle serveur + L.TECH | Sondes température/humidité et détection de fuite d'eau | 1 | 1 200 € | 1 200 € | Remontées dans LibreNMS ; fuite : salle au sous-sol (point 14) |
| Énergie / locaux | Salle serveur | Détection incendie raccordée au SSI + extincteurs CO2 | 1 | 1 500 € | 1 500 € | Report d'alarme au SSI du bâtiment (point 14) |
| Énergie / locaux | Salle serveur | Extinction automatique par gaz inerte (IG-541) + détection précoce par aspiration (VESDA) | 1 | 8 500 € | 8 500 € | v2 (audit SYS-03) : un incendie la nuit ne détruit plus la salle. Gaz inerte : sans danger pour le matériel (point 14) |
| Énergie / locaux | Salle serveur | Plancher technique surélevé 30 cm, baies et onduleurs sur socles | 25 | 160 € | 4 000 € | v2 (SYS-03) : matériel hors d'eau en cas d'inondation du sous-sol (prix au m²) (point 14) |
| Énergie / locaux | Salle serveur | Batardeau amovible à la porte (60 cm) + clapet anti-retour sur l'évacuation des condensats | 1 | 1 500 € | 1 500 € | v2 (SYS-03) : retarde l'entrée de l'eau par la circulation (point 14) |
| Énergie / locaux | Salle serveur | Câble de détection de fuite sous le plancher (centrale + 20 m) | 1 | 900 € | 900 € | v2 (SYS-03) : alerte dès les premiers centimètres, avant que l'eau n'atteigne le matériel (point 14) |
| Énergie / locaux | Locaux techniques | Extracteur d'air de gaine avec thermostat (150 ou 300 m³/h) | 3 | 450 € | 1 350 € | v2.1 : débit vérifié pour l'été par le BET (N0-LT01 150 m³/h, N0-LT02 300 m³/h, N1-LT01 300 m³/h) (point 14) |
| Énergie / locaux | Locaux techniques | Mini-split 2,5 kW froid (unité extérieure en toiture-terrasse) | 1 | 3 200 € | 3 200 € | v2.1 (BET) : N1-LT02 trop chaud en été sous la toiture, même avec un extracteur (point 14) |
| Énergie / locaux | Locaux techniques | Coffret électrique de L.TECH (différentiels 30 mA type A SI et F, prise détrompée de l'onduleur) | 6 | 350 € | 2 100 € | v2.1 (BET) : protections adaptées aux onduleurs et aux ventilateurs (point 14) |
| Énergie / secours | Extérieur, façade est | Groupe électrogène diesel 33 kVA ESP / 30 kVA PRP, capoté insonorisé, cuve double paroi 250 l, démarrage automatique | 1 | 17 500 € | 17 500 € | v2.1 : le site n'a pas de groupe. Groupe 30 kVA capoté : 15 à 20 k€ HT fourni chez les distributeurs (ordre de grandeur) (point 14) |
| Énergie / secours | TD-INFO | Inverseur de source automatique 4P 63 A (NF EN 60947-6-1), coffret, reports d'état | 1 | 3 500 € | 3 500 € | v2.1 : bascule réseau / groupe en tête du tableau informatique. Appareil ≈ 1,5 à 2 k€, plus coffret, pose et mise en service (point 14) |
| Énergie / secours | Extérieur, façade est | Génie civil : dalle béton armé ≈ 3 × 2 m, fourreaux, clôture et portillon | 1 | 4 500 € | 4 500 € | v2.1 : ordre de grandeur d'entreprise de génie civil (point 14) |
| Énergie / secours | GE → TD-INFO, TGBT | Raccordement : câble 5G16 mm² (≈ 60 m) en fourreau, câble de commande, départ 4P 63 A au TGBT, circuit des auxiliaires du groupe | 1 | 4 000 € | 4 000 € | v2.1 : ≈ 40 €/m posé pour le câble de puissance, plus l'appareillage (point 14) |
| Énergie / secours | Groupe électrogène | Transport, levage, mise en service, essai de réception sur banc de charge (4 h), premier plein, formation | 1 | 2 500 € | 2 500 € | v2.1 : forfait installateur (point 14) |
| Sûreté | Caméras 14 (plan de câblage) | Caméra IP fixe PoE 802.3af, ONVIF profils S et T, 802.1X, posée, raccordée et réglée (masquage des zones privatives), panneaux d'information compris | 14 | 550 € | 7 700 € | v2.1 : lot 4 chiffré ; ordre de grandeur 400 à 700 € posée, à confirmer par devis. Aucune caméra au foyer des étudiants |
| Sûreté | VS-NVR1 | Licence VMS par caméra (perpétuelle, 3 ans de mises à jour) | 14 | 150 € | 2 100 € | v2.1 : ordre de grandeur 100 à 200 € par caméra, à confirmer par devis |
| Sûreté | VS-NVR1 | Enregistreur vidéo 2U, 8 × 8 To en RAID 6 (≈ 43 To utiles), logiciel VMS, 2 alimentations | 1 | 7 500 € | 7 500 € | v2.1 : baie 2 de la salle serveur. 30 jours d'images : 14 caméras × 4 Mb/s ≈ 18 To (36 To à 8 Mb/s). À confirmer par devis |
| Sûreté | Badgeuses 11 (plan de câblage) | Lecteur sans contact DESFire EV3 + UTL OSDP v2 (canal sécurisé), gâche ou ventouse, posés et raccordés | 11 | 1 200 € | 13 200 € | v2.1 : remplace le forfait v2 de 5 000 € (7 portes) ; ordre de grandeur 800 à 1 500 € par porte, à confirmer par devis |
| Sûreté | Contrôle d'accès | Logiciel de contrôle d'accès (licence serveur, VM du datacenter) | 1 | 1 500 € | 1 500 € | v2.1 : à confirmer par devis |
| Câblage | Prises | Prise RJ45 Cat6A fournie, posée et recettée | 483 | 140 € | 67 620 € | 10 Gb/s, durée de vie 15 ans (CdC). Usagers + bornes + caméras + badgeuses (plan de câblage) |
| Câblage | Rocades | Fibre OM4 12 brins L.TECH vers salle serveur | 12 | 1 500 € | 18 000 € | 2 câbles par local, par deux chemins distincts (colonnes Nord et Sud ; au sous-sol, deux circulations différentes) |
| Câblage | Chemins de câbles | Chemin de câbles fil 100×50 mm, posé | 628 | 35 € | 21 980 € | Métré du plan de câblage (circulations et locaux) |
| Câblage | Chemins de câbles | Chemin de câbles fil 200×60 mm, posé | 17 | 45 € | 765 € | Métré du plan de câblage (circulations et locaux) |
| Câblage | Chemins de câbles | Chemin de câbles fil 300×100 mm, posé | 7 | 60 € | 420 € | Métré du plan de câblage (circulations et locaux) |
| Câblage | Optiques | Modules SFP+/SFP28/QSFP compatibles et câbles DAC | 114 | 70 € | 7 980 € | v2.1 : décompte (60 optiques pour les Po1 des 15 switchs d'accès + 54 DAC et QSFP dans la salle serveur, v2 : 96 forfaitaires), à valider par l'équipe réseau. Optiques Cisco d'origine : environ ×4 |
| Câblage | Brassage | Panneaux, cordons, passe-câbles | 1 | 4 000 € | 4 000 € | Forfait |
| Prestations | Intégration | Ingénierie, intégration et configuration (jours) | 50 | 650 € | 32 500 € | v2 : +5 j (3 clusters Proxmox, WLC, chaîne de journalisation) |
| Prestations | Recette | Recette, documentation et formation (jours) | 10 | 650 € | 6 500 € |  |

## OPEX annuel (années 1 à 5)

| Poste | Détail | Montant/an |
|---|---|---:|
| Accès Internet FAI 1 | Fibre dédiée FTTO 1 Gb/s symétrique, GTR 4 h | 10 800 € |
| Accès Internet FAI 2 | Fibre dédiée 500 Mb/s, autre opérateur | 5 400 € |
| Interconnexion WAN | VPN MPLS vers le site jumeau (Digne/Gap) | 8 400 € |
| Proxmox VE | Souscription Standard : NM 2 nœuds × 2 sockets, DT et DMZ 4 nœuds × 1 socket, 550 €/socket | 4 400 € |
| Proxmox Backup Server | v2.1 : souscription Basic de DT-BKP1 (1 socket), à confirmer | 550 € |
| Sauvegarde externalisée | Stockage objet ~20 To hors site, verrouillage S3 Object Lock en mode conformité (hébergeur qualifié SecNumCloud, données dans l'UE) | 2 160 € |
| Support Cisco 24 h/24 7 j/7, remplacement sous 4 h (v2.1) | EL-RTR1/2 : 2 × 350 € ; CL-SW1/2, DL-SW1 à 4 : 6 × 1 200 € ; WLC1/2 : 2 × 600 € | 9 100 € |
| Fortinet : remplacement matériel sous 4 h, 24 h/24 7 j/7 (v2.1) | EL-FGT1/2 (en plus de FortiCare Premium) : 2 × 700 € | 1 400 € |
| Stormshield : échange sur site sous 4 h, 24 h/24 7 j/7 (v2.1) | EL-SNS1/2 : 2 × 600 € | 1 200 € |
| Dell : ProSupport Plus Mission Critical, intervention sous 4 h, 24 h/24 7 j/7 (v2.1) | DT-PVE1/2, NM-PVE1/2, DT-BKP1 : supplément sur la garantie de base : 5 × 750 € | 3 750 € |
| Électricité du réseau | 59 422 kWh/an × 0,20 € (salle serveur, PUE 1,45, 6 locaux techniques) | 11 884 € |
| Maintenance de la climatisation | v2.1 : 2 unités, 2 visites par an, dépannage 24 h/24 7 j/7 avec rétablissement en 4 h (astreinte 1 200 €) | 2 100 € |
| Maintenance des onduleurs de la salle | v2.1 : 2 APC SRT 6 kVA, contrat 24 h/24 7 j/7, intervention sur site en 4 h, une visite préventive par an (650 € par onduleur) | 1 300 € |
| Provision batteries d'onduleurs | Remplacement tous les 5 ans (salle) et tous les 4 ans (L.TECH, v2.1), lissé par an | 1 575 € |
| Maintenance de l'extinction automatique | Visite annuelle obligatoire (APSAD R13), contrôle des bouteilles | 600 € |
| Maintenance du groupe électrogène et de l'inverseur | v2.1 : contrat de 2 visites par an (vidange, filtres, liquide, batterie de démarrage, contrôle de l'inverseur) | 1 100 € |
| Essai annuel du groupe sur banc de charge | v2.1 : location du banc et technicien, 2 h à 75 % de la PRP | 700 € |
| Gazole du groupe électrogène | v2.1 : 55 l/an × 1,40 € (essais mensuels, banc, coupures) + analyse et traitement du gazole | 157 € |
| Maintenance du mini-split des L.TECH | v2.1 : visite annuelle (filtres, contrôle d'étanchéité) | 150 € |
| Nom de domaine | Domaine + DNS secondaire | 30 € |

Support des équipements critiques (v2.1) : rétablissement en 4 h, 24 h/24 7 j/7, pour les routeurs EL-RTR, les pare-feu EL-FGT et EL-SNS, le cœur CL-SW, la distribution DL-SW, les WLC, les hyperviseurs DT-PVE et NM-PVE, DT-BKP1, les onduleurs et les climatiseurs de la salle : 15 450 € HT/an (réseau et serveurs) + 3 400 € HT/an (lot énergie). Le reste (accès AL-SW, bornes, DMZ, objets) : J+1 ouvré, garanties constructeur. Prix des contrats en ordre de grandeur, à confirmer par devis.

## Renouvellements (à partir de l'année 4)

| Poste | Détail | Montant/an |
|---|---|---:|
| FortiGuard UTP + FortiCare | 2 FortiGate 120G | 4 200 € |
| Stormshield Premium UTM | 2 SN710 | 3 000 € |
| Cisco DNA Essentials / AP | v2.1 : 15 switchs d'accès × 220 € + 14 switchs de la salle × 500 € + 38 bornes × 90 € + 2 routeurs × 300 € (v2 : 12 000 € × switchs et bornes / 56, base non documentée) | 14 320 € |
| Support matériel serveurs | Extension de garantie J+1 de 9 serveurs × 400 € (v1 : 16 serveurs, comptés 18 × 350 €) | 3 600 € |
| Sûreté (lot 4) | v2.1 : mises à jour du VMS (14 caméras × 30 €), du logiciel de contrôle d'accès (400 €), extension de garantie du VS-NVR1 (300 €) | 1 120 € |

## Pistes d'optimisation

| Piste | Détail | Économie CAPEX |
|---|---|---:|
| Cœur replié (collapsed core) | Un seul bâtiment : fusionner distribution et cœur sur 2 C9500-48Y4C (SVL). Suppression de DL-SW1 à DL-SW4. Étudiée, non retenue : le cahier des charges demande 3 couches (audit NET-02). Économie brute : le surcoût des deux C9500-48Y4C par rapport aux C9500-16X du cœur est à déduire (non chiffré). | jusqu'à 38 000 € (brut) |
| Services libres pour NPS et DHCP | Remplacer NPS et le DHCP Windows par FreeRADIUS et Kea (déjà utilisés pour les autres VRF) : seules les 2 VM AD restent sous Windows, soit 1 licence par nœud au lieu de 3. | 4 400 € |
| Tarifs Éducation | Remises éditeur Microsoft/Cisco/Fortinet pour l'enseignement supérieur (souvent −30 à −50 %). | variable |

## Écarts avec la version 1 (audit du 15/11/2026)

Détail par constat : `livrables/audit/traitement_audit.pdf`. Version 1 : `livrables/archives/v1_2026-11-15/chiffrage/`.

| | v1 | v2.1 | Écart |
|---|---:|---:|---:|
| CAPEX total | 582 951 € | 678 991 € | +96 040 € |
| OPEX annuel | 44 081 € | 66 756 € | +22 675 € |
| Renouvellements annuels | 27 857 € | 26 240 € | −1 617 € |
| TCO 5 ans | 859 070 € | 1 065 251 € | +206 181 € |

Principales causes (v2) : 12 serveurs physiques et 3 nœuds Ceph remplacés par 6 hyperviseurs et 2 témoins (−) ; contrôleurs Wi-Fi physiques, modules 10G du Stormshield, kits de pile, sauvegarde hors ligne (+) ; extinction automatique, plancher surélevé et batardeau (lot énergie, +). Puis v2.1 : voir ci-dessous.

## Écarts avec la version 2 (15/11/2026)

Version 2 : `livrables/archives/v2_2026-11-20/`. Étude BET et groupe électrogène : `livrables/energie_refroidissement/bet_locaux_techniques.pdf`.

| | v2 | v2.1 | Écart |
|---|---:|---:|---:|
| Lot énergie (Énergie / locaux + Énergie / secours) | 71 900 € (dont 5 000 € de contrôle d'accès) | 104 550 € | +32 650 € |
| Lot sûreté (caméras, VMS, enregistreur, badgeuses) | 5 000 € (forfait, dans le lot énergie) | 32 000 € | +27 000 € |
| CAPEX total (aléas compris) | 606 403 € | 678 991 € | +72 588 € |
| OPEX annuel | 44 892 € | 66 756 € | +21 864 € |
| Renouvellements annuels | 25 157 € | 26 240 € | +1 083 € |
| TCO 5 ans | 881 177 € | 1 065 251 € | +184 074 € |

Causes : groupe électrogène 33 kVA ESP, inverseur de source, génie civil et raccordement (32 000 € HT) ; ventilation renforcée de trois L.TECH (mini-split, extracteurs 300 m³/h) et coffrets électriques ; OPEX : maintenance, essai sur banc et gazole du groupe, électricité recalculée (pertes réelles des onduleurs, auxiliaires, enregistreur vidéo) ; lot 4 chiffré : 14 caméras et leurs licences VMS, enregistreur VS-NVR1, 11 lecteurs de badge et UTL, logiciel de contrôle d'accès, au lieu du forfait de 5 000 € classé dans le lot énergie ; caméra du foyer retirée (15 → 14 caméras, 484 → 483 prises) ; optiques et DAC décomptés (96 → 114), carte 2 × 10G des DM-PVE ; support 24 h/24 7 j/7 en 4 h des équipements critiques (18 850 € HT/an), souscription Proxmox Backup Server ; renouvellement DNA par prix unitaires, mises à jour du lot sûreté.

## Hypothèses de dimensionnement

- Bâtiment IUT Génie Télécom (Luminy) : sous-sol, RDC, étage 1, 6 locaux techniques (plans `docs/plans_batiment/`).
- 483 prises d'après le plan de câblage (`livrables/plan_cablage/`) : bureaux 2 par poste, salles de TP 1 par poste + 2, salles de TD/cours/réunion 3, 38 bornes Wi-Fi (étude RSSI), 14 caméras IP, 11 badgeuses.
- Postes clients, imprimantes et téléphones IP exclus (budget poste de travail à part).
- Sûreté (lot 4, v2.1) : enregistrement continu, 30 jours au plus ; 14 caméras × 4 à 8 Mb/s = 18 à 36 To, couverts par les 43 To utiles de VS-NVR1. Prix en ordre de grandeur, à confirmer par devis. Le VMS n'est plus une VM du datacenter.
- La `cisco-price-list.pdf` (`docs/references_prix/`) date du début des années 2000 (gammes Aironet 340/350, VPN 3000) : elle n'est pas utilisable pour des prix actuels.
- Électricité, onduleurs, climatisation : bilan du point 14 (`livrables/energie_refroidissement/`), PUE 1,45, 59 422 kWh/an, 0,20 €/kWh HT.
- Groupe électrogène (v2.1) : le site n'en a pas (confirmé par le client). Groupe diesel 33 kVA ESP / 30 kVA PRP et inverseur automatique en tête du tableau informatique, prix en ordre de grandeur (distributeurs, installateurs), à confirmer par devis.
