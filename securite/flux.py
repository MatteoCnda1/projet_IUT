"""Point 09 : matrice des flux, source unique (version du dossier : commun/charte.py).

v2.1 (audit du 20/11/2026) : DNS de sortie des résolveurs et de la DMZ, relais DHCP des objets et de l'administration, CAPWAP,
NUT (onduleurs, clients internes et de la DMZ), NTP externe, DT-BKP1 et postes d'administration, administration des serveurs et
des objets par le bastion, alertes par courriel, groupe électrogène (supervision en lecture seule), pool du VPN d'administration ;
ordre de déploiement explicite et contrôle des autorisations masquées ; objet INTERNET par négation des préfixes du site.

Chaque règle dit qui parle à qui, sur quels ports, avec quel profil d'inspection, et pourquoi. Le pare-feu qui l'applique
n'est pas écrit à la main : il se déduit des zones (fonction `filtre`), comme dans le réseau réel où l'on ne change de VRF
qu'en traversant le Stormshield, et où l'on n'atteint Internet ou la DMZ qu'en traversant le FortiGate.

Les adresses viennent de architecture/reseau/donnees.py (plan d'adressage). `verifier()` contrôle que chaque objet existe
dans le plan, que les propositions (zone IA) ne chevauchent rien, que chaque couple de zones du résumé de l'architecture L3
(documents.FLUX) est bien détaillé ici, qu'aucun objet « Internet » ne contient d'adresse du site, et qu'aucune autorisation
n'est masquée par un refus placé avant elle dans l'ordre de déploiement.

Repris par :
  securite/build.py    -> livrables/securite/ (RLI-P09-matrice-flux.pdf et .csv, PSSI, analyse de risque : noms du dépôt GesTT)
"""
import importlib.util
import ipaddress as ip
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent


def _plan():
    """Plan d'adressage chargé sous un nom propre (« reseau_donnees ») : juridique/ a aussi un module « donnees » (SEC21-24)."""
    if "reseau_donnees" not in sys.modules:
        spec = importlib.util.spec_from_file_location("reseau_donnees", ICI.parent / "architecture" / "reseau" / "donnees.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["reseau_donnees"] = mod
        spec.loader.exec_module(mod)
    return sys.modules["reseau_donnees"]


D = _plan()

# ---------------------------------------------------------------------------
# Zones de sécurité (une zone = un niveau de confiance ; on ne passe d'une zone à l'autre que par un pare-feu)
# ---------------------------------------------------------------------------
ZONES = {
    "INTERNET": ("Internet", "aucune confiance", "#6C6861"),
    "WAN":      ("Site jumeau (Digne ou Gap), par l'opérateur", "confiance partielle (point 07)", "#6C6861"),
    "VPN":      ("Administrateurs nomades : pool du VPN IKEv2", "authentifiée (certificat + MFA), bastion seulement", "#4D525B"),
    "DMZ":      ("DMZ : services publiés", "exposée", "#a75c00"),
    "GST":      ("Invités et échecs 802.1X", "aucune confiance", "#97549b"),
    "IOT":      ("Objets : caméras, badgeuses, GTB", "faible (équipements peu durcis)", "#a75c00"),
    "USR":      ("Utilisateurs authentifiés", "moyenne", "#0079b5"),
    "IA":       ("Plateforme d'IA locale (proposition)", "sensible (données des utilisateurs)", "#2f6f3e"),
    "SRV":      ("Serveurs tier 1", "élevée", "#008889"),
    "T0":       ("Tier 0 : contrôleurs de domaine", "maximale", "#5b2c8c"),
    "ADM":      ("SI d'administration", "maximale", "#c13c3b"),
}
INTERNES = ("GST", "IOT", "USR", "IA", "SRV", "T0", "ADM")

# ---------------------------------------------------------------------------
# Proposition : zone de l'IA locale (note du point 11). Pas encore dans donnees.py : à y reporter quand le point 11
# sera validé. Même modèle que le tier 0 : passerelle sur le Stormshield, donc tout accès passe par le pare-feu.
# 10.13.54.0/24 est libre (entre le tier 0 10.13.52.0/27 et l'administration 10.13.56.0/21).
# ---------------------------------------------------------------------------
PROPOSITIONS = {
    320: {"nom": "IA-FRONT", "vrf": "IA", "v4": "10.13.54.0/26", "v6": "2001:660:5402:4320::/64",
          "usage": "Passerelle d'accès à l'IA : portail web et API, authentification, quotas, journal des requêtes"},
    321: {"nom": "IA-BACK", "vrf": "IA", "v4": "10.13.54.64/26", "v6": "2001:660:5402:4321::/64",
          "usage": "Nœuds GPU d'inférence et stockage des modèles : joignables seulement depuis IA-FRONT et l'administration"},
}
HOTES_PROP = {
    320: [("VIP passerelle IA (keepalived)", 10), ("Passerelle IA 1", 11), ("Passerelle IA 2", 12)],
    321: [("Nœuds GPU d'inférence", "21-28"), ("Stockage des modèles", 40)],
}


def _net(vid):
    if vid in PROPOSITIONS:
        p = PROPOSITIONS[vid]
        return p["v4"], p["v6"]
    v = D.VLANS[vid]
    return v["v4"], v["v6"]


def _hote(vid, fin):
    if vid in PROPOSITIONS:
        n4, n6 = PROPOSITIONS[vid]["v4"], PROPOSITIONS[vid]["v6"]
        return str(ip.ip_network(n4).network_address + int(fin)), n6.replace("::/64", f"::{fin}")
    return D.adresse(vid, fin)


def V(*vids):
    """Réseaux entiers de un ou plusieurs VLAN."""
    return [("vlan", vid) for vid in vids]


def H(vid, *fins):
    """Hôtes d'un VLAN, par leur terminaison (la même en IPv4 et en IPv6)."""
    return [("hote", vid, f) for f in fins]


def L(v4, v6=None):
    """Adresse ou préfixe littéral (hors plan interne : Internet, adresses publiques, site jumeau, pool VPN, boucles)."""
    return [("litteral", v4, v6)]


# Préfixes du site, exclus des objets « Internet » : sur le Stormshield, objet par négation ; sur le FortiGate, interface externe.
# Sans cette exclusion, 0.0.0.0/0 contiendrait aussi les zones internes (SEC21-04, SEC21-05).
SITE = [(str(D.P4_PRIVE), str(D.P6_SITE)), ("172.16.13.0/24", None), ("10.4.0.0/16", None)]
HORS_SITE = [("sauf", v4, v6) for v4, v6 in SITE]


# ---------------------------------------------------------------------------
# Objets (groupes d'adresses). Zone, description, contenu.
# ---------------------------------------------------------------------------
GW_USR = [("passerelle", vid) for vid in (110, 111, 112, 113, 210, 211, 212, 213)]
OBJETS = {
    # Internet et adresses publiques (VIP du FortiGate)
    "INTERNET":    ("INTERNET", "Toute adresse hors des préfixes du site (10.13.0.0/16, 172.16.13.0/24, 10.4.0.0/16, "
                                "2001:660:5402:4000::/52)", L("0.0.0.0/0", "::/0") + HORS_SITE),
    "NOMADES":     ("INTERNET", "Postes nomades des administrateurs sur Internet, avant l'établissement du VPN", L("0.0.0.0/0", "::/0") + HORS_SITE),
    "EDUROAM-FLR": ("INTERNET", "Proxys RADIUS nationaux eduroam (RENATER)", L("193.49.159.0/24")),
    "VIP-WEB":     ("DMZ", "139.124.112.33 → VIP Caddy 172.16.13.10", L("139.124.112.33")),
    "VIP-MX":      ("DMZ", "139.124.112.34 → DM-MAIL1", L("139.124.112.34")),
    "VIP-DNS":     ("DMZ", "139.124.112.35 → DM-DNS1 (ns1), 139.124.112.37 → DM-DNS2 (ns2)", L("139.124.112.35") + L("139.124.112.37")),
    "VIP-VPN":     ("DMZ", "139.124.112.36 : passerelle VPN d'administration du FortiGate", L("139.124.112.36")),
    # DMZ
    "DM-RP":       ("DMZ", "Reverse proxies Caddy (VIP et deux VM)", H(400, 10, 11, 12) + H(401, 41, 42)),
    "DM-DNS":      ("DMZ", "DNS publics faisant autorité (ns1, ns2)", H(400, 20, 22)),
    "DM-MAIL":     ("DMZ", "Messagerie DM-MAIL1", H(400, 21)),
    "DM-APP":      ("DMZ", "Site web DM-WEB1 et serveur applicatif DM-SRV1 (réservation de salles)", H(401, 51, 52)),
    "DM-SRV1":     ("DMZ", "Serveur applicatif DM-SRV1", H(401, 52)),
    "DM-PVE":      ("DMZ", "Hyperviseurs DM-PVE1/2 (réseau de gestion de la DMZ)", H(402, 67, 68)),
    "DMZ-TOUT":    ("DMZ", "Toute la DMZ", V(400, 401, 402)),
    "DMZ-GEST":    ("DMZ", "Gestion de la DMZ : switchs, hyperviseurs, témoin, iDRAC", V(402)),
    "FGT-DMZ":     ("DMZ", "Interfaces du FortiGate dans la DMZ (relais DNS récursif pour la DMZ)", H(400, 1) + H(401, 33) + H(402, 65)),
    "NUT-CLI-DMZ": ("DMZ", "Clients NUT de la DMZ : DM-PVE1/2, DM-WITNESS", H(402, 67, 68, 69)),
    # Utilisateurs
    "POSTES":      ("USR", "Postes du domaine : personnel et salles de TP (filaire, 802.1X)", V(110, 111, 210, 211)),
    "PERS":        ("USR", "Postes fixes du personnel", V(110, 210)),
    "ETU":         ("USR", "Postes des salles de TP", V(111, 211)),
    "WIFI-USR":    ("USR", "Wi-Fi personnel et étudiants (eduroam), appareils personnels compris", V(514, 515)),
    "USR-TOUT":    ("USR", "Tous les VLAN utilisateurs", V(110, 111, 112, 113, 210, 211, 212, 213, 514, 515)),
    "VOIX":        ("USR", "Téléphones IP", V(112, 212)),
    "IMPR":        ("USR", "Imprimantes et copieurs", V(113, 213)),
    "RELAIS-USR":  ("USR", "Passerelles des VLAN de bloc (relais DHCP des switchs de distribution)", GW_USR),
    "RELAIS-WIFI": ("USR", "Passerelles des VLAN Wi-Fi sur le cœur (relais DHCP)", [("passerelle", 514), ("passerelle", 515)]),
    # Objets
    "CAM":         ("IOT", "Caméras IP", V(120, 220)),
    "BADGE":       ("IOT", "Lecteurs et UTL du contrôle d'accès", V(121, 221)),
    "GE":          ("IOT", "Contrôleur du groupe électrogène et inverseur de source (VLAN GTB du bloc 1)", H(122, 110, 111)),
    "IOT-TOUT":    ("IOT", "Tous les objets", V(120, 121, 122, 220, 221, 222)),
    "RELAIS-IOT":  ("IOT", "Passerelles des VLAN objets (relais DHCP vers Kea)", [("passerelle", vid) for vid in (120, 121, 122, 220, 221, 222)]),
    # Invités
    "GST-TOUT":    ("GST", "Wi-Fi invités et VLAN restreint (échec 802.1X)", V(130, 230, 530)),
    "RELAIS-GST":  ("GST", "Passerelles des VLAN invités (relais DHCP vers Kea)", [("passerelle", 130), ("passerelle", 230), ("passerelle", 530)]),
    # Serveurs tier 1 et tier 0
    "DT-RAD":      ("SRV", "Serveurs RADIUS NPS", H(300, 21, 22)),
    "DT-DHCP":     ("SRV", "Serveurs DHCP Windows (utilisateurs)", H(300, 31, 32)),
    "VS-NVR1":     ("SRV", "Enregistreur vidéo physique VS-NVR1 (lot sûreté)", H(300, 60)),
    "CTRL-ACCES":  ("SRV", "Serveur de contrôle d'accès (lot sûreté)", H(300, 61)),
    "SRV-TOUT":    ("SRV", "Tous les serveurs tier 1", V(300)),
    "DT-AD":       ("T0", "Contrôleurs de domaine DT-AD1/2", H(310, 11, 12)),
    # IA locale (proposition)
    "IA-GW":       ("IA", "Passerelle d'accès à l'IA (VIP et deux nœuds)", H(320, 10, 11, 12)),
    "IA-BACK":     ("IA", "Nœuds GPU et stockage des modèles", V(321)),
    # Administration
    "KEA":         ("ADM", "DHCP Kea (objets, invités, administration)", H(904, 11, 12)),
    "NTP":         ("ADM", "Serveurs de temps chrony", H(904, 21, 22)),
    "DNS-INT":     ("ADM", "Résolveurs internes Unbound (filtrage DNS)", H(904, 31, 32)),
    "TELEPORT":    ("ADM", "Bastion Teleport (VIP et deux nœuds)", H(904, 40, 41, 42)),
    "SUPERV":      ("ADM", "VM de supervision (LibreNMS, snmptrapd, Loki, Grafana)", H(904, 50)),
    "LOGS":        ("ADM", "Collecteurs de journaux rsyslog (VIP et deux nœuds)", H(904, 55, 56, 57)),
    "PAW":         ("ADM", "Postes d'administration dédiés", V(906)),
    "BKP":         ("ADM", "Proxmox Backup Server DT-BKP1", H(909, 130)),
    "GEST-EQUIP":  ("ADM", "Interfaces de gestion : réseau, pare-feu, iDRAC, hyperviseurs, bornes, WLC", V(190, 191, 290, 291, 900, 901, 902, 907)),
    "BOUCLES":     ("ADM", "Loopback0 du cœur et de la distribution (source de l'AAA et des journaux)",
                    [("litteral", a4, a6) for _, a4, a6 in D.BOUCLES]),
    "EQUIP-AAA":   ("ADM", "Clients RADIUS : switchs (gestion et Loopback0), pare-feu, WLC",
                    V(190, 290, 900, 907) + [("litteral", a4, a6) for _, a4, a6 in D.BOUCLES]),
    "ADM-SERVICES": ("ADM", "VM et conteneurs de services de l'administration", V(904)),
    "PVE-ADM":     ("ADM", "Hyperviseurs NM et DT (réseau de gestion)", H(902, 11, 12, 14, 15)),
    "NUT-SRV":     ("ADM", "Serveur NUT (upsd) sur NM-WITNESS", H(902, 13)),
    "ONDULEURS":   ("ADM", "Cartes réseau des onduleurs A et B et sondes de la salle serveur", H(900, 45, 46, 47)),
    "BORNES":      ("ADM", "Bornes Wi-Fi", V(191, 291)),
    "WLC":         ("ADM", "WLC : interface de gestion sans fil (WMI, CAPWAP)", H(907, 70)),
    "RELAIS-ADM":  ("ADM", "Passerelles des VLAN d'administration des blocs et des PAW (relais DHCP vers Kea)",
                    [("passerelle", vid) for vid in (190, 191, 290, 291, 906)]),
    # Administrateurs nomades
    "VPN-ADM":     ("VPN", "Pool du VPN d'administration IKEv2 (certificat + MFA)", L(D.VPN_ADM["v4"], D.VPN_ADM["v6"])),
    # Site jumeau (point 07, à confirmer)
    "SITE2-AD":    ("WAN", "Contrôleurs de domaine du site jumeau (adresses réservées, point 07)", L("10.4.52.0/27")),
}

# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------
AD_CLIENT = ["tcp/88", "udp/88", "tcp/389", "udp/389", "tcp/636", "tcp/3268-3269", "tcp/445", "tcp/464", "udp/464",
             "tcp/135", "tcp/50000-50255"]
# RPC dynamique restreint à 256 ports sur les contrôleurs de domaine (netsh int ipv4 set dynamicport tcp start=50000 num=256)
WEB = ["tcp/80", "tcp/443"]
DNS = ["udp/53", "tcp/53"]
ICMP_ECHO = ["icmp/echo-request", "icmpv6/echo-request"]

# ---------------------------------------------------------------------------
# Règles, dans l'ordre de présentation (par thème). Ordre de déploiement sur les pare-feu (voir deploiement()) : sessions
# établies, puis toutes les autorisations (ordre Fxx), puis les refus explicites (ordre Fxx), puis F99. Champs :
#   id, section, source(s), destination(s), services, action, profil d'inspection, journal, justification, références,
#   statut ("" = retenu ; "à confirmer (Pxx)" ; "écart Ex" = règle actuelle à faire évoluer, voir ECARTS)
#   tests : cas de recette proposés [(poste de la maquette, objet, service)] ; le résultat attendu découle de l'action
# ---------------------------------------------------------------------------
R = []


def regle(id, section, src, dst, svc, action="autoriser", profil="filtrage à états", journal="refus", pourquoi="", ref="",
          statut="", tests=()):
    R.append({"id": id, "section": section, "src": src if isinstance(src, list) else [src],
              "dst": dst if isinstance(dst, list) else [dst], "svc": svc, "action": action, "profil": profil,
              "journal": journal, "pourquoi": pourquoi, "ref": ref, "statut": statut, "tests": list(tests)})


S = "Internet → DMZ"
regle("F01", S, "INTERNET", "VIP-WEB", WEB, profil="IPS + antivirus, TLS terminé sur Caddy", journal="tout",
      pourquoi="Site vitrine et application de réservation de salles. Le port 80 ne sert qu'à rediriger vers HTTPS (HSTS).",
      ref="ANSSI passerelle Internet v3 ; sécurisation des sites web")
regle("F02", S, "INTERNET", "VIP-MX", ["tcp/25"], profil="IPS + antispam + antivirus", journal="tout",
      pourquoi="Réception du courrier. STARTTLS, SPF, DKIM et DMARC vérifiés sur DM-MAIL1.", ref="ANSSI passerelle Internet v3")
regle("F03", S, "INTERNET", "VIP-DNS", DNS, profil="IPS, limitation de débit (RRL)", journal="refus",
      pourquoi="DNS faisant autorité, sans récursion : pas d'amplification possible. Zones signées DNSSEC.",
      ref="ANSSI PA-105 (architectures DNS) ; noms de domaine v1.3")
regle("F04", S, "INTERNET", "DM-MAIL", ["tcp/465", "tcp/587", "tcp/993"], profil="IPS", journal="tout",
      pourquoi="Messagerie des personnels hors du site, depuis Internet (sans VPN) : soumission authentifiée (MFA, M-IDA-2) et IMAPS, "
               "chiffrés de bout en bout.", ref="ANSSI TLS v1.2", statut="écart E1")
regle("F05", S, "NOMADES", "VIP-VPN", ["udp/500", "udp/4500"], profil="IKEv2, certificat machine + MFA", journal="tout",
      pourquoi="VPN d'administration en IPsec IKEv2 (plus de VPN SSL : écart E2 intégré en v2.1). Il attribue une adresse du pool "
               "VPN-ADM, qui n'atteint que le bastion Teleport (F38).", ref="ANSSI PA-054 (nomadisme) ; PA-022 (administration)")

S = "DMZ → Internet"
regle("F06", S, "DM-MAIL", "INTERNET", ["tcp/25"], journal="tout", pourquoi="Envoi du courrier sortant (MTA).")
regle("F07", S, "DM-RP", "INTERNET", ["tcp/443"], profil="filtrage d'URL (autorité ACME seulement)", journal="tout",
      pourquoi="Renouvellement automatique des certificats Let's Encrypt (ACME).")
regle("F08", S, ["DM-RP", "DM-DNS", "DM-MAIL", "DM-APP", "DM-PVE"], "INTERNET", ["tcp/443"],
      profil="filtrage d'URL (dépôts Debian et Proxmox)", journal="tout",
      pourquoi="Mises à jour des VM et des hyperviseurs de la DMZ, limitées aux dépôts officiels.",
      ref="Guide d'hygiène, mesure 34 (mises à jour)")
regle("F56", S, ["DM-RP", "DM-DNS", "DM-MAIL", "DM-APP", "DM-PVE"], "FGT-DMZ", DNS, profil="relais DNS récursif du FortiGate, filtrage DNS",
      journal="refus", pourquoi="Résolution des noms Internet pour la DMZ (MX et SPF, DKIM, DMARC du courrier, autorité ACME, dépôts), sans "
      "les résolveurs internes (F12) et sans mêler autorité (DM-DNS) et récursion.", ref="ANSSI PA-105")

S = "DMZ → interne (exceptions)"
regle("F09", S, "DM-PVE", "BKP", ["tcp/8007"], journal="tout",
      pourquoi="Sauvegarde des VM de la DMZ vers DT-BKP1. Les flux d'infrastructure de la DMZ vers l'intérieur se limitent à F09 "
               "(sauvegarde), F42 à F44 (journaux, traps, heure) et F57 (arrêt ordonné), jamais vers le tier 0 ni les utilisateurs.",
      ref="ANSSI BP-100 (sauvegarde)")
regle("F10", S, "DM-MAIL", "DT-AD", ["tcp/636"], profil="IPS complet", journal="tout",
      pourquoi="Authentification des boîtes aux lettres sur l'annuaire. Un serveur exposé qui parle au tier 0 : à supprimer (voir E1).",
      ref="ANSSI PA-099 (tiering AD)", statut="écart E1")
regle("F11", S, "DM-SRV1", "SRV-TOUT", ["tcp/5432"], profil="IPS complet", journal="tout",
      pourquoi="Base de données de l'application de réservation de salles (port et serveur à fixer avec le point 13).",
      statut="à confirmer (P13)")
regle("F57", S, "NUT-CLI-DMZ", "NUT-SRV", ["tcp/3493"], profil="filtrage à états, NUT sur TLS", journal="tout",
      pourquoi="Arrêt ordonné de la DMZ si le groupe électrogène n'a pas repris : DM-PVE1/2 et DM-WITNESS écoutent le serveur NUT de "
               "NM-WITNESS (document énergie, séquence NUT).", ref="Point 14")
regle("F12", S, "DMZ-TOUT", ["USR-TOUT", "IOT-TOUT", "GST-TOUT", "SRV-TOUT", "DT-AD", "IA-GW", "ADM-SERVICES"], ["tout"],
      action="refuser", journal="tout + alerte",
      pourquoi="Une machine de la DMZ compromise ne doit pas pouvoir rebondir vers l'intérieur.", ref="ANSSI passerelle Internet v3")

S = "Utilisateurs"
regle("F13", S, "POSTES", "DT-AD", AD_CLIENT, profil="IPS complet, protocoles contrôlés", journal="refus",
      pourquoi="Ouverture de session, GPO, partages SYSVOL. Seuls les postes du domaine (filaire, 802.1X EAP-TLS) parlent à l'annuaire.",
      ref="ANSSI PA-099", tests=[("pers-b1", "DT-AD", "tcp/636"), ("pers-b1", "DT-AD", "tcp/88"), ("etu-b1", "DT-AD", "tcp/445")])
regle("F14", S, ["RELAIS-USR", "RELAIS-WIFI"], "DT-DHCP", ["udp/67", "udp/547"],
      pourquoi="Relais DHCPv4 et DHCPv6 (sans état) des passerelles des blocs et des SVI Wi-Fi du cœur vers DT-DHCP1/2.")
regle("F15", S, ["USR-TOUT", "GST-TOUT"], "DNS-INT", DNS, profil="filtrage DNS (domaines malveillants)", journal="refus",
      pourquoi="Seuls les résolveurs internes répondent aux clients. Le DNS direct vers Internet est refusé (F18) : "
               "le filtrage DNS ne se contourne pas.", ref="ANSSI PA-105")
regle("F16", S, "USR-TOUT", "INTERNET", WEB, profil="postes gérés : inspection TLS (liste d'exclusion) ; Wi-Fi : SNI et réputation",
      journal="tout : données de connexion 1 an ; URL complètes 6 mois",
      pourquoi="Navigation. Données techniques de connexion (qui, quand, adresses et ports source et destination, volumes) conservées "
               "1 an ; URL complètes du proxy de filtrage web du FortiGate 6 mois, pour la sécurité seulement, consultation tracée.",
      ref="CPCE L34-1 et R10-13 ; décrets n° 2021-1361 et 2021-1362 ; ANSSI analyse des flux HTTPS")
regle("F17", S, "POSTES", "INTERNET", ["udp/443"], action="refuser", journal="non",
      pourquoi="QUIC refusé sur les postes gérés : le navigateur revient en TCP 443, que le FortiGate sait inspecter.")
regle("F18", S, ["USR-TOUT", "GST-TOUT", "IOT-TOUT"], "INTERNET", ["udp/53", "tcp/53", "tcp/853"], action="refuser", journal="tout",
      pourquoi="Pas de DNS, ni de DNS sur TLS, directement vers Internet.")
regle("F19", S, "USR-TOUT", ["DM-RP", "DM-MAIL"], ["tcp/443", "tcp/465", "tcp/587", "tcp/993"], profil="IPS", journal="refus",
      pourquoi="Accès interne au site, à l'application de réservation et à la messagerie.")
regle("F20", S, "VOIX", "SRV-TOUT", ["tcp/5061", "udp/16384-32767"], profil="filtrage à états (SIP-TLS, SRTP)", journal="refus",
      pourquoi="Téléphones vers l'IPBX (adresse à fixer par le point 12) : signalisation SIP-TLS et média SRTP.",
      ref="ANSSI DAT-NT-14 (ToIP)", statut="à confirmer (P12)")
regle("F21", S, "POSTES", "IMPR", ["tcp/631", "tcp/9100", "tcp/443"], profil="ACL de la distribution", journal="refus",
      pourquoi="Impression (IPP, RAW) et interface web des copieurs. Les imprimantes n'initient aucun flux vers les postes.")
regle("F22", S, "ETU", "PERS", ["tout"], action="refuser", profil="ACL de la distribution", journal="refus",
      pourquoi="Les postes des salles de TP n'atteignent pas ceux du personnel (même VRF : ACL sur les passerelles).")
regle("F23", S, "USR-TOUT", ["IOT-TOUT", "GST-TOUT", "SRV-TOUT", "ADM-SERVICES", "GEST-EQUIP"], ["tout"], action="refuser",
      journal="tout", pourquoi="Les utilisateurs n'atteignent ni les objets, ni les serveurs hors services listés, ni l'administration.",
      tests=[("etu-b1", "GEST-EQUIP", "tcp/22"), ("pers-b1", "SUPERV", "tcp/22"), ("pers-b1", "DT-DHCP", "tcp/22"),
             ("etu-b1", "TELEPORT", "tcp/443")])

S = "Objets"
regle("F24", S, "VS-NVR1", "CAM", ["tcp/554", "tcp/443"], profil="filtrage à états, IPS léger (RTSP)", journal="refus",
      pourquoi="L'enregistreur VS-NVR1 va chercher les flux des caméras (RTSP) et les pilote (ONVIF sur HTTPS). La caméra n'initie "
               "rien (écart E3 intégré en v2.1).", ref="ANSSI PA-072 (vidéoprotection)")
regle("F25", S, "BADGE", "CTRL-ACCES", ["tcp/443"], profil="IPS complet", journal="tout",
      pourquoi="Remontée des événements des UTL et lecteurs vers le serveur de contrôle d'accès (TLS ; port exact du lot sûreté).",
      ref="ANSSI PA-072", statut="à confirmer (lot sûreté)")
regle("F26", S, "IOT-TOUT", "NTP", ["udp/123"], journal="refus",
      pourquoi="Horloge juste sur les caméras et badgeuses : l'horodatage des images et des passages a une valeur de preuve.")
regle("F58", S, "RELAIS-IOT", "KEA", ["udp/67", "udp/547"], journal="refus",
      pourquoi="Relais DHCPv4 et DHCPv6 (réservations) des caméras, badgeuses et automates de la GTB vers Kea.")
regle("F27", S, "IOT-TOUT", ["INTERNET", "USR-TOUT", "SRV-TOUT", "DT-AD", "ADM-SERVICES"], ["tout"], action="refuser",
      journal="tout + alerte", pourquoi="Un objet compromis reste enfermé : pas d'Internet, pas de rebond. Micrologiciels poussés depuis "
      "l'administration par le bastion (F68). Groupe électrogène compris : ni modem ni télésurveillance en nuage (M-PHY-5).",
      ref="ANSSI sécurité des objets connectés v1.0", tests=[("cam-b1", "PERS", "icmp/echo-request"), ("cam-b1", "DT-AD", "tcp/636")])

S = "Invités"
regle("F28", S, "RELAIS-GST", "KEA", ["udp/67"], pourquoi="Relais DHCP des VLAN invités vers Kea (bail 1 h).")
regle("F29", S, "GST-TOUT", "INTERNET", WEB + ["udp/443"], profil="SNI et réputation, débit limité à 10 Mb/s par client",
      journal="tout : données de connexion 1 an", pourquoi="Internet seulement, par une plage NAT séparée (.88/29). Données techniques "
      "de connexion (qui, quand, adresses et ports, volumes) conservées 1 an ; pas de déchiffrement, donc pas d'URL complète.",
      ref="CPCE L34-1 ; décrets n° 2021-1361 et 2021-1362")
regle("F30", S, "GST-TOUT", ["USR-TOUT", "IOT-TOUT", "SRV-TOUT", "DT-AD", "IA-GW", "ADM-SERVICES", "GEST-EQUIP", "DMZ-TOUT"], ["tout"],
      action="refuser", journal="tout", pourquoi="Un invité n'atteint aucune ressource interne, pas même la DMZ par son adresse privée.",
      tests=[("inv-b1", "DT-AD", "icmp/echo-request"), ("inv-b1", "DT-AD", "tcp/636"), ("inv-b1", "PERS", "icmp/echo-request")])

S = "Serveurs et tier 0"
regle("F31", S, ["DT-RAD", "DT-DHCP"], "DT-AD", AD_CLIENT + DNS, profil="IPS complet", journal="refus",
      pourquoi="NPS vérifie les comptes dans l'annuaire, le DHCP met à jour le DNS de l'AD. Tier 1 → tier 0 : par le Stormshield.",
      ref="ANSSI PA-099")
regle("F32", S, "DNS-INT", "DT-AD", DNS, journal="refus", pourquoi="Les résolveurs internes transmettent la zone de l'AD aux contrôleurs de domaine.")
regle("F33", S, "EQUIP-AAA", "DT-RAD", ["udp/1812", "udp/1813"], journal="refus",
      pourquoi="802.1X et MAB : les switchs d'accès et les WLC interrogent NPS. Clé partagée par client, longue et unique.",
      ref="ANSSI PA-043 (802.1X)")
regle("F34", S, "DT-RAD", "EQUIP-AAA", ["udp/3799"], journal="refus", pourquoi="Changement d'autorisation (CoA) : NPS change le VLAN ou coupe une session.")
regle("F35", S, "DT-RAD", "EDUROAM-FLR", ["udp/1812", "udp/1813"], journal="tout",
      pourquoi="eduroam : les comptes des autres établissements sont relayés vers les proxys de RENATER. NPS ne parle pas RadSec : "
               "RADIUS sur UDP avec un secret partagé long, vers ces seuls proxys ; un relais radsecproxy en zone SRV si RENATER impose RadSec.")
regle("F36", S, ["SRV-TOUT"], "INTERNET", ["tcp/443"], profil="filtrage d'URL (éditeurs, Windows Update)", journal="tout",
      pourquoi="Mises à jour des serveurs tier 1. Les contrôleurs de domaine n'ont aucun accès Internet (F37) : leurs correctifs sont "
               "téléchargés par l'administration (F46), vérifiés, puis copiés par le rôle Teleport tier 0 (F40).")
regle("F37", S, "DT-AD", "INTERNET", ["tout"], action="refuser", journal="tout + alerte",
      pourquoi="Un contrôleur de domaine ne sort jamais sur Internet.", ref="ANSSI PA-099")

S = "Administration"
regle("F38", S, ["PAW", "VPN-ADM"], "TELEPORT", ["tcp/443"], profil="MFA matériel (FIDO2)", journal="tout",
      pourquoi="On n'administre qu'en passant par le bastion, depuis un poste d'administration ou le pool du VPN d'administration.",
      ref="ANSSI PA-022 (administration sécurisée)")
regle("F39", S, "TELEPORT", ["GEST-EQUIP", "DMZ-TOUT", "ADM-SERVICES"], ["tcp/22", "tcp/443", "tcp/830", "tcp/8006"], journal="tout",
      pourquoi="SSH, HTTPS, NETCONF et interface Proxmox de tous les équipements et des VM de la DMZ, sessions enregistrées par Teleport.",
      ref="ANSSI PA-022 ; OpenSSH DAT-NT-007")
regle("F40", S, "TELEPORT", "DT-AD", ["tcp/3389", "tcp/5986"], profil="IPS complet", journal="tout",
      pourquoi="Administration des contrôleurs de domaine par le rôle Teleport « tier 0 » seulement (RDP, WinRM sur HTTPS), y compris la "
               "copie de leurs correctifs, téléchargés par l'administration et vérifiés.", ref="ANSSI PA-099")
regle("F63", S, "TELEPORT", "BKP", ["tcp/22", "tcp/8007"], journal="tout",
      pourquoi="Administration de DT-BKP1 (SSH, interface PBS) par le rôle Teleport tier 0 (SEC-02, SEC-03).", ref="ANSSI PA-099 ; BP-100")
regle("F67", S, "TELEPORT", "SRV-TOUT", ["tcp/22", "tcp/443", "tcp/3389", "tcp/5986"], profil="IPS", journal="tout",
      pourquoi="Administration des serveurs tier 1 (NPS, DHCP, VS-NVR1, contrôle d'accès) par le rôle Teleport tier 1, prestataires du "
               "lot sûreté compris, avec un compte nominatif ouvert pour l'intervention (M-ADM-2).", ref="ANSSI PA-022")
regle("F68", S, "TELEPORT", "IOT-TOUT", ["tcp/22", "tcp/443"], journal="tout",
      pourquoi="Configuration et micrologiciels des caméras, UTL et automates (groupe électrogène compris), poussés depuis "
               "l'administration : les objets n'initient rien (F27).", ref="ANSSI PA-072 ; objets connectés v1.0")
regle("F41", S, "SUPERV", ["GEST-EQUIP", "SRV-TOUT", "DT-AD", "DMZ-TOUT", "BKP", "IOT-TOUT", "IA-GW", "IA-BACK"], ICMP_ECHO + ["udp/161", "tcp/9100"],
      journal="refus", pourquoi="Supervision : disponibilité (ping), SNMPv3 (authPriv) et métriques des serveurs Linux.",
      tests=[("sup", "DT-AD", "icmp/echo-request")])
regle("F70", S, "SUPERV", "GE", ICMP_ECHO + ["udp/161", "tcp/502"],
      profil="IPS Modbus : codes fonction en lecture seule, écritures refusées", journal="tout",
      pourquoi="Supervision du groupe électrogène et de l'inverseur : secteur présent, groupe en marche, inverseur sur groupe, défauts, "
               "niveau de carburant, batterie de démarrage. Aucune commande à distance (M-PHY-5).", ref="ANSSI GTB/GTC ; PA-072")
regle("F42", S, ["GEST-EQUIP", "BOUCLES", "SRV-TOUT", "DT-AD", "DMZ-TOUT", "IOT-TOUT", "BKP", "PAW", "IA-GW", "IA-BACK"], "LOGS", ["tcp/6514"],
      journal="non", pourquoi="Journaux de toutes les zones vers les collecteurs, en syslog sur TLS (le journal légal vers les deux collecteurs).",
      ref="ANSSI journalisation v2.0")
regle("F43", S, ["GEST-EQUIP", "BOUCLES", "SRV-TOUT", "DT-AD", "DMZ-GEST", "BKP", "GE"], "SUPERV", ["udp/162"], journal="non",
      pourquoi="Traps SNMP vers snmptrapd.")
regle("F44", S, ["GEST-EQUIP", "BOUCLES", "SRV-TOUT", "DT-AD", "USR-TOUT", "GST-TOUT", "IA-GW", "IA-BACK", "DMZ-TOUT", "BKP", "PAW"], "NTP",
      ["udp/123"], journal="non", pourquoi="Une seule source de temps pour tous les journaux : condition de leur valeur de preuve.",
      ref="ANSSI journalisation v2.0")
regle("F65", S, "BORNES", "WLC", ["udp/5246", "udp/5247"], profil="ACL de la distribution", journal="refus",
      pourquoi="CAPWAP des bornes en mode local vers les WLC (contrôle en DTLS, données des clients) : sans ce flux, plus de Wi-Fi.")
regle("F66", S, "RELAIS-ADM", "KEA", ["udp/67", "udp/547"], profil="ACL du cœur et de la distribution", journal="refus",
      pourquoi="Relais DHCP des VLAN d'administration vers Kea : réservations des switchs d'accès, des bornes (option 43) et des PAW.")
regle("F61", S, "NUT-SRV", "ONDULEURS", ["udp/161"], profil="SNMPv3 authPriv", journal="refus",
      pourquoi="NUT lit l'état des deux onduleurs et la température de la salle (déclencheurs de l'arrêt ordonné).", ref="Point 14")
regle("F62", S, ["PVE-ADM", "BKP", "VS-NVR1"], "NUT-SRV", ["tcp/3493"], profil="NUT sur TLS", journal="refus",
      pourquoi="Clients NUT : hyperviseurs NM et DT, DT-BKP1 et VS-NVR1 s'arrêtent dans l'ordre si le groupe électrogène n'a pas repris.",
      ref="Point 14")
regle("F64", S, "PVE-ADM", "BKP", ["tcp/8007"], profil="ACL du cœur (même VRF)", journal="tout",
      pourquoi="Sauvegardes vzdump des hyperviseurs NM et DT, dans la VRF ADM, sans traverser le Stormshield (SEC-01) ; jetons API "
               "limités à l'écriture (SEC-03).", ref="ANSSI BP-100")
regle("F45", S, "BKP", "INTERNET", ["tcp/443"], profil="filtrage d'URL (fournisseur de stockage objet)", journal="tout",
      pourquoi="Copie externalisée et immuable des sauvegardes (prestataire SecNumCloud, à choisir au point 15).", ref="ANSSI BP-100")
regle("F46", S, "ADM-SERVICES", "INTERNET", ["tcp/443"],
      profil="filtrage d'URL (dépôts, FortiGuard, mises à jour, passerelle SMS d'astreinte)", journal="tout",
      pourquoi="Mises à jour des services et des équipements, téléchargées sur l'administration puis poussées ; SMS d'astreinte.")
regle("F59", S, "DNS-INT", "INTERNET", DNS, profil="IPS (DNS), validation DNSSEC sur Unbound", journal="refus",
      pourquoi="Résolution récursive des noms Internet par les seuls résolveurs internes ; tout autre DNS vers Internet est refusé (F18).",
      ref="ANSSI PA-105")
regle("F60", S, "NTP", "INTERNET", ["udp/123", "tcp/4460"], profil="filtrage à états (serveurs NTP de RENATER, NTS)", journal="refus",
      pourquoi="Sources de temps des serveurs chrony ; tcp/4460 pour l'échange de clés NTS.", ref="ANSSI journalisation v2.0")
regle("F69", S, ["SUPERV", "NUT-SRV"], "DM-MAIL", ["tcp/587"], profil="IPS", journal="tout",
      pourquoi="Alertes de la supervision et de NUT par courriel (soumission authentifiée sur DM-MAIL1) : coupure secteur, groupe "
               "électrogène en défaut, fuite d'eau, la nuit comme le jour.")
regle("F47", S, "PAW", ["INTERNET", "USR-TOUT"], ["tout"], action="refuser", journal="tout + alerte",
      pourquoi="Un poste d'administration ne navigue pas sur Internet et ne lit pas la messagerie.", ref="ANSSI PA-022")

S = "IA locale (proposition)"
regle("F48", S, ["POSTES", "WIFI-USR"], "IA-GW", ["tcp/443"], profil="IPS, quotas par utilisateur", journal="tout",
      pourquoi="Portail web et API de l'IA pour les étudiants, enseignants et chercheurs, après authentification (SSO sur l'AD).",
      statut="à confirmer (P11)")
regle("F49", S, "IA-GW", "DT-AD", ["tcp/636"], profil="IPS complet", journal="tout",
      pourquoi="Authentification et groupes des utilisateurs (compte de service en lecture seule).", ref="ANSSI PA-099", statut="à confirmer (P11)")
regle("F50", S, "IA-GW", "IA-BACK", ["tcp/8000"], journal="refus",
      pourquoi="La passerelle seule parle aux nœuds d'inférence (API vLLM). Aucun utilisateur n'atteint un GPU directement.",
      statut="à confirmer (P11)")
regle("F51", S, "TELEPORT", ["IA-GW", "IA-BACK"], ["tcp/22", "tcp/443"], journal="tout", pourquoi="Administration de la plateforme d'IA par le bastion.",
      statut="à confirmer (P11)")
regle("F52", S, ["IA-GW", "IA-BACK"], "INTERNET", ["tout"], action="refuser", journal="tout + alerte",
      pourquoi="Pas de sortie : ni fuite des requêtes, ni téléchargement de modèle non vérifié. Les modèles entrent par une procédure "
               "contrôlée (téléchargement sur l'administration, vérification des empreintes, puis copie).", statut="à confirmer (P11)")

S = "Site jumeau (point 07)"
regle("F53", S, "DT-AD", "SITE2-AD", AD_CLIENT + DNS, profil="IPS complet, lien chiffré (IPsec)", journal="refus",
      pourquoi="Réplication de l'annuaire entre Marseille et le site jumeau (un domaine, deux sites AD).", statut="à confirmer (P07)")
regle("F54", S, "SITE2-AD", "DT-AD", AD_CLIENT + DNS, profil="IPS complet, lien chiffré (IPsec)", journal="refus",
      pourquoi="Sens retour de la réplication.", statut="à confirmer (P07)")

S = "Règles communes"
regle("F55", S, ["tout"], ["tout"], ["icmp/destination-unreachable", "icmpv6/packet-too-big", "icmp/time-exceeded"], journal="non",
      pourquoi="Messages ICMP indispensables (découverte du MTU, traceroute). Ils ne passent que s'ils se rapportent à une session connue.",
      ref="RFC 4890")
regle("F99", S, ["tout"], ["tout"], ["tout"], action="refuser", journal="tout",
      pourquoi="Politique par défaut : tout ce qui n'est pas autorisé est refusé et journalisé.", ref="ANSSI politique de filtrage")

# ---------------------------------------------------------------------------
# Écarts relevés en v2 entre l'architecture et cette matrice. v2.1 : E2, E3 et E4 sont intégrés à l'architecture (L3) ;
# E1 et E5 restent des propositions, qui dépendent des points 13 et 11.
# ---------------------------------------------------------------------------
INTEGRES_V21 = ("E2", "E3", "E4")
ECARTS = {
    "E1": ("Messagerie : DM-MAIL1 parle au tier 0 (F10)",
           "Un serveur exposé à Internet interroge directement les contrôleurs de domaine. Si DM-MAIL1 est compromis, l'attaquant "
           "a un chemin vers le tier 0.",
           "DM-MAIL1 devient un relais (MX et passerelle de soumission, sans boîtes aux lettres). Les boîtes vont sur un serveur "
           "de messagerie en zone SRV, qui seul parle à l'AD. F10 disparaît ; F04 vise le relais, qui transmet au serveur interne.",
           "points 13 (messagerie) et 03"),
    "E2": ("VPN d'administration en SSL (architecture v2) → IPsec IKEv2",
           "Les passerelles VPN SSL sont la première cible des attaquants depuis 2019 (vulnérabilités FortiOS exploitées en masse), "
           "et Fortinet retire le mode tunnel SSL de FortiOS 7.6.",
           f"VPN IPsec IKEv2 avec certificat machine et MFA, comme le recommande l'ANSSI. L'adresse publique .36 est inchangée ; "
           f"pool {D.VPN_ADM['v4']} (plan d'adressage v2.1).",
           "point 08 (bordure)"),
    "E3": ("Sens du flux vidéo (architecture v2 : caméras → enregistreur)",
           "Avec la plupart des logiciels de vidéoprotection, c'est l'enregistreur qui ouvre la connexion RTSP vers la caméra.",
           "Règle F24 : VS-NVR1 → caméras. Les caméras n'ouvrent aucune connexion ; l'ACL téléchargée sur leur port reste en place.",
           "points 12 et 17 (lot sûreté)"),
    "E4": ("DNS des postes (architecture v2 : USR → contrôleurs de domaine en DNS)",
           "Si les postes interrogent directement les contrôleurs de domaine, le filtrage DNS des résolveurs Unbound ne s'applique pas.",
           "Les postes utilisent les résolveurs internes (F15), qui transmettent la zone de l'AD (F32). Le DNS sort du flux USR → T0.",
           "point 11 (AD, DHCP)"),
    "E5": ("Zone IA locale (note du point 11)",
           "La plateforme d'IA n'a pas encore de place dans le plan d'adressage.",
           "VLAN 320 IA-FRONT 10.13.54.0/26 et 321 IA-BACK 10.13.54.64/26, passerelles sur le Stormshield (même modèle que le tier 0).",
           "points 05 et 11"),
}

# ---------------------------------------------------------------------------
# Recette : postes de la maquette (point 06) et adresses de test. La configuration des pare-feu revient à l'équipe.
# ---------------------------------------------------------------------------
# Dans la maquette, l'AD est encore en VLAN 300 (écart noté dans le TP, partie 7)
MAQUETTE_ADRESSES = {"DT-AD": [("10.13.48.11", "2001:660:5402:4300::11")]}
MAQUETTE_POSTES = {  # poste : (zone, adresse IPv4) ; postes Docker de containerlab, VPCS de GNS3
    "pers-b1": "10.13.18.10", "etu-b1": "10.13.16.10", "cam-b1": "10.13.28.10", "inv-b1": "10.13.30.10",
    "pers-b2": "10.13.34.10", "inv-b2": "10.13.46.10", "srv-ad": "10.13.48.11", "srv-dhcp": "10.13.48.31",
    "sup": "10.13.59.50", "paw": "10.13.60.11",
}
CIBLES_MAQUETTE = {  # objet -> adresse de test dans la maquette
    "DT-AD": "10.13.48.11", "DT-DHCP": "10.13.48.31", "SUPERV": "10.13.59.50", "PERS": "10.13.18.10",
    "GEST-EQUIP": "10.13.56.1", "TELEPORT": "10.13.59.40",
}


# ---------------------------------------------------------------------------
# Résolution et contrôles
# ---------------------------------------------------------------------------
def zone(obj):
    return None if obj == "tout" else OBJETS[obj][0]


def filtre(zs, zd):
    """Équipement qui applique la règle, déduit du chemin réel."""
    if zs is None or zd is None:
        return "tous"
    if zs == zd:
        return "ACL (même zone)" if zs not in ("INTERNET", "DMZ", "WAN") else ("FortiGate" if zs == "DMZ" else "—")
    externes = {"INTERNET", "DMZ", "VPN"}
    if zs in externes and zd in externes:
        return "FortiGate"
    if zs in externes or zd in externes:
        return "FortiGate + Stormshield"
    if "WAN" in (zs, zd):  # v2.1 (SEC21-22) : la liaison avec le site jumeau est un tunnel IPsec du FortiGate, puis le Stormshield
        return "FortiGate (tunnel IPsec) + Stormshield"
    return "Stormshield"


def adresses(obj, maquette=False):
    """Liste de (IPv4, IPv6) pour un objet. Préfixes pour les VLAN, adresses pour les hôtes."""
    if maquette and obj in MAQUETTE_ADRESSES:
        return MAQUETTE_ADRESSES[obj]
    out = []
    for el in OBJETS[obj][2]:
        if el[0] == "vlan":
            out.append(_net(el[1]))
        elif el[0] == "hote":
            if isinstance(el[2], str):  # plage
                a, b = el[2].split("-")
                out += [_hote(el[1], k) for k in range(int(a), int(b) + 1)]
            else:
                out.append(_hote(el[1], el[2]))
        elif el[0] == "passerelle":
            v = D.VLANS[el[1]]
            out.append((v["gw4"], v["gw6"]))
        elif el[0] == "litteral":
            out.append((el[1], el[2]))
    return out


def exclusions(obj):
    """Préfixes retirés d'un objet défini par négation (INTERNET, NOMADES) : liste de (IPv4, IPv6)."""
    return [(el[1], el[2]) for el in OBJETS[obj][2] if el[0] == "sauf"]


def _dans_objet(obj, reseau, maquette=False):
    """Vrai si le réseau (ou l'adresse) IPv4 est entièrement dans l'objet, exclusions comprises."""
    n = ip.ip_network(reseau, strict=False)
    if any(n.overlaps(ip.ip_network(x4)) for x4, _ in exclusions(obj) if x4):
        return False
    listes = adresses(obj, maquette=True) + adresses(obj) if maquette else adresses(obj)
    return any(a4 and n.subnet_of(ip.ip_network(a4, strict=False)) for a4, _ in listes)


def contient(objets, adresse4):
    """Vrai si l'adresse IPv4 appartient à l'un des objets (« tout » contient tout)."""
    return any(o == "tout" or _dans_objet(o, adresse4, maquette=True) for o in objets)


def deploiement():
    """Ordre de déploiement sur les pare-feu : autorisations (ordre Fxx), refus explicites (ordre Fxx), puis F99 (SEC21-04)."""
    cle = lambda r: int(r["id"][1:])
    autor = sorted((r for r in R if r["action"] == "autoriser"), key=cle)
    refus = sorted((r for r in R if r["action"] == "refuser" and r["id"] != "F99"), key=cle)
    return autor + refus + [r for r in R if r["id"] == "F99"]


def _svc_couverts(a, b):
    """Vrai si tous les services de a sont dans b (« tout » couvre tout ; les plages de ports sont comparées)."""
    if "tout" in b:
        return True
    if "tout" in a:
        return False

    def plage(x):
        proto, _, port = x.partition("/")
        if proto not in ("tcp", "udp"):
            return proto, port, port
        d, _, f = port.partition("-")
        return proto, int(d), int(f or d)
    for x in a:
        p, d, f = plage(x)
        if not any(q == p and (dd <= d and f <= ff if isinstance(d, int) else dd == d) for q, dd, ff in map(plage, b)):
            return False
    return True


def _objets_couverts(a, b):
    """Couples d'objets (oa, ob) de a et b tels que oa est entièrement dans ob."""
    out = []
    for oa in a:
        for ob in b:
            if ob == "tout" or (oa != "tout" and adresses(oa) and all(_dans_objet(ob, a4) for a4, _ in adresses(oa) if a4)
                                and not exclusions(oa)):
                out.append((oa, ob))
    return out


def masques(ordre):
    """Autorisations (ou parties d'autorisation) masquées par un refus placé avant elles dans `ordre`."""
    out = []
    for i, r in enumerate(ordre):
        if r["action"] != "autoriser":
            continue
        for q in ordre[:i]:
            if q["action"] == "refuser" and _svc_couverts(r["svc"], q["svc"]):
                for s_, _ in _objets_couverts(r["src"], q["src"]):
                    for d_, _ in _objets_couverts(r["dst"], q["dst"]):
                        out.append((r["id"], q["id"], s_, d_))
    return out


def verifier():
    D.verifier()
    erreurs = []
    # 1. objets : chaque VLAN et chaque hôte existent dans le plan (ou dans les propositions)
    for nom, (z, _, contenu) in OBJETS.items():
        assert z in ZONES, (nom, z)
        for el in contenu:
            if el[0] in ("vlan", "passerelle", "hote") and el[1] not in D.VLANS and el[1] not in PROPOSITIONS:
                erreurs.append(f"{nom} : VLAN {el[1]} absent du plan")
            if el[0] == "hote" and el[1] in D.HOTES:
                connus = {str(f) for _, f in D.HOTES[el[1]]}
                if str(el[2]) not in connus and not any("-" in c and int(c.split("-")[0]) <= int(el[2]) <= int(c.split("-")[1])
                                                         for c in connus):
                    erreurs.append(f"{nom} : hôte .{el[2]} absent du VLAN {el[1]} dans donnees.HOTES")
        for a4, a6 in adresses(nom):
            ip.ip_network(a4, strict=False)
            if a6:
                ip.ip_network(a6, strict=False)
    # 2. propositions : pas de chevauchement avec le plan
    plan = [ip.ip_network(v["v4"]) for v in D.VLANS.values() if v["v4"]]
    for vid, p in PROPOSITIONS.items():
        assert vid not in D.VLANS, f"VLAN {vid} déjà pris"
        n = ip.ip_network(p["v4"])
        for m in plan:
            if n.overlaps(m):
                erreurs.append(f"proposition VLAN {vid} {n} chevauche {m}")
    # 3. règles : objets connus, identifiants uniques
    ids = [r["id"] for r in R]
    assert len(ids) == len(set(ids)), "identifiants de règle en double"
    for r in R:
        for o in r["src"] + r["dst"]:
            if o != "tout" and o not in OBJETS:
                erreurs.append(f"{r['id']} : objet inconnu {o}")
        st = r["statut"]
        if st.startswith("écart") and st.split()[1] not in ECARTS:
            erreurs.append(f"{r['id']} : écart {st} non décrit")
    # 4. tests : postes et cibles connus de la maquette
    for r in R:
        for poste, cible, svc in r["tests"]:
            if poste not in MAQUETTE_POSTES:
                erreurs.append(f"{r['id']} : poste de test inconnu {poste}")
            if cible not in CIBLES_MAQUETTE:
                erreurs.append(f"{r['id']} : cible de test sans adresse dans la maquette {cible}")
            if not contient(r["dst"], CIBLES_MAQUETTE.get(cible, "0.0.0.0")):
                erreurs.append(f"{r['id']} : la cible {cible} n'est pas dans les destinations de la règle")
            if not contient(r["src"], MAQUETTE_POSTES.get(poste, "0.0.0.0")) and poste not in ("srv-ad",):
                erreurs.append(f"{r['id']} : le poste {poste} n'est pas dans les sources de la règle")
    # 5. couverture du résumé de l'architecture L3 : chaque couple de zones y figure ici
    couples = {(zone(s), zone(d)) for r in R for s in r["src"] for d in r["dst"] if s != "tout" and d != "tout"}
    for a, b, _ in RESUME_L3:
        if (a, b) not in couples:
            erreurs.append(f"couple {a} → {b} du résumé L3 sans règle détaillée")
    # 6. v2.1 (RES-01, SEC21-04/05) : chaque hôte, passerelle et transit cité est dans son sous-réseau (plan d'adressage) ;
    #    aucun objet hors site ne contient d'adresse du site ; aucune autorisation masquée dans l'ordre de déploiement
    try:
        D.verifier_adresses()
    except AssertionError as x:
        erreurs.append(f"plan d'adressage : {x}")
    internes = [v["gw4"] for v in D.VLANS.values() if v["gw4"]] + [D.VLANS[t[0]]["a"][1] for t in D.TRANSITS] + \
               [str(ip.ip_network(D.VPN_ADM["v4"]).network_address + 1)]
    for nom, (z, _, _) in OBJETS.items():
        if z in ("INTERNET", "WAN"):
            for a in internes:
                if _dans_objet(nom, a):
                    erreurs.append(f"objet {nom} (zone {z}) : contient l'adresse interne {a}")
                    break
    for rid, qid, s_, d_ in masques(deploiement()):
        erreurs.append(f"{rid} ({s_} → {d_}) masquée par le refus {qid}, placé avant elle dans l'ordre de déploiement")
    if erreurs:
        raise SystemExit("Matrice de flux : " + "\n  ".join(["erreurs"] + erreurs))
    return True


# Couples de zones du tableau résumé de l'architecture L3 (architecture/reseau/documents.py, FLUX), recopiés en codes de zone
RESUME_L3 = [
    ("USR", "T0", ""), ("USR", "SRV", ""), ("SRV", "T0", ""), ("T0", "INTERNET", ""), ("USR", "INTERNET", ""),
    ("USR", "DMZ", ""), ("USR", "IOT", ""), ("USR", "ADM", ""), ("USR", "GST", ""), ("SRV", "IOT", ""), ("IOT", "SRV", ""),
    ("IOT", "INTERNET", ""), ("ADM", "IOT", ""), ("GST", "INTERNET", ""), ("GST", "USR", ""), ("SRV", "INTERNET", ""),
    ("ADM", "ADM", ""), ("ADM", "DMZ", ""), ("DMZ", "ADM", ""), ("ADM", "INTERNET", ""), ("VPN", "ADM", ""), ("INTERNET", "DMZ", ""),
    ("DMZ", "DMZ", ""), ("DMZ", "USR", ""), ("DMZ", "T0", ""), ("DMZ", "SRV", ""),
]
# v2.1 : documents.FLUX écrit désormais « SRV (VS-NVR1) → IOT (caméras) » comme la matrice (écart E3 intégré).


if __name__ == "__main__":
    verifier()
    n = {"autoriser": 0, "refuser": 0}
    for r in R:
        n[r["action"]] += 1
    print(f"Matrice de flux : {len(R)} règles ({n['autoriser']} autorisations, {n['refuser']} refus), {len(OBJETS)} objets, "
          f"{len(ECARTS)} écarts. Contrôles : OK. Déployées dans l'ordre des numéros, {len(masques(sorted(R, key=lambda r: int(r['id'][1:]))))} "
          "parties d'autorisation seraient masquées : d'où l'ordre de déploiement imposé.")
