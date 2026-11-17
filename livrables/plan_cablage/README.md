# Plan de câblage – Site de Marseille (point 04)

Généré le 12/11/2026 par `cablage/` à partir des plans d'architecte (`docs/plans_batiment/`). Pour régénérer : `python3 cablage/salles.py && python3 cablage/etude_rssi.py && python3 cablage/plan_cablage.py && python3 cablage/rapport.py && python3 chiffrage/estimation.py`.

## Décisions de l'équipe (12/11/2026)

| Sujet | Décision |
|---|---|
| Salle serveur | Partie sud de la **SALLE J05** (sous-sol), ≈ 25 m² cloisonnés, contre le L.TECH 01 du sous-sol. Au centre du bâtiment : rocades les plus courtes. |
| Répartiteurs d'étage | Les **6 L.TECH** des plans, 2 par niveau. |
| Logement de fonction (étage 1, aile nord-est) | **Hors périmètre** : abonnement opérateur séparé, aucune prise. |
| Densité de prises | Bureau : 2 par poste (PC + téléphone). Salle de TP : 1 par poste (≈ 2,5 m²/poste, 24 max) + 2 enseignant. Salle de TD, cours, réunion : 3. Projet : 8. |
| Wi-Fi | Nombre de bornes fixé par une **étude RSSI prédictive** (ci-dessous), validée par l'équipe. |
| Sécurité | 15 caméras IP, 11 badgeuses (salle serveur, 6 L.TECH, entrées, salles réseaux). |
| Téléphonie IP | 1 téléphone par bureau d'enseignant + l'accueil (secrétariat) : 17 postes, sur la 2ᵉ prise du bureau. |
| Adductions opérateur | **Deux entrées séparées** : FAI 1 façade ouest (L.TECH 02 du sous-sol, côté chaufferie), FAI 2 façade est (parking). |
| Rocades | **Deux fibres OM4 par local, par deux chemins disjoints** (une par colonne montante). |

## Résultats

- **484 prises RJ45 Cat6A** : 420 usagers, 38 bornes Wi-Fi, 15 caméras, 11 badgeuses.
- **13 037 m de câble cuivre**, lien moyen 26.9 m, **lien le plus long 57.1 m** (aucun au-delà de 90 m).
- **12 rocades fibre**, 732 m au total.
- **15 switchs d'accès** 48 ports PoE+ (Catalyst C9200L-48P-4X) répartis dans les 6 locaux.

### Locaux techniques et baies

| Local | Salle du plan | Surface | Prises | Usagers / Wi-Fi / caméras / badges | Switchs 48p | Baie | PoE | Lien max |
|---|---|---:|---:|---|---:|---|---:|---:|
| N-1-LT01 | L.TECH 01 | 7 m² | 10 | 3 / 2 / 3 / 2 | 1 | 24U murale (9U) | 103 W | 38 m |
| N-1-LT02 | L.TECH 02 | 16 m² | 17 | 13 / 2 / 1 / 1 | 1 | 24U murale (9U) | 70 W | 26 m |
| N0-LT01 | L.TECH | 2 m² | 53 | 38 / 10 / 3 / 2 | 2 | 24U murale (13U) | 333 W | 54 m |
| N0-LT02 | L.TECH 02 | 7 m² | 136 | 120 / 10 / 4 / 2 | 4 | 24U murale (20U) | 385 W | 53 m |
| N1-LT01 | L.TECH 01 | 4 m² | 58 | 49 / 6 / 2 / 1 | 2 | 24U murale (13U) | 192 W | 39 m |
| N1-LT02 | L.TECH 02 | 7 m² | 210 | 197 / 8 / 2 / 3 | 5 | 42U au sol (27U) | 262 W | 57 m |

Le local du RDC nord (`L.TECH`, ≈ 2 m²) est un placard : baie murale 24U, ventilation à prévoir. Le L.TECH 02 de l'étage reçoit la baie au sol 42U (aile sud, salles de TP).

### Rocades (fibre OM4 12 brins)

| Local | Voie | Chemin | Longueur |
|---|---|---|---:|
| N-1-LT01 | A | sous-sol (chemin direct) | 14 m |
| N-1-LT01 | B | sous-sol (second chemin) | 14 m |
| N-1-LT02 | A | sous-sol (chemin direct) | 51 m |
| N-1-LT02 | B | sous-sol (second chemin) | 53 m |
| N0-LT01 | A | colonne Nord | 48 m |
| N0-LT01 | B | colonne Sud | 93 m |
| N0-LT02 | A | colonne Sud | 36 m |
| N0-LT02 | B | colonne Nord | 105 m |
| N1-LT01 | A | colonne Nord | 57 m |
| N1-LT01 | B | colonne Sud | 104 m |
| N1-LT02 | A | colonne Sud | 42 m |
| N1-LT02 | B | colonne Nord | 114 m |

