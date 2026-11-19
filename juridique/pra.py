"""Point 19 : PRA, volet juridique (données). Version 1, 19/11/2026.

Ce que le droit impose à la reprise d'activité du site, et ce que le PRA technique du point 15 doit donc garantir.
Partage : ici les obligations, les exigences de reprise par service, les contrats, les preuves et le calendrier légal ;
au point 15 les sauvegardes, l'ordre de restauration et les procédures. La cellule de crise et les notifications sont
celles de donnees.py (CELLULE, NOTIFICATIONS), reprises telles quelles.
"""

VERSION = "1.0"

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
     "Une sauvegarde n'est pas un archivage : on restaure des originaux intègres, et on ne détruit pas d'originaux sans visa."),
    ("Données de connexion", "CPCE art. L34-1 ; politique de journalisation (volet juridique, section 4)",
     "Conserver un an les données qui identifient l'auteur d'une connexion, pour les réquisitions.",
     "Les journaux légaux sont restaurables et copiés hors ligne : leur perte est une faute, pas seulement une panne."),
    ("Alerte des secours", "Règlement de sécurité des ERP, art. MS 70",
     "Disposer d'une liaison avec les sapeurs-pompiers.",
     "Une ligne de secours (analogique ou GSM) indépendante de la téléphonie IP et du réseau du site."),
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
# 2. Exigences de reprise par service, données au point 15 (à confirmer avec le client)
# service, serveurs ou zone, traitements du registre, enjeu juridique, DMIA, PDMA, mode dégradé
# ---------------------------------------------------------------------------
SERVICES = [
    ("Annuaire et authentification (tier 0)", "DT-AD1, DT-AD2", "T01",
     "Tous les accès et l'imputabilité des actions en dépendent.", "4 h", "1 h",
     "Comptes de secours sous enveloppe scellée, coffre du RSSI ; reconstruction du tier 0 en premier."),
    ("Accès réseau authentifié", "DT-RAD1/2, DT-DHCP1/2, contrôleurs Wi-Fi", "T02, T03",
     "Pas d'accès sans authentification : sinon les connexions ne sont plus imputables (journal légal).", "4 h", "24 h",
     "Salles de TP sur un VLAN isolé et un poste d'émargement ; pas de Wi-Fi ouvert sans portail."),
    ("Journaux légaux et de sécurité", "collecteur de journaux, DT-BKP1, copie hors ligne", "T03, T04, T05",
     "Obligation de conservation (1 an) et valeur de preuve après l'incident.", "72 h", "24 h",
     "Copie quotidienne hors ligne ; pendant la crise, on conserve tout, on ne purge rien."),
    ("Messagerie", "DM-MAIL1", "hors registre (à ajouter)",
     "Correspondance administrative ; canal d'information des usagers.", "24 h", "4 h",
     "Messagerie de l'AMU et liste de contacts imprimée ; pas de courriel depuis le SI compromis."),
    ("Site web et réservation de salles", "DM-WEB1, DM-SRV1, DM-RP1/2", "T11",
     "Information du public pendant la crise (message d'indisponibilité).", "48 h", "24 h",
     "Page statique d'information hébergée hors du site, préparée à l'avance."),
    ("DNS publics", "DM-DNS1/2", "—",
     "Joignabilité du site et de la messagerie.", "4 h", "sans objet",
     "Zone secondaire chez RENATER ou l'AMU ; la configuration est versionnée, rien à restaurer."),
    ("Vidéoprotection et contrôle d'accès", "enregistreur, badgeuses (zone IOT)", "T06, T07",
     "Sécurité des personnes ; preuves ; durées maximales (30 jours d'images, 3 mois de passages).", "24 h", "24 h",
     "Gardiennage et ouverture mécanique des issues. PDMA pour les passages ; aucune pour les images, jamais restaurées au-delà de 30 jours."),
    ("Téléphonie IP", "IPBX (point 12)", "T12",
     "Alerte des secours (ERP, MS 70) et joignabilité de l'établissement.", "secours : immédiat ; IPBX : 24 h", "24 h",
     "Ligne de secours au PC sécurité et à l'accueil, testée chaque mois."),
    ("Plateforme d'IA locale (proposition)", "IA-FRONT, IA-BACK", "T08",
     "Confort pédagogique ; données des requêtes (30 jours).", "1 semaine", "sans objet",
     "Service suspendu ; les modèles sont retéléchargés, les conversations ne sont pas restaurées."),
    ("Postes et salles de TP", "postes gérés, images de déploiement", "T01",
     "Continuité pédagogique et examens sur machine.", "48 h", "sans objet",
     "Réinstallation par image ; les données locales ne sont pas sauvegardées : la charte demande de stocker les travaux sur l'espace réseau."),
]

NOTE_SERVICES = ("Notes, inscriptions et délibérations sont dans les applications de l'AMU (hors du site) : le PRA du site leur garantit "
                 "l'accès réseau, la reprise de ces applications relève de la DSI de l'AMU. DMIA et PDMA sont des propositions du concepteur, "
                 "à arbitrer avec le client : chaque heure gagnée a un coût, chiffré au point 18.")

