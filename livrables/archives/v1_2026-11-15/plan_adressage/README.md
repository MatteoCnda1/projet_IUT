# Plan d'adressage IPv4 et IPv6 (point 05)
<!-- onglet: Adressage -->

Document principal : **[plan_adressage.pdf](plan_adressage.pdf)**. Tables : `vlans.csv`, `equipements.csv`, `interconnexions.csv`.

| | |
|---|---|
| IPv4 privé | 10.13.0.0/16 (bloc 1 : 10.13.16.0/20, bloc 2 : 10.13.32.0/20, datacenter 10.13.48.0/22, admin 10.13.56.0/21) |
| IPv4 public | 139.124.112.0/24 dans le bloc AMU 139.124.0.0/16 (à confirmer par la DSI) |
| IPv6 | 2001:660:5402:4000::/52 dans 2001:660:5402::/48 (Luminy) ; VLAN *n* → 2001:660:5402:4*nnn*::/64 |
| VLAN | 37 VLAN + 6 transits, 5 VRF (USR, IOT, GST, SRV, ADM) |

Régénérer : `python3 architecture/reseau/build.py` (source unique : `architecture/reseau/donnees.py`).
