"""Point 19 : données du volet juridique (registre RGPD, durées, AIPD, journalisation, crise). Version 1, 18/11/2026.

Repris par juridique/build.py -> livrables/juridique/. Les mesures M-xx renvoient à la PSSI (securite/pssi.py), les règles
Fxx à la matrice des flux (securite/flux.py). Ce n'est pas un avis juridique : chaque choix est à valider par le DPO et le
service juridique de l'AMU (rôle du concepteur : être force de proposition).
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "1.0"

# ---------------------------------------------------------------------------
# Textes cités (référence courte -> intitulé). Un seul endroit, pour éviter les références approximatives.
# ---------------------------------------------------------------------------
TEXTES = {
    "RGPD": "Règlement (UE) 2016/679 (RGPD)",
    "LIL": "Loi n° 78-17 du 6 janvier 1978 (Informatique et libertés)",
    "CPCE": "Code des postes et des communications électroniques, art. L34-1 et R10-13 (conservation des données de connexion)",
    "LCEN": "Loi n° 2004-575 du 21 juin 2004 pour la confiance dans l'économie numérique (LCEN)",
    "CSI": "Code de la sécurité intérieure, art. L251-1 et suivants (vidéoprotection des lieux ouverts au public)",
    "CP-STAD": "Code pénal, art. 323-1 et suivants (atteintes aux systèmes de traitement automatisé de données)",
    "CP-CORR": "Code pénal, art. 226-15 (secret des correspondances)",
    "CT": "Code du travail, art. L1121-1 (proportionnalité) et L1222-4 (information préalable des salariés)",
    "CGFP": "Code général de la fonction publique : consultation du comité social d'administration (CSA)",
    "AIA": "Règlement (UE) 2024/1689 sur l'intelligence artificielle (AI Act)",
    "NIS2": "Directive (UE) 2022/2555 (NIS 2) et projet de loi relatif à la résilience des infrastructures critiques",
    "CCP": "Code de la commande publique (dont les clauses environnementales obligatoires de la loi n° 2021-1104 Climat et résilience)",
    "CPI": "Code de la propriété intellectuelle (logiciels, bases de données, œuvres)",
    "CPP": "Code de procédure pénale, art. 60-1, 77-1-1 et 99-3 (réquisitions judiciaires)",
}

# ---------------------------------------------------------------------------
# Registre des traitements (RGPD art. 30) : traitements créés ou touchés par l'infrastructure du site.
# Responsable de traitement : l'AMU (président), représentée sur le site par le directeur de l'IUT. DPO : DPO de l'AMU.
# Base légale : e = mission d'intérêt public (art. 6.1.e), c = obligation légale (art. 6.1.c), a = consentement (art. 6.1.a)
# ---------------------------------------------------------------------------
BASES = {"e": "mission d'intérêt public (art. 6.1.e)", "c": "obligation légale (art. 6.1.c)", "a": "consentement (art. 6.1.a)"}
TRAITEMENTS = [
    # code, nom, finalités, base, personnes, données, destinataires, durée, mesures, AIPD, point du projet
    ("T01", "Comptes et annuaire", "Identifier et authentifier les utilisateurs, gérer leurs droits", "e",
     "personnels, étudiants, chercheurs, prestataires", "identité, identifiant, groupes, empreinte du mot de passe, dates de connexion",
     "administrateurs habilités", "durée de la fonction ou de l'inscription, puis 3 mois (désactivation, puis suppression)",
     "M-IDA-1, M-IDA-3", "non", "P11"),
    ("T02", "Contrôle d'accès au réseau (802.1X, Wi-Fi, portail invités)", "Ne laisser entrer sur le réseau que les personnes et "
     "équipements autorisés", "e", "utilisateurs, invités", "identifiant, adresse MAC, borne, VLAN attribué, horodatage ; invités : "
     "nom et contact déclarés", "administrateurs réseau", "6 mois pour les journaux d'authentification (sécurité), 1 an pour ceux qui "
     "servent à l'identification (T03)", "M-RES-2, M-RES-4", "non", "P10"),
    ("T03", "Données de connexion (journal légal)", "Répondre aux réquisitions judiciaires : identifier l'auteur d'une connexion",
     "c", "toute personne connectée au réseau du site", "adresse privée et publique, ports (NAT), adresse MAC, identifiant, horodatage. "
     "Jamais le contenu ni les sites consultés", "autorités judiciaires sur réquisition ; 2 personnes habilitées", "1 an, puis effacement "
     "automatique", "M-DET-1", "non", "P08, P16"),
    ("T04", "Journaux de sécurité et supervision", "Détecter et analyser les incidents, administrer le réseau", "e",
     "utilisateurs, administrateurs", "journaux des pare-feu, des serveurs et des équipements, alertes", "RSSI, administrateurs",
     "6 mois en recherche (90 jours indexés), 1 an au plus pour les incidents", "M-DET-1, M-DET-2", "non", "P09, P16"),
    ("T05", "Bastion d'administration (enregistrement des sessions)", "Tracer les actions d'administration", "e",
     "administrateurs, prestataires", "identité, sessions SSH/RDP enregistrées, commandes", "RSSI", "1 an", "M-ADM-1",
     "non", "P09, P11"),
    ("T06", "Vidéoprotection", "Sécurité des personnes et des biens : accès au bâtiment, parkings, salle serveur", "e",
     "personnes passant devant les caméras", "images (sans son), horodatage", "chargé de sécurité et agents habilités ; forces de "
     "l'ordre sur réquisition", "30 jours au plus, effacement automatique", "M-PHY-3", "oui", "P12, P17"),
    ("T07", "Contrôle d'accès physique (badges)", "Réserver les locaux sensibles aux personnes autorisées", "e",
     "personnels, prestataires", "identité, numéro de badge, droits, journal des passages (porte, heure)", "chargé de sécurité",
     "droits : durée de la fonction ; journal des passages : 3 mois", "M-PHY-1", "non", "P17"),
    ("T08", "Plateforme d'IA locale", "Mettre un assistant d'IA à disposition de l'enseignement et de la recherche", "e",
     "étudiants, enseignants, chercheurs", "identifiant, requêtes et réponses, volumes, horodatage", "aucun en temps normal ; RSSI sur "
     "incident", "contenus : 30 jours (effaçables par l'utilisateur) ; métadonnées : 1 an", "M-IA-1 à M-IA-4", "oui", "P11"),
    ("T09", "Gestion des absences", "Suivre l'assiduité des étudiants (contrôle pédagogique, bourses)", "e", "étudiants",
     "identité, groupe, séance, présence ou absence, justificatif", "enseignants, scolarité", "année universitaire + 1 an", "M-IDA-1, M-POS-3",
     "non", "P13"),
    ("T10", "Géolocalisation (« géotrack »)", "Envisagée au point 13 : vérifier la présence d'un étudiant en cours", "e",
     "étudiants", "position", "—", "—", "—", "oui", "P13"),
    ("T11", "Réservation de salles", "Réserver les salles et le matériel", "e", "personnels, étudiants", "identité, réservations",
     "personnels, scolarité", "année universitaire + 1 an", "M-RES-5", "non", "P13"),
    ("T12", "Téléphonie IP", "Fournir la téléphonie, facturer et dépanner", "e", "personnels", "numéros appelant et appelé, durée, "
     "poste ; jamais le contenu des appels", "administrateurs ToIP", "1 an", "M-RES-1", "non", "P12"),
]

# ---------------------------------------------------------------------------
# Analyses d'impact (AIPD, RGPD art. 35). Critères du CEPD (lignes directrices WP248) : deux critères ou plus => AIPD.
# ---------------------------------------------------------------------------
CRITERES = {"surv": "surveillance systématique", "vuln": "personnes vulnérables ou en situation de dépendance (étudiants, agents)",
            "echelle": "large échelle", "innov": "usage innovant ou nouvelle technologie", "sens": "données sensibles ou très personnelles",
            "croise": "croisement de données", "eval": "évaluation ou notation"}
AIPD = {
    "T06": {
        "criteres": ["surv", "vuln", "echelle"],
        "necessite": "Sécuriser les accès du bâtiment, les parkings et la salle serveur, qui contient le matériel le plus coûteux. "
                     "Moins intrusif d'abord : contrôle d'accès par badge aux locaux sensibles, éclairage, fermeture des parkings la nuit.",
        "proportion": ["Caméras limitées aux entrées, aux circulations, aux parkings et à la salle serveur ; aucune caméra ne filme un "
                       "poste de travail, une salle de cours en continu, des sanitaires ni un lieu de pause",
                       "Masquage dynamique des zones privatives et de la voie publique",
                       "Images conservées 30 jours au plus, effacées automatiquement ; extraction seulement sur incident, tracée",
                       "Panneaux d'information à chaque entrée (responsable, finalité, durée, droits, contact du DPO)",
                       "Accès aux images limité au chargé de sécurité et à deux agents nommés, par le serveur de vidéo (VRF SRV) "
                       "uniquement, jamais depuis Internet"],
        "risques": [("Accès illégitime aux images", 3, 2, "Réseau IOT cloisonné (F24, F27), comptes nominatifs, journal des consultations"),
                    ("Modification ou effacement des images (après un incident)", 2, 2, "Enregistreur en zone SRV, sauvegarde des extraits"),
                    ("Détournement de finalité (surveiller le travail des agents)", 3, 2, "Champ des caméras validé avec le CSA, audit annuel")],
        "conclusion": "Risques résiduels acceptables, sous réserve de retirer la caméra du foyer des étudiants et de l'autorisation "
                      "préfectorale pour les caméras qui filment des lieux ouverts au public.",
    },
    "T08": {
        "criteres": ["innov", "echelle", "vuln", "sens"],
        "necessite": "Offrir un assistant d'IA aux usagers sans envoyer leurs données à un service étranger. La plateforme locale est "
                     "justement la mesure de protection, par rapport aux services en ligne grand public.",
        "proportion": ["Pas de réentraînement du modèle sur les requêtes", "Conversations cloisonnées par utilisateur, effaçables par lui",
                       "Contenus conservés 30 jours, métadonnées 1 an ; aucune lecture des contenus hors incident de sécurité",
                       "Aucune sortie Internet de la zone IA (F52)",
                       "Charte d'usage : ne pas confier de données sensibles (santé, opinions, données de tiers), vérifier les réponses",
                       "Interdiction d'utiliser la plateforme pour évaluer, noter ou surveiller des étudiants (usages à haut risque ou "
                       "interdits par l'AI Act)"],
        "risques": [("Fuite des requêtes d'un utilisateur vers un autre (défaut de cloisonnement)", 3, 2, "M-IA-3, tests avant mise en service"),
                    ("Données sensibles saisies par les utilisateurs", 3, 3, "Charte, avertissement à l'écran, durée courte (30 jours)"),
                    ("Réponses fausses utilisées comme vraies (décision, devoir)", 2, 3, "Formation à l'IA (AI Act art. 4), mention à l'écran")],
        "conclusion": "Risques résiduels acceptables avec les mesures prévues. Le risque « données sensibles saisies » reste le plus fort : "
                      "il dépend des usagers, d'où la formation et le rappel à chaque connexion.",
    },
    "T10": {
        "criteres": ["surv", "vuln", "sens", "echelle"],
        "necessite": "Vérifier qu'un étudiant est présent en cours. Ce but peut être atteint sans géolocalisation : appel, émargement "
                     "électronique en salle, code affiché par l'enseignant au début de la séance.",
        "proportion": ["Une géolocalisation continue des étudiants serait disproportionnée : le moyen n'est pas nécessaire au but",
                       "Si le point 13 en garde une forme : vérification ponctuelle, au moment de l'émargement seulement, position non "
                       "conservée (on garde « présent ou absent »), et un autre moyen d'émarger pour qui refuse"],
        "risques": [("Suivi des déplacements des étudiants hors des cours", 4, 3, "Ne pas mettre en place la géolocalisation"),
                    ("Accès aux positions par des tiers", 3, 2, "Pas de stockage des positions")],
        "conclusion": "Avis défavorable à la géolocalisation des étudiants, que l'on propose de remplacer par un émargement en salle (code de "
                      "séance). À transmettre au point 13.",
    },
}

# ---------------------------------------------------------------------------
# Journaux : ce qui est conservé, combien de temps, qui y accède (politique de journalisation)
# ---------------------------------------------------------------------------
JOURNAUX = [  # journal, sources, contenu, finalité, durée, accès, traitement
    ("Données de connexion (journal légal)", "FortiGate (NAT), Kea et DT-DHCP (baux), NPS (802.1X), portail invités",
     "qui avait quelle adresse, à quelle heure ; jamais les URL ni le contenu", "réquisitions judiciaires", "1 an",
     "2 personnes nommées, sur réquisition écrite", "T03"),
    ("Journaux des pare-feu", "FortiGate, Stormshield", "flux autorisés et refusés (règle Fxx), alertes IPS", "sécurité",
     "6 mois (90 jours indexés dans Loki)", "RSSI, administrateurs réseau", "T04"),
    ("Journaux des systèmes", "serveurs, hyperviseurs, AD", "connexions, erreurs, changements de droits", "sécurité, exploitation",
     "6 mois", "administrateurs du tier concerné", "T04"),
    ("Sessions d'administration", "Teleport", "enregistrement des sessions et des commandes", "traçabilité de l'administration",
     "1 an", "RSSI", "T05"),
    ("Passages aux portes", "contrôle d'accès", "badge, porte, heure, refus", "sûreté", "3 mois", "chargé de sécurité", "T07"),
    ("Images de vidéoprotection", "enregistreur", "images", "sûreté", "30 jours au plus", "chargé de sécurité + 2 agents", "T06"),
    ("Requêtes à l'IA", "passerelle IA", "contenus ; métadonnées (qui, quand, volume)", "service rendu ; traçabilité",
     "contenus 30 jours ; métadonnées 1 an", "utilisateur (les siens) ; RSSI sur incident", "T08"),
    ("Appels téléphoniques", "IPBX", "numéros, durée, poste", "exploitation, facturation", "1 an", "administrateurs ToIP", "T12"),
]

INTERDITS_JOURNAUX = [
    "Aucun journal ne contient le contenu des communications (courriels, pages consultées, conversations).",
    "L'inspection TLS des postes gérés ne conserve rien : elle sert à bloquer des menaces, pas à enregistrer.",
    "Les journaux ne servent pas à évaluer le travail des agents ni la présence des étudiants (détournement de finalité).",
    "Consulter les journaux d'une personne nommément demande un motif écrit (incident, réquisition) et laisse une trace.",
]

# ---------------------------------------------------------------------------
# Crise d'origine cyber : notifications et cellule de crise (volet gouvernance du PRA ; le PRA technique est au point 15)
# ---------------------------------------------------------------------------
NOTIFICATIONS = [  # qui, quand, délai, par qui, texte
    ("CNIL", "violation de données personnelles présentant un risque pour les personnes", "72 h après en avoir pris connaissance",
     "DPO de l'AMU", "RGPD art. 33"),
    ("Personnes concernées", "violation présentant un risque élevé pour elles", "dans les meilleurs délais", "DPO + direction", "RGPD art. 34"),
    ("ANSSI (CERT-FR)", "incident important, au sens de NIS 2 (une fois la loi entrée en vigueur)",
     "alerte précoce 24 h, notification 72 h, rapport final 1 mois", "RSSI de l'AMU", "NIS 2 art. 23"),
    ("Police ou gendarmerie", "infraction (intrusion, rançon, vol de données) : dépôt de plainte", "le plus tôt possible, avant toute "
     "remise en état qui effacerait les traces", "direction de l'IUT", "Code pénal art. 323-1"),
    ("Ministère (haut fonctionnaire de défense et de sécurité)", "incident touchant la recherche ou d'ampleur nationale",
     "sans délai", "RSSI de l'AMU", "organisation du MESR"),
    ("Assureur", "sinistre cyber, si un contrat existe", "selon le contrat (souvent 48 h à 5 jours)", "service juridique", "contrat"),
]

CELLULE = [  # rôle, qui, mission
    ("Pilote de crise", "Directeur de l'IUT", "décide (coupures, communication, reprise), arbitre"),
    ("RSSI", "RSSI de l'AMU", "dirige la réponse technique, relation avec le CERT-FR et les prestataires PRIS"),
    ("DPO", "DPO de l'AMU", "qualifie la violation de données, notifie la CNIL"),
    ("Communication", "service communication", "messages aux étudiants, aux personnels, à la presse ; moyens hors du SI"),
    ("Exploitation", "administrateurs du site", "confinement, préservation des preuves, restauration (PRA technique, point 15)"),
    ("Main courante", "assistant de direction", "journal horodaté de chaque décision et action (servira à la plainte et au retour d'expérience)"),
    ("Continuité pédagogique", "direction des études", "salles, examens, outils de repli"),
]

FICHES_REFLEXES = [
    ("Poste ou serveur suspect (rançongiciel)", ["Débrancher du réseau sans éteindre (préserver la mémoire)",
     "Prévenir le correspondant SSI", "Ne pas payer, ne pas contacter l'attaquant", "Noter l'heure et ce qui a été vu"]),
    ("Fuite de données", ["Prévenir le DPO tout de suite (le délai de 72 h court)", "Identifier les données et les personnes",
     "Couper l'accès en cause", "Conserver les preuves"]),
    ("Compte compromis", ["Désactiver le compte et ses sessions (AD, Teleport)", "Changer les secrets liés",
     "Chercher les connexions du compte dans les journaux", "Vérifier les droits ajoutés récemment"]),
    ("Crise majeure (SI indisponible)", ["Réunir la cellule de crise, hors du SI (téléphones, salle prévue)",
     "Isoler les zones atteintes (VRF) et Internet si besoin", "Déposer plainte, alerter le CERT-FR",
     "Restaurer depuis les sauvegardes hors ligne, en commençant par le tier 0 (guide ANSSI de remédiation)"]),
]


def cameras():
    """Caméras du plan de câblage, avec le régime juridique probable et les points d'attention."""
    out = []
    with open(ROOT / "livrables" / "plan_cablage" / "prises.csv", encoding="utf-8") as f:
        for p in csv.DictReader(f):
            if p["type"] != "camera":
                continue
            salle = p["salle"].upper()
            if "FOYER" in salle:
                regime, note = "à retirer", "lieu de vie des étudiants : la CNIL s'oppose à la surveillance des lieux de pause"
            elif any(k in salle for k in ("ENTREE", "HALL", "PARKING")):
                regime, note = "CSI si ouvert au public", "autorisation préfectorale si le lieu reçoit du public ; masquer la voie publique"
            elif "SERVEUR" in salle:
                regime, note = "RGPD", "local sensible, accès restreint : finalité claire"
            else:
                regime, note = "RGPD", "circulation intérieure : pas de poste de travail dans le champ"
            out.append((p["id"], p["niveau"], p["salle"], regime, note))
    return out
