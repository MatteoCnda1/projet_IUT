"""Point 19 : cahiers des clauses techniques particulières (CCTP) pour le client, 5 lots (RLI-CCTP-001 à 005).

Le client (l'AMU) achète en marché public : ces CCTP sont des modèles qu'il complète (le CCAP, le règlement de la
consultation et le bordereau de prix relèvent de ses services achats). Rien n'est recopié : les quantités et les désignations
sont lues dans chiffrage/estimation.json (lignes du CAPEX et de l'OPEX), livrables/plan_cablage/resume.json (prises, rocades)
et livrables/energie_refroidissement/resume.json (onduleurs, climatisation, locaux techniques, clé « bet » : groupe
électrogène, TGBT). Les notes internes du chiffrage (repères v1/v2, codes d'audit, prix, « à confirmer ») sont filtrées par
note_cctp() : un CCTP est lu par les candidats. Exigences de sécurité : PSSI (M-xx) et matrice des flux (Fxx). Maintenance :
décision D4 de la v2.1 (pra.GTR_4H, pra.GTR_J1). Les marques citées le sont à titre indicatif : la désignation est alors
suivie de « ou équivalent » (principe d'égalité de traitement des candidats). Repère « [v2.1] » : exigence changée en v2.1.
"""
import json
import re
from pathlib import Path

import donnees as J
import pra as PRA

ROOT = Path(__file__).resolve().parent.parent
EST = json.loads((ROOT / "chiffrage" / "estimation.json").read_text(encoding="utf-8"))
CAB = json.loads((ROOT / "livrables" / "plan_cablage" / "resume.json").read_text(encoding="utf-8"))
ENE = json.loads((ROOT / "livrables" / "energie_refroidissement" / "resume.json").read_text(encoding="utf-8"))
BET = ENE["bet"]
GE = BET["groupe_electrogene"]
OND = ENE["onduleurs"]
CLIM = ENE["clim"]
V21 = J.V21
fr = PRA.fr

# ---------------------------------------------------------------------------
# Lecture du chiffrage : désignations, quantités, notes filtrées
# ---------------------------------------------------------------------------
_MARQUES = re.compile(r"\b(Cisco|Catalyst|Forti\w*|Stormshield|SN\d+|Dell|PowerEdge|APC|Smart-UPS|SRT\w*|Windows|Proxmox|Kea|chrony|"
                      r"Unbound|LibreNMS|Grafana|Loki|rsyslog|snmptrapd|Teleport|NUT|MIFARE|DESFire|VESDA|CW\d\w*|C\d{4}\w*|R\d{3}\w*|"
                      r"StackWise|DNA|Milestone|Genetec|Axis|Hikvision)\b")
_PAR_INTERNE = re.compile(r"\s*\([^()]*(?:\bv\d|\bpoint \d|\baudit\b|\b[A-Z]{3}-\d|OPEX|CAPEX|prix|BET|schéma|moins ch[eè]re?)[^()]*\)")
_VERSION_TETE = re.compile(r"^\s*v\d(?:\.\d)?\s*(?:\([^)]*\))?\s*:\s*")
_PHRASE_INTERNE = re.compile(r"Prix à confirmer|Le schéma en montre|oubli|ordre de grandeur|devis|[Tt]arif|€|Remplace la VM|"
                             r"\bx\d+ environ|environ [x×]\d|ne détruit plus|à valider|à confirmer|équipe|option écartée|"
                             r"^\s*v\d(?:\.\d)?\b|\b[A-Z]{3}-\d")


def note_cctp(note):
    """Note du chiffrage réduite à ce qu'un candidat doit lire : sans historique de version, code d'audit, prix ni renvoi interne."""
    n = (note or "").replace("par le BET", "par l'étude thermique")
    n = re.sub(r",?\s*0 € de licence", "", n)
    n = re.sub(r"\s*au lieu de [^.;]*", "", n)
    n = _PAR_INTERNE.sub("", n)
    n = _VERSION_TETE.sub("", n)
    phrases = [p.strip() for p in re.split(r"(?<=\.)\s+", n) if p.strip()]
    garde = [p for p in phrases if not _PHRASE_INTERNE.search(p)]
    out = " ".join(garde).strip(" .;,")
    out = re.sub(r"(\d)\.(\d)", r"\1,\2", out)          # virgule décimale
    out = re.sub(r"(?<![\w-])-(\d)", "−\\1", out)       # signe moins
    return out[:1].upper() + out[1:]


def marque(designation):
    return bool(_MARQUES.search(designation))


def quantite(l):
    """Quantité avec son unité quand elle n'est pas un nombre d'articles."""
    note, sol = l.get("note", ""), l["solution"]
    if "au m²" in note:
        return f"{l['quantite']} m²"
    if "Métré" in note:
        return f"{l['quantite']} m"
    if "(jours)" in sol:
        return f"{l['quantite']} j"
    return str(l["quantite"])


def lignes(*categories, filtre=None, prefixe=False):
    out = []
    for l in EST["capex_lignes"]:
        cat = l["categorie"]
        dedans = any(cat.startswith(c) for c in categories) if prefixe else cat in categories
        if dedans and (filtre is None or filtre(l)):
            out.append((l["schema"], l["solution"], quantite(l), note_cctp(l.get("note", ""))))
    return out


def est_switch(l):
    """Switchs et kits de pile des zones Egress, DMZ, NM et DT : ils vont au lot 1 avec le reste du réseau."""
    return l["solution"].startswith("Cisco Catalyst C9") or "StackWise" in l["solution"]


def est_badge(l):
    return "badge" in l["solution"].lower()


