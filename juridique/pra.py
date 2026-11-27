"""Point 19 : PRA, volet juridique (données de pra_juridique.pdf, RLI-ETU-011).

Ce que le droit impose à la reprise d'activité du site, et ce que le PRA technique du point 15 doit donc garantir.
Partage : ici les obligations, les exigences de reprise par service, les moyens qui les tiennent, les contrats, les preuves et
le calendrier légal ; au point 15 les sauvegardes, l'ordre de restauration et les procédures. La cellule de crise et les
notifications sont celles de donnees.py (CELLULE, NOTIFICATIONS), reprises telles quelles.

Les valeurs techniques sont lues, jamais recopiées : groupe électrogène et onduleurs dans
livrables/energie_refroidissement/resume.json, supports de sauvegarde dans chiffrage/estimation.json. Garanties de
rétablissement (GTR) : décision D4 de la v2.1, 4 h 24 h/24 et 7 j/7 pour les équipements critiques, jour ouvré suivant
pour les autres. Repère « [v2.1] » : élément changé en v2.1 (badge).
"""
import json
import re
from pathlib import Path

import donnees as J

ROOT = Path(__file__).resolve().parent.parent
EST = json.loads((ROOT / "chiffrage" / "estimation.json").read_text(encoding="utf-8"))
ENE = json.loads((ROOT / "livrables" / "energie_refroidissement" / "resume.json").read_text(encoding="utf-8"))
GE = ENE["bet"]["groupe_electrogene"]
OND = ENE["onduleurs"]
V21 = J.V21


def fr(x):
    """Nombre court au format français (virgule décimale, pas de « ,0 »)."""
    return f"{x:g}".replace(".", ",")


def _ligne(motif):
    return next((l for l in EST["capex_lignes"] if motif in l["solution"]), None)


_disques = _ligne("Disque externe")
_inverseur = _ligne("Inverseur de source")
NB_DISQUES = _disques["quantite"] if _disques else 3
TAILLE_DISQUE = (re.search(r"(\d+) To", _disques["solution"]).group(1) + " To") if _disques else "24 To"
DEPART_TGBT = (re.search(r"\d+P \d+ A", _inverseur["solution"]).group(0)) if _inverseur else "4P 63 A"
T_ARRET = GE["arret_nut_si_ge_absent_min"]
T_FIN = GE["fin_arret_min"]

# Garanties de rétablissement (décision D4), reprises par les CCTP lots 1, 2, 3 et 5
GTR_4H = ["routeurs EL-RTR", "pare-feu EL-FGT et EL-SNS", "cœur CL-SW", "distribution DL-SW", "contrôleurs Wi-Fi (WLC)",
          "hyperviseurs DT-PVE et NM-PVE", "serveur de sauvegarde DT-BKP1", "onduleurs et climatiseurs de la salle serveur"]
GTR_J1 = ["switchs d'accès AL-SW", "bornes Wi-Fi", "DMZ (DM-SW, DM-PVE, DM-WITNESS)", "objets (caméras, lecteurs, VS-NVR1)", "autres équipements"]

