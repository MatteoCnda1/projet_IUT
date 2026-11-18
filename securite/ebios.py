"""Point 09 : analyse de risque EBIOS Risk Manager allégée (ateliers 1 à 3 et plan de traitement). Version 1, 18/11/2026.

Méthode : guide ANSSI EBIOS RM v1.5 (09/2024). Allégée : les scénarios opérationnels (atelier 4) ne sont pas détaillés
technique par technique ; leur vraisemblance est estimée directement, à partir de l'architecture v2 et de la menace
décrite par le CERT-FR pour l'enseignement supérieur (CERTFR-2024-CTI-008).

Les mesures citées (M-xx) sont celles de la PSSI (securite/pssi.py), les règles (Fxx) celles de la matrice (securite/flux.py).
"""

# Échelles (guide EBIOS RM, adaptées au client)
GRAVITE = {
    1: ("Mineure", "gêne ponctuelle, sans effet sur les cours ni sur les données"),
    2: ("Significative", "service dégradé quelques heures, données peu sensibles exposées"),
    3: ("Grave", "cours ou examens interrompus plusieurs jours, données personnelles ou de recherche divulguées, plainte"),
    4: ("Critique", "arrêt de plusieurs semaines, atteinte à des personnes, perte définitive de données, crise publique"),
}
VRAISEMBLANCE = {
    1: ("Peu vraisemblable", "demande des moyens hors de portée de la source de risque, ou un concours de circonstances"),
    2: ("Vraisemblable", "possible pour une source de risque motivée et outillée"),
    3: ("Très vraisemblable", "déjà observé dans l'enseignement supérieur, outils disponibles"),
    4: ("Quasi certain", "se produit régulièrement dans des établissements comparables"),
}

# ---------------------------------------------------------------------------
# Atelier 1 : socle, valeurs métier, biens supports, événements redoutés
# ---------------------------------------------------------------------------
MISSION = ("Former les étudiants de l'IUT Génie Télécom (BUT R&T, licences professionnelles) et soutenir la recherche des laboratoires "
           "de Luminy, sur deux sites reliés (Marseille, Digne), avec un datacenter qui héberge aussi une plateforme d'IA locale.")

VALEURS = [  # code, valeur métier, responsable, biens supports
    ("VM1", "Continuité pédagogique : cours, TP, examens", "Direction de l'IUT",
     "Réseau du bâtiment (cœur, distribution, Wi-Fi), postes des salles de TP, AD et RADIUS, plateformes en ligne"),
    ("VM2", "Données personnelles des étudiants et des personnels (scolarité, absences, géolocalisation des outils du point 13)",
     "Direction + DPO de l'AMU", "AD, application d'absences et de réservation, messagerie, journaux"),
    ("VM3", "Travaux et données de recherche, calculs du datacenter", "Directeurs des laboratoires",
     "Datacenter (clusters DT, stockage), comptes des chercheurs, lien avec Digne"),
    ("VM4", "Service d'IA locale et confidentialité des requêtes", "Direction + DSI",
     "Nœuds GPU, passerelle IA, modèles, journaux des requêtes"),
    ("VM5", "Sécurité des personnes et des biens (contrôle d'accès, vidéoprotection, salle serveur)", "Direction + chargé de sécurité",
     "Badgeuses, caméras, enregistreur, serveur de contrôle d'accès, GTB, alimentation et climatisation"),
    ("VM6", "Image de l'IUT et services publics en ligne (site, messagerie, réservation)", "Direction + service communication",
     "DMZ (Caddy, DNS publics, messagerie), noms de domaine, accès Internet"),
]

EVENEMENTS = [  # code, valeur, événement redouté, impacts, gravité
    ("ER1", "VM1", "Indisponibilité du réseau ou de l'annuaire pendant plus de 2 jours (rançongiciel)",
     "cours et examens annulés, enseignants sans outils, image dégradée", 4),
    ("ER2", "VM2", "Vol et publication des données personnelles des étudiants",
     "violation de données à notifier (CNIL, personnes), sanctions, plaintes", 3),
    ("ER3", "VM3", "Exfiltration discrète de travaux de recherche",
     "perte d'avantage scientifique, contrats de recherche, atteinte au potentiel scientifique", 3),
    ("ER4", "VM4", "Fuite des requêtes envoyées à l'IA, ou IA détournée (contenus illicites, contournement des règles)",
     "atteinte à la vie privée, responsabilité de l'établissement, image", 3),
    ("ER5", "VM5", "Prise de contrôle du contrôle d'accès ou des caméras",
     "intrusion physique, vol de matériel, atteinte aux personnes, images détournées", 4),
    ("ER6", "VM6", "Défiguration du site ou usurpation de la messagerie (hameçonnage au nom de l'IUT)",
     "image publique, hameçonnage des étudiants avec la marque de l'IUT", 2),
    ("ER7", "VM1", "Fraude aux examens : modification de notes ou accès aux sujets", "valeur des diplômes, recours, crise interne", 3),
]