Colonne **Nord** : à l'aplomb du L.TECH du RDC nord, depuis le vide sanitaire 01. Colonne **Sud** : à l'aplomb des L.TECH 02 du RDC et de l'étage, depuis le plafond du parking. La voie B d'un local passe toujours par l'autre colonne : une colonne coupée n'isole aucun local.

### Adductions

| Opérateur | Entrée | Longueur jusqu'à la salle serveur |
|---|---|---:|
| FAI 1 | façade ouest, chambre de tirage côté chaufferie | 58 m (dont 15 m jusqu'à la chambre de tirage) |
| FAI 2 | façade est, par le parking | 55 m (dont 15 m jusqu'à la chambre de tirage) |

### Chemins de câbles (circulations et locaux)

| Niveau | Dimension (mm) | Longueur |
|---|---|---:|
| Sous-sol | 100×50 | 120 m |
| RDC | 100×50 | 274 m |
| RDC | 200×60 | 8 m |
| Étage 1 | 100×50 | 242 m |
| Étage 1 | 200×60 | 9 m |
| Étage 1 | 300×100 | 7 m |

Dimension choisie pour un taux de remplissage ≤ 40 % (câble Cat6A Ø 7,5 mm). Dans les salles, le câble suit une goulotte périmétrique depuis la porte.

## Étude Wi-Fi prédictive (RSSI)

Modèle multi-murs à 5500 MHz : PIRE 18 dBm, exposant 2.2, mur porteur 12 dB, cloison 5 dB, vitrage 3 dB (parois lues sur le plan). Objectif : **≥ −67 dBm** (voix et vidéo) sur 98 % de chaque niveau et 90 % de chaque salle occupée. Une borne par salle de TP, de TD et de projet pour la capacité, deux pour l'amphithéâtre et S.Cours.

| Niveau | Bornes | Surface couverte | ≥ −67 dBm | 2ᵉ borne ≥ −70 dBm (itinérance) |
|---|---:|---:|---:|---:|
| Sous-sol | 4 | 225 m² | 99.1 % | 86.4 % |
| RDC | 18 | 1269 m² | 98.5 % | 87.8 % |
| Étage 1 | 16 | 1186 m² | 98.8 % | 92.4 % |

Plan de canaux : 12 canaux de 40 MHz à 5 GHz, 0 conflit co-canal (niveaux compris). Cartes : `wifi/N-1_rssi.png`, `wifi/N0_rssi.png`, `wifi/N1_rssi.png` ; liste des bornes : `wifi/bornes.csv`.

## Fichiers

| Fichier | Contenu |
|---|---|
| `plans/<niveau>_cablage.pdf` (.svg, .png) | Plan A3 de chaque niveau : prises, bornes, caméras, badgeuses, chemins de câbles, rocades, colonnes, salles teintées par local |
| `implantation.pdf` (.html) | **Document d'implantation** : salle serveur, locaux techniques, fibres, et salle par salle le local de rattachement et le chemin des câbles |
| `synoptique.pdf` (.svg, .png) | Rocades, colonnes montantes, adductions, contenu de chaque baie |
| `prises.csv` | Toutes les prises : repère (`N0-LT02-P017`), local, salle, type, usage, PoE, position, longueur |
| `baies.csv`, `rocades.csv`, `resume.json` | Dimensionnement des baies, longueurs des rocades, synthèse |
| `wifi/` | Étude RSSI : cartes de couverture, bornes et canaux |

## Normes et règles appliquées

- Câblage structuré ISO/IEC 11801-1 et EN 50173-1 : classe EA (Cat6A, 10GBASE-T), lien permanent ≤ 90 m, canal ≤ 100 m.
- Installation EN 50174-2 : séparation courants forts / faibles, rayons de courbure, rebouchage coupe-feu des traversées.
- Câbles Euroclasse Cca-s1b,d1,a1 (règlement CPR, établissement recevant du public).
- Repérage TIA-606 : `<niveau>-LT<local>-P<numéro>`, la même étiquette sur la prise et au panneau de brassage.
- Longueur d'un lien = 1,10 × cheminement sur le plan + 3 m de descentes + 2 m de lovage.

## Limites et points à valider avec le client

- Échelle mesurée sur le cartouche des plans : précision ±2 %. Les longueurs sont des estimations, à confirmer au relevé.
- Étude Wi-Fi prédictive, faite sur plan : affaiblissements estimés d'après le trait des parois, pertes entre étages ignorées. Une mesure sur site (site survey) devra la confirmer.
- Emplacement des chambres de tirage des deux opérateurs et accord pour faire passer les chemins de câbles en vide sanitaire et au plafond du parking.
- Salle serveur dans J05 : cloison coupe-feu, plancher technique, détection de fuite (sous-sol), climatisation et réaffectation de la salle.
- L'amphithéâtre de l'étage n'est accessible que par le bas : ses prises sont câblées depuis le RDC, par les gradins.
- Les petites salles J02 à J04 et la partie restante de J05 sont comptées comme des salles de TD (3 prises), à confirmer selon leur usage.
