"""Source unique du plan d'adressage et de la segmentation (points 03 et 05).

Tout ce qui suit est repris par build.py pour produire :
  - livrables/plan_adressage/  (CSV des VLAN, sous-réseaux, équipements)
  - livrables/architecture_l2/ (VLAN, trunks, agrégats, STP, profils de ports)
  - livrables/architecture_l3/ (VRF, routage, NAT, pare-feu, IPv6)
  - la zone Net Management du schéma architecture/Projet_Marseille_site.drawio

Conventions
-----------
IPv4 privé : 10.13.0.0/16 (13 = Bouches-du-Rhône). Site jumeau : 10.4.0.0/16 (Digne) réservé.
IPv4 public : 139.124.112.0/24, pris dans le bloc AMU 139.124.0.0/16 (affectation fictive, à demander à la DSI AMU).
IPv6 : 2001:660:5402:4000::/52, pris dans le /48 de Luminy 2001:660:5402::/48 (bloc AMU 2001:660:5400::/40, AS2457).
       Un /64 par VLAN : le 4e groupe vaut « 4 » suivi du numéro de VLAN (VLAN 112 -> 2001:660:5402:4112::/64).
       Les numéros de VLAN n'utilisent que des chiffres décimaux, donc le préfixe se lit directement.
       Blocs réservés : 4000::/64 boucles locales, 4Fxx::/64 liens d'interconnexion (/127 sur les liens point à point).
Numéro de VLAN : 1er chiffre = zone (1 bloc 1, 2 bloc 2, 3 datacenter, 4 DMZ, 9 administration),
                 2e chiffre = VRF dans un bloc (1 USR, 2 IOT, 3 GST, 9 ADM). D'où des résumés IPv6 en /60 par VRF et par bloc.
Passerelle : toujours la première adresse (.1 / ::1). Les équipements ont la même terminaison en IPv4 et en IPv6
             (10.13.59.41 <-> 2001:660:5402:4904::41) pour se repérer facilement.
"""
import ipaddress as ip

V6 = "2001:660:5402:"
P6_SITE = ip.ip_network("2001:660:5402:4000::/52")
P4_PRIVE = ip.ip_network("10.13.0.0/16")
P4_PUBLIC = ip.ip_network("139.124.112.0/24")

# ---------------------------------------------------------------------------
# VRF (VRF-lite sur le cœur et la distribution : aucune route entre VRF, tout passe par le Stormshield)
# ---------------------------------------------------------------------------
VRF = {
    "USR": {"id": 10, "nom": "Utilisateurs", "couleur": "#0079b5",
            "role": "Personnel, étudiants, téléphonie, impression, Wi-Fi authentifié (802.1X)"},
    "IOT": {"id": 20, "nom": "Objets", "couleur": "#a75c00",
            "role": "Caméras IP, badgeuses, GTB : aucun accès Internet, flux limités à leurs serveurs"},
    "GST": {"id": 30, "nom": "Invités", "couleur": "#97549b",
            "role": "Wi-Fi invités : Internet seulement (HTTP/HTTPS/DNS), isolation entre clients"},
    "SRV": {"id": 40, "nom": "Serveurs", "couleur": "#008889",
            "role": "Datacenter : AD, RADIUS, DHCP, sauvegarde"},
    "ADM": {"id": 90, "nom": "Administration", "couleur": "#c13c3b",
            "role": "Gestion des équipements, IPMI, Proxmox, services d'infrastructure, postes d'admin (ANSSI : SI d'administration dédié)"},
}

