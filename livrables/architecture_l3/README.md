# Architecture de niveau 3 (points 03, 05 et 07)
<!-- onglet: Archi L3 -->

Document principal : **[architecture_l3.pdf](architecture_l3.pdf)** : VRF-lite, matrice des flux entre zones, OSPFv3 par VRF, routes statiques vers les pare-feu, zone tier 0, politique d'inspection et inspection TLS, eBGP double opérateur avec annonce conditionnelle, SD-WAN FortiGate, NAT et VIP, IPv6 (SLAAC/DHCPv6, NPTv6 de secours), MTU, journalisation légale, services IP, extraits de configuration, tests de bascule.

Schéma modifiable : `architecture/architecture_l3.drawio`. **Version 2** (après l'audit du 15/11/2026) : changements repérés « v2 » dans le document, détail par constat dans [`../audit/traitement_audit.pdf`](../audit/README.md). Version 1 : `livrables/archives/v1_2026-11-15/`.

Régénérer : `python3 architecture/reseau/build.py` (source unique : `architecture/reseau/donnees.py`).