# ---------------------------------------------------------------------------
# 1. Obligations de continuité : texte, ce qu'il impose, conséquence pour le PRA
# ---------------------------------------------------------------------------
OBLIGATIONS = [
    ("Principe de continuité du service public", "Conseil constitutionnel, décision 79-105 DC du 25 juillet 1979",
     "Le service public d'enseignement ne s'interrompt pas sans nécessité.",
     "Chaque service utile aux cours et aux examens a un mode dégradé écrit, utilisable sans le SI."),
    ("Disponibilité et résilience", "RGPD art. 32.1 b et c",
     "Pouvoir rétablir la disponibilité des données personnelles et leur accès « dans des délais appropriés ».",
     "Une durée maximale d'interruption (DMIA) et une perte de données maximale (PDMA) pour chaque traitement du registre."),
    ("Tester les mesures", "RGPD art. 32.1 d et art. 5.2",
     "Tester, analyser et évaluer régulièrement l'efficacité des mesures, et pouvoir le prouver.",
     "Tests de restauration datés et tracés : un PRA jamais testé ne prouve rien devant la CNIL."),
    ("Registre des violations", "RGPD art. 33.5",
     "Documenter toute violation de données, même celles qui ne sont pas notifiées.",
     "Le registre est tenu par le DPO hors du SI touché ; chaque incident du PRA y est reporté."),
    ("Continuité et gestion de crise", "NIS 2 art. 21.2 c (transposition française en cours)",
     "Continuité des activités : gestion des sauvegardes, reprise après sinistre, gestion de crise.",
     "Le PRA et l'organisation de crise font partie des mesures exigées d'une entité concernée."),
    ("Responsabilité de la direction", "NIS 2 art. 20",
     "Les organes de direction approuvent les mesures, en supervisent la mise en œuvre et se forment.",
     "Le PRA est approuvé par le directeur de l'IUT et le RSSI de l'AMU, revu chaque année."),
    ("Archives publiques", "Code du patrimoine, art. L211-4 et L212-2",
     "Les données produites par l'IUT sont des archives publiques ; leur élimination suit un tri convenu avec les Archives.",
     "Une sauvegarde n'est pas un archivage : la restauration rend des originaux intègres, et aucun original n'est détruit sans visa."),
    ("Données de connexion " + V21, "CPCE art. L34-1 ; politique de journalisation (volet juridique, section 4)",
     "Conserver un an les données techniques de connexion (qui, quand, adresses et ports, volumes), pour les réquisitions.",
     "Les journaux légaux arrivent sur deux collecteurs, sont copiés chaque nuit dans le stockage immuable et chaque semaine sur "
     "disque hors ligne : leur perte est une faute, pas seulement une panne."),
    ("Alerte des secours " + V21, "Règlement de sécurité des ERP, art. MS 70",
     "Disposer d'une liaison avec les sapeurs-pompiers.",
     "Une ligne de secours (analogique ou GSM) indépendante de la téléphonie IP, du réseau du site et de son alimentation "
     "(batterie propre, ou circuit secouru par le groupe électrogène)."),
    ("Signalement au procureur", "Code de procédure pénale, art. 40 al. 2",
     "Tout fonctionnaire qui apprend un délit dans ses fonctions en avise sans délai le procureur de la République.",
     "Une intrusion (C. pénal art. 323-1 à 323-3) est un délit : le signalement fait partie de la procédure de crise."),
    ("Indemnisation par l'assurance", "Code des assurances, art. L12-10-1 (loi LOPMI du 24 janvier 2023)",
     "L'indemnisation d'une cyberattaque suppose une plainte déposée au plus tard 72 h après en avoir eu connaissance.",
     "La plainte figure dans le calendrier des 72 premières heures, avant la remise en état."),
    ("Recherche sensible (si l'enclave est créée)", "Instruction interministérielle II 901",
     "Un système traitant des informations sensibles ou Diffusion Restreinte est homologué, avec ses propres mesures.",
     "L'enclave aurait un PRA à part, homologué ; ce PRA-ci ne la couvre pas."),
]