# ---------------------------------------------------------------------------
# VLAN
# cle : id -> (nom, vrf, IPv4, passerelle, où vit le VLAN, routé, DHCP, usage)
# « passerelle » : DL-B1 / DL-B2 (blocs de distribution StackWise Virtual), CL (cœur), FGT (FortiGate), aucune
# ---------------------------------------------------------------------------
def _bloc(n, base):
    b = f"10.13.{base}"
    o = lambda k: f"10.13.{base + k}"
    gw = f"DL-B{n}"
    return [
        (n * 100 + 10, f"PERS-B{n}", "USR", f"{o(2)}.0/24", gw, "Postes fixes du personnel (802.1X, VLAN donné par RADIUS)"),
        (n * 100 + 11, f"ETU-B{n}", "USR", f"{b}.0/23", gw, "Postes des salles de TP et des étudiants (802.1X)"),
        (n * 100 + 12, f"VOIX-B{n}", "USR", f"{o(3)}.0/25", gw, "Téléphones IP (voice VLAN, LLDP-MED, DSCP EF)"),
        (n * 100 + 13, f"IMPR-B{n}", "USR", f"{o(3)}.128/26", gw, "Imprimantes et copieurs (MAB, adresses réservées)"),
        (n * 100 + 14, f"WIFI-PERS-B{n}", "USR", f"{o(8)}.0/23", gw, "SSID AMU-Personnel (WPA3-Entreprise)"),
        (n * 100 + 15, f"WIFI-ETU-B{n}", "USR", f"{o(4)}.0/22", gw, "SSID AMU-Etudiants et eduroam (WPA3-Entreprise)"),
        (n * 100 + 20, f"CAM-B{n}", "IOT", f"{o(12)}.0/26", gw, "Caméras IP (MAB + profilage, vers l'enregistreur seulement)"),
        (n * 100 + 21, f"BADGE-B{n}", "IOT", f"{o(12)}.64/27", gw, "Lecteurs de badge (MAB, vers le serveur de contrôle d'accès)"),
        (n * 100 + 22, f"GTB-B{n}", "IOT", f"{o(12)}.96/27", gw, "Gestion technique du bâtiment (réservé)"),
        (n * 100 + 30, f"INVITES-B{n}", "GST", f"{o(14)}.0/23", gw, "SSID AMU-Invites (portail captif, isolation client)"),
        (n * 100 + 90, f"GEST-ACC-B{n}", "ADM", f"{o(13)}.0/26", gw, "Gestion des switchs d'accès et de distribution du bloc"),
        (n * 100 + 91, f"AP-B{n}", "ADM", f"{o(13)}.64/26", gw, "Bornes Wi-Fi (CAPWAP vers le contrôleur, FlexConnect)"),
    ]


VLAN_BRUTS = _bloc(1, 16) + _bloc(2, 32) + [
    (300, "SRV-INFRA", "SRV", "10.13.48.0/24", "CL", "Serveurs du datacenter : AD, DHCP, RADIUS, sauvegarde"),
    (400, "DMZ-FRONT", "DMZ", "172.16.13.0/27", "FGT", "Reverse proxies Caddy, DNS public, messagerie (publiés par VIP)"),
    (401, "DMZ-BACK", "DMZ", "172.16.13.32/27", "FGT", "Applications derrière Caddy (site web, serveur applicatif)"),
    (402, "DMZ-GEST", "DMZ", "172.16.13.64/27", "FGT", "Gestion des switchs et iDRAC de la DMZ"),
    (900, "GEST-RESEAU", "ADM", "10.13.56.0/24", "CL", "Interfaces de gestion : cœur, pare-feu, switchs EL/DT/NM, PDU, onduleurs, sondes"),
    (901, "NM-IPMI", "ADM", "10.13.57.0/24", "CL", "iDRAC de tous les serveurs (hors DMZ)"),
    (902, "NM-MGMT", "ADM", "10.13.58.0/27", "CL", "Administration des hyperviseurs Proxmox (GUI 8006, SSH) et du témoin"),
    (903, "NM-CLUSTER", "ADM", "10.13.58.32/28", None, "Corosync lien 0 et QDevice : non routé, latence faible"),
    (904, "NM-WORKLOAD", "ADM", "10.13.59.0/24", "CL", "VM et conteneurs de services : Kea, chrony, DNS, Teleport, supervision, WLC"),
    (905, "NM-REPL", "ADM", "10.13.58.48/30", None, "Réplication ZFS et migration à chaud : câble direct 25G entre les deux nœuds, non routé"),
    (906, "ADMIN-PAW", "ADM", "10.13.60.0/26", "CL", "Postes d'administration dédiés (accès aux équipements uniquement via Teleport)"),
    (998, "PARKING", None, None, None, "Ports inutilisés (désactivés), jamais routé"),
    (999, "NATIF-NUL", None, None, None, "VLAN natif des trunks : ne transporte rien (contre le VLAN hopping)"),
]

