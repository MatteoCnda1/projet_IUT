"""Point 09 : politique de sécurité du système d'information (PSSI) du site de Marseille (version du dossier : commun/charte.py).

Déclinaison, pour le bâtiment IUT Génie Télécom, de la PSSI de l'AMU (établissement de rattachement). Chaque mesure M-xx dit
ce qui est exigé, où en est l'architecture v2.1, et sur quoi elle s'appuie. Les mesures sont reprises par l'analyse de risque
(securite/ebios.py) et reliées aux 42 mesures du guide d'hygiène de l'ANSSI (tableau HYGIENE).
v2.1 : groupe électrogène (M-PHY-4 réécrite, M-PHY-5), extinction en place et travail isolé séparé (M-PHY-6), VPN IKEv2 intégré
(M-ADM-2), conservation des journaux en deux durées (M-DET-1), mises à jour des contrôleurs de domaine (M-POS-2).
Les valeurs du groupe électrogène et des onduleurs sont lues dans livrables/energie_refroidissement/resume.json (point 14).
"""
import json
from pathlib import Path

_ENERGIE = json.loads((Path(__file__).resolve().parent.parent / "livrables" / "energie_refroidissement" / "resume.json")
                      .read_text(encoding="utf-8"))
GE = _ENERGIE["bet"]["groupe_electrogene"]          # prp_kva, esp_kva, cuve_l, autonomie_h, autonomie_75_h, arret_nut_si_ge_absent_min
AUTONOMIE_ONDULEUR = _ENERGIE["onduleurs"]["autonomie_degrade"]  # minutes avec un seul onduleur

ROLES = [  # rôle, qui, responsabilités
    ("Autorité d'homologation", "Directeur de l'IUT, par délégation du président de l'AMU",
     "Accepte les risques résiduels, prononce l'homologation du SI du site, arbitre les moyens."),
    ("RSSI", "RSSI de l'AMU", "Porte la PSSI, valide les dérogations, pilote les audits et la gestion des incidents."),
    ("Correspondant SSI du site", "Administrateur réseau de l'IUT (désigné et connu de tous, mesure 39)",
     "Applique la PSSI au quotidien, tient la matrice de flux, premier contact en cas d'incident."),
    ("DPO", "Délégué à la protection des données de l'AMU", "Registre des traitements, AIPD, violations de données (point 19)."),
    ("Administrateurs", "Équipe informatique de l'IUT, par niveau (tier 0, 1, 2)",
     "Comptes d'administration nominatifs et séparés, administration par le bastion seulement."),
    ("Chargé de sécurité des biens et des personnes", "Responsable logistique du bâtiment",
     "Contrôle d'accès, vidéoprotection, sécurité incendie, consignes de la salle serveur."),
    ("Utilisateurs", "Personnels, étudiants, chercheurs, invités", "Respectent la charte informatique (point 19), signalent les incidents."),
    ("RudyLink Infrastructure (MOE)", "Prestataire de conception", "Conçoit l'architecture et ses mesures, ne détient aucun accès de production."),
]

PRINCIPES = [
    ("Défense en profondeur", "Deux pare-feu de marques différentes, cloisonnement en VRF, ACL au plus près des ports, 802.1X : "
     "une seule défaillance ne suffit pas à atteindre une ressource sensible."),
    ("Moindre privilège", "Chaque compte, chaque flux, chaque équipement n'a que les droits nécessaires. Refus par défaut partout."),
    ("Cloisonnement par niveau de confiance", "Une zone par niveau (invités, objets, utilisateurs, serveurs, tier 0, administration) ; "
     "on ne change de zone qu'en traversant un pare-feu."),
    ("Administration séparée", "Le SI d'administration ne sert qu'à administrer : postes, réseau, comptes et bastion dédiés."),
    ("Traçabilité", "Tout accès sensible est journalisé, horodaté par une source commune, conservé et protégé contre la modification."),
    ("Produits maîtrisés", "Produits qualifiés par l'ANSSI là où c'est possible (Stormshield pour le pare-feu interne), versions suivies."),
    ("Sécurité dès la conception", "Les exigences de sécurité entrent dans les CCTP des marchés (point 19), pas après la livraison."),
]

