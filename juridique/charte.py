"""Point 19 : charte informatique du site (utilisateurs), annexe administrateurs, annexe d'usage de l'IA. Version 1, 18/11/2026.

Rédigée pour être annexée au règlement intérieur de l'AMU (c'est ce qui la rend opposable), après consultation du comité
social d'administration (CSA) pour ce qui touche aux personnels. Texte court et lisible : un utilisateur doit pouvoir la
lire en dix minutes. Les justifications juridiques sont dans le volet juridique, pas dans la charte.
"""

PREAMBULE = (
    "L'IUT met à la disposition de ses étudiants, de ses personnels et de ses invités un réseau, des postes, des services en ligne "
    "et une plateforme d'intelligence artificielle. Ces moyens servent l'enseignement, la recherche et le fonctionnement de l'IUT. "
    "Cette charte dit ce que chacun peut en faire, ce qui est interdit, et ce que l'IUT contrôle. Elle est annexée au règlement "
    "intérieur : la respecter est une obligation pour tous les utilisateurs."
)

ARTICLES = [  # titre, paragraphes
    ("Qui est concerné", [
        "Toute personne qui utilise les moyens informatiques de l'IUT, sur place ou à distance : étudiants, enseignants, chercheurs, "
        "personnels administratifs et techniques, prestataires, invités.",
        "Les administrateurs sont en plus soumis à l'annexe A, et tous les utilisateurs de l'IA à l'annexe B."]),
    ("Votre compte", [
        "Votre compte est personnel. Vous ne le prêtez pas, vous ne communiquez jamais votre mot de passe, même à un informaticien "
        "(l'équipe informatique ne vous le demandera jamais).",
        "Choisissez un mot de passe d'au moins 12 caractères que vous n'utilisez nulle part ailleurs ; activez la double "
        "authentification quand elle est proposée.",
        "Vous êtes responsable de ce qui est fait avec votre compte. Verrouillez votre poste quand vous le quittez."]),
    ("Le réseau et les équipements", [
        "Ne branchez sur les prises du bâtiment que les appareils autorisés. Vos appareils personnels se connectent au Wi-Fi "
        "(eduroam ou réseau invités), jamais sur une prise murale.",
        "Il est interdit de contourner les protections : changer d'adresse pour échapper aux filtres, installer un point d'accès, un "
        "routeur ou un serveur DHCP, analyser le trafic des autres, scanner le réseau.",
        "Exception pédagogique : dans les salles de TP réseau, ces manipulations sont permises sur le matériel et le réseau du TP, "
        "isolés du réseau de l'IUT, sous la responsabilité de l'enseignant. Elles restent interdites partout ailleurs."]),
    ("Usage des moyens", [
        "Les moyens sont fournis pour les études, la recherche et le travail. Un usage personnel raisonnable est toléré (courriels, "
        "démarches) tant qu'il ne gêne pas le service et respecte la loi.",
        "Rangez vos fichiers personnels dans un dossier nommé « Personnel » ou « Privé » : l'IUT n'y accède pas, sauf dans les cas "
        "prévus par la loi ou en votre présence.",
        "Sont interdits notamment : télécharger ou partager des œuvres sans droit, consulter ou diffuser des contenus illicites, "
        "harceler, usurper l'identité de quelqu'un, accéder sans droit à un système (c'est un délit), installer des logiciels "
        "sans licence."]),
    ("Messagerie", [
        "L'adresse de l'IUT sert aux échanges liés aux études et au travail. Méfiez-vous des messages inattendus qui demandent un "
        "mot de passe, un paiement ou d'ouvrir une pièce jointe : en cas de doute, signalez le message sans cliquer.",
        "Un message dont l'objet porte la mention « Personnel » ou « Privé » relève du secret des correspondances."]),
    ("Données personnelles", [
        "Si vous traitez des données sur d'autres personnes (fichiers d'étudiants, enquêtes, données de recherche), ne les utilisez "
        "que pour leur finalité, ne les copiez pas sur des services en ligne non validés par l'IUT, et parlez-en au DPO de l'AMU.",
        "Vous avez des droits sur vos propres données (accès, rectification, opposition) : contactez le DPO de l'AMU."]),
    ("Ce que l'IUT contrôle", [
        "Pour la sécurité du réseau et parce que la loi l'impose, l'IUT conserve pendant un an les données qui permettent de savoir "
        "qui avait quelle adresse et à quelle heure. Il ne conserve ni le contenu de vos échanges ni la liste des sites consultés.",
        "Sur les postes gérés par l'IUT, le trafic chiffré vers Internet peut être analysé automatiquement pour bloquer les virus "
        "et les sites dangereux ; les banques, la santé et les messageries personnelles en sont exclues, et rien n'est enregistré.",
        "Les journaux de sécurité ne servent pas à surveiller votre travail ni votre présence. Un contrôle individuel n'a lieu "
        "qu'en cas d'incident ou d'indice sérieux d'abus, avec un motif écrit, et vous en êtes informé.",
        "Certaines zones du bâtiment sont sous vidéoprotection (entrées, parkings, salle serveur), signalées par des panneaux."]),
    ("Incidents", [
        "Signalez sans attendre tout comportement anormal (poste lent, message de rançon, fichier disparu), la perte d'un appareil "
        "ou un message suspect, au correspondant sécurité de l'IUT. Débranchez le câble réseau d'un poste qui affiche une rançon, "
        "sans l'éteindre.",
        "On ne vous reprochera pas d'avoir signalé une erreur que vous avez faite : plus elle est signalée tôt, moins elle coûte."]),
    ("Départ", [
        "À la fin de vos études ou de votre contrat, votre compte est désactivé puis supprimé trois mois plus tard. Récupérez vos "
        "fichiers personnels avant. Rendez le matériel et les badges qui vous ont été confiés."]),
    ("Sanctions", [
        "Le non-respect de la charte peut entraîner la suspension de l'accès, des poursuites disciplinaires et, pour les infractions, "
        "des poursuites pénales. Les mesures conservatoires (suspension d'un compte) peuvent être prises sans délai si la sécurité "
        "l'exige."]),
]