# Socle de sécurité : référentiels applicables et état dans l'architecture v2
SOCLE = [
    ("Guide d'hygiène informatique (42 mesures)", "ANSSI v2 2017", "appliqué : voir le tableau de conformité de la PSSI"),
    ("RGPD et loi Informatique et libertés", "obligatoire", "à formaliser au point 19 (registre, AIPD)"),
    ("Conservation des données de connexion (CPCE L34-1, R10-13)", "obligatoire", "chaîne de journalisation v2, conservation 1 an"),
    ("Directive NIS 2 / loi Résilience, ReCyF", "à venir : entité concernée (hypothèse retenue)", "anticipé : gouvernance, notification, mesures du ReCyF"),
    ("PSSI de l'AMU", "obligatoire (établissement de rattachement)", "la PSSI du site en est une déclinaison"),
    ("Administration sécurisée (PA-022), tiering AD (PA-099)", "recommandations ANSSI", "appliqué en v2 (PAW, Teleport, tier 0)"),
    ("Sécurité de l'IA générative (ANSSI, 2024)", "recommandations ANSSI", "appliqué à la zone IA proposée (E5)"),
]

# ---------------------------------------------------------------------------
# Atelier 2 : sources de risque et objectifs visés
# ---------------------------------------------------------------------------
SOURCES = [  # code, source, objectif visé, motivation (1-3), ressources (1-3), retenu, commentaire
    ("SR1", "Groupe cybercriminel (rançongiciel)", "Chiffrer le SI et voler des données pour faire payer", 3, 3, True,
     "Menace n° 1 pour l'enseignement supérieur selon le CERT-FR : universités françaises touchées chaque année."),
    ("SR2", "Service de renseignement étatique", "Espionner les travaux de recherche, garder un accès durable", 2, 3, True,
     "Visées documentées par le CERT-FR sur les laboratoires (CERTFR-2024-CTI-008)."),
    ("SR3", "Hacktiviste", "Défigurer le site, saturer les services publics, dénoncer", 2, 2, True,
     "Attaques par déni de service et défigurations régulières contre les sites publics."),
    ("SR4", "Étudiant malveillant ou trop curieux", "Modifier des notes, obtenir des sujets, défier l'IUT, abuser de l'IA", 3, 2, True,
     "Accès légitime au réseau, compétences réseau (formation R&T !), outils de test faciles à trouver."),
    ("SR5", "Personnel ou prestataire négligent", "Aucun (erreur) : mauvaise manipulation, mot de passe réutilisé", 1, 2, True,
     "Source d'incidents la plus fréquente ; pas de motivation, mais des accès privilégiés."),
    ("SR6", "Fraudeur à la téléphonie", "Revendre des appels vers des numéros surtaxés", 2, 2, False,
     "Couvert par les mesures ToIP du point 12 (SIP-TLS, comptes par poste, limites) : non détaillé ici."),
]

# ---------------------------------------------------------------------------
# Atelier 3 : écosystème et scénarios stratégiques
# ---------------------------------------------------------------------------
# Partie prenante : dépendance, pénétration, maturité, confiance (1 à 4). Menace = (dépendance × pénétration) / (maturité × confiance)
PARTIES = [
    ("PP1", "Prestataire de maintenance (lot sûreté : caméras, badgeuses)", 3, 3, 2, 2),
    ("PP2", "Éditeurs des pare-feu (Fortinet, Stormshield) : mises à jour", 4, 2, 3, 3),
    ("PP3", "DSI de l'AMU (annuaire fédéré, RENATER, messagerie)", 4, 3, 3, 3),
    ("PP4", "Site jumeau de Digne (même domaine)", 3, 4, 2, 3),
    ("PP5", "Fournisseurs des modèles d'IA (poids téléchargés)", 3, 2, 1, 2),
    ("PP6", "Hébergeur de la sauvegarde externalisée", 3, 1, 3, 3),
    ("PP7", "Étudiants et leurs appareils personnels (BYOD)", 2, 3, 1, 1),
]


def menace(pp):
    _, _, dep, pen, mat, conf = pp
    return round(dep * pen / (mat * conf), 2)


