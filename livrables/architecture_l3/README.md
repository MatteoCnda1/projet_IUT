# Architecture de niveau 3 (points 03, 05 et 07)
<!-- onglet: Archi L3 -->

Architecture de niveau 3 du bâtiment : VRF, routage, bordure, NAT, filtrage entre zones et services IP.

| Document | Réf. | Contenu |
|---|---|---|
| **[architecture_l3.pdf](architecture_l3.pdf)** | RLI-ETU-005 | VRF-lite et zone tier 0, matrice résumée des flux, OSPFv3 par VRF, routes statiques vers les pare-feu, politique d'inspection et inspection TLS, eBGP à deux opérateurs avec annonce conditionnelle, SD-WAN, NAT et VIP, IPv6 (SLAAC, DHCPv6, NPTv6 de secours), MTU, services IP, journalisation légale, extraits de configuration, tests de bascule |
| `architecture_l3.png` | — | Schéma de niveau 3 (modifiable : `architecture/architecture_l3.drawio`) |

**Version 2.1 — 20/11/2026** : transits corrigés, matrice résumée alignée sur le point 09 (VPN IKEv2, DNS des postes, sens du flux vidéo, NUT, DNS de la DMZ, mises à jour des contrôleurs de domaine), boucles dans le résumé ADM, ns2 publié, route IPv6 vers le /52, conservation des journaux en deux durées, test BGP reformulé, repérés « v2.1 » dans le document (les changements de la v2, après l'audit du 15/11/2026, restent repérés « v2 » ; détail par constat dans [`../audit/traitement_audit.pdf`](../audit/traitement_audit.pdf)). Version précédente : `livrables/archives/v2_2026-11-20/`.

Régénérer : `python3 architecture/reseau/build.py` (source unique : `architecture/reseau/donnees.py` ; documents : `documents.py`, schémas : `schemas.py`).