ANNEXE_ADMIN = [  # titre, paragraphes
    ("Comptes", [
        "Un administrateur a deux comptes au moins : un compte ordinaire pour la bureautique et la messagerie, et un compte "
        "d'administration par niveau (tier 0 pour l'annuaire, tier 1 pour les serveurs, tier 2 pour les postes). Un compte "
        "d'administration ne lit pas de courriel et ne navigue pas sur Internet.",
        "On administre depuis un poste d'administration dédié, en passant par le bastion, avec la double authentification."]),
    ("Accès aux données des utilisateurs", [
        "Les droits techniques d'un administrateur ne l'autorisent pas à lire les données des utilisateurs. Il n'y accède que si "
        "c'est nécessaire à une intervention, et le moins possible ; il n'ouvre pas les fichiers et messages marqués « Personnel ».",
        "Ce qu'il voit à l'occasion de son travail est couvert par une obligation de confidentialité, y compris après son départ.",
        "Une recherche dans les journaux visant une personne demande un motif écrit (incident, réquisition, demande de la direction "
        "validée par le RSSI) et est elle-même tracée."]),
    ("Changements", [
        "Toute modification des pare-feu, de la matrice des flux ou des droits d'administration suit la procédure de changement de "
        "la PSSI : demande écrite, relecture par un second administrateur, trace.",
        "Les secrets (mots de passe d'équipements, clés) sont dans le coffre prévu : jamais dans un fichier, un ticket ou un courriel."]),
    ("Réquisitions et demandes d'accès", [
        "Une réquisition judiciaire est transmise à la direction et au RSSI, qui y répondent. L'administrateur fournit les données "
        "demandées, et seulement elles, selon la procédure de la politique de journalisation.",
        "Une demande d'un supérieur hiérarchique de « regarder ce que fait » un agent ou un étudiant est refusée et renvoyée au RSSI."]),
    ("Alerte", [
        "L'administrateur qui constate une faille, un abus ou une demande contraire à cette annexe le signale au RSSI. Il n'est pas "
        "inquiété pour une alerte faite de bonne foi."]),
]

ANNEXE_IA = [  # titre, paragraphes
    ("À quoi sert la plateforme", [
        "L'IUT met à disposition un assistant d'IA hébergé dans son propre datacenter : vos requêtes ne quittent pas l'IUT et ne "
        "servent pas à entraîner le modèle.",
        "Il aide à rédiger, résumer, expliquer, programmer, traduire. Il se trompe parfois avec assurance : vérifiez toujours ce qu'il "
        "produit avant de vous en servir."]),
    ("Ce qu'il ne faut pas lui confier", [
        "Pas de données sensibles : santé, opinions, origine, vie privée de tiers, mots de passe, données personnelles d'autres "
        "personnes (copies, dossiers d'étudiants), données de recherche confidentielles non autorisées par le laboratoire.",
        "Vos conversations sont gardées 30 jours (vous pouvez les effacer avant) ; seules les informations de connexion (qui, quand, "
        "combien) sont gardées un an."]),
    ("Intégrité des études et des travaux", [
        "Un travail noté doit respecter les règles fixées par l'enseignant sur l'usage de l'IA. Faute de règle, signalez ce qui a été "
        "produit avec l'IA. Présenter comme sien un texte ou un code généré, quand c'est interdit, est une fraude.",
        "Citez l'IA quand vous reprenez ce qu'elle a produit dans un document public ou une publication."]),
    ("Usages interdits", [
        "Générer des contenus illicites, haineux, ou visant à tromper (faux documents, usurpation d'identité).",
        "Contourner les consignes et les filtres de la plateforme, chercher à lire les conversations d'autres utilisateurs.",
        "Utiliser l'IA pour évaluer, noter, classer ou surveiller des étudiants ou des agents, ou pour reconnaître leurs émotions : "
        "ces usages sont interdits ou très encadrés par le règlement européen sur l'IA, et ne sont pas autorisés sur la plateforme.",
        "Revendre l'accès ou automatiser des requêtes en masse sans accord."]),
    ("Se former", [
        "L'IUT propose une courte formation à l'usage de l'IA (fonctionnement, limites, erreurs, données). Elle est demandée avant le "
        "premier usage pour les personnels, et recommandée pour les étudiants."]),
]