# ---------------------------------------------------------------------------
# 2. Exigences de reprise par service, données au point 15
# service, équipements et leur GTR, traitements du registre, enjeu juridique, DMIA, PDMA (et ce qui la tient), mode dégradé
# ---------------------------------------------------------------------------
SERVICES = [
    ("Alimentation électrique (salle serveur, locaux techniques) " + V21,
     "onduleurs SRT 6 kVA A et B, climatiseurs (4 h) ; groupe électrogène et inverseur de source (4 h pendant une coupure) ; "
     "onduleurs des L.TECH (J+1)", "—",
     "Condition de toutes les autres DMIA ; ligne de secours des pompiers (MS 70) et contrôle d'accès des issues.",
     "aucune coupure : onduleurs, puis groupe en ≈ 15 s", "sans objet",
     f"Groupe absent à T0 + {T_ARRET} min : arrêt ordonné NUT, fini à T0 + {T_FIN} min (données protégées), redémarrage dans "
     f"l'ordre au retour du secteur ; gazole livré sous 24 h ({GE['autonomie_h']} h d'autonomie à charge moyenne)."),
    ("Accès Internet et filtrage " + V21, "routeurs EL-RTR, pare-feu EL-FGT et EL-SNS (4 h) ; liens des deux opérateurs (4 h)", "T03",
     "Traçabilité des connexions (journal légal NAT) ; accès aux applications de l'AMU (notes, inscriptions) ; information du public.",
     "4 h", "sans objet : configurations sauvegardées chaque nuit",
     "Un seul opérateur (SD-WAN) ou un seul membre de chaque grappe de pare-feu : le service continue, la redondance revient sous 4 h."),
    ("Annuaire et authentification (tier 0)", "DT-AD1, DT-AD2 sur DT-PVE1/2 (4 h)", "T01",
     "Tous les accès et l'imputabilité des actions en dépendent.", "4 h",
     "0 pour la panne d'un serveur (deux contrôleurs de domaine) ; 24 h après une compromission (sauvegarde de la nuit) " + V21,
     "Comptes de secours sous enveloppe scellée, coffre du RSSI ; reconstruction du tier 0 en premier."),
    ("Accès réseau authentifié", "DT-RAD1/2, DT-DHCP1/2 ; cœur CL-SW, distribution DL-SW, WLC (4 h) ; switchs d'accès et bornes (J+1)",
     "T02, T03", "Pas d'accès sans authentification : sinon les connexions ne sont plus imputables (journal légal).", "4 h",
     "24 h : configurations et VM sauvegardées chaque nuit " + V21,
     "Salles de TP sur un VLAN isolé et un poste d'émargement ; pas de Wi-Fi ouvert sans portail ; un switch d'accès en panne : "
     "usagers du local repliés sur le Wi-Fi jusqu'au remplacement."),
    ("Journaux légaux et de sécurité " + V21, "deux collecteurs sur NM-PVE1/2, DT-BKP1 (4 h)", "T03, T04, T05",
     "Obligation de conservation (1 an pour les données de connexion) et valeur de preuve après l'incident.", "72 h",
     "0 visée : les sources du journal légal envoient aux deux collecteurs ; 24 h au plus si la salle est perdue (copie immuable de la nuit)",
     "Pendant la crise, tout est conservé, rien n'est purgé ; les sources gardent leurs journaux en file d'attente sur disque."),
    ("Messagerie", "DM-MAIL1 sur DM-PVE1/2 (DMZ, J+1)", "T13 " + V21,
     "Correspondance administrative ; canal d'information des usagers.", "24 h",
     "15 min pour la panne d'un nœud (réplication) ; 24 h après une compromission (sauvegarde de la nuit) " + V21,
     "Messagerie de l'AMU et liste de contacts imprimée ; pas de courriel depuis le SI compromis."),
    ("Site web et réservation de salles", "DM-WEB1, DM-SRV1, DM-RP1/2 (DMZ, J+1)", "T11",
     "Information du public pendant la crise (message d'indisponibilité).", "48 h", "24 h : sauvegarde de la nuit",
     "Page statique d'information hébergée hors du site, préparée à l'avance."),
    ("DNS publics", "DM-DNS1/2 (DMZ, J+1)", "—",
     "Joignabilité du site et de la messagerie.", "4 h", "sans objet",
     "Zone secondaire chez RENATER ou l'AMU ; la configuration est versionnée, rien à restaurer."),
    ("Vidéoprotection et contrôle d'accès " + V21, "enregistreur VS-NVR1 (zone SRV), caméras, lecteurs et UTL (zone IOT) (J+1)",
     "T06, T07", "Sécurité des personnes ; preuves ; durées maximales (30 jours d'images, 3 mois de passages).", "24 h",
     "passages : 24 h (sauvegarde de la nuit) ; images : non sauvegardées (RAID 6 et double alimentation de VS-NVR1), seuls les "
     "extraits d'un incident le sont",
     "Gardiennage et ouverture mécanique des issues ; aucune image n'est restaurée au-delà de 30 jours."),
    ("Téléphonie IP", "IPBX (point 12), switchs d'accès PoE (J+1)", "T12",
     "Alerte des secours (ERP, MS 70) et joignabilité de l'établissement.", "secours : immédiat ; IPBX : 24 h", "24 h",
     "Ligne de secours au PC sécurité et à l'accueil, testée chaque mois."),
    ("Plateforme d'IA locale (tranche optionnelle)", "IA-FRONT, IA-BACK", "T08",
     "Confort pédagogique ; données des requêtes (30 jours).", "1 semaine", "sans objet",
     "Service suspendu ; les modèles sont réimportés par la procédure contrôlée (M-IA-2, empreintes vérifiées), les conversations "
     "ne sont pas restaurées. " + V21),
    ("Postes et salles de TP", "postes gérés, images de déploiement", "T01",
     "Continuité pédagogique et examens sur machine.", "48 h", "sans objet",
     "Réinstallation par image ; les données locales ne sont pas sauvegardées : la charte demande de stocker les travaux sur l'espace réseau."),
]