# VLAN de transit (L2 sur EL-SW, entre le cœur et le Stormshield ; puis entre les deux pare-feu)
TRANSITS = [
    # vlan, nom, vrf, IPv4, côté A (adresse), côté B (adresse), préfixe v6 (/64)
    (1010, "TR-USR", "USR", "10.13.2.0/29", ("CL", 1), ("EL-SNS", 2), "4F21"),
    (1020, "TR-IOT", "IOT", "10.13.2.8/29", ("CL", 9), ("EL-SNS", 10), "4F22"),
    (1030, "TR-GST", "GST", "10.13.2.16/29", ("CL", 17), ("EL-SNS", 18), "4F23"),
    (1040, "TR-SRV", "SRV", "10.13.2.24/29", ("CL", 25), ("EL-SNS", 26), "4F24"),
    (1090, "TR-ADM", "ADM", "10.13.2.32/29", ("CL", 33), ("EL-SNS", 34), "4F29"),
    (1100, "TR-FW", None, "10.13.3.0/29", ("EL-FGT", 1), ("EL-SNS", 2), "4F10"),
]

# Liens routés point à point cœur <-> distribution : un agrégat L3 par bloc, une sous-interface 802.1Q par VRF
P2P = []
for bloc, depart in ((1, 0), (2, 8)):
    for k, (vrf, tag) in enumerate((("USR", 1), ("IOT", 2), ("GST", 3), ("ADM", 9))):
        a = depart + 2 * k
        P2P.append({"bloc": bloc, "vrf": vrf, "sous_if": f"Po{100 + bloc}.{VRF[vrf]['id']}",
                    "v4": f"10.13.1.{a}/31", "cl4": f"10.13.1.{a}", "dl4": f"10.13.1.{a + 1}",
                    "v6": f"{V6}4F{2 + bloc}{tag}::/127", "cl6": f"{V6}4F{2 + bloc}{tag}::", "dl6": f"{V6}4F{2 + bloc}{tag}::1"})

BOUCLES = [  # Loopback0 (identifiant OSPF, source des flux de gestion : SNMP, syslog, TACACS)
    ("CL (CL-SW1/2)", "10.13.0.1/32", f"{V6}4000::1/128"),
    ("DL-B1 (DL-SW1/2)", "10.13.0.2/32", f"{V6}4000::2/128"),
    ("DL-B2 (DL-SW3/4)", "10.13.0.3/32", f"{V6}4000::3/128"),
]

# ---------------------------------------------------------------------------
# Public et WAN
# ---------------------------------------------------------------------------
PUBLIC = [
    # préfixe, usage, détail
    ("139.124.112.0/30", "Lien EL-RTR1 <-> FAI 1 (AMU / RENATER)", "PE opérateur .1, EL-RTR1 .2 · IPv6 2001:660:5402:4FF0::/127"),
    ("139.124.112.8/29", "OUT-A : EL-RTR1 <-> cluster FortiGate", "EL-RTR1 .9, FortiGate .14 · IPv6 2001:660:5402:4F00::/64 (::1 / ::e)"),
    ("139.124.112.16/29", "OUT-B : EL-RTR2 <-> cluster FortiGate", "EL-RTR2 .17, FortiGate .22 · IPv6 2001:660:5402:4F01::/64 (::1 / ::e)"),
    ("139.124.112.32/27", "Adresses publiées (VIP FortiGate vers la DMZ)", ".33 web (Caddy), .34 messagerie (MX), .35 DNS public (ns1), .36 VPN admin FortiGate"),
    ("139.124.112.64/28", "NAT sortant VRF USR", "PAT, journalisé (traçabilité, loi n° 2006-64)"),
    ("139.124.112.80/29", "NAT sortant VRF SRV et ADM", "Mises à jour des serveurs et des équipements"),
    ("139.124.112.88/29", "NAT sortant VRF GST", "Séparé des usagers : une plainte sur une IP invités ne vise pas le personnel"),
    ("139.124.112.96/27", "Réserve", ""),
    ("139.124.112.128/25", "Réserve", "Extensions, deuxième bâtiment"),
]
FAI2 = {"lien4": "203.0.113.0/30", "lien6": "2001:db8:ffff::/127", "pa6": "2001:db8:2000::/48", "as": "AS64496"}
AS_SITE = 65013  # AS privé du site (eBGP vers les deux opérateurs)

