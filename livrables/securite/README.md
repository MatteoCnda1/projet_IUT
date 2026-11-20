# Sécurité des réseaux (point 09)
<!-- onglet: Sécurité -->

Politique de sécurité du réseau du bâtiment : flux autorisés entre zones, analyse de risque et PSSI.

| Document | Réf. | Contenu |
|---|---|---|
| **[matrice_flux.pdf](matrice_flux.pdf)** | RLI-ETU-006 | Matrice des flux entre zones : 71 règles détaillées, pare-feu, inspection, justification, ordre de déploiement, écarts avec l'architecture, tests de recette proposés. Tableur : `matrice_flux.csv` |
| **[analyse_risque.pdf](analyse_risque.pdf)** | RLI-ETU-007 | Analyse EBIOS RM allégée : valeurs métier, événements redoutés, sources de risque, écosystème, scénarios stratégiques, plan de traitement, risques non intentionnels et cartes des risques |
| **[pssi.pdf](pssi.pdf)** | RLI-ETU-008 | Politique de sécurité du SI du site : organisation, principes, mesures (biens, personnes, réseaux, énergie, IA), conformité aux 42 mesures du guide d'hygiène |

**Version 2.1 — 20/11/2026** : règles F56 à F70 (DNS, DHCP, CAPWAP, NUT, NTP, sauvegarde, bastion, alertes, groupe électrogène), ordre de déploiement contrôlé, écarts E2 à E4 intégrés, coupure électrique prolongée dans l'analyse de risque, mesures M-PHY-4 à M-PHY-6 dans la PSSI, journaux en deux durées (connexion 1 an, navigation 6 mois), repérés « v2.1 » dans les documents. Version précédente : `livrables/archives/v2_2026-11-20/`.

Régénérer : `python3 securite/build.py` (sources : `securite/flux.py`, `ebios.py`, `pssi.py`).