NOTE_SERVICES = ("Notes, inscriptions et délibérations sont dans les applications de l'AMU (hors du site) : le PRA du site leur garantit "
                 "l'accès réseau, la reprise de ces applications relève de la DSI de l'AMU. DMIA et PDMA sont des propositions du concepteur, "
                 "à arbitrer avec le client : chaque heure gagnée a un coût, chiffré au point 18. Entre parenthèses, la garantie de "
                 "rétablissement (GTR) exigée des titulaires : 4 h, 24 h/24 et 7 j/7, ou jour ouvré suivant (J+1). " + V21 + " "
                 "Coupure électrique : en v2, sans groupe électrogène, une coupure de plus de 5 à 8 minutes arrêtait tous les serveurs "
                 "jusqu'au retour du secteur, et aucune DMIA ne tenait pendant une coupure longue. En v2.1, le groupe reprend la salle "
                 "serveur et les locaux techniques : les DMIA valent aussi pour une coupure du réseau public, dans la limite de "
                 f"l'autonomie carburant ({GE['autonomie_h']} h à charge moyenne, gazole livré sous 24 h). " + V21)

# ---------------------------------------------------------------------------
# 3. Moyens qui tiennent les PDMA (architecture v2.1 ; fréquences à paramétrer au point 15)
# moyen, ce qu'il protège, fréquence, perte maximale, limite
# ---------------------------------------------------------------------------
MOYENS = [
    ("Services doublés", "deux contrôleurs de domaine, deux NPS, deux DHCP, deux collecteurs de journaux, grappes de deux nœuds "
     "avec témoin", "en continu", "0 pour la panne d'un serveur", "ne protège ni d'une compromission ni d'une erreur, répliquées aussi"),
    ("Réplication ZFS entre les deux nœuds d'une grappe", "VM et conteneurs des grappes NM, DT et DMZ",
     "1 min pour la supervision, 15 min pour les autres VM", "quelques minutes", "même limite"),
    ("Serveur de sauvegarde DT-BKP1 (Proxmox Backup Server, hors domaine)", "toutes les VM et tous les conteneurs, archives des journaux",
     "chaque nuit", "24 h", "dans la salle serveur : perdu avec elle (incendie, inondation)"),
    (f"Disques hors ligne : {NB_DISQUES} × {TAILLE_DISQUE} en rotation (1 branché, 1 au coffre ignifuge, 1 hors site)",
     "copie complète de DT-BKP1", "chaque semaine", "7 jours (disque du coffre), 14 jours (disque hors site)",
     "restauration locale rapide ; à l'abri d'un rançongiciel une fois débranché"),
    ("Copie externalisée immuable (S3 Object Lock en mode conformité)", "copie de DT-BKP1, chiffrée par l'IUT avant l'envoi",
     "chaque nuit, après la sauvegarde", "24 h", "restauration lente (débit des accès Internet) : dernier recours"),
]