# ---------------------------------------------------------------------------
# Mesures : code, domaine, intitulé, exigence, état v2.1, références
# états : « en place » (dans l'architecture v2.1), « proposé » (dans ce dossier, à intégrer dans une version ultérieure),
# « organisationnel » (à faire par le client, la conception ne peut pas l'imposer)
# ---------------------------------------------------------------------------
MESURES = [
    # Gouvernance
    ("M-GOU-1", "Gouvernance", "Analyse de risque et homologation",
     "Analyse EBIOS RM tenue à jour (au moins tous les 3 ans ou à chaque changement majeur), dossier d'homologation du SI du site "
     "présenté à l'autorité d'homologation avant la mise en service.", "proposé", "EBIOS RM v1.5 ; guide de l'homologation 2025"),
    ("M-GOU-2", "Gouvernance", "Gestion des changements",
     "Toute modification de la matrice de flux, des pare-feu ou des droits d'administration est demandée par écrit, relue par une "
     "deuxième personne et tracée (source de configuration versionnée).", "proposé", "ANSSI politique de filtrage"),
    ("M-GOU-3", "Gouvernance", "Audits réguliers",
     "Audit de configuration annuel, test d'intrusion avant mise en service puis tous les deux ans par un prestataire qualifié PASSI.",
     "organisationnel", "Catalogue des prestataires qualifiés"),
    # Identités et accès
    ("M-IDA-1", "Identités et accès", "Annuaire en tiers",
     "Contrôleurs de domaine en tier 0 (VLAN 310, passerelle sur le Stormshield, sans Internet). Comptes d'administration séparés "
     "par tier ; un compte de tier 0 ne se connecte jamais sur un poste ou un serveur de tier 1 ou 2.", "en place", "ANSSI PA-099"),
    ("M-IDA-2", "Identités et accès", "Mots de passe et authentification forte",
     "Mots de passe d'au moins 12 caractères pour les utilisateurs, 16 pour les administrateurs, vérifiés contre les listes de mots "
     "de passe compromis ; pas d'expiration périodique imposée hors compromission. MFA pour la messagerie à distance, le VPN, le "
     "bastion (clé FIDO2 pour les administrateurs).", "proposé", "ANSSI authentification multifacteur et mots de passe v2.0"),
    ("M-IDA-3", "Identités et accès", "Cycle de vie des comptes",
     "Arrivées et départs synchronisés avec la scolarité et les RH : comptes étudiants désactivés à la fin de l'inscription, revue "
     "trimestrielle des comptes privilégiés et des comptes de service (gMSA), mots de passe d'administrateur local uniques (LAPS).",
     "organisationnel", "Guide d'hygiène, mesures 5 et 6"),
    # Administration
    ("M-ADM-1", "Administration", "SI d'administration dédié",
     "VRF ADM séparée, postes d'administration dédiés (VLAN 906) sans Internet ni messagerie (F47), administration uniquement "
     "par le bastion Teleport avec MFA (F38, F39) et enregistrement des sessions.", "en place", "ANSSI PA-022"),
    ("M-ADM-2", "Administration", "Accès distant d'administration",
     "Depuis l'extérieur, seulement par le VPN d'administration IPsec IKEv2 (certificat + MFA), dont le pool n'atteint que le "
     "bastion (F05, F38). Les prestataires (lot sûreté compris) passent par le même chemin, avec un compte nominatif ouvert pour la "
     "durée de l'intervention (F67, F68).", "en place", "ANSSI PA-054, PA-022 ; écart E2 intégré en v2.1"),
    ("M-ADM-3", "Administration", "Secrets d'administration",
     "Mots de passe des équipements et clés SSH dans un coffre (Teleport émet des certificats SSH courts : pas de clé permanente) ; "
     "comptes par défaut changés ou désactivés à l'installation.", "proposé", "Guide d'hygiène, mesure 12 ; OpenSSH DAT-NT-007"),
    # Réseau
    ("M-RES-1", "Réseau", "Cloisonnement et matrice de flux",
     "Zones et VRF de l'architecture v2.1, refus par défaut, matrice de flux détaillée (voir matrice_flux.pdf) déployée dans un "
     "ordre fixé (autorisations, refus explicites, refus par défaut), revue semestrielle.",
     "en place", "Guide d'hygiène, mesure 19 ; matrice_flux.pdf"),
    ("M-RES-2", "Réseau", "Contrôle d'accès au réseau (NAC)",
     "802.1X EAP-TLS sur tous les ports d'accès pour les postes du domaine, MAB et profilage pour les objets, VLAN restreint (Internet "
     "seulement) en cas d'échec ; ports inutilisés désactivés (VLAN 998).", "en place", "ANSSI PA-043 ; note sur les commutateurs de desserte"),
    ("M-RES-3", "Réseau", "Sécurité du niveau 2",
     "DHCP snooping, inspection ARP dynamique, IP source guard, BPDU guard et root guard, VLAN natif inutilisé (999), storm control.",
     "en place", "Architecture L2 ; note sur les commutateurs de desserte"),
    ("M-RES-4", "Réseau", "Wi-Fi",
     "WPA3-Entreprise (802.1X) pour le personnel et eduroam, réseau invités séparé (portail, isolation des clients, NAT dédié), "
     "WPS et UPnP désactivés, détection des bornes pirates sur les WLC.", "en place", "ANSSI Essentiels Wi-Fi ; mesure 20"),
    ("M-RES-5", "Réseau", "Exposition sur Internet",
     "Seuls les services de la DMZ sont publiés, derrière le reverse proxy (TLS 1.2 minimum, en-têtes HSTS et CSP). DNS faisant "
     "autorité séparé des résolveurs, DNSSEC. Protection contre le déni de service demandée à RENATER et au FAI 2.",
     "en place", "ANSSI passerelle Internet v3 ; PA-105 ; mesures 22 et 23"),
    ("M-RES-6", "Réseau", "Messagerie",
     "SPF, DKIM et DMARC en mode rejet, antispam et antivirus sur le FortiGate et le relais. DM-MAIL1 devient un relais sans boîte "
     "aux lettres (écart E1).", "proposé", "Guide d'hygiène, mesure 24 ; écart E1"),
    # Postes et serveurs
    ("M-POS-1", "Postes et serveurs", "Socle des postes",
     "Postes du domaine durcis par GPO (pare-feu local actif, pas de droits d'administrateur pour les utilisateurs, supports amovibles "
     "contrôlés), EDR, BitLocker sur les portables.", "organisationnel", "Guide d'hygiène, mesures 14 à 17, 29 et 31"),
    ("M-POS-2", "Postes et serveurs", "Mises à jour",
     "Correctifs de sécurité critiques sur les équipements exposés (pare-feu, VPN, DMZ) sous 72 h, autres sous 30 jours ; inventaire "
     "des versions et des fins de support suivi par la supervision. Contrôleurs de domaine : correctifs téléchargés par "
     "l'administration, empreinte et signature vérifiées, puis copiés par le rôle Teleport tier 0 (aucun flux sortant du tier 0, F37, F40).",
     "proposé", "Guide d'hygiène, mesures 34 et 35 ; ANSSI PA-099"),
    ("M-POS-3", "Postes et serveurs", "Durcissement des serveurs",
     "Debian et Proxmox selon le guide ANSSI GNU/Linux (niveau intermédiaire), conteneurs sans root, hyperviseurs DMZ séparés des "
     "hyperviseurs tier 0.", "en place", "ANSSI GNU/Linux v2.0 ; PG-040 ; FT-082"),
    # Biens et personnes
    ("M-PHY-1", "Sécurité des biens et des personnes", "Accès aux locaux techniques",
     "Salle serveur et 6 locaux techniques fermés par badge + code, liste nominative des accès, journal des passages conservé, "
     "visiteurs accompagnés.", "en place", "Guide d'hygiène, mesure 26 ; plan de câblage"),
    ("M-PHY-2", "Sécurité des biens et des personnes", "Extinction automatique de la salle serveur",
     "Extinction automatique par gaz inerte (IG-541) avec détection précoce par aspiration, temporisation et alarme avant "
     "déclenchement, consigne d'évacuation affichée.", "en place", "Code du travail (R4227) ; point 14, SYS-03"),
    ("M-PHY-3", "Sécurité des biens et des personnes", "Systèmes de sûreté cloisonnés",
     "Caméras, badgeuses et GTB (dont le groupe électrogène) dans la VRF IOT, sans Internet, flux limités à l'enregistreur VS-NVR1, au "
     "serveur de contrôle d'accès et à la supervision (F24 à F27, F70) ; équipements sûreté certifiés CSPN ou qualifiés quand c'est "
     "possible ; aucune caméra dans les lieux de pause (foyer des étudiants) ; vidéoprotection autorisée par le préfet pour les lieux "
     "ouverts au public, inscrite au registre des traitements et signalée (point 19).",
     "en place", "ANSSI PA-072 ; objets connectés v1.0 ; CSI L252-1"),
    ("M-PHY-4", "Sécurité des biens et des personnes", "Énergie et climatisation",
     "Double alimentation des baies (voies A et B), deux onduleurs en ligne 6 kVA avec pack batterie "
     f"({AUTONOMIE_ONDULEUR} min avec un seul onduleur), climatisation redondante, sondes, onduleurs et PDU supervisés ; arrêt ordonné "
     f"des serveurs par NUT seulement si l'onduleur est encore sur batterie {GE['arret_nut_si_ge_absent_min']} min après la coupure "
     "(groupe électrogène absent), séquence testée une fois par an (point 14).", "en place", "Point 14 ; NF EN 62040"),
    ("M-PHY-5", "Sécurité des biens et des personnes", "Groupe électrogène",
     f"Groupe électrogène diesel dédié ({GE['esp_kva']} kVA ESP / {GE['prp_kva']} kVA PRP, cuve double paroi de {GE['cuve_l']} l, "
     f"{GE['autonomie_h']} h d'autonomie à charge moyenne) et inverseur de source automatique en tête du TD-INFO : reprise de la salle "
     "serveur et des locaux techniques sans intervention. Essai mensuel en charge et essai annuel sur banc de charge tracés, contrat "
     "de maintenance et de livraison de gazole. Contrôleur du groupe et inverseur supervisés en lecture seule (VLAN GTB, F70), sans "
     "modem ni service en nuage ; toute télémaintenance passe par le bastion (M-ADM-2).", "en place",
     "NF EN ISO 8528 ; NF C 15-100 (section 551) ; NF EN IEC 60947-6-1 ; ANSSI GTB/GTC ; point 14"),
    ("M-PHY-6", "Sécurité des biens et des personnes", "Travail isolé et habilitations",
     "Personne n'entre seul la nuit en salle serveur sans dispositif d'alarme pour travailleur isolé (DATI) ; habilitation "
     "électrique des intervenants (tableau informatique, inverseur, groupe électrogène).", "organisationnel",
     "Code du travail (R4544) ; NF C 18-510"),
    # Journalisation, détection
    ("M-DET-1", "Journalisation et détection", "Chaîne de journalisation",
     "Collecte centralisée (syslog TLS, F42), horloge commune (F44, F60), archives scellées. Données techniques de connexion (qui, "
     "quand, adresses et ports source et destination, volumes) conservées 1 an, accès restreint ; journaux détaillés de navigation "
     "(URL complètes du proxy de filtrage web) conservés 6 mois, pour la sécurité seulement, consultation tracée, sans contrôle individuel de l'activité.",
     "en place", "ANSSI journalisation v2.0 ; mesure 36 ; CPCE art. L34-1 ; décrets n° 2021-1361 et 2021-1362"),
    ("M-DET-2", "Journalisation et détection", "Détection",
     "Corrélation des journaux (SIEM open source, par exemple Wazuh, dans la VRF ADM), alertes sur les refus explicites de la matrice "
     "(une caméra qui cherche un poste, un poste d'administration qui sort), sur les connexions d'administration hors heures et sur "
     "les créations de comptes privilégiés.", "proposé", "ANSSI journalisation v2.0"),
    ("M-INC-1", "Journalisation et détection", "Gestion des incidents",
     "Procédure écrite : qualification, confinement (isoler une VRF ou un port), alerte du RSSI de l'AMU et du CERT-FR ou du CSIRT "
     "régional, notification CNIL sous 72 h en cas de violation de données, notification NIS 2 (alerte sous 24 h, notification sous 72 h, "
     "rapport sous 1 mois). Cellule de crise décrite au point 19.", "proposé", "Guide d'hygiène, mesure 40 ; RGPD art. 33 ; NIS 2 art. 23"),
    # Sauvegarde
    ("M-SAV-1", "Sauvegarde et continuité", "Sauvegardes protégées",
     "Règle 3-2-1 avec une copie hors ligne et une copie externalisée immuable (F45). Instance de sauvegarde hors domaine, comptes "
     "dédiés et nominatifs, tests de restauration réguliers (détail au point 15).", "en place", "ANSSI BP-100 ; mesure 37"),
    # Sensibilisation
    ("M-SEN-1", "Sensibilisation", "Former et sensibiliser",
     "Charte informatique signée (point 19), sensibilisation à l'arrivée et une fois par an, exercice d'hameçonnage annuel, formation "
     "des administrateurs aux guides ANSSI.", "organisationnel", "Guide d'hygiène, mesures 1 et 2"),
    # Fournisseurs
    ("M-FOU-1", "Fournisseurs", "Sécurité dans les marchés",
     "Clauses de sécurité dans chaque CCTP (point 19) : accès distant par le bastion, comptes nominatifs, correctifs, notification des "
     "incidents, réversibilité, localisation des données (SecNumCloud pour la sauvegarde externalisée).", "proposé",
     "Guide d'hygiène, mesures 3 et 42"),
    # IA
    ("M-IA-1", "IA locale", "Isolement de la plateforme",
     "Zone dédiée (VLAN 320/321, passerelle sur le Stormshield), aucune sortie Internet (F52), utilisateurs limités à la passerelle (F48), "
     "GPU joignables seulement par elle (F50).", "proposé", "ANSSI sécurité d'un système d'IA générative (2024) ; écart E5"),
    ("M-IA-2", "IA locale", "Chaîne d'approvisionnement des modèles",
     "Modèles récupérés depuis la source officielle, empreinte vérifiée, format sans code exécutable (safetensors), analyse avant "
     "copie dans la zone, registre des versions déployées.", "proposé", "ANSSI IA générative, recommandations sur la chaîne d'approvisionnement"),
    ("M-IA-3", "IA locale", "Contrôles d'usage",
     "Authentification SSO, quotas par utilisateur, filtrage des entrées et sorties (consignes système, modèle modéré), pas de "
     "réentraînement sur les requêtes des utilisateurs, cloisonnement des conversations entre utilisateurs.", "proposé", "ANSSI IA générative"),
    ("M-IA-4", "IA locale", "Journal des requêtes",
     "Métadonnées des requêtes (qui, quand, volume) conservées 1 an pour la traçabilité ; contenu des conversations conservé au plus "
     "30 jours, effaçable par l'utilisateur, consultable seulement sur incident (cadre RGPD au point 19).", "proposé", "RGPD art. 5 et 32"),
    # Nomadisme
    ("M-NOM-1", "Nomadisme", "Postes nomades",
     "Portables chiffrés (BitLocker + TPM), VPN obligatoire hors du site pour les ressources internes, filtre de confidentialité pour "
     "les administrateurs.", "organisationnel", "ANSSI PA-054 ; mesures 30 à 33"),
]
CODES = {m[0] for m in MESURES}

