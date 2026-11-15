# Architecture de niveau 2 (points 03 et 06)
<!-- onglet: Archi L2 -->

Document principal : **[architecture_l2.pdf](architecture_l2.pdf)** : VLAN par équipement, agrégats et trunks, piles et StackWise Virtual, Rapid PVST+, profils de ports 802.1X/MAB, sécurité L2, SSID et contrôleurs Wi-Fi, zone Net Management (2 nœuds Proxmox + témoin, réseaux ipmi / mgmt / cluster / workload / réplication), clusters DT et DMZ.

Schéma modifiable : `architecture/architecture_l2.drawio`. **Version 2** (après l'audit du 15/11/2026) : changements repérés « v2 » dans le document, détail par constat dans [`../audit/traitement_audit.pdf`](../audit/README.md). Version 1 : `livrables/archives/v1_2026-11-15/`.

Régénérer : `python3 architecture/reseau/build.py` (source unique : `architecture/reseau/donnees.py`).