SURETE_CHIFFREE = any(l["categorie"] == "Sûreté" for l in EST["capex_lignes"])
NB_CAMERAS = CAB["par_type"]["camera"]
NB_BADGES = CAB["par_type"]["badge"]
VIDEO_30J_TO = {d: NB_CAMERAS * d * 1e6 * 86400 * 30 / 8 / 1e12 for d in (4, 8)}   # enregistrement continu, 30 jours
_inverseur = next((l for l in EST["capex_lignes"] if "Inverseur de source" in l["solution"]), None)
DEPART = PRA.DEPART_TGBT


def quantites_lot4():
    if SURETE_CHIFFREE:
        q = lignes("Sûreté")
    else:  # chiffrage antérieur à la catégorie « Sûreté » : quantités du plan de câblage
        q = [("Caméras IP", "Caméra fixe PoE, ONVIF S/T, 802.1X, intérieur ou extérieur selon l'emplacement", str(NB_CAMERAS), ""),
             ("Lecteurs de badge", "Lecteur sans contact DESFire + unité de traitement locale (UTL) OSDP, posé", str(NB_BADGES), ""),
             ("VS-NVR1", "Enregistreur vidéo 2U, disques en RAID 6, logiciel VMS + licences par caméra", "1", "")]
    if not any("contrôle d'accès" in b.lower() and "logiciel" in b.lower() for _, b, _, _ in q):
        q.append(("Contrôle d'accès", "Logiciel de contrôle d'accès et licences des lecteurs, sur une VM de la zone SRV (10.13.48.61) "
                  "fournie par l'IUT", "1", ""))
    return q


def opex(motif):
    return next((o for o in EST["opex"] if motif in o["detail"] or motif in o["poste"]), None)


def maintenance(critiques=None, autres=None, supports="disques"):
    """Bloc « Maintenance » d'un lot, selon la décision D4 (GTR 4 h pour les équipements critiques, J+1 pour les autres)."""
    l = ["Support du constructeur, correctifs et remplacement du matériel pendant 3 ans au moins à compter de l'admission. " + V21]
    if critiques:
        l.append(f"Garantie de rétablissement de 4 h, 24 h/24 et 7 j/7, pièces, main-d'œuvre et déplacement compris : {critiques}. " + V21)
    if autres:
        l.append(f"Garantie de rétablissement le jour ouvré suivant l'appel (J+1) : {autres}. " + V21)
    if supports == "disques":
        l.append("Les disques et supports de stockage défectueux restent à l'IUT, qui les fait détruire par une filière certifiée "
                 "(certificat de destruction) : ils contiennent des données personnelles. " + V21)
    elif supports == "configuration":
        l.append("Un équipement rendu au constructeur l'est après effacement sécurisé de sa configuration (secrets, certificats), "
                 "constaté par l'IUT. " + V21)
    return ("Maintenance", l)


def rocades_communes():
    """Locaux dont les deux voies de rocade suivent la même suite de locaux dans le plan de câblage."""
    voies = {}
    for r in CAB.get("rocades", []):
        voies.setdefault(r["local"], set()).add(r["chemin"])
    return sorted(loc for loc, chemins in voies.items() if len(chemins) < 2)


def ventilation_locaux():
    """Ventilation de chaque local technique d'après l'étude du point 14."""
    actifs = [f"{x['local']} : {x['ventilation']}" for x in ENE["locaux"] if "grille" not in x["ventilation"]]
    passifs = [x["local"] for x in ENE["locaux"] if "grille" in x["ventilation"]]
    t = [x["t_ete"] for x in ENE["locaux"]]
    return (" ; ".join(actifs) + (f" ; grilles hautes et basses pour {' et '.join(passifs)}" if passifs else "")
            + f" (température d'été calculée de {fr(min(t))} à {fr(max(t))} °C)")


# ---------------------------------------------------------------------------
# Clauses communes à tous les lots
# ---------------------------------------------------------------------------
COMMUNES = {
    "Sécurité": [
        "Accès distant du titulaire uniquement par le VPN d'administration et le bastion de l'IUT, avec un compte nominatif par "
        "intervenant, ouvert pour la durée de l'intervention (PSSI M-ADM-2). Aucun accès permanent ; aucun boîtier de "
        "télémaintenance ni modem cellulaire du titulaire, y compris intégré au matériel (groupe électrogène, onduleurs). " + V21,
        "Comptes et mots de passe par défaut changés ou désactivés à l'installation, secrets remis dans le coffre de l'IUT (M-ADM-3).",
        "Correctifs de sécurité : le titulaire signale sous 48 h toute vulnérabilité critique publiée sur un produit livré et fournit le "
        "correctif ou une mesure de contournement ; installation sous 72 h pour les équipements exposés (M-POS-2).",
        "Notification à l'IUT, sous 24 h, de tout incident de sécurité touchant le titulaire et pouvant affecter le marché.",
        "Durée de support des logiciels et micrologiciels d'au moins 7 ans après la livraison, date de fin de support indiquée dans l'offre.",
        "Aucune fonction de connexion à un service en nuage du fabricant activée par défaut ; toute fonction de ce type est décrite et "
        "désactivable.",
        "Confidentialité : le titulaire et ses sous-traitants sont tenus au secret sur les informations du SI (schémas, adresses, "
        "configurations), y compris après le marché."],
    "Maintenance et garanties " + V21: [
        "La garantie de rétablissement court de l'appel de l'IUT au retour au fonctionnement nominal ; elle comprend le diagnostic, les "
        "pièces, la main-d'œuvre et le déplacement. Pénalités par heure de retard fixées au CCAP.",
        "Délais par équipement (décision commune à tous les lots, reprise par le PRA, volet juridique) : 4 h, 24 h/24 et 7 j/7 pour les "
        "équipements critiques (" + ", ".join(PRA.GTR_4H) + ") ; jour ouvré suivant pour les autres.",
        "Rapport d'intervention remis à chaque appel (cause, pièces remplacées, durée) ; bilan annuel de la maintenance."],
    "Environnement (obligatoire : loi Climat et résilience)": [
        "Consommation électrique mesurée et déclarée (fiche constructeur), alimentations certifiées 80 PLUS Platinum au moins pour "
        "les serveurs.",
        "Équipements réparables : disponibilité des pièces détachées pendant la durée du support, indice de réparabilité quand il existe ; "
        "le matériel reconditionné garanti est accepté en variante.",
        "Reprise et traitement des emballages et des équipements remplacés par une filière agréée (DEEE), avec certificat.",
        "Livraisons regroupées, emballages réduits et recyclables."],
    "Documentation et transfert de compétences": [
        "Dossier des ouvrages exécutés (DOE) : plans de récolement, configurations finales, schémas, mots de passe dans le coffre, "
        "procédures d'exploitation, en français.",
        "Formation des administrateurs de l'IUT sur chaque produit (durée indiquée dans l'offre).",
        "Réversibilité : à la fin du marché, le titulaire remet tout ce qui permet à l'IUT ou à un autre prestataire de reprendre "
        "l'exploitation (configurations, licences, documentation), sans surcoût."],
    "Recette": [
        "Vérification d'aptitude (VA) : tests décrits dans le plan de recette proposé par le titulaire et validé par l'IUT, dont les "
        "tests de recette de la matrice des flux (RLI-P09-matrice-flux.pdf, section 7) pour les lots qui touchent au filtrage.",
        "Vérification de service régulier (VSR) : un mois d'exploitation sans anomalie bloquante avant l'admission.",
        "Les anomalies sont classées bloquantes, majeures ou mineures ; l'admission est prononcée sans anomalie bloquante ni majeure."],
}

