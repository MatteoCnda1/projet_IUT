# Plan de câblage (point 04)
<!-- onglet: Câblage -->

Plan de câblage du bâtiment Génie des Télécommunications de l'IUT, campus de Luminy : prises, locaux techniques, fibres, arrivées opérateur et étude Wi-Fi, calculés à partir des plans d'architecte (`docs/plans_batiment/`).

| Document | Réf. | Contenu |
|---|---|---|
| **[implantation.pdf](implantation.pdf)** | RLI-ETU-001 | Document d'implantation : salle serveur, locaux techniques, fibres, arrivées opérateur, et salle par salle le local de rattachement et le chemin des câbles |
| [plans/N-1_cablage.pdf](plans/N-1_cablage.pdf), [N0](plans/N0_cablage.pdf), [N1](plans/N1_cablage.pdf) (.svg, .png) | — | Plan A3 de chaque niveau : prises, bornes, caméras, badgeuses, chemins de câbles, rocades, colonnes, salles teintées par local |
| [synoptique.pdf](synoptique.pdf) (.svg, .png) | — | Rocades, colonnes montantes, adductions, contenu de chaque baie |
| `prises.csv` | — | Toutes les prises : repère (`N0-LT02-P017`), local, salle, type, usage, PoE, position, longueur, repère de l'équipement |
| `baies.csv`, `rocades.csv`, `resume.json` | — | Dimensionnement des baies, longueurs et chemins des rocades, synthèse (lue par le chiffrage, l'énergie, l'adressage et les CCTP) |
| `wifi/` | — | Étude RSSI : cartes de couverture, bornes et canaux |

**Version 2.1 — 20/11/2026** : caméra du foyer des étudiants retirée (7 caméras, 476 prises), voies B du sous-sol et arrivée FAI 2 tracées par d'autres circulations que la voie A, câbles écartés de la gaine d'ascenseur, repères uniques des bornes, caméras et badgeuses, charte commune, repérés « v2.1 » dans les documents. Version précédente : `livrables/archives/v2_2026-11-20/`.

Régénérer : `python3 cablage/salles.py && python3 cablage/etude_rssi.py && python3 cablage/plan_cablage.py && python3 cablage/rapport.py` (sources : `cablage/`). Chaîne complète du dépôt, dans l'ordre des dépendances : `bash outils/ci/generer_tout.sh`.

## Décisions de l'équipe (12/11/2026, complétées le 20/11/2026)

| Sujet | Décision |
|---|---|
| Salle serveur | Partie sud de la **SALLE J05** (sous-sol), environ 25 m² cloisonnés, contre le L.TECH 01 du sous-sol. Au centre du bâtiment : rocades les plus courtes. |
| Répartiteurs d'étage | Les **6 L.TECH** des plans, 2 par niveau. |
| Logement de fonction (étage 1, aile nord-est) | **Hors périmètre** : abonnement opérateur séparé, aucune prise. |
| Densité de prises | Bureau : 2 par poste (PC, téléphone ou réserve). Salle de TP : 1 par poste (environ 2,5 m² par poste, 24 au plus) + 2 pour l'enseignant. Salle de TD, cours, réunion : 3. Projet : 8. |
| Wi-Fi | Nombre de bornes fixé par une **étude RSSI prédictive** (ci-dessous), validée par l'équipe. |
| Sûreté | 7 caméras IP (v2.1 : aucune au foyer des étudiants, lieu de pause), 11 badgeuses (salle serveur, 6 L.TECH, entrée, hall, 2 salles réseaux). |
| Téléphonie IP | 1 téléphone par bureau d'enseignant + l'accueil (secrétariat) : 17 postes, sur la 2e prise du bureau. |
| Adductions opérateur | **Deux entrées séparées** : FAI 1 façade ouest (L.TECH 02 du sous-sol, côté chaufferie), FAI 2 façade est (parking) ; v2.1 : le tracé intérieur de FAI 2 évite les circulations de FAI 1. |
| Rocades | **Deux fibres OM4 par local, par deux chemins distincts** : une par colonne montante (RDC, étage) ; au sous-sol, voie B par d'autres circulations et une autre traversée de mur que la voie A (v2.1). |

## Résultats

- **476 prises RJ45 Cat6A** : 420 usagers, 38 bornes Wi-Fi, 7 caméras, 11 badgeuses.
- **12 783 m de câble cuivre**, lien moyen 26,9 m, **lien le plus long 57,1 m** (aucun au-delà de 90 m).
- **12 rocades fibre**, 738 m au total.
- **15 switchs d'accès** 48 ports PoE+ (Catalyst C9200L-48P-4X) répartis dans les 6 locaux.

### Locaux techniques et baies

