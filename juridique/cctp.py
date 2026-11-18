"""Point 19 : cahiers des clauses techniques particulières (CCTP) pour le client, 4 lots. Version 1, 18/11/2026.

Le client (l'AMU) achète en marché public : ces CCTP sont des modèles qu'il complète (le CCAP, le règlement de la
consultation et le bordereau de prix relèvent de ses services achats). Les quantités viennent du chiffrage
(chiffrage/estimation.json) et du plan de câblage, les exigences de sécurité de la PSSI (M-xx) et de la matrice (Fxx).
Les marques citées le sont à titre indicatif : un CCTP public décrit un besoin et ajoute « ou équivalent »
(principe d'égalité de traitement des candidats).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EST = json.loads((ROOT / "chiffrage" / "estimation.json").read_text(encoding="utf-8"))
CAB = json.loads((ROOT / "livrables" / "plan_cablage" / "resume.json").read_text(encoding="utf-8"))

# ---------------------------------------------------------------------------
# Clauses communes à tous les lots
# ---------------------------------------------------------------------------
COMMUNES = {
    "Sécurité": [
        "Accès distant du titulaire uniquement par le VPN d'administration et le bastion de l'IUT, avec un compte nominatif par "
        "intervenant, ouvert pour la durée de l'intervention (PSSI M-ADM-2). Aucun accès permanent, aucun boîtier de télémaintenance "
        "du titulaire sur le réseau.",
        "Comptes et mots de passe par défaut changés ou désactivés à l'installation, secrets remis dans le coffre de l'IUT (M-ADM-3).",
        "Correctifs de sécurité : le titulaire signale sous 48 h toute vulnérabilité critique publiée sur un produit livré et fournit le "
        "correctif ou une mesure de contournement ; installation sous 72 h pour les équipements exposés (M-POS-2).",
        "Notification à l'IUT, sous 24 h, de tout incident de sécurité touchant le titulaire et pouvant affecter le marché.",
        "Durée de support des logiciels et micrologiciels d'au moins 7 ans après la livraison, date de fin de support indiquée dans l'offre.",
        "Aucune fonction de connexion à un service en nuage du fabricant activée par défaut ; toute fonction de ce type est décrite et "
        "désactivable.",
        "Confidentialité : le titulaire et ses sous-traitants sont tenus au secret sur les informations du SI (schémas, adresses, "
        "configurations), y compris après le marché."],
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
        "tests de recette de la matrice des flux (matrice_flux.pdf, section 7) pour les lots qui touchent au filtrage.",
        "Vérification de service régulier (VSR) : un mois d'exploitation sans anomalie bloquante avant l'admission.",
        "Les anomalies sont classées bloquantes, majeures ou mineures ; l'admission est prononcée sans anomalie bloquante ni majeure."],
}

# ---------------------------------------------------------------------------
# Lots
# ---------------------------------------------------------------------------


def lignes(*categories, filtre=None):
    out = []
    for l in EST["capex_lignes"]:
        if l["categorie"] in categories and (filtre is None or filtre(l)):
            out.append((l["schema"], l["solution"], l["quantite"], l["note"] if "note" in l else ""))
    return out


def est_switch(l):
    """Switchs et kits de pile des zones Egress, DMZ, NM et DT : ils vont au lot 1 avec le reste du réseau."""
    return l["solution"].startswith("Cisco Catalyst C9") or "StackWise" in l["solution"]

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
                "Rocades en fibre OM4, 12 brins, doublées par deux chemins différents entre chaque local technique et la salle serveur.",
                "Repérage conforme à TIA-606 (étiquette identique à la prise et au panneau), plans de récolement par niveau.",
                "Mise en œuvre selon EN 50174 ; cheminements séparés des courants forts ; respect du classement au feu des câbles (Euroclasse "
                "Cca-s1,d1,a1 au minimum dans les circulations)."]),
            ("Switchs", [
                "Couches cœur et distribution en paires virtualisées (une seule entité logique, de type StackWise Virtual ou équivalent), "
                "liens montants 10G au minimum, 40G entre les membres du cœur.",
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
        ],
        "hors_lot": "Pare-feu (lot 2), serveurs (lot 3), caméras et badgeuses (lot 4) ; énergie et locaux techniques (lot séparé, point 14).",
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
                "Routeurs de bordure : eBGP vers deux opérateurs, iBGP entre eux, BFD, annonce conditionnelle, IPv4 et IPv6."]),
            ("Filtrage", [
                "Mise en œuvre de la matrice des flux du point 09 (56 règles), chaque règle nommée par son identifiant Fxx et commentée ; "
                "politique par défaut : tout refuser et journaliser.",
                "Profils d'inspection par flux (IPS, antivirus, filtrage d'URL, inspection TLS avec liste d'exclusion) ; débit mesuré avec "
                "ces profils actifs indiqué dans l'offre, pour 10 Gb/s de trafic entre zones au minimum.",
                "Journaux en syslog sur TLS vers les collecteurs de l'IUT, horodatage NTP ; journal NAT complet (traçabilité légale)."]),
            ("Accès distant", [
                "VPN d'administration en IPsec IKEv2, authentification par certificat et second facteur ; pas de VPN SSL exposé "
                "(écart E2 de la matrice).",
                "Accès limité au bastion de l'IUT (règle F38)."]),
            ("Maintenance", [
                "Abonnements de sécurité (signatures IPS, antivirus, réputation) et support constructeur pendant 3 ans au moins, "
                "remplacement du matériel en panne le jour ouvré suivant.",
                "Revue annuelle des règles avec l'IUT (compteurs, règles inutilisées) comprise dans le marché."]),
        ],
        "hors_lot": "Switchs de la zone Egress (lot 1), accès Internet et liaison avec le site jumeau (marchés opérateurs).",
    },
    {
        "num": 3, "titre": "Datacenter : serveurs, virtualisation, sauvegarde, plateforme d'IA",
        "objet": "Fourniture, installation et configuration des serveurs des trois grappes de virtualisation (administration, datacenter, "
                 "DMZ), du serveur de sauvegarde et de la sauvegarde externalisée ; tranche optionnelle : plateforme d'IA locale.",
        "references": ["architecture_l2 §11 (clusters)", "énergie et refroidissement (point 14)", "stockage et sauvegarde (point 15)",
                       "pssi, matrice_flux (point 09)"],
        "quantites": lignes("DMZ", "Net Management", "Datacenter", filtre=lambda l: not est_switch(l)),
        "exigences": [
            ("Serveurs et virtualisation", [
                "Serveurs au format rack, double alimentation, contrôleur de gestion à distance (iDRAC ou équivalent) avec comptes "
                "nominatifs et chiffrement, raccordé au réseau de gestion seulement.",
                "Grappes de deux nœuds avec témoin de quorum, stockage local répliqué, migration à chaud ; hyperviseurs de la DMZ physiquement "
                "séparés de ceux qui portent l'annuaire (tier 0, guide ANSSI PA-099).",
                "Durcissement des systèmes selon le guide ANSSI GNU/Linux, niveau intermédiaire (PSSI M-POS-3)."]),
            ("Sauvegarde", [
                "Règle 3-2-1 : serveur de sauvegarde hors domaine, copie hors ligne sur supports amovibles rangés dans un coffre ignifuge, "
                "copie externalisée immuable (verrouillage des objets en mode conformité).",
                "Hébergeur de la copie externalisée qualifié SecNumCloud, données en France, chiffrées avant l'envoi avec une clé détenue "
                "par l'IUT seulement (PSSI M-SAV-1).",
                "Test de restauration complet d'une VM et d'un contrôleur de domaine pendant la recette."]),
            ("Tranche optionnelle : plateforme d'IA locale", [
                "Besoin exprimé en performance et non en matériel : servir un modèle ouvert d'au moins 1 000 milliards de paramètres "
                "(architecture à experts accepté), avec une latence et un nombre d'utilisateurs simultanés à fixer par le point 11 ; le "
                "candidat propose le nombre de GPU, la mémoire et le réseau d'interconnexion.",
                "Fonctionnement entièrement hors ligne : aucune dépendance à un service en nuage, modèles et mises à jour importés par "
                "l'IUT (PSSI M-IA-1 et M-IA-2).",
                "Passerelle d'accès : authentification par l'annuaire, quotas, cloisonnement des conversations, journal des requêtes "
                "paramétrable (durées de la politique de journalisation), API compatible avec les outils courants.",
                "Consommation électrique et dissipation thermique déclarées par nœud : elles conditionnent l'énergie et le refroidissement "
                "de la salle serveur (point 14)."]),
        ],
        "hors_lot": "Switchs du datacenter (lot 1), énergie, climatisation et extinction (lot séparé, point 14).",
    },
    {
        "num": 4, "titre": "Sûreté : vidéoprotection et contrôle d'accès",
        "objet": "Fourniture, installation et mise en service des caméras IP, du logiciel d'enregistrement, des lecteurs de badge, des "
                 "unités de traitement locales et du logiciel de contrôle d'accès.",
        "references": ["plan_cablage (emplacements des caméras et des badgeuses)", "volet juridique (point 19) : AIPD, durées",
                       "matrice_flux (règles F24 à F27)"],
        "quantites": [("Caméras IP", "Caméras fixes PoE, intérieur et extérieur selon l'emplacement", CAB["par_type"]["camera"], ""),
                      ("Lecteurs de badge", "Lecteurs sans contact + unités de traitement locales (UTL)", CAB["par_type"]["badge"], ""),
                      ("Logiciel de vidéo", "VMS installé sur une VM du datacenter (zone SRV)", 1, ""),
                      ("Logiciel de contrôle d'accès", "Installé sur une VM du datacenter (zone SRV)", 1, "")]
                     + [(a, b, q, "ligne du chiffrage (point 18), qui ne couvre que la salle serveur et les locaux techniques : "
                         "à réévaluer pour les 11 lecteurs") for a, b, q, _ in lignes("Énergie / locaux", filtre=lambda l: "badge" in l["solution"])],
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
            ("Protection des données (RGPD)", [
                "Masquage dynamique des zones privatives et de la voie publique dans l'image ; champ de chaque caméra validé par l'IUT "
                "avant la mise en service (voir l'AIPD du volet juridique).",
                "Durées paramétrables et appliquées automatiquement : images 30 jours au plus, journal des passages 3 mois.",
                "Comptes nominatifs pour la consultation, journal des consultations et des exports, export chiffré.",
                "Panneaux d'information fournis et posés à chaque entrée."]),
            ("Exploitation", [
                "Intervention du titulaire à distance uniquement par le bastion de l'IUT (clauses communes) ; le prestataire du lot n'a "
                "aucun accès direct au réseau des objets.",
                "Correctifs des micrologiciels pendant toute la durée du support, appliqués depuis l'administration de l'IUT."]),
        ],
        "hors_lot": "Câblage et switchs (lot 1), serveurs qui hébergent les logiciels (lot 3).",
        "attention": "Avant la consultation : retirer la caméra prévue au foyer des étudiants (N0-LT01-P050) et demander l'autorisation "
                     "préfectorale pour les caméras qui filment des lieux ouverts au public (entrées, hall, parkings), selon la position du DPO.",
    },
]

# ---------------------------------------------------------------------------
# Guide : construire un cahier des charges et un CCTP (pour le client)
# ---------------------------------------------------------------------------
PIECES = [
    ("Cahier des charges fonctionnel", "Le besoin, en termes de services rendus et de contraintes, sans solution imposée. Il précède le "
     "marché et sert à le préparer (et au sourçage auprès des fournisseurs)."),
    ("Règlement de la consultation (RC)", "Comment répondre : procédure, pièces à fournir, critères de choix et leur pondération."),
    ("CCAP", "Clauses administratives : prix, délais, pénalités, garanties, réception. Renvoie au CCAG-TIC (fournitures et services "
     "informatiques) ou au CCAG-Travaux (câblage)."),
    ("CCTP", "Clauses techniques : ce qui doit être livré et comment on le vérifie. C'est l'objet des modèles de ce dossier."),
    ("BPU et DQE", "Bordereau des prix unitaires et détail quantitatif estimatif : la grille de prix que remplissent les candidats."),
]

DEMARCHE = [
    "Partir du besoin et de l'architecture (dossier de conception RudyLink), pas d'un catalogue de produits.",
    "Allotir : un lot par métier (câblage, réseau, sécurité, serveurs, sûreté) ouvre la concurrence et évite qu'un seul titulaire "
    "maîtrise tout le SI.",
    "Faire un sourçage avant la consultation (rencontres fournisseurs, UGAP et centrales d'achat) pour vérifier que le besoin trouve preneur.",
    "Fixer les critères et leur poids, par exemple : valeur technique 45 %, prix 40 %, performance environnementale 15 % "
    "(un critère environnemental est obligatoire depuis la loi Climat et résilience).",
    "Choisir la procédure selon le montant estimé et les seuils européens en vigueur (révisés tous les deux ans), avec les services "
    "achats de l'AMU.",
    "Écrire des exigences vérifiables (« certifiées à 100 % au testeur », pas « de bonne qualité »), chacune reliée à un test de recette.",
    "Citer une marque seulement à titre d'exemple, suivie de « ou équivalent ».",
]

SOMMAIRE_CDC = [
    "Contexte et objectifs (enseignement, recherche, site jumeau)",
    "Périmètre (bâtiment, salles, nombre d'usagers, services)",
    "Besoins fonctionnels par service (réseau filaire, Wi-Fi, téléphonie, serveurs, sécurité, sûreté, IA)",
    "Exigences non fonctionnelles : disponibilité, performances, sécurité (PSSI), conformité (RGPD, conservation des journaux), "
    "développement durable",
    "Contraintes : bâtiment occupé, calendrier universitaire, existant à reprendre, compétences de l'équipe",
    "Organisation : MOA, MOE, comité de pilotage, recette",
    "Budget prévisionnel et calendrier",
]
