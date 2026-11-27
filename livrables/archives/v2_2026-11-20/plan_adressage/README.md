# Plan d'adressage IPv4 et IPv6 (point 05)
<!-- onglet: Adressage -->

> **Archive de la version 2** (15/11/2026, après l'audit), figée le 20/11/2026 depuis le commit `7e1db0b`. Version en vigueur : `livrables/plan_adressage/` (v2.1). Sources de cette version : `architecture/archives/v2_2026-11-20/`. Les commandes « Régénérer » ci-dessous visent les scripts en vigueur, pas cette archive.

Document principal : **[plan_adressage.pdf](plan_adressage.pdf)**. Tables : `vlans.csv`, `equipements.csv`, `interconnexions.csv`.

| | |
|---|---|
| IPv4 privé | 10.13.0.0/16 (bloc 1 : 10.13.16.0/20, bloc 2 : 10.13.32.0/20, datacenter 10.13.48.0/22, tier 0 10.13.52.0/27, admin 10.13.56.0/21, Wi-Fi 10.13.64.0/18) |
| IPv4 public | 139.124.112.0/24 dans le bloc AMU 139.124.0.0/16 (à confirmer par la DSI) |
| IPv6 | 2001:660:5402:4000::/52 dans 2001:660:5402::/48 (Luminy) ; VLAN *n* → 2001:660:5402:4*nnn*::/64 |
| VLAN | 41 VLAN + 6 transits, 5 VRF (USR, IOT, GST, SRV, ADM) + zone tier 0 (VLAN 310) |

**Version 2** (après l'audit du 15/11/2026) : changements repérés « v2 » dans le document, détail par constat dans [`livrables/audit/traitement_audit.pdf`](../../../audit/traitement_audit.pdf) (partie v1 → v2). Version 1 : `livrables/archives/v1_2026-11-15/`.

Régénérer : `python3 architecture/reseau/build.py` (source unique : `architecture/reseau/donnees.py`).
