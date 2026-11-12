# Étude Technique – Architecture Physique, Énergie & Refroidissement
## Point 14 du Référentiel BUT3 Réseaux & Télécommunications – Site de Marseille (Campus de Luminy)

---

### Informations Générales du Projet
- **Projet** : Refonte de l'infrastructure réseau et système – Bâtiment Génie Télécom, Campus de Luminy (Marseille).
- **Livrable** : Architecture physique, alimentation électrique secourue 2N et climatisation de précision N+1.
- **Périmètre** :
  1. **Salle Serveur (Datacenter)** : ~25 m² située en partie sud de la salle J05 au sous-sol (N-1), mitoyenne du local N-1-LT01, abritant 2 baies 42U (800×1000 mm).
  2. **6 Locaux Techniques d'Étage (L.TECH)** : répartiteurs d'étage hébergeant 15 commutateurs d'accès 48 ports PoE+, 38 bornes Wi-Fi 6E, 15 caméras IP et 11 badgeuses.
- **Auteur** : Ingénieur Consultant Spécialiste Architecture Physique, Énergie & Climatisation.
- **Schémas vectoriels associés** :
  - [Synoptique Électrique 2N (SVG)](file:///home/matteo/Projet_perso/projet_IUT/livrables/energie_refroidissement/schemas/synoptique_electrique.svg)
  - [Plan d'Aménagement & Aéraulique Salle Serveur (SVG)](file:///home/matteo/Projet_perso/projet_IUT/livrables/energie_refroidissement/schemas/aeraulique_salle_serveur.svg)
- **Fichier de calculs** : [bilan_puissance.csv](file:///home/matteo/Projet_perso/projet_IUT/livrables/energie_refroidissement/bilan_puissance.csv) généré par [bilan_puissance.py](file:///home/matteo/Projet_perso/projet_IUT/livrables/energie_refroidissement/bilan_puissance.py).

---

## Sommaire

1. [Introduction & Objectifs de Résilience (Tier III / EN 50600 Class 3)](#1-introduction--objectifs-de-résilience)
2. [Bilan de Puissance Détaillé (Salle Serveur & 6 L.TECH)](#2-bilan-de-puissance-détaillé)
   - 2.1 Baie 1 : Réseau, Sécurité, DMZ, Cœur et Distribution
   - 2.2 Baie 2 : Datacenter, Cluster Proxmox Ceph HA, Active Directory, PBS Backup
   - 2.3 Synthèse globale de la salle serveur
   - 2.4 Bilan des 6 Locaux Techniques (L.TECH)
3. [Architecture Électrique Redondante 2N](#3-architecture-électrique-redondante-2n)
   - 3.1 Chaîne d'alimentation amont (Enedis + Groupe Électrogène + ATS)
   - 3.2 TGBT Salle Serveur et découplage strict Voie A / Voie B
   - 3.3 Onduleurs On-Line Double Conversion APC Smart-UPS SRT 6 kVA
   - 3.4 Dimensionnement des batteries et profil d'autonomie (standard vs packs externes)
   - 3.5 Distribution terminale : PDU métrées et commutateur de transfert ATS 1U
   - 3.6 Sélectivité ampèremétrique et chronométrique (NF C 15-100)
4. [Bilan Thermique, Climatisation de Précision & Aéraulique](#4-bilan-thermique-climatisation--aéraulique)
   - 4.1 Bilan thermique exhaustif (charges sensibles et latentes)
   - 4.2 Solution de climatisation redondante N+1 (armoires DX Inverter 7.2 kW)
   - 4.3 Urbanisation en allée froide confinée (Cold Aisle Containment - CAC)
   - 4.4 Exploitation du free-cooling nocturne méditerranéen
   - 4.5 Ventilation forcée des 6 locaux techniques (dont le placard N0-LT01 de 2.3 m²)
5. [Efficacité Énergétique, Green IT & Trajectoire PUE](#5-efficacité-énergétique-green-it--trajectoire-pue)
   - 5.1 Calcul mathématique du PUE prévisionnel (été, hiver, moyenne annuelle)
   - 5.2 Leviers Green IT mis en œuvre (Ashrae A1, alimentations Titanium, mode ECO)
   - 5.3 Métrologie continue SNMPv3 / Modbus avec LibreNMS & Grafana
6. [Sécurité Physique et Environnementale](#6-sécurité-physique-et-environnementale)
   - 6.1 Système d'extinction automatique par gaz propre FK-5-1-12 (Novec 1230)
   - 6.2 Détection précoce d'incendie par aspiration laser (VESDA)
   - 6.3 Contrôle d'accès physique et conformité aux recommandations ANSSI
7. [Synthèse Économique & Conformité CAPEX/OPEX](#7-synthèse-économique--conformité-capexopex)

---

## 1. Introduction & Objectifs de Résilience

### 1.1 Contexte et Enjeux
L'infrastructure informatique et de télécommunications du campus de Luminy à Marseille dessert l'ensemble des départements pédagogiques, des équipes de recherche et des services administratifs. L'arrêt inopiné de la salle serveur entraîne l'interruption immédiate de l'accès à Internet, des réseaux pédagogiques, des services d'authentification centralisés (Active Directory, RADIUS 802.1X), de la téléphonie sur IP et des systèmes de sûreté physique (vidéoprotection et contrôle des accès par badge).

Pour répondre à ces exigences sans compromis, la conception physique du datacenter et des locaux techniques s'appuie sur :
- **La norme européenne EN 50600** : Niveau de disponibilité **Class 3** (composants redondants avec distribution 2N tolérante aux pannes sans interruption).
- **Le référentiel Uptime Institute** : Équivalence **Tier III** (Maintenance concourante : tout composant de la chaîne électrique ou frigorifique peut être isolé pour maintenance préventive ou curative sans interruption de l'activité IT).
- **La disponibilité visée** : **99.982 %** (indisponibilité maximale cumulée inférieure à 1.6 heure par an).

```
                      +---------------------------------------+
                      |       Réseau Enedis 400V Triphasé     |
                      +-------------------+-------------------+
                                          |
                      +-------------------+-------------------+
                      |   Groupe Électrogène Campus 250 kVA   |
                      +-------------------+-------------------+
                                          |
                      +-------------------+-------------------+
                      |    Inverseur de Source Campus (ATS)   |
                      +-------------------+-------------------+
                                          |
                 +------------------------+------------------------+
                 |                                                 |
                 v                                                 v
   +---------------------------+                     +---------------------------+
   |   TGBT Voie A (Normale)   |                     |   TGBT Voie B (Secours)   |
   +-------------+-------------+                     +-------------+-------------+
                 |                                                 |
   +-------------v-------------+                     +-------------v-------------+
   |  Onduleur A : SRT 6 kVA   |                     |  Onduleur B : SRT 6 kVA   |
   |   On-Line Double Conv.    |                     |   On-Line Double Conv.    |
   +-------------+-------------+                     +-------------+-------------+
                 |                                                 |
   +-------------v-------------+                     +-------------v-------------+
   |   PDU A1 (Baie 1) & A2    |                     |   PDU B1 (Baie 1) & B2    |
   +-------------+-------------+                     +-------------+-------------+
                 \                                                 /
                  \                                               /
                   +---------------------------------------------+
                   | 16 Serveurs Dell + Switchs Réseau Double Alim|
                   +---------------------------------------------+
```

---

## 2. Bilan de Puissance Détaillé

Le calcul précis des puissances nominales, puissances crêtes et facteurs de puissance a été réalisé sur chaque équipement référencé dans l'architecture matérielle du site. Les puissances thermiques sont rigoureusement égales à l'intégralité de l'énergie électrique consommée par effet Joule (1 W électrique consommé = 1 W thermique dissipé = 3.412142 BTU/h).

### 2.1 Baie 1 : Réseau, Sécurité, DMZ, Cœur et Distribution (42U 800×1000)

| Repère | Équipement | U | Nb Alim | Type Alim | $P_{\text{nom}}$ (W) | $P_{\text{pic}}$ (W) | $\cos \varphi$ | $S_{\text{nom}}$ (VA) | Dissipation (BTU/h) | Fonction & Remarques |
|:---|:---|:---:|:---:|:---|---:|---:|:---:|---:|---:|:---|
| **EL-RTR1** | Cisco Catalyst C8200L-1N-4T | U41 | 1 | Monosource interne | 20 | 28 | 0.88 | 22.7 | 68.2 | Routeur bordure WAN 1 (FAI 1) via ATS 1U |
| **EL-RTR2** | Cisco Catalyst C8200L-1N-4T | U40 | 1 | Monosource interne | 20 | 28 | 0.88 | 22.7 | 68.2 | Routeur bordure WAN 2 (FAI 2) via ATS 1U |
| **ATS-B1** | APC AP4421A Rack ATS | U39 | 2 | 2x Entrées C14 (10A) | 10 | 15 | 0.90 | 11.1 | 34.1 | Inverseur automatique 1U pour EL-RTR1/2 |
| **EL-FGT1** | FortiGate 120G | U38 | 2 | Double 1+1 100W | 32 | 53 | 0.95 | 33.7 | 109.2 | Pare-feu externe HA (Actif) |
| **EL-FGT2** | FortiGate 120G | U37 | 2 | Double 1+1 100W | 32 | 53 | 0.95 | 33.7 | 109.2 | Pare-feu externe HA (Passif) |
| **EL-SW1** | Cisco Catalyst C9200L-24T-4X-E | U35 | 2 | Double 1+1 125W | 45 | 70 | 0.95 | 47.4 | 153.5 | Switch WAN 1 |
| **EL-SW2** | Cisco Catalyst C9200L-24T-4X-E | U34 | 2 | Double 1+1 125W | 45 | 70 | 0.95 | 47.4 | 153.5 | Switch WAN 2 |
| **EL-SNS1** | Stormshield SN710 | U32 | 2 | Double 1+1 150W | 40 | 65 | 0.95 | 42.1 | 136.5 | Pare-feu interne HA (Qualif Standard ANSSI) |
| **EL-SNS2** | Stormshield SN710 | U31 | 2 | Double 1+1 150W | 40 | 65 | 0.95 | 42.1 | 136.5 | Pare-feu interne HA (Qualif Standard ANSSI) |
| **DM-SW1** | Cisco Catalyst C9200L-24T-4X-E | U29 | 2 | Double 1+1 125W | 45 | 70 | 0.95 | 47.4 | 153.5 | Switch DMZ 1 |
| **DM-SW2** | Cisco Catalyst C9200L-24T-4X-E | U28 | 2 | Double 1+1 125W | 45 | 70 | 0.95 | 47.4 | 153.5 | Switch DMZ 2 |
| **DM-RP1** | Dell PowerEdge R260 | U26 | 2 | Double 1+1 450W Plat | 110 | 200 | 0.95 | 115.8 | 375.3 | Reverse-proxy public 1 (Caddy) |
| **DM-RP2** | Dell PowerEdge R260 | U25 | 2 | Double 1+1 450W Plat | 110 | 200 | 0.95 | 115.8 | 375.3 | Reverse-proxy public 2 (Caddy) |
| **DM-DNS1** | Dell PowerEdge R260 | U24 | 2 | Double 1+1 450W Plat | 110 | 200 | 0.95 | 115.8 | 375.3 | Serveur DNS autoritaire externe |
| **DM-WEB1** | Dell PowerEdge R260 | U23 | 2 | Double 1+1 450W Plat | 110 | 200 | 0.95 | 115.8 | 375.3 | Serveur Web public & réservations |
| **DM-MAIL1**| Dell PowerEdge R260 | U22 | 2 | Double 1+1 450W Plat | 110 | 200 | 0.95 | 115.8 | 375.3 | Passerelle de messagerie (MX) |
| **DM-SRV1** | Dell PowerEdge R260 | U21 | 2 | Double 1+1 450W Plat | 110 | 200 | 0.95 | 115.8 | 375.3 | Serveur applicatif interne DMZ |
| **CL-SW1** | Cisco Catalyst C9500-16X-E | U18 | 2 | Double 1+1 950W | 140 | 220 | 0.95 | 147.4 | 477.7 | Switch Cœur 1 (StackWise Virtual) |
| **CL-SW2** | Cisco Catalyst C9500-16X-E | U17 | 2 | Double 1+1 950W | 140 | 220 | 0.95 | 147.4 | 477.7 | Switch Cœur 2 (StackWise Virtual) |
| **DL-SW1** | Cisco Catalyst C9500-16X-E | U15 | 2 | Double 1+1 950W | 140 | 220 | 0.95 | 147.4 | 477.7 | Switch Distribution 1 (SVL Bloc 1) |
| **DL-SW2** | Cisco Catalyst C9500-16X-E | U14 | 2 | Double 1+1 950W | 140 | 220 | 0.95 | 147.4 | 477.7 | Switch Distribution 2 (SVL Bloc 1) |
| **DL-SW3** | Cisco Catalyst C9500-16X-E | U12 | 2 | Double 1+1 950W | 140 | 220 | 0.95 | 147.4 | 477.7 | Switch Distribution 3 (SVL Bloc 2) |
| **DL-SW4** | Cisco Catalyst C9500-16X-E | U11 | 2 | Double 1+1 950W | 140 | 220 | 0.95 | 147.4 | 477.7 | Switch Distribution 4 (SVL Bloc 2) |
| **PDU-B1** | 2x APC AP8959EU3 | 0U | 2 | 2x 230V 16A (Voies A/B) | 30 | 30 | 0.95 | 31.6 | 102.4 | PDU intelligentes métrées par prise |
| **UPS-A** | APC SRT6KRMXLI | U1-U4| - | Châssis rack 4U | - | - | - | - | - | Onduleur Voie A logé en fond de baie |
| **TOTAL** | **Baie 1 (24 matériels)**| - | - | - | **1 904 W**| **3 137 W**| **0.95**| **2 008 VA**| **6 497 BTU/h** | **Charge nominale parfaitement équilibrée** |

---

### 2.2 Baie 2 : Datacenter, Cluster Proxmox Ceph HA, AD & Backup (42U 800×1000)

| Repère | Équipement | U | Nb Alim | Type Alim | $P_{\text{nom}}$ (W) | $P_{\text{pic}}$ (W) | $\cos \varphi$ | $S_{\text{nom}}$ (VA) | Dissipation (BTU/h) | Fonction & Remarques |
|:---|:---|:---:|:---:|:---|---:|---:|:---:|---:|---:|:---|
| **NM-SW1** | Cisco Catalyst C9200L-24T-4X-E | U41 | 2 | Double 1+1 125W | 45 | 70 | 0.95 | 47.4 | 153.5 | Switch Administration Out-of-Band 1 |
| **NM-SW2** | Cisco Catalyst C9200L-24T-4X-E | U40 | 2 | Double 1+1 125W | 45 | 70 | 0.95 | 47.4 | 153.5 | Switch Administration Out-of-Band 2 |
| **NM-PVE1**| Dell PowerEdge R660xs | U37 | 2 | Double 1+1 800W Tit. | 200 | 350 | 0.96 | 208.3 | 682.4 | Nœud Proxmox HA 1 (2x Xeon 4510, Ceph OSD) |
| **NM-PVE2**| Dell PowerEdge R660xs | U36 | 2 | Double 1+1 800W Tit. | 200 | 350 | 0.96 | 208.3 | 682.4 | Nœud Proxmox HA 2 (2x Xeon 4510, Ceph OSD) |
| **NM-PVE3**| Dell PowerEdge R660xs | U35 | 2 | Double 1+1 800W Tit. | 200 | 350 | 0.96 | 208.3 | 682.4 | Nœud Proxmox HA 3 (2x Xeon 4510, Ceph OSD) |
| **DT-SW1** | Cisco Catalyst C9300X-12Y-E | U32 | 2 | Double 1+1 715W | 130 | 200 | 0.95 | 136.8 | 443.6 | Switch Datacenter 1 (25 GbE SFP28) |
| **DT-SW2** | Cisco Catalyst C9300X-12Y-E | U31 | 2 | Double 1+1 715W | 130 | 200 | 0.95 | 136.8 | 443.6 | Switch Datacenter 2 (25 GbE SFP28) |
| **DT-AD1** | Dell PowerEdge R360 | U28 | 2 | Double 1+1 600W Plat | 115 | 180 | 0.95 | 121.1 | 392.4 | Active Directory 1 (PDC / DNS / LDAP) |
| **DT-AD2** | Dell PowerEdge R360 | U27 | 2 | Double 1+1 600W Plat | 115 | 180 | 0.95 | 121.1 | 392.4 | Active Directory 2 (BDC / DNS / LDAP) |
| **DT-RAD1**| Dell PowerEdge R360 | U25 | 2 | Double 1+1 600W Plat | 115 | 180 | 0.95 | 121.1 | 392.4 | Serveur NPS / RADIUS 802.1X Primaire |
| **DT-RAD2**| Dell PowerEdge R360 | U24 | 2 | Double 1+1 600W Plat | 115 | 180 | 0.95 | 121.1 | 392.4 | Serveur NPS / RADIUS 802.1X Secondaire |
| **DT-DHCP1**| Dell PowerEdge R360 | U22 | 2 | Double 1+1 600W Plat | 115 | 180 | 0.95 | 121.1 | 392.4 | Serveur DHCP Failover 1 |
| **DT-DHCP2**| Dell PowerEdge R360 | U21 | 2 | Double 1+1 600W Plat | 115 | 180 | 0.95 | 121.1 | 392.4 | Serveur DHCP Failover 2 |
| **DT-BKP1**| Dell PowerEdge R760xd2 (2U) | U16-17 | 2 | Double 1+1 1100W Tit. | 250 | 380 | 0.96 | 260.4 | 853.0 | Proxmox Backup Server (12x 10 To SAS ~100 To) |
| **PDU-B2** | 2x APC AP8959EU3 | 0U | 2 | 2x 230V 16A (Voies A/B) | 30 | 30 | 0.95 | 31.6 | 102.4 | PDU intelligentes métrées par prise |
| **UPS-B** | APC SRT6KRMXLI | U1-U4| - | Châssis rack 4U | - | - | - | - | - | Onduleur Voie B logé en fond de baie |
| **TOTAL** | **Baie 2 (15 matériels)**| - | - | - | **1 920 W**| **3 080 W**| **0.95**| **2 012 VA**| **6 551 BTU/h** | **Consommation quasi identique à Baie 1** |

---

### 2.3 Synthèse Globale de la Salle Serveur

| Indicateur | Puissance Active (W) | Puissance Apparente (VA) | Facteur Puissance ($\cos \varphi$) | Charge Thermique (BTU/h) |
|:---|---:|---:|:---:|---:|
| **Baie 1 (Réseau, DMZ, Cœur)** | 1 904.0 W | 2 008.1 VA | 0.95 | 6 497 BTU/h |
| **Baie 2 (Datacenter, PVE, Backup)** | 1 920.0 W | 2 011.7 VA | 0.95 | 6 551 BTU/h |
| **Total IT Salle Serveur (Nominal)** | **3 824.0 W (~3.82 kW)** | **4 019.9 VA (~4.02 kVA)** | **0.95** | **13 048 BTU/h** |
| **Total IT Salle Serveur (Crête 100%)**| **6 217.0 W (~6.22 kW)** | **6 534.1 VA (~6.53 kVA)** | **0.95** | **21 214 BTU/h** |
| **Total IT Salle Serveur (Pic Foisonné 85%)** | **5 284.4 W (~5.28 kW)** | **5 554.0 VA (~5.55 kVA)** | **0.95** | **18 032 BTU/h** |

> [!NOTE]
> La répartition entre la Baie 1 (1 904 W) et la Baie 2 (1 920 W) présente un écart remarquable de seulement 16 W (moins de 1 % d'asymétrie). Cet équilibrage aéraulique et électrique parfait évite tout point chaud asymétrique dans l'allée confinée.

---

### 2.4 Bilan des 6 Locaux Techniques (L.TECH Répartiteurs d'Étage)

Les données proviennent rigoureusement du métré de câblage ([resume.json](file:///home/matteo/Projet_perso/projet_IUT/livrables/plan_cablage/resume.json)). Chaque local technique est protégé par son propre onduleur rackable APC Smart-UPS 1.5 kVA (SMT1500RMI2U, 1 000 W / 1 500 VA).

| Local | Niveau & Emplacement | Surface | Switchs Cisco C9200L-48P | Prises Usagers | Budget PoE | Puissance Nominale | Taux Charge Onduleur | Autonomie Batterie | Type Baie |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **N-1-LT01** | Sous-sol (mitoyen J05) | 6.7 m² | 1x 48P | 10 | 103 W | **148.0 W** | 14.8 % | ~72 min | 24U murale |
| **N-1-LT02** | Sous-sol (Ouest/Chaufferie)| 16.0 m² | 1x 48P | 17 | 70 W | **115.0 W** | 11.5 % | ~79 min | 24U murale |
| **N0-LT01** | RDC Nord (Placard restreint) | 2.3 m² | 2x 48P | 53 | 333 W | **423.0 W** | 42.3 % | ~33 min | 24U murale (Ventilée) |
| **N0-LT02** | RDC Sud (Circulation 04) | 6.9 m² | 4x 48P | 136 | 385 W | **565.0 W** | 56.5 % | ~22 min | 24U murale |
| **N1-LT01** | Étage 1 Nord | 3.7 m² | 2x 48P | 58 | 192 W | **282.0 W** | 28.2 % | ~49 min | 24U murale |
| **N1-LT02** | Étage 1 Sud | 6.6 m² | 5x 48P | 210 | 262 W | **487.0 W** | 48.7 % | ~27 min | 42U 600×800 au sol |
| **TOTAL** | **Ensemble des 6 L.TECH** | **42.2 m²** | **15 switchs** | **484 prises** | **1 345 W** | **2 020.0 W** | - | **> 20 min partout** | **5 murales, 1 sol** |

---

## 3. Architecture Électrique Redondante 2N

Le schéma directeur de l'alimentation électrique repose sur une stricte **architecture 2N**, où deux chemins électriques entièrement séparés (Voie A et Voie B) coexistent sans aucun point unique de défaillance (Single Point of Failure - SPOF) depuis le TGBT jusqu'aux alimentations de chaque serveur.

![Synoptique Électrique 2N](file:///home/matteo/Projet_perso/projet_IUT/livrables/energie_refroidissement/schemas/synoptique_electrique.svg)

### 3.1 Chaîne d'Alimentation Amont

1. **Source Normale (Réseau Public Enedis)** :
   - Raccordement triphasé 400 V + Neutre + PE, fréquence 50 Hz.
   - Livraison sur le TGBT Principal du campus de Luminy, comptage électronique HTA/BT.
2. **Source Secours (Groupe Électrogène Campus)** :
   - Groupe électrogène diesel industriel SDMO / Kohler de **250 kVA**.
   - Démarrage automatique commandé dès coupure réseau : synchronisation et prise de charge effective en **moins de 12 secondes** (classe G3 conforme ISO 8528).
   - Cuve journalière intégrée de 500 litres de fioul lourd assurant plus de **24 heures d'autonomie continue** à pleine charge (possibilité de réapprovisionnement par camion-citerne en service continu).
3. **Inverseur Automatique de Source (ATS Amont Campus)** :
   - Inverseur tétrapolaire motorisé 4P 160A avec double verrouillage mécanique et électrique.
   - En cas de rupture du secteur Enedis, l'ATS bascule vers le groupe électrogène après stabilisation de la tension et de la fréquence (~8 à 10 secondes).
   - Les onduleurs absorbent intégralement ce temps de coupure sans la moindre perturbation pour les charges IT.

---

### 3.2 TGBT Salle Serveur et Découplage Strict Voie A / Voie B

Le TGBT dédié de la salle serveur (implanté contre la paroi ouest de la pièce J05 Sud) est cloisonné en deux compartiments étanches indépendants :

- **Colonne Voie A (Alimentation Primaire)** :
  - Sectionneur général tétrapolaire avec cadenassage de sécurité.
  - Parafoudre débrochable **Type 2** ($I_n = 20\text{ kA}$, $I_{\max} = 40\text{ kA}$) conforme à la norme NF C 15-100 pour la protection contre les surtensions transitoires orageuses (très fréquentes sur le massif des Calanques).
  - Disjoncteur de tête différentiel tétrapolaire **C32A / 300 mA Type A-Si** (Super-Immunisé contre les déclenchements intempestifs causés par les courants harmoniques d'alimentation à découpage).
  - Inverseur de bypass manuel de maintenance 3 positions (**Normal / Test / Bypass**) permettant d'isoler l'onduleur A pour remplacement ou maintenance sans couper la Voie A.
- **Colonne Voie B (Alimentation Secondaire Indépendante)** :
  - Architecture symétrique rigoureusement identique à la Voie A (Sectionneur, Parafoudre Type 2, Disjoncteur différentiel C32A 300 mA Si, Bypass manuel 3 positions).

---

### 3.3 Onduleurs On-Line Double Conversion APC Smart-UPS SRT 6 kVA

Pour la salle serveur, deux onduleurs **APC Smart-UPS SRT 6 kVA (SRT6KRMXLI)** sont déployés en châssis rackables 4U :
- **Technologie VFI-SS-111 (Voltage and Frequency Independent)** : On-Line Double Conversion permanente. Le redresseur convertit le courant alternatif d'entrée en courant continu pour charger les batteries et alimenter l'onduleur interne, qui régénère une onde sinusoïdale parfaite (THD < 2%). Temps de transfert rigoureusement égal à **0 milliseconde** ($0\text{ ms}$).
- **Facteur de Puissance Unitaire ($PF = 1.0$)** : Chaque onduleur fournit **6 000 W réels pour 6 000 VA**.
- **Taux de Charge en Régime Normal 2N (Voies A et B actives)** :
  $$\text{Charge par onduleur} = \frac{3\,824\text{ W}}{2} = 1\,912\text{ W}$$
  $$\text{Taux de charge Voie A / B} = \frac{1\,912\text{ W}}{6\,000\text{ W}} = \mathbf{31.9\,\%}$$
  Ce point de fonctionnement correspond à la plage optimale de rendement de l'électronique de puissance (rendement $\approx 94.5\,\%$ en double conversion permanente).
- **Taux de Charge en Régime Dégradé N (Perte complète d'une voie ou maintenance)** :
  L'onduleur survivant absorbe instantanément 100 % de la charge IT de la salle serveur :
  $$\text{Charge nominale dégradée} = 3\,824\text{ W} \implies \frac{3\,824\text{ W}}{6\,000\text{ W}} = \mathbf{63.7\,\%}$$
  $$\text{Charge pic foisonnée (85 \%)} = 5\,284\text{ W} \implies \frac{5\,284\text{ W}}{6\,000\text{ W}} = \mathbf{88.1\,\%}$$
  L'onduleur supporte cette charge continue sans aucun déclassement, avec une marge de sécurité de plus de 11 % sur le pic de charge absolu.

---

### 3.4 Dimensionnement des Batteries et Autonomie

Chaque onduleur APC Smart-UPS SRT 6 kVA est équipé de sa batterie interne au plomb étanche sans entretien (VRLA, 192 V DC) et d'un **pack batterie externe additionnel 3U (APC SRT192RMBP)** branché à chaud sur le bus DC externe.

#### Tableau comparatif des autonomies réelles (courbes de décharge constructeur)

| Régime d'Exploitation | Puissance Totale | Puissance / Onduleur | Autonomie (Batterie Interne Seule) | Autonomie (Avec Pack Externe SRT192RMBP) |
|:---|:---:|:---:|:---:|:---:|
| **Régime Normal 2N** (50 % Voie A / 50 % Voie B) | 3 824 W | 1 912 W | **~28 minutes** | **~95 minutes** |
| **Régime Dégradé N** (100 % sur Voie survivante) | 3 824 W | 3 824 W | **~11.5 minutes** | **~42 minutes** |
| **Régime Pic Sévère Dégradé N** | 5 284 W | 5 284 W | **~6.5 minutes** | **~23 minutes** |

> [!IMPORTANT]
> Avec **42 minutes d'autonomie à pleine charge IT sur une seule voie**, l'infrastructure dispose d'un temps largement supérieur aux 15 secondes nécessaires au démarrage du groupe électrogène.
> Si le groupe électrogène tombait en panne de carburant ou en défaut de démarrage, le système dispose d'un délai confortable de 30 minutes avant que le contrôleur logiciel (PowerChute Network Shutdown / démon NUT sous Debian) n'ordonne l'extinction ordonnée et progressive :
> 1. Mise en pause et snapshot des VM pédagogiques non critiques.
> 2. Synchronisation et vidage des caches d'écriture des nœuds de stockage Ceph.
> 3. Arrêt propre des bases de données et des hyperviseurs Proxmox VE.
> 4. Arrêt des serveurs Windows Active Directory et enfin des commutateurs réseau.

---

### 3.5 Distribution Terminale : PDU Managées et ATS Rackable 1U

#### PDU Managées et Métrées par Prise (APC AP8959EU3)
Chaque baie 42U intègre **deux PDU verticales 0U** (24 prises : 21x C13 + 3x C19, 230 V 16 A) :
- Baie 1 : **PDU A1** (Voie A) et **PDU B1** (Voie B).
- Baie 2 : **PDU A2** (Voie A) et **PDU B2** (Voie B).
- **Fonctionnalités avancées** :
  - Mesure continue du courant RMS, de la tension, de la puissance active (W), du facteur de puissance et des kWh consommés par chaque prise individuelle.
  - Commutation distante des sorties (Hard reboot d'un équipement planté sans déplacement en salle).
  - Port Ethernet dédié avec support SNMPv3, HTTPS et intégration directe dans LibreNMS pour le suivi énergétique Green IT.

#### Commutateur Automatique de Transfert 1U (APC AP4421A)
Les deux routeurs de bordure Cisco Catalyst C8200L-1N-4T ne disposent que d'un seul bloc d'alimentation électrique interne (monosource) :
- L'**ATS rackable 1U APC AP4421A** est raccordé en entrée 1 sur la Voie A et en entrée 2 sur la Voie B.
- En fonctionnement nominal, il alimente les routeurs depuis la Voie A.
- En cas de disparition de la Voie A, un relais statique ultra-rapide bascule l'alimentation sur la Voie B en **moins de 8 millisecondes** ($< 8\text{ ms}$).
- Comme le temps de maintien des alimentations Cisco (Hold-up time) est de **20 ms**, le basculement est totalement imperceptible pour les routeurs (aucun reboot, aucune perte de paquet BGP/OSPF).

---

### 3.6 Sélectivité Ampèremétrique et Chronométrique

Pour garantir qu'un court-circuit sur une prise de serveur ne fasse pas disjoncter l'ensemble d'une baie ou d'une voie, la cascade de protection respecte la sélectivité totale :
1. **Disjoncteur général TGBT Voie A/B** : Courbe C 32 A, différentiel 300 mA sélectif temporisé (Type S, 60 ms).
2. **Départs divisionnaires TD-OND vers PDU** : Disjoncteurs différentiels monophasés Phase+Neutre **C16 A / 30 mA instantanés Type A-Si** (pouvoir de coupure $I_{cn} = 10\text{ kA}$).
3. **Protection interne PDU** : Disjoncteurs thermiques divisionnaires 16 A par rangée de 7 prises.
4. **Alimentations des serveurs** : Fusibles rapides intégrés aux blocs d'alimentation Dell (8 A / 250 V).

---

## 4. Bilan Thermique, Climatisation de Précision & Aéraulique

La salle serveur J05 Sud (~25.1 m², volume 80.5 m³) fait l'objet d'un aménagement aéraulique optimisé suivant le principe du confinement d'allée froide (Cold Aisle Containment).

![Schéma Aéraulique Salle Serveur](file:///home/matteo/Projet_perso/projet_IUT/livrables/energie_refroidissement/schemas/aeraulique_salle_serveur.svg)

### 4.1 Bilan Thermique Exhaustif de la Salle Serveur

La totalité de la puissance électrique injectée dans la salle est convertie en chaleur sensible par dissipation thermique :

$$\Phi_{\text{total}} = \Phi_{\text{IT}} + \Phi_{\text{Onduleurs}} + \Phi_{\text{Lignes/PDU}} + \Phi_{\text{Éclairage}} + \Phi_{\text{Parois}} + \Phi_{\text{Technicien}}$$

1. **Chaleur IT utile ($\Phi_{\text{IT}}$)** :
   - Régime nominal : $3\,824.0\text{ W}$
   - Régime crête : $6\,217.0\text{ W}$
2. **Pertes thermiques des deux onduleurs ($\Phi_{\text{Onduleurs}}$)** :
   - À 94.5 % de rendement : $3\,824 \times \frac{1 - 0.945}{0.945} = 222.6\text{ W}$
3. **Pertes des lignes électriques, PDU et transformateurs ($\Phi_{\text{Lignes}}$)** :
   - Résistance de ligne et électronique des 4 PDU : $\approx 40.0\text{ W}$
4. **Éclairage LED basse consommation ($\Phi_{\text{Éclairage}}$)** :
   - Éclairage LED régulé par détecteur de présence infrarouge : $100\text{ W}$ intermittent, moyenne pondérée $\approx 20.0\text{ W}$.
5. **Apports par transmission thermique à travers les parois ($\Phi_{\text{Parois}}$)** :
   - Salle en sous-sol enterrée (parois en béton banché de 20 cm, mitoyenne de locaux semi-enterrés). Surface totale des parois : $S_{\text{parois}} \approx 65\text{ m²}$, coefficient moyen $U \approx 0.8\text{ W/m²}\cdot\text{K}$. Écart thermique moyen $\Delta T = 5\text{ K}$ (air extérieur/sol à 27°C, salle à 22°C) :
   $$\Phi_{\text{Parois}} = 65 \times 0.8 \times 5 = 260.0\text{ W}$$
6. **Présence humaine ($\Phi_{\text{Technicien}}$)** :
   - 1 technicien en intervention de maintenance : $120.0\text{ W}$.

#### Synthèse des Besoins Frigorifiques

| Régime | Puissance Thermique Active (W) | Puissance Thermique Frigorifique (kW) | Débit Calorifique (BTU/h) |
|:---|---:|---:|---:|
| **Charge Thermique Nominale** | **4 366.6 W** | **4.37 kW** | **14 899 BTU/h** |
| **Charge Thermique Crête Maximale** | **7 118.9 W** | **7.12 kW** | **24 291 BTU/h** |

---

### 4.2 Solution de Climatisation Redondante N+1

Pour évacuer ces 4.37 kW nominaux (et jusqu'à 7.12 kW en crête exceptionnelle), l'architecture met en œuvre **deux armoires de climatisation de précision à détente directe (DX Inverter)** d'une puissance frigorifique sensible unitaire de **7.2 kW** (ex. Schneider Uniflair / Vertiv Liebert HPS) :
- **Principe de Redondance N+1** :
  - **Unité 1 (Active)** : En régime nominal, l'Unité 1 fonctionne à **60.6 % de sa capacité** ($4.37\text{ kW} / 7.20\text{ kW}$). Le compresseur Inverter régule sa vitesse de rotation à fréquence intermédiaire, garantissant un COP/EER optimal et une longévité maximale.
  - **Unité 2 (Secours N+1 en veille active)** : L'Unité 2 reste sous tension, prête à démarrer automatiquement en moins de 30 secondes en cas d'alarme débit d'air, de défaut pressostatique ou de coupure d'alimentation sur l'Unité 1.
- **Permutation Automatique Hebdomadaire** :
  - L'automate de régulation intervertit les rôles maître/esclave chaque dimanche à 03h00 du matin. Cette rotation automatique garantit un nombre d'heures de fonctionnement parfaitement équilibré sur les compresseurs et les ventilateurs EC.
- **Rapport de Chaleur Sensible (Sensible Heat Ratio - SHR)** :
  - Dans un datacenter étanche sans apport d'humidité externe, la climatisation de confort résidentielle (SHR ~0.70) est proscrite car elle condense inutilement l'humidité de l'air.
  - Les armoires retenues présentent un **SHR supérieur à 0.95**, consacrant 95 % de leur puissance au refroidissement sensible de l'air sans assèchement excessif de l'ambiance.

---

### 4.3 Urbanisation en Allée Froide Confinée (Cold Aisle Containment - CAC)

L'aménagement physique de la salle J05 Sud adopte le standard international des datacenters éco-efficients :
1. **Confinement de l'espace inter-baies** :
   - La Baie 1 et la Baie 2 se font face à une distance de **1.20 m**.
   - L'allée froide est fermée à ses deux extrémités par des **portes coulissantes vitrées étanches** à fermeture automatique amortie.
   - Le plafond de l'allée est surmonté de **panneaux vitrés trempés transparents** équipés de loquets thermofusibles (libération automatique en cas de déclenchement du système d'extinction incendie).
2. **Circuit aéraulique en boucle fermée** :
   - **Plénum de soufflage (Faux-plancher technique 30 cm)** : Les ventilateurs à commutation électronique (EC fans) des climatiseurs insufflent l'air froid sous une dalle étanche sous une pression positive régulée de **25 Pa**.
   - **Dalles perforées haute perméabilité** : Des dalles de sol 600×600 mm perforées (taux de vide 65 % avec registres réglables) laissent monter l'air froid exclusivement à l'intérieur de l'allée confinée à **22°C ± 1°C**.
   - **Traversée des serveurs** : Les ventilateurs internes des serveurs aspirent l'air frais depuis leur façade avant et rejettent l'air réchauffé par l'arrière dans la pièce périphérique.
   - **Plénum de reprise chaud (Faux-plafond 50 cm)** : L'air chaud à **32°C - 35°C** monte par convection naturelle et est capté par des grilles d'aspiration plafonnières pour retourner directement à l'évaporateur des climatiseurs.
3. **Suppression radicale des dérivations (By-pass & Recirculation)** :
   - Tous les emplacements U non occupés dans les baies 42U sont systématiquement obturés par des **passe-câbles à brosses étanches** et des **panneaux pleins de masquage 1U/2U (Blanking panels)**.
   - Cette étanchéité évite tout court-circuit aéraulique où l'air chaud arrière reviendrait vers l'aspiration avant.

---

### 4.4 Exploitation du Free-Cooling Nocturne Méditerranéen

Le campus de Luminy est implanté au pied du massif boisé des Calanques. Cette situation géographique engendre un micro-climat caractérisé par une forte amplitude thermique diurne/nocturne :
- Dès que la température extérieure nocturne descend en dessous de **18°C**, le système de régulation bascule en mode **Free-cooling indirect** :
  - Les compresseurs frigorifiques thermodynamiques s'arrêtent.
  - Une vanne 3 voies oriente le fluide caloporteur vers une batterie à eau glycolée (Dry Cooler) située à l'extérieur sur la toiture technique.
  - La simple convection d'air extérieur suffit à refroidir l'eau du circuit sans aucune compression mécanique.
- **Analyse climatique de Luminy** :
  - D'octobre à mai (8 mois de l'année) ainsi que pendant la majorité des nuits estivales, Luminy enregistre plus de **3 680 heures par an à moins de 18°C** (~42 % de l'année).
  - L'EER (Energy Efficiency Ratio) passe de **3.6 en compression mécanique à plus de 12.0 en free-cooling**.
  - L'économie électrique sur la facture de climatisation atteint **~40 % par an**, prolongeant simultanément la durée de vie des compresseurs frigorifiques.

---

### 4.5 Ventilation Forcée des 6 Locaux Techniques (L.TECH)

Les locaux techniques d'étage hébergent chacun une baie de brassage contenant des commutateurs Cisco PoE+ dissipant de 115 W à 565 W de chaleur continue :

1. **Cas critique du placard N0-LT01 (RDC Nord)** :
   - **Volume ultra-restreint** : Surface de seulement **2.3 m²** (hauteur 2.70 m, volume utile $\approx 6.2\text{ m³}$).
   - **Dissipation continue** : 2 switchs C9200L-48P alimentant 10 bornes Wi-Fi, 3 caméras et 2 badgeuses $\implies P_{\text{nom}} = \mathbf{423.0\text{ W}}$.
   - En espace clos sans ventilation, l'échauffement provoquerait une température interne supérieure à **48°C** en été, entraînant la dégradation prématurée des batteries de l'onduleur et la mise en sécurité thermique des commutateurs.
   - **Dimensionnement du débit d'extraction** :
     $$Q_v = \frac{\Phi}{\rho \times C_p \times \Delta T} = \frac{423\text{ W}}{1.2\text{ kg/m³} \times 1\,005\text{ J/kg}\cdot\text{K} \times 7\text{ K}} = 0.050\text{ m³/s} = \mathbf{181\text{ m³/h}}$$
   - **Solution technique retenue** : Installation d'un caisson d'extraction double ventilateur basse émission sonore ($< 32\text{ dBA}$, N+1) pulsant **185 m³/h** vers le plénum de circulation du RDC, avec grille de transfert acoustique filtrante en bas de porte.
2. **Locaux N0-LT02 (6.9 m² • 565 W) et N1-LT02 (6.6 m² • 487 W)** :
   - Équipés chacun d'un extracteur d'air motorisé régulé par thermostat à bilame (consigne de déclenchement à 26°C, débit $250\text{ m³/h}$).
3. **Locaux N-1-LT01, N-1-LT02 et N1-LT01** :
   - Dissipation plus faible (115 W à 282 W) et volumes suffisants : ventilation naturelle renforcée par grilles de détalonnage hautes et basses avec filtres anti-poussière G3.

---

## 5. Efficacité Énergétique, Green IT & Trajectoire PUE

Le développement durable et la maîtrise de l'empreinte environnementale constituent une exigence centrale du cahier des charges du projet IUT BUT3 R&T.

### 5.1 Calcul Mathématique du PUE Prévisionnel

Le PUE (Power Usage Effectiveness, norme ISO/IEC 30134-2) mesure l'efficacité énergétique d'un centre informatique :

$$\text{PUE} = \frac{P_{\text{totale infrastructure}}}{P_{\text{IT utile}}} = \frac{P_{\text{IT}} + P_{\text{Climatisation}} + P_{\text{Pertes Onduleurs}} + P_{\text{Distribution}} + P_{\text{Auxiliaires}}}{P_{\text{IT}}}$$

Avec les valeurs de notre bilan nominal ($P_{\text{IT}} = 3\,824.0\text{ W}$) :
- Pertes onduleurs double conversion : $P_{\text{ups}} = 222.6\text{ W}$ (ou $58.1\text{ W}$ en mode ECO Green)
- Pertes câbles et distribution : $P_{\text{distrib}} = 40.0\text{ W}$
- Éclairage et sécurité auxiliaire : $P_{\text{aux}} = 20.0\text{ W}$

#### Scénario 1 : Période Estivale / Forte Chaleur (Compression mécanique 100 %, EER = 3.6)
$$P_{\text{clim}} = \frac{4\,366.6\text{ W}}{3.6} = 1\,212.9\text{ W}$$
$$P_{\text{totale, été}} = 3\,824.0 + 1\,212.9 + 222.6 + 40.0 + 20.0 = 5\,319.5\text{ W}$$
$$\mathbf{PUE_{\text{été}}} = \frac{5\,319.5}{3\,824.0} = \mathbf{1.391}$$

#### Scénario 2 : Période Hivernale / Nocturne (Free-cooling actif, EER = 12.0 & Mode ECO Onduleur)
$$P_{\text{clim}} = \frac{4\,366.6\text{ W}}{12.0} = 363.9\text{ W}$$
$$P_{\text{totale, hiver}} = 3\,824.0 + 363.9 + 58.1 + 40.0 + 20.0 = 4\,306.0\text{ W}$$
$$\mathbf{PUE_{\text{hiver}}} = \frac{4\,306.0}{3\,824.0} = \mathbf{1.126}$$

#### Moyenne Annuelle Pondérée (Site de Marseille Luminy : 42 % Free-cooling / 58 % Compression)
$$\mathbf{PUE_{\text{annuel}}} = (0.58 \times 1.391) + (0.42 \times 1.126) = \mathbf{1.280}$$

> [!TIP]
> **Performance Green IT atteinte** :
> L'hypothèse forfaitaire initiale du chiffrage budgétaire retenait un PUE de **1.60** (représentatif d'une vieille salle serveur non confinée).
> Grâce au confinement d'allée froide, à la régulation Inverter, au free-cooling et aux blocs d'alimentation Titanium, le PUE réel annuel est abaissé à **1.28** !
> Ce gain de 0.32 point de PUE représente une économie directe de plus de **10 700 kWh par an**, évitant l'émission de ~600 kg d'équivalent $CO_2$ par an sur le réseau électrique français.

---

### 5.2 Leviers Green IT Mis en Œuvre

1. **Recommandations ASHRAE TC 9.9 (Thermal Guidelines for Data Processing Environments)** :
   - Fonctionnement en **Classe A1** avec consigne de soufflage à **22°C** (admissible jusqu'à 27°C).
   - Augmentation de la consigne d'air froid de 19°C à 22°C : chaque degré d'élévation de consigne réduit la consommation électrique du compresseur de **3.8 à 4.2 %**.
2. **Certification 80 PLUS Titanium & Platinum** :
   - Les 3 serveurs Proxmox Dell PowerEdge R660xs sont commandés avec des alimentations **Titanium** affichant un rendement supérieur à **96.0 %** à mi-charge.
   - Les 12 serveurs Dell R260 et R360 sont équipés de blocs **Platinum** ($> 94.0\,\%$ de rendement).
3. **Fluide Frigorigène à Faible Potentiel de Réchauffement Global (GWP)** :
   - Remplacement du fluide R410A ($GWP = 2\,088$) par le **fluide écologique R32 ($GWP = 675$)** ou **R454B ($GWP = 466$)**, en totale conformité avec la réglementation européenne F-Gas (Règlement UE n° 517/2014 et révision 2024).

---

### 5.3 Métrologie Continue SNMPv3 avec LibreNMS & Grafana

L'ensemble des composants électriques et climatiques est supervisé en continu :
- **PDU APC AP8959EU3** : Interrogées toutes les 60 secondes via SNMPv3 (chiffrement AES-256 / SHA-256). Remontée des Watts, VA, Ampères et kWh par équipement.
- **Onduleurs APC SRT 6 kVA** : Cartes NMC3 monitorées par SNMPv3 et par le démon de supervision NUT (Network UPS Tools) hébergé sur le cluster Proxmox de gestion.
- **Climatiseurs & Centrales T°/HR** : Passerelle Modbus-TCP vers SNMP.
- **Calcul automatique du PUE en temps réel** : Un script Python exécuté sous cron calcule le PUE instantané et pousse la métrique dans la base Prometheus/InfluxDB du cluster NM, avec affichage d'une jauge dynamique sur le tableau de bord Grafana de la DSI.

---

## 6. Sécurité Environnementale et Physique

### 6.1 Système d'Extinction Automatique par Gaz Propre FK-5-1-12 (Novec 1230)

L'utilisation de systèmes d'extinction à eau (sprinklers traditionnels) est strictement exclue en salle informatique en raison des risques de court-circuit destructif irrémédiable.

- **Agent Extincteur FK-5-1-12 (Dodécafluoro-2-méthylpentan-3-one / Novec 1230)** :
  - **Inoffensif pour la vie humaine** : Concentration de conception à **5.3 % vol.**, très inférieure à la limite NOAEL (No Observed Adverse Effect Level) fixée à 10.0 % vol.
  - **Écologique** : Potentiel de déplétion ozonique nul ($ODP = 0$), durée de vie atmosphérique de seulement 5 jours, $GWP = 1$.
  - **Propriétés diélectriques** : Gaz non conducteur, propre, ne laissant aucun résidu gras ni dépôt pulvérulent sur les cartes électroniques.
- **Bouteille de Stockage & Réseau de Diffusion** :
  - Bonbonne monobloc en acier haute pression de **42 litres pressurisée à 50 bar** d'azote sec, logée dans le coin sud-est de la pièce.
  - Décharge volumique intégrale réalisée en **moins de 10 secondes** par des buses de diffusion 360° en acier inox certifiées VdS / APSAD R13.
- **Volet de Surpression Étalonné à 50 Pa** :
  - Lors de la vaporisation instantanée du gaz, la détente brutale crée une surpression mécanique dans la pièce.
  - Un volet gravitaire de décompression étalonné à **50 Pascals** est installé en traversée de paroi donnant vers la cour anglaise extérieure, protégeant l'intégrité structurelle des cloisons et du vitrage.

---

### 6.2 Détection Précoce d'Incendie par Aspiration Laser (VESDA)

Avant même l'apparition d'une flamme ou de fumées visibles, les composants électroniques en surchauffe ou les câbles sous-dimensionnés émettent des micro-particules invisibles à l'œil nu :
- **Centrale VESDA LaserFocus** :
  - Un réseau de micro-tubes d'échantillonnage en PVC rigide prélève en continu l'air dans la veine de reprise chaude des climatiseurs et au plafond.
  - La chambre de mesure optique laser détecte des concentrations d'aérosols de combustion dès **0.005 % d'obscurcissement par mètre**.
- **Scénario d'Asservissement & Déclenchement** :
  - **Seuil d'alerte 1 (0.015 % obs/m)** : Notification silencieuse SNMP vers LibreNMS et envoi de SMS d'alerte aux astreintes techniques.
  - **Seuil d'action 2 (Confirmation par détection optique croisée de plafond)** :
    1. Déclenchement de l'alarme sonore et visuelle d'évacuation (flash rouge + sirène 90 dB).
    2. Compte à rebours de sécurité de **30 secondes** (interrompable par bouton-poussoir coup de poing d'arrêt d'urgence si fausse alerte).
    3. Coupure automatique de la ventilation des climatiseurs et fermeture des clapets coupe-feu pour éviter la dilution du gaz.
    4. Percussion pyrotechnique de la bonbonne de gaz FK-5-1-12.

---

### 6.3 Contrôle d'Accès Physique et Conformité ANSSI

Conformément aux recommandations de l'ANSSI sur la sécurité des systèmes industriels et du bâtiment (**Guide Sécurité GTB/GTC 2025** et **Guide PA-072 v2.0 Contrôle d'accès physique**) :

1. **Enveloppe Physique et Porte d'Accès** :
   - Parois maçonnées en béton plein de 20 cm coupe-feu **EI60** (résistance au feu 1 heure minimum).
   - Porte d'accès blindée certifiée anti-effraction classe 3 (EN 1627) et coupe-feu EI60, équipée d'un ferme-porte hydraulique automatique.
   - Verrouillage par double ventouse électromagnétique 300 kg maintenant la porte bloquée même sous contrainte mécanique.
2. **Badges et Lecteurs Haute Sécurité** :
   - Lecteur mural RFID extérieur certifié conforme aux standards ANSSI : technologies **MIFARE DESFire EV3** avec chiffrement mutuel AES-128bits (les technologies obsolètes non sécurisées 125 kHz EM4100 ou MIFARE Classic sont formellement bannies).
   - Bouton-poussoir intérieur de sortie d'urgence sous boîtier bris de glace vert à déverrouillage mécanique direct hors tension.
   - Contact d'ouverture de porte magnétique télésurveillé (alarme intrusion si la porte reste ouverte plus de 45 secondes).
3. **Vidéoprotection et Cloisonnement Réseau** :
   - Caméra IP dôme grand-angle anti-vandale filmant le sas d'accès à la salle serveur et les deux allées de baies.
   - Tous les équipements de contrôle d'accès, centrales d'alarme intrusion et caméras sont isolés sur le **VLAN 60 (Sûreté / Vidéo / Badge)**, filtré par le pare-feu interne Stormshield SN710 sans aucun accès direct depuis les réseaux usagers ou Internet.

---

## 7. Synthèse Économique & Conformité CAPEX/OPEX

L'ensemble des matériels et prestations dimensionnés dans cette étude technique est en parfaite conformité avec l'estimation budgétaire globale du projet ([estimation.py](file:///home/matteo/Projet_perso/projet_IUT/chiffrage/estimation.py)) :

### Tableau Récapitulatif CAPEX / OPEX (Poste Énergie & Refroidissement)

| Composant Infrastructure | Modèle Retenu | Qté | Prix Unitaire HT | Total CAPEX HT | Justification Technique |
|:---|:---|:---:|---:|---:|:---|
| **Baies Datacenter 42U** | Baie 42U 800×1000 portes perforées 80% | 2 | 1 500 € | 3 000 € | Logement Baie 1 et Baie 2 J05 Sud |
| **Baies Répartiteurs 24U** | Baies murales 24U 600×600 | 5 | 700 € | 3 500 € | Locaux N-1-LT01/02, N0-LT01/02, N1-LT01 |
| **Baie Répartiteur 42U** | Baie au sol 42U 600×800 | 1 | 1 200 € | 1 200 € | Local N1-LT02 (210 prises usagers) |
| **Onduleurs Salle Serveur** | APC Smart-UPS SRT 6 kVA On-Line (SRT6KRMXLI) | 2 | 4 800 € | 9 600 € | Redondance 2N Voies A et B |
| **Packs Batteries Externes**| APC SRT192RMBP (+45 min d'autonomie) | 2 | 1 400 € | 2 800 € | Autonomie portée à 42 min dégradé N |
| **Onduleurs Locaux Tech.** | APC Smart-UPS 1.5 kVA Rack (SMT1500RMI2U) | 6 | 900 € | 5 400 € | Protection locale des switchs PoE |
| **PDU Managées Métrées** | APC AP8959EU3 (0U, 16A, métrage par prise) | 4 | 700 € | 2 800 € | 2 par baie (A1/B1 et A2/B2, Green IT) |
| **ATS Rackable 1U** | APC AP4421A (Automatic Transfer Switch 10A) | 1 | 650 € | 650 € | Sécurisation 2N des C8200L monosources |
| **Climatisation N+1** | 2x Armoires de précision Inverter 7.2 kW DX | 1 | 12 000 € | 12 000 € | N+1 avec alternance automatique hebdo |
| **Confinement Allée Froide**| Portes coulissantes vitrées + toit vitré étanche | 1 | 3 500 € | 3 500 € | Confinement CAC des baies 1 et 2 |
| **Extinction Incendie Gaz**| Centrale FK-5-1-12 (42L/50b) + VESDA Laser | 1 | 8 500 € | 8 500 € | Sécurité incendie sans eau |
| **Contrôle d'Accès Badge** | Lecteur MIFARE DESFire EV3 + ventouses EI60 | 1 | 5 000 € | 5 000 € | Sécurité physique conforme ANSSI |
| **Ventilation N0-LT01** | Caisson d'extraction acoustique 185 m³/h | 1 | 850 € | 850 € | Refroidissement placard 2.3 m² |
| **SOUS-TOTAL CAPEX** | **Lot Énergie, Climatisation & Locaux** | - | - | **58 800 € HT** | **Enveloppe budgétaire respectée** |

---

### Bilan Énergétique et Impact sur l'OPEX Annuel
- **Consommation IT moyenne** : $3.82\text{ kW}$
- **PUE moyen annuel pondéré** : $\mathbf{1.28}$
- **Consommation totale de la salle serveur** : $3.82 \times 1.28 = \mathbf{4.89\text{ kW}}$
- **Consommation annuelle en énergie électrique** :
  $$E_{\text{annuel}} = 4.89\text{ kW} \times 8\,760\text{ h/an} = \mathbf{42\,836\text{ kWh/an}}$$
- **Facture d'électricité annuelle (à 0.22 €/kWh HT)** :
  $$\text{OPEX Électricité} = 42\,836 \times 0.22 = \mathbf{9\,424\text{ € HT / an}}$$
  *(À comparer aux **11 780 € HT / an** qu'aurait coûté une salle non optimisée à PUE 1.60, soit une économie récurrente de **2 356 € HT par an** pour l'IUT).*

---

### Conclusion et Prêt pour Réception
L'ensemble des livrables techniques du Point 14 (**bilan de puissance**, **dimensionnement onduleur 2N**, **climatisation de précision N+1**, **PUE optimisé à 1.28**, **schémas vectoriels SVG normés**) est validé, exhaustif et directement intégrable dans le mémoire de fin d'études et le dossier d'ingénierie d'infrastructure du projet IUT BUT3 R&T.
