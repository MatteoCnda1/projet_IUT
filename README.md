# Projet IUT – Infrastructure réseau du site de Marseille

Projet BUT3 R&T (R5.08 Gestion de projets / SAÉ 5.02) : concevoir le réseau complet du bâtiment IUT Génie Télécom (Luminy), relié au site jumeau (Digne ou Gap), dans le rôle d'une SS2I de conseil réseau.

**Source de vérité : GesTT** (https://gestion-projet-iut.tail4df302.ts.net/?project=proj_iut_marseille). Statut, dates, responsables, décisions et livrables déposés de chaque point y font foi : en cas d'écart, c'est le dépôt qu'on aligne sur GesTT. Les livrables se déposent depuis GesTT, qui crée la pull request ; `roadmap/gestt_2026-11-20.json` en garde un instantané.

**Roadmap interactive (vue des 21 points alignée sur GesTT, journal de bord, chiffrage)** : https://claude.ai/artifact/KP4Dycvm54F3N8PZLvhXbW
(privée : la partager avec les membres du groupe avec le niveau *Contributeur* depuis le menu Partager.)

## Arborescence

| Dossier | Contenu |
|---|---|
| `docs/cahier_des_charges/` | Consignes du projet (`PS5 Projet.pptx`, `Presentation_Projets_LP2021.pptx`) et grille des 21 points (`Avancement projet.xlsx`) |
| `docs/cours/` | Cours architecture d'entreprise (CCNP ch. 22), présentation du réseau AMU / Luminy |
| `docs/plans_batiment/` | Plans du bâtiment : sous-sol, RDC, étage 1, toiture |
| `docs/anssi/` | Référentiel des guides ANSSI applicables, reliés aux points du CdC, avec l'état de chaque écart (injecté dans la roadmap) |
| `docs/references_prix/` | `cisco-price-list.pdf` (ancienne, gammes des années 2000) |
| `maquette/` | Point 06 : TP de la maquette du LAN à deux switchs de cœur (GNS3 / Cisco IOU et containerlab), en cours : pas encore versionné, sera mis au plan v2.1 avant d'entrer dans le dépôt |
| `commun/` | `charte.py` : charte commune des livrables techniques (version et date du dossier, feuille de style, en-tête, cartouche, pied de page numéroté, suivi des versions, typographie française, impression PDF) |
| `architecture/` | Schéma principal `Projet_Marseille_site.drawio` (+ `.png`) : schéma de référence de l'équipe, identique à celui que référence GesTT (commit `7e1db0b`), modifié à la main dans draw.io et jamais réécrit par la chaîne ; schémas logiques `architecture_l2.drawio` et `architecture_l3.drawio`, `archives/` (schémas et sources de la v1 et de la v2). **`architecture/reseau/`** : source unique du plan d'adressage et des VLAN (`donnees.py`) et `build.py` → `livrables/plan_adressage/`, `livrables/architecture_l2/`, `livrables/architecture_l3/`. **`architecture/audit/`** : rapport d'audit du 15/11/2026 (texte figé) et son générateur, `constats_v21.json` (constats de l'audit v2.1 et leur statut), `traitement_audit.py` → `livrables/audit/` |
| `cablage/` | Scripts du plan de câblage et de l'étude Wi-Fi RSSI, à partir des plans PDF (voir `cablage/README.md`) → `livrables/plan_cablage/` |
| `energie/` | Scripts du point 14 : `energie.py` (énergie, onduleurs, groupe électrogène, climatisation, PUE, finances) et `bet.py` (étude BET des locaux techniques) → `livrables/energie_refroidissement/` |
| `chiffrage/` | Estimation budgétaire de l'infra : `estimation_infra.md`, `.csv`, `.json`, script `estimation.py` (reprend le plan de câblage et le lot énergie) |
| `securite/` | Scripts du point 09 (matrice des flux, analyse de risque EBIOS RM, PSSI) → `livrables/securite/` (noms `RLI-P09-*` du dépôt GesTT) |
| `juridique/` | Scripts du point 19 (charte informatique, volet juridique, PRA, guide CdC/CCTP, CCTP des lots 1 à 5) → `livrables/depots/p19/` (dossier et noms du dépôt GesTT de P19, voir `juridique/README.md`) |
| `communication/` | Scripts du point 02 (société fictive **RudyLink Infrastructure**) : logo, charte, plaquette, organisation MOA/MOE, modèles Office → `livrables/communication/` |
| `roadmap/` | Source de la roadmap (`roadmap.template.html`, `build.py`, `seed_points.json`). `build.py` y injecte le chiffrage, le référentiel ANSSI et la version du dossier, et met à jour les notes du point 14 |
| `outils/ci/` | Intégration continue (`.github/workflows/ci.yml`) : `generer_tout.sh` (chaîne complète), `verifier_coherence.py`, `verifier_a_jour.py`, `orthographe.py`, `ruff.toml` (voir `outils/ci/README.md`) |
| `livrables/` | Rapport, présentation, maquette, site web, journal de bord, vidéo en anglais. **`plan_cablage/`** (point 04), **`plan_adressage/`** (point 05), **`architecture_l2/`**, **`architecture_l3/`** (point 03), **`energie_refroidissement/`** (point 14, dont l'étude BET), **`securite/`** (point 09), **`juridique/`** (point 19), **`communication/`** (point 02), **`site_web/`** (site vitrine et journal de bord), **`audit/`** (audits du 15/11 et du 20/11 et leur traitement), **`archives/`** (versions v1 et v2) |

## Versions de l'infrastructure

| Version | Date | État | Où |
|---|---|---|---|
| v1 | 13/11/2026 | auditée le 15/11/2026 (16,9 / 20, 9 constats) | `livrables/archives/v1_2026-11-15/`, `architecture/archives/v1_2026-11-15/` |
| v2 | 15/11/2026 | les 9 constats traités, changements repérés « v2 » ; archivée le 20/11/2026 | `livrables/archives/v2_2026-11-20/`, `architecture/archives/v2_2026-11-20/` |
| **v2.1** | 20/11/2026 | **actuelle** : audit v2.1 traité (4 audits, 167 constats), étude BET, groupe électrogène, charte commune, intégration continue ; changements repérés « v2.1 » | `livrables/` |

Traitement des audits, constat par constat : [`livrables/audit/traitement_audit.pdf`](livrables/audit/traitement_audit.pdf). Chaîne de génération complète, dans l'ordre des dépendances : `bash outils/ci/generer_tout.sh` (puis `python3 outils/ci/verifier_coherence.py`).

## Chiffrage (résumé)

| | HT |
|---|---:|
| CAPEX (avec 10 % d'aléas) | 678 991 € |
| OPEX annuel (années 1 à 5, hors renouvellements) | 66 756 € |
| Coût total sur 5 ans | 1 065 251 € |

Version 2.1 de l'infrastructure (20/11/2026). Version 1 : 582 951 € / 44 081 € / 859 070 €. Version 2 : 606 403 € / 44 892 € / 881 177 €.

Détail et hypothèses : [`chiffrage/estimation_infra.md`](chiffrage/estimation_infra.md). Après une modification d'un script ou de `docs/anssi/referentiel_anssi.md` : `bash outils/ci/generer_tout.sh`, puis republier la roadmap.

## Société fictive : RudyLink Infrastructure

Le groupe joue **RudyLink Infrastructure**, branche conseil réseau (imaginaire) de RudyLink, micro-entreprise réelle d'un membre. Charte, logo, modèles de rapport / slides / compte rendu : [`livrables/communication/`](livrables/communication/README.md). Équipe (comptes GesTT) : Mattéo Canada (chef de projet), Rafael Maunier, Solal Kruczinsky, Raphael Hovsepian. Journal de bord : `livrables/site_web/journal.html`.

## Livrables attendus

Rapport technique (30 p. + annexes) · présentation orale · maquette Packet Tracer/GNS3 · site web du projet · journal de bord · vidéo en anglais. Tous les supports sont à rendre 8 à 10 jours avant l'oral.
