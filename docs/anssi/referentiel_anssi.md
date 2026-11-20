# Référentiel ANSSI applicable au projet

Site de Marseille. Recherche du 12/11/2026, écarts mis à jour en v2.1 (20/11/2026). Tous les guides sont publiés sur [cyber.gouv.fr](https://cyber.gouv.fr) (ex-ssi.gouv.fr) ou [MesServicesCyber](https://messervices.cyber.gouv.fr).
Les numéros « Pt » renvoient aux 21 points du cahier des charges (roadmap). Ligne marquée *à vérifier* : version ou date lue dans une source secondaire.

## 1. Cadre général et réglementaire

| Document | Réf. / version | Ce qu'il apporte au projet | Pt |
|---|---|---|---|
| [Guide d'hygiène informatique – 42 mesures](https://cyber.gouv.fr/sites/default/files/2013/01/guideline-for-a-healthy-information-system-in-42-measures_v2.pdf) | v2 (2017) | Socle minimal : inventaire, comptes, mises à jour, cloisonnement, journalisation, sauvegarde. Sert de liste de contrôle dans le rapport. | 9, 21 |
| [Référentiel Cyber France (ReCyF)](https://cyber.gouv.fr/actualites/nis-2-lanssi-poursuit-et-renforce-sa-dynamique-daccompagnement/) | 17/03/2026, document de travail | Mesures recommandées par l'ANSSI pour atteindre les objectifs NIS 2, avec un outil de correspondance vers ISO 27001. Non contraignant tant que la loi n'est pas promulguée. | 9, 19 |
| [Directive NIS 2](https://cyber.gouv.fr/la-directive-nis-2) / projet de loi Résilience | Non promulgué au 12/11/2026 | Environ 15 000 entités et 18 secteurs visés en France. Un établissement d'enseignement supérieur devrait être concerné : à citer comme exigence à venir pour le client. | 19 |
| RGS (référentiel général de sécurité) | v2.0 (2014) | S'applique aux autorités administratives, donc à l'université : homologation des téléservices, certificats qualifiés. | 19 |
| [Kit d'exercice de crise ESR](https://cyber.gouv.fr/le-kit-dexercice-dedie-au-secteur-de-lenseignement-superieur-et-de-la-recherche-esr) | ANSSI | Scénarios de crise propres à l'enseignement supérieur : continuité pédagogique, données de recherche. | 15, 19 |
| [Menace sur l'ESR (CERTFR-2024-CTI-008)](https://cert.ssi.gouv.fr/uploads/CERTFR-2024-CTI-008.pdf) | CERT-FR 2024 | État de la menace (espionnage des laboratoires). Sert à justifier l'analyse de risque. | 9 |

## 2. Méthode : risque, homologation, cartographie

| Document | Réf. / version | Ce qu'il apporte au projet | Pt |
|---|---|---|---|
| [EBIOS Risk Manager](https://cyber.gouv.fr/sites/default/files/document/20240901_Guide-EBIOS-RM-V1.5.pdf) | v1.5 (01/09/2024), alignée ISO 27005:2022 | Méthode d'analyse de risque en 5 ateliers. À utiliser pour justifier les choix de sécurité dans le rapport. | 9, 19 |
| [Guide de l'homologation de sécurité](https://messervices.cyber.gouv.fr/documents-guides/guide-homologation-securite-web-04-2025.pdf) | Édition 04/2025 | Démarche pour faire valider le SI par l'autorité (le client). Un bon livrable « force de proposition ». | 19, 21 |
| Cartographie du SI – guide en 5 étapes | 2018 | Vues métier, applicative, infrastructure, administration. Le schéma drawio en est la vue infrastructure. | 3 |
| [Catalogue des produits et services qualifiés](https://cyber.gouv.fr/sites/default/files/document/catalogue-produits-services-qualifies-agrees-certifies-anssi.pdf) | Édition 06/2025 | Liste des produits qualifiés et des prestataires (PASSI audit, PRIS réponse à incident, PDIS détection). | 9, 18 |

## 3. Architecture réseau et pare-feu (Egress, DMZ, cœur, accès)

| Document | Réf. / version | Application au schéma | Pt |
|---|---|---|---|
| [Interconnexion d'un SI à Internet](https://cyber.gouv.fr/sites/default/files/2020/06/anssi-guide-passerelle_internet_securisee-v3.pdf) | v3 (2020) | Architecture de la passerelle Internet : zones, DMZ, flux, relais applicatifs. Couvre EL-RTR, EL-FGT, la DMZ et le reverse proxy Caddy. | 8, 9 |
| [Choisir des pare-feux maîtrisés en zone exposée](https://cyber.gouv.fr/sites/default/files/2018/01/guide_preconisations-pare-feux-zone-exposee-internet_anssi_pa_044_v1.pdf) | PA-044 v1 (2018) | Au moins deux pare-feux en cascade. **Notre FortiGate (externe) + Stormshield (interne) va dans ce sens** : argument à mettre en avant. | 9 |
| [Politique de filtrage d'un pare-feu](https://cyber.gouv.fr/sites/default/files/IMG/pdf/NP_Politique_pare_feu_NoteTech.pdf) | Note technique (2013) | Méthode pour la matrice de flux : liste blanche, règles commentées, revue périodique. | 9 |
| [Configuration sécurisée Stormshield SNS](https://cyber.gouv.fr/sites/default/files/2016/04/guide_sns_anssi_bp_031_v.2.0.pdf) + [guide éditeur v4.3 LTSB](https://documentation.stormshield.eu/SNS/v4/fr/Content/PDF/InstallationGuides/sns-fr-guide_anssi_recommandations_configuration-v4.3-LTSB.pdf) | BP-031 v2.0 | Durcissement de EL-SNS1/2. Choisir une **version qualifiée** (SNS a la Qualification Standard ANSSI). | 9 |
| [Sécurisation d'un commutateur de desserte](https://messervices.cyber.gouv.fr/documents-guides/nt_commutateurs.pdf) | Note technique (*version à vérifier*) | Durcissement des AL-SW et DL-SW : ports inutilisés coupés, sécurité des ports, administration restreinte. | 6 |
| [Contrôle d'accès 802.1X aux réseaux locaux](https://cyber.gouv.fr/sites/default/files/2018/08/guide_802.1x_anssi_pa_043_v1.pdf) | PA-043 v1 (2018) | 802.1X sur les ports d'accès et le Wi-Fi, avec DT-RAD1/2 comme serveurs RADIUS. | 6, 9, 10 |
| [Architectures des SI sensibles ou DR](https://cyber.gouv.fr/sites/default/files/2021/09/anssi-guide-recommandations_architectures_systemes_information_sensibles_ou_diffusion_restreinte-v1.2.pdf) | II 901, v1.2 (2021) | Obligatoire seulement pour un SI Diffusion Restreinte. Bonne référence de zonage pour les laboratoires de recherche. | 3, 9 |
| [Protection des SI essentiels](https://cyber.gouv.fr/sites/default/files/2020/12/guide_protection_des_systemes_essentiels.pdf) | PA-085 (2020) | Architecture de référence (SI d'administration, cloisonnement), utile en vue de NIS 2. | 3, 9 |
| [Nomadisme numérique](https://cyber.gouv.fr/sites/default/files/document/guide_nomadisme_anssi_pa_054_v2.pdf) | PA-054 v2 | VPN des personnels en déplacement, postes nomades, BYOD. | 10, 13 |

## 4. Sans fil, objets connectés, sûreté physique

| Document | Réf. / version | Application | Pt |
|---|---|---|---|
| [Les Essentiels : sécurisation des réseaux Wi-Fi](https://messervices.cyber.gouv.fr/documents-guides/anssi_essentiels_wifi_1.0.pdf) | v1.0 | Désactiver WPS et UPnP, n'autoriser que les bornes maîtrisées, ne pas masquer le SSID, journaliser bornes et contrôleur. WPA2/WPA3-Entreprise. | 10 |
| [Contrôle d'accès physique et vidéoprotection](https://cyber.gouv.fr/sites/default/files/document/anssi-guide-recommandations_securisation_systemes_controle_acces_physique_et_videoprotection-v2.0.pdf) | PA-072 v2.0 (2020) | Badgeuses et caméras IP : réseau dédié, cartographie, interconnexion maîtrisée. Il existe des cibles de sécurité ANSSI pour le [contrôle d'accès](https://cyber.gouv.fr/sites/default/files/document/Syst%C3%A8me%20de%20contr%C3%B4le%20d_acc%C3%A8s%20physique%20v1-1-fr.pdf), les [caméras](https://cyber.gouv.fr/sites/default/files/document/Vid%C3%A9o%20IP%20Cam%C3%A9ra%20v1-0-fr.pdf) et le [VMS](https://cyber.gouv.fr/sites/default/files/document/Vid%C3%A9o%20IP%20VMS%20v1-0-fr.pdf). | 9, 17 |
| [Sécurité des systèmes d'objets connectés](https://cyber.gouv.fr/sites/default/files/2021/09/anssi-guide-securite_des_systemes_objets_connectes_iot-v1.0.pdf) | v1.0 (2021) | Bâtiment intelligent : capteurs et GTB à isoler. | 17 |
| [Systèmes industriels : GTB/GTC](https://messervices.cyber.gouv.fr/documents-guides/Guide__Systemes_industriels___GTB_GTC_2025.pdf) | 2025 | Gestion technique du bâtiment (clim, énergie, accès). | 14, 17 |

## 5. Systèmes, administration et services (NM, Datacenter, DMZ)

| Document | Réf. / version | Application au schéma | Pt |
|---|---|---|---|
| Administration sécurisée des SI ([fiche](https://messervices.cyber.gouv.fr/guides/en-recommendations-secure-administration-it-systems)) | PA-022 v3 (2021) | SI d'administration dédié, postes d'administration dédiés, bastion. Valide notre zone NM et le bastion Teleport. Postes d'administration dédiés : VLAN 906 ADMIN-PAW (v1). | 9, 11, 16 |
| [Administration sécurisée des SI reposant sur Active Directory](https://www.lemondeinformatique.fr/actualites/lire-l-anssi-publie-un-guide-sur-la-securisation-des-si-reposant-sur-active-directory-91922.html) | PA-099 v1.0 (10/2023) | Modèle en tiers : tier 0 (DT-AD1/2), tier 1 (serveurs), tier 2 (postes). Comptes d'administration séparés par tier. | 11 |
| [Remédiation du tier 0 Active Directory](https://www.ssi.gouv.fr/uploads/2023/04/20230417_np_anssi_remediation_volet-technique_tiers0-active-directory_v0_1.pdf) | 2023 | Reconstruction de l'AD après compromission. Va dans le PRA. | 15 |
| [Authentification multifacteur et mots de passe](https://www.val-doise.gouv.fr/index.php/contenu/telechargement/27982/210024/file/Guide%20Authentification%20Multifacteur%20et%20Mots%20de%20passe.pdf) | v2.0 (10/2021) | MFA à privilégier (en particulier pour les administrateurs et le VPN), pas de SMS, au moins 20 caractères pour les secrets non mémorisés, pas d'expiration imposée sur les comptes non sensibles. | 9, 11 |
| [Configuration d'un système GNU/Linux](https://cyber.gouv.fr/sites/default/files/document/fr_np_linux_configuration-v2.0.pdf) | v2.0 (2022) | Durcissement des Debian, LXC et nœuds Proxmox (NM-PVE1/2, DT-PVE1/2, DM-PVE1/2 et témoins). | 11 |
| [Usage sécurisé d'(Open)SSH](https://cyber.gouv.fr/sites/default/files/2014/01/NT_OpenSSH.pdf) + [transition post-quantique SSH](https://messervices.cyber.gouv.fr/documents-guides/transition_post_quantique_ssh_v2.pdf) | DAT-NT-007 (2015) | Authentification par clé, algorithmes, accès par le bastion uniquement. | 11 |
| [Mise en place de cloisonnement système](https://cyber.gouv.fr/sites/default/files/2017/12/guide_cloisonnement_systeme_anssi_pg_040_v1.pdf) | PG-040 v1 (2017) | Isolation des VM et des conteneurs sur le cluster Proxmox. | 11 |
| [Déploiement de conteneurs Docker](https://cyber.gouv.fr/sites/default/files/2020/12/docker_fiche_technique.pdf) | FT-082 (2020) | Supervision (LibreNMS, Grafana, Loki) : conteneurs sans root, ressources limitées ; journaux sur les collecteurs LXC dédiés (v2, SEC-04). | 16 |
| [Fondamentaux : infrastructure VMware](https://messervices.cyber.gouv.fr/documents-guides/anssi-fondamentaux-securisation_infrastructure_vmware_v1-0.pdf) | v1.0 | Il n'existe pas de guide ANSSI pour Proxmox. Les principes de ce guide (administration de l'hyperviseur, réseau de gestion) s'y transposent. | 11 |
| [Architecture d'un système de journalisation](https://cyber.gouv.fr/sites/default/files/2022/01/anssi-guide-recommandations_securite_architecture_systeme_journalisation.pdf) | v2.0 (01/2022) | Chaîne production, collecte, stockage, analyse. Horodatage homogène (LXC chrony). Les deux collecteurs rsyslog dédiés, avec archives scellées (v2, SEC-04), l'appliquent. | 16 |
| [Journalisation Windows en environnement AD](https://cyber.gouv.fr/sites/default/files/2022/01/anssi-guide-recommandations_securite_journalisation_systemes_microsoft_windows_environnement_active_directory.pdf) | 01/2022 | Événements à collecter sur DT-AD, DT-DHCP et NPS. | 16 |
| Recommandations de sécurité relatives à TLS ([fiche](https://messervices.cyber.gouv.fr/guides/en-security-recommendations-tls)) | v1.2 (2020) *à vérifier* | Suites et versions TLS pour Caddy, la messagerie et le VPN. | 9 |
| [Sécurisation des sites web](https://cyber.gouv.fr/sites/default/files/IMG/pdf/NP_Securite_Web_NoteTech.pdf) + [standards côté navigateur](https://cyber.gouv.fr/uploads/2013/05/anssi-guide-recommandations_mise_en_oeuvre_site_web_maitriser_standards_securite_cote_navigateur-v2.0.pdf) + [10 recommandations CMS](https://cyber.gouv.fr/sites/default/files/document/anssi_essentiels_mise-en-oeuvre-securisee-cms_v1.1%20%281%29.pdf) | 2013, v2.0 (2021) | DM-WEB1, l'application de réservation de salles, le site vitrine du projet. En-têtes de sécurité (CSP, HSTS). | 9, 13 |
| [Architectures des services DNS](https://cyber.gouv.fr/sites/default/files/document/anssi-guide-archi_services_dns-v1-0.pdf) | PA-105 v1.0 (07/2024) | Séparer DNS faisant autorité (DM-DNS1) et résolveurs internes (LXC DNS). | 9, 11 |
| [Acquisition et exploitation de noms de domaine](https://cyber.gouv.fr/sites/default/files/2014/05/guide_dns_fr_anssi_1.3.pdf) | v1.3 (2017) | Choix du bureau d'enregistrement, verrouillage du domaine, DNSSEC. | 9 |
| [Sécurisation d'une architecture de téléphonie sur IP](https://messervices.cyber.gouv.fr/documents-guides/NP_securiser_ToIP_NoteTech-v1.pdf) | DAT-NT-14 (12/2013) | VLAN voix, IPBX cloisonné, SIP/SRTP, risque de fraude téléphonique. | 12 |

## 6. Sauvegarde, continuité, crise

| Document | Réf. / version | Application | Pt |
|---|---|---|---|
| [Sauvegarde des SI – les fondamentaux](https://messervices.cyber.gouv.fr/documents-guides/anssi_fondamentaux_sauvegarde_systemes_dinformation_v1.1.pdf) | BP-100 v1.1 | Règle 3-2-1, comptes d'administration de la sauvegarde nominatifs et dédiés, instance dédiée pour le SI d'administration et l'AD, externalisation. Traité en v2 (SEC-03) : disques hors ligne en rotation et copie immuable externalisée (S3 Object Lock). | 15 |
| [Crise d'origine cyber : les clés d'une gestion opérationnelle et stratégique](https://cyber.gouv.fr/publications/crisis-cyber-origin-keys-operational-and-strategic-management) | ANSSI / CDSE | Cellule de crise, rôles, PCA/PRA. | 15, 19 |
| [Anticiper et gérer une crise cyber](https://cyber.gouv.fr/anticiper-et-gerer-une-crise-cyber) (exercice, communication de crise) | ANSSI / CCA | Organiser un exercice et préparer la communication. | 15, 19 |
| [Cyberattaques et remédiation (volet technique)](https://cyber.gouv.fr/sites/default/files/document/20231218_Volet_technique_cyberattaquesetremediation_a5_v1h.pdf) | 12/2023 | Reconstruction après incident, à intégrer au PRA. | 15 |
| [Attaques par rançongiciels, tous concernés](https://www.cybermalveillance.gouv.fr/medias/2019/11/anssi-guide-attaques_par_rancongiciels_tous_concernes-v1.0.pdf) | v1.0 | Prévention et réaction, sauvegardes déconnectées. | 15 |

## 7. Produits : qualification ANSSI

- **Stormshield SNS** : Qualification Standard ANSSI (version 4.3 LTSB qualifiée). La qualification vaut pour une version précise : déployer la version qualifiée et suivre le [cycle de vie des versions qualifiées](https://documentation.stormshield.eu/PLC/SNS/en/Content/SNS_Product_Life_Cycle/Policy_qualified_versions.htm). Bon argument de souveraineté pour le pare-feu interne.
- **FortiGate** : aucune qualification ANSSI trouvée. Ce n'est pas bloquant pour la barrière externe, mais il faut le dire dans le rapport. Consulter le catalogue officiel pour une éventuelle certification CSPN.
- Contrôle d'accès physique : il existe des produits certifiés CSPN ou qualifiés (par exemple Genetec Synergis).
- Hébergement externalisé des sauvegardes : offre qualifiée SecNumCloud (exigée par le CCTP lot 3), données hébergées et traitées dans l'Union européenne, en France de préférence ; à défaut d'offre qualifiée compatible avec le verrouillage S3 Object Lock, dérogation écrite du RSSI.

## 8. Écarts relevés le 12/11/2026 et leur traitement

1. **Postes d'administration dédiés** (PA-022) : traité en v1 (VLAN 906 ADMIN-PAW, accès par le bastion Teleport).
2. **Tiering AD** (PA-099) : traité en v2 (SEC-02) : contrôleurs de domaine en VLAN 310 derrière le Stormshield, hyperviseurs et sauvegarde du tier 0 hors domaine, rôle Teleport dédié ; comptes par tier dans la PSSI.
3. **Sauvegarde hors ligne ou externalisée** (BP-100) : traité en v2 (SEC-03) : PBS hors domaine, disques hors ligne en rotation, copie immuable externalisée (S3 Object Lock).
4. **Journalisation sécurité** : traité en v2 (SEC-04) : deux collecteurs dédiés, archives scellées ; durées fixées en v2.1 (1 an pour les données techniques de connexion, 6 mois pour les URL du proxy). Reste l'analyse (corrélation ou SIEM), à préciser au point 16.
5. **Réseaux dédiés** pour la ToIP, les caméras, les badgeuses et la GTB (PA-072, ToIP, IoT) : traité en v1 (VRF IOT et VLAN par usage, filtrage dans la matrice des flux du point 09).
6. **802.1X** sur tous les ports d'accès et WPA3-Entreprise sur le Wi-Fi (PA-043) : traité dans l'architecture L2 (profils de ports 802.1X/MAB, SSID).
7. **DNS** : séparer le DNS public (DMZ) et les résolveurs internes (PA-105) : en place depuis la v1, justifié dans l'architecture L3 et la matrice des flux.
8. **Analyse de risque EBIOS RM et dossier d'homologation** : analyse de risque livrée au point 09 (RLI-ETU-007) ; le dossier d'homologation reste à produire pour le client.

## 9. Autres normes utiles (hors ANSSI)

- **ISO/IEC 27001 / 27002 / 27005** : SMSI, mesures de sécurité, gestion du risque.
- **ISO 22301** : continuité d'activité (PCA).
- **EN 50600 / TIA-942** : conception des datacenters (énergie, refroidissement, niveaux de disponibilité).
- **ISO/IEC 11801, EN 50173 / 50174** : câblage structuré. **NF C 15-100** : installation électrique.
- Secours électrique (v2.1) : **NF ISO 8528** (groupes électrogènes), **NF EN 60947-6-1** (inverseurs de source), **NF C 15-100** (raccordement au TGBT et au tableau informatique), **NF EN 62040** (onduleurs), **EN 50600-2-2** (alimentation des datacenters).
- **IEEE 802.1X, 802.11ax/be, WPA3** : accès réseau et Wi-Fi.
- **RGPD et CNIL** : registre des traitements, vidéoprotection, durée de conservation. Guides CNIL sur la [sécurité du réseau](https://cnil.fr/fr/securite-proteger-le-reseau-informatique) et la [sauvegarde](https://cnil.fr/fr/securite-sauvegarder).
- **Conservation des données de connexion** (CPCE art. L34-1 ; décrets n° 2021-1361 et 2021-1362) : 1 an pour les données techniques de connexion, 6 mois pour les URL (volet juridique, point 19).