| Local | Salle du plan | Surface | Prises | Usagers / Wi-Fi / caméras / badges | Switchs 48p | Baie | PoE | Lien max |
|---|---|---:|---:|---|---:|---|---:|---:|
| N-1-LT01 | L.TECH 01 | 7 m² | 9 | 3 / 2 / 2 / 2 | 1 | 24U murale (9U) | 90 W | 26 m |
| N-1-LT02 | L.TECH 02 | 16 m² | 17 | 13 / 2 / 1 / 1 | 1 | 24U murale (9U) | 70 W | 26 m |
| N0-LT01 | L.TECH | 2 m² | 51 | 38 / 10 / 1 / 2 | 2 | 24U murale (13U) | 307 W | 54 m |
| N0-LT02 | L.TECH 02 | 7 m² | 133 | 120 / 10 / 1 / 2 | 4 | 24U murale (20U) | 346 W | 53 m |
| N1-LT01 | L.TECH 01 | 4 m² | 57 | 49 / 6 / 1 / 1 | 2 | 24U murale (13U) | 179 W | 39 m |
| N1-LT02 | L.TECH 02 | 7 m² | 209 | 197 / 8 / 1 / 3 | 5 | 42U au sol (27U) | 249 W | 57 m |

Le local du RDC nord (`L.TECH`, environ 2 m²) est un placard : baie murale 24U, ventilation dimensionnée par l'étude BET du point 14. Le L.TECH 02 de l'étage reçoit la baie au sol 42U (aile sud, salles de TP).

### Rocades (fibre OM4 12 brins)

| Local | Voie | Par | Chemin | Longueur |
|---|---|---|---|---:|
| N-1-LT01 | A | sous-sol (chemin direct) | SALLE SERVEUR → L.TECH 01 → N-1-LT01 | 14 m |
| N-1-LT01 | B | sous-sol (second chemin) | SALLE SERVEUR → CIRC 03 → L.TECH 01 → N-1-LT01 | 17 m |
| N-1-LT02 | A | sous-sol (chemin direct) | SALLE SERVEUR → CIRC 03 → PARKING NORD → PARKING → L.TECH 02 → N-1-LT02 | 51 m |
| N-1-LT02 | B | sous-sol (second chemin) | SALLE SERVEUR → L.TECH 01 → SAS 01 → CIRC 05 → L.TECH 02 → N-1-LT02 | 57 m |
| N0-LT01 | A | colonne Nord | SALLE SERVEUR → CIRC 02 → CIRCULATION 01 → VIDE SANITAIRE 02 → VIDE SANITAIRE 01 → colonne Nord (montée 3,5 m) → L.TECH → N0-LT01 | 48 m |
| N0-LT01 | B | colonne Sud | SALLE SERVEUR → CIRC 03 → PARKING NORD → PARKING NORD EST → colonne Sud (montée 3,5 m) → L.TECH 02 → CIRCULATION 04 → SOUS-PASSERELLE → DGMT → PL.ELEC → L.TECH → N0-LT01 | 93 m |
| N0-LT02 | A | colonne Sud | SALLE SERVEUR → CIRC 03 → PARKING NORD → PARKING NORD EST → colonne Sud (montée 3,5 m) → L.TECH 02 → N0-LT02 | 36 m |
| N0-LT02 | B | colonne Nord | SALLE SERVEUR → CIRC 02 → CIRCULATION 01 → VIDE SANITAIRE 02 → VIDE SANITAIRE 01 → colonne Nord (montée 3,5 m) → L.TECH → PL.ELEC → DGMT → SOUS-PASSERELLE → CIRCULATION 04 → L.TECH 02 → N0-LT02 | 105 m |
| N1-LT01 | A | colonne Nord | SALLE SERVEUR → CIRC 02 → CIRCULATION 01 → VIDE SANITAIRE 02 → VIDE SANITAIRE 01 → colonne Nord (montée 7,0 m) → RGMT 01 → L.TECH 01 → N1-LT01 | 57 m |
| N1-LT01 | B | colonne Sud | SALLE SERVEUR → CIRC 03 → PARKING NORD → PARKING NORD EST → colonne Sud (montée 7,0 m) → CIRC 05 → PASSERELLE → CIRC 02 → CIRCULATION 01 → L.TECH 01 → N1-LT01 | 104 m |
| N1-LT02 | A | colonne Sud | SALLE SERVEUR → CIRC 03 → PARKING NORD → PARKING NORD EST → colonne Sud (montée 7,0 m) → L.TECH 02 → N1-LT02 | 42 m |
| N1-LT02 | B | colonne Nord | SALLE SERVEUR → CIRC 02 → CIRCULATION 01 → VIDE SANITAIRE 02 → VIDE SANITAIRE 01 → colonne Nord (montée 7,0 m) → CIRCULATION 01 → CIRC 02 → PASSERELLE → CIRC 05 → L.TECH 02 → N1-LT02 | 114 m |

Colonne **Nord** : à l'aplomb du L.TECH du RDC nord, depuis le vide sanitaire 01. Colonne **Sud** : à l'aplomb des L.TECH 02 du RDC et de l'étage, depuis le plafond du parking. La voie B d'un local passe toujours par l'autre colonne : une colonne coupée n'isole aucun local. Au sous-sol, la voie B évite les salles, circulations et traversées de mur de la voie A (v2.1) : aucune circulation commune.