# ---------------------------------------------------------------------------
# Lots
# ---------------------------------------------------------------------------
_communes = rocades_communes()
_s3 = opex("Object Lock")
_disques = PRA._disques

LOTS = [
    {
        "num": 1, "titre": "Câblage structuré et équipements actifs du réseau",
        "objet": "Fourniture, pose et recette du câblage du bâtiment (cuivre Cat6A, fibre OM4, chemins de câbles, panneaux et cordons de brassage) et "
                 "fourniture, installation et configuration des switchs, des bornes Wi-Fi et des contrôleurs Wi-Fi.",
        "references": ["plan_cablage (point 04)", "plan_adressage (point 05)", "architecture_l2 et architecture_l3 (points 03 et 06)",
                       "étude Wi-Fi (point 10)"],
        "quantites": lignes("Câblage", "Cœur", "Distribution", "Accès")
                     + lignes("Egress / WAN", "DMZ", "Net Management", "Datacenter", filtre=est_switch),
        "exigences": [
            ("Câblage", [
                f"{CAB['prises']} prises RJ45 catégorie 6A (classe EA), liaisons de 90 m au plus (la plus longue fait {CAB['lien_max_m']:.0f} m), "
                "certifiées à 100 % au testeur de niveau IV ou supérieur, rapports de test remis.",
                "Rocades en fibre OM4, 12 brins, doublées : deux câbles par local technique vers la salle serveur, par deux cheminements "
                "physiquement séparés (colonnes Nord et Sud)."
                + (f" Là où le plan de câblage fait suivre aux deux voies la même suite de locaux ({', '.join(_communes)}), le titulaire "
                   "réalise un second cheminement séparé (autre chemin de câbles ou fourreau dédié) ou indique l'écart dans son mémoire "
                   "technique. " + V21 if _communes else ""),
                "Repérage conforme à TIA-606 (étiquette identique à la prise et au panneau), plans de récolement par niveau.",
                "Mise en œuvre selon EN 50174-2 ; cheminements séparés des courants forts ; respect du classement au feu des câbles "
                "(Euroclasse Cca-s1b,d1,a1 au minimum dans les circulations). " + V21]),
            ("Switchs", [
                "Couches cœur et distribution en paires virtualisées (une seule entité logique, de type StackWise Virtual ou équivalent), "
                "liens montants 10G au minimum, 40G entre les membres d'une paire (modules compris).",
                "Switchs d'accès PoE+ (802.3at) sur tous les ports, budget PoE suffisant pour les bornes Wi-Fi, téléphones, caméras.",
                "Fonctions de sécurité exigées : 802.1X et MAB avec VLAN dynamique, ACL téléchargeables, changement d'autorisation (CoA, "
                "RFC 5176), DHCP snooping, inspection ARP dynamique, IP source guard, protection BPDU et root guard (PSSI M-RES-2 et M-RES-3).",
                "VRF-lite, OSPFv3 IPv4 et IPv6 avec authentification, BFD, IPv6 complet (RA guard, DHCPv6 guard).",
                "Administration par SSH v2, NETCONF/RESTCONF et SNMPv3 seulement ; Telnet, HTTP et SNMPv1/v2c désactivables."]),
            ("Wi-Fi", [
                "Bornes Wi-Fi 6E au minimum, WPA3-Entreprise et WPA2/WPA3 de transition pour eduroam, 802.11r/k/v.",
                "Deux contrôleurs en haute disponibilité avec reprise des sessions ; détection des bornes pirates ; portail invités avec "
                "isolation des clients (PSSI M-RES-4).",
                "Étude de couverture après pose (mesures sur site) remise avec la recette."]),
            maintenance("cœur (CL-SW), distribution (DL-SW) et contrôleurs Wi-Fi (WLC)",
                        "switchs d'accès (AL-SW), bornes Wi-Fi et switchs des zones (EL-SW, DM-SW, NM-SW, DT-SW)", supports="configuration"),
        ],
        "hors_lot": "Pare-feu (lot 2), serveurs (lot 3), caméras et badgeuses (lot 4) ; énergie, baies et locaux techniques (lot 5).",
    },
    {
        "num": 2, "titre": "Sécurité périmétrique : routeurs de bordure, pare-feu, VPN",
        "objet": "Fourniture, installation, configuration et maintenance des routeurs de bordure, du pare-feu externe (Internet, DMZ, VPN) "
                 "et du pare-feu interne (entre les zones), en grappes à haute disponibilité.",
        "references": ["architecture_l3 (point 03)", "matrice_flux, pssi, analyse_risque (point 09)", "interconnexion Internet (point 08)"],
        "quantites": lignes("Sécurité interne") + lignes("Egress / WAN", filtre=lambda l: not est_switch(l)),
        "exigences": [
            ("Architecture", [
                "Deux pare-feu de constructeurs différents en cascade : un pare-feu externe et un pare-feu interne, chacun en grappe "
                "actif/passif avec synchronisation des sessions (guide ANSSI PA-044).",
                "Pare-feu interne : produit bénéficiant d'une qualification ANSSI, livré et maintenu dans une version qualifiée "
                "(PSSI M-RES-1, mesure 42 du guide d'hygiène).",
                "Routeurs de bordure : eBGP vers deux opérateurs, iBGP entre eux, BFD, annonce conditionnelle, IPv4 et IPv6.",
                "Sécurité du routage : sessions BGP authentifiées (TCP-AO, à défaut MD5), GTSM, filtrage des préfixes reçus et annoncés, "
                "nombre maximal de préfixes, validation RPKI si l'opérateur la propose, plan de contrôle protégé (CoPP), BFD seulement "
                "vers les voisins configurés (guide ANSSI de configuration de BGP). " + V21]),
            ("Filtrage", [
                "Mise en œuvre de la matrice des flux du point 09 (toutes les règles Fxx de RLI-P09-matrice-flux.csv), chaque règle nommée par son "
                "identifiant Fxx et commentée ; ordre de déploiement : autorisations, puis refus explicites, puis refus par défaut ; "
                "politique par défaut : tout refuser et journaliser. " + V21,
                "Profils d'inspection par flux (IPS, antivirus, filtrage d'URL, inspection TLS avec liste d'exclusion : banques, santé, "
                "sites des administrations, messageries personnelles) ; débit mesuré avec ces profils actifs indiqué dans l'offre, pour "
                "10 Gb/s de trafic entre zones au minimum. " + V21,
                "Journaux en syslog sur TLS vers les collecteurs de l'IUT, horodatage NTP. Journal légal complet (adresses et ports source "
                "et destination avant et après NAT, volumes), conservé 1 an par l'IUT ; journal du proxy (URL complètes), conservé 6 mois "
                "(politique de journalisation du volet juridique). " + V21]),
            ("Accès distant", [
                "VPN d'administration en IPsec IKEv2, authentification par certificat et second facteur ; pas de VPN SSL exposé "
                "(écart E2 de la matrice).",
                "Accès limité au bastion de l'IUT (règle F38)."]),
            ("Abonnements et revue", [
                "Abonnements de sécurité (signatures IPS, antivirus, réputation) pendant 3 ans au moins.",
                "Revue annuelle des règles avec l'IUT (compteurs, règles inutilisées) comprise dans le marché."]),
            maintenance("routeurs EL-RTR, pare-feu EL-FGT et EL-SNS", None, supports="configuration"),
        ],
        "hors_lot": "Switchs de la zone Egress (lot 1), accès Internet et liaison avec le site jumeau (Digne ou Gap) (marchés opérateurs).",
    },
    {
        "num": 3, "titre": "Datacenter : serveurs, virtualisation, sauvegarde, plateforme d'IA",
        "objet": "Fourniture, installation et configuration des serveurs des trois grappes de virtualisation (administration, datacenter, "
                 "DMZ), du serveur de sauvegarde et de la sauvegarde externalisée ; tranche optionnelle : plateforme d'IA locale.",
        "references": ["architecture_l2, section 11 (grappes)", "énergie et refroidissement (point 14)", "stockage et sauvegarde (point 15)",
                       "pssi, matrice_flux (point 09)", "PRA, volet juridique (point 19)"],
        "quantites": lignes("DMZ", "Net Management", "Datacenter", filtre=lambda l: not est_switch(l))
                     + ([("Sauvegarde externalisée", re.sub(r"\s*\([^()]*SecNumCloud[^()]*\)", "", note_cctp(_s3["detail"])), "1",
                          "Abonnement annuel, 3 ans ; hébergeur : voir l'exigence sur la copie externalisée " + V21)] if _s3 else []),
        "exigences": [
            ("Serveurs et virtualisation", [
                "Serveurs au format rack, double alimentation, contrôleur de gestion à distance (iDRAC ou équivalent) avec comptes "
                "nominatifs et chiffrement, raccordé au réseau de gestion seulement.",
                "Grappes de deux nœuds avec témoin de quorum, stockage local répliqué, migration à chaud ; hyperviseurs de la DMZ physiquement "
                "séparés de ceux qui portent l'annuaire (tier 0, guide ANSSI PA-099).",
                "Durcissement des systèmes selon le guide ANSSI GNU/Linux, niveau intermédiaire (PSSI M-POS-3)."]),
            ("Sauvegarde", [
                "Règle 3-2-1-1-0 : serveur de sauvegarde hors domaine, sauvegarde de toutes les VM et de tous les conteneurs chaque nuit ; "
                + (f"copie hors ligne sur {PRA.NB_DISQUES} disques amovibles de {PRA.TAILLE_DISQUE} en rotation hebdomadaire (un branché, "
                   "un dans un coffre ignifuge, un hors site) ; " if _disques else "copie hors ligne sur supports amovibles rangés dans un "
                   "coffre ignifuge ; ")
                + "copie externalisée immuable (verrouillage des objets S3 Object Lock en mode conformité), mise à jour chaque nuit. " + V21,
                f"Hébergeur de la copie externalisée : {J.SECNUMCLOUD}. Données chiffrées avant l'envoi avec une clé détenue par l'IUT "
                "seulement (PSSI M-SAV-1) ; contrat de sous-traitance (RGPD art. 28). " + V21,
                "Test de restauration complet d'une VM et d'un contrôleur de domaine pendant la recette."]),
            ("Tranche optionnelle : plateforme d'IA locale", [
                "Besoin exprimé en performance et non en matériel : servir un modèle ouvert d'au moins 1 000 milliards de paramètres "
                "(architecture à experts acceptée), avec une latence et un nombre d'utilisateurs simultanés à fixer par le point 11 ; le "
                "candidat propose le nombre de GPU, la mémoire et le réseau d'interconnexion. " + V21,
                "Fonctionnement entièrement hors ligne : aucune dépendance à un service en nuage, modèles et mises à jour importés par "
                "l'IUT (PSSI M-IA-1 et M-IA-2).",
                "Passerelle d'accès : authentification par l'annuaire, quotas, cloisonnement des conversations, journal des requêtes "
                "paramétrable (durées de la politique de journalisation), API compatible avec les outils courants.",
                "Consommation électrique et dissipation thermique déclarées par nœud : au-delà de la réserve des onduleurs et de la "
                "climatisation de la salle (lot 5), l'offre décrit l'adaptation nécessaire. " + V21]),
            maintenance("hyperviseurs DT-PVE et NM-PVE, serveur de sauvegarde DT-BKP1",
                        "hyperviseurs et témoin de la DMZ (DM-PVE, DM-WITNESS), témoin NM-WITNESS"),
        ],
        "hors_lot": "Switchs du datacenter (lot 1), énergie, climatisation et extinction (lot 5).",
    },
    {
        "num": 4, "titre": "Sûreté : vidéoprotection et contrôle d'accès",
        "objet": "Fourniture, installation et mise en service des caméras IP, de l'enregistreur vidéo VS-NVR1 et de son logiciel, des "
                 "lecteurs de badge, des unités de traitement locales et du logiciel de contrôle d'accès.",
        "references": ["plan_cablage (emplacements des caméras et des badgeuses)", "volet juridique (point 19) : AIPD, durées",
                       "matrice_flux (règles F24 à F27, F58, F67 et F68)"],
        "quantites": quantites_lot4(),
        "exigences": [
            ("Cybersécurité des équipements", [
                "Caméras et UTL compatibles 802.1X EAP-TLS (à défaut MAB), HTTPS et chiffrement des flux, SNMPv3, journaux en syslog ; "
                "aucun service en nuage ni connexion pair à pair, Telnet et UPnP désactivés (guide ANSSI PA-072).",
                "Produits certifiés CSPN ou qualifiés par l'ANSSI quand l'offre existe (contrôle d'accès, VMS) ; sinon, le candidat décrit "
                "sa politique de correctifs.",
                "Caméras conformes ONVIF (profils S et T) : c'est l'enregistreur qui ouvre les flux (règle F24), la caméra n'initie aucune "
                "connexion.",
                "Badges et lecteurs : technologie sans contact à chiffrement robuste (de type MIFARE DESFire EV2/EV3 ou équivalent, pas de "
                "MIFARE Classic) ; liaison lecteur-UTL en OSDP v2 canal sécurisé, pas de Wiegand ; pas de biométrie."]),
            ("Enregistrement " + V21, [
                "Enregistreur dédié (repère VS-NVR1), au format 2U, posé dans la baie 2 de la salle serveur, en zone SRV (10.13.48.60), "
                "double alimentation (voies A et B), disques en RAID 6. Le logiciel de vidéo (VMS) tourne sur l'enregistreur, pas sur "
                "les hyperviseurs du datacenter. " + V21,
                f"Capacité utile suffisante pour 30 jours d'enregistrement continu des {NB_CAMERAS} caméras à 8 Mb/s, soit ≈ "
                f"{VIDEO_30J_TO[8]:.0f} To ({VIDEO_30J_TO[4]:.0f} To à 4 Mb/s, H.265) ; durée de conservation bornée à 30 jours par "
                "paramétrage, quelle que soit la capacité installée. " + V21]),
            ("Protection des données (RGPD)", [
                "Aucune caméra dans un lieu de pause (foyer, salle de repos), une salle de cours, un bureau ou des sanitaires ; masquage "
                "dynamique des zones privatives et de la voie publique dans l'image ; champ de chaque caméra validé par l'IUT avant la "
                "mise en service (voir l'AIPD du volet juridique). " + V21,
                "Durées paramétrables et appliquées automatiquement : images 30 jours au plus, journal des passages 3 mois.",
                "Comptes nominatifs pour la consultation, journal des consultations et des exports, export chiffré.",
                "Panneaux d'information fournis et posés à chaque entrée."]),
            ("Exploitation", [
                "Intervention du titulaire à distance uniquement par le bastion de l'IUT (clauses communes) ; le prestataire du lot n'a "
                "aucun accès direct au réseau des objets.",
                "Correctifs des micrologiciels pendant toute la durée du support, appliqués depuis l'administration de l'IUT."]),
            maintenance(None, "caméras, lecteurs et UTL, enregistreur VS-NVR1"),
        ],
        "hors_lot": "Câblage et switchs (lot 1), VM du logiciel de contrôle d'accès (lot 3), alimentation secourue de la salle serveur et "
                    "des locaux techniques (lot 5).",
        "attention": ("Avant la consultation : retirer la caméra prévue dans un lieu de pause ("
                      + ", ".join(c[0] for c in J.CAMERAS if c[3] == "à retirer") + ") et demander l'autorisation "
                      "préfectorale pour les caméras qui filment des lieux ouverts au public (entrées, hall, parkings), selon la position "
                      "du DPO." if J.LIEU_DE_PAUSE_FILME else
                      "Avant la mise en service : autorisation préfectorale pour les caméras qui filment des lieux ouverts au public (entrées, "
                      "hall, parkings) et validation par le DPO du champ de chaque caméra." if J.LIEU_PUBLIC_FILME else
                      "Caméras limitées aux accès contrôlés des locaux techniques (porte badgée) : aucune ne filme un lieu ouvert au "
                      "public, pas d'autorisation préfectorale. Avant la mise en service : validation par le DPO du champ de chaque caméra."),
    },
    {
        "num": 5, "titre": "Énergie et locaux techniques", "nouveau": True,
        "objet": "Fourniture, pose, raccordement, essais et maintenance du groupe électrogène, de son inverseur de source et de leur génie "
                 "civil, du tableau électrique informatique (TD-INFO), des onduleurs et des PDU ; climatisation de la salle serveur, "
                 "ventilation des locaux techniques, extinction automatique, plancher technique, protections contre l'eau et baies "
                 "(étude du point 14). Marché de travaux, sous le CCAG-Travaux.",
        "references": ["énergie et refroidissement, BET des locaux techniques (point 14)", "plan_cablage (baies, locaux techniques)",
                       "pssi (mesures M-PHY) et matrice_flux (point 09)", "PRA, volet juridique (point 19)"],
        "quantites": lignes("Énergie", prefixe=True, filtre=lambda l: not est_badge(l)),
        "recurrent": [(o["poste"], note_cctp(o["detail"])) for o in ENE["opex"] if "Électricité" not in o["poste"]],
        "exigences": [
            ("Groupe électrogène", [
                f"Groupe diesel neuf (HVO accepté en variante), 400 V triphasé, d'au moins {GE['prp_kva']} kVA en puissance continue (PRP) "
                f"et {GE['esp_kva']} kVA en secours (ESP) selon la NF ISO 8528-1, pour un besoin calculé de {fr(GE['besoin_kva'])} kVA "
                f"(onduleurs en recharge, climatisation, TD-INFO, locaux techniques) ; charge réelle maximale ≈ {GE['charge_max_pct']} % de "
                "la PRP. Choix sur la PRP : une coupure peut durer plusieurs jours.",
                "Démarrage automatique sur ordre de l'inverseur, trois tentatives, prise de charge en 15 s au plus après la coupure ; "
                "préchauffage permanent du moteur ; batterie de démarrage avec chargeur et alarme ; démarrage et arrêt manuels sur place.",
                "Régulation électronique de classe G2 au moins (NF ISO 8528-5) ; alternateur à excitation AREP ou PMG, qui maintient un "
                "courant de court-circuit d'environ 3 In pendant 10 s pour le déclenchement des protections ; compatibilité avec les "
                "onduleurs en ligne démontrée (fréquence, distorsion, stabilité) par un essai commun.",
                "Conformité NF ISO 8528 (parties 1, 5 et 6) et NF EN ISO 8528-13 (sécurité) ; niveau de puissance acoustique garanti "
                "(directive 2000/14/CE)."]),
            ("Inverseur de source", [
                f"Inverseur automatique {DEPART} conforme à la NF EN 60947-6-1, en tête du TD-INFO : interverrouillage mécanique et "
                "électrique, transfert à coupure (jamais de marche en parallèle avec le réseau public), neutre commuté selon le schéma de "
                "liaison à la terre.",
                "Temporisations réglables : confirmation du défaut du réseau (3 s, les onduleurs couvrent les microcoupures), retour sur "
                "le réseau après 2 min de tension stable, marche à vide de 5 min du groupe avant l'arrêt.",
                "Commande manuelle de secours et by-pass de maintenance : intervention sur l'inverseur sans couper la salle serveur ; "
                "reports d'état (position, défaut) vers la supervision."]),
            ("Génie civil, raccordement, conformité", [
                "Dalle en béton armé, plots antivibratiles, fourreaux entre le groupe et le bâtiment, clôture et portillon fermés à clé "
                "(clés sur la liste nominative de la PSSI, M-PHY-1).",
                "Raccordement : câble de puissance en fourreau dimensionné pour une chute de tension de 2 % au plus entre le groupe et "
                f"l'inverseur, câble de commande, circuit des auxiliaires du groupe, départ {DEPART} au TGBT pour la voie « réseau ».",
                "Installation conforme à la NF C 15-100 (partie 5-55, section 551, groupes générateurs) : protections, sélectivité avec le "
                "TGBT, schéma de liaison à la terre, liaisons équipotentielles, coupure d'urgence.",
                "Le groupe est une source de remplacement, pas une source de sécurité : il n'alimente ni l'éclairage de sécurité ni le "
                "système de sécurité incendie du bâtiment, qui gardent leurs propres sources ; avis du bureau de contrôle sur l'installation.",
                "Vérification initiale par un organisme accrédité avant la mise en service (Code du travail, art. R4226-14), rapport remis "
                "à l'IUT."]),
            ("Implantation, carburant, bruit", [
                "Groupe en extérieur, façade est, sur dalle près de l'entrée du parking (accès du camion de gazole), hors zone inondable : "
                "jamais au sous-sol ; échappement orienté à l'opposé des façades, à 8 m au moins des prises d'air neuf, des fenêtres "
                "ouvrantes et des unités extérieures de climatisation.",
                f"Cuve intégrée double paroi d'au moins {GE['cuve_l']} l, avec détecteur de fuite entre les parois (elle tient lieu de "
                "rétention) ; remplissage depuis l'extérieur avec limiteur ; jauge remontée à la supervision ; autonomie sans "
                f"ravitaillement d'au moins {GE['autonomie_h']} h à la charge moyenne et {GE['autonomie_75_h']} h à 75 % de la PRP.",
                "Capot insonorisé (65 dB(A) au plus à 7 m) ; émergence en limite de propriété de 5 dB(A) au plus le jour et 3 dB(A) la nuit "
                "(Code de la santé publique, art. R1336-6 et R1336-7), mesurée à la réception ; essais programmés en journée.",
                "Installation non classée au titre des ICPE (rubrique 2910 : déclaration à partir de 1 MW thermique ; rubrique 4734 : à "
                "partir de 50 t de produits pétroliers) : le titulaire le confirme avec les caractéristiques du groupe livré."]),
            ("Supervision et cybersécurité", [
                "Contrôleur du groupe et inverseur communicants en SNMPv3 ou en Modbus TCP en lecture seule, raccordés au VLAN de gestion "
                "technique du bâtiment (VRF IOT) ; remontées : réseau présent, groupe en marche, inverseur sur groupe, défauts, niveau de "
                "carburant, batterie de démarrage ; contacts secs en secours.",
                "Aucune commande à distance (démarrage, arrêt, transfert) par le réseau ; aucun modem cellulaire ni service de "
                "télésurveillance en nuage ; si le titulaire télésurveille, il passe par le bastion de l'IUT (clauses communes, PSSI M-ADM-2).",
                "Mots de passe par défaut changés, micrologiciel maintenu pendant toute la durée du support, horloge NTP, journaux en "
                "syslog vers les collecteurs de l'IUT ; mêmes exigences pour les cartes réseau des onduleurs, des PDU et des climatiseurs."]),
            ("Onduleurs, tableau et distribution", [
                f"Deux onduleurs en ligne double conversion (NF EN 62040-3) de {fr(OND['capacite'] / 1000)} kVA, voies A et B, chacun avec "
                f"un pack de batteries externe : un seul onduleur porte toute la salle ({OND['taux_degrade']} % de charge) pendant "
                f"{OND['autonomie_degrade']} min au moins ; une carte réseau SNMPv3 par onduleur.",
                f"Arrêt ordonné des serveurs compatible NUT : si le groupe n'a pas repris {PRA.T_ARRET} min après la coupure (onduleur "
                f"encore sur batterie), la séquence d'arrêt commence et se termine à T0 + {PRA.T_FIN} min.",
                "Onduleurs des locaux techniques (line-interactive, rackables) : autonomie d'au moins "
                f"{min(x['autonomie'] for x in ENE['locaux'])} min à la charge typique du local le plus chargé, qui suffit au "
                "pont avant la reprise par le groupe (≈ 15 s) ; sensibilité réglée pour tolérer la fréquence du groupe.",
                "Tableau électrique informatique (TD-INFO) et coffrets des locaux techniques : départs et protections différentielles de "
                "l'étude du point 14 (type B pour les onduleurs, type F pour la climatisation, type A SI ou F dans les locaux techniques), "
                "sélectivité vérifiée ; PDU managées et métrées, en SNMPv3."]),
            ("Climatisation et locaux techniques", [
                f"Climatisation de la salle serveur en redondance N+1 : chaque unité ({fr(CLIM['unite_kw'])} kW froid) couvre seule la "
                f"charge de pointe ({fr(CLIM['q_pointe'])} kW) ; relance automatique après une coupure (contacteur temporisé, compresseur "
                f"inverter) ; alarmes reportées. Sans climatisation, la salle atteint 35 °C en {fr(BET['salle']['t35_min'])} min : la "
                "relance sur le groupe est vérifiée à la réception.",
                f"Ventilation des locaux techniques selon l'étude du point 14 : {ventilation_locaux()}.",
                "Confinement d'allée froide (obturateurs des U vides, rideaux) ; sondes de température et d'humidité remontées à la supervision."]),
            ("Protection contre l'eau et le feu", [
                "Plancher technique surélevé, baies et onduleurs sur socles, batardeau amovible à la porte et clapet anti-retour sur "
                "l'évacuation des condensats (désignations du tableau des quantités) ; câble de détection de fuite sous le plancher avec "
                "centrale, alarme remontée à la supervision et à l'astreinte.",
                "Détection incendie raccordée au SSI du bâtiment, extincteurs CO2 ; extinction automatique par gaz inerte (IG-541) avec "
                "détection précoce par aspiration, conçue, installée et maintenue selon la règle APSAD R13 par un installateur certifié : "
                "alarme sonore et lumineuse temporisée avant l'émission, commande manuelle et inhibition à la porte, essai d'étanchéité de "
                "la salle à la réception."]),
            ("Baies", [
                "Baies de la salle serveur et des locaux techniques livrées, posées et mises à la terre avant le câblage (planning "
                "coordonné avec le lot 1) ; portes ventilées, obturateurs des U vides."]),
            ("Essais et réception", [
                "Essai de réception du groupe sur banc de charge pendant 4 h, par paliers jusqu'à 100 % de la PRP (NF ISO 8528-6), puis "
                "coupure réelle du réseau hors période de cours : temps de démarrage et de transfert mesurés, onduleurs sans décharge "
                "prolongée, séquence NUT non déclenchée, climatisation relancée, retour au réseau temporisé.",
                "Essai de la séquence d'arrêt NUT, groupe volontairement bloqué : serveurs arrêtés dans l'ordre avant la fin de "
                "l'autonomie, puis redémarrés dans l'ordre au retour du réseau.",
                "Mesure acoustique en limite de propriété ; DOE : schéma unifilaire, réglages de l'inverseur et des protections, "
                "procès-verbaux, notices en français, registre d'essais ouvert."]),
            ("Maintenance et exploitation", [
                "Support du constructeur, pièces et remplacement du matériel pendant 3 ans au moins à compter de l'admission.",
                "Garantie de rétablissement de 4 h, 24 h/24 et 7 j/7, pièces, main-d'œuvre et déplacement compris : onduleurs et "
                "climatiseurs de la salle serveur. Groupe électrogène et inverseur de source : intervention sous 4 h, 24 h/24, pendant une "
                "coupure du réseau public (groupe en service ou appelé à démarrer), jour ouvré suivant sinon.",
                "Garantie de rétablissement le jour ouvré suivant l'appel (J+1) : onduleurs des locaux techniques, PDU, extracteurs, "
                "mini-split, détections.",
                "Maintenance préventive du groupe et de l'inverseur : deux visites par an (huile, filtres, liquide de refroidissement, "
                "courroies, batterie de démarrage, contrôle de l'inverseur) ; essai mensuel automatique de 1 h en charge réelle et essai "
                "annuel de 2 h sur banc de charge à 75 % de la PRP, tracés dans le registre.",
                "Livraison de gazole sous 24 h pendant une coupure prolongée (contrat ou bon de commande signé à l'avance, astreinte du "
                "fournisseur) ; analyse annuelle et traitement du gazole stocké.",
                "Climatisation, extinction (visite annuelle selon la règle APSAD R13) et onduleurs (remplacement préventif des batteries) : "
                "contrats compris dans l'offre, prix annuels au bordereau."]),
        ],
        "hors_lot": "Contrôle d'accès des locaux (lot 4), câblage et switchs (lot 1), serveurs (lot 3). Réseau public et TGBT du bâtiment : "
                    "existants.",
        "attention": f"À vérifier sur site avant la consultation : réserve de puissance du TGBT ({BET['reserve_tgbt_kva']} kVA, départ "
                     f"{DEPART}), régime de neutre du bâtiment (TN-S supposé par l'étude) et emplacement exact du groupe sur la façade est.",
    },
]
for _lot in LOTS:
    _lot["ref"] = f"RLI-CCTP-{_lot['num']:03d}"


