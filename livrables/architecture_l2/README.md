# Architecture de niveau 2 (points 03 et 06)
<!-- onglet: Archi L2 -->

Architecture de niveau 2 du bâtiment : VLAN, agrégats, piles, Spanning Tree, ports d'accès et zone Net Management.

| Document | Réf. | Contenu |
|---|---|---|
| **[architecture_l2.pdf](architecture_l2.pdf)** | RLI-ETU-004 | VLAN par équipement, agrégats et trunks, piles et StackWise Virtual, Rapid PVST+, profils de ports 802.1X et MAB, sécurité de niveau 2, SSID et contrôleurs Wi-Fi, zone Net Management (2 nœuds Proxmox et un témoin), clusters DT et DMZ, enregistreur vidéo |
| `architecture_l2.png`, `nm_zone.png` | — | Schéma de niveau 2 et zone Net Management (schémas modifiables : `architecture/architecture_l2.drawio`, `architecture/Projet_Marseille_site.drawio`) |

**Version 2.1 — 20/11/2026** : enregistreur vidéo physique VS-NVR1 (Po24), profil de port du groupe électrogène, ACL des caméras dans le sens enregistreur → caméra, flux de la DMZ vers l'intérieur décrits sans contradiction, collecteurs de journaux et NUT précisés, repérés « v2.1 » dans le document (les changements de la v2, après l'audit du 15/11/2026, restent repérés « v2 » ; détail par constat dans [`../audit/traitement_audit.pdf`](../audit/traitement_audit.pdf)). Version précédente : `livrables/archives/v2_2026-11-20/`.

Régénérer : `python3 architecture/reseau/build.py` (source unique : `architecture/reseau/donnees.py` ; documents : `documents.py`, schémas : `schemas.py`).