# ---------------------------------------------------------------------------
# 4. Continuité électrique (étude du point 14, valeurs lues dans resume.json)
# situation, ce qui se passe, limite
# ---------------------------------------------------------------------------
CONTINUITE = [
    ("Microcoupure, coupure de moins de 15 s", "Onduleurs en ligne double conversion (voies A et B) : aucune interruption.", "—"),
    ("Coupure longue du réseau public",
     f"Le groupe diesel {GE['esp_kva']} kVA ESP / {GE['prp_kva']} kVA PRP démarre seul (défaut confirmé à T0 + 3 s), l'inverseur "
     "de source bascule en ≈ 15 s : les onduleurs ne font que le pont, la climatisation repart à 60 s.",
     f"{GE['autonomie_h']} h à charge moyenne, {GE['autonomie_75_h']} h à 75 % de la PRP (cuve de {GE['cuve_l']} l), puis gazole "
     "livré sous 24 h"),
    ("Le groupe ne démarre pas",
     f"NUT attend {T_ARRET} min : si l'onduleur est encore sur batterie, il lance l'arrêt ordonné (VM non essentielles, VM "
     f"d'infrastructure, contrôleurs de domaine, hyperviseurs), fini à T0 + {T_FIN} min. Les données sont protégées ; les services "
     "restent arrêtés jusqu'au retour du secteur.", f"{OND['autonomie_degrade']} min d'autonomie même avec un seul onduleur"),
    ("Panne d'un onduleur", "L'autre onduleur porte toute la salle (serveurs à double alimentation) ; remplacement sous 4 h.",
     f"{OND['autonomie_degrade']} min sur batterie si le réseau tombe aussi"),
    ("Panne d'un climatiseur", "Le second climatiseur (redondance N+1) prend le relais ; intervention sous 4 h.",
     f"sans aucune climatisation, la salle atteint 35 °C en {fr(ENE['bet']['salle']['t35_min'])} min"),
]

# ---------------------------------------------------------------------------
# 5. Restaurer sans enfreindre le droit
# ---------------------------------------------------------------------------
REGLES_RESTAURATION = [
    ("Les preuves d'abord", "Avant de réinstaller une machine atteinte : copie de la mémoire et des disques, empreintes (SHA-256), "
     "scellés, main courante horodatée. Sans preuve, pas de plainte utile ni d'indemnisation."),
    ("Environnement sain", "Restaurer dans un réseau isolé, en commençant par le tier 0, comme le recommande l'ANSSI (remédiation) : "
     "restaurer sur un annuaire compromis réinstalle l'attaquant."),
    ("Durées de conservation", "Ne remettre en service que des données encore dans leur durée de conservation ; purger ce qui l'a dépassée "
     "(images de plus de 30 jours, contenus de l'IA de plus de 30 jours, adresses des pages consultées de plus de 6 mois) avant la "
     "remise en service. " + V21),
    ("Effacements rejoués", "Une sauvegarde ancienne contient des données effacées depuis (droit à l'effacement, RGPD art. 17). Le DPO tient "
     "un journal des effacements, rejoué après chaque restauration."),
    ("Intégrité des archives", "Pour les documents qui font foi (procès-verbaux, conventions, registres), vérifier les empreintes après "
     "restauration et noter dans la main courante la version restaurée."),
    ("Sauvegarde hors site " + V21, "Le flux F45 envoie une copie chiffrée vers un stockage objet externe. Le fournisseur est sous-traitant "
     f"(RGPD art. 28) : {J.SECNUMCLOUD} ; chiffrement par l'IUT avec une clé que le fournisseur n'a pas, réversibilité et notification "
     "des incidents."),
    ("Pas de rançon", "Ne pas payer, ne pas négocier seul : recommandation constante de l'ANSSI et du ministère de l'Intérieur. Payer ne "
     "garantit ni la restitution ni l'absence de publication."),
]

