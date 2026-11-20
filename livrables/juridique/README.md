# Aspects juridiques et chartes (point 19)
<!-- onglet: Juridique -->

Charte informatique, volet juridique (RGPD, journaux, IA, crise), PRA juridique et modèles de CCTP pour les marchés du client.

| Document | Réf. | Contenu |
|---|---|---|
| **[charte_informatique.pdf](charte_informatique.pdf)** | RLI-ETU-009 | Charte des utilisateurs, annexe A administrateurs, annexe B usage de l'IA |
| **[volet_juridique.pdf](volet_juridique.pdf)** | RLI-ETU-010 | Cadre légal, registre des traitements, AIPD (vidéoprotection, IA, géolocalisation), politique de journalisation, AI Act, gestion de crise (volet gouvernance du PRA), clauses reprises par les CCTP |
| **[pra_juridique.pdf](pra_juridique.pdf)** | RLI-ETU-011 | PRA, volet juridique : obligations de continuité, DMIA et PDMA par service (entrée du point 15), sauvegardes et continuité électrique qui les tiennent, garanties de rétablissement, contrats, calendrier légal des 72 premières heures |
| **[guide_cdc_cctp.pdf](guide_cdc_cctp.pdf)** | RLI-ETU-012 | Construire un cahier des charges et un CCTP ; les 5 lots |
| [cctp_lot1.pdf](cctp_lot1.pdf) | RLI-CCTP-001 | CCTP lot 1 : Câblage structuré et équipements actifs du réseau |
| [cctp_lot2.pdf](cctp_lot2.pdf) | RLI-CCTP-002 | CCTP lot 2 : Sécurité périmétrique : routeurs de bordure, pare-feu, VPN |
| [cctp_lot3.pdf](cctp_lot3.pdf) | RLI-CCTP-003 | CCTP lot 3 : Datacenter : serveurs, virtualisation, sauvegarde, plateforme d'IA |
| [cctp_lot4.pdf](cctp_lot4.pdf) | RLI-CCTP-004 | CCTP lot 4 : Sûreté : vidéoprotection et contrôle d'accès |
| [cctp_lot5.pdf](cctp_lot5.pdf) | RLI-CCTP-005 | CCTP lot 5 : Énergie et locaux techniques |

**Version 2.1 — 20/11/2026** : lot 5 « Énergie et locaux techniques » (groupe électrogène, inverseur de source, onduleurs, climatisation, extinction), garanties de rétablissement 4 h et J+1, conservation des journaux en deux classes (connexion 1 an, navigation 6 mois), enregistreur vidéo VS-NVR1 et caméra du foyer retirée, règle SecNumCloud unique, quantités des CCTP lues dans le chiffrage sans ses notes internes, charte commune ; changements repérés « v2.1 » dans les documents. Version précédente : `livrables/archives/v2_2026-11-20/`.

Régénérer : `python3 juridique/build.py` (sources : `juridique/donnees.py`, `pra.py`, `charte.py`, `cctp.py` ; entrées : `chiffrage/estimation.json`, `livrables/plan_cablage/resume.json`, `livrables/energie_refroidissement/resume.json`). Propositions du concepteur, à valider par le DPO et le service juridique de l'AMU.