SEUIL_MENACE = 1.5  # au-dessus : partie prenante critique, à traiter

SCENARIOS = [  # code, source, ER visés, chemin d'attaque (étapes), gravité, vraisemblance initiale
    ("SS1", "SR1", ["ER1", "ER2"],
     ["Hameçonnage d'un personnel, ou exploitation d'une passerelle VPN exposée",
      "Rebond depuis le poste vers l'annuaire (vol d'identifiants, élévation de privilèges)",
      "Prise de contrôle du tier 0, désactivation des sauvegardes, chiffrement massif et vol de données"], 4, 3),
    ("SS2", "SR2", ["ER3"],
     ["Compromission d'un chercheur (pièce jointe piégée) ou d'un compte du site jumeau",
      "Mouvement latéral vers le datacenter, exfiltration lente par HTTPS"], 3, 2),
    ("SS3", "SR4", ["ER7", "ER2"],
     ["Étudiant branché en salle de TP ou en Wi-Fi : écoute, faux serveur DHCP, usurpation ARP",
      "Accès aux postes du personnel ou à l'application des absences, modification de notes"], 3, 3),
    ("SS4", "SR1", ["ER5"],
     ["Compromission du prestataire du lot sûreté (accès distant à ses équipements)",
      "Prise en main des caméras ou des UTL du contrôle d'accès, ouverture de portes ou effacement des images"], 4, 2),
    ("SS5", "SR3", ["ER6"],
     ["Exploitation d'une faille du site ou du CMS en DMZ, ou déni de service sur l'accès Internet",
      "Défiguration, ou envoi de courriels frauduleux depuis le domaine de l'IUT"], 2, 3),
    ("SS6", "SR4", ["ER4"],
     ["Injection de consignes dans l'IA (contournement des filtres), abus de quota, extraction des requêtes d'autres utilisateurs",
      "Génération de contenus illicites au nom de l'IUT, ou fuite de données confiées à l'IA"], 3, 3),
    ("SS7", "SR5", ["ER3"],
     ["Erreur d'administration (règle trop large, suppression) ou mot de passe d'administration réutilisé et fuité",
      "Exposition d'un service interne ou perte de données"], 3, 2),
]

# ---------------------------------------------------------------------------
# Plan de traitement : mesures par scénario, vraisemblance résiduelle
# ---------------------------------------------------------------------------
TRAITEMENT = {  # scénario : (mesures PSSI, règles de flux, vraisemblance résiduelle, risque résiduel accepté par)
    "SS1": (["M-ADM-1", "M-ADM-2", "M-IDA-1", "M-IDA-3", "M-RES-1", "M-SAV-1", "M-DET-1", "M-SEN-1"],
            ["F05", "F13", "F37", "F38", "F40", "F45", "F47"], 1, "autorité d'homologation"),
    "SS2": (["M-RES-1", "M-DET-1", "M-DET-2", "M-IDA-3", "M-GOU-3"], ["F16", "F53", "F54"], 1, "directeurs de laboratoire"),
    "SS3": (["M-RES-2", "M-RES-3", "M-RES-4", "M-POS-1"], ["F22", "F23", "F30"], 1, "direction de l'IUT"),
    "SS4": (["M-PHY-3", "M-RES-1", "M-FOU-1", "M-ADM-2"], ["F24", "F25", "F27"], 1, "chargé de sécurité"),
    "SS5": (["M-RES-5", "M-POS-2", "M-DET-1"], ["F01", "F02", "F03", "F12"], 2, "direction de l'IUT"),
    "SS6": (["M-IA-1", "M-IA-2", "M-IA-3", "M-IA-4"], ["F48", "F50", "F52"], 2, "direction + DPO"),
    "SS7": (["M-ADM-1", "M-ADM-3", "M-GOU-2", "M-SAV-1"], ["F38", "F39"], 1, "RSSI"),
}


def verifier(mesures_pssi):
    codes_er = {e[0] for e in EVENEMENTS}
    codes_sr = {s[0] for s in SOURCES if s[5]}
    for code, sr, ers, etapes, g, v in SCENARIOS:
        assert sr in codes_sr, (code, sr)
        assert all(e in codes_er for e in ers), code
        assert g == max(ev[4] for ev in EVENEMENTS if ev[0] in ers), f"{code} : gravité ≠ max des ER visés"
        assert code in TRAITEMENT, code
        mes, regles, vr, _ = TRAITEMENT[code]
        assert vr <= v, code
        for m in mes:
            assert m in mesures_pssi, f"{code} : mesure {m} absente de la PSSI"
    return True
