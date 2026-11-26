# Projet IUT – Infrastructure réseau du site de Marseille

Projet BUT3 R&T (R5.08 Gestion de projets / SAÉ 5.02) : concevoir le réseau complet du bâtiment IUT Génie Télécom (Luminy), relié à un site jumeau (Digne/Gap), dans le rôle d'une SS2I de conseil réseau.

**Roadmap interactive (suivi partagé des 21 points, journal de bord, chiffrage)** : https://claude.ai/artifact/KP4Dycvm54F3N8PZLvhXbW
(privée : la partager aux membres du groupe avec le niveau *Contributeur* depuis le menu Partager.)

## Arborescence

| Dossier | Contenu |
|---|---|
| `docs/cahier_des_charges/` | Consignes du projet (`PS5 Projet.pptx`, `Presentation_Projets_LP2021.pptx`) et grille des 21 points (`Avancement projet.xlsx`) |
| `docs/cours/` | Cours architecture d'entreprise (CCNP ch. 22), présentation du réseau AMU / Luminy |
| `docs/plans_batiment/` | Plans du bâtiment : sous-sol, RDC, étage 1, toiture |
| `docs/anssi/` | Référentiel des guides ANSSI applicables, reliés aux points du CdC et au schéma |
| `docs/references_prix/` | `cisco-price-list.pdf` (ancienne, gammes des années 2000) |
| `maquette/` | Point 06 : TP pour construire la maquette du LAN sous containerlab avec **deux switchs de cœur** (cl1/cl2 : ECMP, VRRP, STP, BFD) : `TP_maquette_LAN_containerlab.md`. Images : `images/construire.sh`. Vos fichiers vont dans `maquette/lan/`. Corrigé testé : `corrige/` (à ouvrir après avoir cherché). Tests automatiques : `bash maquette/tests/verifier.sh --pannes`. Ancienne version à 1 cœur : `archives/` |
| `architecture/` | Schéma `Projet_Marseille_site.drawio` (**v2** : zones DMZ et Datacenter virtualisées, Stormshield sur le cœur, contrôleurs Wi-Fi, iBGP ; zone Net Management : 2 nœuds Proxmox + témoin), schémas logiques `architecture_l2.drawio` et `architecture_l3.drawio`, `archives/` (dont `v1_2026-11-15/` : schémas et sources de la v1). **`architecture/audit/`** : rapport d'audit du 15/11/2026, script qui l'a produit, et `traitement_audit.py` → `livrables/audit/`. **`architecture/reseau/`** : source unique du plan d'adressage et des VLAN (`donnees.py`) et script `build.py` → `livrables/plan_adressage/`, `livrables/architecture_l2/`, `livrables/architecture_l3/` |
| `chiffrage/` | Estimation budgétaire de l'infra : `estimation_infra.md`, `.csv`, script `estimation.py` (reprend les quantités du plan de câblage) |
| `communication/` | Scripts du point 02 (société fictive **RudyLink Infrastructure**) : logo, charte, plaquette, organisation MOA/MOE, modèles Office → `livrables/communication/` (copie des PDF dans `livrables/site_web/documents/`) |
| `energie/` | Script du point 14 (énergie, onduleurs, climatisation, PUE, finances) → `livrables/energie_refroidissement/` |
| `cablage/` | Scripts du plan de câblage et de l'étude Wi-Fi RSSI, à partir des plans PDF (voir `cablage/README.md`) |
| `roadmap/` | Source de la roadmap (`roadmap.template.html`, `build.py`, `seed_points.json`). `build.py` y injecte le chiffrage et le référentiel ANSSI |
| `livrables/` | Rapport, présentation, maquette GNS3, site web, journal de bord, vidéo en anglais. **`livrables/audit/`** : audit du 15/11/2026 et son traitement (v1 → v2). **`livrables/archives/`** : versions précédentes des livrables. **`livrables/plan_cablage/`** : plan de câblage (point 04) et étude Wi-Fi. **`livrables/communication/`** : identité, charte et modèles (point 02). **`livrables/site_web/`** : site vitrine (HTML simple, hébergé sur DM-WEB1) avec le journal de bord |

## Versions de l'infrastructure

| Version | Date | État | Où |
|---|---|---|---|
| v1 | 13/11/2026 | auditée le 15/11/2026 (16,9 / 20, 9 constats) | `livrables/archives/v1_2026-11-15/`, `architecture/archives/v1_2026-11-15/` |
| **v2** | 15/11/2026 | **actuelle** : les 9 constats traités, changements repérés « v2 » dans les documents | `livrables/` |

Traitement de l'audit, constat par constat : [`livrables/audit/traitement_audit.pdf`](livrables/audit/README.md). Chaîne de génération complète :
`python3 architecture/reseau/build.py && python3 energie/energie.py && python3 chiffrage/estimation.py && python3 cablage/plan_cablage.py && python3 communication/build.py && python3 roadmap/build.py && python3 architecture/audit/traitement_audit.py`.

## Chiffrage (résumé)

| | HT |
|---|---:|
| CAPEX (avec 10 % d'aléas) | 606 403 € |
| OPEX annuel (années 1 à 3) | 44 892 € |
| Coût total sur 5 ans | 881 177 € |

Version 2 de l'infrastructure (après l'audit du 15/11/2026). Version 1 : 582 951 € / 44 081 € / 859 070 €.

Détail et hypothèses : [`chiffrage/estimation_infra.md`](chiffrage/estimation_infra.md). Après une modification de `estimation.py` ou de `docs/anssi/referentiel_anssi.md` : `python3 chiffrage/estimation.py && python3 roadmap/build.py`, puis republier la page.

## Société fictive : RudyLink Infrastructure

Le groupe joue **RudyLink Infrastructure**, branche conseil réseau (imaginaire) de RudyLink, micro-entreprise réelle d'un membre. Charte, logo, modèles de rapport / slides / compte rendu : [`livrables/communication/`](livrables/communication/README.md). Équipe (comptes GesTT) : Mattéo Canada (chef de projet), Rafael Maunier, Solal Kruczynski, Raphael Hovsepian. Journal de bord : `livrables/site_web/journal.html`.

## Livrables attendus

Rapport technique (30 p. + annexes) · présentation orale · maquette Packet Tracer/GNS3 · site web du projet · journal de bord · vidéo en anglais. Tous les supports sont à rendre 8 à 10 jours avant l'oral.