def couverture():
    """Lignes du CAPEX qui ne tombent dans aucun lot (hors prestations, réparties entre les lots)."""
    pris = {(a, b) for lot in LOTS for a, b, _, _ in lot["quantites"]}
    return [(l["categorie"], l["schema"], l["solution"]) for l in EST["capex_lignes"]
            if l["categorie"] != "Prestations" and (l["schema"], l["solution"]) not in pris]


# ---------------------------------------------------------------------------
# Guide : construire un cahier des charges et un CCTP (pour le client)
# ---------------------------------------------------------------------------
PIECES = [
    ("Cahier des charges fonctionnel", "Le besoin, en termes de services rendus et de contraintes, sans solution imposée. Il précède le "
     "marché et sert à le préparer (et au sourçage auprès des fournisseurs)."),
    ("Règlement de la consultation (RC)", "Comment répondre : procédure, pièces à fournir, critères de choix et leur pondération."),
    ("CCAP", "Clauses administratives : prix, délais, pénalités, garanties, réception. Renvoie au CCAG-TIC (fournitures et services "
     "informatiques : lots 1 à 4) ou au CCAG-Travaux (câblage du lot 1, lot 5 énergie et locaux techniques). " + V21),
    ("CCTP", "Clauses techniques : ce qui doit être livré et comment le vérifier. C'est l'objet des modèles de ce dossier."),
    ("BPU et DQE", "Bordereau des prix unitaires et détail quantitatif estimatif : la grille de prix que remplissent les candidats."),
]