# ---------------------------------------------------------------------------
# Conformité aux 42 mesures du guide d'hygiène informatique (ANSSI, v2 2017). Intitulés du guide, outil de suivi p. 60-65.
# couverture : (mesures PSSI, niveau) ; niveau = « couverte », « partielle », « à la charge du client »
# ---------------------------------------------------------------------------
HYGIENE = [
    ("I", "Sensibiliser et former", [
        (1, "Former les équipes opérationnelles à la sécurité des systèmes d'information", ["M-SEN-1"], "à la charge du client"),
        (2, "Sensibiliser les utilisateurs aux bonnes pratiques élémentaires de sécurité informatique", ["M-SEN-1"], "à la charge du client"),
        (3, "Maîtriser les risques de l'infogérance", ["M-FOU-1", "M-ADM-2"], "couverte")]),
    ("II", "Connaître le système d'information", [
        (4, "Identifier les informations et serveurs les plus sensibles et maintenir un schéma du réseau", ["M-GOU-1"], "couverte"),
        (5, "Disposer d'un inventaire exhaustif des comptes privilégiés et le maintenir à jour", ["M-IDA-3"], "partielle"),
        (6, "Organiser les procédures d'arrivée, de départ et de changement de fonction des utilisateurs", ["M-IDA-3"], "à la charge du client"),
        (7, "Autoriser la connexion au réseau de l'entité aux seuls équipements maîtrisés", ["M-RES-2"], "couverte")]),
    ("III", "Authentifier et contrôler les accès", [
        (8, "Identifier nommément chaque personne accédant au système et distinguer les rôles utilisateur/administrateur", ["M-IDA-1", "M-ADM-1"], "couverte"),
        (9, "Attribuer les bons droits sur les ressources sensibles du système d'information", ["M-IDA-1", "M-RES-1"], "couverte"),
        (10, "Définir et vérifier des règles de choix et de dimensionnement des mots de passe", ["M-IDA-2"], "couverte"),
        (11, "Protéger les mots de passe stockés sur les systèmes", ["M-ADM-3"], "partielle"),
        (12, "Changer les éléments d'authentification par défaut sur les équipements et services", ["M-ADM-3"], "couverte"),
        (13, "Privilégier lorsque c'est possible une authentification forte", ["M-IDA-2", "M-ADM-1"], "couverte")]),
    ("IV", "Sécuriser les postes", [
        (14, "Mettre en place un niveau de sécurité minimal sur l'ensemble du parc informatique", ["M-POS-1"], "à la charge du client"),
        (15, "Se protéger des menaces relatives à l'utilisation de supports amovibles", ["M-POS-1"], "à la charge du client"),
        (16, "Utiliser un outil de gestion centralisée afin d'homogénéiser les politiques de sécurité", ["M-POS-1", "M-IDA-1"], "partielle"),
        (17, "Activer et configurer le pare-feu local des postes de travail", ["M-POS-1"], "à la charge du client"),
        (18, "Chiffrer les données sensibles transmises par voie Internet", ["M-RES-5", "M-ADM-2"], "couverte")]),
    ("V", "Sécuriser le réseau", [
        (19, "Segmenter le réseau et mettre en place un cloisonnement entre ces zones", ["M-RES-1"], "couverte"),
        (20, "S'assurer de la sécurité des réseaux d'accès Wi-Fi et de la séparation des usages", ["M-RES-4"], "couverte"),
        (21, "Utiliser des protocoles sécurisés dès qu'ils existent", ["M-RES-5", "M-DET-1", "M-ADM-1"], "couverte"),
        (22, "Mettre en place une passerelle d'accès sécurisé à Internet", ["M-RES-5"], "couverte"),
        (23, "Cloisonner les services visibles depuis Internet du reste du système d'information", ["M-RES-5", "M-RES-1"], "partielle"),
        (24, "Protéger sa messagerie professionnelle", ["M-RES-6"], "partielle"),
        (25, "Sécuriser les interconnexions réseau dédiées avec les partenaires", ["M-RES-1"], "partielle"),
        (26, "Contrôler et protéger l'accès aux salles serveurs et aux locaux techniques", ["M-PHY-1"], "couverte")]),
    ("VI", "Sécuriser l'administration", [
        (27, "Interdire l'accès à Internet depuis les postes ou serveurs utilisés pour l'administration du système d'information", ["M-ADM-1"], "couverte"),
        (28, "Utiliser un réseau dédié et cloisonné pour l'administration du système d'information", ["M-ADM-1"], "couverte"),
        (29, "Limiter au strict besoin opérationnel les droits d'administration sur les postes de travail", ["M-POS-1", "M-IDA-1"], "à la charge du client")]),
    ("VII", "Gérer le nomadisme", [
        (30, "Prendre des mesures de sécurisation physique des terminaux nomades", ["M-NOM-1"], "à la charge du client"),
        (31, "Chiffrer les données sensibles, en particulier sur le matériel potentiellement perdable", ["M-NOM-1"], "à la charge du client"),
        (32, "Sécuriser la connexion réseau des postes utilisés en situation de nomadisme", ["M-ADM-2", "M-NOM-1"], "couverte"),
        (33, "Adopter des politiques de sécurité dédiées aux terminaux mobiles", ["M-NOM-1"], "à la charge du client")]),
    ("VIII", "Maintenir à jour le système d'information", [
        (34, "Définir une politique de mise à jour des composants du système d'information", ["M-POS-2"], "couverte"),
        (35, "Anticiper la fin de la maintenance des logiciels et systèmes et limiter les adhérences logicielles", ["M-POS-2"], "partielle")]),
    ("IX", "Superviser, auditer, réagir", [
        (36, "Activer et configurer les journaux des composants les plus importants", ["M-DET-1"], "couverte"),
        (37, "Définir et appliquer une politique de sauvegarde des composants critiques", ["M-SAV-1"], "couverte"),
        (38, "Procéder à des contrôles et audits de sécurité réguliers puis appliquer les actions correctives associées", ["M-GOU-3"], "à la charge du client"),
        (39, "Désigner un référent en sécurité des systèmes d'information et le faire connaître auprès du personnel", ["M-GOU-1"], "à la charge du client"),
        (40, "Définir une procédure de gestion des incidents de sécurité", ["M-INC-1"], "couverte")]),
    ("X", "Pour aller plus loin", [
        (41, "Mener une analyse de risques formelle", ["M-GOU-1"], "couverte"),
        (42, "Privilégier l'usage de produits et de services qualifiés par l'ANSSI", ["M-FOU-1", "M-RES-1"], "partielle")]),
]


def verifier():
    nums = [n for _, _, l in HYGIENE for n, *_ in l]
    assert nums == list(range(1, 43)), "les 42 mesures du guide, dans l'ordre"
    for _, _, l in HYGIENE:
        for n, _, mes, niv in l:
            assert niv in ("couverte", "partielle", "à la charge du client"), n
            for m in mes:
                assert m in CODES, (n, m)
    assert len(CODES) == len(MESURES)
    return True
