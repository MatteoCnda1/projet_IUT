# Plan d'adressage IPv4 et IPv6 (point 05)
<!-- onglet: Adressage -->

VLAN, sous-réseaux IPv4 et IPv6, passerelles, interconnexions et adresses fixes du bâtiment, avec les tables qui en sont tirées.

| Document | Réf. | Contenu |
|---|---|---|
| **[plan_adressage.pdf](plan_adressage.pdf)** | RLI-ETU-003 | Principes, blocs attribués, table des VLAN et dimensionnement, interconnexions, adresses fixes, résumés par VRF, réserves |
| `vlans.csv` | — | 41 VLAN + 6 transits : VRF, IPv4, IPv6, passerelles, usage |
| `equipements.csv` | — | Adresses fixes des équipements (IPv4 et IPv6), transits, liens point à point, boucles |
| `interconnexions.csv` | — | Bloc public 139.124.112.0/24 et liens cœur-distribution |

IPv4 privé 10.13.0.0/16, public 139.124.112.0/24 (bloc AMU, à confirmer par la DSI), IPv6 2001:660:5402:4000::/52 (VLAN *n* → 2001:660:5402:4*nnn*::/64), 5 VRF (USR, IOT, GST, SRV, ADM) et une zone tier 0 (VLAN 310).

**Version 2.1 — 20/11/2026** : transits 1020 à 1090 remis dans leur /29, plage des bornes dans son /26, passerelles IPv6 en ::1, une adresse par onduleur, PDU et climatiseur, EL-RTR1/2 en VLAN 900, boucles dans le résumé ADM, ns2 publié, pool du VPN d'administration, VS-NVR1, groupe électrogène en VLAN GTB ; contrôle automatique de chaque adresse, repérés « v2.1 » dans le document (les changements de la v2, après l'audit du 15/11/2026, restent repérés « v2 » ; détail par constat dans [`../audit/traitement_audit.pdf`](../audit/traitement_audit.pdf)). Version précédente : `livrables/archives/v2_2026-11-20/`.

Régénérer : `python3 architecture/reseau/build.py` (source unique : `architecture/reseau/donnees.py` ; documents : `documents.py`, schémas : `schemas.py`).