# ---------------------------------------------------------------------------
# 3. Restaurer sans enfreindre le droit
# ---------------------------------------------------------------------------
REGLES_RESTAURATION = [
    ("Les preuves d'abord", "Avant de réinstaller une machine atteinte : copie de la mémoire et des disques, empreintes (SHA-256), "
     "scellés, main courante horodatée. Sans preuve, pas de plainte utile ni d'indemnisation."),
    ("Environnement sain", "Restaurer dans un réseau isolé, en commençant par le tier 0, comme le recommande l'ANSSI (remédiation) : "
     "restaurer sur un annuaire compromis réinstalle l'attaquant."),
    ("Durées de conservation", "Ne remettre en service que des données encore dans leur durée de conservation ; purger ce qui l'a dépassée "
     "(images de plus de 30 jours, contenus de l'IA de plus de 30 jours) avant la remise en service."),
    ("Effacements rejoués", "Une sauvegarde ancienne contient des données effacées depuis (droit à l'effacement, RGPD art. 17). Le DPO tient "
     "un journal des effacements, rejoué après chaque restauration."),
    ("Intégrité des archives", "Pour les documents qui font foi (procès-verbaux, conventions, registres), vérifier les empreintes après "
     "restauration et noter dans la main courante la version restaurée."),
    ("Sauvegarde hors site", "Le flux F45 envoie une copie chiffrée vers un stockage objet externe. Le fournisseur est sous-traitant (RGPD art. 28) : "
     "hébergement dans l'Union, chiffrement par l'IUT avec une clé que le fournisseur n'a pas, réversibilité et notification des incidents."),
    ("Pas de rançon", "Ne pas payer, ne pas négocier seul : recommandation constante de l'ANSSI et du ministère de l'Intérieur. Payer ne "
     "garantit ni la restitution ni l'absence de publication."),
]

# ---------------------------------------------------------------------------
# 4. Contrats : clauses à prévoir (reprises dans les CCTP)
# contrat, clause, pourquoi, où
# ---------------------------------------------------------------------------
CONTRATS = [
    ("Opérateurs (Internet et liaison inter-sites)", "Garantie de temps de rétablissement de 4 h, 24 h/24 ; deux adductions séparées ; "
     "pénalités", "Sans lien, rien ne se restaure depuis le site jumeau ni depuis le stockage externe.", "points 07 et 08"),
    ("Maintenance du matériel", "Remplacement sous 4 h pour le cœur, les pare-feu et les hyperviseurs ; le client garde les disques défectueux",
     "Délai de reprise matériel ; un disque rendu au constructeur emporte des données personnelles.", "CCTP lots 1 à 3"),
    ("Stockage externe des sauvegardes", "Contrat de sous-traitance RGPD art. 28 : localisation UE, audit, réversibilité, effacement en fin "
     "de contrat, notification d'incident sous 24 h ; offre qualifiée SecNumCloud de préférence", "Les sauvegardes contiennent tout le SI.", "CCTP lot 3"),
    ("Réponse à incident", "Prestataire qualifié PRIS par l'ANSSI, bon de commande ouvert signé à l'avance",
     "Pendant la crise, on n'a pas le temps de passer un marché.", "à créer"),
    ("Assurance cyber (si souscrite)", "Déclaration du sinistre dans le délai du contrat ; plainte sous 72 h (C. assurances L12-10-1)",
     "Condition de l'indemnisation.", "service juridique"),
    ("Achats en urgence", "Marché sans publicité ni mise en concurrence en cas d'urgence impérieuse (Code de la commande publique, art. R2122-1)",
     "Racheter du matériel saisi ou détruit dans les jours qui suivent.", "service achats"),
]

# ---------------------------------------------------------------------------
# 5. Calendrier légal des premières heures (H0 = l'incident est connu)
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
# 6. Ce que le point 15 doit livrer pour respecter ce volet
# ---------------------------------------------------------------------------
EXIGENCES_P15 = [
    "Les DMIA et PDMA du tableau de la section 3, service par service, avec la mesure qui les tient.",
    "Règle 3-2-1-1-0 : trois copies, deux supports, une hors site, une hors ligne ou immuable, zéro erreur aux tests de restauration.",
    "Sauvegarde du tier 0 séparée des autres, restaurable sur un réseau isolé.",
    "Ordre de restauration : tier 0, réseau et authentification, journaux, messagerie, puis les autres services.",
    "Copie quotidienne hors ligne des journaux légaux ; aucune purge automatique pendant une crise.",
    "Chiffrement des sauvegardes externes avec une clé conservée par l'IUT (deux exemplaires, hors du SI).",
    "Un test de restauration par trimestre, daté et tracé (preuve de l'art. 32.1 d), et un exercice de crise par an.",
    "Un journal des restaurations : quoi, depuis quelle sauvegarde, par qui, empreintes vérifiées.",
]

GOUVERNANCE = [
    ("Approbation", "directeur de l'IUT et RSSI de l'AMU, après avis du DPO", "à la création, puis chaque année"),
    ("Revue", "RSSI, DPO, administrateurs du site", "après chaque exercice, incident ou changement majeur d'architecture"),
    ("Test de restauration", "administrateurs du site", "chaque trimestre (un service différent à chaque fois)"),
    ("Exercice de crise", "cellule de crise complète, kit d'exercice de l'ANSSI pour l'enseignement supérieur", "une fois par an"),
    ("Formation", "membres de la cellule de crise et direction (NIS 2 art. 20)", "à la prise de fonction, puis chaque année"),
    ("Contacts", "assistant de direction", "liste imprimée et à jour, vérifiée chaque trimestre"),
]

A_VALIDER = [
    "L'ajout de la messagerie (DM-MAIL1) au registre des traitements : elle n'y figure pas encore.",
    "Les DMIA et PDMA de chaque service, et leur coût (point 18).",
    "Le fournisseur de stockage externe et sa qualification (SecNumCloud ou non).",
    "La souscription d'une assurance cyber et le contrat de réponse à incident (PRIS).",
    "Le circuit de signalement au procureur (article 40) avec le service juridique de l'AMU.",
    "La ligne de secours vers les sapeurs-pompiers avec le chargé de sécurité de l'ERP.",
    "Le partage des rôles avec la DSI de l'AMU pour les applications hébergées hors du site.",
]