### Adductions

| Opérateur | Entrée | Chemin jusqu'à la salle serveur | Longueur |
|---|---|---|---:|
| FAI 1 | façade ouest, chambre de tirage côté chaufferie | chambre de tirage → L.SERVICE → L.TECH 02 → PARKING → PARKING NORD → CIRC 03 → SALLE SERVEUR | 58 m (dont 15 m jusqu'à la chambre de tirage) |
| FAI 2 | façade est, par le parking | chambre de tirage → PARKING EST → PARKING NORD EST → PARKING NORD → L.TECH 01 → SALLE SERVEUR | 57 m (dont 15 m jusqu'à la chambre de tirage) |

Point commun restant : les deux fourreaux traversent le PARKING NORD, seul passage du côté est vers la salle serveur (supports distincts au plafond du parking).

### Chemins de câbles (circulations et locaux)

| Niveau | Dimension (mm) | Longueur |
|---|---|---:|
| Sous-sol | 100×50 | 88 m |
| RDC | 100×50 | 271 m |
| RDC | 200×60 | 8 m |
| Étage 1 | 100×50 | 233 m |
| Étage 1 | 200×60 | 9 m |
| Étage 1 | 300×100 | 7 m |

Dimension choisie pour un taux de remplissage ≤ 40 % (câble Cat6A de 7,5 mm de diamètre). Dans les salles, le câble suit une goulotte périmétrique depuis la porte.

## Étude Wi-Fi prédictive (RSSI)

Modèle multi-murs à 5 500 MHz : PIRE 18 dBm, exposant 2,2, mur porteur 12 dB, cloison 5 dB, vitrage 3 dB (parois lues sur le plan). Objectif : **≥ −67 dBm** (voix et vidéo) sur 98 % de chaque niveau et 90 % de chaque salle occupée. Une borne par salle de TP, de TD et de projet de 20 m² ou plus, une au foyer, deux pour l'amphithéâtre et S.Cours.

| Niveau | Bornes | Surface couverte | ≥ −67 dBm | 2e borne ≥ −70 dBm (itinérance) |
|---|---:|---:|---:|---:|
| Sous-sol | 4 | 225 m² | 99,1 % | 86,4 % |
| RDC | 18 | 1 269 m² | 98,5 % | 87,8 % |
| Étage 1 | 16 | 1 186 m² | 98,8 % | 92,4 % |

Plan de canaux : 12 canaux de 40 MHz à 5 GHz, 0 conflit co-canal (niveaux compris). Cartes : `wifi/N-1_rssi.png`, `wifi/N0_rssi.png`, `wifi/N1_rssi.png` ; liste des bornes : `wifi/bornes.csv`.

## Normes et règles appliquées

- Câblage structuré ISO/IEC 11801-1 et EN 50173-1 : classe EA (Cat6A, 10GBASE-T), lien permanent ≤ 90 m, canal ≤ 100 m.
- Installation EN 50174-2 : séparation courants forts / faibles, rayons de courbure, rebouchage coupe-feu des traversées.
- Aucun câble dans la gaine ni dans le local de machinerie d'ascenseur (NF EN 81-20) : le calcul des chemins les évite (v2.1).
- Câbles Euroclasse Cca-s1b,d1,a1 (règlement CPR, établissement recevant du public).
- Repérage TIA-606 : prise `<niveau>-LT<local>-P<numéro>`, la même étiquette sur la prise et au panneau de brassage ; équipement raccordé `AP-<niveau>-<nn>` (borne, identifiant de l'étude Wi-Fi), `<niveau>-C<n>` (caméra), `<niveau>-B<n>` (badgeuse), uniques dans le bâtiment.
- Longueur d'un lien = 1,10 × cheminement sur le plan + 3 m de descentes + 2 m de lovage.

## Limites et points à valider avec le client

- Échelle mesurée sur le cartouche des plans : précision ±2 %. Les longueurs sont des estimations, à confirmer au relevé.
- Étude Wi-Fi prédictive, faite sur plan : affaiblissements estimés d'après le trait des parois, pertes entre étages ignorées. Une mesure sur site (site survey) devra la confirmer.
- Emplacement des chambres de tirage des deux opérateurs et accord pour faire passer les chemins de câbles en vide sanitaire et au plafond du parking.
- Les deux arrivées opérateur traversent toutes deux le PARKING NORD : point commun accepté (supports séparés) ou autre entrée pour FAI 2, à décider avec les opérateurs.
- Salle serveur dans J05 : réaffectation de la salle et cloison coupe-feu à valider ; plancher technique, détection de fuite, extinction et climatisation sont au lot énergie (point 14).
- L'amphithéâtre de l'étage n'est accessible que par le bas : ses prises sont câblées depuis le RDC, par les gradins.
- Les petites salles J02 à J04 et la partie restante de J05 sont comptées comme des salles de TD (3 prises), à confirmer selon leur usage.