# ---------------------------------------------------------------------------
# Équipements (adresses fixes). Les terminaisons sont reprises en IPv6 dans le même VLAN.
# ---------------------------------------------------------------------------
HOTES = {
    300: [("Passerelle (SVI CL)", 1), ("DT-AD1", 11), ("DT-AD2", 12), ("DT-RAD1", 21), ("DT-RAD2", 22),
          ("DT-DHCP1", 31), ("DT-DHCP2", 32), ("DT-BKP1 (Proxmox Backup Server)", 41)],
    400: [("FortiGate (port DMZ)", 1), ("VIP Caddy (keepalived)", 10), ("DM-RP1 Caddy", 11), ("DM-RP2 Caddy", 12),
          ("DM-DNS1 (ns1)", 20), ("DM-MAIL1", 21)],
    401: [("FortiGate", 33), ("DM-RP1 Caddy", 41), ("DM-RP2 Caddy", 42), ("DM-WEB1", 51), ("DM-SRV1", 52)],
    402: [("FortiGate", 65), ("DM-SW (pile)", 66), ("iDRAC DM-RP1", 71), ("iDRAC DM-RP2", 72), ("iDRAC DM-DNS1", 73),
          ("iDRAC DM-WEB1", 74), ("iDRAC DM-MAIL1", 75), ("iDRAC DM-SRV1", 76)],
    900: [("Passerelle (SVI CL)", 1), ("EL-FGT1 (mgmt HA)", 13), ("EL-FGT2 (mgmt HA)", 14), ("EL-SNS1 (mgmt)", 15),
          ("EL-SNS2 (mgmt)", 16), ("EL-SW (pile)", 21), ("DT-SW (pile)", 23), ("NM-SW (pile)", 25),
          ("PDU A1 / B1 / A2 / B2", 41), ("Onduleurs SRT 6 kVA A / B", 45), ("Sondes salle serveur", 47), ("Climatiseurs 1 / 2", 48)],
    901: [("Passerelle (SVI CL)", 1), ("iDRAC NM-PVE1", 11), ("iDRAC NM-PVE2", 12), ("iDRAC DT-AD1", 21), ("iDRAC DT-AD2", 22),
          ("iDRAC DT-RAD1", 23), ("iDRAC DT-RAD2", 24), ("iDRAC DT-DHCP1", 25), ("iDRAC DT-DHCP2", 26), ("iDRAC DT-BKP1", 27)],
    902: [("Passerelle (SVI CL)", 1), ("NM-PVE1", 11), ("NM-PVE2", 12), ("NM-WITNESS", 13)],
    903: [("NM-WITNESS (corosync-qnetd)", 40), ("NM-PVE1", 41), ("NM-PVE2", 42)],
    905: [("NM-PVE1", 49), ("NM-PVE2", 50)],
    904: [("Passerelle (SVI CL)", 1), ("LXC Kea DHCP 1 (primaire)", 11), ("LXC Kea DHCP 2 (secondaire)", 12),
          ("LXC NTP 1 chrony", 21), ("LXC NTP 2 chrony", 22), ("LXC DNS interne 1 (Unbound)", 31), ("LXC DNS interne 2 (Unbound)", 32),
          ("VIP Teleport (keepalived)", 40), ("LXC Teleport 1", 41), ("LXC Teleport 2", 42),
          ("VM supervision Docker (LibreNMS, snmptrapd, syslog, Grafana)", 50), ("VM contrôleur Wi-Fi C9800-CL", 60)],
    906: [("Passerelle (SVI CL)", 1), ("Postes d'administration (Kea, réservations)", "11-30")],
}
# VLAN de bloc : passerelle .1 (SVI sur le bloc StackWise Virtual), équipements de gestion dans GEST-ACC
for n in (1, 2):
    HOTES[n * 100 + 90] = [(f"Passerelle DL-B{n} (SVI)", 1), (f"DL-SW{2 * n - 1}/{2 * n} (SVL, gestion)", 2),
                           (f"AL-SW du bloc {n} (1 par switch d'accès)", "11-30")]
    HOTES[n * 100 + 91] = [(f"Passerelle DL-B{n} (SVI)", 1), ("Bornes CW9164I (Kea, option 43 vers le WLC)", "11-62")]

# Réseaux Net Management, dans l'ordre du schéma (nom court, VLAN, couleur du trait)
NM_RESEAUX = [
    ("ipmi", 901, "#C2185B"),
    ("mgmt", 902, "#00897B"),
    ("cluster", 903, "#6D727B"),
    ("workload", 904, "#0097A7"),
    ("replication", 905, "#7B1FA2"),
]

# ---------------------------------------------------------------------------
# Fonctions utiles
# ---------------------------------------------------------------------------

def v6_vlan(vid):
    return f"{V6}4{vid:03d}::/64"


def adresse(vid, fin):
    """Adresse d'un hôte : terminaison décimale reprise telle quelle dans l'IID IPv6."""
    v = VLANS[vid]
    if not v["v4"]:
        return None, None
    net = ip.ip_network(v["v4"])
    a4 = str(net.network_address + (int(fin) if str(fin).isdigit() else 0))
    a6 = f"{V6}4{vid:03d}::{fin}" if v["v6"] else None
    return a4, a6