# ---------------------------------------------------------------------------
# 6. Contrats : clauses à prévoir (reprises dans les CCTP)
# contrat, clause, pourquoi, où
# ---------------------------------------------------------------------------
CONTRATS = [
    ("Opérateurs (Internet et liaison inter-sites)", "Garantie de temps de rétablissement de 4 h, 24 h/24 ; deux adductions séparées ; "
     "pénalités", "Sans lien, rien ne se restaure depuis le site jumeau ni depuis le stockage externe.", "points 07 et 08"),
    ("Maintenance du matériel " + V21, "Garantie de rétablissement de 4 h, 24 h/24 et 7 j/7 pour les équipements critiques ("
     + ", ".join(GTR_4H) + ") ; jour ouvré suivant pour les autres ; le client garde les disques défectueux",
     "Délai de reprise matériel ; un disque rendu au constructeur emporte des données personnelles.", "CCTP lots 1, 2, 3 et 5"),
    ("Groupe électrogène : maintenance et carburant " + V21, "Deux visites préventives par an ; intervention sous 4 h, 24 h/24, "
     "pendant une coupure du réseau public ; livraison de gazole sous 24 h ; essai mensuel en charge et essai annuel sur banc de charge tracés",
     "Un groupe qui ne démarre pas ou tombe en panne sèche ne tient aucune DMIA.", "CCTP lot 5"),
    ("Stockage externe des sauvegardes " + V21, f"Contrat de sous-traitance RGPD art. 28 : {J.SECNUMCLOUD} ; audit, réversibilité, "
     "effacement en fin de contrat, notification d'incident sous 24 h", "Les sauvegardes contiennent tout le SI.", "CCTP lot 3"),
    ("Réponse à incident", "Prestataire qualifié PRIS par l'ANSSI, bon de commande ouvert signé à l'avance",
     "Pendant la crise, il n'y a pas le temps de passer un marché.", "à créer"),
    ("Assurance cyber (si souscrite)", "Déclaration du sinistre dans le délai du contrat ; plainte sous 72 h (C. assurances L12-10-1)",
     "Condition de l'indemnisation.", "service juridique"),
    ("Achats en urgence", "Marché sans publicité ni mise en concurrence en cas d'urgence impérieuse (Code de la commande publique, art. R2122-1)",
     "Racheter du matériel saisi ou détruit dans les jours qui suivent.", "service achats"),
]

# ---------------------------------------------------------------------------
# 7. Calendrier légal des premières heures (H0 = l'incident est connu)
# échéance, action, qui, texte
# ---------------------------------------------------------------------------
CALENDRIER = [
    ("H0", "Ouvrir la main courante, réunir la cellule de crise hors du SI, isoler sans éteindre", "pilote de crise, RSSI", "procédure interne"),
    ("H0 + quelques heures", "Qualifier : données personnelles touchées ? incident important au sens de NIS 2 ?", "DPO, RSSI", "RGPD art. 33 ; NIS 2 art. 23"),
    ("sans délai", "Aviser le procureur de la République", "directeur de l'IUT", "CPP art. 40 al. 2"),
    ("24 h", "Alerte précoce à l'ANSSI (CERT-FR)", "RSSI de l'AMU", "NIS 2 art. 23"),
    ("72 h", "Notifier la CNIL (violation de données présentant un risque)", "DPO de l'AMU", "RGPD art. 33"),
    ("72 h", "Notification d'incident à l'ANSSI, avec une première évaluation", "RSSI de l'AMU", "NIS 2 art. 23"),
    ("72 h", "Dépôt de plainte (police ou gendarmerie)", "direction de l'IUT", "C. pénal art. 323-1 ; C. assurances L12-10-1"),
    ("dès que possible", "Informer les personnes concernées si le risque est élevé", "DPO et direction", "RGPD art. 34"),
    ("1 mois", "Rapport final à l'ANSSI", "RSSI de l'AMU", "NIS 2 art. 23"),
    ("après la crise", "Retour d'expérience ; mise à jour du PRA, de la PSSI et de l'analyse de risque ; registre des violations",
     "RSSI, DPO", "RGPD art. 33.5 ; NIS 2 art. 21"),
]