DEMARCHE = [
    "Partir du besoin et de l'architecture (dossier de conception RudyLink Infrastructure), pas d'un catalogue de produits.",
    "Allotir : un lot par métier (câblage et réseau, sécurité, serveurs, sûreté, énergie et locaux techniques) ouvre la concurrence et "
    "évite qu'un seul titulaire maîtrise tout le SI. " + V21,
    "Faire un sourçage avant la consultation (rencontres fournisseurs, UGAP et centrales d'achat) pour vérifier que le besoin trouve preneur.",
    "Fixer les critères et leur poids, par exemple : valeur technique 45 %, prix 40 %, performance environnementale 15 % "
    "(un critère environnemental est obligatoire depuis la loi Climat et résilience).",
    "Choisir la procédure selon le montant estimé et les seuils européens en vigueur (révisés tous les deux ans), avec les services "
    "achats de l'AMU.",
    "Écrire des exigences vérifiables (« certifiées à 100 % au testeur », pas « de bonne qualité »), chacune reliée à un test de recette.",
    "Citer une marque seulement à titre d'exemple, suivie de « ou équivalent ».",
]

SOMMAIRE_CDC = [
    "Contexte et objectifs (enseignement, recherche, site jumeau (Digne ou Gap))",
    "Périmètre (bâtiment, salles, nombre d'usagers, services)",
    "Besoins fonctionnels par service (réseau filaire, Wi-Fi, téléphonie, serveurs, sécurité, sûreté, IA)",
    "Exigences non fonctionnelles : disponibilité (DMIA, PDMA, garanties de rétablissement), performances, sécurité (PSSI), conformité "
    "(RGPD, conservation des journaux), développement durable",
    "Contraintes : bâtiment occupé, calendrier universitaire, existant à reprendre, alimentation électrique et locaux techniques, "
    "compétences de l'équipe",
    "Organisation : MOA, MOE, comité de pilotage, recette",
    "Budget prévisionnel et calendrier",
]