VLANS = {}
for vid, nom, vrf, v4, gw, usage in VLAN_BRUTS:
    net = ip.ip_network(v4) if v4 else None
    routable = net is not None and gw is not None
    v6 = None
    if net is not None and vid not in (903, 905):  # cluster et réplication : IPv4 seulement (non routés, liens internes)
        v6 = v6_vlan(vid)
    VLANS[vid] = {"id": vid, "nom": nom, "vrf": vrf, "v4": v4, "gw_eq": gw, "usage": usage,
                  "gw4": str(net.network_address + 1) if routable else None,
                  "v6": v6, "gw6": f"{V6}4{vid:03d}::1" if (v6 and routable) else None,
                  "taille": net.num_addresses - 2 if net else None}
for vid, nom, vrf, v4, a, b, p6 in TRANSITS:
    net = ip.ip_network(v4)
    VLANS[vid] = {"id": vid, "nom": nom, "vrf": vrf, "v4": v4, "gw_eq": None, "usage": f"Transit {a[0]} <-> {b[0]}",
                  "gw4": None, "v6": f"{V6}{p6}::/64", "gw6": None, "taille": net.num_addresses - 2,
                  "a": (a[0], str(net.network_address + a[1]), f"{V6}{p6}::{a[1]}"),
                  "b": (b[0], str(net.network_address + b[1]), f"{V6}{p6}::{b[1]}")}

DHCP = {"USR": "DT-DHCP1/2", "IOT": "Kea (réserv.)", "GST": "Kea (bail 2 h)", "ADM": "Kea", "SRV": "statique", "DMZ": "statique"}

# Résumés annoncés / routes statiques sur le Stormshield, par VRF
RESUMES = {
    "USR": ["10.13.16.0/21", "10.13.24.0/22", "10.13.32.0/21", "10.13.40.0/22",
            f"{V6}4110::/60", f"{V6}4210::/60"],
    "IOT": ["10.13.28.0/24", "10.13.44.0/24", f"{V6}4120::/60", f"{V6}4220::/60"],
    "GST": ["10.13.30.0/23", "10.13.46.0/23", f"{V6}4130::/60", f"{V6}4230::/60"],
    "SRV": ["10.13.48.0/22", f"{V6}4300::/60"],
    "ADM": ["10.13.29.0/24", "10.13.45.0/24", "10.13.56.0/21", f"{V6}4190::/60", f"{V6}4290::/60", f"{V6}4900::/60"],
}


def verifier():
    """Contrôles : pas de chevauchement, tout est dans les blocs prévus, résumés exacts."""
    nets = []
    for v in VLANS.values():
        if v["v4"]:
            nets.append((ip.ip_network(v["v4"]), v["nom"]))
    for p in P2P:
        nets.append((ip.ip_network(p["v4"]), p["sous_if"]))
    for _, n4, _ in BOUCLES:
        nets.append((ip.ip_network(n4), "boucle"))
    for i, (a, na) in enumerate(nets):
        for b, nb in nets[i + 1:]:
            assert not a.overlaps(b), f"chevauchement {na} {a} / {nb} {b}"
        assert a.subnet_of(P4_PRIVE) or a.subnet_of(ip.ip_network("172.16.13.0/24")), na
    for vrf, liste in RESUMES.items():
        for vid, v in VLANS.items():
            if v["vrf"] != vrf or not v["v4"] or vid >= 1000:
                continue
            assert any(ip.ip_network(v["v4"]).subnet_of(ip.ip_network(r)) for r in liste if ":" not in r), (vrf, v["nom"])
            if v["v6"]:
                assert any(ip.ip_network(v["v6"]).subnet_of(ip.ip_network(r)) for r in liste if ":" in r), (vrf, v["nom"])
    for v in VLANS.values():
        if v["v6"]:
            assert ip.ip_network(v["v6"]).subnet_of(P6_SITE), v["nom"]
    pubs = [ip.ip_network(p[0]) for p in PUBLIC]
    for i, a in enumerate(pubs):
        assert a.subnet_of(P4_PUBLIC)
        for b in pubs[i + 1:]:
            assert not a.overlaps(b)
    return True


if __name__ == "__main__":
    verifier()
    for vid in sorted(VLANS):
        v = VLANS[vid]
        print(f"{vid:5} {v['nom']:14} {str(v['vrf']):4} {str(v['v4']):17} {str(v['gw4']):14} {str(v['v6'])}")