# ---------------------------------------------------------------------------
# 8. Ce que le point 15 doit livrer pour respecter ce volet
# ---------------------------------------------------------------------------
EXIGENCES_P15 = [
    "Les DMIA et PDMA du tableau de la section 3, service par service, avec le moyen qui les tient (section 4).",
    "Règle 3-2-1-1-0 : trois copies, deux supports, une hors site, une hors ligne ou immuable, zéro erreur aux tests de restauration.",
    "Sauvegarde de toutes les VM et de tous les conteneurs chaque nuit par DT-BKP1, copiée aussitôt dans le stockage immuable "
    "(S3 Object Lock) et chaque semaine sur le disque hors ligne de la rotation. " + V21,
    "Sauvegarde du tier 0 séparée des autres, restaurable sur un réseau isolé.",
    "Ordre de restauration : alimentation et climatisation, tier 0, réseau et authentification, journaux, messagerie, puis les autres services. " + V21,
    "Journaux légaux envoyés aux deux collecteurs (.56 et .57, pas seulement à la VIP), copie immuable quotidienne, copie hors ligne "
    "hebdomadaire ; aucune purge automatique pendant une crise. " + V21,
    "Chiffrement des sauvegardes externes avec une clé conservée par l'IUT (deux exemplaires, hors du SI).",
    f"Séquence d'arrêt ordonné NUT (déclenchée à T0 + {T_ARRET} min si le groupe électrogène n'a pas repris) et redémarrage dans "
    "l'ordre au retour du secteur, testés une fois par an hors période de cours. " + V21,
    "Un test de restauration par trimestre, daté et tracé (preuve de l'art. 32.1 d), et un exercice de crise par an.",
    "Un journal des restaurations : quoi, depuis quelle sauvegarde, par qui, empreintes vérifiées.",
]

GOUVERNANCE = [
    ("Approbation", "directeur de l'IUT et RSSI de l'AMU, après avis du DPO", "à la création, puis chaque année"),
    ("Revue", "RSSI, DPO, administrateurs du site", "après chaque exercice, incident ou changement majeur d'architecture"),
    ("Test de restauration", "administrateurs du site", "chaque trimestre (un service différent à chaque fois)"),
    ("Essai du groupe électrogène " + V21, "exploitant et mainteneur (CCTP lot 5)",
     "chaque mois, 1 h en charge réelle ; chaque année, 2 h sur banc de charge à 75 % de la PRP ; séquence NUT une fois par an"),
    ("Exercice de crise", "cellule de crise complète, kit d'exercice de l'ANSSI pour l'enseignement supérieur", "une fois par an"),
    ("Formation", "membres de la cellule de crise et direction (NIS 2 art. 20)", "à la prise de fonction, puis chaque année"),
    ("Contacts", "assistant de direction", "liste imprimée et à jour, vérifiée chaque trimestre"),
]

A_VALIDER = [
    "Le report au registre de l'AMU des traitements du site, dont la messagerie (T13), ajoutée en v2.1. " + V21,
    "Les DMIA et PDMA de chaque service, et leur coût (point 18).",
    f"Le choix du fournisseur de stockage externe, selon la règle unique : {J.SECNUMCLOUD}. " + V21,
    "La souscription d'une assurance cyber et le contrat de réponse à incident (PRIS).",
    "Le circuit de signalement au procureur (article 40) avec le service juridique de l'AMU.",
    "La ligne de secours vers les sapeurs-pompiers avec le chargé de sécurité de l'ERP.",
    "Le partage des rôles avec la DSI de l'AMU pour les applications hébergées hors du site.",
    f"À vérifier sur site (étude du point 14) : réserve de puissance du TGBT ({ENE['bet']['reserve_tgbt_kva']} kVA, départ "
    f"{DEPART_TGBT}), régime de neutre du bâtiment et emplacement exact du groupe électrogène. " + V21,
]
